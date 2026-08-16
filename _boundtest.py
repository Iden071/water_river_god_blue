import os,sys,json,random,inspect,io,contextlib
os.chdir('/root/audit'); sys.path.insert(0,'/root/audit')
os.environ['MAX_FREE']='2'; os.environ['D_LANG']='10.0'
import research_v3 as RV, rank2 as R2, difficulty as DIFF
import prof as PROF
SYNTH = sys.argv[1] if len(sys.argv)>1 else 'none'
P,REQ,ELEC,code=RV.build()
if SYNTH=='synth':
    rng0=random.Random(11)
    allsec=[s['c'] for v in P.values() for s in v]
    names=sorted({PROF.prof_of(c) for c in allsec})
    PROF._RATINGS = {n: rng0.choice([-1.0,-0.5,0.0,0.5,1.0]) for n in names if n!='(none)'}
    print(f"synthetic ratings injected for {len(PROF._RATINGS)} professors")
print("PROF ratings:",len(PROF.ratings()),"bonus range:",
      min([PROF.bonus(c) for v in P.values() for s in v for c in [s['c']]]),
      max([PROF.bonus(c) for v in P.values() for s in v for c in [s['c']]]))
src=inspect.getsource(RV.run_branch)
line='if week_value(p, f)[0] + b + k * PBMAX + pen + dif + pb + ch_c <= best[0]:\n                    return'
assert line in src
nob=src.replace(line,'if False:\n                    return').replace('def run_branch(','def run_branch_nobound(')
ns=dict(RV.__dict__); exec(compile(nob,'<nb>','exec'),ns); run_nb=ns['run_branch_nobound']
rng=random.Random(7); RV.TOPN=200000
for trial in range(3):
    Ps={k:list(v) for k,v in P.items()}
    RQ={n_:rng.sample(v,min(len(v),5)) for n_,v in REQ.items()}
    Ps['Chapel']=rng.sample(P['Chapel'],min(len(P['Chapel']),3))
    EL=rng.sample(ELEC,min(len(ELEC),60))
    for b in ('MR','Lang','WCiv','SciRD'):
        got={}
        for tag,fn in (('bound',RV.run_branch),('nobound',run_nb)):
            st=os.path.join('/root/audit',f'_bt_{tag}'); os.makedirs(st,exist_ok=True)
            RV.STATE=st; ns['STATE']=st
            with contextlib.redirect_stdout(io.StringIO()): fn(b,Ps,RQ,EL,code)
            rows=json.load(open(os.path.join(st,f'part_{b}.json'),encoding='utf-8'))['rows']
            got[tag]=(rows[0]['score'] if rows else None, len(rows))
        a,c=got['bound'],got['nobound']
        bad = a[0] is not None and c[0] is not None and c[0]>a[0]+1e-6
        print(f"trial {trial} {b:6s} bound_best={a[0]} nobound_best={c[0]} rows {a[1]}/{c[1]}"
              f"{'   ⛔ BOUND UNSOUND' if bad else '   ok'}",flush=True)
