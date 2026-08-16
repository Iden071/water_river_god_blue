# -*- coding: utf-8 -*-
"""
b1_curve.py — B-1 on the `_crowd_curve` engine: K(req, n) at REALISTIC semester loads.

WHY THIS FILE REPLACES THE semester_sim PATH
--------------------------------------------
`b1_receiving.py` measured K only for n ≤ 2 (R227). Beyond that, choosing 6 sections from
139–184 distinct time-masks is ~7.7e9 combinations, `semester_sim`'s naive recursion hit its
node budget, and the two arms of `K = week_without − week_with` truncated by DIFFERENT
amounts — so K went negative. That was an artefact of unequal truncation, not hole-filling.
A real receiving semester holds 5 other courses, so K was measurable only where it does not
matter.

`_crowd_curve.py` already solved this exact shape of problem exhaustively in ~5 s. This file
reuses its three ideas and fixes its one flaw.

WHAT IS TAKEN FROM `_crowd_curve`
  1. **Signature collapse** — sections are deduplicated on (time mask, presence mask). Two
     sections with identical masks score identically, so only one need ever be enumerated.
  2. **A strong incumbent first** — `_crowd_curve` gets one by seeding each subset from its
     supersets. Here the same job is done by a greedy + randomised-restart pass before the
     exact search, because any feasible solution is a valid lower bound.
  3. **Branch and bound with an exact prune**, visiting light sections first.

WHAT IS FIXED
  `_crowd_curve` prunes on `fast_score`, asserting monotonicity from 4,000 random pairs.
  R217 later produced a counterexample — hole-filling — so that prune is **unsound**, and
  `crowding.json` (which the live model still reads) was built with it. This file prunes on
  `week_value`, which is sound by proof rather than by sampling:

      fast_score(final) = week_value(final) + Σ day_pen(final)
                       ≤ week_value(final)    — day_pen ≤ 0, verified EXHAUSTIVELY over all
                                                65,536 day masks, 0 exceptions
                       ≤ week_value(partial)  — every term of week_value is non-increasing in
                                                occupancy: adding hours can only shorten the
                                                presence-free weekend run, remove a
                                                genuinely-empty weekday, or void the Friday
                                                bonus.

  A looser bound prunes less, which is paid for by (2). Every result reports whether the
  search **completed** — a completed search is EXACT, not a bound.
"""
import itertools, collections, json, time, os, random, statistics, sys

import rank as RK
import rank2 as R2, difficulty as DIFF
R2.LANG = set(DIFF.LANG_ALL)
import rank3
from rank2 import fast_score, week_value
import semester_sim as SS

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# POOLS — distinct (tm, pm) signatures, per campus
# ---------------------------------------------------------------------------
MIN_HOURS = 3      # a ledger unit is a 3-credit course; the median real section is 3 hours.
                   # `semester_sim.filler_pool` kept the LIGHTEST masks, which are 1-hour
                   # sections, and so modelled every receiving semester far emptier than it
                   # will be (R227).


def pool_for(campus, min_hours=MIN_HOURS):
    src = SS._INTL if campus == '국제' else SS._SIN
    seen, out = set(), []
    for c, sec in src.items():
        tm = sec['tm']; pm = sec.get('pm', tm)
        if bin(tm).count('1') < min_hours:
            continue
        if (tm, pm) in seen:
            continue
        seen.add((tm, pm))
        out.append((tm, pm))
    out.sort(key=lambda g: bin(g[0]).count('1'))      # light first: good incumbents early
    return out


# ---------------------------------------------------------------------------
# THE SEARCH
# ---------------------------------------------------------------------------
def greedy_incumbent(pool, m, tm0, pm0, restarts=300, rng=None):
    """Any feasible timetable is a valid lower bound. Greedy + randomised restarts."""
    rng = rng or random.Random(0)
    best = -1e9
    for r in range(restarts):
        t, p, k = tm0, pm0, 0
        cand = list(range(len(pool)))
        if r:
            rng.shuffle(cand)
        for j in cand:
            if k == m:
                break
            a, b = pool[j]
            if t & a:
                continue
            t |= a; p |= b; k += 1
        if k == m:
            sc, _ = fast_score(t, p)
            if sc > best:
                best = sc
    return best


