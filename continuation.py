# -*- coding: utf-8 -*-
"""
continuation.py — what the rest of the degree is worth, given what Fall 2026 leaves undone.

THE POINT (R181)
----------------
Iden: "Electives not costing anything is probably right. Because the real cost comes from
choosing the elective over some other thing, the opportunity cost."

So this file does not charge electives. It computes the value of the SIX SEMESTERS AFTER
Fall 2026 as a function of the requirement set they inherit. Putting a free elective in a
slot leaves one more requirement in that inheritance, and V goes down by exactly as much as
that requirement costs to place later. The opportunity cost becomes arithmetic.

This replaces `defer_costs.json` (G-2) — seven numbers fitted in R117 to two anchors on a
scale that has since moved twice, and, per R180, the ONLY thing currently separating the
top two timetables.

WHAT V CONTAINS
---------------
  V(remaining) = max over feasible plans of
        Σ_items  year_gap_pen(year_of_semester, chart_year)      <- R145/R146, both arms
      − Σ_sems   crowd(number of low-supply courses in that semester)   <- MEASURED
  and −infinity if no feasible plan exists at all.

Feasibility means: campus matches, term matches, ≤6 courses and ≤18 credits per semester,
≤1 chapel pass per semester, and at least one 국제 Spring for QRM3003 (R144).

⭐ THE LATE ARM OF THE YEAR PENALTY BECOMES LIVE HERE. In `rank2.py`, `YEAR_PEN` hardcodes
`taken_in_year = 1`, so only the "too early" arm can ever fire (R173). The late arm — built
in R146 as the principled replacement for R117 and never reachable since — needs to know
WHICH SEMESTER a deferred course lands in. That is exactly what this file computes.

⚠️ WHAT IS A PROXY, AND SAY SO (G-9)
The crowding curve is measured on the Fall 2026 국제 catalogue (`_crowd_curve.py` →
`crowding.json`). Applying it to a 신촌 semester in 2029 is the right instrument on the
wrong population. It carries the SHAPE (convex, steep after the third course), which is
what the model needs, but its absolute level should not be quoted as a fact about 2029.
"""
import json, itertools, os
import numpy as np
from scipy.optimize import linear_sum_assignment

from plan_model import (SEMESTERS, ITEMS, CREDIT_CAP, MIN_INTL_SEMESTERS,
                        build_semesters, SUMMER_ELIGIBLE_DEFAULT)
from rank2 import year_gap_pen
import risk

KOREAN_ME_COURSE_CAP = 4        # [M] R152/R105 — 4 courses / 12 cr of Korean 상경·응통
                                # sections may count as Major Credit, for the whole degree.
RISK_TARGET_P = 0.8             # the acquisition probability a plan must be able to buy

_BID_CACHE = {}


def item_bid(item):
    """Mileage a semester must spend to acquire one unit of this ledger item.

    Uses risk.min_bid_for on the item's representative course codes, taking the CHEAPEST
    code (he only needs one of them). Returns 0 for items with no mileage evidence — which
    UNDERSTATES cost, so the budget check is conservative in the direction of allowing too
    much rather than forbidding wrongly. Unpriced items are reported by budget_audit().
    """
    k = item['key']
    if k in _BID_CACHE:
        return _BID_CACHE[k]
    best = None
    for code in item.get('codes', []):
        b = risk.min_bid_for(code, RISK_TARGET_P)
        if b is not None and (best is None or b < best):
            best = b
    _BID_CACHE[k] = best or 0
    return _BID_CACHE[k]


def semester_bids(units):
    """{code: bid} for one semester's assigned items. Keyed by ledger key, which is what
    risk.budget_check's ceiling lookup tolerates for unknown codes."""
    out = {}
    for u in units:
        b = item_bid(u)
        if b:
            out[u['key']] = out.get(u['key'], 0) + b
    return out


HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# CROWDING — measured, not assumed
# ---------------------------------------------------------------------------
_c = json.load(open(os.path.join(HERE, 'crowding.json'), encoding='utf-8'))
# best week with n low-supply courses; key '-' is n=0
_by_n = {}
for k, v in _c.items():
    n = 0 if k == '-' else len(k.split('+'))
    _by_n[n] = max(_by_n.get(n, -1e9), v)
_BASE = _by_n[0]
CROWD = {n: _BASE - _by_n[n] for n in sorted(_by_n)}      # cost, 0 at n=0

# incremental cost of the n-th low-supply course
_raw_inc = [CROWD[n] - CROWD[n - 1] for n in range(1, max(CROWD) + 1)]
# The measured increments are convex apart from one inversion (19.64 then 17.29). The
# slot-expansion below is only exact for a CONVEX cost, so take the convex minorant by
# sorting ascending. The distortion is confined to n=2 (19.64 -> 17.29) and is reported.
INC = sorted(_raw_inc)
# a 6th low-supply course is off the measured range (only 5 requirements exist this term).
# Extrapolate by continuing the final gap. Flagged, not hidden.
INC.append(INC[-1] + (INC[-1] - INC[-2]))
EXTRAPOLATED_FROM = len(_raw_inc)

# ⭐ DERIVED 2026-08-09 (R196), not guessed and not elicited cold. Iden answered "not sure"
# when asked for the size directly — correctly, it is not a number a person can produce. So
# it is DERIVED from two values he HAS given:
#
#     a free weekday at 신촌 = not working + not travelling
#         not working    = REST                                  =  7.00  [E]
#         not travelling = a 4-hour round trip (2h each way, HANDOFF §1)
#                          his own price for 4 dead hours = HOLE(4) = 10.00  [E]
#                                                                     ------
#                                                                      17.00
#
# BRACKET [12, 22]: transit may be worse than a campus hole (tiring, twice daily, cannot
# rest) or better (can read on the train). Swept across the whole bracket — #1 is the SAME
# at 12, 17 and 22, so the conclusion does not depend on where inside it the truth sits.
# This is the R146 move: derive from the chart/anchors rather than elicit a seventh constant.
# ⛔ UNIT ERROR CORRECTED 2026-08-09 (R205), found by external audit finding F8.
# The 17.0 is a value PER FREE WEEKDAY. It was being spent PER COURSE. A course is not a
# day: MEASURED over the 341 live sections, a course occupies **1.551 distinct weekdays**
# (45% meet on 1 day, 55% on 2). And six courses need 9.3 day-slots against only 5 weekdays,
# so days SATURATE — which makes 신촌 crowding CONCAVE, not flat.
#
# Treating each course as covering d/5 of the week independently:
#     E[occupied days | n courses] = 5 * (1 - (1 - d/5)^n)
# and the n-th course costs SINCHON_PER_DAY x (the marginal day it opens).
SINCHON_PER_DAY = float(os.environ.get('SINCHON_PER_DAY', 17.0))   # [D] R196
SINCHON_DAYS_PER_COURSE = 1.551                                    # [M] 341 sections
_q = 1.0 - SINCHON_DAYS_PER_COURSE / 5.0
_sin_days = [5.0 * (1.0 - _q ** n) for n in range(7)]
_SIN_RAW = [SINCHON_PER_DAY * (_sin_days[n + 1] - _sin_days[n]) for n in range(6)]
# The slot expansion is exact only for a CONVEX cost, so take the convex minorant — the
# same treatment the 국제 curve already gets. Total per semester is preserved exactly.
SINCHON_INC = sorted(_SIN_RAW)
SINCHON_PER_COURSE = float(os.environ.get('SINCHON_PER_COURSE', SINCHON_PER_DAY))
SINCHON_BRACKET = (12.0, 22.0)

