import os,sys,json,io,contextlib,time
os.chdir('/root/audit'); sys.path.insert(0,'/root/audit')
os.environ.setdefault('MAX_FREE','2'); os.environ.setdefault('D_LANG','10.0')
import fallback as FB
import research_v3 as RV
import rank3, fm_fix, eligibility, rank2 as R2
RV.MAX_FREE=2
RV.STATE=os.path.join('/root/audit','_audit_tmp'); os.makedirs(RV.STATE,exist_ok=True)
FB.TOPN_SEARCH=3000
t0=time.time()
Pp,sig,sigs,SIGCODES,code = rank3.build()
fm_fix.apply(Pp,verbose=False); eligibility.apply(Pp,verbose=False)
ZERO={c[:7] for c,s in {x['c']:x for v in Pp.values() for x in v}.items() if s['fm']==0 and s['tm']}
for pool in Pp.values(): pool[:] = [s for s in pool if s['code'] not in ZERO]
LANGP=[s for s in Pp['OPEN'] if code(s) in R2.LANG]
ELEC=[s for s in Pp['OPEN'] if code(s) not in R2.LANG]
REQ={'MR':Pp['MR'],'WCiv':Pp['WCiv'],'LHP':Pp['LHP'],'SciRD':Pp['SciRD'],'Lang':LANGP}
res={}
for b in FB.B:
    RV.TOPN=3000
    buf=io.StringIO()
    with contextlib.redirect_stdout(buf):
        RV.run_branch(b,Pp,REQ,ELEC,code)
    rows=json.load(open(os.path.join(RV.STATE,f'part_{b}.json'),encoding='utf-8'))['rows']
    best=None
    for r in rows:
        v=r['score']+sum(FB.unit_cost(i) for i in r['items'])
        if best is None or v>best[0]: best=(v,r)
    res[b]={'pre_K':round(best[0],3),'row':best[1],'n_rows':len(rows)}
    print(f"branch {b:6s}  max(score+Σunit_cost) = {best[0]:9.3f}   [{time.time()-t0:.0f}s]",flush=True)
json.dump(res,open('/root/audit/_branchmax.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
