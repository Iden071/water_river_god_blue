# -*- coding: utf-8 -*-
"""
partition.py — the R285 fix. Optimise the PARTITION of remaining units across remaining
semesters, instead of optimising Fall 2026 and subtracting a per-course proxy.

WHY (R285, Iden 2026-08-16)
---------------------------
    "For all courses, we don't know if we're applying a penalty to this semester that will
     just be pushed over to the next one. For required components especially, this is
     important."

Every ledger item must be taken eventually, so a penalty on a required course is not
avoidable — only relocatable. `K` prices avoidance. The correct objective is

    total = week(Fall 2026)  −  Σ_{s in remaining semesters} discomfort(s)

where the remaining units are PARTITIONED over the remaining semesters. Choosing Fall's six
courses chooses the first block; everything else is constrained by what is left.

R286 already showed the size of the error: with a realistic receiving semester the K spread
across branches falls 24.643 → 4.375 and the margin 19.203 → 2.500. This replaces the proxy
entirely.

THE MODEL
---------
Semesters 3–8 remain (Springs 3/5/7, Falls 4/6/8; R144 skeleton in plan_model).
A semester's discomfort is fixed by which OBLIGATIONS it holds — the free electives that fill
the rest are chosen freely, which is exactly `b1_curve.best_week(pinned, n_free, pool)`:

    cost(S, campus, season) = best_week([], 6, pool) − best_week(S, 6−|S|, pool)

so cost(∅) = 0 and cost grows as a semester is forced to carry more fixed geometry.

CONSTRAINTS (all from plan_model / R144, none invented)
  · ≤ 6 courses per semester
  · QRM3003 is 국제-only AND Spring-only AND chart-year 3  -> sem 5 or 7, campus 국제
  · chart-year: an item may not be taken before its chart year (the year-gap penalty already
    prices earliness, so this is a soft cost, not a hard bar — carried as YEAR_PEN)
  · campus: ≥ 2 국제 semesters overall, sem 2 being one of them

RUN:  NODE_CAP=400000 python partition.py          # builds the cost table, resumable
      python partition.py --solve                  # solves once the table is complete
"""
import json, os, sys, time, itertools, collections

import pools_past as PP
import b1_curve as B
import plan_model as PM
import difficulty as DIFF
from rank2 import year_gap_pen

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda f: os.path.join(HERE, f)
NODE_CAP = int(os.environ.get('NODE_CAP', 400_000))
OUT = P('partition.json')
MAX_PIN = int(os.environ.get('MAX_PIN', 3))
PICKS   = int(os.environ.get('PICKS', 3))    # geometries tried per pinned item   # obligations pinned per semester in the table

# remaining semesters after Fall 2026: (sem, season, academic year)
REM = [(3, 'S', 2), (4, 'F', 2), (5, 'S', 3), (6, 'F', 3), (7, 'S', 4), (8, 'F', 4)]
CAMPUSES = ('국제', '신촌')

# ledger item -> (codes, chart year, hard campus, hard season)
ITEM_RULES = {
    'QRM3003': (['QRM3003'], 3, '국제', 'S'),      # R144: the most constrained item
}


# the five requirements a Fall branch may DEFER. Exactly one of them can be deferred, so a
# future semester carries at most one — which bounds the table blow-up (R290).
DEFERRABLE = ('WCiv', 'LHP', 'SciRD', 'Lang', 'QRM1001')


def units():
    """Remaining (item, codes, count) after Fall 2026 takes one of each Fall item."""
    taken = {'WCiv', 'LHP', 'SciRD', 'Lang', 'ECO1101', 'ME', 'Chapel'}
    out = []
    for i in PM.ITEMS:
        codes = i.get('codes') or []
        n = i['count'] - (1 if i['key'] in taken else 0)
        if n > 0 and codes:
            out.append((i['key'], codes, n))
    return out


