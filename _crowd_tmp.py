# Measure: best SCHEDULE-ONLY value achievable as a function of how many
# constrained requirements the semester carries. No DEFER, no chapel bonus.
import csv, json, collections
import rank as RK, rank2 as R2, rank3
from rank2 import fast_score, eff_year, YEAR_PEN

P, sig, sigs, SIGCODES, code = rank3.build()
byc = {s['c']: s for v in P.values() for s in v}
DEFER = json.load(open('defer_costs.json', encoding='utf-8'))

rows = list(csv.DictReader(open('FINAL_ranked3.csv', encoding='utf-8-sig')))
best = {}
for r in rows:
    d = r['deferred']
    if d not in best or float(r['score']) > float(best[d]['score']): best[d] = r

print(f"{'defer':8s} {'#req':>4} {'score':>8} {'sched':>8} {'bonus':>7} {'yrpen':>7} {'dcost':>8} {'chapel':>7}")
for d, r in sorted(best.items(), key=lambda kv: -float(kv[1]['score'])):
    codes = r['requirements'].split() + r['electives'].split()
    tm = pm = 0
    for c in codes:
        s = byc[c]; tm |= s['tm']; pm |= s['pm']
    ch = r['chapel']
    if ch and ch != '-':
        s = byc[ch]; tm |= s['tm']; pm |= s['pm']
    sched, det = fast_score(tm, pm)
    bonus = sum(byc[c].get('_role', 0.0) for c in r['electives'].split())
    yrpen = sum(YEAR_PEN(eff_year(byc[c], code)) for c in codes)
    dfset = [] if d == '-' else d.split('+')
    dcost = (10.0 if (ch and ch != '-') else DEFER['Chapel']) + sum(DEFER[n] for n in dfset)
    nreq = 5 - len(dfset)
    print(f"{d:8s} {nreq:4d} {float(r['score']):8.3f} {sched:8.3f} {bonus:7.2f} "
          f"{yrpen:7.2f} {dcost:8.3f} {'yes' if ch and ch!='-' else 'no':>7}")
    print(f"         check: sched+bonus+yrpen+dcost = "
          f"{sched+bonus+yrpen+dcost:.3f}")
