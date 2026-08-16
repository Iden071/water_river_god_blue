# -*- coding: utf-8 -*-
"""
risk.py — acquisition probability. THE LOGIC, with a shaped hole for the 8/15 data.

Iden, 2026-08-09:
  "I know you are worried about the seat data, but that is data. As long as we finalize the
   logic, it will fit in quite neatly."

Correct, and it reorders the work. This file builds the MECHANISM. Every function returns
`(probability, basis)` where `basis` names the evidence — and where evidence is absent it
returns **1.0 with basis 'NO DATA'** rather than a guess, so the model is numerically
unchanged today and the 8/15 pull drops into a hole already the right shape. Same pattern as
`difficulty.D_LANG`, which existed before it had a value.

TWO REGIMES, NEVER TO BE CONFLATED (R130 vs R165)
--------------------------------------------------
  Fall 2026   Iden is 1학년 on 대기순번제, competing for FRESHMAN seats. Mileage 배율 says
              nothing about him. Decided by `sy1PercpCnt` — the per-학년 quota — which does
              not exist until after the 2학년+ rounds close on 8/14.
  Sems 3-8    Iden is a mileage bidder. Budget 72 (R3 area), per-course ceiling
              `usePosblMaxMlgVal`, and at most TWO courses may be bid at 36.

AND TWO SUB-REGIMES INSIDE MILEAGE, WHICH R3 ESTABLISHED AND NOTHING HAS USED
-----------------------------------------------------------------------------
  cap 36   real bidding. P(win) genuinely rises with the bid.
  cap 12   "Everyone bids the cap; bid size is NOT a lever; placement decided by the
           tie-break ladder." So for these, spending more mileage buys NOTHING. Any model
           that treats mileage as a single continuous currency is wrong about this class,
           and ECO2102 — a Major Required course — is in it.

⚠️ R134: a per-학년 quota of **0** makes registration *impossible*, not merely hard. That is
the one check that can invalidate the whole plan, and it is a data lookup, not a model.
"""
import json, os, collections

HERE = os.path.dirname(os.path.abspath(__file__))
MILEAGE_BUDGET = 72.0        # [M] 제도안내 대학별 마일리지 table, from 2학년 (1학년 has none)
MAX_PER_COURSE = 36          # [M] student-side cap
MAX_AT_CAP = 2               # [M] at most two courses may be bid at 36
SEATS_FILE = os.path.join(HERE, 'fall2026_seats.json')   # ← the 8/15 pull lands here

_ROWS = None


def rows():
    global _ROWS
    if _ROWS is None:
        _ROWS = json.load(open(os.path.join(HERE, 'mileage_history.json'),
                               encoding='utf-8'))
    return _ROWS


def course_rows(code, campus=None):
    return [r for r in rows()
            if r.get('subjtnb') == code and (campus is None or r.get('campsDivNm') == campus)]


def ceiling(code, campus=None):
    """The offering department's per-course mileage ceiling (R3). None if unknown."""
    rs = course_rows(code, campus)
    caps = {r.get('usePosblMaxMlgVal') for r in rs if r.get('usePosblMaxMlgVal')}
    return max(caps) if caps else None


# ---------------------------------------------------------------------------
# REGIME 2 — mileage bidding (sems 3-8). Buildable TODAY; no missing data.
# ---------------------------------------------------------------------------
# ⛔ WHAT minMlg / avgMlg / maxMlg ACTUALLY MEAN — settled 2026-08-09 by internal check
# --------------------------------------------------------------------------------------
# The obvious reading is "statistics of the students who WON the seat". That reading is
# FALSE, and it is falsifiable without any external document:
#
#   For a section with exactly 2 seats, if the stats described the 2 winners then
#   avg must equal (min+max)/2 exactly.
#   Measured over all 28 two-seat sections in mileage_history.json:  9 match, **19 do not.**
#   And values like avgMlg = 19.33 (= 58/3) and 17.18 (11 points) and 24.4 (5 points)
#   have denominators far larger than 2.
#
# ⇒ These are statistics over **APPLICANTS**, not winners.
#
# The consequence is the whole point: for a 2-seat section you must finish in the TOP TWO of
# the applicant bid distribution, so what matters is proximity to `maxMlg`, NOT clearing
# `minMlg`. `minMlg` is merely the most timid applicant — beating them means nothing.
#
# An earlier version of this function used minMlg and reported UIC1805 as winnable at a bid
# of 6. That was optimistic by an order of magnitude and is withdrawn (R190).