# ---------------------------------------------------------------------------
# ⭐ THE 신촌 FREE-DAY RULE (G-7) — elicited 2026-08-09 (R195)
# ---------------------------------------------------------------------------
# Iden: "신촌 rule is, yes, as per the purpose, days of the week have no difference from
#        each other, isolated or not. Or maybe minimal difference, since connected days do
#        still give some merit. (Friday event bonus still holds.)"
#
# At 국제 he DORMS, so a free day only pays as part of a weekend-connected block worth
# travelling for — hence the convex TRIP term and the measured convex crowding curve.
# At 신촌 he COMMUTES FROM HOME DAILY, so EVERY free day saves a round trip, isolated or not.
#
# Structurally that means: the marginal cost of occupying one more day is CONSTANT at 신촌,
# where at 국제 it is convex. So the crowding curve becomes LINEAR.
#
# ⚠️ SINCHON_PER_COURSE has never been elicited — only its SHAPE has (linear, per Iden).
# It is swept by sweep_sinchon.py, which reports the value at which the Fall 2026 answer
# changes. Default = the mean measured 국제 increment, which keeps the total cost of a full
# semester unchanged and moves only its distribution. That is the neutral choice, not a guess.
SINCHON_LINEAR = os.environ.get('SINCHON_LINEAR', '1') == '1'

# ---------------------------------------------------------------------------
# ⭐ THE 신촌 PREFERENCE (R200) — a stated preference that lived only in prose
# ---------------------------------------------------------------------------
# R126 records Iden calling a 신촌 semester "much much much more preferable", strongly
# enough that one 신촌 semester was said to outrank the entire weekly-schedule range.
# NOTHING in the objective ever expressed it. Left free, V chose 4 국제 / 3 신촌 when the
# minimum FORCED is 2 국제 — it was voluntarily spending two extra 국제 semesters.
#
# This is a per-신촌-semester bonus. Unelicited, so it is swept, not guessed.
# Default 0.0 reproduces the model exactly as it was before this constant existed.
# ⭐ CONFIRMED 2026-08-09 (R201). Shown the scale (9:00 start = 10 · free Friday at 국제 = 20
# · an entirely empty week ~ 96) and told the threshold was 30, Iden reaffirmed R126:
# a 신촌 semester is worth **96+** — it beats any weekly schedule outright.
# Set to 96.0, the "entirely empty week" anchor, as a LOWER bound on what he said.
# ✅ ROBUST: every value >= 40 gives the identical campus plan (2 국제 / 5 신촌, the forced
# minimum) and the identical Fall 2026 answer, so the exact size does not matter.
SINCHON_SEMESTER_VALUE = float(os.environ.get('SINCHON_SEMESTER_VALUE', 96.0))
SLOTS_PER_SEM = 6            # 18 cr / 3 cr
# [P] NEVER JUSTIFIED OR SWEPT. This threshold decides WHICH items incur a crowding cost
# at all, so it silently gates the largest term in V. It was set by eyeballing the measured
# set — the five Fall-2026 requirements have supply 1..35 and all constrain the week;
# electives have 303+ and do not. Nothing has ever tested a value between 40 and 300, and
# the ledger items sit at 1, 2, 3, 4, 9, 15, 20, 35, 38, 422 — so 40 is a real choice with
# real consequences, not a formality. FLAGGED FOR AUDIT.
LOW_SUPPLY_MAX = 40


def expand(remaining):
    """dict {item_key: count} -> flat list of unit items."""
    by_key = {i['key']: i for i in ITEMS}
    units = []
    for k, n in remaining.items():
        if n <= 0:
            continue
        it = by_key[k]
        for _ in range(int(n)):
            units.append(it)
    return units


def full_remaining():
    return {i['key']: i['count'] for i in ITEMS}


def _campus_ok(item, campus):
    return item['campus'] == 'any' or item['campus'] == campus


def _term_ok(item, term):
    return term in item['terms']