def table_items():
    """Every item the cost table must cover, at its FULL ledger count.

    R290, in two misses. First: the table was built from `units()` — the remainder of the MR
    branch — so every OTHER branch left a requirement outstanding that had no rows at all, and
    five of six branches reported NO FEASIBLE PARTITION. That reads like a constraint violation
    and was really a missing row.

    Second: adding only DEFERRABLE was still not enough. A Fall timetable that does not burn an
    `ECO1101` elective leaves ECO1101 outstanding too, so LHP, Lang and '-' still failed. The
    rule is simply that EVERY ledger item with course codes can survive into the remainder, at
    its full count, because Fall consumes at most one of each.
    """
    out = {}
    for i in PM.ITEMS:
        if i.get('codes'):
            out[i['key']] = (list(i['codes']), i['count'])
    return [(k, v[0], v[1]) for k, v in out.items()]


def _spread(g):
    """(distinct weekdays, hours) — a geometry touching fewer days damages a week less."""
    tm = g[0]
    days = sum(1 for d in range(5) if any((tm >> (d * 16 + p)) & 1 for p in range(1, 15)))
    hrs = bin(tm).count('1')
    return (days, hrs)


def geoms(codes, campus, season):
    """Observed geometries, BEST FIRST.

    ⚠️ This returned a dict in insertion order, so `PICKS = n` took n ARBITRARY geometries,
    not the n best. With PICKS lowered for speed at 신촌 that silently turned an approximation
    into a random sample. Ordering by day-spread makes a truncated pick the *best available*
    one, which is the semantics the rest of the model assumes (you choose your section).
    """
    g = {}
    for c in codes:
        for _lab, sigs in PP.course_geometries(c, campus, season).items():
            for s in sigs:
                g[PP.show(s[0])] = s
    return dict(sorted(g.items(), key=lambda kv: _spread(kv[1])))


# the last two terms of each season — "recent" for a course that runs annually
RECENT = ('2025-2', '2026-1', '2026-2')
STALE_MIN_HISTORY = 20   # below this, absence from the recent window is noise, not a move
# how many raw products to enumerate before clash-filtering. Enumeration is a bitmask AND per
# product; only the surviving PICKS of them ever reach best_week. Generous on purpose.
PRODUCT_CAP = int(os.environ.get('PRODUCT_CAP', 20000))
# TWO-STAGE PLACEMENT SEARCH.
# The first version of the F3 fix ordered legal placements by day-spread and evaluated the
# first PICKS of them. Measured, that ordering does NOT predict week value:
#     국제S Chapel+MR5+ME   placement #1 = -3.500, best of first 3 = 2.125
#     국제S Seminar+ME+ME   placement #1 = -7.167, best of first 3 = 5.587, of 6 = 6.658
# So it was rank-by-heuristic then maximise — truncate-then-maximise a seventh time, in the
# code written to fix the sixth. Instead: score EVERY legal placement cheaply, then re-score
# only the best few properly. Nothing is discarded unmeasured, and the shortlist is built from
# computed values rather than a guess. Validated exhaustively on three cells (6, 6 and 18
# legal placements): two-stage == brute force at 600k, 3/3, including the 17.691 the red team
# measured by hand.
SCREEN_CAP = int(os.environ.get('SCREEN_CAP', 40000))    # cheap pass, all placements
SCREEN_MAX = int(os.environ.get('SCREEN_MAX', 600))      # cap on how many we screen at all


def _spread_key(mask):
    """Order legal placements the way `_spread` orders single geometries: fewest days touched
    first, then earliest. Applied to the COMBINED mask so the ordering reflects the whole
    placement rather than each pin in isolation (RED-TEAM F3 defect 2)."""
    days = sum(1 for dd in range(5) if (mask >> (dd * 16)) & 0x7FFF)
    return (days, mask.bit_length())

_OBS = {}