def p_win_bracket(code, bid, campus=None):
    """(p_low, p_high, basis) — a BRACKET, because the applicant distribution is unknown.

    p_high  optimistic: bid >= minMlg (you beat the weakest applicant). An upper bound.
    p_low   conservative: bid >= maxMlg (you match the strongest). A lower bound — and even
            this is not a guarantee, because matching the top bid drops you into the
            tie-break ladder, which is NOT modelled anywhere in this project.
    The truth is inside. Do not collapse it to a point estimate.
    """
    rs = course_rows(code, campus)
    if not rs:
        # ⛔ FIXED 2026-08-16 (R259). This returned (1.0, 1.0) — a POINT estimate of
        # CERTAIN acquisition, dressed as a neutral default. It is the most optimistic
        # value in the range, and R254 showed it landing directly on the threshold that
        # decided the deferral verdict: every hard-tier language was unfetched, so every
        # one returned "certain", so deferring Language looked free.
        # A bracket whose two arms are equal asserts knowledge. With no observations the
        # honest bracket is the WIDEST one: could fail, could succeed.
        return 0.0, 1.0, 'NO DATA — no mileage history for this course (widest bracket)'
    cap = ceiling(code, campus)
    if cap and cap <= 12:
        # R3: everyone bids the ceiling; the bid is not a lever at all.
        return None, None, (f'CAP-{cap} — bidding is not a lever (R3); decided entirely by '
                            f'the tie-break ladder, which is NOT modelled')
    # ⛔ THE TIE-BREAK WALL. If the top applicant already bid the ceiling, then bidding the
    # ceiling yourself does not win the section — it enters you into the tie-break ladder
    # (이수학점 / 학년 / etc.), which NOTHING in this project models. Reporting 1.0 here
    # would be a fabricated certainty, and the first version of this function did exactly
    # that, returning P(hard language)=0.000. Contested sections must surface as UNKNOWN.
    contested = [r for r in rs
                 if (r.get('maxMlg') or 0) >= (cap or MAX_PER_COURSE)
                 and (r.get('atnlcPercpCnt') or 99) <= 4]
    hi = sum(1 for r in rs if (r.get('minMlg') or 0) <= bid) / len(rs)
    lo = sum(1 for r in rs if (r.get('maxMlg') or 0) < bid) / len(rs)   # strict: must BEAT
    seats = sorted({r.get('atnlcPercpCnt') for r in rs})
    note = f'{len(rs)} sections; seats {seats}'
    if contested:
        note += (f'; ⛔ {len(contested)}/{len(rs)} are small sections where the top '
                 f'applicant already bid the {cap or MAX_PER_COURSE} ceiling — those are '
                 f'decided by an UNMODELLED tie-break')
    return lo, hi, note


def p_win_mileage(code, bid, campus=None):
    """Conservative (lower-bound) probability. Use p_win_bracket when the width matters."""
    lo, hi, basis = p_win_bracket(code, bid, campus)
    if lo is None:
        return None, basis
    return lo, basis


def min_bid_for(code, target_p=0.8, campus=None):
    """Cheapest bid reaching `target_p`. None if unreachable, unpriceable, or UNKNOWN.

    ⛔ The NO-DATA path must NOT fall through to a cheap bid. p_win_* returns 1.0 with basis
    'NO DATA' so that consumers are numerically unchanged, but a *bid* of 1 for a course
    nobody has ever observed is a fabricated fact, not a neutral default. ECO2102 — a Major
    Required course with zero mileage rows — was being reported as costing 1 mileage.
    """
    if not course_rows(code, campus):
        return None
    cap = ceiling(code, campus) or MAX_PER_COURSE
    for b in range(1, int(cap) + 1):
        p, _ = p_win_mileage(code, b, campus)
        if p is None:
            return None
        if p >= target_p:
            return b
    return None


def budget_check(bids):
    """bids = {code: bid}. Returns (ok, detail) against the 72-point budget rules."""
    total = sum(bids.values())
    at_cap = sum(1 for b in bids.values() if b >= MAX_PER_COURSE)
    over = {c: b for c, b in bids.items()
            if b > (ceiling(c) or MAX_PER_COURSE)}
    problems = []
    if total > MILEAGE_BUDGET:
        problems.append(f'spends {total} of {MILEAGE_BUDGET}')
    if at_cap > MAX_AT_CAP:
        problems.append(f'{at_cap} courses bid at {MAX_PER_COURSE} (max {MAX_AT_CAP})')
    if over:
        problems.append(f'over the course ceiling: {over}')
    return (not problems), ('; '.join(problems) or
                            f'{total:.0f}/{MILEAGE_BUDGET:.0f} mileage, {at_cap} at cap')