def solve(remaining, break_after=None, return_term=None, summers=False,
          summer_eligible=None):
    """Return (value, plan) for the best feasible placement after Fall 2026.

    break_after / return_term : a 휴학 for 병역 (R186). 학년 does NOT advance during a
        leave, so the year-gap costs are unchanged; what moves is TERM PARITY, and that
        decides whether QRM3003 (Spring-only, 국제-only, chart-year 3) has a legal home.
    summers : include 계절학기 sessions, 7 cr / 2 slots each (수강편람 2026-2).
    summer_eligible : which ledger items may be taken in a summer. NO DATA EXISTS for this
        — it is a parameter, and callers should sweep it rather than trust one setting.

    plan = {slot label: [item_key, ...]}.  value = -inf if infeasible.
    """
    if summer_eligible is None:
        summer_eligible = SUMMER_ELIGIBLE_DEFAULT
    sems = build_semesters(break_after, return_term, summers)
    units = [u for u in expand(remaining) if u['key'] != 'Chapel']
    n_chapel = int(remaining.get('Chapel', 0))
    if n_chapel > sum(1 for s in sems if s['kind'] == 'sem'):
        return float('-inf'), None

    best = (float('-inf'), None)
    for pattern in itertools.product(['국제', '신촌'], repeat=len(sems)):
        n_intl = 1 + sum(1 for c, s in zip(pattern, sems)
                         if c == '국제' and s['kind'] == 'sem')
        if n_intl < MIN_INTL_SEMESTERS:
            continue
        # QRM3003 needs a 국제 Spring among the REGULAR semesters. A summer cannot host it.
        if not any(c == '국제' and s['term'] == 'S' and s['kind'] == 'sem'
                   for c, s in zip(pattern, sems)):
            continue

        cols = [(si, slot) for si in range(len(sems))
                for slot in range(sems[si]['slots'])]
        if len(units) > len(cols):
            continue

        BIG = 1e7
        C = np.full((len(units), len(cols)), BIG)
        for ui, u in enumerate(units):
            low = u['supply'] <= LOW_SUPPLY_MAX
            for ci, (si, slot) in enumerate(cols):
                s = sems[si]
                campus = pattern[si]
                if s['kind'] == 'summer':
                    if u['key'] not in summer_eligible:
                        continue
                elif not _term_ok(u, s['term']):
                    continue
                if not _campus_ok(u, campus):
                    continue
                cost = -year_gap_pen(s['year'], u['chart_year'])
                if low:
                    # 국제: convex, measured. 신촌: linear — every day costs the same,
                    # because every free day saves a commute regardless of position (R195).
                    cost += (SINCHON_INC[slot] if (SINCHON_LINEAR and campus == '신촌')
                             else INC[slot])
                C[ui, ci] = cost

        if np.any(C.min(axis=1) >= BIG):
            continue
        try:
            r, c = linear_sum_assignment(C)
        except ValueError:
            continue
        tot = C[r, c].sum()
        if tot >= BIG:
            continue

        # ---- POST-CHECKS. Constraints the assignment problem cannot express ----------
        by_sem = {}
        for ui, ci in zip(r, c):
            si, slot = cols[ci]
            by_sem.setdefault(si, []).append(units[ui])

        # (1) ⭐ THE KOREAN MAJOR-ELECTIVE CAP (R152/R105), finally ENFORCED.
        # QRM's own elective sections are 국제-only. So a Major Elective taken during a
        # 신촌 semester must be a Korean 상경·응통 section — and those are capped at
        # 4 courses / 12 credits of Major Credit for the whole degree. Measured today:
        # 0 of the 13 ME-eligible sections in the Fall 2026 국제 pool are Korean-capped,
        # so this never binds in Fall 2026; it binds hard across the 신촌 semesters.
        me_at_sinchon = sum(1 for si, us in by_sem.items()
                            if pattern[si] == '신촌'
                            for u in us if u['key'] == 'ME')
        if me_at_sinchon > KOREAN_ME_COURSE_CAP:
            continue

        # (2) ⭐ THE MILEAGE BUDGET (R3 / R171), finally ENFORCED rather than described.
        # From 2학년 every semester is a mileage auction with 72 points, a per-course
        # ceiling, and at most two bids at 36. A plan that cannot be BOUGHT is not a plan.
        # Items with no mileage evidence contribute 0 and are counted as unpriced.
        over = False
        for si, us in by_sem.items():
            bids = semester_bids(us)
            ok, _detail = risk.budget_check(bids)
            if not ok:
                over = True
                break
        if over:
            continue

        # ⭐ R200: reward 신촌 semesters. Uniform per regular 신촌 semester.
        val = -tot + SINCHON_SEMESTER_VALUE * sum(
            1 for c, sm in zip(pattern, sems) if c == '신촌' and sm['kind'] == 'sem')
        if val > best[0]:
            plan = {}
            for ui, ci in zip(r, c):
                si, slot = cols[ci]
                plan.setdefault(sems[si]['label'], []).append(units[ui]['key'])
            best = (val, {'campus': {s['label']: p for s, p in zip(sems, pattern)},
                          'placement': plan,
                          'sems': sems})
    return best


