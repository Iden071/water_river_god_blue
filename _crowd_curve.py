# -*- coding: utf-8 -*-
"""Best SCHEDULE-ONLY value for every subset of the 5 Fall-2026 requirements carried.

Purpose (R181 / G-9): the continuation model needs to know how much a semester's week
degrades as it is forced to carry more low-supply courses. That shape is MEASURED here
rather than assumed.

No DEFER, no chapel bonus, no role bonus, no year penalty — pure week quality.

TWO EXACT ACCELERATIONS (neither is a heuristic):
 1. MONOTONICITY. fast_score is non-increasing in the occupied mask: adding a course can
    only add day penalties, destroy a free day, or void the Friday bonus. So if a PARTIAL
    timetable already scores <= the incumbent, no completion of it can win. Verified
    empirically on 4000 random pairs before being relied on; the run aborts if violated.
 2. SUPERSET SEEDING. best(S) >= best(S ∪ {x}) — dropping a forced course cannot hurt.
    So each subset starts with the best value already found for any superset, which gives
    prune (1) a strong incumbent immediately. Subsets are visited largest-first.
"""
import itertools, collections, json, time, random
import rank2 as R2, rank3
from rank2 import fast_score

P, sig, sigs, SIGCODES, code = rank3.build()
LANGP = [s for s in P['OPEN'] if code(s) in R2.LANG]
ELEC  = [s for s in P['OPEN'] if code(s) not in R2.LANG]
REQ = {'MR': P['MR'], 'WCiv': P['WCiv'], 'LHP': P['LHP'], 'SciRD': P['SciRD'], 'Lang': LANGP}
print("pool sizes:", {k: len(v) for k, v in REQ.items()}, "| elec", len(ELEC), flush=True)

esig = collections.defaultdict(list)
for s in ELEC:
    esig[(s['tm'], s['pm'], s['cr'])].append(s)
ekeys = list(esig)
ECODES = {g: {code(s) for s in esig[g]} for g in ekeys}
print("elective signatures:", len(ekeys), flush=True)

random.seed(0)
viol = 0
for _ in range(4000):
    a, b = random.sample(ekeys, 2)
    if a[0] & b[0]:
        continue
    s1, _d = fast_score(a[0], a[1])
    s2, _d = fast_score(a[0] | b[0], a[1] | b[1])
    if s2 > s1 + 1e-9:
        viol += 1
print(f"monotonicity check: {viol} violations / 4000 pairs "
      f"({'OK' if viol == 0 else 'PRUNE INVALID'})", flush=True)
assert viol == 0, "fast_score is not monotone; the prune would be unsound"

CHAPEL = P['Chapel']
N = 6
CR_LO, CR_HI = 17.0, 21.0
out = {}
t0 = time.time()

for k in range(5, -1, -1):                       # largest subsets first -> seeds
    for taken in itertools.combinations(REQ, k):
        seed = -1e9
        for t2, v2 in out.items():
            if set(taken) < set(t2) and v2 > seed:
                seed = v2
        box = [seed, None]
        for ch in CHAPEL + [None]:
            ch_t = ch['tm'] if ch else 0
            ch_p = ch['pm'] if ch else 0
            for combo in itertools.product(*[REQ[n] for n in taken]):
                tm, pm, ok = ch_t, ch_p, True
                for s in combo:
                    if tm & s['tm']:
                        ok = False
                        break
                    tm |= s['tm']
                    pm |= s['pm']
                if not ok:
                    continue
                bc = {code(s) for s in combo}
                if len(bc) < len(combo):
                    continue
                cr = sum(s['cr'] for s in combo)
                cand = [g for g in ekeys if not (tm & g[0]) and (ECODES[g] - bc)]

                def rec(i, kk, t, p, c, used):
                    sc, det = fast_score(t, p)
                    if sc <= box[0]:
                        return                    # EXACT: completions only score lower
                    if kk == 0:
                        if CR_LO <= c <= CR_HI:
                            box[0], box[1] = sc, det
                        return
                    for j in range(i, len(cand)):
                        g = cand[j]
                        if t & g[0]:
                            continue
                        if not (ECODES[g] - used):
                            continue
                        if c + g[2] + 3.0 * (kk - 1) > CR_HI:
                            continue
                        rec(j + 1, kk - 1, t | g[0], p | g[1], c + g[2],
                            used | ECODES[g])

                rec(0, N - k, tm, pm, cr, bc)
        out[taken] = box[0]
        fd = ''.join('월화수목금'[d] for d in sorted(box[1]['free'])) if box[1] else '(=seed)'
        print(f"  n={k} carry={'+'.join(taken) or '(none)':28s} best week = {box[0]:8.3f}"
              f"  free={fd:8s} [{time.time()-t0:.0f}s]", flush=True)

json.dump({('+'.join(kk) or '-'): v for kk, v in out.items()},
          open('crowding.json', 'w'), indent=1)

print("\n--- MEASURED CROWDING CURVE ---", flush=True)
print("best achievable week vs. number of low-supply requirements the semester carries")
prev = None
for k in range(0, 6):
    vals = [v for t, v in out.items() if len(t) == k]
    b = max(vals)
    d = '' if prev is None else f"   marginal cost of the {k}th: {prev - b:8.3f}"
    print(f"  n={k}  best {b:8.3f}   worst {min(vals):8.3f}   ({len(vals)} subsets){d}")
    prev = b