# ---------------------------------------------------------------------------
# REGIME 1 — Fall 2026, 대기순번제 on freshman seats. THE HOLE.
# ---------------------------------------------------------------------------
def seats_available():
    return os.path.exists(SEATS_FILE) and os.path.getsize(SEATS_FILE) > 0


def p_get_freshman(section_code):
    """P(Iden secures this section on 8/25).

    ⛔ FIXED 2026-08-16. The previous version tested `sy1 == 0` ALONE. That is the exact
    error R2 and R134 exist to prevent, and it was harmless only for as long as
    `fall2026_seats.json` did not exist. The moment the 8/16 pull landed it began returning

        UIC1561-01-00  p=0.0  IMPOSSIBLE
        QRM1001-01-00  p=0.0  IMPOSSIBLE
        UIC1551-01-00  p=0.0  IMPOSSIBLE

    — i.e. it declared the entire recommendation unregistrable, because those sections have
    `sy1..sy6 = [0,0,0,0,0,0]`, which is **no per-year scheme at all**. Per-year quotas are
    OPTIONAL (제도안내 FAQ 라). The test must be two-sided:

        all sy1..sy6 == 0            -> no scheme          -> NOT a gate (R2)
        some sy_i != 0 AND sy1 == 0  -> scheme, 1학년 = 0   -> IMPOSSIBLE (R134)
        no row at all                -> NOT a gate (R249)

    Nothing called this function, which is why the model was unaffected — but it is the
    same predicate `eligibility.year_barred()` applies for real, and the two must agree.

    ⚠️ This returns 1.0 for "not barred". That is ELIGIBILITY, not probability. The seat
    pull cannot price competition: `atnlcPercpCnt` is not section capacity (R248).
    """
    if not seats_available():
        return 1.0, 'NO DATA — run fetch_fall2026.py (G-1)'
    seats = json.load(open(SEATS_FILE, encoding='utf-8'))
    s = seats.get(section_code)
    if not s:
        return 1.0, 'NO DATA — no mileage row for this section (absence ≠ bar, R249)'
    sy = [s.get(f'sy{i}PercpCnt') or 0 for i in range(1, 7)]
    if not any(sy):
        return 1.0, 'no 학년별정원 scheme in force — NOT a year gate (R2)'
    if sy[0] == 0:
        # ⛔ R134. Not "unlikely" — impossible. Must propagate as a hard exclusion.
        return 0.0, f'IMPOSSIBLE — scheme in force and the 1학년 quota is 0 (R134); sy={sy}'
    return 1.0, f'1학년 quota = {sy[0]} (first-come; no arrival model yet)'


# ---------------------------------------------------------------------------
# REPORT
# ---------------------------------------------------------------------------
def report():
    from plan_model import ITEMS
    print("=" * 78)
    print("ACQUISITION RISK — what the logic can price TODAY, and what waits on data")
    print("=" * 78)
    print(f"\nREGIME 1 · Fall 2026 (1학년, 대기순번제)")
    print(f"  seat file present: {seats_available()}   -> "
          f"{'live' if seats_available() else 'every p_get_freshman() returns 1.0, flagged'}")
    print(f"  expected at: {os.path.basename(SEATS_FILE)}  (fetch_fall2026.py, after 8/14)")

    print(f"\nREGIME 2 · sems 3-8 (mileage). Budget {MILEAGE_BUDGET:.0f}, "
          f"max {MAX_PER_COURSE}/course, <= {MAX_AT_CAP} at cap.")
    codes = ['QRM1001', 'ECO1101', 'ECO2101', 'ECO2102', 'QRM3003', 'QRM3004', 'QRM3005',
             'UIC1805', 'UIC1806', 'UIC1561', 'UIC2151', 'STA2102']
    print(f"\n  {'course':9s} {'ceil':>5} {'obs':>4}  {'bid for 80%':>12}  basis")
    print("  " + "-" * 74)
    nodata = []
    for c in codes:
        rs = course_rows(c)
        cap = ceiling(c)
        if not rs:
            nodata.append(c)
            print(f"  {c:9s} {'-':>5} {0:4d}  {'—':>12}  ⚠️ NO DATA")
            continue
        b = min_bid_for(c)
        p, basis = p_win_mileage(c, b if b else MAX_PER_COURSE)
        if p is None:
            print(f"  {c:9s} {str(cap):>5} {len(rs):4d}  {'n/a':>12}  ⚠️ {basis[:46]}")
        else:
            print(f"  {c:9s} {str(cap):>5} {len(rs):4d}  {str(b):>12}  {basis}")
    if nodata:
        print(f"\n  ⚠️ NO MILEAGE EVIDENCE for {len(nodata)}: {', '.join(nodata)}  (G-3)")


if __name__ == '__main__':
    report()