def describe(remaining, **kw):
    val, plan = solve(remaining, **kw)
    if plan is None:
        return f"INFEASIBLE — no placement of the remaining requirements exists.\n"
    out = [f"continuation value V = {val:.3f}", ""]
    camp = plan['campus']
    reg = [s for s in plan['sems'] if s['kind'] == 'sem']
    n_intl = 1 + sum(1 for s in reg if camp[s['label']] == '국제')
    out.append(f"  {n_intl} 국제 / {1 + len(reg) - n_intl} 신촌 regular semesters "
               f"(Fall 2026 국제 is forced)")
    out.append("")
    TERM = {'S': 'Spring', 'F': 'Fall  ', 'U': 'summer'}
    # ⭐ R206: mark COST-INDIFFERENT items. Anything with supply > LOW_SUPPLY_MAX incurs no
    # crowding in ANY semester, so the solver is indifferent to where it lands and the
    # displayed semester is an arbitrary tie-break, NOT a recommendation. Showing those
    # without a marker presented a degenerate optimum as if it were a plan.
    by_key = {i['key']: i for i in ITEMS}
    def mark(k):
        it = by_key.get(k)
        return k if (it and it['supply'] <= LOW_SUPPLY_MAX) else f"{k}*"
    for s in plan['sems']:
        ks = plan['placement'].get(s['label'], [])
        binding = [k for k in ks if by_key.get(k, {}).get('supply', 0) <= LOW_SUPPLY_MAX]
        out.append(f"  {s['label']:20s} {TERM[s['term']]} yr{s['year']} "
                   f"{camp[s['label']]}  ({len(binding)} binding + {len(ks)-len(binding)} free)"
                   f"  " + " ".join(mark(k) for k in sorted(ks)))
    out.append("")
    out.append("  * = costs nothing in ANY semester (supply > "
               f"{LOW_SUPPLY_MAX}); its placement is an arbitrary tie, not a recommendation.")
    return "\n".join(out)


if __name__ == "__main__":
    print("MEASURED CROWDING (from crowding.json)")
    print(f"  baseline (an empty week, no low-supply course) = {_BASE:.3f}")
    for n in sorted(CROWD):
        print(f"  n={n}  cost {CROWD[n]:8.3f}")
    print(f"\n  raw increments      : {[round(x,3) for x in _raw_inc]}")
    print(f"  convex minorant used: {[round(x,3) for x in INC[:EXTRAPOLATED_FROM]]}")
    print(f"  extrapolated 6th    : {INC[-1]:.3f}  ⚠ beyond the measured range")
    print()
    print("=" * 74)
    print("V FOR THE FULL REMAINDER (nothing taken in Fall 2026)")
    print("=" * 74)
    print(describe(full_remaining()))
