# -*- coding: utf-8 -*-
"""
difficulty.py — the difficulty axis. Built 2026-08-09.

WHY IT EXISTS NOW
-----------------
Iden, on being told the language tier "cannot change the answer":
  "even if something 'does not change the answer', it should still be in the model in case
   of future model changes. Like why are we treating the model like some kind of already
   finished thing with only minimal changes to make."

He is right, and R185 is the proof: four questions were retired with "cannot change the
answer", the model was then replaced (R182/R184), and not one of them re-checked itself.
A measurement recorded as a conclusion decays silently. So the mechanism goes in.

THE CARRIER
-----------
R137 forbids per-course difficulty questions — Iden cannot rate 700 courses and asking him
to would be offloading the modelling. So difficulty is carried by a CATEGORY. The first
category is the one Iden volunteered unprompted (R166):

  "The courses we were originally aiming are 'Beginning Chinese, Beginning Japanese' and
   are much easier."  ... the others are "really learning the language, pretty hard."

THE WEIGHT IS NOT GUESSED, AND NOT ASKED YET
--------------------------------------------
`D_LANG` (points per difficulty step) has never been elicited. Rather than invent it or
leave the axis out, the mechanism is parameterised and `sweep_difficulty.py` reports the
SWITCHING THRESHOLD — the value of D_LANG at which the ranking changes. That converts an
impossible question ("what is difficulty worth in schedule points?") into an easy one
("is it more or less than X?"), which is the only form R141 says is safe to ask.
"""
import json, os, collections

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# THE LANGUAGE POOL — R166, all ten level-1 courses. G-10 closed.
# The live ranker had LANG = {'UIC1805','UIC1806'} — 2 courses. That came from D-3, which
# was Iden's PREFERENCE for the easy ones, recorded as if it were a rule (R166).
# ---------------------------------------------------------------------------
LANG_EASY = {'UIC1805', 'UIC1806'}                      # UIC "Beginning" — "much easier"
LANG_HARD = {'YCF1301', 'YCF1351', 'YCF1451', 'YCF1501',
             'YCF1551', 'YCF1601', 'YCF1603', 'YCF1607'}  # 언어와표현 — "pretty hard"
LANG_ALL = LANG_EASY | LANG_HARD

# difficulty in STEPS above the baseline. One step = whatever D_LANG is worth.
TIER_STEPS = {c: 0 for c in LANG_EASY} | {c: 1 for c in LANG_HARD}

# ⭐ ELICITED 2026-08-09 (R188). Iden was shown two identical semesters differing only in
# whether the language slot held Beginning Chinese or a 언어와표현 course, and answered that
# the hard one is worse by "about the same as a 9am start".
#   one 9:00 start = 10 (MODEL.md §0 anchor)  =>  D_LANG = 10.0
#
# ⚠️ THIS LANDS ON A SWITCHING THRESHOLD. The boundary is at 10.25 and the two surviving
# strategies differ by 0.002 at D_LANG = 10. The model does NOT separate them. Do not
# present either as the answer on the strength of this constant — see R188.
D_LANG = float(os.environ.get('D_LANG', 10.0))

# ⭐ THE GPA GATE (R153) — the only genuine feedback loop in the model, still unpriced.
#   difficulty -> GPA -> double-major admission (December, competitive, on Sem 1+2 ONLY)
#                     -> GPA >= 3.75 -> +3 credits of capacity next semester
# Both edges run through THIS semester. So a hard course in Fall 2026 costs more than the
# same course in Spring 2029, and nothing has ever represented that.
# [P] NEVER ELICITED. Default 1.0 = inert; the model is numerically unchanged.
# Sweep it, do not guess it.
GPA_GATE_MULT = float(os.environ.get('GPA_GATE_MULT', 1.0))

D_LANG_DEFAULT = 10.0    # [E] R188. Was 0.0 (unelicited) for the length of one session.


def steps(course_code):
    """Difficulty steps for a course. 0 for anything with no tier evidence."""
    return TIER_STEPS.get(course_code[:7], 0)


# ---------------------------------------------------------------------------
# WHAT A DEFERRED LANGUAGE ACTUALLY COSTS — measured from the mileage history
# ---------------------------------------------------------------------------
# R130 / R165: this Fall Iden registers on 대기순번제 with FRESHMAN seats, so the easy tier
# is obtainable without bidding. From 2학년 he is a mileage bidder against the same 2-seat
# 분반. So deferring Language is not tier-neutral: it is a bet on winning a contested
# section later, and losing that bet means taking a HARD language instead.
def easy_tier_competition(path=None):
    """How hard is the easy tier to win as a 2학년+? Measured, not assumed."""
    rows = json.load(open(path or os.path.join(HERE, 'mileage_history.json'),
                          encoding='utf-8'))
    intl = [r for r in rows
            if r.get('subjtnb') in LANG_EASY and r.get('campsDivNm') == '국제']
    at_cap = [r for r in intl if (r.get('maxMlg') or 0) >= 36]
    seats = [r.get('atnlcPercpCnt') for r in intl]
    return {
        'rows': len(intl),
        'sections_won_only_at_the_36_cap': len(at_cap),
        'share_at_cap': (len(at_cap) / len(intl)) if intl else None,
        'seats_per_section': sorted(set(seats)),
        'avg_winning_bid_range': (min((r.get('avgMlg') or 99) for r in intl),
                                  max((r.get('avgMlg') or 0) for r in intl)),
    }


def p_hard_if_deferred(path=None, bid=36):
    """P(Iden ends up in the HARD tier | he defers Language).

    ⛔ REVISED 2026-08-09 (R190). This now delegates to `risk.p_win_bracket`, which knows
    that minMlg/avgMlg/maxMlg are statistics over APPLICANTS, not winners — proved by the
    fact that 19 of 28 two-seat sections have avg != (min+max)/2.

    To take the easy tier later he must finish in the TOP TWO of a 2-seat section, i.e. at
    or near maxMlg, spending one of his only two 36-bids on a 3-credit CC requirement — and
    then still win a tie-break the model does not represent.

    Returns (p_low, p_high): a BRACKET, not a point. The conservative arm assumes he must
    match the top applicant; the optimistic arm assumes beating the weakest suffices.
    """
    import risk
    lo5, hi5, _ = risk.p_win_bracket('UIC1805', bid, '국제')
    lo6, hi6, _ = risk.p_win_bracket('UIC1806', bid, '국제')
    p_easy_lo = 1 - (1 - lo5) * (1 - lo6)      # either course, conservative
    p_easy_hi = 1 - (1 - hi5) * (1 - hi6)      # either course, optimistic
    return (1 - p_easy_hi), (1 - p_easy_lo)    # P(hard): low, high


if __name__ == '__main__':
    c = easy_tier_competition()
    print("EASY-TIER LANGUAGE COMPETITION AT 국제 — measured from mileage_history.json")
    for k, v in c.items():
        print(f"  {k:34s} {v}")
    print()
    lo, hi = p_hard_if_deferred()
    print(f"  => P(hard tier | Language deferred) is BRACKETED at [{lo:.3f}, {hi:.3f}]")
    print(f"     (bidding the 36 cap on one of the two easy courses)")
    print()
    print(f"language pool: {len(LANG_ALL)} courses "
          f"({len(LANG_EASY)} easy, {len(LANG_HARD)} hard)")
    print(f"D_LANG has never been elicited. Default {D_LANG_DEFAULT} — sweep it.")
