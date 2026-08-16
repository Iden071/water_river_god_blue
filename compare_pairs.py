# -*- coding: utf-8 -*-
"""compare_pairs.py — R212b. Corrected total for the DEFER-TWO branches.

Reads `_rank4_parts/part_<A>+<B>.json` directly (these pairs are deliberately NOT in
BRANCHES, so they are not merged into FINAL_ranked4.csv and cannot contaminate it).

For each elective-item multiset in the branch, take the BEST proxy score, strip the proxy
continuation (dV) to recover r(x), and add the SIMULATED V for that same remainder. Grouping
by item multiset matters: V_sim depends only on (deferral set, items), so the best corrected
row need not be the best proxy row.
"""
import json, os, glob, collections
import rank4, continuation_sim as CS
from defer_value2 import remainder_after, ALL_REQS

HERE = os.path.dirname(os.path.abspath(__file__))
V_REF = rank4.v_ref()

print("=" * 88)
print("DEFER-TWO BRANCHES — corrected total   (r(x) recovered from the part file)")
print("=" * 88)
rows_out = []
for path in sorted(glob.glob(os.path.join(HERE, '_rank4_parts', 'part_*+*.json'))):
    name = os.path.basename(path)[5:-5]
    d = json.load(open(path, encoding='utf-8'))
    if not d.get('rows'):
        print(f"{name:14s} EMPTY — ceiling below floor {d.get('floor')}")
        continue
    dfset = frozenset(name.split('+'))
    bygroup = {}
    for r in d['rows']:
        k = tuple(sorted(r['elective_items']))
        if k not in bygroup or r['score'] > bygroup[k]['score']:
            bygroup[k] = r
    best = None
    for items, r in bygroup.items():
        dV = rank4.V((dfset, items)) - V_REF
        rx = r['score'] - dV
        taken = [x for x in ALL_REQS if x not in dfset]
        rem = remainder_after(taken, [], chapel=True)
        for k in items:
            rem[k] = max(0, rem[k] - 1)
        res = CS.best_plan(rem)
        v = res['value'] if res else float('-inf')
        tot = rx + v
        if best is None or tot > best[0]:
            best = (tot, rx, v, dV, r['score'], items, r)
    tot, rx, v, dV, sc, items, r = best
    print(f"{name:14s} proxy {sc:8.3f}  dV {dV:8.3f}  r(x) {rx:8.3f}  V(sim) {v:8.3f}"
          f"  TOTAL {tot:8.3f}   {'+'.join(items)}")
    rows_out.append(dict(branch=name, total=tot, rx=rx, v=v, dV=dV, ranked=sc,
                         items=list(items)))
json.dump(rows_out, open(os.path.join(HERE, 'pairs_corrected.json'), 'w'), indent=1)

sing = json.load(open(os.path.join(HERE, 'branch_corrected.json'), encoding='utf-8'))
allr = sorted(sing + rows_out, key=lambda x: -x['total'])
print()
print("ALL BRANCHES MEASURED SO FAR, corrected order:")
for i, r in enumerate(allr, 1):
    print(f"  {i:2d}. defer={r['branch']:12s} {r['total']:9.3f}"
          f"   (r(x) {r['rx']:7.3f} + V {r['v']:7.3f})")
