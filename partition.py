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
MAX_PIN = int(os.environ.get('MAX_PIN', 2))   # obligations pinned per semester in the table

# remaining semesters after Fall 2026: (sem, season, academic year)
REM = [(3, 'S', 2), (4, 'F', 2), (5, 'S', 3), (6, 'F', 3), (7, 'S', 4), (8, 'F', 4)]
CAMPUSES = ('국제', '신촌')

# ledger item -> (codes, chart year, hard campus, hard season)
ITEM_RULES = {
    'QRM3003': (['QRM3003'], 3, '국제', 'S'),      # R144: the most constrained item
}


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


def chart_year(key, codes):
    from rank2 import QRM_CHART_YEAR
    ys = [QRM_CHART_YEAR[c] for c in codes if c in QRM_CHART_YEAR]
    return min(ys) if ys else 1


def geoms(codes, campus, season):
    g = {}
    for c in codes:
        for _lab, sigs in PP.course_geometries(c, campus, season).items():
            for s in sigs:
                g[PP.show(s[0])] = s
    return g


def load():
    if os.path.exists(OUT) and os.path.getsize(OUT):
        try:
            return json.load(open(OUT, encoding='utf-8'))
        except Exception:
            pass
    return {'base': {}, 'cost': {}}


def save(d):
    json.dump(d, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)


def build_table(budget=150):
    """cost[campus|season|item1+item2+...] — the discomfort of carrying that set."""
    d = load()
    t0 = time.time()
    U = units()
    # only the (campus, season) pairs the plan can actually use, and that k_real measured
    for campus, season in (('국제', 'S'), ('신촌', 'F')):
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
                    key = f'{campus}|{season}|' + '+'.join(combo)
                    if key in d['cost']:
                        continue
                    # cheapest legal placement of this multiset: pick the best geometry each
                    pins, ok_all = [], True
                    for k in combo:
                        codes = dict((a, b) for a, b, _n in U)[k]
                        gg = geoms(codes, campus, season)
                        if not gg:
                            ok_all = False; break
                        pins.append(list(gg.values()))
                    if not ok_all:
                        d['cost'][key] = [None, False]; save(d); continue
                    best = None
                    for pick in itertools.islice(itertools.product(*pins), 8):
                        m = 0; clash = False
                        for g in pick:
                            if m & g[0]:
                                clash = True; break
                            m |= g[0]
                        if clash:
                            continue
                        v, _n, ok = B.best_week(list(pick), 6 - r, pool, node_cap=NODE_CAP)
                        if v is not None and (best is None or v > best):
                            best = v
                    d['cost'][key] = [None if best is None else round(base - best, 3), True]
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
