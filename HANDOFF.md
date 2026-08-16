> ⚠️ **HISTORY ONLY — superseded 2026-08-07. Do not act on this file.** Facts here may be out of date; `MODEL.md` is authoritative for the model and `REQUIREMENTS_AUDIT.md` for the degree. Kept because it records elicited statements and evidence held nowhere else. See `INDEX.md`.

# HANDOFF — Iden's Yonsei UIC Course Planning

**Written:** 2026-08-04 · **For:** any AI or person picking this up cold, with zero prior context.
**Read this whole file before doing anything.** Then read `RULES.md` (40 verified rules).

---

## 0. THE SINGLE MOST IMPORTANT THING

**Do not invent, assume, or default anything on Iden's behalf.**

This project went wrong repeatedly because the assistant kept encoding its own judgments as
Iden's model — preset priorities, hidden courses, invented weights, "recommended" picks baked
into tooling. Iden caught every one. The final instruction was explicit:

> "I want to strip this from all bias… You are literally just giving me a good timetable that
> you think is good at this point. Do you not know the meaning of what 'brute force' means?
> I want numbers, not weird suggestions."

**Build mechanisms. Leave values empty. Output numbers. Let Iden decide.**

If you catch yourself writing a default priority, a recommended course, or a hidden option —
stop and ask instead.

---

## 1. WHO

- **Iden** — Yonsei University, Underwood International College (UIC)
- **Entry year: 2026** (this matters — requirement tables differ by 학번; use the **2026~** column)
- **Division:** HASS (Humanities & Social Sciences)
- **Major:** QRM — Quantitative Risk Management (계량위험관리)
- **Currently:** finished Semester 1 (Spring 2026). Registering for **Semester 2 (Fall 2026)**.
- **Double major:** ~85% likely, undecided which. Cannot apply until Sem 3 (Spring 2027).

### Iden's stated preferences (from Iden, not inferred)
- Strongly prefers **신촌 (Sinchon)** campus over **국제 (Songdo/International)**.
- The problem with Songdo is the **2-hour commute**, not Songdo itself. Therefore:
  **pure-campus semesters beat mixed semesters**, even if that means more Songdo semesters total.
- Wants requirements **separated from** "good-if-done" bonuses, so *Iden* can compare timetables.
- Language of instruction (Korean vs English) **does not matter** to Iden.
- 미래/원주 (Mirae/Wonju) campus is **completely irrelevant** — different school, out of reach.
  Filter it out of every dataset. (Watch for ECN-prefix courses + 강원도 addresses = wrong school.)

---

## 2. THE IMMEDIATE DEADLINE

**신입생 수강신청 (freshman registration): 2026-08-25, 09:00–17:00 KST.**

- Freshman round is **first-come, first-served** — NOT the mileage system (R7).
- Mileage only starts from Semester 3.
- Iden is **locked to 국제 campus** for Fall 2026: freshmen taking RC Education cannot take
  Sinchon courses (R8, UIC Guide §2.5). This is a hard constraint, not a preference.

Other dates (from 강의계획서, apply to all Fall 2026 courses):
| Date | Event |
|---|---|
| 2026-08-10 ~ 08-14 | 수강신청 (returning students) |
| **2026-08-25** | **신입생 수강신청 ← Iden** |
| 2026-09-01 | 개강 |
| 2026-09-03 ~ 09-07 | 수강신청 확인 및 변경 |
| 2026-10-13 ~ 10-15 | 수강철회 (withdrawal) |
| 2026-10-20 ~ 10-26 | 중간시험 |
| 2026-10-27 ~ 10-29 | S/U 평가신청 |
| 2026-12-15 ~ 12-21 | 기말시험 |

---

## 3. GRADUATION REQUIREMENTS (QRM, 2026~ entrant) — 126 credits total

Source: `QRM_Graduation_Requirement_table (2022~).pdf`, **2026~ column** (in Downloads).