DAYMASK = [0xffff << (d * 16) for d in range(5)]


def ub_free(F):
    """Closed-form ceiling on fast_score for any timetable whose presence-free weekday set
    is exactly F. trip is determined by F; REST ≤ 7·|F| because a fixed-free day must also be
    presence-free; the Friday bonus needs 4 ∈ F; and Σ day_pen ≤ 0 (verified exhaustively)."""
    free = set(F)
    run = 2
    for d in (4, 3, 2, 1, 0):
        if d in free: run += 1
        else: break
    if run < 7:
        for d in (0, 1, 2, 3, 4):
            if d in free: run += 1
            else: break
    run = min(run, 7)
    trip = RK.DAY_CONTIG * (run - 2) ** RK.RUN_EXP if run > 2 else 0.0
    return trip + RK.REST * len(free) + (RK.FRI_EVENT if 4 in free else 0.0)


# ---------------------------------------------------------------------------
# ⭐ THE SECOND EXACT BOUND — the least-bad day with h occupied hours
# ---------------------------------------------------------------------------
# The free-day ceiling caps week_value but says nothing about day_pen, so a branch forced to
# cram six courses into three days looks as good as one that spreads them. Yet Σ day_pen is
# bounded above too: for a day holding h hours, the BEST it can score is
#     G[h] = max over all 16-bit masks of popcount h of day_pen(mask),
# computed exhaustively (65,536 masks, once). Then over d available days carrying H hours in
# total, the best achievable is a small DP, and it is monotone decreasing in H — so using the
# MINIMUM hours still to be placed keeps the bound valid.
def _build_G():
    from rank2 import day_pen
    G = [-1e9] * 16
    for msk in range(1 << 16):
        h = bin(msk).count('1')
        if h < 16:
            v = day_pen(msk)[0]
            if v > G[h]:
                G[h] = v
    return G


_G = _build_G()
_PEN = {}


def pen_ub(d, H):
    """Upper bound on Σ day_pen for H occupied hours spread over d days."""
    if H <= 0:
        return 0.0
    key = (d, H)
    if key in _PEN:
        return _PEN[key]
    best = [-1e9] * (H + 1)
    best[0] = 0.0
    for _ in range(d):
        nxt = best[:]
        for used in range(H + 1):
            if best[used] <= -1e9:
                continue
            for h in range(1, min(15, H - used) + 1):
                v = best[used] + _G[h]
                if v > nxt[used + h]:
                    nxt[used + h] = v
        best = nxt
    # fewer hours can only be better, so take the best over >= H is wrong; we want exactly H
    # placed or fewer days used — take the max over totals >= H is unsound, so use H itself.
    _PEN[key] = best[H] if best[H] > -1e9 else 0.0
    return _PEN[key]


def _bb(cand, m, tm, pm, box, node_cap, need=(), ceiling=None, ndays=7, minh=MIN_HOURS):
    """Branch and bound over `cand`. Mutates box[0] with any improvement found.

    `need` = weekdays that must end up occupied (exact-F semantics; keeps branches disjoint
    so the closed-form ceiling is valid). `ceiling` = that branch ceiling."""
    nodes = [0]; done = [True]
    needm = [DAYMASK[d] for d in need]

    def rec(i, k, t, p):
        if nodes[0] >= node_cap:
            done[0] = False; return
        nodes[0] += 1
        if ceiling is not None and ceiling <= box[0]:
            return
        ub, _ = week_value(p, t)                  # ⭐ SOUND upper bound on any completion
        if ub + pen_ub(ndays, bin(t).count('1') + minh * k) <= box[0]:
            return                                # ⭐ plus the day-occupancy ceiling
        miss = sum(1 for dm in needm if not (p & dm))
        if miss > k:                              # cannot still cover every required day
            return
        if k == 0:
            if miss:
                return
            sc, _ = fast_score(t, p)
            if sc > box[0]:
                box[0] = sc
            return
        if len(cand) - i < k:
            return
        for j in range(i, len(cand)):
            a, b = cand[j]
            if t & a:
                continue
            rec(j + 1, k - 1, t | a, p | b)

    rec(0, m, tm, pm)
    return nodes[0], done[0]


