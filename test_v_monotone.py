# -*- coding: utf-8 -*-
"""test_v_monotone.py — R213. Is the simulated V MONOTONE in the remainder?

Adding one more required item to the future cannot make the future BETTER. If
V(rem + item) > V(rem), the simulated continuation is broken, and any comparison that
defers more items is reading a bug as a recommendation.

This is the same class of test as the fast_score monotonicity proof (R? / _crowd_curve)
and the filler-pool bug: a constraint must never improve the objective.
"""
import copy, sys
import continuation_sim as CS
from defer_value2 import remainder_after, ALL_REQS

base_taken = ['MR', 'WCiv', 'LHP', 'SciRD']          # the 'defer Lang' remainder
rem0 = remainder_after(base_taken, [], chapel=True)
rem0['ME'] = max(0, rem0['ME'] - 1)
rem0['ME'] = max(0, rem0['ME'] - 1)

r0 = CS.best_plan(rem0)
print(f"base remainder (defer Lang, electives ME+ME):  V = {r0['value']:.3f}")
print(f"  {dict((k, v) for k, v in sorted(rem0.items()) if v)}")
print()

bad = 0
for extra in ['LHP', 'WCiv', 'SciRD', 'MR5', 'ME', 'ECO1101', 'FREE']:
    rem = dict(rem0)
    rem[extra] = rem.get(extra, 0) + 1
    r = CS.best_plan(rem)
    if r is None:
        print(f"  +{extra:8s} INFEASIBLE")
        continue
    d = r['value'] - r0['value']
    flag = ''
    if d > 1e-6:
        flag = '  <-- ⛔ ADDING WORK IMPROVED THE FUTURE'
        bad += 1
    print(f"  +{extra:8s} V = {r['value']:9.3f}   delta {d:+9.3f}{flag}")


# ---------------------------------------------------------------------------
# ⭐ WHY 'defer Lang+LHP' HAS A *HIGHER* V THAN 'defer Lang'
# Both Falls hold 6 academic courses, so both remainders hold the same NUMBER of items —
# the composition differs. Decompose the difference one item at a time.
# ---------------------------------------------------------------------------
print()
print("=" * 78)
print("DECOMPOSITION: 'defer Lang' remainder -> 'defer Lang+LHP' remainder")
print("=" * 78)
steps = [('+LHP', 'LHP', +1), ('+ME', 'ME', +1), ('-ECO1101', 'ECO1101', -1),
         ('-FREE', 'FREE', -1)]
rem = dict(rem0)
prev = r0['value']
for label, k, d in steps:
    rem[k] = rem.get(k, 0) + d
    r = CS.best_plan(rem)
    v = r['value'] if r else float('nan')
    print(f"  {label:10s} V = {v:9.3f}   step {v - prev:+9.3f}")
    prev = v
print(f"  -> the 'defer Lang+LHP' remainder is worth {prev:.3f}")

print()
if bad:
    print(f"❌ {bad} violations. The simulated V is NOT monotone — the defer-two result is "
          f"not trustworthy.")
    sys.exit(1)
print("✅ monotone: every added item costs. Deferring more can only lower V.")
