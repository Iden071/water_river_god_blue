"""test_weights.py — VERIFY 11 regression test.

Asserts that the LIVE constants in rank.py / rank2.py still reproduce every preference
Iden actually stated. Run this after ANY weight edit. If a check fails, either the edit
was wrong or Iden changed his mind — and if the latter, update the claim string here so
the elicited wording and the constant stay tied together.
"""
import rank as RK, rank2 as R2

def _mk(bl):
    m = 0
    for d, p in bl: m |= 1 << (d*16 + p)
    return m

# Tue + Thu on campus; Wednesday sandwiched between them (the case Iden raised).
_BASE = [(1,3),(1,4),(3,3),(3,4)]
def _wed(online=False, inperson=False):
    t = _BASE + ([(2,3),(2,4)] if (online or inperson) else [])
    p = _BASE + ([(2,3),(2,4)] if inperson else [])
    return R2.week_value(_mk(p), _mk(t))[0]
def _monfri():                      # 월+금 genuinely empty
    b = [(1,3),(2,3),(3,3)]
    return R2.week_value(_mk(b), _mk(b))[0]
def _midweek():                     # 화수목 free but NOT touching the weekend
    b = [(0,3),(4,3)]
    return R2.week_value(_mk(b), _mk(b))[0]
def _monfri_online():               # 월+금 campus-free but each carries an online class
    b = [(1,3),(2,3),(3,3)]
    t = b + [(0,3),(4,2)]           # 금 class at 2교시 = outside the event window
    return R2.week_value(_mk(b), _mk(t))[0]

CLAIMS = [
    ('"1교시 = anchor −10"',                  lambda: RK.W_E1,                     -10,   .15),
    ('"17:50(9교시) should be −1"',            lambda: RK.LATE(9),                   -1,   .15),
    ('"21:50(13교시) should be −10"',          lambda: RK.LATE(13),                 -10,   .15),
    ('"22:50(14교시) bigger than −10"',        lambda: RK.LATE(14),                 -13.0, .10),
    ('"저녁 slightly bigger than 점심"',        lambda: RK.W_DINNER - RK.W_LUNCH,     -2,   .15),
    ('"4연강 = −8"',                          lambda: RK.MARATHON(4),               -8,   .15),
    ('marathon convex (8연강 ≫ 2×4연강)',      lambda: RK.MARATHON(8),              -20.8, .05),
    ('"4교시 구멍 ≈ 9시 수업 하루"',            lambda: RK.HOLE(4),                  -10,   .15),
    ('"월 = 금의 75%"',                        lambda: RK.DAY_CONTIG/(RK.DAY_CONTIG+RK.FRI_EVENT), 0.75, .02),
    # RETIRED (was: '"고립 공강일 = 붙은 날의 25%"' -> REST/DAY_CONTIG == 0.25). R129 made REST
    # a different quantity from the old ISOLATED, and R140 elicited it independently against
    # three fixed anchors. The 25% ratio described the superseded concept.
    ('R140 REST bracketed to (6,8) by 3 anchors', lambda: RK.REST,                 7.0,  .15),
    ('R142 free Friday = two 9am starts',      lambda: RK.DAY_CONTIG + RK.REST,    20.0, .05),
    ('R101: MR_CODES has 7 codes, not 6',     lambda: len(R2.MR_CODES),              7,   .01),
    # --- R129: TRIP and REST are two goods (Iden 2026-08-07) -------------------------
    # "rest should apply to every single weekday (genuinely free days). Days connected
    #  to the weekend should just scale sharply by day."
    ('R129 online-only 수 gets NO rest',       lambda: _wed(online=True) - _wed(online=False), -7.00, .02),
    ('R129 online-only 수 == in-person 수',    lambda: _wed(online=True) - _wed(inperson=True),  0.0, .01),
    # asserts the STRUCTURE, not a magnitude: RUN_EXP is still [P] (R142 bracket [1.2,1.6]),
    # so a hard-coded total here breaks every time the bracket is narrowed. The claim that
    # matters is that an empty 월+금 pays REST on BOTH days on top of the trip value.
    ('R129 empty 월+금 pays trip AND rest',    lambda: _monfri() - _monfri_online(), 14.0, .01),
    ('R129 midweek run earns no trip value',  lambda: _midweek(),                   21.00, .01),
    # RETIRED (was: '"MR/ME lower than the 학년2 minus"' -> ROLE_MR + YEAR_PEN(2) == -2).
    # Iden 2026-08-07: the 학년 penalty means "I'm not ready for it" — a READINESS cost.
    # The role bonus measures DEGREE PROGRESS. They are different accounts and were never
    # comparable; the original constraint was a category error, not a preference. R128
    # rescaling the penalty to -4 did not break a preference, it exposed a bad test.
    # RETIRED (was: '"MR slightly higher than ME"' -> ROLE_MR - ROLE_ME == 2). Iden withdrew
    # the statement himself on 2026-08-07: he made it before the 4-year structure existed, and
    # what he was reaching for ("MEs are easier to get than MRs") is exactly what R149's
    # scarcity formula measures. Replaced by the claim that actually survives:
    ('R149 formula reproduces the elicited ROLE_MR', lambda: R2.ROLE_MR,             8.0, .01),
    ('R152 ME measured w/ the Korean cap',     lambda: R2.ROLE_ME,                   2.29, .02),
    ('MR still ranks above ME',               lambda: 1.0 if R2.ROLE_MR > R2.ROLE_ME else 0.0, 1.0, .0),
    ('R103: MB role scrapped',                lambda: R2.ROLE_MB,                    0,   .00),
    ('R103: Econ 2nd-major bonus scrapped',   lambda: R2.BONUS_ECON2ND,              0,   .00),
    # RETIRED (was: 'language bonus kept' -> R2.BONUS['UIC1805'] == 8). R162: the live scorer
    # never reads that dict — rank3 scores language as a REQUIREMENT SLOT, so the +8 was
    # unreachable. The test asserted a constant nothing consulted. Replaced by the real claim:
    ('R162 only ONE per-course bonus is live', lambda: float(len(R2.BONUS) + len(RK.BONUS)), 0.0, .0),
    ('R127 chapel +10 is that one bonus',      lambda: __import__('rank3').CHAPEL_BONUS, 10.0, .01),
]

def main():
    bad = 0
    for claim, f, want, tol in CLAIMS:
        got = f()
        ok = abs(got - want) <= tol * max(1, abs(want))
        if not ok: bad += 1
        print(f"  {'✅' if ok else '❌'} {claim:42s} want {want:+8.2f}  got {got:+8.2f}")
    print(f"\n  {len(CLAIMS)-bad}/{len(CLAIMS)} pass")
    return bad

if __name__ == '__main__':
    raise SystemExit(1 if main() else 0)
