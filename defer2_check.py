"""defer2_check.py — can ANY 2-deferral timetable beat the 1-deferral incumbent?

Runs one deferral pair at a time with the incumbent preloaded, so branch-and-bound prunes
from the first node instead of after 30s of warm-up. Usage:  python defer2_check.py MR LHP
"""
import sys, time, json, collections, itertools, heapq
import rank as RK, rank2 as R2, rank3 as R3
from rank2 import fast_score, year_of, YEAR_PEN, eff_year

# R129 re-run. THREE staleness bugs fixed at the same time — this script had drifted
# away from rank3 and was no longer checking the thing it claimed to check:
#   1. INCUMBENT was 29.34, three optima out of date.
#   2. it used year_of() where rank3 uses eff_year() — i.e. it silently dropped R128b's
#      QRM-chart-year override, so it scored QRM courses differently from the ranker.
#   3. it never added R127's CHAPEL_BONUS (+10), so every chapel-taking timetable scored
#      10 points low here relative to rank3.
INCUMBENT = 21.795  # R157: re-synced. GOES STALE ON EVERY WEIGHT CHANGE — re-read
SCHED_UB = 276.0    # true ceiling on week_value under R129 — see rank3.py

def run(defer):
    P, sig, sigs, SIGCODES, code = R3.build()
    LANGP = [s for s in P['OPEN'] if code(s) in R2.LANG]
    ELEC  = [s for s in P['OPEN'] if code(s) not in R2.LANG]
    REQ = {'MR': P['MR'], 'WCiv': P['WCiv'], 'LHP': P['LHP'],
           'SciRD': P['SciRD'], 'Lang': LANGP}
    esig = collections.defaultdict(list)
    for s in ELEC:
        b = R2.BONUS.get(code(s), 0.0) + s.get('_role', 0.0) + YEAR_PEN(eff_year(s, code))
        esig[(s['tm'], s['pm'], b, s['cr'])].append(s)
    ekeys = sorted(esig, key=lambda g: -g[2])
    ECODES = {g: {code(s) for s in esig[g]} for g in ekeys}

    D = R3.DEFER
    best = [INCUMBENT]; found = [None]; nodes = [0]
    taken = [n for n in REQ if n not in defer]
    t0 = time.time()
    for ch in P['Chapel'] + [None]:
        dcost = (R3.CHAPEL_BONUS if ch else D['Chapel']) + sum(D[n] for n in defer)
        if dcost + SCHED_UB < best[0]:
            continue
        tm0 = ch['tm'] if ch else 0; pm0 = ch['pm'] if ch else 0
        for combo in itertools.product(*[REQ[n] for n in taken]):
            tm, pm, ok = tm0, pm0, True
            for s in combo:
                if tm & s['tm']: ok = False; break
                tm |= s['tm']; pm |= s['pm']
            if not ok: continue
            bc = {code(s) for s in combo}
            if len(bc) < len(combo): continue
            cr  = sum(s['cr'] for s in combo)
            pen = sum(YEAR_PEN(year_of(s['yr'])) for s in combo)
            cand = [g for g in ekeys if not (tm & g[0]) and (ECODES[g] - bc)]
            k0 = R3.N_ACADEMIC - len(taken)
            bb = sorted((g[2] for g in cand), reverse=True)
            bestb = [0.0] + [sum(bb[:k]) for k in range(1, k0+1)]
            def rec(i, k, t, p, c, b, used):
                nodes[0] += 1
                if b + bestb[k] + pen + dcost + SCHED_UB < best[0]: return
                if k == 0:
                    if not (R3.CR_LO <= c <= R3.CR_HI): return
                    sc, _ = fast_score(t, p); sc += b + pen + dcost
                    if sc > best[0]: best[0] = sc; found[0] = (sc, combo, defer)
                    return
                for j in range(i, len(cand)):
                    g = cand[j]
                    if b + g[2] + bestb[k-1] + pen + dcost + SCHED_UB < best[0]: break
                    if t & g[0]: continue
                    if not (ECODES[g] - used): continue
                    if c + g[3] + 3.0*(k-1) > R3.CR_HI: continue
                    rec(j+1, k-1, t|g[0], p|g[1], c+g[3], b+g[2], used | ECODES[g])
            rec(0, k0, tm, pm, cr, 0.0, bc)
    return best[0], found[0], nodes[0], time.time()-t0

if __name__ == '__main__':
    defer = tuple(sys.argv[1:])
    b, f, n, el = run(defer)
    print(f"defer={defer}  cost={sum(R3.DEFER[x] for x in defer):.1f}  "
          f"nodes={n:,}  {el:.0f}s")
    print(f"  -> {'BEATS' if f else 'cannot beat'} incumbent {INCUMBENT}" +
          (f", new best {b:.2f}" if f else ""))
