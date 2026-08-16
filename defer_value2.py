# -*- coding: utf-8 -*-
"""
defer_value2.py — the computed replacement for `defer_costs.json` (G-2).

For each thing Fall 2026 might leave undone, compute V(remainder) with continuation.py
and report the DIFFERENCE. That difference is the deferral cost — derived from where the
course can actually land and what it does to those semesters, not fitted to an anchor.

Also answers R181 directly: what does spending a Fall-2026 slot on a free elective cost,
given the elective itself scores 0? Answer: V drops by whatever the displaced requirement
would have cost to place later. Nothing is charged to the elective.

Run:  python defer_value2.py
"""
import json, time, os
from continuation import solve, full_remaining
from plan_model import ITEMS

HERE = os.path.dirname(os.path.abspath(__file__))

# Which ledger item does a Fall-2026 course satisfy?
#   requirement-slot name (rank3's REQ keys) -> ledger key
REQ_TO_ITEM = {'MR': 'QRM1001', 'WCiv': 'WCiv', 'LHP': 'LHP',
               'SciRD': 'SciRD', 'Lang': 'Lang'}

# elective course code -> ledger key it advances (anything unlisted advances FREE)
ELECTIVE_TO_ITEM = {
    'ECO1101': 'ECO1101',    # MR, and the only other MR reachable this Fall
    'STA2102': 'ME',         # QRM ME (R102/R152)
    'QRM2001': 'ME', 'QRM2002': 'ME', 'QRM2004': 'ME', 'QRM2102': 'ME',
    'QRM3001': 'ME', 'QRM3007': 'ME', 'QRM4807': 'ME', 'QRM4808': 'ME',
    'QRM4809': 'ME',
    # ⛔ ECO1103 / ECO1104 REMOVED 2026-08-09. VERIFY 22 says the COURSES are QRM ME;
    # VERIFY 22b — parked, still open — asks whether SECTIONS QRM did not list count.
    # The pool answers it for the section that actually mattered: ECO1104-07-00 has
    # qcat=None and _qrm_me=False. Listing them here overrode the data and flipped #1.
}


def remainder_after(taken_reqs, elective_codes, chapel=True):
    """Ledger remaining after a Fall 2026 timetable."""
    rem = full_remaining()
    for r in taken_reqs:
        k = REQ_TO_ITEM[r]
        rem[k] = max(0, rem[k] - 1)
    for c in elective_codes:
        k = ELECTIVE_TO_ITEM.get(c[:7], 'FREE')
        rem[k] = max(0, rem[k] - 1)
    if chapel:
        rem['Chapel'] = max(0, rem['Chapel'] - 1)
    return rem


ALL_REQS = ['MR', 'WCiv', 'LHP', 'SciRD', 'Lang']

if __name__ == '__main__':
    t0 = time.time()
    print("=" * 78)
    print("DEFERRAL COST, COMPUTED  —  V(remainder) for each thing Fall 2026 leaves undone")
    print("=" * 78)
    print("Baseline: Fall 2026 carries all 5 requirements + 1 free elective + chapel.")
    base_rem = remainder_after(ALL_REQS, ['FREE1'])
    base_v, base_plan = solve(base_rem)
    print(f"  V(baseline) = {base_v:9.3f}      [{time.time()-t0:.0f}s]")
    print()
    print(f"  {'defers':8s} {'V(remainder)':>13} {'ΔV vs baseline':>16}   "
          f"{'R117 fitted':>12}   {'difference':>11}")
    print("  " + "-" * 72)
    old = json.load(open(os.path.join(HERE, 'defer_costs.json'), encoding='utf-8'))
    rows = []
    for d in ALL_REQS:
        taken = [r for r in ALL_REQS if r != d]
        # the freed slot is filled by a free elective (this is what the ranker does)
        rem = remainder_after(taken, ['FREE1', 'FREE2'])
        v, _ = solve(rem)
        dv = v - base_v
        rows.append((d, v, dv, old.get(d)))
        print(f"  {d:8s} {v:13.3f} {dv:16.3f}   {old.get(d, float('nan')):12.3f}   "
              f"{dv - old.get(d, 0):11.3f}")
    print()
    print("=" * 78)
    print("R181 — WHAT DOES A FREE ELECTIVE SLOT COST?  (the elective still scores 0)")
    print("=" * 78)
    print("Fall 2026 keeps all 5 requirements; the 6th slot is either a free elective")
    print("or a course that advances a real quota. Nothing is charged to the elective —")
    print("the difference is entirely in what the remaining six semesters inherit.")
    print()
    print(f"  {'6th slot':28s} {'V(remainder)':>13} {'vs free elective':>18}")
    print("  " + "-" * 62)
    ref = None
    for label, code in [('free elective', 'FREE1'),
                        ('ECO1101 (MR)', 'ECO1101'),
                        ('a QRM major elective', 'QRM2004')]:
        rem = remainder_after(ALL_REQS, [code])
        v, _ = solve(rem)
        if ref is None:
            ref = v
        print(f"  {label:28s} {v:13.3f} {v - ref:18.3f}")
    print(f"\n  [{time.time()-t0:.0f}s]")