def best_week(pinned, m, pool, node_cap=4_000_000):
    """Exact best achievable week: `pinned` sections plus m free choices from `pool`.

    ⭐ DECOMPOSED BY FREE-DAY PATTERN — the acceleration that makes realistic loads reachable.
    Every timetable has some set of presence-free weekdays. Enumerating that set F first and
    restricting the pool to sections that avoid F splits the problem into 32 much smaller
    ones whose union is exhaustive: a solution whose free set is F is found in the F branch.
    Large F gives a tiny pool and an instant, strong incumbent, which is then shared with the
    smaller-F branches — the same superset-seeding trick `_crowd_curve` uses, applied to days
    instead of requirement subsets. Plain greedy sits 30–67 points below the optimum and
    cannot drive the bound; this reaches the optimum immediately.

    Returns (best, nodes, completed). completed=True => the value is EXACT."""
    tm = pm = 0
    for a, b in pinned:
        if tm & a:
            return None, 0, True          # the pinned set self-conflicts
        tm |= a; pm |= b
    cand0 = [(a, b) for (a, b) in pool if not (tm & a)]
    if len(cand0) < m:
        return None, 0, True

    box = [greedy_incumbent(cand0, m, tm, pm, restarts=40)]
    total, done = 0, True
    # ⭐ EXACT-F semantics + a CLOSED-FORM CEILING PER BRANCH.
    # Branch F holds exactly the timetables whose presence-free weekday set IS F. For those,
    # week_value is capped in closed form before a single node is expanded:
    #     trip is fixed by F · REST ≤ 7·|F| (fixed-free ⊆ presence-free) · Friday bonus needs
    #     4 ∈ F · and Σ day_pen ≤ 0.
    # So ub(F) is an upper bound on everything the branch can yield. Branches are visited in
    # descending ub(F), and any whose ceiling is already below the incumbent is skipped whole.
    # This is what makes a full 6-course 신촌 semester reachable: with no free weekday at all,
    # ub(∅) = 0, so that branch — the one holding the entire unrestricted pool — is discarded
    # outright once any timetable scoring above 0 has been seen.
    branches = []
    for size in range(5, -1, -1):
        for F in itertools.combinations(range(5), size):
            branches.append((ub_free(F), F))
    branches.sort(key=lambda x: -x[0])
    for ubF, F in branches:
        if ubF <= box[0]:
            continue                              # whole branch is dominated
        block = 0
        for d in F:
            block |= DAYMASK[d]
        if pm & block:                            # a pinned course already occupies day d
            continue
        cand = [(a, b) for (a, b) in cand0 if not (b & block)]
        if len(cand) < m:
            continue
        need = [d for d in range(5) if d not in F]
        n, ok = _bb(cand, m, tm, pm, box, node_cap, need=need, ceiling=ubF,
                    ndays=(5 - len(F)) + 2)
        total += n; done = done and ok
    return box[0], total, done


# ---------------------------------------------------------------------------
# THE REQUIREMENTS, WITH Lang SPLIT BY TIER (R227 finding 2)
# ---------------------------------------------------------------------------
CASES = [
    ('MR',        ['QRM1001'],                       'S', '국제', '국제-only'),
    ('WCiv',      ['UIC1561'],                       'S', '국제', '국제-only'),
    ('LHP',       ['UIC1551', 'UIC1251', 'UIC1501'], 'F', '신촌', 'any campus'),
    ('SciRD',     ['UIC2151'],                       'F', '신촌', 'any campus'),
    ('Lang·easy', sorted(DIFF.LANG_EASY),            'S', '국제', '국제 ONLY — 0 신촌 sections'),
    ('Lang·hard', sorted(DIFF.LANG_HARD),            'F', '신촌', 'the only tier at 신촌'),
]


