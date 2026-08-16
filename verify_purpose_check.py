# -*- coding: utf-8 -*-
"""Recompute #1 from PURPOSE_CHECK's stated formulas and constants ONLY.
Imports rank3 for the section data and continuation for V, but NO scoring code:
every weight and every formula below is transcribed from the document, not imported."""
import json, csv, os
import rank3, rank4
from continuation import solve
from defer_value2 import remainder_after, ALL_REQS

# --- constants exactly as written in PURPOSE_CHECK_2026-08-10.md -----------------
W_E1,W_E2,W_LUNCH,W_DINNER = -10.0,-5.0,-6.0,-8.0
MARATHON = lambda L: -(8.0+0.8*(L-4)**2) if L>=4 else 0.0
LATE     = lambda last: -((last-8)**1.4307) if last>=9 else 0.0
HOLE     = lambda L: -10.0*(L/4.0)**2
DAY_CONTIG, RUN_EXP, REST, FRI_EVENT = 13.00, 1.4, 7.00, 4.333
EVENT_WINDOW = range(6,12)
EARLY_K, LATE_K, YEAR_EXP = 4.0, 4.0/1.5, 2.5
CHAPEL_BONUS, CHAPEL_DEFER = 10.0, -4.2
D_LANG = 10.0
LANG_HARD={'YCF1301','YCF1351','YCF1451','YCF1501','YCF1551','YCF1601','YCF1603','YCF1607'}
QRM_CHART_YEAR={'STA1001':1,'QRM1001':1,'ECO1101':1,'ECO1103':1,'ECO1104':1,
 'QRM2001':2,'QRM2002':2,'QRM2004':2,'QRM2100':2,'QRM2101':2,'QRM2102':2,'ECO2101':2,
 'ECO2102':2,'STA2102':2,'STA2104':2,'STA2105':2,'ECO1105':2,'QRM3001':3,'QRM3002':3,
 'QRM3003':3,'QRM3004':3,'QRM3005':3,'QRM3007':3,'ECO3104':3,'ECO3127':3,'ECO3130':3,
 'ECO3134':3,'QRM4001':4,'QRM4807':4,'QRM4808':4,'QRM4809':4,'STA4103':4,'ECO4115':4,
 'ECO4862':4,'ECO4865':4}
import re
def year_of(yr):
    n=[int(x) for x in re.findall(r'\d+', yr or '') if x!='0']
    return min(n) if n else 0
def pi(y):
    if not y: return 0.0
    d=1-y
    if d==0: return 0.0
    return -(EARLY_K if d<0 else LATE_K)*abs(d)**YEAR_EXP

def day_penalty(m):
    if not m: return 0.0
    sc=0.0; first=(m&-m).bit_length()-1; last=m.bit_length()-1
    if first==1: sc+=W_E1
    elif first==2: sc+=W_E2
    if all((m>>p)&1 for p in (3,4,5)): sc+=W_LUNCH
    if last>=9: sc+=LATE(last)
    if all((m>>p)&1 for p in (9,10,11)): sc+=W_DINNER
    run=gap=0
    for p in range(first,last+2):
        if p<=last and (m>>p)&1:
            if gap: sc+=HOLE(gap); gap=0
            run+=1
        else:
            if run>=4: sc+=MARATHON(run)
            run=0
            if p<=last: gap+=1
    return sc

P,sig,sigs,SIGCODES,code=rank3.build()
byc={s['c']:s for v in P.values() for s in v}
HERE='/sessions/awesome-blissful-hypatia/mnt/수강신청'
r=list(csv.DictReader(open(HERE+'/FINAL_ranked4.csv',encoding='utf-8-sig')))[0]
reqs=r['requirements'].split(); els=r['electives'].split(); ch=r['chapel']
tm=pm=fm=0
for c in reqs+els+[ch]:
    s=byc[c]; tm|=s['tm']; pm|=s['pm']; fm|=s['fm']

# TRIP
presfree=[not ((pm>>(d*16))&0xffff) for d in range(7)]
run=0
if presfree[5] and presfree[6]:
    run=2
    for d in (4,3,2,1,0):
        if presfree[d]: run+=1
        else: break
    if run<7:
        for d in (0,1,2,3,4):
            if presfree[d]: run+=1
            else: break
    run=min(run,7)
trip=DAY_CONTIG*(run-2)**RUN_EXP if run>2 else 0.0
rest=REST*sum(1 for d in range(5) if not ((fm>>(d*16))&0xffff))
fri=0.0
if presfree[4]:
    f=(fm>>(4*16))&0xffff
    if not any((f>>p)&1 for p in EVENT_WINDOW): fri=FRI_EVENT
wv=trip+rest+fri
dp=sum(day_penalty((fm>>(d*16))&0xffff) for d in range(7))
week=wv+dp
yr=sum(pi(QRM_CHART_YEAR.get(code(byc[c])) or year_of(byc[c].get('yr'))) for c in reqs+els)
chap=CHAPEL_BONUS
dif=-D_LANG*sum(1 for c in reqs+els if code(byc[c]) in LANG_HARD)

ITEM=json.load(open(HERE+'/elective_items.json',encoding='utf-8'))
dfset=frozenset(r['deferred'].split('+'))
items=tuple(sorted(ITEM.get(c,'FREE') for c in els))
taken=[x for x in ALL_REQS if x not in dfset]
rem=remainder_after(taken,[],chapel=True)
for k in items: rem[k]=max(0,rem[k]-1)
V,_=solve(rem)
rem0=remainder_after(ALL_REQS,[],chapel=True)
for k in ('FREE','FREE'): rem0[k]=max(0,rem0[k]-1)
V0,_=solve(rem0)
dV=V-V0
total=week+yr+chap+dif+dV

print("RECOMPUTED FROM THE DOCUMENT'S OWN CONSTANTS AND FORMULAS")
print(f"  trip (run={run})            {trip:10.3f}   doc says  34.307")
print(f"  rest                       {rest:10.3f}   doc says   7.000")
print(f"  friday event               {fri:10.3f}   doc says   4.333")
print(f"  week_value                 {wv:10.3f}   doc says  45.640")
print(f"  day penalties              {dp:10.3f}   doc says -27.750")
print(f"  week                       {week:10.3f}   doc says  17.890")
print(f"  year gap                   {yr:10.3f}   doc says  -4.000")
print(f"  chapel                     {chap:10.3f}   doc says  10.000")
print(f"  difficulty                 {dif:10.3f}   doc says   0.000")
print(f"  V(remainder)               {V:10.3f}   doc says 260.561")
print(f"  V(reference)               {V0:10.3f}   doc says 123.874")
print(f"  dV                         {dV:10.3f}   doc says 136.687")
print(f"  ------------------------------------")
print(f"  TOTAL                      {total:10.3f}")
print(f"  FINAL_ranked4.csv reports  {float(r['score']):10.3f}")
ok=abs(total-float(r['score']))<1e-3
print("\n"+("✅ the document reproduces the live #1 exactly." if ok else
      f"❌ MISMATCH of {total-float(r['score']):.4f} — the document is wrong."))