def observed_recent(codes, campus=None, season=None):
    """Sections seen in the RECENT window only (R298)."""
    n = 0
    for lab, rs in PP.terms().items():
        if lab not in RECENT:
            continue
        sea = 'S' if lab.endswith('-1') else 'F'
        if season and sea != season:
            continue
        for r in rs:
            if str(r.get('subjtnb')) in set(codes):
                if campus and r.get('campsDivNm') != campus:
                    continue
                n += 1
    return n


def observed(codes, campus=None, season=None):
    """How many sections of these codes were seen, optionally at one campus/season."""
    key = (tuple(codes), campus, season)
    if key in _OBS:
        return _OBS[key]
    n = 0
    for lab, rs in PP.terms().items():
        sea = 'S' if lab.endswith('-1') else 'F'
        if season and sea != season:
            continue
        for r in rs:
            if str(r.get('subjtnb')) in set(codes):
                if campus and r.get('campsDivNm') != campus:
                    continue
                n += 1
    _OBS[key] = n
    return n


def availability(key, campus, season):
    """'OK' | 'IMPOSSIBLE' | 'UNMEASURED' — and the difference matters to the solver.

    ⛔ R288. A missing cost meant two incompatible things. A course genuinely not offered at a
    campus is a CONSTRAINT the partition must respect; a course we simply never observed there
    is a DATA GAP that must be closed. Conflating them lets the solver treat a real restriction
    as a fixable hole, or worse, silently route around a hole as if it were a restriction.

    The test is evidential, not assumed: if a code has substantial history somewhere and ZERO
    sections at this campus across BOTH seasons, it is campus-restricted. Otherwise the blank
    is thin data.
    """
    # ⭐ R296. DOCUMENTED constraints beat the counting threshold. UIC/QRM courses run at
    # 국제 only, and R144 states QRM3003 is 국제-only AND Spring-only outright. Those have
    # 3-6 observations each — far under the 15 the evidential rule needs — so the threshold
    # returned UNMEASURED for them. It happened to be harmless (UNMEASURED is unplaceable,
    # which is the right answer at 신촌) but it was right for the wrong reason, and a future
    # reader would not be able to tell the two apart.
    if key in ('WCiv', 'QRM1001', 'QRM3003') and campus != '국제':
        return 'IMPOSSIBLE'            # UIC/QRM offerings are 국제 (R8, R144)
    if key == 'QRM3003' and season != 'S':
        return 'IMPOSSIBLE'            # R144, stated
    codes = PM.codes_for(key, campus, season)
    if not codes:
        return 'IMPOSSIBLE'
    # ⭐ R298 — RECENCY BEATS TOTALS (Iden). "If 2019~2024 show some class being available only
    # at S, but 2025~2026 changed to F, then we're assuming F." Counting all six terms equally
    # lets a stale offering outvote the current one. Measured shifts in this data:
    #   LHP    국 only -> 국/신 from 2026-1     (gained 신촌; recent evidence ADDS)
    #   SciRD  국 only -> 국/신 from 2025-2     (same)
    #   ECO2102  국/신 in 2024-2 only, 신 ever since  (LOST 국제 — stale evidence)
    # So: if the item appears at this campus in the RECENT window, OK. If it appears only in
    # OLDER terms and not recently, the offering has moved and the old sighting is stale.
    if observed_recent(codes, campus, season):
        return 'OK'
    if observed(codes, campus, season):
        # ⚠️ only call it stale when there is ENOUGH history to tell a move from noise.
        # MR5 has 6 observations total and bounces between campuses term to term; declaring
        # its 국제-Fall sighting stale would forbid a legal placement on one data point.
        # ECO2102 has 62, of which the 국제 ones are all 2024-2 — that is a move.
        if observed(codes) >= STALE_MIN_HISTORY:
            return 'STALE'
        return 'OK'
    if observed_recent(codes, campus, None):
        return 'UNMEASURED'     # still at this campus lately, just not this season
    if observed(codes, campus, season):
        return 'OK'
    total = observed(codes)
    at_campus = observed(codes, campus, None)
    if total >= 15 and at_campus == 0:
        return 'IMPOSSIBLE'
    return 'UNMEASURED'


