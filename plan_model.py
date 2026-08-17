#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plan_model.py — the 8-semester skeleton and the remaining-requirement ledger.

WHY THIS EXISTS (R181)
----------------------
Iden, 2026-08-09:
  "BIZ1101 is a pure elective, also is YCE1253-01-00. But that timetable is
   considered #1, right? ... considering the double major, I have like about 5
   pure electives to fit within 7 semesters. But I already have 2 this semester."
and then, on how to fix it:
  "Electives not costing anything is probably right. Because the real cost comes
   from choosing the elective over some other thing, the opportunity cost."

So this file does NOT add a penalty on electives. It builds the thing whose
absence made electives look free: a model of the SIX SEMESTERS AFTER THIS ONE,
so that what Fall 2026 leaves undone can be priced by what it does to them.

An elective still scores 0. It costs you the slot, and the slot is now worth
something measurable.

WHAT IS ASSUMED HERE
--------------------
Every assumption is tagged [E] elicited / [M] measured / [D] derived /
[P] PROVISIONAL — nobody has confirmed it. Run `python plan_model.py` to print
the ledger with the tags; anything marked [P] should be checked by Iden before
the output is trusted (R179: do not let an unverified value become a verdict).
"""

# ---------------------------------------------------------------------------
# 1 · THE SEMESTER SKELETON
# ---------------------------------------------------------------------------
# Sem 1 = Spring 2026, 19.5 cr, DONE (R27). Sems 2-8 remain = 7 semesters.
# Springs are sems 3/5/7; Falls are 2/4/6/8 (R144).
# Academic year: sems 1-2 = yr 1, 3-4 = yr 2, 5-6 = yr 3, 7-8 = yr 4.

SEMESTERS = [
    # sem, label,        term, year, campus_fixed
    (2, "Fall 2026",   "F", 1, "국제"),   # [D] R8: UIC freshman, 국제 only
    (3, "Spring 2027", "S", 2, None),
    (4, "Fall 2027",   "F", 2, None),
    (5, "Spring 2028", "S", 3, None),
    (6, "Fall 2028",   "F", 3, None),
    (7, "Spring 2029", "S", 4, None),
    (8, "Fall 2029",   "F", 4, None),
]

# ---------------------------------------------------------------------------
# 1b · 휴학 (LEAVE OF ABSENCE) AND 계절학기 (SUMMER / WINTER SESSION)
# ---------------------------------------------------------------------------
# Iden, 2026-08-09: he expects a 휴학 for 병역 at some point, and wants 계절학기 modelled
# as an escape valve. Neither had been mentioned once in this project (R185).
#
# ⭐ WHAT A 휴학 DOES AND DOES NOT DO
#   does NOT: advance 학년. Academic year tracks registered semesters, not calendar time,
#             so sems 1-2 = yr1, 3-4 = yr2 ... regardless of a break. The year-gap penalty
#             is therefore INVARIANT to the break. This is the opposite of the intuition.
#   DOES:     change TERM PARITY. Leave after a Fall and return in a Fall, and the Springs
#             move from semesters 3/5/7 to 6/8. That is load-bearing, because QRM3003 is
#             Spring-only AND 국제-only AND chart-year 3 — the single most constrained item
#             in the degree. Parity decides whether it has a legal home.
#
# ⚠️ 계절학기 CREDIT CAP = 7, and that number is SOURCED:
#   수강편람 2026-2, 사회봉사/사회참여 §4-①: "계절학기에는 계절학기 수강신청 최대이수학점인
#   7학점에 포함됨". 7 cr = two 3-credit courses with 1 to spare.
# ⚠️ WHAT IS OFFERED in a 계절학기 is NOT in any document held here. Eligibility is a
#   PARAMETER with no data behind it, and the answer is reported across settings rather
#   than under one guess.
SUMMER_CREDIT_CAP = 7.0     # [M] 수강편람 2026-2
SUMMER_SLOTS      = 2       # [D] 7 cr / 3 cr per course
SUMMER_ELIGIBLE_DEFAULT = frozenset({'LHP', 'Lang', 'SciRD', 'FREE'})
# [P] the plausible 교양 set. Majors and WCiv excluded — no evidence either way.

# ---------------------------------------------------------------------------
# 1c · CODES BY (CAMPUS, SEASON) — R288
# ---------------------------------------------------------------------------
# ⛔ `ITEMS[...]['codes']` records the codes Iden might take, NOT the codes offered at each
# campus in each season. For Chapel that made the whole item look 국제-Fall-only, because
# YCA1006 is the Fall 국제 code — and `partition.py` then priced every Spring Chapel as
# IMPOSSIBLE. Chapel is of course offered every semester; it just changes code.
# Sourced from past_terms.json, all six terms, names verified to contain 채플:
CODES_BY_TERM = {
    'Chapel': {
        ('국제', 'S'): ['YCA1001', 'YCA1005'],                      # 채플(1) 채플(A)
        ('국제', 'F'): ['YCA1002', 'YCA1006'],                      # 채플(2) 채플(B)
        ('신촌', 'S'): ['YCA1003', 'YCA1007', 'YCA1009', 'YCA1011'],
        ('신촌', 'F'): ['YCA1004', 'YCA1008', 'YCA1010', 'YCA1012'],
    },
}


def codes_for(key, campus, season):
    """Codes for a ledger item AT a campus/season. Falls back to the flat `codes` list."""
    m = CODES_BY_TERM.get(key)
    if m:
        return m.get((campus, season), [])
    for i in ITEMS:
        if i['key'] == key:
            return list(i.get('codes') or [])
    return []


CREDIT_CAP     = 18.0   # [M] R-cap: 졸업이수학점 126 → 1~18학년 cap of 18 every semester
FRESHMAN_CAP   = 19.0   # [M] freshman year allows 19; only sems 1-2
CHAPEL_PER_SEM = 1      # [M] one chapel pass per semester, max

# Campus structure, forced and not a matter of preference (R144):
#   - sem 2 is 국제 (freshman rule)
#   - QRM3003 is MR, 국제-only AND Spring-only  =>  one Spring must also be 국제
#   => minimum 2 국제 semesters, maximum 5 신촌, NO MATTER what Fall 2026 takes.
MIN_INTL_SEMESTERS = 2  # [D] R144

# ---------------------------------------------------------------------------
# 2 · THE REMAINING-REQUIREMENT LEDGER
# ---------------------------------------------------------------------------
# Fields:
#   key, label, credits_each, count, chart_year, campus, terms, supply
#
# campus : '국제' | '신촌' | 'any'
# terms  : 'S' | 'F' | 'SF'
# supply : how many distinct sections/courses can satisfy ONE unit of this item
#          in a semester that offers it. This drives the crowding term — a
#          requirement with one section pins a time; one with 400 does not.
#          Counts are [M] from canonical_2026F.json unless tagged otherwise.

ITEMS = [
    # ---- COMMON CURRICULUM · 19.5 cr outstanding (R27/R17) -----------------
    dict(key="Chapel",  label="Chapel pass",                credits=0.5, count=3,
         chart_year=None, campus="any", terms="SF", supply=2, codes=['YCA1006'],
         note="[M] 1/semester max. From yr 2 신촌 online chapel exists (R143 §14.2) "
              "=> no campus constraint after this semester."),

    dict(key="LHP",     label="CC Lit-Hist-Phil, 2nd",      credits=3.0, count=1,
         chart_year=None, campus="any", terms="SF", supply=15, codes=['UIC1551','UIC1251','UIC1501'],
         note="[M] 15 국제 sections Fall 2026; only 2 신촌 (R143) — thin, flagged."),

    dict(key="Lang",    label="CC Language",                credits=3.0, count=1,
         chart_year=None, campus="any", terms="SF", supply=20,
         codes=['UIC1805', 'UIC1806',                                    # easy tier
                'YCF1301', 'YCF1351', 'YCF1451', 'YCF1501',              # hard tier
                'YCF1551', 'YCF1601', 'YCF1603', 'YCF1607'],
         note="[M] CONFIRMED 2026-08-10 over six terms (R232). campus='any' is correct, but "
              "ONLY via the hard tier: measured, the EASY tier (UIC1805/1806) runs at 신촌 in "
              "SPRING (1 section) and NEVER in Fall, while the 8 YCF 언어와표현 courses run at "
              "both campuses in all six terms. The codes list previously held the easy tier "
              "ALONE while claiming 'any' — so a 신촌 lookup returned nothing and K(Lang) "
              "scored 0.000 from a data gap (R227). ⚠️ Deferring Lang into a 신촌 FALL "
              "semester therefore means the hard tier with CERTAINTY, not p_hard=0.35; into a "
              "신촌 SPRING it does not."),

    dict(key="SciRD",   label="CC SciLit or RDQM",          credits=3.0, count=1,
         chart_year=None, campus="any", terms="SF", supply=35, codes=['UIC2151'],
         note="[M] 35 국제 sections; only 1 신촌 (R143) — thin, flagged."),

    dict(key="WCiv",    label="CC Western Civilization",    credits=3.0, count=1,
         chart_year=None, campus="국제", terms="SF", supply=3, codes=['UIC1561'],
         note="[M] 3 sections, all 국제 (R143). One of the four 국제-only items."),

    dict(key="Seminar", label="UIC Seminar",                credits=3.0, count=2,
         chart_year=3,    campus="any", terms="SF", supply=38, codes=['UIC3527','UIC3643','UIC3649','UIC3657'],
         note="[M] R131: no year window for HASS. 4 국제 + 38 신촌 sections. "
              "Chart year 3 (R148/R149)."),

    # ---- MAJOR REQUIRED · 18 cr, all six outstanding (R31: MR unchanged) ---
    dict(key="QRM1001", label="MR Introduction to QRM",     credits=3.0, count=1,
         chart_year=1,    campus="국제", terms="SF", supply=1, codes=['QRM1001'],
         note="[M] single section 목4,5,6. 국제-only. Runs in Spring too (R144)."),

    dict(key="ECO1101", label="MR Mathematics for Econ 1",  credits=3.0, count=1,
         chart_year=1,    campus="any", terms="SF", supply=2, codes=['ECO1101'],
         note="[M] 2 국제 sections this Fall. 신촌 English section is 월1,2/수2 — "
              "Monday AND a 9am (R164). Cheap here, expensive there."),

    dict(key="ECO2102", label="MR Microeconomics",          credits=3.0, count=1,
         chart_year=2,    campus="신촌", terms="SF", supply=4, codes=['ECO2102'],
         note="[M] 신촌-only (R8 blocks it this semester). 원론 ECO1103 is a "
              "different course — do not substitute."),

    dict(key="ECO2101", label="MR Macroeconomics",          credits=3.0, count=1,
         chart_year=2,    campus="신촌", terms="SF", supply=4, codes=['ECO2101'],
         note="[M] 신촌-only, same as Micro."),

    dict(key="MR5",     label="MR MathStat1 or Regression",  credits=3.0, count=1,
         chart_year=3,    campus="any", terms="SF", supply=2, codes=['QRM3005','QRM3004'],
         note="[D] DISJUNCTION: QRM3005 (신촌) OR QRM3004 (국제, Spring only, R74). "
              "'any' campus is correct only because of the disjunction."),

    dict(key="QRM3003", label="MR Prin. Financial Engineering", credits=3.0, count=1,
         chart_year=3,    campus="국제", terms="S", supply=1, codes=['QRM3003'],
         note="[E] Iden: 'only 국제 and it only opens in the spring.' The single "
              "hardest-placed item in the degree — it alone forces a 국제 Spring."),

    # ---- MAJOR ELECTIVES · 18 cr under a double major (R31) ---------------
    # ⚠️ KOREAN CAP (R152/R105): at most 4 courses / 12 cr of Korean 상경·응통 sections
    # count toward Major Credits. Enforced in continuation.solve(), not merely priced.
    dict(key="ME",      label="QRM Major Elective",         credits=3.0, count=6,
         chart_year=3,    campus="any", terms="SF", supply=9, codes=['QRM2004','STA2102'],
         note="[M] 24cr single-major -> 18cr with a double major (R31). "
              "9 QRM elective sections at 국제. Korean 상경/응통 sections count "
              "toward ME but are capped at 4 courses / 12 cr (R152/R105). "
              "Chart year 3 = pool midpoint [P]."),

    # ---- SECOND MAJOR (R147: confirmed; which major is a December decision) -
    dict(key="DM",      label="2nd major course",           credits=3.0, count=12,
         chart_year=None, campus="신촌", terms="SF", supply=20, codes=[],
         note="[P] 36 cr assumed (R31 says 36-39, varies by major). Campus 신촌 "
              "assumed because Iden's candidates — Mathematics, Economics, CS — "
              "are all 신촌 colleges. IF THE 2ND MAJOR IS INSIDE UIC THIS IS WRONG "
              "and flips a large part of the campus arithmetic."),

    # ---- FREE ELECTIVES · the residual (R181) -----------------------------
    dict(key="FREE",    label="Free elective",              credits=3.0, count=5,
         chart_year=None, campus="any", terms="SF", supply=422, codes=[],
         note="[D] RESIDUAL, not a quota: 126 - 19.5 done - 19.5 CC - 36 QRM "
              "- 36 2nd major = 15.0 cr = 5 courses. If the 2nd major is 39 cr "
              "it is 12.0 cr = 4 courses. THIS IS THE BUDGET IDEN SPOTTED."),
]

TOTAL_CREDITS = 126.0
DONE_CREDITS  = 19.5   # [M] R27, Sem 1


def build_semesters(break_after=None, return_term=None, summers=False):
    """The teaching slots available after Fall 2026.

    break_after  : take a 휴학 after this semester number (2..7), or None
    return_term  : 'S' or 'F' — the term he comes back in. Only this matters, not the
                   length of the leave, because 학년 does not advance during a 휴학.
    summers      : include 계절학기 sessions between academic years

    Returns a list of dicts: kind ('sem'|'summer'), n, label, term, year, campus, slots.
    """
    out = []
    n = 3
    term = 'S'                    # sem 3 would be Spring 2027 with no break
    year_of_sem = {3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4}
    for n in range(3, 9):
        if break_after is not None and n == break_after + 1 and return_term:
            # parity may flip on return; everything after inherits the new alternation
            term = return_term
        out.append(dict(kind='sem', n=n, label=f"sem {n}", term=term,
                        year=year_of_sem[n], slots=SLOTS_DEFAULT,
                        after_break=(break_after is not None and n > break_after)))
        term = 'F' if term == 'S' else 'S'
    if summers:
        # one session between each pair of academic years he is actually enrolled for
        for i, s in enumerate(list(out)):
            if s['term'] == 'S':                     # a summer follows every Spring
                out.append(dict(kind='summer', n=s['n'] + 0.5,
                                label=f"summer after sem {s['n']}", term='U',
                                year=s['year'], slots=SUMMER_SLOTS, after_break=s['after_break']))
    out.sort(key=lambda d: d['n'])
    return out


SLOTS_DEFAULT = 6      # 18 cr / 3 cr


def ledger_check():
    """Does the ledger add up to the degree? Returns (ok, lines)."""
    lines, tot = [], 0.0
    groups = {}
    for it in ITEMS:
        c = it["credits"] * it["count"]
        tot += c
        groups.setdefault(it["key"][:3] if it["key"] in ("ME", "DM") else it["key"], 0)
    cc  = sum(i["credits"]*i["count"] for i in ITEMS
              if i["key"] in ("Chapel", "LHP", "Lang", "SciRD", "WCiv", "Seminar"))
    mr  = sum(i["credits"]*i["count"] for i in ITEMS
              if i["key"] in ("QRM1001", "ECO1101", "ECO2102", "ECO2101", "MR5", "QRM3003"))
    me  = sum(i["credits"]*i["count"] for i in ITEMS if i["key"] == "ME")
    dm  = sum(i["credits"]*i["count"] for i in ITEMS if i["key"] == "DM")
    fr  = sum(i["credits"]*i["count"] for i in ITEMS if i["key"] == "FREE")
    lines.append(f"  CC remaining      {cc:6.1f}   (expected 19.5, R27)")
    lines.append(f"  MR                {mr:6.1f}   (expected 18.0, R31)")
    lines.append(f"  ME                {me:6.1f}   (expected 18.0 under a double major, R31)")
    lines.append(f"  2nd major         {dm:6.1f}   (expected 36.0-39.0, R31)")
    lines.append(f"  Free electives    {fr:6.1f}   (RESIDUAL — R181)")
    lines.append(f"  {'-'*44}")
    lines.append(f"  ledger total      {tot:6.1f}")
    lines.append(f"  degree remaining  {TOTAL_CREDITS - DONE_CREDITS:6.1f}"
                 f"   (126 - {DONE_CREDITS} done)")
    ok = abs(tot - (TOTAL_CREDITS - DONE_CREDITS)) < 1e-6
    lines.append(f"  {'MATCH' if ok else 'MISMATCH — the ledger is wrong'}")
    return ok, lines


def slots_check():
    """Do the items even fit in the slots? Capacity vs demand, before any quality."""
    lines = []
    n_sem = len(SEMESTERS) - 1                       # sems 3-8; Fall 2026 handled separately
    cap_cr = n_sem * CREDIT_CAP
    lines.append(f"  semesters after Fall 2026 : {n_sem}")
    lines.append(f"  credit capacity           : {cap_cr:.1f}  ({n_sem} x {CREDIT_CAP})")
    return lines


if __name__ == "__main__":
    print("=" * 74)
    print("SEMESTER SKELETON")
    print("=" * 74)
    for sem, label, term, yr, camp in SEMESTERS:
        print(f"  sem {sem}  {label:12s}  {'Spring' if term=='S' else 'Fall  '}  "
              f"year {yr}   campus {camp or '(free)'}")
    print(f"\n  Springs = sems 3/5/7 · Falls = 2/4/6/8")
    print(f"  minimum 국제 semesters = {MIN_INTL_SEMESTERS}  (sem 2 forced + one Spring "
          f"for QRM3003) — R144")

    print()
    print("=" * 74)
    print("REMAINING-REQUIREMENT LEDGER")
    print("=" * 74)
    print(f"  {'item':10s} {'label':30s} {'cr':>5} {'x':>3} {'yr':>3} "
          f"{'campus':6s} {'trm':3s} {'supply':>7}")
    print("  " + "-" * 70)
    for it in ITEMS:
        print(f"  {it['key']:10s} {it['label']:30s} {it['credits']:5.1f} "
              f"{it['count']:3d} {str(it['chart_year'] or '-'):>3} "
              f"{it['campus']:6s} {it['terms']:3s} {it['supply']:7d}")
    print()
    ok, lines = ledger_check()
    print("CREDIT RECONCILIATION")
    for l in lines: print(l)
    print()
    print("CAPACITY")
    for l in slots_check(): print(l)
    print()
    print("PROVISIONAL — needs Iden before any output is trusted:")
    for it in ITEMS:
        if "[P]" in it["note"]:
            print(f"  · {it['key']:9s} {it['note']}")