def sections_for_case(codes, term, campus):
    out, prov = [], []
    for c in codes:
        s, src = SS.sections_for(c, term, campus)
        for x in s:
            out.append((x['tm'], x.get('pm', x['tm'])))
        if s:
            prov.append(f"{c}:{src.split('(')[0].strip()}({len(s)})")
    seen, ded = set(), []
    for g in out:
        if g not in seen:
            seen.add(g); ded.append(g)
    return ded, ' · '.join(prov)


def run(nmax=5, node_cap=30_000_000, only=None):
    p = os.path.join(HERE, 'b1_K.json')
    res = {}
    if os.path.exists(p) and os.path.getsize(p):
        try: res = json.load(open(p, encoding='utf-8'))
        except Exception: res = {}
    t0 = time.time()
    pools = {c: pool_for(c) for c in ('국제', '신촌')}
    print(f"pools (≥{MIN_HOURS}h, distinct masks): " +
          ' '.join(f"{c} {len(v)}" for c, v in pools.items()), flush=True)

    # the WITHOUT arm depends only on (campus, m) — compute once, share across requirements
    bp = os.path.join(HERE, 'b1_base.json')
    base = {}
    if os.path.exists(bp) and os.path.getsize(bp):
        base = {tuple(k.split('|')[0:1]) + (int(k.split('|')[1]),): tuple(v)
                for k, v in json.load(open(bp, encoding='utf-8')).items()}
    for camp, pool in pools.items():
        for m in range(1, nmax + 2):
            if (camp, m) in base:
                continue
            v, n, ok = best_week([], m, pool, node_cap)
            base[(camp, m)] = (v, ok)
            json.dump({f"{c}|{mm}": list(val) for (c, mm), val in base.items()},
                      open(bp, 'w', encoding='utf-8'))
            print(f"  baseline {camp} {m} courses: {v:8.3f}  {'exact' if ok else 'BOUND'}"
                  f"  [{n} nodes, {time.time()-t0:.0f}s]", flush=True)

    for name, codes, term, campus, note in CASES:
        if only and name not in only:
            continue
        S, prov = sections_for_case(codes, term, campus)
        if not S:
            print(f"{name}: NO SECTION DATA"); continue
        pool = pools[campus]
        row = {}
        for n in range(0, nmax + 1):
            withs, ok_all = [], True
            for s in S:
                v, _nd, ok = best_week([s], n, pool, node_cap)
                if v is not None:
                    withs.append(v); ok_all = ok_all and ok
            b, okb = base[(campus, n + 1)]
            if not withs or b is None:
                row[n] = None; continue
            row[n] = dict(K=b - statistics.median(withs),
                          K_best=b - max(withs), K_worst=b - min(withs),
                          with_median=statistics.median(withs), without=b,
                          exact=bool(ok_all and okb))
        res[name] = dict(note=note, term=term, campus=campus, provenance=prov,
                         n_sections=len(S), curve=row)
        print(f"\n{name:11s} {campus} {'Spring' if term=='S' else 'Fall'}  {note}", flush=True)
        print(f"            {prov}", flush=True)
        print(f"            " + ' '.join(f"n={n}" .ljust(9) for n in range(0, nmax + 1)), flush=True)
        print(f"  K       : " + ' '.join(
            (f"{row[n]['K']:8.2f}{'' if row[n]['exact'] else '~'}" if row[n] else '       -').ljust(9)
            for n in range(0, nmax + 1)), flush=True)
        json.dump(res, open(p, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print(f"\nwrote b1_K.json  [{time.time()-t0:.0f}s]   ('~' = search truncated, value is a bound)")
    return res


if __name__ == '__main__':
    run(only=sys.argv[1:] or None)