def load():
    # ⛔ RED-TEAM F1. This used to be `except Exception: pass` -> return an EMPTY table.
    # `save()` rewrote the whole file once per entry, non-atomically, hundreds of times a run.
    # One interrupted write therefore left truncated JSON, and the next load() swallowed the
    # decode error and handed build_table an empty dict, which rebuilt from scratch in
    # 국제S -> 국제F -> 신촌S -> 신촌F order. A silent total wipe, in a loop whose only health
    # signal is "the entry count went up" — which it does, after a wipe. For a ~19 h unattended
    # run that is the single most dangerous line in the file. Corruption now REFUSES to run.
    if os.path.exists(OUT) and os.path.getsize(OUT):
        try:
            return json.load(open(OUT, encoding='utf-8'))
        except Exception as e:
            bak = OUT + '.corrupt'
            try:
                os.replace(OUT, bak)
            except Exception:
                pass
            raise SystemExit(
                f'\npartition.json is corrupt and was NOT silently discarded.\n'
                f'  {type(e).__name__}: {e}\n'
                f'  moved to: {bak}\n'
                f'Restore a good copy (git show HEAD:partition.json > partition.json) or delete\n'
                f'the .corrupt file to rebuild from scratch — but do that DELIBERATELY.\n')
    return {'base': {}, 'cost': {}}


def save(d):
    # atomic: write beside the target, fsync, then rename. os.replace is atomic on both
    # POSIX and Windows, so an interrupt can no longer leave a half-written table.
    tmp = OUT + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as fh:
        json.dump(d, fh, ensure_ascii=False)
        fh.flush(); os.fsync(fh.fileno())
    os.replace(tmp, OUT)


