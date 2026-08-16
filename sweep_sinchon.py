# -*- coding: utf-8 -*-
"""
sweep_sinchon.py — what is the 신촌 free-day rule worth, and does Fall 2026 care?

WHAT A "SWEEP" AND A "THRESHOLD" MEAN — Iden asked, so plainly:
---------------------------------------------------------------
An unknown constant is not asked for directly. Instead it is set to every plausible value in
turn, the whole ranking is recomputed at each one, and the output is the value where the
ANSWER changes — the threshold. Three things can come out:

  1. no threshold in the plausible range  -> the constant CANNOT change the decision, and
                                             Iden never has to answer. This happened to
                                             RUN_EXP (R160) and the dinner penalty (R174).
  2. one threshold                        -> the question collapses to "is it more or less
                                             than X", which is answerable. This is how
                                             D_LANG went from unanswerable to "more or less
                                             than 3.25" (R187).
  3. the elicited value lands ON one      -> the model genuinely cannot separate the options
                                             and must say so (R188).

Sweeping BEFORE asking also reveals how much precision the answer needs — which is itself a
finding, and R188 is the case where a human could not supply enough.

WHAT IS BEING SWEPT HERE
------------------------
Iden gave the SHAPE, not the size: *"days of the week have no difference from each other,
isolated or not"* at 신촌, because he commutes from home daily and every free day saves a
round trip. So 신촌's crowding cost is LINEAR per occupied day, where 국제's is convex
(measured: 0.00, 19.64, 17.29, 24.21, 31.17).

`SINCHON_PER_COURSE` is the size of that linear step. It has never been elicited.
"""
import csv, os, subprocess, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
VALUES = [0, 5, 10, 14, 18.464, 22, 26, 31, 36, 45]   # 18.464 = the neutral default


def score_at(v):
    """Rescore the live candidate set with SINCHON_PER_COURSE = v, in a fresh process so the
    module-level constant is genuinely re-read."""
    code = r'''
import os, csv, json
VAR = %r

os.environ[VAR] = %r
import rank2 as R2, difficulty as D
R2.LANG = set(D.LANG_ALL)
import rank3, rank4, continuation
from rank2 import fast_score, eff_year, YEAR_PEN
P = rank3.build()[0]
byc = {s['c']: s for v in P.values() for s in v}
code_of = lambda s: s['code']
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
    week, _ = fast_score(tm, pm)
    yr = sum(YEAR_PEN(eff_year(byc[c], code_of)) for c in reqs + els)
    chap = rank4.CHAPEL_BONUS if has else rank4.CHAPEL_DEFER
    dif = -D.D_LANG * D.GPA_GATE_MULT * sum(D.steps(c) for c in reqs + els)
    df = frozenset() if r['deferred'] == '-' else frozenset(r['deferred'].split('+'))
    if 'Lang' in df:
        dif -= D.p_hard_if_deferred()[1] * D.D_LANG
    items = tuple(sorted(ITEM.get(c, 'FREE') for c in els))
    out.append((week + yr + chap + dif + (rank4.V((df, items)) - VREF), r['deferred'],
                ' '.join(c[:7] for c in reqs), ' '.join(c[:7] for c in els)))
out.sort(key=lambda x: -x[0])
print(json.dumps(out[:3]))
''' % str(v)
    p = subprocess.run([sys.executable, '-c', code], cwd=HERE,
                       capture_output=True, text=True, timeout=150)
    line = [l for l in p.stdout.strip().split('\n') if l.startswith('[')]
    if not line:
        return None
    return json.loads(line[-1])


if __name__ == '__main__':
    import continuation
    print(f"국제 increments (measured, convex): "
          f"{[round(x,2) for x in continuation._raw_inc]}")
    print(f"신촌 is LINEAR per Iden — sweeping the step size\n")
    print(f"  {'신촌 step':>10}  {'#1 score':>9}  #1")
    print("  " + "-" * 88)
    prev, switches = None, []
    for v in VALUES:
        top = score_at(v)
        if not top:
            print(f"  {v:10.2f}  (failed)"); continue
        sc, defer, reqs, els = top[0]
        key = (defer, reqs, els)
        mark = ''
        if prev is not None and key != prev:
            switches.append(v); mark = '   <-- ANSWER CHANGES'
        print(f"  {v:10.2f}  {sc:9.3f}  defer={defer:6s} | {reqs} | {els}{mark}")
        prev = key
    print()
    if switches:
        print(f"⭐ threshold(s) at 신촌 step = {switches}")
    else:
        print("⭐ NO THRESHOLD anywhere in the swept range.")
        print("   The 신촌 free-day rule cannot change the Fall 2026 decision, so its size")
        print("   does NOT need to be elicited for 8/25. It still matters for the 4-year")
        print("   plan, and the SHAPE Iden gave (linear) is now in the model either way.")