### Common Curriculum (CC) — 36 + 3 language = 39 cr
| Requirement | Cr | Status for Iden |
|---|---|---|
| Chapel | 2 | ⏳ 0.5/2 — **3 more passes needed** (4 × 0.5cr) |
| Understanding Christianity | 3 | ✅ DONE (기독교와세계문화) |
| Freshman Writing Intensive Seminar | 3 | ✅ DONE (UIC1101) |
| CC L-H-P Series (2 of 3 categories) | 6 | ⏳ 3/6 — World Philosophy done; **need World History OR World Literature** |
| Language | 3 | ❌ not started — **any** language course, incl. non-UIC |
| Science Literacy **OR** RDQM | 3 | ❌ not started — **this is a CHOICE, either satisfies** |
| Critical Reasoning | 3 | ✅ DONE |
| UIC Seminars | 6 | ❌ not started — see R15/R22/R23 |
| Western Civilization | 3 | ❌ not started |
| Eastern Civilization | 3 | ✅ DONE |
| Social Engagement | 0 | ✅ **EXEMPT** (2023+ UIC entrants, R35) |
| Yonsei RC101 | 1 | ✅ DONE — **one-time, 1st semester only, never repeats** (R34) |
| UICE Introduction to Statistics | 3 | ✅ DONE (통계학입문) |

**CC remaining: 19.5 cr** — Chapel ×3 (1.5) · L-H-P 2nd (3) · Language (3) ·
SciLit-or-RDQM (3) · UIC Seminars ×2 (6) · Western Civ (3)

### Major Required (MR) — 18 cr, ALL still outstanding
1. Introduction to Quantitative Risk Management (QRM1001)
2. **Microeconomics** (ECO2102 — 신촌, 상경대학)
3. **Macroeconomics** (ECO2101 — 신촌, 상경대학)
4. Mathematics for Economics 1
5. Mathematical Statistics 1 (QRM3005, retitled "Mathematical Statistics") **OR** Regression Analysis
6. Principles of Financial Engineering (QRM3003)

⚠️ 2022–2025 entrants had "Fundamental Economic Analysis" + "Macro **or** Micro".
**2026~ entrants need BOTH Micro AND Macro**, and QRM2001 Fundamental Economic Analysis
became an **elective** (R40, confirmed in catalogue 유의사항).

⚠️ Since Fall 2024, only **QRM-department** Math Stat 1 / Regression Analysis count as major
credit — 응용통계학과 versions do NOT.