def build_table(budget=None):
    """cost[campus|season|item1+item2+...] — the discomfort of carrying that set."""
    # 150 s was sized for interactive chunks. The 신촌 half is a ~19 h job, and at 150 s the
    # process re-parses every past term on each restart just to do ~2 entries of real work.
    # BUDGET lets an unattended run amortise that startup over an hour instead.
    if budget is None:
        budget = float(os.environ.get('BUDGET', 150))
    d = load()
    t0 = time.time()
    U = table_items()
    # ALL four. Springs are sems 3/5/7 and Falls 4/6/8, and campus is free per semester
    # (subject to >=2 국제 overall and QRM3003 needing a 국제 Spring), so every combination
    # is reachable and the table must cover all of them.
    for campus, season in (('국제', 'S'), ('국제', 'F'), ('신촌', 'S'), ('신촌', 'F')):
        if True:
            pool, _src = PP.pool(campus, season, years=['2026'])
            if not pool:
                continue
            bk = f'{campus}|{season}'
            if bk not in d['base']:
                # ⭐ the 6-free-slot baseline is the single most expensive call in the project
                # (145-signature pool, 6 open slots). k_real.py already computed it EXACTLY for
                # 2026 — reuse rather than recompute at a lower cap and get a BOUND.
                kr = json.load(open(P('k_real.json'), encoding='utf-8'))
                hit = kr['base'].get(f'{campus}|{season}|2026|6')
                if hit:
                    d['base'][bk] = hit
                    print(f"  base {bk}: {hit[0]:8.3f} {'exact' if hit[1] else 'BOUND'} "
                          f"(from k_real)", flush=True)
                else:
                    v, _n, ok = B.best_week([], 6, pool, node_cap=NODE_CAP)
                    d['base'][bk] = [v, ok]
                save(d)
            base, okb = d['base'][bk]
            # every multiset of up to MAX_PIN items that could share this semester
            names = [k for k, _c, _n in U]
            for r in range(1, MAX_PIN + 1):
                for combo in itertools.combinations_with_replacement(names, r):
                    cnt = collections.Counter(combo)
                    if any(cnt[k] > n for k, _c, n in U if k in cnt):
                        continue
                    if sum(cnt[k] for k in DEFERRABLE if k in cnt) > 1:
                        continue      # at most one deferred requirement exists, ever
                    key = f'{campus}|{season}|' + '+'.join(combo)
                    if key in d['cost']:
                        continue
                    # cheapest legal placement of this multiset: pick the best geometry each
                    # R288: ask the ledger for the codes offered AT THIS campus/season, not
                    # the flat list. And separate the two meanings of a missing cost:
                    #   IMPOSSIBLE  — the item is genuinely not offered here (a real
                    #                 constraint the solver must respect)
                    #   UNMEASURED  — offered, but we have no observed geometry (a data gap)
                    # ⭐ WEEKEND GEOMETRIES ARE FREE, and pinning them is pathological.
                    # 예배채플 runs 일1 (Sunday). It occupies no weekday cell, so it costs
                    # nothing in week comfort — and pinning it constrains the search NOT AT
                    # ALL, degenerating best_week into the unconstrained 6-slot case that
                    # OOMs at every node cap tried. Both facts point the same way: drop
                    # weekend-only geometries from the pinned set and charge them zero.
                    pins, verdict, free_items = [], None, 0
                    n_chapel = sum(1 for k in combo if k == 'Chapel')
                    for k in combo:
                        av = availability(k, campus, season)
                        if av != 'OK':
                            verdict = av; break
                        gg = geoms(PM.codes_for(k, campus, season), campus, season)
                        if not gg:
                            verdict = 'UNMEASURED'; break
                        wk = [g for g in gg.values()
                              if any((g[0] >> (dd * 16 + pp)) & 1
                                     for dd in range(5) for pp in range(1, 15))]
                        # ⛔ RED-TEAM F4. This was `if not wk:` — the free path fired only when
                        # NOTHING was left after dropping weekend geometries. So when an item had
                        # both a weekend and a weekday option, the code discarded the free one and
                        # charged for the weekday one. That inverts the "you choose your section"
                        # semantics geoms() is built on, and contradicts R52 (동영상콘텐츠 occupies
                        # nothing). Chapel at 신촌 has 일1 (YCA1003/YCA1007 비대면, room 동영상콘텐츠,
                        # 15 sections over six terms) alongside 수3/수10/목6/목7 — so 신촌 chapel was
                        # over-charged ~6.125 per semester and the shipped plan carries two of them,
                        # all of it on the 신촌 side of a campus comparison whose entire margin is a
                        # hand-set 30-point bonus. 국제 has no 일1 chapel, so the bias was one-sided.
                        # A weekend section costs nothing, pins nothing and consumes no academic
                        # slot, so it WEAKLY DOMINATES every weekday alternative: if one exists,
                        # the item is free.
                        if len(wk) < len(gg):
                            free_items += 1
                            continue
                        pins.append(wk)
                    if verdict:
                        d['cost'][key] = [None, False, verdict]; save(d); continue
                    if not pins:      # every item in this combo is weekend-only
                        d['cost'][key] = [round(base, 3), okb, 'OK', 0.0]; save(d); continue
                    # ⛔ RED-TEAM F3. This was `islice(product(*pins), PICKS)`, which had three
                    # independent defects in one line:
                    #   1. CLASHING products were charged against the PICKS budget, so a cell
                    #      with 152 legal placements could be recorded as having none.
                    #   2. product() varies the LAST list fastest, so with PICKS <= len(pins[-1])
                    #      the first item's geometry was never varied at all — the day-spread
                    #      ordering the budget relies on is per-item, but the truncation only
                    #      ever explored one of them.
                    #   3. best_exact started True and was never touched when nothing was
                    #      evaluated, stamping never-measured cells as `exact`.
                    # Net: 72 cells labelled 'OK', stamped exact=True, holding no value —
                    # indistinguishable from IMPOSSIBLE to the solver, which is exactly the
                    # conflation R288 exists to prevent. Measured true values up to 29.498
                    # against a Lang->MR margin of 5.325.
                    # Clash-filtering is a bitmask AND and costs nothing; best_week is the
                    # expensive part. So enumerate first, keep only LEGAL products, order them
                    # by day-spread, and spend the PICKS budget only on placements that exist.
                    legal = []
                    for pick in itertools.islice(itertools.product(*pins), PRODUCT_CAP):
                        m = 0; clash = False
                        for g in pick:
                            if m & g[0]:
                                clash = True; break
                            m |= g[0]
                        if not clash:
                            legal.append((_spread_key(m), pick))
                    legal.sort(key=lambda t: t[0])
                    if not legal:
                        # genuinely unplaceable: every geometry combination self-clashes.
                        # Record it as such instead of leaving an 'OK' cell with no value.
                        d['cost'][key] = [None, True, 'NOFIT', None]; save(d); continue
                    n_slots_ = 6 - (r - n_chapel) + free_items
                    # ⚠️ if there are more placements than we can even screen, the screen
                    # itself becomes a truncation. That is recorded in the verdict rather than
                    # hidden, so it can never be mistaken for a measured cell.
                    truncated = len(legal) > SCREEN_MAX
                    cand = [p for _sk, p in legal[:SCREEN_MAX]]
                    if len(cand) > PICKS:
                        scored = []
                        for pick in cand:
                            sv, _n, _o = B.best_week(list(pick), n_slots_, pool,
                                                     node_cap=SCREEN_CAP)
                            scored.append((-1e18 if sv is None else sv, pick))
                        scored.sort(key=lambda t: -t[0])
                        cand = [p for _v, p in scored[:PICKS]]
                    best, best_exact = None, False
                    for pick in cand:
                        # ⛔ R291. CHAPEL IS NOT ONE OF THE SIX. It is 0.5 credits, capped at
                        # one per semester, excluded from the credit cap (plan_model) and held
                        # in its own pool by rank3. Counting it against the 6-course budget
                        # meant `Chapel + 5 free` carried FEWER academic hours than `6 free`,
                        # so 16 entries scored ABOVE their own baseline — a semester carrying
                        # obligations beating one carrying nothing, which is impossible.
                        # Chapel still occupies its hour (it is pinned); it just does not
                        # consume an academic slot.
                        v, _n, ok = B.best_week(list(pick), n_slots_, pool,
                                                node_cap=NODE_CAP)
                        if v is not None and (best is None or v > best):
                            best, best_exact = v, bool(ok)
                    # ⭐ store the RAW week value, not base − value. The partition maximises
                    # Σ best_week over semesters, which is equivalent to minimising Σ cost but
                    # does NOT need `base` — and 신촌|S's 6-slot baseline OOMs at every cap
                    # tried (200M nodes), so depending on it would inject a BOUND into every
                    # 신촌 Spring entry. `base` is now presentation only.
                    # ⛔ record the REAL exactness. An earlier draft hardcoded True here,
                    # which would have written BOUND values into the table as if measured —
                    # 신촌 returns exact=False at every cap tried below ~10M.
                    d['cost'][key] = [None if best is None else round(best, 3), best_exact,
                                      'SCREENTRUNC' if truncated else 'OK',
                                      None if best is None else round(base - best, 3)]
                    save(d)
                    if time.time() - t0 > budget:
                        print(f"  … budget reached at {key}, resumable", flush=True)
                        return d
            print(f"  {campus} {season}: table done [{time.time()-t0:.0f}s]", flush=True)
    return d


if __name__ == '__main__':
    if '--solve' in sys.argv:
        import partition_solve  # noqa
    else:
        build_table()
        c = load()
        print(f"\ncost entries: {len(c['cost'])}  bases: {len(c['base'])}")
