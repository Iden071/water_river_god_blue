# -*- coding: utf-8 -*-
"""Recompute k_real's K with pools_past.parse corrected to build_canonical semantics."""
import sys, os, json, time, collections
os.chdir('/root/audit'); sys.path.insert(0,'/root/audit')
import pools_past as PP
from _fixparse import parse_fixed
MODE = sys.argv[1]            # 'broken' | 'fixed'
YEARS = sys.argv[2].split(',') if len(sys.argv)>2 else ['2026']
if MODE=='fixed':
    PP.parse = parse_fixed
import b1_curve as B
import difficulty as DIFF
import k_real as KR
KR.PP = PP

out = {'base':{}, 'k':{}}
t0=time.time()
for name,(codes,camp,sea) in KR.CASES.items():
    if name not in ('Lang·hard','MR','WCiv','LHP','SciRD'): continue
    for y in YEARS:
        pool,_ = PP.pool(camp,sea,years=[y])
        if not pool: continue
        bk=f"{camp}|{sea}|{y}|5"
        if bk not in out['base']:
            v,_n,ok = B.best_week([],5,pool,node_cap=30_000_000)
            out['base'][bk]=[v,ok]
            print(f"  base {bk}: {v:8.3f} {'exact' if ok else 'BOUND'} [{time.time()-t0:.0f}s]",flush=True)
        geos = KR.geometries(codes,camp,sea)
        for g,seen in geos.items():
            kk=f"{name}|{y}|{PP.show(g[0])}|4"
            v,_n,ok = B.best_week([g],4,pool,node_cap=30_000_000)
            b,okb = out['base'][bk]
            out['k'][kk]=[None if v is None else round(b-v,3), bool(ok and okb), sorted(seen)]
            print(f"  {kk:38s} K={out['k'][kk][0]}  exact={out['k'][kk][1]} [{time.time()-t0:.0f}s]",flush=True)
        json.dump(out, open(f'/root/audit/_k_{MODE}.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(out, open(f'/root/audit/_k_{MODE}.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
print("DONE", time.time()-t0)