### Major Electives (ME) — 24 cr, ALL still outstanding
- Drops to **18 cr if Iden completes a double major** (42 → 36 major subtotal). MR unchanged.
- Korean-course cap: max **4 courses / 12 cr** from 상경대학 + 응용통계학과 taught in Korean
  may count toward the QRM major. (Does not limit a *second major's own* requirements.)

### Completed — Semester 1, Spring 2026 (19.5 cr, ALL Common Curriculum)
| Course | Prof | Schedule |
|---|---|---|
| Critical Reasoning | 남기혁 | Mon 9–10 · Wed 10–11 |
| 채플 (A) | 정대경 | Tue 10–11 |
| Freshman Writing Intensive Seminar | 스타이너코리깁슨 | Tue 12–1 · Thu 1–3 |
| 통계학입문 | 필립스다피드 | Mon 1–2 · Wed 1–2 |
| Yonsei RC 101 | 김현상 | Tue 2–3 · Wed 4–5 |
| Eastern Civilization | 장화사 | Mon 3–4:50 · Wed 3–3:50 |
| 기독교와세계문화 | 백영민 | Tue 3–4 · Thu 4–5 |
| World Philosophy | 호조렘산타나안드레 | Tue 4–5 · Thu 3–4 |

**Sem 1 contained ZERO major courses.** All 42 cr of MR+ME remain for Sems 2–8.
**Remaining to graduate: 106.5 cr over 7 semesters ≈ 15.2 cr/sem average.**
**Iden has taken NO calculus and NO programming course.**

---

## 4. HARD CONSTRAINTS (filters — never scoring axes)

1. **Fall 2026 = 국제 campus only** (R8). Non-negotiable for this semester.
2. **No time conflicts.**
3. **Credit cap:** 19 cr for freshmen (18 for sophomore+). **Chapel, RC자기주도활동, Social
   Engagement, UT Seminar, Volunteer Service, Military Science are EXEMPT from the cap** (R37).
4. **Eligibility notes in 유의사항** — e.g. UIC1653 is "UIC-ICU LearnUs program students only",
   Iden is not eligible (R39).
5. **UIC Seminars:** exactly 2 (6cr), **max 1 per semester**, window = **Sem 4–7 only**
   (R15/R22/R23). Identified by code regex `^UIC3[56]\\d\\d` (R4).

### NOT constraints (common misreadings — all verified)
- **학년 column in the catalogue is ADVISORY**, not a gate (R1). Proven: a 학년-2 student
  enrolled in UIC1101, which is labelled 학년 1.
- **학년별정원 all-zeros ≠ prohibition.** That table is scoped to the **mileage round only**;
  freshmen use first-come and are structurally invisible in it (R25). Proven: SOC1002 — a
  heavily-enrolled freshman course — has **no mileage record at all**.
- **QRM3003 is NOT year-3-locked** (R29). Earlier claim withdrawn. It is Spring-only
  (0 rows in Fall 2026). Any year restriction is unverified.
- **No published prerequisite or year-gate exists for ECO2102** (R19).

---

## 5. MILEAGE SYSTEM (irrelevant for Fall 2026; matters from Sem 3)

- Total = **4 × max credits**. Sophomore+ 18cr → **72M/semester**.
- Per-course bid 1–36; max-36 bids on ≤2 courses.
- **"Max Mileage" is a PER-COURSE cap set by the department, not the universal 36** (R3):
  - **Cap 12** (UIC First ECO courses, UIC Seminars): everyone bids the cap (avg 11.5–11.8).
    Bid size is NOT a lever — placement decided by tie-break ladder.
  - **Cap 36** (general 신촌 CC): real bidding, wide spread.
- **UIC First** courses auto-enroll if applied in their own round; 4 × credits auto-deducted.
- Tie-break ladder (R10): mileage → special-ed → **designated major of offering dept** →
  more courses applied (≤6) → graduation applicants → first-time takers → credit ratio.

### Observed competition data (2 semesters sampled)
| Course | Campus | Cap | Min | Max | Avg | 정원 | 참여 | Ratio |
|---|---|---|---|---|---|---|---|---|
| UIC1251 World Lit E.Asian | 신촌 | 36 | 5 | 36 | **19.1** | 19 | 41 | 2.16:1 |
| ECO2102 미시경제학 | 신촌 | **12** | 5 | 12 | **11.82** | 59 | 109 | 1.85:1 |
| UIC2151 RDQM | 신촌 | 36 | 1 | 15 | **7.4** | 19 | **10** | **0.53:1** |
| UIC3512 Seminar | 신촌 | **12** | 1 | 12 | **11.52** | 16 | 27 | 1.69:1 |
| UIC1101 FWIS | 국제 | 36 | 14 | 14 | 14 | 2 | 1 | 0.5:1 |

⚠️ Many sections are tiny (정원 2–19) — small-n makes averages weak evidence (R6).

---

## 6. DOUBLE MAJOR (undecided, ~85% likely)

**Iden CAN double-major OUT of UIC into other colleges** (R32). Official rule:
> "언더우드국제대학 및 글로벌인재대학 내 전공은 해당대학 소속 학생에 한하여 지원 가능"

This blocks non-UIC students coming **in**; it does not block UIC students going **out**.
Blocked destinations for everyone: 건축학(5년제), 시스템반도체공학과, 디스플레이융합공학과,
음악대학, 의학, 치의학, 간호학, 약학. None of Iden's candidates are blocked.

- **Apply from Semester 3** (Spring 2027). Fall 2026 cycle ran 6/23–6/29, results 7/24 —
  expect the Spring window ~Dec 2026.
- **Competitive:** selects ≥ min(50% of applicants, 30% of dept quota), judged on
  **cumulative GPA** + 지원동기 + 학업계획 (500–2000 chars each).
- ⚠️ **At application time Iden's GPA = Sem 1 + Sem 2 only.** Fall 2026 grades directly
  determine double-major admission.
- Reversible: cancellable up to the semester before graduation.

### Candidates (Fall 2026 section counts; 신촌 is the university default, 국제 is the UIC exception)
| | Economics 경제학 | Applied Stats 응용통계학 | Business 경영학 |
|---|---|---|---|
| Fall 2026 sections | 70 | 26 | 125 |
| at 신촌 | 64 (91%) | 22 (85%) | 121 (97%) |
| Overlap with QRM | **Micro + Macro are BOTH QRM MR courses** | Math Stat blocked by QRM-dept rule | finance courses only |

⚠️ **Requirement tables for these three have NOT been fetched.** The 신촌 경제학부 page
(economics.yonsei.ac.kr) shows 2025학번 이후: 전공기초 (미시경제원론, 거시경제원론, 미분적분학,
통계방법론, R/Python), 전공필수 (경제수학1, 미시경제학, 거시경제학), 전공선택 24cr single-major.
The **double-major** elective count for 2025+ is **not published there** — needs the 졸업일람표.
⚠️ Do NOT use econ.yonsei.ac.kr — that is **원주/미래 campus** (ECN codes), wrong school.

---

## 7. DATA FILES (in `C:\\my\\수강신청\\`)

| File | What it is |
|---|---|
| `RULES.md` | **40 verified rules with evidence.** The authoritative reference. Read it. |
| `HANDOFF.md` | This file. |
| `강의목록_2026F.xlsx` | Full Fall 2026 catalogue, **1,690 sections** (827 국제 / 863 신촌) |
| `fetch_2026_fall.py` | Portal scraper. Needs a fresh JSESSIONID each run. `SMT="20"` = Fall |
| `all_kj.json` | **661 국제 sections** with parsed time blocks — the brute-force input |
| `pools_min.json` | Narrowed pools (BIASED — built from assistant's assumptions, see §9) |
| `수강신청_Fall2026.html` | Current artifact (BIASED — Iden rejected its framing, see §9) |
| `SESSION_LOG_2026_COURSE_PLANNING.md` | Earlier narrative log |
| `FINDINGS.md`, `artifact.html`, `plans*.json`, `data_compact.json` | **STALE** — from an earlier pass on an incomplete 1,224-row catalogue. Do not trust. |

In `C:\\Users\\happy_mb3whk1\\Downloads\\`:
- `QRM_Graduation_Requirement_table (2022~).pdf` — **authoritative requirements**
- `2026 Spring UIC Course Enrollment Guide_260114.pdf` — mileage rules, RC rules, CC descriptions

### Portal access notes
- URL: `https://underwood1.yonsei.ac.kr/com/lgin/SsoCtr/initExtPageWork.do?link=handbStdntBusns`
- Course list endpoint: `POST /sch/sles/SlessyCtr/findAtnlcHandbList.do`
- Mileage endpoint: `POST /sch/sles/SlessyCtr/findMlgRankResltList.do`
- 마일 and 계획 popups are **in-page modals**, readable via page text — but they
  **frequently hang under browser automation**. The sandbox cannot reach the portal directly
  (proxy 403). Iden can download 강의계획서 as `Report.pdf` manually — that worked.
- Mileage popup has its **own 학년도/학기 dropdown** — must be set to a *completed* semester
  or it returns empty (R26).
- Searching by 학정번호 returns the course across **2023-1 … 2026-2** (R5).

---

## 8. WHERE THE WORK STOPPED

Iden asked for **true brute force**. Measured facts:

- **661 국제 sections** have parseable time slots
- C(661,5) = **1.04 × 10¹²**, C(661,6) = **1.13 × 10¹⁴** → **exhaustive enumeration over the
  full catalogue is not computable**
- pairwise conflict rate: **11.0%** → conflict-pruning barely helps
- **169 distinct time patterns**; 453 sections share a pattern with ≥5 others
  → sections are highly degenerate in time; enumerating over *patterns* is tractable

Three options were put to Iden, who is **still deciding**:

- **A** — Iden picks the candidate set (any size ~≤40), brute force every conflict-free
  combination of it, output the full table.
- **B** — Enumerate all 169 time patterns: every conflict-free *shape* of a week at a given
  course count, plus which sections can fill each position.
- **C** — Iden states grid constraints ("Friday empty, nothing before 3교시") and gets every
  satisfying combination from all 661, exhaustively.

**No option chosen yet. Do not pick for Iden.**

### Scoring axes Iden defined earlier (as COLUMNS to sort by, not a composite score)
- **Lunch:** any day with class must have ≥1 free period among 3·4·5교시. Scored penalty,
  not a hard block (Iden changed this from hard-block deliberately).
- **Early start:** convex `n^1.4` where 1교시 = 1.0, 2교시 = 0.5.
- **Blank weekdays:** Fri 12 / Mon 9 / Midweek 5, with stacking bonus `8·(m−1)²`.
  ⚠️ These specific numbers came from Iden's own earlier system — **re-confirm before reusing.**
- **Professor ratings:** −2..+2, ×4 multiplier. **No data exists.** Iden would supply it.

### Fall 2026 requirement-relevant 국제 offerings (all verified present)
| Slot | Options | Notes |
|---|---|---|
| QRM1001 Intro to QRM | **1** section, 목4,5,6 | only one exists |
| Western Civilization | 3 (UCB1103, YCE1253, UIC1561) | |
| L-H-P 2nd (World History/Literature) | 15 usable | UIC1653 excluded (R39) |
| RDQM | 13 sections | *or* Science Literacy — a choice |
| Chapel B | 7 sections | 0.5cr, cap-exempt |
| QRM electives (2000-level) | QRM2001, QRM2002, QRM2004, QRM2102 | see below |
| Language | 93 국제 sections | any language counts |

**Prerequisite verification (R38, from official 강의계획서 PDFs):**
| Course | Time | 선수 추천과목 | Grading |
|---|---|---|---|
| QRM2004 Statistical Analytic Methods | 화4,5,6 | **(empty)** | 과제60/기말30/출석10, no real midterm; Python-based |
| QRM2002 Financial Data Analysis | 금1,2,3 | **(empty)** | not populated |
| QRM2102 Linear Algebra & Diff Eq | 금5,6,7 | **"Single-variable and Multivariable Calculus courses"** | 중간25/기말25/퀴즈30/출석20 |

QRM2102's field says 선수 **추천**과목 (*recommended*), not 선수과목 (*required*) — so it
likely does not block registration. **Iden has taken no calculus.** That is a fact for Iden
to weigh, **not** a reason to hide the course. (The assistant hid it by default; Iden objected.)

Attendance rule on all courses: **>1/3 absence = automatic F/NP** regardless of exams.

---

## 9. MISTAKES MADE — DO NOT REPEAT

Every one of these was caught by Iden, not by the assistant.

1. **Read Spring data as Fall.** Fetch the actual semester (`SMT="20"`).
2. **Invented requirements** from a 6-month-old file instead of the official PDF.
3. **Claimed all UIC Seminars were Songdo-only** from one thin sample. Fall has 39 at 신촌.
4. **Claimed "no Korean 금융공학"** after searching an incomplete dataset.
5. **Read 학년 as a gate** (R1) — twice, including inventing a year-lock on QRM3003 (R29).
6. **Read all-zero 학년별정원 as "freshmen banned"** (R25). Absence in a mechanism-scoped
   table ≠ prohibition. **This error was made three times in different forms.**
7. **Lost user-stated facts to context compaction, then "re-derived" them and presented them
   as the assistant's own discovery** (R20/R21). Iden had already said Critical Reasoning and
   Eastern Civ were taken. **Log user-stated facts the same turn they are said.**
8. **Set a credit filter default (18.0) that was unreachable** (max was 15.5) — the UI showed
   "no plans" at every setting. Also told Iden a second elective was possible when the code
   never added one.
9. **Collapsed requirements and preferences into one structure**, destroying the separation
   Iden asked for in the very first message.
10. **Baked opinions into tooling**: preset priority tiers, "ME elective #1 / #2" implying two
    electives, a "hide calculus-prereq courses" toggle on by default, invented point values
    (25/12/5), and a "recommended pick" whose logic was then built into the artifact while
    claiming the artifact was neutral.
11. **Used 원주/미래 campus data** (econ.yonsei.ac.kr, ECN codes) for 신촌 Economics.

### The recurring pattern
Correct → rebuild fast and confidently → introduce new unrequested assumptions → Iden has to
catch those too. **Slow down. Ask. Output numbers. Let Iden choose.**

---

## 10. OPEN QUESTIONS

| # | Question | Why it matters |
|---|---|---|
| 1 | Which brute-force approach — A, B, or C? | Blocks all further work |
| 2 | Which double major? | Changes ME 24→18 and all of Sems 3–8 |
| 3 | 경제학/응용통계/경영 double-major requirement tables | Not fetched; 졸업일람표 needed |
| 4 | Spring 신촌 UIC Seminar availability | Seminars are Sem 4–7 window-locked; if Spring 신촌 has none, both must be Fall |
| 5 | Are the blank-day values (Fri 12 / Mon 9 / mid 5) still what Iden wants? | Carried over from an old system |
| 6 | Professor ratings | No data source exists |
| 7 | Full competition history for 국제 sections | Portal blocks automation; would need manual pulls |
| 8 | QRM prerequisite chains beyond the 4 checked 2000-level courses | Only 3 syllabi verified so far |

---

## 11. QUICK START FOR A COLD AI

1. Read `RULES.md` end to end — 40 rules, each with its evidence.
2. Load `all_kj.json` — 661 국제 sections, time blocks pre-parsed.
3. Ask Iden which of A/B/C from §8 to run. **Do not choose.**
4. Output tables of numbers. No composite score unless Iden defines the weights.
5. When you learn something from Iden, append it to `RULES.md` **in that same turn.**
