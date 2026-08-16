# -*- coding: utf-8 -*-
"""
tiebreak.py — the 동점자 우선순위 ladder. Sourced, not inferred.

WHY IT MATTERS MORE THAN IT SOUNDS
----------------------------------
R190 established that mileage statistics are over APPLICANTS, so winning a small contested
section means finishing in the top-N of the bid distribution — and when several people bid
the ceiling, **the ladder decides, not the bid.** Measured: it decides
  · 7 of 8 observed UIC1806 국제 sections
  · 2 of 5 observed UIC1805 국제 sections
  · EVERY cap-12 course, including **ECO1101** — a Major Required course (R3)
It was the single largest unmodelled mechanism in the project.

SOURCE — two official documents, verbatim and in agreement
-----------------------------------------------------------
`★2026학년도 2학기 수강편람` §2-1-① and `연세대학교 수강신청 제도안내` §3-3.

    ⓐ 높은 마일리지를 배분한 학생 우선
    ⓑ 특수교육대상자 우선
    ⓒ 개설학과에서 설정한 전공자 우선          (제도안내: "전공생 및 복수전공생 우선")
    ⓓ 총 수강신청 과목수가 많은 학생 우선       (최대 6개까지만 반영, 수강허용학점 예외 과목 제외)
    ⓔ 마일리지 기간 종료 시점의 졸업/수료 신청자 우선
    ⓕ 초수강자 우선                             (재수강이 아닌 학생)
    ⓖ 총이수학점 / 졸업이수학점 비율이 높은 학생 우선      (최대 1.00)
    ⓗ 직전학기이수학점 / 학기당수강가능학점 비율이 높은 학생 우선  (최대 1.00)
    ⓘ 동점이면 난수

⭐ TWO RUNGS ARE LEVERS IDEN CONTROLS, AND ONE OF THEM RUNS THROUGH FALL 2026
-----------------------------------------------------------------------------
ⓗ uses **직전학기** — the PREVIOUS semester's credit load. So the number of credits taken in
Fall 2026 sets his tie-break rank in the Spring 2027 mileage round, and in every round after.
The ranker has always treated total credits as a free choice inside [17, 21] with no
consequence. **It has a consequence.**

ⓓ rewards applying for MORE courses, counted up to 6. Six academic courses is exactly the
number that maxes this rung, and chapel/RC are cap-exempt so they do not count toward it.

⭐ AND ONE RUNG IS A CONSEQUENCE OF THE DECEMBER DECISION
The 제도안내 wording is **"전공생 및 복수전공생 우선"** — double-majors get the offering
department's major priority. A declared Economics double major therefore lifts Iden above
non-majors on **ECO2101 and ECO2102**, both Major Required and both 신촌-only. That is an
acquisition advantage attached to a choice the model already tracks but never connected here.

⚠️ ⓖ RUNS THE OTHER WAY, AND IT IS WORTH KNOWING
총이수학점/졸업이수학점 rises monotonically as he progresses, so his tie-break position
IMPROVES every semester. The 제도안내 says so outright: *"총 이수학점이 높은 학생들(고학년)이
우선권을 갖는 것은 졸업을 위한 수강신청을 배려하기…"*. This is a genuine counterweight to
"acquire contested things as early as possible" — on this rung, later is strictly better.
It bites only at equal mileage, so it does not overturn ⓐ; it does mean the model should not
assume deferral is uniformly worse for acquisition.
"""
import os

LADDER = [
    ('a', '높은 마일리지',            'the bid itself'),
    ('b', '특수교육대상자',           'not applicable'),
    ('c', '전공자·복수전공생 우선',    'DEPENDS ON THE DECEMBER DOUBLE-MAJOR CHOICE'),
    ('d', '신청과목수 (최대 6)',       'LEVER — apply for 6 academic courses'),
    ('e', '졸업/수료 신청자',          'against him until his final year'),
    ('f', '초수강자',                  'in his favour — no retakes'),
    ('g', '총이수학점/졸업이수학점',    'improves automatically every semester'),
    ('h', '직전학기이수학점/수강가능학점', 'LEVER — set by THIS semester credit load'),
    ('i', '난수',                      'unmodellable by construction'),
]

