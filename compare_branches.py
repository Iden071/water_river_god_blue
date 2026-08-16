# -*- coding: utf-8 -*-
"""compare_branches.py — R212. Run the CORRECTED continuation on EVERY branch, not two.

⛔ WHY THIS FILE EXISTS. Iden: "You are just comparing A and B traditionally, right? The
scorer doesn't treat the two like C doesn't exist? (both defer / both keep)"

He is right twice.
  1. `continuation_sim.__main__` compared exactly TWO hand-written cases. The ranking has
     SIX branches. 'defer nothing' was never re-measured under the corrected V — and since
     R208's whole finding is that the old objective FLATTERS deferral, the branch that
     defers nothing is precisely the one the correction should help most.
  2. The hand-written B case used elective items ('ECO1101','ME') that do NOT belong to the
     Lang branch — that pair is the WCiv branch's. Read from the CSV, never retyped.

r(x) is recovered from the CSV as  score - dV  (dV is the only continuation term in it),
so the Fall half is exactly what the ranker scored and only V is replaced.
"""
import csv, os, sys, time, json
import rank4, continuation_sim as CS
from defer_value2 import remainder_after, ALL_REQS

HERE = os.path.dirname(os.path.abspath(__file__))
V_REF = rank4.v_ref()
rows = list(csv.DictReader(open(os.path.join(HERE, 'FINAL_ranked4.csv'), encoding='utf-8-sig')))

best = {}
for r in rows:                      # CSV is score-sorted; first hit per branch is its best
    best.setdefault(r['deferred'], r)

print("=" * 92)
print("EVERY BRANCH, CORRECTED CONTINUATION   (r(x) from the ranker, V from real sections)")
print("=" * 92)
print(f"{'branch':10s} {'ranked':>9} {'dV(proxy)':>10} {'r(x)':>9} {'V(sim)':>9} "
      f"{'TOTAL':>9}  {'intl':>4}  electives", flush=True)
out = []
for name, r in sorted(best.items()):
    dfset = frozenset() if r['deferred'] == '-' else frozenset(r['deferred'].split('+'))
    items = tuple(r['elective_items'].split())
    dV = rank4.V((dfset, items)) - V_REF
    rx = float(r['score']) - dV
    taken = [x for x in ALL_REQS if x not in dfset]
    rem = remainder_after(taken, [], chapel=True)
    for k in items:
        rem[k] = max(0, rem[k] - 1)
    t0 = time.time()
    res = CS.best_plan(rem)
    v = res['value'] if res else float('nan')
    n_intl = 1 + sum(1 for c in res['pattern'] if c == '국제') if res else 0
    tot = rx + v
    out.append((tot, name, rx, v, dV, float(r['score']), n_intl))
    print(f"{name:10s} {float(r['score']):9.3f} {dV:10.3f} {rx:9.3f} {v:9.3f} "
          f"{tot:9.3f}  {n_intl:>4}  {r['elective_items']}   [{time.time()-t0:.0f}s]",
          flush=True)

print()
out.sort(reverse=True)
print("CORRECTED ORDER:")
for i, (tot, name, rx, v, dV, sc, ni) in enumerate(out, 1):
    print(f"  {i}. defer={name:8s} {tot:9.3f}")
print()
ranked1 = max(best.items(), key=lambda kv: float(kv[1]['score']))[0]
print(f"  ranked #1 was defer={ranked1}")
print(f"  corrected #1 is defer={out[0][1]}   margin over #2 = {out[0][0]-out[1][0]:+.3f}")
json.dump([dict(branch=n, total=t, rx=rx, v=v, dV=dV, ranked=sc, n_intl=ni)
           for t, n, rx, v, dV, sc, ni in out],
          open(os.path.join(HERE, 'branch_corrected.json'), 'w'), indent=1)
