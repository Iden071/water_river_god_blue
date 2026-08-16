# -*- coding: utf-8 -*-
"""
sweep_difficulty.py — find the SWITCHING THRESHOLD for the language difficulty weight.

The method, which is the point of the file:
  `D_LANG` has never been elicited, and "what is a hard language worth in schedule points?"
  is not a question Iden can answer (R141 — ask about states, never about weights). So
  instead of guessing it or omitting the axis, sweep it and report where the ANSWER changes.
  That converts the question into "is it more or less than X", which is answerable.

Two channels, both real:
  1. TAKE a hard-tier language now      -> costs 1.0 x D_LANG
  2. DEFER Language                     -> costs P(hard) x D_LANG, because from 2학년 Iden
     bids mileage for a 2-seat 분반 of the easy tier and loses it most of the time
     (difficulty.p_hard_if_deferred(), measured at 0.692 from 13 국제 observations).

Channel 2 is what makes this a real trade rather than a penalty: deferring does not avoid
the hard tier, it just makes it probable instead of certain.
"""
import csv, os, json
import difficulty as DIFF

HERE = os.path.dirname(os.path.abspath(__file__))
P_HARD = DIFF.p_hard_if_deferred()
rows = list(csv.DictReader(open(os.path.join(HERE, 'FINAL_ranked4.csv'),
                                encoding='utf-8-sig')))


def channels(r):
    """(base score at D_LANG=0, difficulty steps charged per unit of D_LANG)."""
    codes = r['requirements'].split() + r['electives'].split()
    taken_steps = sum(DIFF.steps(c) for c in codes)
    deferred = 'Lang' in (r['deferred'].split('+') if r['deferred'] != '-' else [])
    return float(r['score']), taken_steps + (P_HARD if deferred else 0.0)


CH = [channels(r) for r in rows]


def rank_at(D):
    sc = [(b - s * D, i) for i, (b, s) in enumerate(CH)]
    sc.sort(key=lambda x: -x[0])
    return sc


def label(i):
    r = rows[i]
    lang = [c for c in r['requirements'].split() + r['electives'].split()
            if c[:7] in DIFF.LANG_ALL]
    tier = ('HARD ' + lang[0][:7]) if lang and lang[0][:7] in DIFF.LANG_HARD else \
           ('easy ' + lang[0][:7]) if lang else 'defers Language'
    return (f"defer={r['deferred']:6s} {tier:16s} | "
            f"{' '.join(c[:7] for c in r['requirements'].split())} | "
            f"{' '.join(c[:7] for c in r['electives'].split())}")


if __name__ == '__main__':
    print(f"P(hard tier | Language deferred) = {P_HARD:.3f}   "
          f"(measured, difficulty.py)")
    print(f"scale reminder: one 9:00 start = -10\n")

    print("HOW #1 CHANGES AS THE DIFFICULTY WEIGHT RISES")
    print(f"  {'D_LANG':>7}  {'#1 score':>9}  #1")
    prev = None
    switches = []
    for D in [x * 0.25 for x in range(0, 81)]:
        top = rank_at(D)[0]
        if top[1] != prev:
            if prev is not None:
                switches.append(D)
            print(f"  {D:7.2f}  {top[0]:9.3f}  {label(top[1])}")
            prev = top[1]
    print()
    if switches:
        print(f"⭐ THE ANSWER CHANGES AT D_LANG ≈ {switches[0]:.2f}"
              + (f", and again at {', '.join(f'{s:.2f}' for s in switches[1:])}"
                 if len(switches) > 1 else ""))
    else:
        print("no switch anywhere in the swept range")
    print()
    print("THE ONLY QUESTION LEFT FOR IDEN")
    print(f"  Is one step of 'really learning the language, pretty hard' worth more or")
    print(f"  less than {switches[0]:.2f} points, where one 9:00 start = 10?")
    print(f"  more  -> defer Language      (the easy tier now, cheaply, is not on offer)")
    print(f"  less  -> take a hard language this Fall and defer SciRD instead")
