# -*- coding: utf-8 -*-
"""Does the 신촌 PREFERENCE (R200) change the Fall 2026 decision?"""
import subprocess, sys, json, os
HERE = os.path.dirname(os.path.abspath(__file__))

def top_at(v):
    code = r'''
import os, csv, json
os.environ['SINCHON_SEMESTER_VALUE'] = %r
import rank2 as R2, difficulty as D
R2.LANG = set(D.LANG_ALL)
import rank3, rank4, continuation
from rank2 import fast_score, eff_year, YEAR_PEN
P = rank3.build()[0]
byc = {s['c']: s for v in P.values() for s in v}
cf = lambda s: s['code']
ITEM = json.load(open('elective_items.json', encoding='utf-8'))
rank4._VC.clear()
VREF = rank4.v_ref()
rows = list(csv.DictReader(open('FINAL_ranked4.csv', encoding='utf-8-sig')))[:600]
out = []
for r in rows:
    reqs = r['requirements'].split(); els = r['electives'].split()
    tm = pm = 0
    for c in reqs + els:
        s = byc[c]; tm |= s['tm']; pm |= s['pm']
    ch = r['chapel']; has = bool(ch and ch != '-')
    if has:
        s = byc[ch]; tm |= s['tm']; pm |= s['pm']
    w, _ = fast_score(tm, pm)
    yr = sum(YEAR_PEN(eff_year(byc[c], cf)) for c in reqs + els)
    chap = rank4.CHAPEL_BONUS if has else rank4.CHAPEL_DEFER
    dif = -D.D_LANG * D.GPA_GATE_MULT * sum(D.steps(c) for c in reqs + els)
    df = frozenset() if r['deferred'] == '-' else frozenset(r['deferred'].split('+'))
    if 'Lang' in df:
        dif -= D.p_hard_if_deferred()[1] * D.D_LANG
    items = tuple(sorted(ITEM.get(c, 'FREE') for c in els))
    out.append((w + yr + chap + dif + (rank4.V((df, items)) - VREF), r['deferred'],
                ' '.join(c[:7] for c in reqs), ' '.join(c[:7] for c in els)))
out.sort(key=lambda x: -x[0])
print(json.dumps(out[:1]))
''' % str(v)
    p = subprocess.run([sys.executable, '-c', code], cwd=HERE, capture_output=True,
                       text=True, timeout=150)
    ln = [l for l in p.stdout.strip().split('\n') if l.startswith('[')]
    return json.loads(ln[-1])[0] if ln else None

if __name__ == '__main__':
    print(f"  {'신촌 bonus':>10}  {'#1 score':>9}  #1")
    prev = None; sw = []
    for v in (0, 10, 20, 30, 40, 60, 80, 120):
        t = top_at(v)
        if not t: print(f'  {v:10.0f}  failed'); continue
        sc, d, rq, el = t
        key = (d, rq, el)
        m = ''
        if prev is not None and key != prev: sw.append(v); m = '   <-- CHANGES'
        print(f'  {v:10.0f}  {sc:9.3f}  defer={d:6s} | {rq} | {el}{m}')
        prev = key
    print()
    print(f"threshold(s): {sw}" if sw else "NO THRESHOLD — the 신촌 preference cannot change the 8/25 decision")