# 수강편람 p.7 / R36: chapel, 사회봉사, 사회참여, RA리더십, RC자기주도활동, UT세미나,
# 진로개발세미나 and <=2cr ROTC are 수강허용학점 예외 — excluded from the ⓓ course count.
CAP_EXEMPT_PREFIXES = ('YCA', 'UCR', 'UCI')

MAX_COURSES_COUNTED = 6      # ⓓ caps the count at 6

# [M] 수강편람 "가. 2022학번 이후 학기당 수강학점": 졸업이수학점 126 → 전 학년 → 1~18.
# QRM is a 126-credit programme, so 18. ⚠️ This CORRECTS R86, which recorded 19.
ALLOWANCE = 18


def rung_d_score(section_codes):
    """ⓓ — how many of these count toward 'more courses applied for'."""
    n = sum(1 for c in section_codes if not c.startswith(CAP_EXEMPT_PREFIXES))
    return min(n, MAX_COURSES_COUNTED)


def rung_h_ratio(credits_taken, allowance):
    """ⓗ — 직전학기이수학점 / 학기당수강가능학점, capped at 1.00.

    ⚠️ 제도안내: the denominator EXCLUDES 초과신청 가능학점 ("직전학기이수학점의 분모에는
    초과신청 가능학점을 포함하지 않습니다"), so the GPA-3.75 bonus credits do not make this
    harder to max. The base allowance is what counts.
    """
    return min(1.0, credits_taken / float(allowance))


def fall2026_consequences(credits, n_academic_courses, allowance):
    """What a Fall 2026 timetable does to Iden's tie-break rank from Spring 2027 onward."""
    return {
        'rung_d_courses_counted': rung_d_score(['X'] * n_academic_courses),
        'rung_d_maxed': n_academic_courses >= MAX_COURSES_COUNTED,
        'rung_h_ratio': round(rung_h_ratio(credits, allowance), 4),
        'rung_h_maxed': rung_h_ratio(credits, allowance) >= 1.0,
    }


if __name__ == '__main__':
    print("=" * 78)
    print("동점자 우선순위 — the ladder that decides contested sections")
    print("=" * 78)
    for k, name, note in LADDER:
        print(f"  {k})  {name:26s} {note}")

    print()
    print("=" * 78)
    print("WHAT FALL 2026 DOES TO IT — the live #1 takes 6 academic courses, 18 credits")
    print("=" * 78)
    # ✅ RESOLVED from the 수강편람 table itself: "졸업이수학점이 126학점인 대학·학과·전공
    # 전 학년 ... 1~18". QRM is 126 credits, so the allowance is 18 — R86's 19 is wrong.
    # And the GPA-3.75 bonus is 초과신청, which the 제도안내 excludes from the denominator,
    # so 21 credits would NOT lower the ratio. 18/18 = 1.00 exactly.
    for allowance in (ALLOWANCE,):
        r = fall2026_consequences(18.0, 6, allowance)
        print(f"\n  if 학기당수강가능학점 = {allowance}:")
        print(f"    ⓓ courses counted : {r['rung_d_courses_counted']}/6   "
              f"{'MAXED' if r['rung_d_maxed'] else 'not maxed'}")
        print(f"    ⓗ ratio           : {r['rung_h_ratio']:.4f}   "
              f"{'MAXED' if r['rung_h_maxed'] else 'NOT maxed — a 19th credit would'}")
    print()
    print("  ✅ Allowance resolved from the 수강편람 table: 126-credit programme, 전 학년,")
    print("     1~18. R86's 19 is corrected. The GPA-3.75 bonus is 초과신청 and is excluded")
    print("     from ⓗ's denominator, so 18/18 = 1.00 exactly — rung ⓗ is maxed.")
    print()
    print("  ⏳ Still open on this ladder:")
    print("     ⓒ needs the December double-major choice (Economics would lift him above")
    print("        non-majors on ECO2101 and ECO2102, both Major Required, both 신촌-only)")
    print("     ⓖ improves automatically each semester — a counterweight to acquiring")
    print("        contested courses early. Bites only at equal mileage.")
