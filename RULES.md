# Standing Rules — 수강신청 / Course Planning
Persistent, reusable facts. Append new rules as they are verified; never delete a
rule without noting why. Each rule cites the evidence that established it.

---

## R1. 학년 (catalogue column) is ADVISORY, not a restriction
The `학년` column in 개설교과목 목록 is a **target-year label**. It does NOT gate enrollment.

**Evidence:** UIC1101 FRESHMAN WRITING INTENSIVE SEMINAR is labelled `학년 1`, but the
mileage ranking table for UIC1101-01-00 shows the enrolled student had **학년 = 2**.
A sophomore held a seat in a course labelled "1". (User observed this independently
in the wild; portal data confirms it.)

**Supporting:** the column holds ranges and nulls — `3,4`, `2,3,4`, `1,2`, `0` —
which only makes sense as advisory targeting. 681 of 1,690 Fall 2026 rows have `학년 = 0`.

**Use:** treat 학년 as a soft signal about course level/audience. Never use it to
exclude a course from a plan.

---

## R2. 학년별정원 (mileage popup) is the REAL year gate — and all-zeros means NO gate
The mileage popup (마일리지 수강신청 결과 조회) has a `학년별정원` block with six columns
(years 1–6). These are actual per-year seat allocations.

**Critical reading rule:** `0 0 0 0 0 0` does **NOT** mean "no year may enroll".
It means **no per-year sub-quota is configured**; the overall `정원` governs instead.

**Evidence:** UIC1101-01-00 shows 정원 2, 학년별정원 all zeros — yet 1 student
successfully enrolled (참여 1, winning bid 14).

**Corrects an earlier error:** I previously read ECO2102's `1학년 = 0` as "freshmen
cannot take Micro." That inference was WRONG per this rule. ECO2102's non-zero
values (2학년 35, 3학년 15, 4학년 9) alongside 1학년 0 may still indicate a real
freshman exclusion, but all-zero rows must not be read as universal exclusion.
**Status: ECO2102 freshman eligibility UNRESOLVED — needs separate confirmation.**

---

## R3. Max Mileage is a PER-COURSE cap, not the universal 36
The guide's 36 is the *student-side* limit (max bid on one course, ≤2 such bids).
Each course additionally carries its own `Max Mileage` ceiling set by the offering dept.

**Two observed classes:**
- **Cap 12** — UIC First ECO courses, UIC Seminars. Everyone bids the cap; avg lands
  11.5–11.8. Bid size is NOT a lever; placement decided by tie-break ladder.
- **Cap 36** — general 신촌 CC. Real bidding; spread is wide (7.4 to 19.1 observed).

**Evidence:** ECO2102 cap 12 (avg 11.82); UIC3512 cap 12 (avg 11.52);
UIC1251 cap 36 (avg 19.1); UIC2151 cap 36 (avg 7.4); UIC1101 cap 36 (avg 14).

---

## R4. UIC Seminars are identifiable by course code
Official 유의사항 text on UIC3512:
> "A UIC Seminar. Courses with course codes of **UIC35(XX) and UIC36(XX)** are UIC Seminars."

**Use:** regex `^UIC3[56]\d\d` — definitive. Supersedes all prior guessing about
which courses count toward the seminar requirement.

---

## R5. Portal exposes multi-year competition history per course
Searching by 학정번호 returns the same course across many semesters
(2023-1 … 2026-2 observed; UIC3512 returned 22 rows). Each row has its own 마일 popup.
Full historical competition series is retrievable per course.

**Endpoint:** `https://underwood1.yonsei.ac.kr/sch/sles/SlessyCtr/findMlgRankResltList.do`
(popup is in-page, not a separate window; readable via page text once loaded)

---

## R6. Small-n sections make competition history weak evidence
Many UIC sections are tiny (정원 2–19). A single interested student flips the outcome.

**Evidence:** UIC1101-01-00 — 정원 2, 참여 1, single bid of 14.

**Use:** weight historical avg bids by 참여인원. Treat n < 10 as directional only,
not predictive. Prefer the max across recent semesters over the mean for planning.

---

## R7. Freshman round is first-come (Wait List), NOT mileage
Mileage applies from sophomore year onward. Freshman enrollment date is a separate
first-come round; mileage totals are irrelevant to Fall 2026 itself.

**Evidence:** 2026 Spring UIC Course Enrollment Guide, §2.1–2.2.

**Use:** for Fall 2026 planning, competition history informs *add/drop pressure* and
*section desirability*, not bid strategy.

---

## R8. Freshmen taking RC Education cannot take 신촌 courses
> "Freshmen who must take RC Education cannot take courses offered at Sinchon Campus."

**Evidence:** 2026 Spring UIC Course Enrollment Guide, §2.5.

**Use:** Fall 2026 (Sem 2) is mandatorily all-국제. Not a preference — a hard constraint.

---

## R9. Mileage totals
- Total mileage = **4 × max credits per semester**
- Sophomore+ (18cr cap) → **72M**;  Freshman (19cr) → 76M (unused, see R7)
- Per-course bid 1–36, max-36 bids on ≤2 courses
- **UIC First**: applied in its own round, auto-enrolled, 4×credits auto-deducted
  (12M per 3cr course) from the mileage available in the later general round

**Evidence:** 2026 Spring UIC Course Enrollment Guide, pp. 6–9.

---

## R10. Tie-break ladder (decides cap-12 courses)
When bids tie (which is the norm at cap 12):
1. higher mileage allocated
2. special-education status
3. **designated major of the offering department**  ← QRM courses favour Iden
4. more courses applied for (up to 6 counted; chapel/volunteer/seminar excluded)
5. graduation / completion applicants
6. first-time takers (not repeating)
7. higher earned/required credit ratio (max 1.00)

**Evidence:** Guide §2.2(2); confirmed by popup column headers.

---

## R11. Verify field semantics before inferring constraints
Two errors this session came from reading a column's name and assuming its meaning
(학년 as a gate; all-zero 학년별정원 as exclusion). Both were caught by the user
citing real-world observation.

**Use:** before treating any catalogue field as a hard constraint, find a case that
would violate it and check whether that case exists. Prefer observed enrollments over
column labels.

---

## R12. All-zero 학년별정원 correlates with UIC-run courses, not with freshman exclusion
Refines R2. The all-zero pattern is not about freshmen specifically — it reflects that
**UIC departments do not configure per-year quotas at all**.

**Evidence (Fall 2026 / recent semesters):**

| Course | Offering dept | 학년별정원 (1–6) |
|---|---|---|
| UIC1101 Freshman Writing | UIC 공통교과과정 | `0 0 0 0 0 0` |
| UIC1251 World Lit | UIC 공통교과과정 | `0 0 0 0 0 0` |
| UIC2151 RDQM | UIC 공통교과과정 | `0 0 0 0 0 0` |
| UIC3512 Seminar | UIC 공통교과과정 | `0 0 0 0 0 0` |
| **ECO2102 미시경제학** | **상경대학 경제학전공** | **`0 35 15 9 0 0`** |

4/4 UIC-run courses are all-zero; the sole non-UIC course carries real quotas.

**Use:** for UIC courses, ignore 학년별정원 entirely — it carries no information.
For non-UIC courses (ECO/BIZ/STA etc.), the quotas are real and must be checked.

---

## R13. ECO2102 freshman eligibility remains UNRESOLVED (two hypotheses, same signature)
ECO2102 shows `1학년 = 0` while other years are non-zero. Two competing explanations
produce an identical pattern:

- **H1 — real gate:** Micro is genuinely sophomore+ (course is labelled 학년 2, has
  prerequisite structure), so no freshman seats are allocated.
- **H2 — artifact of the enrollment system** (user's hypothesis): 상경대학 allocates
  per-year quotas only to year-groups that bid through the **mileage** round. Freshmen
  enroll via the separate **first-come** round (R7), so they never appear in the
  mileage-side quota table.

**Why the ranking list cannot settle it:** under BOTH hypotheses, zero 학년 1 students
appear in the mileage ranking — under H1 because they're barred, under H2 because they
don't bid. Absence of freshmen in the ranking is therefore not evidence for either.

**Resolution requires:** the 수강편람 prerequisite note for ECO2102, the course syllabus
(선수과목 field), or asking 상경대학/학사지원팀 directly.

**Practical impact for Fall 2026: NONE.** Sem 2 is mandatorily 국제 (R8) and ECO2102 is
신촌, so Micro is out of scope this semester regardless of which hypothesis is true.
Revisit before Sem 3 planning.

**Supersedes:** the earlier claim "freshmen literally cannot take ECO2102." That was
stated with unwarranted confidence and is withdrawn.

---

## R14. Distinguish structural absence from prohibition
Recurring failure mode this session: reading a zero/blank as "forbidden" when it
actually means "this population is handled by a different mechanism."

Both R2 and R13 arose this way. A zero in a table scoped to mechanism X tells you
nothing about populations that use mechanism Y.

**Use:** before reading absence as prohibition, ask *which mechanism is this table
scoped to, and who is outside that mechanism?* If a plausible structural explanation
exists, mark the finding unresolved rather than asserting the restriction.

---

## R15. UIC Seminars are WINDOW-LOCKED (Sem 4–7), not freely placeable
> "Underwood Division Humanities & Social Sciences students will take one UIC Seminar
> per semester (3 credits each) **from the second semester of their sophomore year
> through the first semester of their senior year.**"
> — 2026 Spring UIC Course Enrollment Guide, CC section (UD HASS)

**Window = Sem 4, 5, 6, 7.** QRM requirement table mandates 6 credits = 2 seminars.

**Planning impact:** Sem 5 (the Songdo semester in both Plan A and Plan B) falls INSIDE
the seminar window. Earlier plans treated seminars as freely schedulable — WRONG.
Either a seminar is taken from the 국제 pool during Sem 5, or seminars are concentrated
in Sems 4/6/7. Must be modeled explicitly.

**Seminar identification:** `^UIC3[56]\d\d` (R4).

---

## R16. ⚠️ CONFLICT: seminar count — 4 (guide) vs 2 (QRM table)
- **Guide (UD HASS general):** "Students are required to take **4** UIC Seminars"
  (reduced to 3 if one exchange semester, 2 if two exchange semesters)
- **QRM Graduation Requirement table (2022~ and 2026~):** UIC Seminars = **6 credits** = 2 seminars

These are inconsistent. QRM-specific table should govern for a QRM major, but this is a
**6-credit graduation-requirement discrepancy**.

**ACTION REQUIRED: confirm with UIC academic advisor before finalizing the 4-year plan.**
Status: UNRESOLVED. Do not treat either number as settled.

---

## R17. Corrected CC requirement list for QRM 2026~ entrants (Iden)
Source: `QRM_Graduation_Requirement_table (2022~).pdf`, column **2026~**.
This SUPERSEDES all earlier CC composition assumptions.

| Requirement | Credits | Notes |
|---|---|---|
| Chapel | 2 | 4 passes × 0.5cr |
| Understanding Christianity | 3 | 1st-year course |
| Freshman Writing Intensive Seminar | 3 | UIC1101 |
| CC L-H-P Series | 6 | pick 2 of 3 categories (World History / Literature / Philosophy) |
| **Language** | **3** | **1 course only** — UIC Language&Arts OR **any non-UIC language course** |
| Science Literacy **OR** RDQM | 3 | **a CHOICE** — RDQM (UIC2151) is the cheap path (avg bid 7.4) |
| **Critical Reasoning** | 3 | **mandatory, separate** |
| UIC Seminars | 6 | see R15/R16 |
| **Western Civilization** | 3 | required |
| **Eastern Civilization** | 3 | required |
| Social Engagement | 0 | **EXEMPT** for 2022+ entrants |
| Yonsei RC101 | 1 | |
| UICE Introduction to Statistics | 3 | sits in **CC**, not major |
| **Subtotal** | **36 + 3 (language) = 39** | |

**Errors corrected:** Language was 3cr not 6cr; Eastern Civ was missing; Critical
Reasoning was missing entirely; RDQM was treated as required when it's one of two options;
Intro to Statistics was misfiled under major.

---

## R18. MR list for 2026~ entrants — both Micro AND Macro (no "or")
2022~2025 column read: "Fundamental Economic Analysis" + "Macroeconomics **or** Microeconomics".
**2026~ column reads: "Microeconomics" + "Macroeconomics"** — both required, no choice,
and Fundamental Economic Analysis is gone.

MR (18cr) for Iden:
1. Introduction to Quantitative Risk Management
2. **Microeconomics**
3. **Macroeconomics**
4. Mathematics for Economics 1
5. Mathematical Statistics 1 (QRM3005, retitled "Mathematical Statistics") **or** Regression Analysis
6. Principles of Financial Engineering (QRM3003)

**Constraint:** since Fall 2024, only Math Stat 1 / Regression Analysis offered by the
**QRM department** count as major credit (not 응용통계학과 versions).

**Korean-course cap:** of QRM courses taken from 상경대학(School of Economics) and
응용통계학과 taught in Korean, **max 4 courses (12 credits)** count as Major Credits.

---

## R19. No published prerequisite or year-gate exists for ECO2102
Neither the QRM requirement table nor the enrollment guide states any year restriction
or prerequisite for Microeconomics. The `1학년 = 0` quota (R13) therefore has **no
documentary basis as a prohibition**.

This strengthens H2 (user's hypothesis: quota table is scoped to the mileage round, and
freshmen are structurally absent because they use first-come). Still not positively
confirmed, but no official source contradicts it.

**Status:** H2 favoured; no action needed for Fall 2026 (国际-locked, ECO2102 is 신촌).

---

## R20. ⚠️ COMPLETED COURSES — Iden, Spring 2026 (Sem 1). DO NOT RE-DERIVE.
**Confirmed by Iden. These are DONE and must be subtracted from all remaining plans.**

- **Critical Reasoning** (3cr, CC) — COMPLETED Sem 1
- **Eastern Civilization** (3cr, CC) — COMPLETED Sem 1

*(This list is incomplete — see ACTION below. Other Sem 1 courses must be added.)*

**Correction to R17:** R17 listed Critical Reasoning and Eastern Civ as if newly
discovered requirements I had "omitted." That framing was WRONG. Iden had already told
me both were taken; the fact was lost to context compaction, then re-derived from the
PDF and mislabeled as my own correction. The requirements were never missing from the
plan — they were **already satisfied**.

**ACTION: retrieve full Sem 1 (Spring 2026) transcript from Notion and log it here
permanently.** Every future plan must start from completed-courses state, not from the
full requirement table.

---

## R21. Context compaction is a data-loss hazard — log user-stated facts IMMEDIATELY
This session lost at least one user-stated fact (R20) to compaction, then re-derived it
incorrectly and presented it as a new finding.

**Rule:** any fact the user states about their own history, preferences, or constraints
gets written to RULES.md or the session log **in the same turn it is stated**. Never rely
on conversation context to carry a user-supplied fact across turns.

**Tell for this failure:** if I am about to present something as a "correction" or
"discovery" that concerns the user's own record, check the logs first — the user very
likely already told me.

---

## R22. Seminar count = 2 (6 credits) — user-confirmed; supersedes R16 conflict
Iden confirms **2 seminars / 6 credits** (QRM requirement table), not the 4 stated in the
guide's general UD HASS section. QRM-specific table governs.

**R16 status: RESOLVED.** Plan for 2 seminars.

## R23. Seminar scheduling constraints — user-confirmed
- **Max 1 seminar per semester** (cannot double up)
- Seminars have **hard seat limits** (small 정원; observed 16 for UIC3512)
- Combined with R15 window (Sem 4–7) and R22 count (2):
  → 2 seminars must be placed in 2 DISTINCT semesters drawn from {4, 5, 6, 7}

**Planning consequence:** if Sem 5 is Songdo (国际) in both current plans, the seminar
placement options are:
  - Sems 4 + 6  (both 신촌 in Plan A; 4 신촌 / 6 국제 in Plan B)
  - Sems 4 + 7  (both 신촌 in either plan)
  - Sems 6 + 7  (Plan A: both 신촌)
  - any pair including Sem 5 → forces a 国际-pool seminar
**Cleanest: Sems 4 + 7**, both 신촌 in Plan A and Plan B, avoids the 国제 seminar pool
entirely and spreads the seat-limit risk across two well-stocked Fall/Spring 신촌 pools.
⚠️ Verify 신촌 seminar availability in SPRING (Sem 7) — earlier observation suggested
Spring 신촌 seminar pool may be thin (0 observed in one Spring sample). If Spring 신촌
seminars are unavailable, fall back to Sems 4 + 6.

---

## R24. OPEN QUESTION: the 학년 / 학년별정원 gate — STILL UNRESOLVED
Do not present this as settled. Current state:

- **R1:** catalogue `학년` is advisory (proven — sophomore in 학년-1 course)
- **R12:** all-zero `학년별정원` correlates with UIC-run courses (4/4 UIC vs 1 non-UIC)
- **R13:** ECO2102 `1학년 = 0` has two live explanations (real gate vs mileage-scoped artifact)
- **R19:** no official document states any ECO2102 prerequisite or year restriction

**Not yet tried:**
1. 강의계획서 (syllabus) for ECO2102 — has a 선수과목 (prerequisite) field
2. 상경대학 (School of Economics) own course/registration page
3. Yonsei 학사지원팀 or 상경대학 office — direct answer
4. Check a NON-UIC, NON-상경 course (e.g. STA/MAT) to test whether all-zero really
   tracks "UIC-run" or just "some departments don't set quotas"
5. Check a 1학년-targeted non-UIC course — if its 1학년 quota is also 0 while
   2/3/4 are non-zero, that strongly supports H2 (mileage-scoped table)

**Test 5 is the highest-value next step** and is doable from the portal directly.

---

## R25. ✅ RESOLVED — 학년별정원 is scoped to the MILEAGE ROUND ONLY (user's H2 confirmed)
**The 학년 question from R13/R24 is settled. Iden's hypothesis was correct.**

**Decisive test — SOC1002 사회학의이해:**
- 신촌, **non-UIC** (대학교양 국가와사회 / 사회과학대학 사회학전공), **학년 1**, 3cr
- A general-education course freshmen take in large numbers
- Mileage popup, 2026-1학기: **총건수 [0] — 조회된 내역이 없습니다**
- Mileage popup, 2025-2학기: **총건수 [0] — 조회된 내역이 없습니다**

**No mileage record exists at all.** Not zeros — complete absence.

**Inference:** if the mileage table described enrollment eligibility, a heavily-enrolled
freshman course would produce rows. It produces none. Therefore the table records
**only the mileage round**, and populations enrolling by other mechanisms
(freshmen → first-come Wait List, per R7) are structurally invisible in it.

**Therefore ECO2102's `1학년 = 0` means:** 상경대학 allocated mileage-round seats to the
year-groups that bid (2/3/4학년). Freshmen are absent because they don't bid — **not
because they are barred.**

**WITHDRAWN:** every earlier claim that freshmen cannot take ECO2102. No official source
states any freshman restriction on Microeconomics (R19), and the quota pattern that
prompted the claim is fully explained by round-scoping.

**Supersedes:** R13 (H1 eliminated), R24 (question closed).
**Confirms:** R14 — absence in a mechanism-scoped table ≠ prohibition. Third instance.

---

## R26. Mileage popup has a per-semester 학년도/학기 dropdown
The popup (마일리지 수강신청 결과 조회) contains its own **학년도/학기 select** at the top,
independent of the main search form. Default = current/most-recent semester, which for
an upcoming term returns empty.

**Use:** to read historical competition for any course, open the popup and switch this
dropdown to a **completed** semester. Empty results for a future term are expected and
carry no information; empty results for a *completed* term are meaningful (see R25).

**Access:** `find` for the combobox, then `form_input` with e.g. `"2025-2학기"`.
Direct clicking is unreliable — the native select needs form_input.

---

## R27. ✅ COMPLETED — Sem 1 (Spring 2026), 8 courses / 19.5 credits — AUTHORITATIVE
Source: Notion "🎓 2026 Spring Semester Hub" (fetched Aug 4 2026). **Supersedes R20's partial list.**

| # | Course | Prof | Schedule | Requirement satisfied | Cr |
|---|---|---|---|---|---|
| 1 | **Critical Reasoning** | 남기혁 | Mon 9–10 · Wed 10–11 | CC Critical Reasoning | 3 |
| 2 | **채플 (A)** | 정대경 | Tue 10–11 | CC Chapel (pass 1 of 4) | 0.5 |
| 3 | **Freshman Writing Intensive Seminar** | 스타이너코리깁슨 | Tue 12–1 · Thu 1–3 | CC FWIS (UIC1101) | 3 |
| 4 | **통계학입문 (Intro to Statistics)** | 필립스다피드 | Mon 1–2 · Wed 1–2 | CC UICE Intro to Statistics | 3 |
| 5 | **Yonsei RC 101** | 김현상 | Tue 2–3 · Wed 4–5 | CC RC101 | 1 |
| 6 | **Eastern Civilization** | 장화사 | Mon 3–4:50 · Wed 3–3:50 | CC Eastern Civilization | 3 |
| 7 | **기독교와세계문화** | 백영민 | Tue 3–4 · Thu 4–5 | CC Understanding Christianity | 3 |
| 8 | **World Philosophy** | 호조렘산타나안드레 | Tue 4–5 · Thu 3–4 | CC L-H-P (1 of 2 categories) | 3 |

**Total: 19.5 credits.**

### CC requirement status after Sem 1 (vs R17 table)
| Requirement | Cr | Status |
|---|---|---|
| Chapel | 2 | ⏳ 0.5/2 — **3 more passes needed** |
| Understanding Christianity | 3 | ✅ DONE (기독교와세계문화) |
| Freshman Writing Intensive Seminar | 3 | ✅ DONE |
| CC L-H-P Series (2 of 3 categories) | 6 | ⏳ 3/6 — World Philosophy done; **need 1 more from World History or World Literature** |
| Language | 3 | ❌ NOT STARTED |
| Science Literacy **or** RDQM | 3 | ❌ NOT STARTED |
| Critical Reasoning | 3 | ✅ DONE |
| UIC Seminars (2, window Sem 4–7) | 6 | ❌ NOT STARTED |
| Western Civilization | 3 | ❌ NOT STARTED |
| Eastern Civilization | 3 | ✅ DONE |
| Social Engagement | 0 | ✅ EXEMPT (2022+ entrant) |
| Yonsei RC101 | 1 | ✅ DONE |
| UICE Introduction to Statistics | 3 | ✅ DONE (통계학입문) |

**CC done: 19.5 / 39.  CC remaining: 19.5 cr**
→ Chapel ×3 (1.5) · L-H-P second course (3) · Language (3) · SciLit-or-RDQM (3)
  · UIC Seminars ×2 (6) · Western Civ (3)

### MR/ME status
**Sem 1 contained ZERO major courses.** All 18 MR credits and all 24 ME credits remain.
- MR remaining: Intro to QRM · Microeconomics · Macroeconomics · Math for Economics 1
  · (Math Stat 1 **or** Regression Analysis) · Principles of Financial Engineering = 18cr
- ME remaining: 24cr

**Total remaining to graduate: 126 − 19.5 = 106.5 credits over Sems 2–8 (7 semesters)
≈ 15.2 cr/semester average.** Comfortable against the 18cr cap (19 as freshman).

⚠️ **Front-loading note:** Sem 1 was 100% CC. MR/ME (42cr) is now compressed into
Sems 2–8, and QRM3003 is Spring-only + Year-3-locked (Sem 5 or 7 only). Prerequisite
chains inside the major must be checked before finalizing the 4-year plan.

---

## R28. 학년 restrictions: NO general rule found — but scope the claim carefully
Verified: catalogue `학년` is advisory (R1); `학년별정원` is mileage-round-scoped (R25);
no official document states year limits for ECO2102 (R19).

**What this supports:** absence of a *catalogue-level* year gate. Registration is not
blocked by the 학년 column, and the quota table cannot be read as a prohibition.

**What this does NOT establish — do not treat as free-for-all:**
1. **Per-course prerequisites (선수과목)** live in the 강의계획서 (syllabus), which has NOT
   been checked for any course. A prereq chain restricts年级 in practice.
2. **QRM3003 is explicitly Year-3-locked** (observed 학년 3 + MR, Spring-only, 국제-only) —
   a real year restriction already exists in this very major.
3. **UIC Seminar window Sem 4–7** (R15) is a year restriction stated in the official guide.
4. **Chapel has year/campus rules** by division (guide §14.4).
5. Departments can set 학년별정원 that genuinely bind *within* the mileage round for
   sophomores+, even though freshmen are out-of-scope.

**Correct framing:** the 학년 *column* is not a gate, and quota zeros are not prohibitions
— but year restrictions DO exist in this program, stated in prose in the guide and in
syllabi rather than in that column. **Check 강의계획서 선수과목 per course before assuming
any specific course is open.**

---

## R29. ❌ CORRECTION — QRM3003 is NOT year-3-locked. Claim withdrawn.
I stated QRM3003 is "Year-3-locked" (R28 pt.2, and in earlier plan discussion).
**That was wrong and had no documentary basis.**

**What actually happened:** the Spring 2026 portal row for QRM3003 showed `학년 3`.
I treated that as a restriction — the exact error R1 exists to prevent. The 학년 column
is ADVISORY. A `3` there means "aimed at juniors", not "juniors only".

**What IS supported:**
- QRM3003 does **not** appear in the Fall 2026 catalogue (0 rows) → **Spring-only offering**
- Campus: 국제 (Songdo), UIC-only, blended (동영상콘텐츠 + 1 live block)
- Any year restriction: **UNVERIFIED**. Would need the 강의계획서 선수과목 field.

**Impact:** the constraint "QRM3003 must be Sem 5 or Sem 7" rested on the year-lock.
Without it, QRM3003 may be placeable in **any Spring semester** (Sem 3, 5, or 7),
subject only to prerequisites. This LOOSENS the four-year plan considerably and
must be re-derived rather than assumed.

**R28 pt.2 is void.** The other year restrictions in R28 (seminar window Sem 4–7 per
official guide; Chapel division rules) remain valid — those ARE stated in prose.

---

## R30. Fall 2026 QRM course offerings (from catalogue, 학년 = advisory only)
| Code | Course | 학년(adv.) | Campus | Time |
|---|---|---|---|---|
| QRM1001 | Introduction to Quantitative Risk Management | 1 | 국제 | 목4,5,6 |
| QRM2001 | Fundamental Economic Analysis | 2 | 국제 | 화1,목2,3 |
| QRM2002 | Financial Data Analysis | 2 | 국제 | 금1,2,3 |
| QRM2004 | Statistical Analytic Methods | 2 | 국제 | 화4,5,6 |
| QRM2102 | Linear Algebra and Differential Equations | 2 | 국제 | 금5,6,7 |
| QRM3001 | Theory of Financial Analysis | 3 | 국제 | 수7,8/금7 |
| **QRM3005** | **Mathematical Statistics** | 3,4 | **신촌** | 수8,9,10 |
| QRM3007 | Financial Machine Learning | 3 | 국제 | 수10,11/금2 |
| QRM4807 | Methods of AI in Finance and Investment | 3,4 | 국제 | 수5,6/금5 |
| QRM4808 | Financial Time Series Analysis | 4 | 국제 | 수12,13/금4 |
| QRM4809 | Corporate Finance Strategies | 4 | 국제 | 수9,10/목3 |

**Notable:** QRM3005 (Mathematical Statistics — satisfies an MR slot) is at **신촌**,
not 국제. Nearly all other QRM courses are 국제. QRM3003 absent (Spring-only, R29).

**⚠️ 학년 values above are ADVISORY (R1).** Do not use them to exclude courses.
QRM1001 (Intro to QRM) is an MR requirement offered Fall at 국제 — a Sem 2 candidate.

---

## R31. Double major — QRM requirement changes (Iden: ~85% likely)
Source: `QRM_Graduation_Requirement_table (2022~).pdf` p.3 (Double Major table, **2026~** column)
plus p.2 note 2: "Major credits will be reduced to 36 if a student completes a double major."

### What changes on the QRM side
| | QRM as 1st/single major | QRM with a double major |
|---|---|---|
| MR | 18 cr (6 courses) | **18 cr — UNCHANGED** |
| ME | 24 cr | **18 cr — saves 6 cr** |
| Major subtotal | 42 cr | **36 cr** |
| UICE Intro to Statistics | in CC (39) | listed separately, 3 cr — ✅ already done (R27) |
| **Total credits still 126** | | |

**MR is identical either way** — all six courses still required:
Intro to QRM · Microeconomics · Macroeconomics · Math for Economics 1 ·
(Math Stat 1 **or** Regression Analysis) · Principles of Financial Engineering.

**Only ME shrinks: 24 → 18 (two fewer 3-cr electives).**

### CC under a double major
p.3 note 2: *"For common curriculum requirements, students having a double (2nd) major
should follow the CC requirements of their **1st major**."*
→ If QRM stays 1st major, R17/R27 CC list is unchanged (19.5 cr remaining).
→ If the new major becomes 1st, its CC rules govern instead — **re-derive**.

### Credit budget (Sem 1 = 19.5 done)
| | single | double |
|---|---|---|
| CC remaining | 19.5 | 19.5 |
| QRM remaining | 42 | 36 |
| 2nd major | — | **~36–39** (varies by major) |
| Free electives | 45.0 | **~12–15** |

**Key consequence:** a double major consumes nearly all free-elective slack.
45 cr of freedom → roughly 12–15 cr. Timetable optimization (blank days, lunch, late
starts) gets substantially harder because there is far less discretionary course choice.

### Eligibility
p.3 note 1: **"Only UIC students can apply for a double major within UIC major offerings."**
⚠️ Reads as restricting UIC-internal double majors to UIC students. Whether a UIC student
may double-major OUTSIDE UIC (e.g. 상경대학 Economics, 응용통계학과) is **NOT stated here**.

### ❗ OPEN — required before planning around this
1. **Which 2nd major?** Requirements, campus, and prereq chain all depend on it.
2. **Can a UIC student double-major outside UIC?** (affects 신촌-campus strategy directly)
3. **2nd major's own CC/MR/ME tables** — fetch its Graduation Requirement PDF.
4. Confirm whether QRM remains 1st major (determines whose CC rules apply).

Until (1) is known, four-year plans should be built **QRM-single** with a note that
6 ME credits may be released, rather than modeling a specific double major.

---

## R32. ✅ RESOLVED — UIC students CAN double-major into other colleges (one-way gate)
Source: 교무처 학사지원팀, **"2026학년도 2학기 캠퍼스내 복수전공 신청 안내"** (2026.06.05)
https://www.yonsei.ac.kr/bbs/sc/58/943397/artclView.do

**The key clause (모집학과 3):**
> "언더우드국제대학 및 글로벌인재대학 내 전공은 **해당대학 소속 학생에 한하여** 지원 가능"
> "Majors in Underwood International College and Global Leaders College are available
> **only to students enrolled in those colleges**."

**This is a one-way restriction, and it is the OPPOSITE of what R31 feared:**
- Non-UIC students → **cannot** double-major INTO UIC. (This is what the QRM PDF's
  "Only UIC students can apply for a double major within UIC major offerings" meant.)
- **Iden (UIC) → CAN double-major OUT into 상경대학, 응용통계학과, 경영대학, etc.** ✅

**Blocked destinations (all students):** 건축학(5년제), 시스템반도체공학과,
디스플레이융합공학과, 음악대학 전 학과, 의학, 치의학, 간호학, 약학.
→ None of Iden's plausible targets (Economics / Applied Statistics / Business) are blocked.

### Eligibility & timing — ACTIONABLE
- **Apply from 3rd semester** through the semester before graduation.
  → **Iden's first application window = Sem 3 (Spring 2027).**
- Requires 1st major approved; 2016+ admits. Iden qualifies.
- **Fall 2026 cycle (for reference): applied 6/23–6/29, results 7/24.**
  Spring cycle will run on an analogous schedule — watch ~Dec 2026 for the Sem-3 window.

### Selection is COMPETITIVE — this is the important part
- Selected ≥ **min(50% of applicants, 30% of dept quota)**
- Evaluated on: **cumulative GPA (all semesters)** + 지원동기 (statement of purpose)
  + 학업계획 (academic plan), each 500–2,000 characters
- ⚠️ **Sem 1 + Sem 2 grades are the entire GPA record** at the Sem-3 application.
  Fall 2026 performance directly determines double-major admission odds.

### Other notes
- 제3전공 possible later without prior approval, but only if the 2nd major is completed.
- Cancellation allowed until the semester before graduation (so it is reversible).
- Approved double majors MUST meet that major's full graduation requirements.

**Planning consequence:** the 신촌-heavy candidates (상경대학 Economics, 응용통계학과,
경영대학) are all OPEN to Iden. A 신촌-based 2nd major would *reinforce* the campus goal
rather than conflict with it — it supplies 신촌 coursework to fill 신촌 semesters.

**R31 open question 2: CLOSED.** Remaining open: which major, and its requirement table.

---

## R33. Second-major candidates — Fall 2026 data (신촌-based, all OPEN to Iden per R32)
Campus is NOT a differentiator: 신촌 is the university default; 국제 is the UIC exception.
The real axes are **language of instruction**, **QRM overlap**, and **section volume**.

| | Economics (상경대학 경제학) | Applied Statistics (상경대학 응용통계학) | Business (경영대학 경영학) |
|---|---|---|---|
| Fall 2026 sections | 70 | 26 | 125 |
| **English** | **29 (41%)** | **6 (23%)** | 44 (35%) |
| Korean | 41 (59%) | 20 (77%) | 81 (65%) |
| at 신촌 | 64 (91%) | 22 (85%) | 121 (97%) |

### Overlap with QRM requirements — decisive difference
**Economics — HIGHEST overlap.** Two QRM **MR** courses are literally 상경대학 경제학 courses:
- **ECO2102 미시경제학 (Microeconomics)** — MR requirement, English section exists (화5,6/목4)
- **ECO2101 거시경제학 (Macroeconomics)** — MR requirement, English section exists (화5,6/목4)
Also relevant: ECO3134 화폐금융론, ECO3130 국제금융론, ECO3119 금융공학의이해,
ECO4126 인공지능과금융공학 — all finance-adjacent to QRM.
→ **Iden must take ECO2101 + ECO2102 regardless of the double-major decision.**
   An Economics 2nd major builds directly on required coursework.

**Applied Statistics — MEDIUM overlap, but a REQUIREMENT TRAP.**
Per R18: since Fall 2024, only **QRM-department** Math Stat 1 / Regression Analysis count
toward the QRM major — 응용통계학과 versions do NOT. STA3109 수리통계학(2) etc. would count
for the STA major but **not** substitute for QRM's MR slot.
⚠️ Also the weakest English coverage (23%) — 77% Korean.

**Business — LOWEST QRM overlap** but largest catalogue (125 sections → best timetable
flexibility) and finance courses exist (BIZ2119 재무관리, BIZ3162 금융시장론, BIZ4122 파생상품론).

### Korean-language consideration
Iden's Fall 2026 catalogue is 755 English / 915 Korean overall. For a 2nd major the
**English share within that department** is what matters:
Economics 41% > Business 35% > Applied Statistics 23%.
⚠️ Korean-taught 2nd-major courses are fine for the 2ND MAJOR's own requirements —
the R18 4-course/12cr Korean cap applies ONLY to counting toward the **QRM major**.

### Assessment
- **Economics** = strongest structural fit: two MR courses already required, best English
  coverage, deep finance overlap with QRM.
- **Business** = best flexibility/volume, weakest overlap; more "breadth" than synergy.
- **Applied Statistics** = superficially the natural quant pair, but the R18 rule blocks
  the obvious credit synergy and English coverage is thin.

**⚠️ NOT YET FETCHED:** the actual graduation-requirement tables for these three
(credit counts, required course lists, prereq chains). Section counts ≠ requirements.
Next step before any recommendation is final.

---

## R34. ✅ RC101 is ONE-TIME, 1st semester only — DONE, never repeats
Official, stated 4× in the 2026 Spring UIC Enrollment Guide (once per division):
> "Yonsei RC 101: This is a required course for freshmen. **Freshmen are required to
> take this course during their 1st semester.**"

QRM requirement table: **Yonsei RC101 = 1 credit** (single credit = single enrollment).
Contrast Chapel, which the same table lists as 2 credits and the guide explains as
4 passes × 0.5 across 4 semesters — repetition IS spelled out when required.
RC101 has no pass structure, no multi-semester language.

**Iden: COMPLETED Sem 1 (Spring 2026, 김현상).** Requirement closed permanently.
Fall 2026 offers 1 section (UCR1007-01, 수6) — not needed.

---

## R35. ✅ 사회참여 (Social Engagement, UCR1015) NOT required for Iden
> "for UIC students admitted in **2023 and thereafter, SE course is not required
> for graduation.**" — Guide §15.1, footnote to RC graduation-requirement change table

Iden = 2026 entrant → **exempt**. Matches QRM requirement table (Social Engagement, 0 cr,
"Students admitted in 2022 and thereafter get an exemption for Social Engagement courses").

**Planning impact:** the 32 SE sections in the Fall 2026 국제 catalogue occupy prime
daytime slots (월1,2 … 수10,11) but are **irrelevant to Iden**. Do NOT model SE as a slot.

---

## R36. RC자기주도활동 is SCHEDULE-NEUTRAL — no need to wait for house assignment
Fall 2026: **24 sections (UCR1013/UCR1014), ALL at 수13,14**, room I종301, 0.5 credits.

Period 13–14 is far outside the 1–11 band used by academic courses
(guide §17: period 1 = 09:00, period 10 = 18:00).

**Consequences:**
1. RC자기주도활동 **cannot conflict** with any academic timetable.
2. The RC house / RA assignment mail determines only WHICH section number, not WHEN.
3. Credits are exempt from the per-semester load cap — guide §3.1: "Credits from Chapel,
   Volunteer Service, Social Engagement, **RA Leadership Development Theory, RC
   Self-Directed Activity**, UT Seminar, Career Development/Planning Seminar, and
   Military Science courses **can exceed the above course load per academic term.**"

**→ Iden does NOT need to wait for the RC mail to finalize Aug 25 registration.**

⚠️ Note: RC자기주도활동 requires ≥12 RC시간 of program participation per semester
(≥1 RC공통프로그램 + ≥1 RC하우스프로그램). That is out-of-class activity load, not timetable load.

---

## R37. Course-load cap exemptions (guide §3.1)
These do NOT count against the 18/19-credit per-semester maximum:
Chapel · Volunteer Service · Social Engagement · RA Leadership Development Theory ·
**RC Self-Directed Activity** · UT Seminar · Career Development/Planning Seminar ·
Military Science.

**Use:** when computing a semester's credit total against the cap, exclude the above.
Iden's Fall 2026 academic load should be counted WITHOUT Chapel (0.5) and
RC자기주도활동 (0.5).

---

## R38. ✅ PREREQUISITE VERIFICATION — 강의계획서 선수 추천과목 field (Fall 2026 ME pool)
Source: official 수업계획서 PDF exports (Report.pdf / Report2.pdf), downloaded by Iden Aug 4 2026.
**The 선수 추천과목 field is on page 2 of every 강의계획서 — this is the authoritative place to check.**

| Course | Time | 선수 추천과목 | Grading | Verdict |
|---|---|---|---|---|
| **QRM2004** Statistical Analytic Methods | 화4,5,6 | **(empty)** | 개인과제 60 / 기말 30 / 출석 10 / **중간 0** | ✅ **OPEN — recommended pick** |
| **QRM2002** Financial Data Analysis | 금1,2,3 | **(empty)** | (not populated) | ✅ open, but **kills blank Friday** |
| **QRM2102** Linear Algebra & Diff Eq | 금5,6,7 | ⚠️ **"Single-variable and Multivariable Calculus courses"** | 중간25/기말25/퀴즈30/출석20 | ⚠️ **GATED — see below** |

### QRM2102 — recommended-prereq risk
- Field says 선수 **추천**과목 (*recommended*), NOT 선수과목 (*required*) → likely will not block registration.
- **Iden has taken NO calculus.** Sem 1 was 100% CC; 통계학입문 is statistics, not calculus (R27).
- Syllabus wk1 = axiomatic vector spaces & spanning sets; wk2 = linear independence, basis, dimension.
  Proof-oriented, assumes mathematical maturity.
- Grading is **exam/quiz-heavy (80%)** with no assignment cushion — high variance.
- ⚠️ **Fall 2026 GPA determines the Sem-3 double-major application (R32).** Taking a gated,
  exam-heavy course without the assumed background is a direct risk to that.
- Textbook: Edwards/Penney/Calvis, *Differential Equations and Linear Algebra* (Pearson 2017).
- **Note:** professor 가르얀토나다나엘 is at SKKU (NATANAEL@SKKU.EDU, 031-299-6243) — external.

**Decision: demote QRM2102 in the Fall 2026 ME pool.** Revisit after taking calculus
(QRM curriculum includes Mathematics for Economics 1 as MR — a natural precursor).

### QRM2004 — why it's the pick
No prereq · builds directly on completed 통계학입문 · continuous assessment (60% assignments,
no real midterm — wk8 "midterm" is an EDA report) · preserves blank Friday · English ·
Python-based (wk2 OOP → wk13 logistic regression).
⚠️ Attendance: >1/3 absence = automatic F/NP regardless of exam results.

### Key dates from syllabus (apply to ALL Fall 2026 courses)
- **9.1** 개강 · **9.3–9.7** 수강신청 확인 및 변경
- **10.13–10.15** 수강철회 (withdrawal escape hatch)
- **10.20–10.26** 중간시험 · **10.27–10.29** S/U 평가신청
- **12.15–12.21** 기말시험

---

## R39. UIC1653 WORLD HISTORY — restricted, REMOVE from L-H-P pool
유의사항: **"UIC-ICU LearnUs program students only"**, UIC students only.
Iden is not in the UIC-ICU LearnUs program → **not eligible**. Drop from pool.
(Was appearing in top-ranked plans at 화8,9/목7 — must be excluded.)

---

## R40. QRM2001 Fundamental Economic Analysis = ME for 2026 entrants (not MR)
Catalogue 유의사항, verbatim:
> "2025학번까지 Major Requisite 과목, **2026학번부터 Major Elective 과목**
> Major Requisite course for students admitted in 2025 or earlier; Major Elective course for st[udents admitted in 2026...]"

Confirms the R18/R31 reading: the 2026~ requirement column replaced "Fundamental Economic
Analysis" (MR) with Microeconomics + Macroeconomics. For Iden, QRM2001 counts as **ME**.

---

## R41. Science Literacy (SciLit) course list — provided by Iden (2026-08-04)
The SciLit half of the "Science Literacy OR RDQM" CC choice (R17) is served by:
UIC1541 · UIC1918 · UIC1502 · UIC1920 · UIC1751 · MAT1001 · PHY1001 · CHE1001 ·
BIO1001 · MAT1002 · PHY1002 · CHE1002 · BIO1002 (all 3 cr).

**Fall 2026 국제 presence: 40 sections** — CHE1002 ×14, PHY1002 ×12, BIO1002 ×6,
MAT1002 ×5, MAT1001 ×1, CHE1001 ×1, UIC1751 ×1; the other six codes have 0 국제
sections this Fall. Note MAT1001 (Calculus & Vector Analysis 1) is in this list —
also relevant to the QRM2102 recommended-prereq gap (R38).

---

## R42. Four-group type map for Fall 2026 enumeration — confirmed by Iden (2026-08-04)
Iden confirmed stratifying the option-B enumeration by type t(s) ∈ {REQ, MR, ME, ELEC},
typed relative to Iden's residual requirements (R27):

- **MR (1 section):** QRM1001.
- **ME (9):** all other QRM sections — QRM2001/2002/2004/2102/3001/3007/4807/4808/4809.
  (Typing rule: any non-MR QRM-dept course = ME. Includes 3000/4000-level; hiding them
  would repeat HANDOFF §9 mistake 10.)
- **REQ (161):** WestCiv 3 (UCB1103/YCE1253/UIC1561) · LHP-2nd 15 (name regex "WORLD
  HISTORY|LITERATURE", UIC1653 excluded per R39) · RDQM 13 (UIC2151) · SciLit 40 (R41)
  · Chapel 7 (YCA1006) · Language 83.
- **ELEC (490):** everything else — includes 국제 UIC Seminars (window-locked to
  Sem 4–7 per R15, so they satisfy nothing in Sem 2), SE (exempt, R35), RC101 (done,
  R34), and CC categories already completed.

**Language pool definition used:** 대학교양 "언어와표현" category (72 sections) +
UIC language courses UIC1804/1805/1806/1808/1809/2302 (11) = **83**.
⚠️ HANDOFF §8 said "93 국제 sections" — NOT reproduced under any clean rule tried;
the 83-rule above is explicit and re-runnable. If Iden's intended rule differs,
retype and rerun (seconds).

---

## R43. 9-type slot-split confirmed by Iden (2026-08-04) + archive move
Iden approved refining the R42 type map to 9 types: WCiv 3 · LHP 15 · RDQM 13 ·
SciLit 40 · Chapel 7 · Lang 83 · MR 1 · ME 9 · ELEC 490. (RDQM and SciLit stay
separate types but fill the SAME CC slot — χ merges them downstream.)
Full exact table: `composition_table_9type.csv` — 4,199 cells, k ≤ 6,
conservation-checked to the digit against the untyped totals.

Key exact counts (Fall 2026 국제 catalogue, time-conflict-exact):
- **Full-coverage k=6** (QRM1001 + WCiv + LHP + RDQM-or-SciLit + Chapel + Language):
  **134,233** conflict-free timetables (29,355 via RDQM · 104,878 via SciLit).
  In these cells same-course repeats are impossible (≤1 section per type) and
  credits = 15.5 ≤ 19, so these counts are FULLY valid, not just time-feasible.
- Language deferred, +1 ME instead: **22,000** (4,848 RDQM · 17,152 SciLit).
- Slot-distinct mass (every non-ELEC type ≤1): 85.0% of k=5, 79.6% of k=6.
- ⚠️ Credit cap is NOT automatic for ELEC-containing cells (ELEC sections go up to
  6 cr) — enforce at expansion.

Also per Iden's instruction, 10 stale/biased files moved to `archive/`:
FINDINGS.md, artifact.html, timetable_artifact.html, plans.json, plans_min.json,
data_compact.json, pools_min.json, pools_fall2026.json, plans_fall2026.json,
수강신청_Fall2026.html. (HANDOFF §7's file table refers to pre-archive paths.)

---

## R44. Ranking decisions — stated by Iden (2026-08-04)
- Iden DOES want a ranking (supersedes the pure no-ranking reading of "numbers only";
  the no-INVENTED-weights rule stands — Iden supplies every value).
- **Form: weighted points.** Scope: **everything** — full-coverage (134,233),
  lang-deferred (22,000), k=7 extensions (+1 ME 681,531; +1 ELEC 30,526,816),
  and all six defer-one-slot families (≈213M candidates total, scored exhaustively;
  output = top-N + distributions, since 213M rows are not materializable).
- **Axes: all four** (lunch, early starts, blank weekdays, prof ratings) and Iden is
  open to suggested additional axes.
- Values collected via `ranking_weights.md` (blank = axis off; old blank-day values
  12/9/5 + 8·(m−1)² prefilled as UNCONFIRMED per open Q5; lunch penalty was never
  stated in the old system; prof ratings have no data source — sparse self-rated).
- ⚠️ Cross-family comparability requires slot-closure values (§2 of the sheet):
  without them, pure-schedule scoring structurally favors deferral families.
Exact neighbor-family counts (all verified this session): F+ME 681,531 · F+ELEC
30,526,816 · F−MR: +ME 2,705,574 / +ELEC 145,831,108 · F−WCiv: 480,138 / 20,155,975 ·
F−LHP: 102,494 / 4,498,631 · F−SciRD: 30,982 / 1,465,172 · F−Chapel: 170,530 /
7,811,493 · F−Lang: 22,000 / 1,003,087.

---

## R45. Comfort-weight elicitation — Iden's answers (2026-08-04)
Elicited via forced-choice scenarios; full fitted table with provenance in
`ranking_weights.md`. Key facts stated by Iden:
- **Gap penalties are NOT linear** — "very low avoidance towards short gaps"; a 4-period
  dead block ≈ one 9am morning. (Modeled: −10·(ℓ/4)² per sandwiched free-run of length ℓ.)
- Early starts strongly disliked: preferred 6 scattered gaps over one 1교시 day.
- Free Friday worth 2–3 9am-mornings ("two, not three"). Mon ≈ 75% of Fri, midweek ≈ 40%.
- Two free days stack superadditively ("much more" than the sum).
- Lunch-fail ≈ 2 short gaps (low confidence — answered pre-currency-change).
  Late endings ≈ negligible (~1 short gap). Marathon ≥4: break it (sign only).
- Chapel: desirable in itself, "easy to catch, finish offline chapels this semester" —
  special bonus term, value TBD.
- Prof ratings: post-hoc manual layer on shortlists, not global data.
- N: top-50 for manual review, top-5000 for analysis.
Provisional comfort-only ranking over F ∪ F−Lang+ME (156,233 rows): top score 43.8
(Mon/Wed/Thu campus week, Tue+Fri free, no 9am). Top-5000: 100% Friday-free, 67% also
Tue-free; SciLit path 75%; 56 distinct professors. ⚠️ Merged list implicitly values
Lang = ME progress — revisit when §1 slot values exist.

---

## R46. Language slot = UIC Beginning Chinese/Japanese only — stated by Iden (2026-08-04)
Iden: the intended Language courses are **UIC1805 Beginning Chinese(1)** and
**UIC1806 Beginning Japanese(1)** ("I don't have any reason to listen to that advanced
chinese course over these easy ones"). Pool cut 83 → **4 sections**. Excluded per literal
reading: Beginning Chinese(2)/Korean(1)(2)/Intermediate Korean, all YCF/UCK 언어와표현.
Supersedes the R42 Language definition for ranking purposes (R17's "any language counts"
still true for the *requirement*; this is Iden's preference restriction).

### ⚠️ Structural conflict discovered (verified, Fall 2026):
- UIC1805-02 (화5,6/목4) and UIC1806-02 (화4/목5,6) both **clash with QRM1001 (목4,5,6)**.
- The only surviving sections, UIC1805-01 and UIC1806-01, are both **화1,목2,3** —
  a 9am Tuesday, and 목2,3 + QRM1001 목4,5,6 = a 5-period Thursday marathon.
- Therefore QRM1001 + beginner CN/JP this Fall ⇒ forced 화1,목2,3 shape.
  Comfort price measured: best full-coverage = 4.12 pts (rank 1,049) vs best
  lang-deferred = 40.75 pts → **language-now costs ≈ 36.6 comfort points** under R45
  weights. This is a §1-type deferral decision for Iden, now with an exact price.
- Counts after cut: full-coverage 3,966 · lang-deferred 22,000 · total 25,966.
- Comfort top-50 is 100% lang-deferred, all with **QRM4809** (수9,10/목3, Corporate
  Finance Strategies, 학년 4 advisory (R1), prof 이재윤 = same prof as QRM1001).
  Broader top-5000 ME spread: QRM2004 1,466 · QRM4809 758 · QRM2102 563 · others lower.

---

## R47. Language now-vs-later: campus/competition facts (from 강의목록_2026F.xlsx, 2026-08-04)
Iden's stated preference: if not taking the UIC beginners now, defer language to a
신촌 semester. Verified facts for that decision:

**UIC language courses are "UIC students only"** (유의사항, all UIC18xx/2302 sections)
— a protected pool: at 국제 now, competition = UIC students only, via the freshman
first-come round (no mileage). Fall 2026 국제 UIC language sections: KOR(1)×2,
KOR(2)×2, CN(1)×2, CN(2)×2, JP(1)×2, Interm.KOR×1 = 11.

**UIC language courses ALSO appear at 신촌** — Fall 2026 has UIC1809-01 Beginning
Chinese(2) (월5,6,수6) and UIC2302-01 Intermediate Korean(1) (월1,2,수2) at 신촌,
still UIC-only. So UIC-protected language seats at 신촌 exist but are few (2 observed)
and NOT the Beginning(1) courses. Whether Beginning CN/JP(1) ever runs at 신촌:
UNVERIFIED (needs past-semester portal search, R5).

**신촌 open-competition supply is large (Iden's premise verified):** 79 언어와표현
sections at 신촌 this Fall, of which **43 are foreign-language instruction**
(중국어(1)×4, 일본어(1)×2, 독일어/프랑스어/스페인어/러시아어/한문/라틴어/이탈리아어…),
"처음 배우는 학생 대상". These are university-wide mileage courses (R3 cap-36 class,
real bidding); the R10 offering-dept tie-break does NOT favor Iden there. Any of them
satisfies the requirement (R17).

**Unknowns that would settle "easier to grab":** (1) 정원/여석 of UIC1805/1806 —
visible on the portal before Aug 25; (2) mileage/enrollment history popups for
UIC1805/1806 and for 2–3 신촌 YCF language courses (R5 method — portal blocks
automation, manual pull); (3) whether UIC language courses are in the UIC First
auto-enroll list (enrollment guide) — matters for Sem 3+ 국제 grabs.
⚠️ The xlsx has NO capacity column — seat numbers cannot be derived from local data.

---

## R48. DECISION by Iden (2026-08-04): take a beginner language NOW
"If early classes are unavoidable this semester, they are unavoidable next semester."
→ Fall 2026 plan = full-coverage family with Language ∈ {UIC1805 Beginning Chinese(1),
UIC1806 Beginning Japanese(1)}. Given QRM1001, the usable sections are the two
화1,목2,3 ones (-01 of each); CN-vs-JP is Iden's identity choice, geometrically identical.
Registration note: both are "UIC students only" first-come — the untaken one is the
natural instant fallback on Aug 25.
**Update (same day): Iden chose Chinese.** UIC1805-01 = primary, UIC1806-01 = fallback.
Deliverable format: geometrically identical timetables collapsed (2,662 rows → 1,066
distinct grids); visual HTML `시간표_Fall2026_top50.html` supersedes the CSVs as the
review artifact (CSVs remain for sorting/filtering).

---

## R50. ⚠️ ONLINE BLOCKS ≠ CAMPUS PRESENCE — stated by Iden (2026-08-04), verified
Iden: "classes that are online or mixed don't count when counting them as blank days."
The assistant had been counting every scheduled block as campus presence — WRONG.

**✅ BETTER SOURCE FOUND (2026-08-05): the xlsx has a `과목종별` delivery-mode column.**
국제 values: 대면강의 688 · 블랜디드(동영상) 126 · 비대면(동영상) 5 · 비대면(실시간) 1 ·
비대면(실시간+동영상) 1 · empty 6. **Cross-check: 과목종별 ≠ 대면강의 ⟺ 강의실 has an
online marker, 133/133 with zero exceptions** — the two sources agree perfectly, so
online *status* is now categorical fact, not regex inference. (Per-BLOCK alignment
still rests on the slash rule below.) Pool modes: QRM1001 · Chapel ×7 · RDQM ×13 ·
UCB1103 · UIC1805 ×2 · UIC1806 ×2 = all 대면강의; YCE1253 = 블랜디드; **UIC1561 =
비대면(실시간+동영상)** — the section that enables 월+금 free.

**Recoverable from the xlsx:** the 강의실 column is **slash-aligned with 강의시간**.
"화5,6/목4" + "I자A305/동영상콘텐츠" ⇒ 화5,6 in-person, 목4 video. Online markers:
온라인 · 동영상 · 비대면 · 사이버. Of 821 국제 sections (xlsx, 강의시간 non-empty):
**7 fully online** (zero campus presence), **126 partially online**.

**Two distinct masks are now required per section:**
- `b` (all blocks) → time-CONFLICT mask (unchanged; conservative — 실시간온라인 really
  does occupy its hour, and 동영상 is kept blocking too, see caveat)
- `pres` (non-online blocks only) → CAMPUS-PRESENCE mask → the ONLY input to free-day
  counting, and arguably to lunch/early/late/gap penalties too.
Corrected dataset: **`all_kj_presence.json`** (both masks per section).

**Key case: UIC1561 WESTERN CIVILIZATION (월7,8/수7) is FULLY ONLINE**
(실시간온라인/동영상, 중복수강불가) — zero campus presence. YCE1253 WestCiv is half
online (목4 = 동영상). Only UCB1103 is fully in-person.

### ✅ Mon+Fri free DOES exist — 36 grids (was 0 under the wrong model)
Free-day distribution over the 1,366 CN-committed grids, presence semantics:
**월금 36 · 수금 8 · 금 776 · 월 90 · none 456.** Enabler in all 36: UIC1561 online
WestCiv. Example: QRM1001 목4,5,6 · UIC1561 (online) · UIC1501-05 화2,3/목1 ·
UIC2151-14 화7,8,9 · Chapel 수2 · 중국어 화1/목2,3 → campus only 화·수(채플 1교시만)·목.

⚠️ Caveat resolved by R52 — see below. (Prior text: 동영상콘텐츠 was conservatively
treated as time-blocking pending verification.)

**ALL rankings/HTML produced before R50 use presence-blind free-day counting and are
superseded.** Rebuild required: presence masks + recalibrated weights.

---

## R51. ⚠️ `all_kj.json` IS INCOMPLETE — 48 국제 sections missing vs the xlsx
Cross-check (2026-08-04): xlsx has **827 국제 rows, 821 with 강의시간**;
`all_kj.json` has **661**. **48 학정번호 present in the xlsx are absent from all_kj.json.**
- 41 of the 48 are 대학교양 체육과건강 (PE) — plausibly filtered on purpose, unverified.
- **2 are requirement-relevant: MAT1002-07-00 and MAT1002-08-00** (Calculus & Vector
  Analysis 2 — SciLit pool per R41), times `(월9)수1,2,3` and `(월9)수4,5,6`.
  This is why the presence-based rebuild found SciLit = 42, not 40.
- 5 others are UIC/AI-college sections (ELEC pool).
- ✅ **Residual RESOLVED (2026-08-05):** 827 국제 rows − 112 duplicate rows (72 학정번호
  listed under two 분류, e.g. YCA1102-13-00 under both 교양기초 기독교의이해 and
  UIC 공통교과과정) = **715 distinct**; − 6 with empty 강의시간 (UIC1101 ×5, UIC1901 ×1,
  both already completed per R27) = **709 distinct sections with a time**; 709 − 661 =
  the 48 missing. Arithmetic fully closed. **Canonical universe = deduplicated xlsx,
  709 국제 sections.**
- **Every pool count in R42/R43/R46 and every enumeration total derived from
  all_kj.json is therefore provisional.** The xlsx is the more complete source;
  `all_kj_presence.json` (built directly from the xlsx, 821 sections, dual masks)
  supersedes both all_kj.json and all_kj_fixed.json going forward — pending the
  duplicate-row reconciliation above.

---

## R52. ✅ BLOCK SEMANTICS — SETTLED by official 수강편람 (2026학년도 2학기, p.4 라-2)
Source: `★2026학년도 2학기 수강편람 원고_배포 260713.pdf`, uploaded by Iden 2026-08-05.
Verbatim:
> ① 대면수업: 강의시간을 표기하고 강의실 정보가 표시됨
> ② 실시간온라인수업: 강의시간을 표기하고 강의실은 "실시간온라인"으로 표시됨
> ③ 동영상콘텐츠수업: 강의시간을 표기하고 강의실은 "동영상콘텐츠" 또는 "동영상(중복수강불가)" 표시됨
>  ※ **"동영상콘텐츠"로 표시된 수업시간은 다른 수업과 강의시간을 중복하여 수강 가능.**
>    단, 시험 등의 활동은 특정 시간에 실시하여 타 수업과 중복불가 할 수 있으므로 수업계획서를 반드시 확인할 것
>  ※ **"동영상(중복수강불가)"로 표시된 수업시간은 다른 수업과 강의시간을 중복하여 수강 불가**

### The four block types (per BLOCK, not per section)
| 강의실 marker | Blocks time? | Campus presence? | 국제 cells |
|---|---|---|---|
| (room code) 대면 | ✅ yes | ✅ yes | 1,970 |
| 실시간온라인 | ✅ yes | ❌ no | 5 |
| **동영상콘텐츠** | **❌ NO — may overlap** | ❌ no | **133** |
| 동영상(중복수강불가) | ✅ yes | ❌ no | 62 |

**My earlier conservative assumption was WRONG in the restrictive direction:**
133 block-cells across **79 sections** were being treated as conflicts when they are
freely overlappable. The conflict graph LOOSENS — every previously-valid timetable
remains valid, and new ones appear. All enumeration counts must be recomputed.

**Pool sections directly affected (동영상콘텐츠 = free cells):**
- **YCE1253 WestCiv 화5,6/목4** → 목4 is 동영상콘텐츠 ⇒ effectively occupies only 화5,6.
  Materially more attractive than previously scored.
- **MAT1001-02, MAT1002-02/03/04/05/06** (SciLit) — each has a free half.
- **QRM3001, QRM3007, QRM4807, QRM4808** (ME) — each has a free 수 half.
- **UIC1561 WestCiv** = 실시간온라인(월7,8) + 동영상(중복수강불가)(수7) ⇒ both BLOCK time,
  neither requires presence. (Unchanged from R50 — still the 월+금 enabler.)
- **QRM4809** = 동영상(중복수강불가)(수9,10) + 대면(목3) ⇒ blocks 수9,10, presence 목3 only.

⚠️ Residual: the same clause warns exams may still be scheduled at fixed times
("시험 등의 활동은 … 중복불가 할 수 있으므로 수업계획서를 반드시 확인") — so a
동영상콘텐츠 overlap is safe for *classes* but must be re-checked per syllabus for
*exam* clashes before final registration.

---

## R53. ⚠️ NEW OPEN QUESTION — 외국인 유학생 30% cap on 비대면(동영상)
수강편람 §11 (p.22): from 2026-1, 외국인 유학생 must keep 단순 동영상 강의
(= 비대면(동영상), fully async) to **≤30% of total registered credits**.
| 강의 종류 | 제한 |
|---|---|
| 비대면(동영상) | ≤30% of credits |
| 비대면(실시간) · 비대면(실시간+동영상) · 블렌디드(동영상) | 제한 없음 |

**✅ CLOSED 2026-08-05 — Iden states: NOT an 외국인 유학생.** Rule does not apply.
No async-credit cap on any plan.

---

## R54. ✅ PARENTHESES = REAL SCHEDULED TIME — verified from 강의계획서 (2026-08-05)
Source: `Report3.pdf` = CHE1002-06 수업계획서 (2026-2), `Report4.pdf` = MAT1002-05 (2025-2),
both uploaded by Iden. Two distinct paren patterns, both resolved:

**Pattern A — parens = 실험/실습 (lab), DIFFERENT room. PROVEN REAL.**
CHE1002-06: 수업시간 `화1,2/(목1,2)`, 강의실 `I자A525/(I자B507)`.
Syllabus, verbatim: "수업은 강의와 실험 둘로 나누어 진행한다. 1. 강의: … **2시간/주** …
2. 실험: 화학 실험실에서 **2시간/주 실시**". → the parenthesized block is a **weekly,
in-person lab in a lab room**. NOT biweekly, NOT optional.
⚠️ "**강의 및 실험 둘 중에 한 부분이라도 1/3 이상 결석시에는 F 학점**" — the lab has its
own independent attendance-failure condition.
⚠️ CHE1002 선수 추천과목: **일반화학및실험1(권장)** — Iden has not taken CHE1001.

**Pattern B — parens = extra period, SAME room.** MAT1002-05: `월5(월6)/수5,6`,
room `I진A218(I진A218)/동영상콘텐츠`. Nothing in the syllabus contradicts it being real
scheduled time; no 격주/optional language anywhere. (2026 version flips the halves:
`월5,6`=동영상콘텐츠 / `(수5)수6`=I진A218.)

**CONCLUSION: keep treating parenthesized periods as occupied time.** Verified correct
for Pattern A; unrefuted and conservative for Pattern B. **VERIFY.md item 4 CLOSED.**

---

## R55. ⚠️ SciLit pool is 93% SEQUEL courses — Iden lacks every prerequisite (1)
Deduplicated xlsx, 국제, Fall 2026: **42 SciLit sections, of which 39 are "(2)" sequels**
— CHE1002 ×14 · PHY1002 ×12 · MAT1002 ×7 · BIO1002 ×6. Fall is the *second* half of
year-long science sequences; Iden took **no science and no calculus** in Sem 1 (R27).

**Only 3 non-sequel SciLit options exist in all of Fall 2026 국제:**
| Section | Course | Time | Mode | Note |
|---|---|---|---|---|
| MAT1001-02-00 | Calculus & Vector Analysis (1) | 화5(화6)/목5,6 | 블랜디드 | 목5,6 = 동영상콘텐츠 (free); also the calculus QRM2102 recommends (R38) |
| CHE1001-01-00 | General Chemistry & Experiment (1) | (화3,4)/목3,4 | 대면 | (화3,4) = weekly lab, own 1/3-absence F rule (R54) |
| UIC1751-01-00 | Science in Society | 수3,금3,4 | 대면 | no lab, no sequence |

**This reframes the SciLit-vs-RDQM choice** (they satisfy the SAME requirement, R17).
Earlier rankings had SciLit winning ~75% of the top-5000 purely on schedule geometry,
drawing freely from all 42 — but 39 of those are sequels. RDQM (UIC2151) has
**13 sections, no prerequisite, no lab, no sequence.**
⚠️ Fall 2026 GPA determines double-major admission (R32) — the sequel/lab courses carry
real academic risk. **Not a filter — a fact for Iden.** Do not auto-hide (HANDOFF §9.10).

---

## R56. ✅ Language count 83 CONFIRMED — handoff's "93" is unsupported
Deduplicated xlsx: 언어와표현 = **72** sections (72 rows, no duplicates), UIC language
(UIC1804/1805/1806/1808/1809/2302) = **11** → **83 distinct**. No combination reproduces
93 (adding 글쓰기 gives 135). The handoff's 93 came from the older incomplete
1,224-row dataset and is **withdrawn**. **VERIFY item 6 CLOSED.**

---

## R57. FREE DAYS ARE CYCLIC, NOT ADDITIVE — stated by Iden (2026-08-05)
Iden: "commute only matters for consecutive days… MON/TUE/FRI is better than
MON/WED/FRI. Nothing on Wednesday still feels good tho."

**Model implication:** a free day's value depends on its ADJACENCY to other free days,
with **Sat+Sun always free**, so the week is a **cycle (Z₇)**, not five independent slots.
- Free {월,화,금} ⇒ free run 금·토·일·월·화 = **5 consecutive days off**
- Free {월,수,금} ⇒ free run 금·토·일·월 = 4, **plus an isolated 수**
Both have 3 free days; the additive model scores them nearly the same, which is wrong.
This also *explains* the old Fri 12 / Mon 9 / mid 5 ratios (R45): 금 and 월 are the two
weekdays adjacent to the weekend — their value was contiguity all along, mis-encoded as
per-day constants.
Iden also confirms an **isolated free day still has positive value** ("nothing on
Wednesday still feels good") — so the correct form is
`value = A·(longest free run incl. weekend) + B·(each additional isolated free day)`,
NOT a pure run-length model. **A and B not yet elicited.**

### ⚠️ Impact on the CURRENT committed family: structurally limited
Given D-3/D-4 (Chinese 화1,목2,3) + QRM1001 (목4,5,6), **화 and 목 are occupied in
every one of the 2,326 timetables**. Therefore **free-day sets ⊆ {월, 수, 금}**, and
Iden's own example {월,화,금} is **unreachable this semester**. Achievable patterns:
| Free | Campus days | Free run (with weekend) | Count |
|---|---|---|---|
| 월수금 | 화, 목 (scattered, 2 trips) | 금·토·일·월 = 4, + isolated 수 | 12 |
| 월금 | 화·수·목 (consecutive, 3 trips) | 금·토·일·월 = 4 | 102 |
| 수금 | 월·화·목 | 금·토·일 = 3, + isolated 수 | 12 |
| 금 | 월–목 | 금·토·일 = 3 | 1,282 |
| 월 | 화–금 | 토·일·월 = 3 | 242 |
| none | 월–금 | 토·일 = 2 | 676 |
→ The cyclic refinement changes little inside the committed family (금 and 월 already
dominate) but is now correctly *modeled* rather than accidentally right.

**Amendment (Iden, same day): Friday carries an EXTRA bonus beyond contiguity** —
"a lot of school events are held on Friday." So the free-day term is
`A·(longest free run) + B·(each isolated free day) + C·[금 free]`, C > 0 separate from A.

---

## R58. ⚠️⚠️ CHAPEL: Iden may take ONLY the 2 ENGLISH sections — pool 7 → 2
Two independent sources agree:
1. **수강편람 §10 "UIC 채플 수강신청 안내"**: `1학년 → 국제캠퍼스 영어채플만 신청가능`
2. **수강편람 §11 table**: YCA1006-**01** (화2) and **-02** (화3) are the 영어 sections,
   수강대상 "UD 1-2학년, **HASS/ISE 전 학년**"; -03~-07 are 수강대상 "1학년" with 비고 "-"
   (Korean) or 소그룹.
3. **xlsx 유의사항 confirms independently**: only YCA1006-01 and -02 carry
   `"UIC, 영어채플"` (and `언어=10`); the other five have an EMPTY note.

Iden = UIC **HASS**, 1학년 → **eligible chapel sections = YCA1006-01 (화2) and
YCA1006-02 (화3) ONLY.** Both are Tuesday.
(Consistent with Sem 1: Iden took 채플(A) on a Tuesday — R27.)

**Impact:** every prior ranking used the 7-section pool and placed chapel on 수2/수3/
목2/목3/목6 in many top rows — **those timetables are INVALID.** Committed-family count
drops **2,326 → 1,310**. Free-day distribution becomes: 월수금 12 · 월금 36 · 수금 12 ·
금 682 · 월 144 · none 424. (The 12 three-free-day plans SURVIVE — they already used
화2/화3.)
⚠️ Confirm at registration: the 수강대상 grid is a PDF table whose row-alignment had to
be read by eye. The xlsx 유의사항 agrees, which is strong, but a portal check of
YCA1006-01/02 수강대상 would make it airtight.

---

## R59. ✅ CREDIT CAP IS 18, NOT 19 — handoff was WRONG
수강편람 §2 "학기당 수강학점", 2022학번 이후:
| 대상 | 수강학점 |
|---|---|
| **졸업이수학점 126학점인 대학·학과·전공 — 전 학년** | **1~18** |
| 졸업이수학점 130학점 1,2학년 / 135~140학점 전 학년 | 1~19 |

**The cap keys off the DEGREE's graduation credits, not the student's year.**
QRM = **126 credits** (R31) ⇒ **Iden's cap is 18, every semester** — the handoff's
"19 for freshmen, 18 for sophomore+" is **withdrawn** (it confused the 130-credit row).

**Exception:** 직전학기 평량평균 **≥ 3.75 → +3 credits** (⇒ 21). Iden's Spring 2026 GPA
is not yet logged — **if ≥3.75, the cap for Fall 2026 is 21.** ASK/verify.
**Exempt from the cap** (unchanged, R37): Chapel, RC자기주도활동, 사회봉사, SE, UT Seminar,
Career Development, 군사학 (ROTC ≤2cr).

**⚠️⚠️ R59 IS ITSELF WRONG — SUPERSEDED BY R86. The handoff's "19 for freshmen" was
correct and my "correction" to 18 was the error. See R86.**

**Practical impact now: none** — all 1,310 committed timetables are 15.0 academic credits
(chapel exempt), well under 18. It matters only if Iden adds a 6th academic course
(15 + 3 = 18 ✅ fits even without the GPA exception).

**✅ Iden's Spring 2026 GPA = 3.8 ≥ 3.75 → Fall 2026 cap is 21** (VERIFY item 18 closed).
Iden nevertheless targets **18** (D-17).

---

## R60. ⚠️⚠️ TARGET IS 18 CREDITS = **6 academic courses**, not 5 — Iden (2026-08-05)
Every family built so far (MR + WCiv + LHP + SciRD + Lang = 15cr + exempt chapel) was
**one course short of Iden's actual target**. Iden: "I was aiming for 18 this semester
(+chapel which doesn't count for max credits anyway)."
→ Canonical Fall 2026 shape = **6 academic courses (18cr) + 1 chapel (0.5, exempt)**.
The 6th course is an **ME or ELEC** (all CC slots are filled by the other five).
This supersedes the 5-course framing in R46/R48/R58 counts.

---

## R61. ⚠️⚠️ ELIGIBILITY AUDIT — 20 of 42 SciLit sections are CLOSED to Iden
Iden's own observation ("there's probably more courses that are 영어만, like the
Christianity requirement") led to a full 유의사항 audit. **The 언어 field alone is not the
gate — 유의사항 is.** Exclusion patterns found and applied:

| 유의사항 pattern | Meaning | Iden (UIC/HASS/1학년/QRM) |
|---|---|---|
| `UIC students only` | UIC-restricted | ✅ eligible |
| **`UIC LSBT & ISED only`** | UIC science divisions only | ❌ **BLOCKED — Iden is HASS** |
| **`[수강대상] 이학•생명시스템계열 9월 신입생`** | science-track freshmen | ❌ **BLOCKED** |
| `UIC-ICU LearnUs program students only` | R39 | ❌ blocked |
| `Senior students only` / `CDM first major` | — | ❌ blocked |
| `UIC First` | UIC gets priority, others get leftovers | ✅ eligible (advantage) |
| (empty) | open to all | ✅ eligible |

**Audit result:** WCiv 3/3 · LHP 15/15 · RDQM 13/13 · Chapel 2/2 · CN 2/2 · MR 1/1 ·
ME 9/9 eligible — but **SciLit 22/42**. Blocked: 20 UIC LSBT&ISED sections (all the
English science ones) + CHE1001-01 (이학계열 only).

**This rewrites R55.** Eligible SciLit = 21 sequels + **only 2 non-sequel options**:
- **MAT1001-02-00** Calculus & Vector Analysis (1), 화5(화6)/목5,6 — Korean, 대학교양
- **UIC1751-01-00** Science in Society, 수3,금3,4 — English, UIC, no lab, no sequence
CHE1001 is NOT available to Iden, contrary to R55. RDQM (13 sections, all eligible)
remains the unrestricted alternative for the same requirement.

---

## R62. 18-CREDIT REBUILD — the 6th course forces a real trade-off
All corrections applied (canonical 709 · eligibility R61 · chapel R58 · block semantics
R52 · presence R50/D-10). Shape = MR + WCiv + LHP + SciRD + CN + **1 more** + chapel.
Eligible pools: MR 1 · WCiv 3 · LHP 15 · SciRD **35** (13 RDQM + 22 SciLit) · CN 2 ·
Chapel 2 · ME 9 · ELEC 422.

| 6th course | Timetables | 3 free days | 2 free days | 1 free day | 0 free days |
|---|---|---|---|---|---|
| **ME** (major progress) | **6,282** | **0** | 88 (월수 72 · 월금 16) | 1,058 | 5,136 |
| **ELEC** (free elective) | **201,600** | **310** (월수금) | 2,558 | 101,950 | 96,782 |

**Why:** 7 of 9 ME sections meet on 금 (QRM2002 금1,2,3 · QRM2102 금5,6,7 · QRM3001 수7,8/금7
· QRM3007 수10,11/금2 · QRM4807 수5,6/금5 · QRM4808 수12,13/금4) and QRM4809 uses 수9,10/목3;
QRM2001 (화1,목2,3) collides with Chinese. **Taking any ME kills the free Friday except
QRM2004.**

**QRM2004 (화4,5,6) is the ONLY ME compatible with a free Friday** — it supplies all 348
Friday-free and all 16 월금 timetables. (Independently, R38: QRM2004 has no prerequisite
and is assignment-based 60% with no real midterm.)
ME reach overall: QRM3001 1,100 · QRM4807 987 · QRM2102 987 · QRM3007 981 · QRM4808 850 ·
QRM2002 737 · QRM2004 640.

⚠️ **Decision for Iden (not to be pre-empted):** 18 credits *with* major progress (ME)
costs the free Friday unless it is QRM2004; 18 credits with an ELEC keeps up to 3 free
days but makes no MR/ME progress. A 3-free-day week and an ME course are **mutually
exclusive** in Fall 2026.
**⚠️ SUPERSEDED IN PART by R63 — the ME-vs-ELEC framing was incomplete; a 2nd MR course
IS available. See R63.**

---

## R63. ⚠️⚠️ A SECOND **MR** COURSE IS AVAILABLE AT 국제 — my ME-vs-ELEC framing was wrong
Caught by Iden ("Why not MR? Is it unavailable?"). It was not unavailable; I never checked.

**ECO1101 MATHEMATICS FOR ECONOMICS I = the MR requirement "Mathematics for Economics 1"**
(QRM_Graduation_Requirement_table 2026~ column, MR row 4 — name match exact).
| Section | Time | Lang | Dept | Note |
|---|---|---|---|---|
| ECO1101-05-00 | 월7,8/수8 | ENG | UIC 언더우드학부(인문사회)-경제학 | UIC students Only |
| ECO1101-06-00 | 월9,10/수10 | ENG | 〃 | UIC students Only |
Both meet **Mon+Wed only** → they do NOT touch Friday.

### Full MR status for Fall 2026 국제 (all 6 MR courses checked)
| MR course | Fall 2026 국제? |
|---|---|
| Introduction to QRM (QRM1001) | ✅ 1 section — already in the base plan |
| **Mathematics for Economics 1 (ECO1101)** | ✅ **2 sections — MISSED until now** |
| Microeconomics (ECO2102, 미시경제학) | ❌ 신촌 only (R8 blocks Iden) |
| Macroeconomics (ECO2101, 거시경제학) | ❌ 신촌 only |
| Math Stat 1 / Regression (QRM dept) | ❌ 0 국제 sections (QRM3005 is 신촌) |
| Principles of Financial Engineering (QRM3003) | ❌ Spring-only (R29) |
→ **2 of 6 MR courses are reachable this semester, and Iden could take both.**

### Also newly surfaced: 원론 (principles) economics at 국제
ECO1103 미시경제원론 (월1,2,수2 — UIC-English *and* 상경 Korean) and ECO1104 거시경제원론
(화4,목5,6 UIC-English / 화8,9,목7 상경 Korean).
⚠️ These are **NOT** the MR courses — MR requires ECO2102/ECO2101 (미시/거시경제**학**,
intermediate). But 원론 are the standard prerequisites for them **and** are 전공기초 for a
신촌 Economics double major (R33, Iden's strongest candidate).
❓ **OPEN:** whether ECO1103/1104 count toward QRM **ME** credit. Unverified.

### Corrected 6th-course option table (18cr, all else fixed)
| 6th course | Timetables | 3 free | 2 free | 1 free | 0 free |
|---|---|---|---|---|---|
| **MR — ECO1101** | 1,340 | 0 | 66 (월금) | 860 | 414 |
| **원론 — ECO1103/1104** | 2,433 | **6** (월수금) | 18 | 1,317 | 1,092 |
| **ME — QRM elective** | 6,282 | 0 | 88 | 1,058 | 5,136 |
| **ELEC** | 201,600 | 310 | 2,558 | 101,950 | 96,782 |

**Key structural fact:** ECO1101 preserves the free Friday in 698 of 1,340 timetables
(52%) — far better than a QRM elective — because it meets Mon/Wed only.

---

## R64. ✅✅ ECONOMICS DOUBLE-MAJOR REQUIREMENTS FOUND — closes HANDOFF open Q3
Source: **2026학년도 2학기 수강편람**, 경제학부 이중전공 table, **25학번~ column**
(applies to Iden, 2026 entrant). Supersedes R33's "NOT YET FETCHED".

**경제학부 이중전공 = 36 전공학점 total:**
- **필수 24학점 (8 courses):** 미시경제원론 · 거시경제원론 · 미분적분학 · 통계방법론 ·
  R프로그래밍과데이터분석 **또는** 파이썬프로그래밍 · **경제수학(1)** · **미시경제학** · **거시경제학**
- **전공선택 12학점**

### ⚡ MASSIVE OVERLAP WITH QRM MR — three courses double-count
| Course | QRM role | Econ 2nd-major role | Fall 2026 국제? |
|---|---|---|---|
| **경제수학(1) = ECO1101** | **MR** (Mathematics for Economics 1) | **필수** | ✅ **2 sections NOW** |
| 미시경제학 = ECO2102 | **MR** | **필수** | ❌ 신촌 |
| 거시경제학 = ECO2101 | **MR** | **필수** | ❌ 신촌 |
| **미시경제원론 = ECO1103** | — (ME? unverified) | **필수** | ✅ 2 sections NOW |
| **거시경제원론 = ECO1104** | — (ME? unverified) | **필수** | ✅ 2 sections NOW |
| 미분적분학 (calculus) | — (counts as CC SciLit) | **필수** | ✅ MAT sections (❓ exact code match unverified) |
| 통계학입문 | ✅ DONE (CC, R27) | 유의사항 나-1: counted if it overlaps 1st-major requirements | — |

**⇒ ECO1101 is the single highest-leverage course available to Iden this Fall:** it
satisfies a **QRM MR** slot AND an **Economics 이중전공 필수** slot simultaneously, and it
is one of only 2 MR courses reachable at 국제 (R63).
**⇒ 원론 ×2 are Econ-필수 and available now**; they are *not* QRM MR.

### Other verified notes (경제학부 유의사항)
- 나-1: 이중전공 students follow their **1st major's** 교양 requirements (matches R31).
  통계학입문 required but counted as done if it overlaps — ✅ Iden has it (R27).
- **나-2: 25학번부터 경제수학(2) can NO LONGER substitute for 경제수학(1)** → ECO1101
  (경제수학1) is mandatory and non-substitutable for Iden.
- 가-4: an Economics student double-majoring elsewhere needs 36 전공학점 (reverse case).
- 3,4천단위 rule: 45 credits at the 3000/4000 level for single majors — check whether
  an Econ 이중전공 carries a 3000/4000-level minimum (⬜ unverified).

⚠️ **Not yet verified:** whether 미분적분학 in this list is satisfied by MAT1001/MAT1002
(미분적분학과벡터해석) or requires a differently-coded calculus course; and whether
ECO1103/1104 count toward QRM **ME** (VERIFY 22).

---

## R65. ⭐ IDEN'S COST PRINCIPLE: unavoidable costs are NOT costs
Stated twice, independently, now generalized:
> (on language, 2026-08-05) "If early classes are unavoidable this semester, they are
> unavoidable next semester."
> (on ECO1101, 2026-08-05) "Semester-wide fixed options are unavoidable, meaning they
> don't count as minuses."

**Formalization.** The schedule cost of taking course X *now* is not its absolute
penalty but the **differential against deferring it**:

  cost_now(X) = [best score now WITH X − best score now WITHOUT X]
              − E[ best score later WITH X − best score later WITHOUT X ]

If X inherently forces a bad slot in **every** semester it is offered, the two brackets
cancel and **cost_now(X) = 0** — the penalty is a constant of the course, not a
consequence of the timing decision, and must not be charged against taking it now.
Only *avoidable* penalty — cost that deferral would genuinely escape — counts.

**Consequences for scoring:**
1. Penalties intrinsic to a required course (it must be taken eventually) are sunk.
2. This is why Iden accepted the 화1 Chinese morning (R48) — the beginner sections are
   화1,목2,3 in any semester, so the morning is unavoidable, hence free.
3. ⚠️ Applying it requires future-semester offering data, which is **NOT fetched**
   (Spring 2027+ unknown). Where unknown, the differential is **interval-bounded**, not
   point-known — flag rather than assume.

**Applied to ECO1101 (경제수학1):** the premise of the elicitation question was
counterfactual — ECO1101 meets **월7,8/수8 or 월9,10/수10, i.e. Mon+Wed, and does NOT
touch Friday**; it preserves a free Friday in 698 of its 1,340 timetables (52%). So the
"would you give up Friday for it" trade does not actually arise. Iden's "No" bounds the
bonus **below** a free Friday's value; it does not zero it.

---

## R66. FINAL WEIGHT SET (all elicited from Iden, 2026-08-05) — implemented in `rank.py`
Anchor: **one 1교시 (9am) day = −10**. Only ratios matter.

| Term | Value | Source |
|---|---|---|
| day starts 1교시 | −10 | anchor |
| day starts 2교시 | −5 | ⚠️ provisional, never re-elicited |
| lunch-fail day (3·4·5 busy) | −6 | fitted: lunch+marathon = 13.75 from the "big hole ≈ small holes" equality |
| marathon (≥4 consecutive) | −8 | same constraint; must exceed a 2-period hole (Iden chose the hole) |
| day ends ≥10교시 | −1 | elicited ("no preference" at ≈1 short gap) |
| dead block of ℓ periods | −10·(ℓ/4)² | elicited: 4-period hole ≈ one 9am; short gaps nearly free |
| weekend-attached free day | +18.75 | Monday = 75% of Friday (**Iden chose the earlier answer**) |
| run-length exponent | (L−2)^1.6 | "the 4th consecutive day is worth MORE than a full Friday" |
| Friday events bonus | +6.25 | = 25% of Friday's value (implied by Mon=75%) |
| isolated free day | +4.70 | 25% of an attached day ("still feels good") |
| **ECO1101 course bonus** | **+10** | Iden's ONE accepted per-course exception (= 1 early morning) |

**Free days use the PRESENCE mask; every other term uses the TIME mask** (D-10).
Free-day value is cyclic over Z₇ with Sat+Sun always free (R57).
⚠️ Iden's two answers on Mon-vs-Fri conflicted (75% vs the 50% implied by "events are
half"); Iden resolved it explicitly in favour of **75%**.

---

## R67. ⚠️ Two scorer bugs found and fixed (2026-08-05)
1. **Period 0 = individually-scheduled research/thesis.** 5 sections (SED4001, NSE4001,
   ASP4009, SIT3010, SIT4308) list 교시 **0** — 유의사항: "학생 개개인의 일정에 따라
   개인별 지도가 진행될 예정임". No fixed meeting time. They were **ranking #1** because
   period 0 dodged every time penalty while still filling a day. Now: period-0 cells
   occupy neither time nor presence, and these senior research courses are excluded.
2. **MAT1012 is 공학수학(2) Engineering Mathematics, NOT calculus** — it is not in the
   SciLit list (R41) and satisfies no requirement. It ranks high purely on geometry;
   correctly typed as ELEC, but worth knowing before picking it.

---

## R68. ✅ FOUR Econ 이중전공 필수 courses are available at 국제 this Fall
Cross-referencing R64's list against the catalogue:
| Econ 필수 course | Code at 국제 | Sections | Also QRM? |
|---|---|---|---|
| 경제수학(1) | **ECO1101** | 2 (월7,8/수8 · 월9,10/수10) | ✅ **QRM MR** |
| 미시경제원론 | **ECO1103** | 2 (월1,2,수2) | ❌ (ME? unverified) |
| 거시경제원론 | **ECO1104** | 2 (화4,목5,6 · 화8,9/목7) | ❌ |
| **미분적분학** | **STA1002** | 2 (월5,6,수6 · 월3,4/수4) — 상경대학 경제학전공 | ❌ (not in SciLit list R41) |
| 통계방법론 | — | **0 at 국제** | — |
| R프로그래밍/파이썬 | — | 0 exact match (CTM1004 "Computer Programming and Literacy" is a possible substitute — **unverified**) | — |
| 통계학입문 | — | ✅ **DONE** Sem 1 (R27); counted per 경제학부 유의사항 나-1 | — |

⚠️ **STA1002 미분적분학 was newly discovered here** — it is 상경대학-offered but present at
국제.

---

## R69. Course bonuses — FINAL (Iden, 2026-08-05)
| Course | Bonus | Rationale (Iden's) |
|---|---|---|
| **ECO1101** 경제수학(1) | **+10** | QRM **MR** *and* Econ 이중전공 필수 — one slot, two degrees |
| **ECO1103** 미시경제원론 | **+5** | Econ 이중전공 필수 |
| **ECO1104** 거시경제원론 | **+5** | 〃 |
| **STA1002** 미분적분학 | **+5** | 〃 |
Iden restated R65 when giving these: point values are **net of unavoidable cost** — a
penalty that recurs every semester (e.g. a 9am that is always 9am) is not a cost of
taking the course *now*.

### ✅ R65 verified to be automatically satisfied *within* this semester
A penalty identical across every candidate timetable is an additive constant and cannot
change the ranking. Checked on the top-5000: early1 {1:4047, 2:953}, early2, lunch_fail,
late and marathon all **vary** → every penalty currently in the score is genuinely
avoidable, so none of them is being wrongly charged.
The 화1 Chinese morning is the one truly forced cost; it contributes the `early1 = 1`
floor seen in every row, and being constant it is ranking-neutral.
⚠️ R65's **cross-semester** half (deferral differential) still cannot be computed —
Spring 2027+ offerings are unfetched. Where it matters, it is a flag, not a number.

---

## R70. RANKING RESULT after bonuses (207,882 scored; `FINAL_ranked.csv`)
Top score **42.54**. Top-50: **40 have 월수금 free** (2-day campus week), 10 have 월금.
6th-course type — top-50: ELEC 36 · Econ2nd 10 · MR+Econ2nd 4.
Top-500: ELEC 441 · Econ2nd 31 · **MR+Econ2nd 26** · ME 2.
**#1 timetable:** QRM1001 목4,5,6 · UIC1561 WestCiv (fully online) · UIC1551-01 화7/목8,9 ·
MAT1001-02 화5(화6)/목5,6 · Chapel 화3 · Chinese 화1/목2,3 · **ECO1104-07 화8,9/목7** —
campus only 화·목, one forced 9am, one lunch-fail, two 1-period gaps.
Note the #1 uses **MAT1001 Calculus(1)** — the non-sequel SciLit option (R55/R61) — and
an Econ 이중전공 필수 course, i.e. it closes CC-SciLit and an Econ requirement together.

---

## R71. ⚠️ RENDER BUG (caught by Iden from the visual): 동영상콘텐츠 cells were INVISIBLE
The grid only drew cells present in `time` ∪ `pres`. Since 동영상콘텐츠 blocks occupy
**neither** (R52), they were drawn nowhere — e.g. ECO1104-07 (화8,9/목7, room
동영상콘텐츠/I진A218) showed only 목7, and its 화8,9 vanished from the picture.
**Fixed:** the renderer now parses every period printed in 강의시간 and draws three
distinct kinds — 대면(solid) · 온라인(hatched, time but no campus) · 동영상콘텐츠(faded,
occupies nothing). A real block never gets hidden by a video block.
Iden spotted this from the artifact, which is exactly what the artifact is for.
⚠️ Verification lesson: my first check script misaligned because empty `<td></td>` has no
class attribute — the *checker* was wrong, not the renderer, on the second cell. Parse
`<td ...>...</td>` pairs, never two independent findall lists.

---

## R72. ⏰ 교시 CLOCK TIMES (수강편람 p.61) — every 교시 is 50 min, on the hour
| 교시 | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 시각 | 08:00 | 09:00 | 10:00 | 11:00 | 12:00 | 13:00 | 14:00 | 15:00 | 16:00 | 17:00 | 18:00 |
→ **N consecutive 교시 = N hours.** Lunch band 3·4·5 = 11:00–13:50. 1교시 = 09:00.

---

## R73. ⚠️ MARATHON PENALTY IS BROKEN — flagged by Iden ("4연강 can mean 4 hours or 9 hours")
`rank.py` fires `if run == 4` **once per run**, so a run of 4 periods and a run of 13
periods both cost exactly −8. Measured over the top-5000 (6,194 runs total):
| run length | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 13 |
|---|---|---|---|---|---|---|---|---|
| occurrences | 501 | 2,597 | 2,093 | 108 | 750 | 135 | 2 | 8 |
**50% of runs are ≥6 hours straight, priced identically to a 4-hour run.** Longest
observed: **13 consecutive 교시 = 09:00–21:50**. The penalty must scale with length.
**✅ FIXED 2026-08-05.** Iden's spec: *"convex-like scale but generally all lower than
steady. 4h = −8 still holds."* Implemented as **MARATHON(L) = −(8 + 0.8·(L−4)²)**:
| L (hours) | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 13 |
|---|---|---|---|---|---|---|---|---|
| this curve | −8 | −8.8 | −11.2 | −15.2 | −20.8 | −28 | −36.8 | −72.8 |
| "steady" −8(L−3) | −8 | −16 | −24 | −32 | −40 | −48 | −56 | −80 |
Convex, anchored at −8, and strictly milder than steady for every L in 5…13. Also fixed:
runs ending at the last period of a day were never being closed, so they escaped the
penalty entirely. New column `runs_hours` in the CSV lists each run's length.
**Effect:** top score 42.54 → 40.79; top-50 6th-course mix shifted toward ECO1101
(MR+Econ2nd 4 → 8).

---

## R74. ✅ SPRING 2026 DATA LOADED — cross-semester (R65) checks now possible
Source: `강의목록_전체_v3.xlsx` (uploaded by Iden 2026-08-05; built ~6 months ago).
2026-**1**학기, 1,303 rows: 국제 869 rows → **776 distinct** · 신촌 434.
⚠️ **Completeness caveat:** Fall 2026 has 863 신촌 rows vs Spring's 434 — the Spring file
looks **incomplete for 신촌**. 국제 (776 vs Fall's 715) looks plausible. Use for 국제
questions only.

### Findings that bear directly on R65 (avoidable vs unavoidable cost)

**1. QRM electives are NOT always on Friday → the Friday cost IS avoidable.**
Spring 2026 국제 QRM offerings: QRM2001 화1,목2,3 · QRM2100 화6,7/목7 · **QRM2101
Multivariate Calculus 월4,5,6** · QRM3002 수5,6/금5 · QRM3003 수7,8/금7 · QRM3004 금1,2,3.
Three of six touch no Friday. Fall's 7-of-9-on-Friday is a **Fall property, not a
permanent one** ⇒ by R65 the Friday penalty on a Fall QRM elective legitimately counts,
and the current ranking's treatment is correct. **Iden's conjecture resolved: it does
NOT hold all-semester.**

**2. ECO1101 recurs in the SAME slots** — Spring 2026: 월7,8/수8 and 월9,10/수10,
identical to Fall 2026. So it is **not** a now-or-never offering; deferring it appears
low-risk. (It remains MR + Econ-필수 double value.)

**3. ⚠️ Beginning Chinese has NON-9am sections in Spring** — UIC1805-02 화4,목5,6 ·
UIC1805-03 화5,6,목4 · UIC1805-04 화1,목2,3. So the 화1 morning is **avoidable by
deferring**, contradicting the premise Iden used in D-3/R48 ("if early classes are
unavoidable this semester, they are unavoidable next semester"). In Fall the 9am is
forced only by the collision with QRM1001 목4,5,6 — and QRM1001 will already be done by
Spring. **This reopens the language-timing decision; Iden should be told.**

**4. QRM3004 REGRESSION ANALYSIS (Spring, 금1,2,3) is an MR5 course** — "Math Stat 1
**or** Regression Analysis" (R18). So **MR5 IS reachable at 국제, in Spring.**
REQUIREMENTS_AUDIT B5 said "no 국제 section" — true for **Fall**; must be annotated.

**5. STA1002 미분적분학: 0 sections in Spring 국제** → Fall-only at 국제. If Iden wants it
for the Econ 이중전공, this Fall is the opportunity (or 신촌 later).

**6. QRM3003 Spring-only confirmed** (R29) — present in Spring, absent in Fall.

---

## R75. LANGUAGE SLOT UNFIXED — Iden: "let the timetable decide" (2026-08-05)
Structure changed: the 5-course base is now **4 courses + chapel** (QRM1001 · WestCiv ·
LHP · SciRD · Chapel) plus **2 OPEN slots** drawn from everything eligible — including
Chinese/Japanese, ECO1101, 원론, STA1002, ME, ELEC. Constraints: ≤1 language course,
no course taken twice, 18 academic credits exactly (both open slots must be 3cr).
Bonuses per Iden: **ECO1101 +10 > Chinese/Japanese +8 > ECO1103/1104/STA1002 +5**
("give ECO1101 a bonus slightly higher than Chinese, but give Chinese/Japanese a bonus
too"). *Note: Iden wrote "QRM1101"; read as ECO1101 — no QRM1101 exists.*

### Result: the ranking says DEFER the language
Top score **73.71** (vs 40.79 when Chinese was forced — a 33-point swing).
**No language course appears until rank 972** (score 48.79, **24.9 below #1**);
0 in the top 500, 125 in the top 5000.
Mechanism: with QRM1001 fixed at 목4,5,6, the only compatible language sections are the
화1 ones ⇒ taking a language forces a 9am (−10) **and** consumes a slot that could hold
ECO1101 (+10) or STA1002 (+5). Net swing ≈ 25 points, far beyond the +8 bonus.
**#1:** QRM1001 목4,5,6 · YCE1253 WestCiv 화5,6 · UIC1551-01 화7/목8,9 · MAT1002-05
월5,6/수5,6 · Chapel 화3 · **ECO1101-05 월7,8/수8** · **STA1002-04 월3,4/수4** —
월+금 free, **zero 9am days, zero 4h+ runs**. 49 of the top 50 have no 9am at all.

---

## R76. ⚠️ THREE MORE SCORER BUGS (found while unfixing the language slot)
1. **Saturday was invisible.** `week_value` assumed 토/일 always free, and the day loop
   ran `range(5)`. Four 토 sections existed (NSE4001/ESE4001/UBC4001 senior theses,
   CTM4001) — they scored as *pure profit*: no weekday penalty, no lost free day.
   UBC4001 "BC SENIOR THESIS 토5,6,7" reached **rank 2**. Fixed: masks and penalties now
   cover all 7 days, and 토/일 count as free only if genuinely empty.
2. **Eligibility patterns were too narrow.** `Senior students only` did not match
   "UIC **Seniors** only" (UBC4001) or "Only pre-app**p**roved students" (CTM4001, note
   the typo in the source) or "해당학과 Only" or "2학년 이상만" (SIT3018). Now
   case-insensitive with broader alternatives.
3. **Credits were never enforced.** SIT3018 is a **1-credit** course and reached the top
   ranks, producing 16-credit timetables against Iden's 18-credit target (D-17). Now the
   two open slots must sum to exactly 6 credits.
Post-fix validation over the full top-5000: wrong-credits 0 · duplicate-course 0 ·
weekend-class 0.

---

## R77. 학년 PENALTY — Iden (2026-08-05), triggered by UBC4001 (senior thesis) ranking high
Iden: *"we should give penalties to anything that has 학년 4+, 3, 2. If it has multiple
학년s, then the lowest decides. If it has null, then no penalty. Penalties should scale
pretty sharply."*

**Implemented:** `YEAR_PEN(y) = 0 if y ≤ 1 else −10·(y−1)^2.5`, where y = **lowest**
listed 학년 ("3,4" → 3; "0"/null → 0 → no penalty). Applied to **all seven** sections.
| 학년 | 0/1 | 2 | 3 | 4 |
|---|---|---|---|---|
| penalty | 0 | **−10** | **−56.6** | **−155.9** |
Anchored so 학년 2 = one 9am morning; 학년 4 is effectively disqualifying (larger than
the entire top score of 73.7) without being a hard filter — 학년 is advisory (R1), so
this must remain a penalty, never an exclusion.
국제 pool 학년 distribution (lowest-year basis): 0→375 · 1→199 · 2→63 · 3→52 · 4→20.

**Effect:** top-50 is now **100% 학년-1-or-lower**; top-500 has 15 rows touching 학년 2
and none above; 학년 3/4 courses are gone from the top 5,000 entirely.

---

## R78. CREDIT FLOOR, not a fixed total — Iden (2026-08-05)
*"19 credits is also possible (19.5 including chapel). 18.5, 18 all possible. Just not
below 18."* → constraint is **academic credits ≥ 18**, capped at 21 (R59, GPA 3.8).
Implemented as: the two open slots must total 6–9 credits (base is 4×3 = 12).
⚠️ **18.5 is not reachable with this structure** — 국제 credit values are
{3.0: 584, 1.0: 86, 0.5: 31, 2.0: 5, 4.0: 2, 6.0: 1} and no 3.5-credit course exists;
18.5 would need a third small course (the 0.5-credit ones are all chapel/RC/SE, already
cap-exempt or excluded). In practice every surviving timetable is **exactly 18.0**.

---

## R79. CURRENT BEST (after R75–R78) — score 73.71
| Slot | Section | Time | 학년 |
|---|---|---|---|
| MR | QRM1001-01 Intro to QRM | 목4,5,6 | 1 |
| WestCiv | YCE1253-01 | 화5,6 (+목4 동영상) | 0 |
| LHP | UIC1551-01 World History II | 화7, 목8,9 | 1 |
| SciRD | MAT1002-05 Calculus & Vector Analysis 2 | 월5,6/수5,6 | 0 |
| Chapel | YCA1006-02 | 화3 | 0 |
| open | **ECO1101-05 경제수학1** | 월7,8/수8 | 1 |
| open | **STA1002-04 미분적분학** | 월3,4/수4 | 1 |
**월 + 금 free · zero 9am · zero 4h+ runs · 18.0 credits · max 학년 1.**
Closes: QRM MR ×2 (QRM1001, ECO1101) · CC WestCiv · CC LHP · CC SciLit · Chapel pass,
and ECO1101 + STA1002 are both Econ 이중전공 필수 (R64/R68).
**⚠️ INVALIDATED by R80 — the WestCiv section used (YCE1253) is not a CC course.**

---

## R80. ⚠️⚠️ WestCiv AND LHP POOLS WERE WRONG — 대학교양 lookalikes are not CC courses
**Caught by Iden from the artifact:** *"Western Civilization is NOT 'western civilization
in the perspectiv'."* Correct — the pool was inherited from HANDOFF §8 and never verified.

| Section in old pool | 국문 | Dept | Verdict |
|---|---|---|---|
| **UIC1561-01** WESTERN CIVILIZATION | (English title) | **UIC 공통교과과정(국제)** | ✅ the real CC course |
| UCB1103-02 | **서양문화의유산** (Heritage of Western Culture) | 대학교양 인간과역사 | ❌ different course, English title merely translates alike |
| YCE1253-01 | **책의역사로본서구문명** (Western Civilization Seen Through the History of Books) | 대학교양 인간과역사 | ❌ a specialised book-history course |

**Decisive evidence:** the CC requirement is a **UIC Common Curriculum** item. The UIC
guide (§11.1) describes Western Civilization as a specific UIC lecture course, and
Iden's own completed Eastern Civilization was **UIC1581**, the UIC-coded CC course —
not a 대학교양 lookalike. The UIC CC department offers exactly **one** WestCiv section.

**Same error in the LHP pool:** `YCD1103 세계문학과사회적상상력` is 대학교양 문학과예술, not
UIC CC. The 14 UIC-coded sections (UIC1251/1351/1401/1501/1551) are the real pool.

### Corrected pools
| Slot | was | now |
|---|---|---|
| **Western Civilization** | 3 | **1** — UIC1561-01 only (월7,8/수7, fully online) |
| **L-H-P 2nd** | 15 | **14** — drop YCD1103 |
⚠️ **Every ranking produced before this is invalid**: the current #1 uses YCE1253.
⚠️ **SciLit is NOT affected** — that pool came from Iden directly (R41), not inherited.
⚠️ **Recurrence of the R63 failure mode**: inherited pool definitions, verified
downstream but never re-derived. REQUIREMENTS_AUDIT rows A2/A5 must record *which
department* satisfies each requirement, not just a section count.

---

## R81. ✅ FULL POOL RE-DERIVATION from the HASS section of the guide (2026-08-05)
Iden asked for every pool to be rechecked. **Key discovery: the guide has a
HASS-specific CC section, §11.3, distinct from §11.1 (UD)** — and I had been quoting
§11.1. Iden is QRM ⊂ **ISSD ⊂ HASS Division** (guide p.1190/1203), so **§11.3 governs**.

| Pool | Verified source | Sections | Change |
|---|---|---|---|
| Chapel | R58 + xlsx 유의사항 | **2** (YCA1006-01 화2 · -02 화3) | unchanged |
| CC L-H-P 2nd | §11.3 categories, UIC CC only | **14** | unchanged (post-R80) |
| Science Literacy & Research Design | §11.3 names the courses | **35** = SciLit 22 + RDQM 13 | unchanged |
| Western Civilization | §11.3 + UIC CC dept | **1** (UIC1561) | unchanged (post-R80) |
| Language | §11.3 "one foreign language course" | 11 UIC CC (Iden restricts to CN/JP) | unchanged |
| MR QRM1001 | catalogue | **1** | unchanged |
| MR ECO1101 | R63/R64 | **2** | unchanged |
| UIC Seminars | §11.3 | 4 eligible at 국제 | ⚠️ see R83 |
**Conclusion: the pools currently in `rank2.py` are correct.** No further changes.

### ⚠️ The R80 trap recurs in SciLit — and Iden's list already avoided it
Matching the guide's English wording ("General Chemistry and Experiments", "Calculus
and Vector Analysis", …) inflates SciLit to **73** sections, because these are DIFFERENT
Korean courses wearing similar English titles:
| Code | 국문 | 영문 | Verdict |
|---|---|---|---|
| CHE1012 | **공학**화학및실험(2) | GENERAL CHEMISTRY AND EXPERIMENT(2) | ❌ engineering chem |
| PHY1012 | **공학**물리학및실험(2) | GENERAL PHYSICS AND EXPERIMENT(2) | ❌ engineering physics |
| BIO1009 / MAT1017 | …(**심화**) | …(HONORS) | ❌ honours variants |
| STA1002 | **미분적분학** | CALCULUS | ❌ not "…and Vector Analysis" |
| FNS1001 | 일반화학 | GENERAL CHEMISTRY | ❌ no lab |
**Iden's R41 list is code-based and excludes all of them — it was right.** SciLit stays
at 22 eligible (MAT1002 ×5 · CHE1002 ×9 · PHY1002 ×6 · MAT1001 ×1 · UIC1751 ×1).
⚠️ Note this also means **STA1002 미분적분학 does NOT satisfy CC SciLit** — it counts only
toward the Econ 이중전공 (R68). It is correctly in the OPEN pool, not the SciRD pool.

---

## R82. ⚠️ SciLit "cannot be double-counted"
§11.3 verbatim: Science Literacy and Research Design "**will not be double-counted
toward other requirements**". Also: "The History of Science and Technology course will be
considered as a science literacy course only, and will not satisfy World History Group I".
→ If MAT1001 fills the SciLit slot it cannot simultaneously fill anything else **within
UIC CC**. Whether it may still count toward the **Economics 이중전공** 미분적분학 requirement
is a different programme's rule and is **UNVERIFIED** (VERIFY 27 remains open).

---

## R83. ⚠️⚠️ UIC SEMINAR WINDOW — §11.3 (HASS) states NO window; R15 quoted §11.1 (UD)
| Section | Text |
|---|---|
| §11.1 **UD** | "…will take one UIC Seminar per semester … **from the second semester of their sophomore year through the first semester of their senior year**" + "required to take **4** UIC Seminars" |
| §11.3 **HASS** | "UIC Seminars (6 credits): HASS students are required to take **two** UIC seminars. Courses with course codes of UIC35(XX) and UIC36(XX) are UIC Seminars." — **no window, no per-semester limit stated** |
R22 (2 seminars) is confirmed by §11.3 ✅. But **R15/R23's Sem 4–7 window came from the
UD section, which does not govern Iden.** 4 eligible seminars exist at 국제 this Fall
(UIC3527 월5,6/수6 · UIC3643 화5,6/목4 · UIC3649 화7/목8,9 · UIC3657 화7/목8,9).
⚠️ Iden previously *confirmed* the window (R23) — so this contradicts a user-stated fact
and must be **asked, not assumed**. If there is no window, seminars become eligible
OPEN-slot candidates for Fall 2026 and the requirement audit changes (A6 currently reads
"structurally deferred").

---

## R84. ✅ MATCH BY 학정번호, NEVER BY NAME — standing rule (Iden, 2026-08-05)
Iden, confirming the SciLit list: *"only this list is officially part of it, **check the
code for eligible classes, not similar names**."*
Authoritative SciLit codes (13): UIC1541 · UIC1918 · UIC1502 · UIC1920 · UIC1751 ·
MAT1001 · PHY1001 · CHE1001 · BIO1001 · MAT1002 · PHY1002 · CHE1002 · BIO1002.

**Generalised as a standing rule.** English course titles are unreliable across
departments (R80 WestCiv, R81 SciLit). Every pool must be defined by an explicit set of
학정번호 prefixes. Audit of `rank2.py` after this instruction:
| Pool | Matching | Status |
|---|---|---|
| SciLit | code set (13) | ✅ already code-based |
| RDQM | `UIC2151` | ✅ code |
| WestCiv | `{UIC1561}` | ✅ code (fixed R80) |
| Chapel | exact section ids `YCA1006-01/02` | ✅ code |
| MR | `QRM1001`, `ECO1101` | ✅ code |
| Language | `{UIC1805, UIC1806}` | ✅ code |
| **L-H-P** | was regex `WORLD (HISTORY|LITERATURE)` + dept | ⚠️ **converted to code set** `{UIC1251, UIC1351, UIC1401, UIC1501, UIC1551}` |
Pool sizes after conversion are unchanged (LHP 14), so no ranking changed — but the last
name-based pool is now gone.

⚠️ The eligibility **filter** still matches 유의사항 *text* (e.g. "LSBT & ISED only").
That is prose in a free-text field with no coded equivalent, so it cannot be
code-based — it remains the one text-matched component (R61/R76).

---

## R85. ⚠️ CODE-BASED ISN'T ENOUGH — 유의사항 declares CROSS-COUNTING equivalences
**Caught by Iden:** *"Are you sure those are the codes for World History/Literature?
I'm pretty sure there were a LOT."* Correct — two courses satisfy CC L-H-P under codes
that look nothing like UIC15xx:

| Code | Course | Time | 학년 | 유의사항 (verbatim) |
|---|---|---|---|---|
| **ASP2022** | AS LHP: Chinese Cinemas | 화7,8/목7 | 2 | "This course is **also considered as World History: Group Ⅱ**, but credited only once for either CC or AS major." |
| **ASP2033** | North Korea: History, Culture, Politics | 화2,3,4 | 2 | same clause |
Both are in 언더우드국제대학 **공통교과과정(국제)** — i.e. genuinely CC. Added.
**CC L-H-P pool: 14 → 16 sections.**

Excluded after checking: ASP2100 / ASP2102 also carry "AS LHP:" in the title but sit in
아시아학부-아시아학 (not CC) and **lack** the equivalence clause → not L-H-P for Iden.

### The generalised lesson (third distinct failure mode)
1. R63 — pool inherited, never re-derived (missed ECO1101)
2. R80/R81 — matched by English name (admitted 대학교양 lookalikes)
3. **R85 — matched by code, but the code LIST was built from what looked like the
   requirement, not from every course the catalogue declares equivalent.**
→ **Rule: build pools from code sets AND sweep 유의사항 for equivalence clauses**
(`also considered as` · `also counted` · `fulfills … requirement` · `교차인정`).

### Full equivalence sweep of the Fall 2026 국제 catalogue (18 sections, 11 courses)
| Declares | Courses |
|---|---|
| World History Group Ⅱ | **ASP2022, ASP2033** ← added to L-H-P |
| "fulfills the language & arts requirement" | UIC1804/1805/1806/1808/1809/2302 — all already in the Language pool ✅ |
| 전공-교양 교차인정 | BIZ1101 (논리와수리), EDU2002 · SOC1004 (국가와사회) — these cross-count toward *대학교양* areas Iden has no outstanding requirement in → no effect |
No other equivalence clauses exist. **Pools are now complete.**

**Effect on ranking: none at the top.** Top score stays 64.91 and UIC1551-01 still wins
the L-H-P slot in all of the top 500 — both ASP courses are 학년 2 (−10) and neither
beats UIC1551-01 geometrically. The pool is now correct regardless.

---

## R86. ❌ MY R59 WAS WRONG — the cap IS 19 for a HASS **freshman**. Handoff reinstated.
Source: **2026 Spring UIC Course Enrollment Guide §3.1 credit table** (uploaded by Iden
2026-08-05). The guide has a **UIC-specific** table keyed on division AND year:
| Credits | Who | Mileage | Requirement credits |
|---|---|---|---|
| **18** | UIC UD H&SS **sophomore to senior**, **HASS Division sophomore to senior** | 72 | 126 |
| **19** | UIC UD H&SS **freshman**, **HASS Division freshman**, UD LSBT, ISE Division | 76 | 126~135 |
| Other | +3 extra credits for GPA > 3.75 in the previous semester | | |

**Iden is a HASS Division freshman in Fall 2026 (1학년 2학기) ⇒ cap = 19**, and with the
Spring GPA of 3.8 the +3 allowance applies ⇒ **effective cap 22**.

**What I got wrong:** R59 read the university-wide 수강편람 rule ("졸업이수학점 126 → 1~18")
and used it to *withdraw* the handoff's "19 cr for freshmen, 18 for sophomore+". But the
UIC guide is the more specific authority for UIC students, and it keys the cap on
**year within division**, not on the degree's total credits. **The handoff was right; my
correction was the error.** R59 is superseded.
Lesson: a university-wide rule does not override a college-specific table. When two
sources disagree, prefer the one scoped to Iden's actual population — and say so.

**Practical impact: none on the current ranking.** All candidates are 18.0 academic
credits (R78), comfortably under 19. It only matters if Iden ever wants a 19-credit term.

---

## R87. ✅ UIC SEMINAR WINDOW — confirmed to be a **UD** rule, absent for HASS
Full-text sweep of the guide for seminar timing: the only occurrence is **line 875**,
inside §11.1 (UD): "…one UIC Seminar per semester (3 credits each) **from the second
semester of their sophomore year through the first semester of their senior year**."
The HASS section §11.3 (lines 979–1036) states only: "UIC Seminars (6 credits): HASS
students are required to take **two** UIC seminars." — **no window, no per-semester cap.**
The QRM graduation table likewise lists "UIC Seminars — 6" with **no timing note**.

⇒ **R15/R23's Sem 4–7 window has no basis for Iden** (QRM ⊂ ISSD ⊂ HASS Division).
⚠️ Iden had *confirmed* that window (R23) — a user-stated fact now contradicted by the
governing document. **Not overridden unilaterally; flagged for Iden's decision.**
If it does not apply, 4 seminars are available at 국제 this Fall (UIC3527 월5,6/수6 ·
UIC3643 화5,6/목4 · UIC3649 화7/목8,9 · UIC3657 화7/목8,9), all 학년 3 → −56.6 penalty
under R77, so they would rank poorly anyway unless Iden values seminar progress
explicitly. **REQUIREMENTS_AUDIT row A6 stays "deferred" until Iden rules.**

---

## R88. ⚠️⚠️ EXAM CLASH RISK from 동영상콘텐츠 overlap — officially warned, and I under-sold it
Source: **교무처 학사지원팀, "2026학년도 2학기 학부 수강신청 및 변경 안내" (2026.07.13)**,
link supplied by Iden. Verbatim:
> "특히 중복수강이 가능한 **동영상콘텐츠 수업**의 경우 **중간 및 기말시험 일정이 타 수업의
> 강의 및 시험시간과 겹쳐 문제가 될 수 있으므로**, 시험 일정과 방식을 반드시 확인하시기 바랍니다."

So the overlap freedom that makes these timetables score well is **explicitly flagged by
the university as an exam-collision hazard**. Iden raised this unprompted; it is real.

**Measured over the current top-50** (a "clash candidate" = one course's 동영상콘텐츠 cell
sitting on another course's real class):
| overlaps per timetable | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| timetables | **1** | 5 | 29 | 2 | 13 |
→ **49 of the top 50 carry at least one.** #1 has four (MAT1002-04's 목5,6 video under
QRM1001; YCK1998's 월7,8 video under UIC1561).
**Best timetable with ZERO overlap: rank 47, score 53.84** (vs #1's 60.84) — a 7-point
premium for eliminating the risk entirely.

⚠️ This is NOT modelled in the score. It cannot be resolved from the catalogue — only the
per-course 강의계획서 states exam dates/times. **Options for Iden: (a) ignore, (b) add a
penalty per overlap, (c) prefer the zero-overlap branch, (d) check 강의계획서 exam dates
for the shortlist before Aug 25.** Not decided by the assistant.

---

## R89. ❌ MY CHAPEL EXAMPLE WAS THE WRONG CAMPUS — Iden is on 국제, which is fully in-person
I illustrated 동영상 viewing with the chapel weekly window (화 0:00 ~ 다음 월 23:55).
That is the **신촌** chapel. 수강편람 1-다: "**국제캠퍼스 채플은 전면 대면 채플로 개설합니다.**"
Iden takes YCA1006 at 국제 = **offline, in person, 화2 or 화3** (R58). Iden's correction
accepted; the example did not apply to them.

---

## R90. ⚠️ REGISTRATION MECHANICS — freshmen get 정원미달 courses only
Same 학사지원팀 notice. **2026-2학기 timetable:**
| Round | When | Mechanism |
|---|---|---|
| 2학년 이상 | 8.10(월) 09:00 ~ 8.11(화) 17:00 | 마일리지선택제 |
| 결과 조회 | 8.12(수) 16:00~ | |
| 추가수강신청 | 8.13(목) 09:00 ~ 8.14(금) 17:00 | 대기순번제 |
| **신입생 및 1학년 ← Iden** | **8.25(화) 09:00~17:00** | **"정원미달과목 신청 가능"** |
| 2차 복학생 | 8.27(목) | |
| 수강변경 | 9.3(목) 08:00 ~ 9.7(월) 17:00 | |

**"정원미달과목 신청 가능"** confirms R47's revised reading: on Aug 25 Iden can only take
courses that still have seats after the sophomore+ rounds. Over-capacity courses give a
**대기번호** (waitlist) rather than a seat.
⚠️ Consequence: **section availability on Aug 25 is unknowable in advance** — it depends
on what upperclassmen leave behind. This raises the value of ranked *fallbacks* over a
single optimal pick, and makes the 9.3–9.7 수강변경 window a real second chance.
Also noted: 진급학년 is checkable at 학사포탈 > 학적 > 학적정보조회 — worth confirming Iden
is coded as 1학년 (determines which day applies).

---

## R91. ⚠️ "공강일" WAS BEING PAID FOR DAYS THAT AREN'T FREE — and the bias had a gradient
**Raised by Iden:** *"Video classes basically seem to disappear off of the timetable, but
I still do put in effort to listen to it. I feel like that effort is just gone."*

**Measured.** Hours of class sitting on days the model scored as 공강:
| Band | avg hours on a "free" day |
|---|---|
| **top-50** | **6.10** |
| 51–500 | 5.02 |
| 501–5000 | 4.42 |
**The higher the rank, the more work is hidden on the "free" days** — and **0 of 5,000
timetables have a genuinely empty free day.** Iden's #1 carried 6 hours across 월+금.
Root cause: free-day values (+18.75/day, superlinear run bonus — **+63** in #1) were
elicited while Iden pictured *days off* ("a 4-day break", "school events"), but D-10
defined the trigger as *no commute*. Both statements were true; they came apart.

**Null result, reported honestly:** total class hours are ~constant (19–21, mostly 20)
at every rank, and 동영상 hours average 3.5–4.0 in every band. So a flat per-video-hour
penalty would shift all scores near-equally and change essentially nothing. The
distortion is specific to the free-day bonus, not to video load.

**Iden's ruling (2026-08-06):** 3 hours on an off day is "manageable" → **no general
discount**. But: *"the 금 bonus over 월 happens because of school events, and if those
3 hours cross over that event time (usually afternoon~evening), then that bonus becomes
meaningless. Online still occupies time."*

### Implemented: the Friday bonus is now CONDITIONAL
`FRI_EVENT (+6.25)` is awarded only if **no time-blocking class** sits in the
**event window 6–11교시 (14:00–19:50)** on Friday.
- 실시간온라인 and 동영상(중복수강불가) **void** it — they hold a fixed hour.
- **동영상콘텐츠 does NOT void it** — no fixed hour, watchable around the event (R52).
Effect: 8 of the top 50 previously collected a Friday bonus they had not earned.
Top score unchanged at 60.84 (its Friday is genuinely clear); the reshuffle is below it —
top-10 now 60.84, 60.84, 58.34 ×3, 57.96, 56.82 ×2, 56.46, 55.46.
⚠️ Event window 6–11교시 is **my interpretation** of "afternoon~evening" — adjustable.

---

## R92. ⚠️⚠️ CC REQUIREMENTS MUST BE FILLED BY **ENGLISH** SECTIONS (언어 = '10')
**Iden's decision rule (2026-08-06):** *"if [the guide] said anything about 'Only English'
for the Christianity requirement, and SLC/RDQM doesn't say anything, it's fine — but if
there's nothing said about Christianity then default-assume all CCs are mandatory
English."*

**Test result: the guide says NOTHING about language, anywhere.** A full-text sweep for
"in English / taught in / 영어로 / English only / language of instruction" returns **zero
hits** in the UIC Enrollment Guide. The Christianity entry (§11.3) names the three
qualifying courses and says nothing about language. → **the default applies.**

**Corroborated by Iden's own transcript — 7 of 7 completed CC courses were 언어 = '10':**
| Sem-1 course | Section | 언어 |
|---|---|---|
| Critical Reasoning | UIC2101-03 | 10 |
| FWIS | UIC1101-01 | 10 |
| **통계학입문** | STA1001-**11** | **10** ← a 대학교양-coded course, English section chosen |
| RC101 | UCR1007-83 | 10 |
| Eastern Civilization | UIC1581-01 | 10 |
| 기독교와세계문화 | YCA1101-**10** | **10** |
| World Philosophy | UIC1901-05 | 10 |
The 통계학입문 case is decisive: Korean sections of that course existed and Iden took the
English one.

### Effect on pools — the science path essentially dies
| Pool | eligible | English | Korean |
|---|---|---|---|
| WestCiv (UIC1561) | 1 | **1** | 0 |
| L-H-P | 16 | **16** | 0 |
| RDQM (UIC2151) | 13 | **13** | 0 |
| Chapel · Language | 2 · 4 | all | 0 |
| **SciLit** | **22** | **2** | **20** |
SciLit breakdown: CHE1002 9/0 English · MAT1002 5/0 · MAT1001 1/0 · PHY1002 6/**1** ·
UIC1751 1/**1**. All the 대학교양 science and calculus sections are Korean.
**SciRD pool 35 → 15** (RDQM 13 + UIC1751 + one PHY1002).
**Consequence: RDQM wins the slot in 100% of the top 50** and 4,863 of the top 5,000;
UIC1751 takes the other 137. Every calculus/chemistry/physics route to the requirement is
gone. Top score **60.84 → 50.21**.

### ⚠️ Routing bug found and fixed while implementing this
First implementation dropped English-failing CC courses from the dataset entirely, so a
Korean MAT1001 could not even be taken as a **free elective**. Corrected: `ok()` now
governs *registration eligibility* only, and a separate `cc_ok()` governs *whether a
section may fill a CC slot*. Korean CC-coded courses now fall through to the OPEN pool
(451 sections, up from 431) — they just can't discharge the requirement.
⚠️ R92 rests on an inference from Iden's transcript plus documentary silence, **not on an
explicit rule**. If any Korean-taught CC section is in fact acceptable, this is the single
most consequential assumption in the model — it removed 20 of 22 SciLit options.

### ✅ Falsification test (Iden's idea) — PASSED, and it strengthens R92
*"Is there any SLC class with the same code that is completely in Korean? That would turn
the tables."* Checked all 13 SciLit codes across Fall 2026 + Spring 2026, both campuses:
| Code | total | ENG | who the English sections are for |
|---|---|---|---|
| MAT1001 | 11 | 2 | **all LSBT/ISED only** |
| CHE1001 / CHE1002 | 17 / 15 | 6 / 5 | **all LSBT/ISED only** |
| BIO1001 / BIO1002 | 8 / 7 | 5 / 6 | **all LSBT/ISED only** |
| PHY1001 / PHY1002 | 16 / 15 | 7 / 7 | 6 LSBT/ISED + 1 open |
| MAT1002 | 9 | 3 | 2 LSBT/ISED + **1 open (신촌)** |
| UIC1751 | 2 | 2 | 1 open to Iden |
| UIC1541·1918·1502·1920 | **0** | — | never offered in either term |
**No SciLit code is 100% Korean anywhere.** English sections exist for every offered
code — they are simply **reserved for the LSBT/ISED science divisions**. That is a
structural argument *for* R92: if Korean sections counted, UIC would not need to run
English-only science sections for its own science students.
📌 **MAT1002 has an unrestricted English section at 신촌** — blocked this term by R8, but
the calculus route to Science Literacy **reopens from Sem 3**.

---

## R93. ⚠️ WHAT COUNTS AS **ME** (Major Elective) — partially answered, key gap remains
Raised by Iden after the Korean-cap discussion. The QRM requirement table names all six
**MR** courses but gives **ME** only as a credit total (24, or 18 with a double major) —
**no course list anywhere**, in the table, the 수강편람 (which does not mention 계량위험관리
at all — QRM is a UIC major, so it is absent from the university-wide 편람), or the UIC
guide (which lists ISSD-QRM only as a portal navigation path).

**What IS established:**
1. **QRM-department courses count.** QRM2001's 유의사항: "2026학번부터 **Major Elective**
   과목" (R40). By extension the other QRM2xxx/3xxx/4xxx courses.
2. **상경대학 (School of Economics) and 응용통계학과 courses CAN count as Major Credits** —
   this is the necessary implication of the table's own note 3, repeated on every page:
   > "Of the QRM courses taken from the **School of Economics and Department of Applied
   > Statistics**, which are taught in Korean, only up to 4 courses (12 credits) can be
   > counted as **Major Credits**."
   A cap on Korean ones is meaningless unless such courses count at all. **⇒ ECO/STA
   courses are ME-eligible, with a ≤4-course/12-credit cap on the Korean-taught ones.**
3. **Exception (note 3, CC block):** since Fall 2024 only **QRM-department** Math Stat 1 /
   Regression Analysis count — the 응용통계학과 versions do NOT (R18).

**❓ STILL UNRESOLVED — the practical question for Iden's shortlist:**
- Does **ECO1101** (경제수학1, English) count as ME *in addition to* filling its MR slot?
  (It fills MR, so this is moot for it.)
- Do **ECO1103/ECO1104** (원론) and **STA1002** (미분적분학, 상경대학-offered) count as ME?
  They are School-of-Economics courses, so note 3 implies **yes** — but no positive list
  confirms it. STA1002 is **Korean**, so if it counts it would consume 1 of the 4 Korean
  slots.
- Is there a **level floor** (e.g. 2000+) for ME? Unverified; ECO1101/1103/1104/STA1002
  are all 1000-level.
**Impact on the model:** ECO1103/1104/STA1002 currently carry Iden's +5 "Econ 2nd-major"
bonus only. If they also count as QRM ME, they are worth more than that. **Not changed —
requires confirmation from 학사지원팀 or the QRM department.** VERIFY item 22 upgraded.

---

## R94. ⚠️ THE SCRAPER LOST THE REAL 과목종별 (전필/전선) — the field that answers R93
**Spotted by Iden** from a portal screenshot: the course list has a column showing
**전선 / 전필** (전공선택 / 전공필수). Example rows: `STA3143-01-00 … 3,4 · 전선`,
`STA3109-01-00 수리통계학(2) … 3 · 전필`.

**Cause — a mislabelled column in `fetch_2026_fall.py`:**
```
base_cols  = [..., "hy", "subjtClNm",      "lessnSessnDivNm", ...]
base_col_names = [..., "학년", "과목종별",  "수업방식",        ...]
```
`과목종별` is populated from **`subjtClNm`**, whose values are 대면강의 / 블랜디드(동영상) /
비대면(동영상) — i.e. **delivery mode**, not course category. (Useful, and R50/R52 depend
on it — but under the wrong name.) `수업방식` ← `lessnSessnDivNm` = "학기" for all 1,690
rows, carrying no information at all.
**The portal's real 과목종별 is a different API field that was never requested.**

**Not recoverable locally:** no raw API response survives on disk — every JSON is
post-processed. Re-fetching needs a fresh JSESSIONID (portal blocks the sandbox, proxy
403), so **only Iden can obtain it**.

### Why this field is the highest-value missing data
It gives, per section, whether a course is 전공필수/전공선택 **for its offering
department** — which is exactly the input R93 needs. Combined with the QRM table's note 3
(상경대학·응용통계 courses can count as Major Credits, ≤4 Korean), it would let ME
membership be **derived** rather than guessed for ECO1103/ECO1104/STA1002 and every other
candidate.
⚠️ Caveat: 과목종별 is relational — STA3143 is 전선 *for 응용통계학과 students*. It does not
by itself prove the course counts as **QRM** ME; it establishes that the course is a
major-level course rather than 교양/일선, which is the necessary first condition.

**Fix — `refetch_full.py` (written 2026-08-06).** Iden did not write the original script
and has no way to know the API's internal field name, so the fix must not require it.
The new script:
1. re-runs the same 37 queries (imported from `fetch_2026_fall.py`, so the split logic
   and 학년 de-capping behaviour are unchanged),
2. saves **`raw_2026F.json` — every field, untouched**, so no column can ever be lost
   again by hand-picking,
3. writes **`field_report.txt`** listing every field name with sample values, and
   **auto-detects** the real 과목종별 by scanning for the *values* 전필/전선/교양/일선 —
   identifying the field by its content rather than its name.
**Iden's only step: paste a fresh JSESSIONID at the top and run it.** (Portal blocks the
sandbox — proxy 403 — so the fetch itself can only run on Iden's machine.)
Worth grabbing in the same pass: 정원/여석 if present (VERIFY 20, previously closed as
unobtainable — the raw dump will show whether the field exists).

---

## R95. ✅✅ **`subsrtDivNm` FOUND — the catalogue labels every course CC / MR / ME / UICE**
`refetch_full.py` ran successfully (2026-08-06): **1,500 distinct sections, 61 fields**
saved to `raw_2026F.json`. The auto-detector found the real 과목종별:

**Field name: `subsrtDivNm`.** Values (all 1,500):
| value | n | meaning |
|---|---|---|
| 대교 | 579 | 대학교양 |
| 전선 / 전필 / 전기 | 199 / 59 / 60 | non-UIC 전공선택 / 전공필수 / 전공기초 |
| **ME** | **185** | **Major Elective — UIC** |
| **CC** | **136** | **Common Curriculum — UIC** |
| 교기 | 104 | 교양기초 |
| RC | 69 | RC교육 |
| **MR** | **30** | **Major Required — UIC** |
| **UICE** | **26** | UIC Elective |
| MB | 20 | **Major Basic** (see below) |
| 자율 · 일반 · 교직 | 20 · 12 · 1 | |

**UIC tags courses with the very same abbreviations the QRM graduation table uses.**
This settles R93 by *derivation* instead of inference.

### Iden's candidates, definitively classified
| Course | subsrtDivNm | Note |
|---|---|---|
| QRM1001 | **MR** | ✅ confirms the MR slot |
| QRM2001/2002/2004/2102/3001/3007/4807/4808/4809 | **ME** | ✅ all nine are ME |
| **ECO1101 경제수학1** | **MB** | ⚠️ **Major *Basic*, not MR and not ME** |
| **ECO1103 미시경제원론** | **MB** | ⚠️ same |
| **ECO1104 거시경제원론** | **MB** | ⚠️ same |
| **STA1002 미분적분학** | **전기** | 상경대학 전공기초 — not a UIC category at all |
| UIC2151 · UIC1561 · UIC1551 · UIC1805 · UIC1751 | **CC** | ✅ confirms every CC pool |
| MAT1001 / MAT1002 | 대교 | 대학교양 — consistent with R92 |
| YCA1006 채플 | 교기 | |

### ⚠️ This CONTRADICTS an assumption in the current model
The QRM requirement table has only **MR / ME** rows — **no "MB" row**. Yet ECO1101 is
tagged **MB**, not MR. Two readings:
1. **MB = the catalogue's label for the UIC-Economics "Major Basic" tier**, and QRM's
   table maps 경제수학1 into its MR list by *name* regardless of the tag; or
2. ECO1101 does **not** discharge the QRM MR slot at all, and R63's identification of it
   as "Mathematics for Economics 1" was wrong.
Reading 1 is more likely — the QRM table names the course explicitly — but this is
**exactly the kind of assumption that has already burned this project twice (R63, R80)**.
**ECO1101's +10 bonus rests on it.** Must be confirmed before Aug 25.

📌 **No 정원/여석 field exists** in any of the 61 — capacity really is unobtainable from
this endpoint (VERIFY 20 stays closed, now on positive evidence rather than assumption).
📌 1,500 distinct sections here vs the xlsx's 1,690 *rows* — consistent with R51's finding
that the xlsx contains 112+ duplicate rows.

---

## R96. ✅✅ **STA2102 선형대수 IS a QRM ME COURSE — AT 국제, AND IT WAS NEVER IN THE POOL**
From `raw_2026F.json`: the ME courses listed under **개설전공 = 언더우드국제대학 융합사회과학부-
계량위험관리** (QRM's own department) number **11 at 국제** — the 9 known QRM courses **plus**:
| Section | Campus | subsrtDivNm | 개설전공 | Time |
|---|---|---|---|---|
| **STA2102-04-00 선형대수** | 국제 | **ME** | **QRM department** | 화4/목5,6 |
| **STA2102-05-00 선형대수** | 국제 | **ME** | **QRM department** | 월5,6/수6 |
(3 more STA2102 ME sections exist at 신촌.)
STA2102 is cross-listed *by QRM itself*, so it is unambiguously ME — no inference needed.
⚠️ **It has been missing from the ME pool this whole time**, because the pool was built as
"course code starts with QRM". 선형대수 is also plainly relevant to a QRM major.
⚠️ Its 언어 is **None (Korean)** → if taken, it consumes 1 of the 4 Korean 상경/응용통계
major-credit slots (R18 note 3). English-only does not apply (ME is not CC, R92).

---

## R97. ⚠️ **THE SAME COURSE CODE IS TAGGED DIFFERENTLY BY SECTION** — MB vs 전기
The raw data shows ECO courses offered **twice over**, by two different departments, with
different `subsrtDivNm`:
| Course | UIC 경제학 sections | 상경대학 경제학전공 sections |
|---|---|---|
| ECO1101 경제수학1 | -04 신촌, **-05·-06 국제** → **MB**, 언어 10 | -01·-02·-03 신촌 → **전필**, Korean |
| ECO1103 미시경제원론 | -01·-04·-06 신촌, **-02 국제** → **MB**, 언어 10 | -03·-05 신촌, **-07 국제** → **전기**, Korean |
| ECO1104 거시경제원론 | -02·-03·-04 신촌, **-06 국제** → **MB**, 언어 10 | -01·-05 신촌, **-07 국제** → **전기**, Korean |

**Consequences:**
1. **Category is a property of the SECTION, not the course code.** Every pool built on
   code prefixes (R84's rule) is blind to this. The correct key is (학정번호-분반).
2. Iden's current #1 timetable uses **ECO1104-07** — the **상경대학 / 전기 / Korean**
   section — not the UIC/MB/English one. Whatever ECO1104 is worth to Iden, the two
   sections are **not interchangeable**.
3. **MB = "Major Basic"**, a UIC tier of only 20 courses university-wide: ECO1101, ECO1103,
   ECO1104, ECO2101 거시경제학, ECO2102 미시경제학, plus 3 nano-science courses.
   Note ECO2101/2102 — the two QRM **MR** courses — are also tagged **MB**, which supports
   reading 1 of R95: the QRM table maps MB-tier Economics courses into its MR list by name.
   That makes ECO1101 = MR far more plausible, though still not documented.

**Model impact — DONE, not Iden's call.** Iden pushed back on being handed these as
"decisions"; correctly. None of the three were value judgements — one was a catalogue
fact, one was already handled by the ranking, one was a bug. **The no-assumptions rule
covers preferences, not facts or correctness.** All three implemented 2026-08-06:

---

## R98. ✅ REBUILD ON THE API DATA — `build_canonical.py` v2
Source switched from `강의목록_2026F.xlsx` (18 hand-picked columns, duplicate rows) to
**`raw_2026F.json` (61 fields, straight from the portal)**. Records are now keyed by
**section id (학정번호-분반)**, never by course code (R97).
- 국제 sections with a time: **712** (was 709 from the xlsx). The 3 extra: UIC1901-01
  (World Philosophy — already completed), UIC3668-01, UIC3669-01 (UIC Seminars).
  **The API is a strict superset — no section was lost.**
- Every record now carries `cat` = **subsrtDivNm**, `grade` (절대/상대평가), the real
  language code, and the full 유의사항.
- Category distribution at 국제: 대교 287 · **ME 93** · 교기 89 · **CC 81** · RC 69 ·
  **MR 26** · UICE 24 · 전선 15 · 전기 12 · **MB 7** · 전필 5 · 자율 4.
- Validation: section ids unique ✓ · 4 segment-count mismatches · 5 sections with no time.

### Pools now derived from the catalogue's own category
| Pool | Definition | n (국제) |
|---|---|---|
| CC (WestCiv/LHP/SciRD/Lang) | `cat == 'CC'`, all 81 in 공통교과과정(국제) | as before |
| Chapel | 교기 + 유의사항 "UIC, 영어채플" | 2 |
| **QRM ME** | **`cat == 'ME'` AND dept contains 계량위험관리** | **11** |
The ME definition is what finally pulls in **STA2102 선형대수** (2 국제 sections) alongside
the 9 QRM courses — QRM cross-lists it, so it needs no inference.
⚠️ The other 82 국제 ME sections are ME *for their own departments* (nano, design, …), not
for QRM. Whether 상경대학/응용통계 courses also count (note 3) stays unverified — VERIFY 22.

### Both ECO variants are in the pool; the ranking picks
No choice was needed: ECO1103-02 (UIC/MB/English/월1,2,수2) and ECO1103-07
(상경/전기/Korean/월1,2,수2) both compete, as do the two ECO1104 sections. They differ in
time, language and category, and the scorer already prices all three.

**Result:** top score unchanged at 50.21; STA2102 first appears at **rank 110** and in 156
of the top 5,000. It does not crack the top 50 — it is Korean (no CC English penalty
applies, but it wins no bonus) and 학년 2 (−10). It is now *visible* rather than absent.

---

## R99. ✅✅ **전기 = MB** — Iden's observation; the two label systems are ONE, and this
## closes the ME question (R93 / VERIFY 22)
Iden: *"전기 IS MB, so your questions self-answer."* Verified across all 1,500 sections.

**The catalogue uses two label alphabets, split perfectly by who offers the course:**
| | UIC departments | non-UIC departments |
|---|---|---|
| labels used | CC 136 · ME 185 · MR 30 · **MB 20** · UICE 26 | 대교 579 · 전선 195 · **전기 60** · 전필 59 · 교기 104 |
| cross-over | RC (7 UIC / 62 non-UIC) — the only shared label | |

**Courses offered by BOTH a UIC and a non-UIC department carry both labels — that is the
Rosetta stone:**
| Course | UIC label | non-UIC label |
|---|---|---|
| ECO3101·3104·3106·3110·3130·3134·4110 | **ME** | **전선** |
| ECO1103 미시경제원론 · ECO1104 거시경제원론 | **MB** | **전기** |
| **ECO1101 경제수학1 · ECO2101 거시경제학 · ECO2102 미시경제학** | **MB** | **전필** |
| BIO1002 · CHE1002 · MAT1002 · PHY1002 · STA1001 · ECO1001 | **UICE** | **대교** |
⇒ **ME = 전선 · MB = 전기(or 전필) · UICE = 대교.** Iden's equivalence holds.

### What this settles — three open questions at once
1. **ECO1101 = QRM MR: now strongly supported.** The MB courses that 상경대학 calls **전필**
   are exactly **ECO1101, ECO2101, ECO2102** — precisely the three Economics courses QRM's
   requirement table lists as MR. The 원론 pair (ECO1103/1104), which QRM does *not* list,
   are the ones 상경 calls **전기**. The split lines up perfectly. **R95's worry is
   resolved; the +10 bonus stands.**
2. **ECO1103 / ECO1104 / STA1002 are NOT QRM ME.** They are MB/전기 — 전공기초, a different
   tier from ME/전선. So they earn **no** QRM major-elective credit, and Iden's **+5
   "Econ 이중전공 필수 only"** was exactly the right valuation. No change needed.
3. **QRM ME = ME/전선 sections**, of which QRM's own department offers **11 at 국제**
   (9 QRM + STA2102 선형대수). The table's note-3 allowance for 상경대학/응용통계 courses
   would cover their **전선** offerings — nearly all at 신촌, so out of scope this term.

**VERIFY 22 → CLOSED by derivation.** No email required.
⚠️ Remaining nuance: whether a 전기/MB course can be counted as *free elective* credit
toward the 126 total — almost certainly yes (all credit counts), which is how ECO1103/1104
already function in the model.

---

## R100. ✅ THE COMPLETE CATEGORY MAP — confirmed by Iden, plus **UICE identified**
Iden confirmed: **MR = 전필 · ME = 전선 · MB = 전기 · CC is UIC-exclusive.** UICE was the
one label neither of us knew; resolved below from the data.

| UIC label | non-UIC equivalent | meaning |
|---|---|---|
| **MR** | 전필 | 전공필수 — Major Required |
| **ME** | 전선 | 전공선택 — Major Elective |
| **MB** | 전기 | 전공기초 — Major Basic |
| **CC** | *(none)* | Common Curriculum — **UIC-exclusive**, all 136 in 공통교과과정 |
| **UICE** | 대교 | see below |
| RC | RC | the only label used by both (7 UIC / 62 non-UIC) |

### UICE = a UIC-run section of a 대학교양 course
All 26 UICE sections sit in **공통교과과정**, and every UICE course code **also exists as
대교** elsewhere: BIO1002 · CHE1002 · MAT1002 · PHY1002 · STA1001 · ECO1001 (plus ASP2010,
POL1002 which are UICE-only). Every one carries a UIC-restricted 유의사항 —
**"UIC LSBT & ISED only"** for the lab sciences, **"UIC students only"** for
STA1001/ECO1001/POL1002.
⇒ **UICE = the UIC-taught (English, UIC-restricted) edition of a 대학교양 course.**

**Decisive corroboration — the QRM requirement table has a UICE row of its own:**
> `UICE | Introduction to Statistics | 3`
listed *outside* the CC subtotal (CC = 36+3 language; UICE = 3 separately).
And Iden's completed 통계학입문 was **STA1001-11-00**, a **UICE** section (R92). So UICE is
a real requirement category in Iden's own degree — **already satisfied**.

### This explains R92 from the other side
The English science sections are exactly the **UICE** ones, and they are LSBT/ISED-locked.
A HASS student therefore cannot reach an English lab science at all — which is why the
SciLit path collapses to RDQM + UIC1751. The category structure and the eligibility notes
tell the same story independently.

**No model change required** — UICE courses are already excluded for Iden (LSBT/ISED
filter), and the one UICE requirement she has is complete.

---

## R49. ⚠️ PARSER BUG FOUND & FIXED (2026-08-04): "/(...)" time blocks were dropped
`all_kj.json` (from fetch_2026_fall.py parsing) LOST parenthesized day-blocks of the
form "화5,6/(목5,6)" — the (목5,6) block was absent from `b`. Inline forms like
"수3(수4)" HAD been parsed. **101 of 661 sections were affected (176 block-cells
recovered)**, concentrated in MAT/PHY/CHE/BIO lab sections (= the SciLit pool).
Caught by the assistant when an impossible row ranked #1 (CHE1002-08 "화5,6/(목5,6)"
appeared compatible with QRM1001 목4,5,6).

- Corrected dataset: **`all_kj_fixed.json`** (661 sections re-parsed from the xlsx
  강의시간 column with a char-scan parser). Original kept untouched.
- Corrected stats: **171** patterns (was 169), conflict rate **12.55%** (was 11.05%).
- **ALL pre-fix counts are superseded**, incl. R43's table and both composition CSVs
  (they overcount by admitting phantom-compatible lab sections). Corrected operative
  counts: full-coverage(CN/JP Lang) **2,662** (was 3,966) · lang-deferred **16,100**
  (was 22,000). Composition tables not yet recomputed — rerun on demand.
- ⚠️ **Interpretation assumption (conservative, UNVERIFIED):** parenthesized periods
  are treated as REAL occupied time. If "(월7,8)/수7,8" actually means alternating/
  subgroup lab weeks, some excluded combinations are actually valid (never the
  reverse — no invalid row survives). Verify the convention in one lab-course
  syllabus (수업계획서) before finalizing a timetable containing one.

---

## R86. ✅ COMPLETE Science Literacy course list (13 courses, with codes)
Source: **UIC website → MAJORS AND CURRICULUM → Common Curriculum → Courses**
https://uic.yonsei.ac.kr/main/major.php?mid=m02_05_08
> "Course offerings that serve the science literacy requirement include:"

| Code | Course | Cr |
|---|---|---|
| UIC1541 | HISTORY OF SCIENCE & TECHNOLOGY | 3 |
| UIC1918 | INTRODUCTION TO THE SCIENCE OF THE MIND | 3 |
| UIC1502 | SOCIAL COGNITION | 3 |
| UIC1920 | SCIENCE IN CONTEXT | 3 |
| UIC1751 | SCIENCE IN SOCIETY | 3 |
| MAT1001 | CALCULUS AND VECTOR ANALYSIS(1) | 3 |
| PHY1001 | GENERAL PHYSICS AND LABORATORY(1) | 3 |
| CHE1001 | GENERAL CHEMISTRY AND EXPERIMENTS(1) | 3 |
| BIO1001 | GENERAL BIOLOGY AND LABORATORY(1) | 3 |
| MAT1002 | CALCULUS AND VECTOR ANALYSIS(2) | 3 |
| PHY1002 | GENERAL PHYSICS AND LABORATORY(2) | 3 |
| CHE1002 | GENERAL CHEMISTRY AND EXPERIMENTS(2) | 3 |
| BIO1002 | GENERAL BIOLOGY AND LABORATORY(2) | 3 |

**This is the authoritative list — match by CODE, never by course name.**

### ❌ Correction: earlier name-matched list was OVER-INCLUSIVE
A previous search matched on English titles and wrongly included:
**BIO1009, CHE1011, CHE1012, MAT1017, PHY1012, STA1002, FNS1001** — none of these codes
appear on the official list. Notably **STA1002 "CALCULUS" ≠ MAT1001/1002 "CALCULUS AND
VECTOR ANALYSIS"** despite similar titles. (Same failure mode as R1/R25: reading a label
instead of the identifier.)

### Fall 2026 국제 availability (matched by code) — 42 sections total
| Code | 국제 | Notes |
|---|---|---|
| UIC1751 SCIENCE IN SOCIETY | 1 | 수3,금3,4 |
| MAT1001 CALC & VECTOR(1) | 1 | 화5(화6)/목5,6 — blended |
| CHE1001 GEN CHEM(1) | 1 | (화3,4)/목3,4 |
| MAT1002 CALC & VECTOR(2) | 7 | several blended (동영상콘텐츠) |
| PHY1002 GEN PHYSICS(2) | 12 | lab pairs |
| CHE1002 GEN CHEM(2) | 14 | lab pairs |
| BIO1002 GEN BIO(2) | 6 | lab pairs |
| UIC1541, UIC1918, UIC1502, UIC1920, PHY1001, BIO1001 | 0 | not offered Fall 2026 |

⚠️ Science/lab courses use paired blocks — parentheses `(화3,4)` denote the 실습/lab session.
Both parts occupy time. Verify block parsing for these before enumerating.

### Relationship to RDQM
The **UIC website lists RDQM and Science Literacy as SEPARATE Common Curriculum components.**
The QRM requirement table (2026~) states the requirement as:
> "Science Literacy Course **or** Research Design and Quantitative Methods" — 3 cr

→ **One slot, two routes.** Either a course from the 13-item list above, OR RDQM (UIC2151).
(An earlier note described RDQM as being *inside* the Science Literacy set, based on the
Enrollment Guide's prose "The Science Literacy and Research Design courses include Research
Design and Quantitative Methods, ...". The website's structure is the clearer reading.)

### Guide constraints on this requirement
- **"will not be double-counted toward other requirements"** — whatever fills this slot
  cannot also satisfy something else.
- **UIC1541 History of Science & Technology counts as Science Literacy ONLY** — it does
  **not** satisfy World History Group I for 2014+ entrants.

---

## R87. "UIC LSBT & ISED only" on science courses ≠ HASS students barred from Science Literacy
**Iden's reading, supported by the guide.** Logged because it resolves an apparent blocker.

### Observation
MAT1002, PHY1002, CHE1002, BIO1002 each appear TWICE in the Fall 2026 catalogue:
| Bucket | 유의사항 |
|---|---|
| UIC 공통교과과정(국제) | **"UIC LSBT & ISED only"** |
| 대학교양 (논리와수리 / 자연과우주 / 생명과환경) | *(no restriction)* |

### Why this is NOT a barrier
Guide §11.x — who must take Science Literacy & Research Design:
| Division | SLC required? |
|---|---|
| UD Humanities & Social Sciences (CLC, ECON, IS, PSIR) | ✅ yes |
| ASD | ✅ yes |
| **HASS (Iden)** | ✅ **yes** |
| **UD LSBT** | ❌ no — "required to take either Critical Reasoning or RDQM" |
| **ISE** | ❌ no — "either Critical Reasoning or RDQM during 1st or 2nd year" |

**The two groups reserved on those sections (LSBT, ISED) are exactly the two groups with NO
Science Literacy requirement.** For them these are **major foundation courses**; UIC runs
dedicated sections for its own science-track students. The tag reserves the *major-track*
sections — it does not exclude HASS from the requirement.

**Supporting argument:** if HASS students could not use the 대학교양 sections, Fall 2026 would
offer them exactly **one** SLC option university-wide (UIC1751, 1 section). Implausible for a
requirement every HASS student must clear.

### Practical conclusion
Iden fulfils Science Literacy via **대학교양-bucket sections** of the listed course codes
(~42 국제 sections Fall 2026), **or** UIC1751 SCIENCE IN SOCIETY (UIC-run, "UIC students only").

⚠️ **Unconfirmed:** that a 대학교양-bucket section registers against the UIC CC Science Literacy
slot. Codes are identical, which argues yes. Worth confirming with 학사지원팀 / UIC office.
(Do not assert as fact — this project already erred once by reading a 개설전공 bucket as a
requirement spec.)

---

## R88. ❌ Over-correction withdrawn — variant science codes are plausible equivalents
An earlier note called BIO1009 / CHE1011 / CHE1012 / MAT1017 / PHY1012 "not on the list"
and labelled including them an error. **That was overconfident in the opposite direction.**

What they actually are:
| Code | Course | Relationship |
|---|---|---|
| MAT1017 | CALCULUS AND VECTOR ANALYSIS(2) **(HONOR CLASS)** | honors variant of MAT1002 |
| BIO1009 | GENERAL BIOLOGY AND LABORATORY(2) **(HONOR CLASS)** | honors variant of BIO1002 |
| CHE1011 / CHE1012 | GENERAL CHEMISTRY AND EXPERIMENT(1)/(2) | 공학계열 track (CHE1011 tagged 공학계열 9월 신입생) |
| PHY1012 | GENERAL PHYSICS AND EXPERIMENT(2) | parallel track to PHY1002 |
| CHE1001 | GENERAL CHEMISTRY AND EXPERIMENTS(1) | tagged 이학•생명시스템계열 9월 신입생 |

These are **parallel versions of the same subjects for different student populations**, not
unrelated courses. Both sources use **non-exhaustive** language:
- UIC website: "Course offerings that serve the science literacy requirement **include**:"
- Guide: "…and **other courses to be determined later**."

**Neither source states the list is closed.** Status of variant codes: **UNVERIFIED** —
neither confirmed nor excluded.

**Still distinguishable:** **STA1002 "CALCULUS"** is a 상경대학 (경제학전공/응용통계학전공) course,
a different college's offering with a different title from the MAT-series
"Calculus and Vector Analysis". Weakest candidate of the group.

**Method note:** match by course CODE, but do not treat a published "include" list as
exhaustive. Flag variants as unverified rather than ruling them in or out.

---

## R89. (DUPLICATE of R83 — kept for the division-confusion explanation) UIC Seminar window (Sem 4–7) & 1-per-semester DO NOT apply to Iden
**R15 and R23 applied the WRONG DIVISION's rule. Both are withdrawn for Iden.**

### The guide states different rules per division — verbatim

**UD (Underwood Division) — NOT Iden:**
> "UIC Seminar (6~12 credits) … **Underwood Division Humanities & Social Sciences students**
> will take **one UIC Seminar per semester** (3 credits each) **from the second semester of
> their sophomore year through the first semester of their senior year.** Students are
> required to take **4** UIC Seminars, but students are allowed to take electives instead of
> UIC seminars while studying abroad. If a student is away for one semester on exchange, the
> number … is reduced to 3. If away for two semesters, … a minimum of 2.
> Underwood Division LSBT students are required to take 2…"

**HASS (Iden's division) — COMPLETE text, nothing omitted:**
> "UIC Seminars (6 credits): **HASS students are required to take two UIC seminars.**
> Courses with course codes of UIC35(XX) and UIC36(XX) are UIC Seminars."

**ASD:** "…required to take two UIC seminars."  **ISE:** "…required to take two UIC Seminars."

### The division confusion that caused this
**UD ≠ HASS.** UD's internal sub-group "Humanities & Social Sciences" = CLC, ECON, IS, PSIR.
That is NOT the HASS *division*. **QRM is in the HASS division** (per UIC Degree Requirements
page, QRM listed under "Humanities, Arts, and Social Sciences Division").
The 4-seminar / one-per-semester / Sem-4–7 rules belong to UD HASS majors only.

### What actually applies to Iden
- **2 UIC Seminars, 6 credits.** ✅ (R22 was right)
- **NO semester window.** Seminars may be taken in ANY semester. ← R15 WITHDRAWN
- **NO stated one-per-semester cap.** ← R23 partially WITHDRAWN
- Course codes: `^UIC3[56]\d\d` (R4 stands)
- Senior Thesis (3cr, 8th semester, CGPA ≥3.7) **also counts as a UIC seminar** — an
  additional route not previously noted.

### R16 "conflict" — DISSOLVED, was never a conflict
R16 flagged guide (4 seminars) vs QRM table (2 seminars) as contradictory and marked it
"ACTION REQUIRED: confirm with advisor." **There was no contradiction** — the 4 came from
UD's paragraph. Guide and QRM table agree: HASS = 2 seminars. **No advisor query needed.**

### ⚠️ Unsourced claim to re-check with Iden
"Max 1 seminar per semester" was logged in R23 as user-confirmed. Iden's message
("seminars can not be two per semester… confirmed") may have been agreeing with the
assistant's framing rather than independent knowledge. **The guide states no per-semester
cap for HASS.** If Iden knows this from an advisor/portal/upperclassmen it stands; if it
originated from the assistant it is unsourced.
Seat limits ARE real (UIC3512 정원 16).

### Planning impact
Earlier four-year plans constrained seminars to Sems 4–7 and worried about Sem 5 (Songdo)
falling inside that window. **That constraint does not exist for Iden.** Seminar placement
is free across all remaining semesters, subject only to offering availability and seats.
This materially loosens the 신촌/국제 semester allocation problem.

---

## R101. ⚠️ Six MR *requirements*, SEVEN codes — a disjunction hid inside a count
`MR_CODES` was written with six elements to match "six MR requirements", and therefore
*looked* correct. But requirement 5 is **"MATHEMATICAL STATISTICS **or** REGRESSION
ANALYSIS"** — one slot, two codes (QRM3005 / QRM3004). QRM3004 was silently absent.

The sanity check that should have caught this (`len(MR_CODES) == 6`) is exactly what
concealed it. Neither code is offered at 국제 in Fall 2026, so **no ranking output could
ever have differed** — it would have surfaced only at Sem 3 planning.

We already held the fact: `REQUIREMENTS_AUDIT.md` line 40 records *"R74: QRM3004
REGRESSION ANALYSIS ran at 국제 in Spring 2026 (금1,2,3)"*. It was never carried into code.

**Rule: when encoding a requirement list as a code list, the two have different
cardinality wherever a requirement is disjunctive. Never validate one against the other's
count.** Distinct from R63/R80/R85, which were pool-*matching* errors.

## R102. 과목종별 is a property of (section × 개설전공), NOT of the section
Caught by Iden from a portal screenshot: **ECO1103-04-00** (김철삼, 화4목5,6, 상본B120)
appears under three 개설전공 — 경제학, 계량위험관리, 상경대학 경제학전공 — with a *different*
`subsrtDivNm` in each. Confirmed at scale: **78 of 1,499 sections carry conflicting
과목종별**. Cleanest example, NSE2003-01-00: **MR** for 나노과학공학, **MB** for 에너지환경융합,
**ME** for 바이오융합. One section, three labels. MB is **not** a superset of ME.

**The bug:** `refetch_full.py` deduped on `subjtnbCorsePrcts` first-seen-wins, and
`UIC - 경제학` runs before `UIC - 계량위험관리` in QUERIES. Every ECO1101/1103/1104 kept
경제학's label. ECO1101 read **MB** when QRM calls it **MR**.

**Fix:** `refetch_listings.py` (v4) keeps one record per (section, query) and never
collapses them → `raw_2026F_listings.json` (1,687 listings / 1,499 sections) and
`qrm_listings.json` (QRM's own label for its 40 sections). `canonical_2026F.json` now
carries **`qcat`** (QRM's view) beside `cat` (whichever query won); `rank2.py` reads
`qcat` first. 4 국제 sections were mislabelled: ECO1101-05/06 MB→MR, ECO1103-02 &
ECO1104-06 MB→ME.

**Rule: never read `cat` for requirement logic. `cat` is query-order noise. Use `qcat`.**

## R103. Double-major bonuses SCRAPPED (Iden 2026-08-06)
> "Only things that count for me should be scored. Scrap every single double major bonus
> for now. We'll work on that later."

Removed: `BONUS_ECON2ND` (+5 on ECO1101), `BONUS` +5 on ECO1103/ECO1104/STA1002, and
`ROLE_MB` (+4 → **0.0**). ROLE_MB only ever fired on **상경대학/경제학's** MB·전기 labels —
i.e. it was scoring a double major Iden has not chosen. STA1002 (미적분학) drops to **0**;
QRM does not list it at all (`qcat = None`).

Surviving bonuses: **ROLE_MR +8 · ROLE_ME +6 · language (UIC1805/1806) +8.** The language
bonus is a UIC requirement, unrelated to any second major, so it stays.

---

## R90. ✅ COMPLETE OFFICIAL ME (Major Elective) LIST — QRM Curriculum Chart
**Source:** HASS Division → Education → QRM → Curriculum
https://ghe.yonsei.ac.kr/uic_hass/Curriculum_Sub_QRM.do
This is the **authoritative MR/ME classification**. 42 major credits = 18 MR + 24 ME.

### MR (6 courses, 18 cr) — confirmed identical to R18
QRM1001 Intro to QRM · ECO2102 Micro · ECO2101 Macro · ECO1101 Math for Economics 1 ·
QRM3005 Mathematical Statistics **or** QRM3004 Regression Analysis · QRM3003 Principles of FinEng

### ME — official chart (26 entries), with Fall 2026 availability
| YR | CODE | COURSE | 국제 | 신촌 |
|---|---|---|---|---|
| 1 | ECO1103 | Principles of Microeconomics | 2 | 5 |
| 1 | ECO1104 | Principles of Macroeconomics | 2 | 5 |
| 2 | QRM2001 | Fundamental Economic Analysis | **1** | 0 |
| 2 | QRM2002 | Financial Data Analysis | **1** | 0 |
| 2 | QRM2004 | Statistical Analytic Methods | **1** | 0 |
| 2 | QRM2100 | Financial Planning and Wealth Management | – | – |
| 2 | QRM2101 | Multivariate Calculus | – | – |
| 2 | STA2102 | Linear Algebra | **2** | 3 |
| 2 | STA2104 | R and Python Programming | – | – |
| 2 | STA2105 | Statistical Method | 0 | 1 |
| 2 | *(no code)* | Quantitative Methods of Financial Engineering | – | – |
| 3 | QRM3001 | Theory of Financial Analysis | **1** | 0 |
| 3 | QRM3002 | Portfolio Theory and Application | – | – |
| 3 | STP3007 | Social Innovation Seminar | – | – |
| 3 | ECO3104 | Econometrics (1) | 0 | 2 |
| 3 | *(no code)* | Financial Risk Analysis | – | – |
| 3 | ECO3127 | Law and Economics | – | – |
| 3 | ECO3130 | International Finance | 0 | 3 |
| 3 | ECO3134 | Money and Banking | 0 | 3 |
| 4 | QRM4001 | Analytics for Social Innovation | – | – |
| 4 | QRM4807 | Methods of AI in Finance and Investment | **1** | 0 |
| 4 | STA4103 | Data Mining | – | – |
| 4 | ECO4115 | Corporate Finance and Economics | 0 | 1 |
| 4 | ECO4862 | Analysis of International Financial Market | – | – |
| 4 | ECO4865 | Real Estate Finance and Economics | – | – |
| 4 | *(no code)* | Acturial Mathematics | – | – |

3 entries have **no course code assigned** — planned, apparently never offered.

### ⚠️ CHART IS INCOMPLETE — 5 courses tagged 계량위험관리 in F26 are NOT on it
| CODE | COURSE | Campus | Time |
|---|---|---|---|
| ECO1105 | PYTHON PROGRAMMING | 신촌 | 화2,3,목1 |
| **QRM2102** | LINEAR ALGEBRA AND DIFFERENTIAL EQUATIONS | 국제 | 금5,6,7 |
| **QRM3007** | FINANCIAL MACHINE LEARNING | 국제 | 수10,11/금2 |
| **QRM4808** | FINANCIAL TIME SERIES ANALYSIS | 국제 | 수12,13/금4 |
| **QRM4809** | CORPORATE FINANCE STRATEGIES | 국제 | 수9,10/목3 |

Likely newer courses added after the chart was published (note QRM2102 "Linear Algebra and
Differential Equations" appears to supersede chart entry QRM2101 "Multivariate Calculus";
ECO1105 "Python Programming" vs chart's STA2104 "R and Python Programming").
**Operative test = 개설전공 tag "융합사회과학부-계량위험관리" in the live catalogue**, not the chart.
⚠️ Their MR/ME classification is **unconfirmed** — see R91 (data bug).

### Additional rules from the same page
- **"If a course is listed under multiple majors, the course will be counted towards
  fulfilling only ONE of the majors. Students should choose which major it counts towards."**
  ← **Critical for the double-major decision**: ECO courses shared between QRM and Economics
  cannot double-count.
- QRM students must take **STA1001 INTRODUCTION TO STATISTICS** from UIC electives, but it is
  **NOT counted toward QRM major credits** (it sits in CC — matches R17/R27).
- Only QRM-department Mathematical Statistics / Regression Analysis count as major credit.
- Korean-taught courses from School of Economics + Applied Statistics: **max 4 courses (12 cr)**.
- Double major: **39 cr** including Intro to Statistics, plus all six MR courses.
- Minor: 21 cr = 5 named MR + Intro to Statistics + 3 cr of ME.

### ME available at 국제 Fall 2026 — 8 confirmed + 4 unconfirmed
**On the official chart (ME confirmed):**
ECO1103 월1,2,수2 · ECO1104 화4,목5,6 / 화8,9-목7 · QRM2001 화1,목2,3 · QRM2002 금1,2,3 ·
QRM2004 화4,5,6 · STA2102 화4/목5,6 · 월5,6/수6 · QRM3001 수7,8/금7 · QRM4807 수5,6/금5
**Tagged 계량위험관리 but classification unconfirmed:**
QRM2102 금5,6,7 · QRM3007 수10,11/금2 · QRM4808 수12,13/금4 · QRM4809 수9,10/목3

---

## R91. ⚠️ DATA BUG — 과목종별 (MR/ME/CC tag) is NOT in 강의목록_2026F.xlsx
`fetch_2026_fall.py` maps `subjtClNm` → "과목종별", but that field returns **수업방식**
values (대면강의, 블랜디드(동영상), 비대면(동영상)…), not the MR/ME/CC classification.

The portal UI *does* show 과목종별 = **ME** for QRM2004 (observed in browser). The correct
JSON field name is **unknown** — the script never captured it.

**Consequence:** the xlsx cannot answer "is this course MR or ME?" — that had to be resolved
from the QRM Curriculum Chart (R90) instead.

**Fix:** re-run the fetch dumping ALL JSON keys for one row to identify the right field
(candidates: `subjtClsfNm`, `subjtDivNm`, `cptnDivNm`…), then re-export.
⚠️ Sandbox cannot reach the portal (proxy 403) — Iden must run it locally.
Until then, MR/ME status of the 5 off-chart courses (R90) stays unverified.

---

## R104. 중복인정 is about CREDITS, not requirements — the mechanism is 과목인정
Iden's reading (2026-08-06) was correct; my earlier requirements-reading was wrong.
The yfl page's *"counted towards fulfilling only one of the majors"* cannot mean the
requirement goes unfulfilled — that would make overlap-heavy double majors impossible.

**수강편람 p.32 (응용통계학과) states the mechanism outright:**
> "과목인정이란 과목인정 된 해당 교과목을 이수하지 않는 대신 응용통계학과의 전공선택 과목을
> 추가로 이수하는 것이다. 과목 인정을 받았을 경우 **학점 인정은 되지 않으므로 추가적으로 다른
> 교과를 이수하여야 한다.** 예를 들어 미분적분학을 과목인정 받은 경우, 이에 해당하는 3학점을
> 전공선택 과목으로 이수하여야만 한다."

→ **requirement ticked on both sides · credits counted once · shortfall made up with
extra electives.** You never retake a course. Corroborated: p.29 (마이크로전공 — "중복되는
학점 수만큼 … 추가 이수해야 함"), p.48 ("한쪽 전공으로만 인정"), p.50, p.61.

**Clincher, p.37:** 이과대학 has an *explicit exemption permitting* credit double-counting
among its 6 majors. An exemption only exists if the default forbids it.

**Consequence for the double-major decision:** overlap saves a *requirement*, never a
*credit*. HANDOFF §6 lists Economics as strongest partly because "Micro + Macro are BOTH
QRM MR courses" — that is NOT the saving it appears to be. Re-derive when choosing.

## R105. The Korean cap covers 상경대학-offered sections of QRM course codes
QRM PDF p.2 note 3 — wording is stronger than the yfl webpage's:
> "Of the **QRM courses** taken from the School of Economics and Department of Applied
> Statistics, **which are taught in Korean**, only up to 4 courses (12 credits) can be
> counted as Major Credits."

"QRM courses taken from 상경대학" presupposes such sections count → **requirement
satisfaction is by 학정번호, not by which 개설전공 lists the 분반.** Closes the
ECO1103-07 / ECO1104-07 ambiguity: they count, and consume Korean-cap slots.
**Exception (p.2 note 3):** 수리통계1 / 회귀분석 must be QRM's OWN section, since Fall 2024.

## R106. ⚠️ AI Concentration Major — never modelled
QRM PDF pp.6–7. 2023~ : 4 of 6 AI Core courses (12cr) + UIC3001 + **QRM4807** (6cr)
+ Major 42 = **60 cr**. Only **UIC 1st-major students** may apply (Iden qualifies).
Korean-taught AI Core courses DO count.
**⚠️ Note 6: "AI Concentration major requirements remain unchanged, even with a double
major. (1st Major – 42 credits)"** → AI Concentration **cancels the 42→36 double-major
reduction**. The two are substitutes, not complements.
QRM4807 runs at 국제 Fall 2026 (수5,6/금5) and is already in the OPEN pool.

## R107. UIC is EXEMPT from the 3000·4000단위 45학점 rule
수강편람 p.21 table: **"언더우드국제대학  적용 면제"**. Closes the open question at
RULES.md:1370. No upper-level credit floor applies to Iden.

## R108. The 30% 동영상 cap does NOT apply to Iden
수강편람 p.24 — the "단순 동영상 강의 ≤30% of 신청학점" rule is titled
**"외국인 학생 단순 동영상 강의 수강 제한 안내"** and applies to 외국인 유학생 only.
Iden is not one (HANDOFF). Checked because it would otherwise have invalidated most of
the top-50. **No constraint change.** Also: only **비대면(동영상)** counts as "단순 동영상";
블렌디드(동영상) and 비대면(실시간+동영상) are unrestricted.

## R109. UIC Seminars 6 cr ARE a graduation requirement (official doc wins)
QRM PDF p.2 lists **"UIC Seminars 6"** inside the CC block (subtotal 36+3).
`REQUIREMENTS_AUDIT.md` §D said "credit yes, requirement no" — **that is wrong**.
Iden 2026-08-06: *"trust the official document. It is safer."* → 6 cr of UIC Seminars is
outstanding and must be planned for. Seminar codes are UIC35xx / UIC36xx (R-existing).

## R110. ⚠️ The portal's keyword box OVERRIDES the 개설학과 filter (needs confirming)
Iden searched 개설학과=계량위험관리 + 통합검색 "ECO1103" and got **all 7** ECO1103 sections,
each showing 개설전공 = 상경대학 경제학전공 — *including ECO1103-02*, which our keyword-free
QRM query returns as 계량위험관리. Same section, different 개설전공 per query ⇒ the keyword
did not refine the filter, it replaced it.
Our keyword-free 계량위험관리 query returns 40 rows / 4 ECO1103 sections.
**Open test:** 개설학과=계량위험관리 with BOTH search boxes empty. 4 rows ⇒ filter is real
(our data correct). 7 rows ⇒ the portal really does list all sections under QRM.
Either way R105 settles the practical question by course code.


---

## R111. Credit cap = 22, but the target is 18 BY CHOICE (Iden 2026-08-06)
VERIFY 18 closed: Spring 2026 GPA **≥ 3.75** ⇒ HASS-freshman cap **19 + 3 = 22** (R86).
Asked whether Plan A should enumerate 6 courses (18cr) or 7 (21cr), Iden chose **6**.

**So the 2-open-slot structure is now a DECISION, not a constraint artifact.** 21 credits
is legal and was declined. The 7-course branch is deliberately out of scope — do not
re-raise it as an oversight, and do not silently widen the search to 3 open slots.
No credit constraint binds at 18/22, so the cap never enters the scoring.

## R112. Science "(2)" courses are unfulfillable SEQUELS — and carried no 유의사항
`PHY1002-06-00` (GENERAL PHYSICS AND LABORATORY**(2)**, 화5,6/목5,6) sat in the **SciRD
fixed slot** pool. It is a part-(2) course; Iden has never taken PHY1001. Unlike the
LSBT/ISED sections it carries an **empty 유의사항**, so the R61 eligibility filter passed it.

Fixed with an explicit prerequisite map, gated on `DONE`:
`MAT1002→MAT1001 · PHY1002→PHY1001 · CHE1002→CHE1001 · BIO1002→BIO1001`

**Impact on output: zero** — PHY1002 never appeared in any ranked timetable (dominated on
schedule). Logged because the *class* of bug is the R49 class: a structurally invalid row
sitting in a pool, invisible until something promotes it.

## R113. VERIFY 9 + 16 CLOSED — the SciLit path is dead; SciRD ≡ RDQM
Full audit of all **55** 국제 sections of SciLit + RDQM codes:

| | |
|---|---|
| RDQM (UIC2151) | **13 sections**, all English, all "UIC students only" → all eligible |
| SciLit, English but **LSBT & ISED only** | blocked (Iden is HASS) |
| SciLit, Korean | cannot fill a CC slot (R92) |
| SciLit, 학과-restricted (화학과/약학과 전용 등) | blocked |
| SciLit sequels with no note | **excluded by R112** |
| **SciLit actually usable** | **UIC1751-01 SCIENCE IN SOCIETY** (수3,금3,4) — the only one |

→ SciRD pool = **13 RDQM + UIC1751 = 14**. And in the ranking the slot is **100% UIC2151
across the entire top-50** — UIC1751 never surfaces.

**So the SciRD slot is effectively RDQM, by dominance rather than by rule.** VERIFY 16
("SciLit is 93% sequels — reconsider vs RDQM") is answered: there is nothing to reconsider.


## R114. VERIFY 11 CLOSED — weights verified, and de-duplicated to one source
**The fit was never the problem.** All 16 assertions pass: the live constants reproduce
every statement Iden actually made, including the fitted ones —
LATE(9)=−1 · LATE(13)=−10 · LATE(14)=−12.98 · MARATHON(4)=−8 · HOLE(4)=−10 ·
월/금 = 75% · 고립/붙은 = 25% · MR−ME = 2 · MR+YEAR_PEN(2) = −2.

**The problem was drift.** Weights lived in THREE places with nothing keeping them in step:
`rank.py` (executed) · `render2.py`'s W table (shown in the HTML) · `ranking_weights.md`
(documentation). The last was **three refits out of date** — still claiming Friday +25,
lunch −2, marathon −2, i.e. values discarded after the convex-marathon and late-ending
refits. Anyone reading it to check for bias would have audited the wrong model.

**Fix — rank.py is now the single source of truth:**
- `test_weights.py` — 16 assertions, each labelled with Iden's *actual wording*. Run after
  any weight edit. A failure means either the edit was wrong or Iden changed his mind; if
  the latter, update the claim string so wording and constant stay tied together.
- `gen_weights.py` — regenerates `ranking_weights.md` from the live constants.
  **Never hand-edit that file again.**

**Also created `PLANS.md`** — deferred work (Plan B tactics · multi-semester layer ·
VERIFY 13 values · parked questions · what is deliberately out of scope), so that
"not yet" cannot quietly become "never".


## R115. VERIFY 5 CLOSED — slash alignment verified three ways
The parser pairs the *n*-th 강의시간 segment with the *n*-th 강의실 segment. That pairing
decides whether an hour costs **time only** or **time + presence**, and presence drives the
free-day bonus (+18.75 ~ +25) — the largest single term in the score. A mispairing could
invent a free day that does not exist.

| Test | Result |
|---|---|
| Segment counts equal, all 국제 sections | **712 / 712** — zero mismatches |
| Parenthesis pattern mirrors position-for-position | **128 / 128** |
| Segment claiming both a room *and* 동영상/실시간 | **0** |

**The paren test is the real evidence.** The catalogue brackets optional/alternate hours in
*both* strings at the same position — `화5(화6)` ↔ `I자A402(I자A402)`,
`월1,2/(수1)수2` ↔ `동영상콘텐츠/(I진A218)I진A218`. This is an independent signal the parser
never reads, so agreement is not circular. `STA1001-04-02` is the sharpest case:
`월5/(월6)/수5,6` ↔ `I진A218/(I진A217)/동영상콘텐츠` — three segments, and the bracketed hour
has a *different room* (A217 vs A218), which only lines up under correct pairing.

Scope note: only **111 of 712** 국제 sections have multiple segments of *mixed* kind, so
alignment can change the answer for those alone; 523 are single-segment and 78 are uniform.

**My first version of this check reported 27 failures — the checker was wrong, not the data.**
`동영상(중복수강불가)` carries parentheses as part of its *label*, which the mask counted as
the positional convention. Same failure as the earlier render-verification incident: when a
check disagrees with the data, suspect the check first.

## R116. ⚠️ `minMlg` is NOT the cutoff — it is the lowest bid among ALL applicants
Caught by Iden from a rank-list screenshot. `findMlgAppcsResltList.do` returns per-section
summary stats, and I read **`minMlg` as "lowest winning bid"**. It is not.

**Ground truth, UIC1561-01 2026-1:** 정원 **30**, `cnt` **38** applicants, `minMlg` **1**,
`avgMlg` 6.58. Iden's screenshot shows rank 30 admitted at mileage **3** and rank 31
rejected at **3** — so the real cutoff is 3, while `minMlg` reports 1 (a bid from one of
the 8 who missed). `minMlg` is nearly always 1 and carries almost no signal.

**Everything I built on it was wrong, in the most misleading direction:** it ranked
과학|RDQM as the *hardest* requirement (−31) when 배율 shows it **0.38× — the easiest thing
on the board**, barely a third full.

**Corrected fields:**
| field | meaning |
|---|---|
| `atnlcPercpCnt` | 정원 (capacity) |
| `cnt` | **신청인원 (applicants)** — the field I overlooked |
| `avgMlg` | average bid across applicants — best available difficulty proxy |
| `minMlg` | lowest bid by anyone. **Do not use.** |
| `sy1..sy6PercpCnt` | per-학년 quotas |
| `mjrprPercpCnt` | 전공자 정원 |

⚠️ True cutoffs live only in the **rank list** (Iden's screenshot), not in this summary.
We hold exactly one measured cutoff (UIC1561 = 3). Everything else uses `avgMlg` as proxy.

Also: **`초수강여부` = first-time taker, NOT a retake** — a tie-break criterion
(수강편람 "⑥ 초수강(재수강 아님) 우선"), not an admission outcome. `수강여부` is the outcome.
Visible in the screenshot: ranks 30 and 31 both bid 3; rank 30 was 초수강 Y and got in.

## R117. Deferral costs — FINAL, fitted to Iden's anchors on measured competition
Mechanism: `cost = 0.658 × (worst avg bid) + 6.44 if 학년=1-only + 5 if gateway`.
Anchors given by Iden: **WCiv −12 · LHP −13 · QRM1001 = 12+5**. All three reproduce.

| requirement | worst avg bid | 배율 | cost | defer gain | net |
|---|---|---|---|---|---|
| QRM입문 (MR) | 9.51 | 0.98× | **−17.7** | +12.45 | −5.25 stays |
| 언어 | 16.00 | 1.17× | −17.0 | — | open slot |
| 과학\|RDQM | 13.00 | 0.38× | −15.0 | +12.45 | −2.54 stays |
| 역사/문학 | 19.75 | 1.68× | **−13.0** | +12.45 | **−0.55** stays, marginal |
| 서양문명 | 8.45 | 1.33× | **−12.0** | +7.12 | −4.88 stays |
| 전선 (ME) | 12.81 | 1.35× | −8.4 | — | open slot |
| 채플 | 6.40 | 0.01× | −4.2 | — | |

Written to `defer_costs.json`. Nothing is deferred at these values, but LHP is within 0.55
of flipping — the machinery surfaces near-ties rather than changing decisions.

**Fork resolved by Iden:** within a requirement, use the *worst* alternative, not the
easiest. ASP2022/ASP2033 clear at low bids because they don't fill — *"those are unpopular
for a reason"*. Low cutoff is evidence of both easy access and low desirability, and the
mileage data cannot separate them. Some of what deferral cost currently absorbs belongs in
the professor/quality layer (PLANS.md §C) when that is built.

## R118. 정원 IS obtainable — VERIFY 20 and item 7 were closed wrongly
Both were closed "⛔ UNOBTAINABLE — 정원/여석 not in the API or xlsx". They are in
`findMlgAppcsResltList.do`: `atnlcPercpCnt` (정원), `cnt` (신청인원), `mjrprPercpCnt`
(전공자 정원) and `sy1..sy6PercpCnt` (**per-학년 quotas**) — for past semesters.
Per-학년 quotas matter for Plan B: they bound how many seats a 1학년 can actually reach on
8/25, which is not the same as how many exist. `mileage_history.json` holds 142 rows.

## R119. Language +8 and −17 are ONE logic, not two — do not add them
Iden asked "why not both? They are separate logics right?" Checked against the record:
the **+8 was elicited inside a family of *requirement* bonuses** (ECO1101 +10 = QRM 전필 +
Econ 필수; 원론/STA1002 +5 = Econ 필수), and was set by ranking it against another
requirement bonus — *"ECO1101 slightly higher than Chinese"*. The −17 is the same quantity
measured from competition data.

Tested for a genuine second axis: is there a **Chinese-specific** bonus that would survive
if the language requirement vanished? **Iden 2026-08-06: "it's not a chinese-specific
bonus. I recall the bonus was from just being a requirement."**

→ **−17 alone. The +8 stays deleted.** `rank3.py` was already correct; no change.
(Chapel is different — Iden has said it is *"desirable in itself"*, so an intrinsic term
there would be separate and additive. Still unset: PLANS.md §C.)

## R120. 대학요람 confirms the QRM curriculum — and still omits the same four courses
`[붙임 2] 2026학년도 대학요람(대학별 교과과정)` pp.246–247 (published 2026-04-28) lists QRM's
curriculum **identically to the yfl webpage**, including the same footnote restricting
수리통계/회귀분석 to QRM's own sections. It confirms **QRM3004 REGRESSION ANALYSIS = MR**,
validating R101's seventh code.

⚠️ **It also omits QRM2102 · QRM3007 · QRM4808 · QRM4809** — the four we admitted under R105
because the registrar tags them ME under 개설전공 = 계량위험관리. So **two official curriculum
documents omit them; one operational source includes them.** My earlier "the webpage is
stale" reading (R105 note) is weakened: the 요람 is not stale, and agrees with the webpage.

**✅ RESOLVED (Iden 2026-08-06): they are NEW COURSES.** Iden looked them up; 2026-04-28 is
the 요람's *publication* date and predates their approval. The evidence fits exactly — of
the 11 QRM-coded courses offered Fall 2026, precisely those 4 are absent from the 요람, and
all 4 are new. The 요람 is not contradicting the registrar, it is simply older.
→ **R105 stands. Keep all four as QRM ME.** No email needed.

Supporting count: **QRM offers 11 courses / 11 sections in Fall 2026, one section each.**
xlsx and API agree exactly. Six curriculum courses are absent this term (QRM2100, QRM2101,
QRM3002, QRM3003, QRM3004, QRM4001) and QRM3005 is 신촌-only. Sole large sections that do
not fill is why every QRM course shows 정원 40–80 with a mileage cutoff of 1.
Also confirmed at 대학요람 p.51: **STA1002 미분적분학 = 전기 for 경제학부**, and STA2105 = 전기.

## R121. MAX_DEFER = 1 is PROVEN sufficient, not a compute compromise
rank3 could in principle defer any subset of the 5 available requirements. Searching
2-deferral space directly was too slow (3 elective slots -> triples over 197 signatures).
Resolved by proof rather than by capping.

**Method** (`defer2_check.py`): run each pair in isolation with the 1-deferral optimum
**32.51** preloaded as the incumbent, so branch-and-bound prunes from the first node, and
with SCHED_UB tightened from 70 to the true ceiling **63.1** — the largest reachable
week_value is 월+금 free -> run 금토일월 = 4 -> DAY_CONTIG*(4-2)^1.6 + FRI_EVENT
= 56.82 + 6.25 = 63.07, and every other term in the score is a penalty (<= 0).

| pair | cost | nodes | result |
|---|---|---|---|
| WCiv+LHP | −25.0 | 2,901,776 | cannot beat |
| WCiv+SciRD | −27.0 | 1,882,324 | cannot beat |
| LHP+SciRD | −28.0 | 175,552 | cannot beat |
| WCiv+Lang | −29.0 | 3,267,735 | cannot beat |
| MR+WCiv | −29.7 | 38,939,746 | cannot beat |
| LHP+Lang | −30.0 | 278,407 | cannot beat |
| MR+LHP · SciRD+Lang · MR+SciRD · MR+Lang | −30.7 … −34.7 | **0** | eliminated on cost alone |

**3+ deferrals:** cheapest triple costs **−40.0**, and 63.1 − 40.0 = 23.1 < 32.51.
Eliminated analytically, no search needed.

→ **rank3's search over ndef ∈ {0,1} is exhaustive.** The reported optimum is global.

⚠️ **RE-VERIFIED after R122** (incumbent fell 32.51 → 29.34, so pruning weakened and the
first proof no longer held). All 10 pairs re-run against 29.34: **none beats it.** Three
pairs that had previously been eliminated on cost alone (SciRD+Lang, MR+SciRD) now required
real search — 63.1 − 32.0 = 31.1 > 29.34 — and still lost. 3-deferral cheapest −40.0 ⇒
63.1 − 40.0 = 23.1 < 29.34, still analytic. **Lesson: this proof is incumbent-dependent and
must be re-run whenever the pool or the optimum changes.**


## R122. Sequel filter was applied to ONE pool — sequels reached #1 as free electives
R112 excluded "(2)" science sequels from the **SciRD** pool. It did not touch **OPEN**.
Result: `MAT1002-05-00` (CALCULUS & VECTOR ANALYSIS **(2)**) sat in the rank-1 timetable as
a free elective. Iden has never taken MAT1001, so that timetable was unregisterable.

**Fix:** the same prerequisite map now gates the OPEN pool. Extended from 4 codes to 19,
covering 미적분·공학수학·일반물리·일반화학·일반생물 honours variants, ISE, UIC 언어(2), and the
YCF 제2외국어(2) family.

⚠️ **CODE MAP ONLY, never names (R80).** `UIC1551` is **"WORLD HISTORY: GROUP II"** — the
"II" is a category, not a part 2. A name-based rule would have deleted it from the LHP pool,
where it appears in the current rank-1 timetable. Checked every candidate name before
building the map, and this was the one that would have broken.

**Impact — the largest of any single fix so far:** OPEN **451 → 362** sections (−89),
signatures 197 → 192, and the optimum fell **32.51 → 29.34**. The previous #1 depended on a
course Iden cannot take. It also invalidated R121's proof, which had to be re-run.

**Rule: a filter that encodes eligibility must be applied to EVERY pool, not the one where
the bug was noticed.** Same family as R112, and the second time this exact class recurred.

## R123. ⚠️ 유의사항 audit — 84 ineligible sections were sitting in the pools
Prompted by Iden ("did you check the 유의사항 tab? It contains some written data that might
need to be translated"). The field *was* being read (R61), but the pattern list covered
only **33 of 712** sections. A full sweep of all **88 distinct 유의사항 texts** across the
437 noted sections found these misses:

| pattern | sections | why it blocks Iden |
|---|---|---|
| **언더우드국제대학 소속 학생 수강 불가** | **59** | states outright that UIC students may not enrol — Iden is UIC HASS |
| 언더우드국제대학 … **를 제외한 1학년** | 7 | first-years *excluding* UIC |
| 의예과 / 치의예과 / 의치예과 학생만 | 9 | medical-only |
| 재외국민·외국인 전형 입학자 | 4 | Iden is neither (D-12) |
| RA(Residential Assistant)만 | 2 | not an RA |
| **Senior students only** | 3 | regex was `senior[s]? only` — the text says "senior **students** only" |

**Impact:** OPEN pool **362 → 311**. Optimum **unchanged at 29.34**, and none of the 84
appeared in the top-50, so the published ranking was accidentally unaffected. The pool was
wrong regardless, and a different weight set would have surfaced them.

**R121's proof still holds a fortiori:** the incumbent is unchanged and every pool only
shrank, so no ndef=2 branch — already unable to beat 29.34 with *larger* pools — can beat
it now. No re-run needed (unlike after R122, where the optimum moved).

Notes checked and deliberately NOT blocked: "UIC students only" (allows Iden),
"화학과·약학과 소속 학생 수강불가" (Iden is neither), "1학년만 수강 가능" (Iden is 1학년),
"해당 언어를 처음 배우는 학생 대상" (Iden has studied none), "UIC First" (priority, not a bar),
"only HASS first major and double major" (Iden is HASS first major).

**Rule: audit the FULL distinct-value list of a free-text field, not just the cases that
happened to surface.** Same family as R112/R122 — a filter that was right in principle and
incomplete in coverage.

## R124. 체육과건강 stays excluded — by decision, now recorded
41 sections, all **1.0 credit**, all **학년 0**, all eligible for Iden. They sit in rank2's
SKIP regex with no logged reason, found during the R123 field sweep.

**Iden 2026-08-06:** *"max credit is 19 credits, so we can fit them in, but they would be
nothing but a minus, so leave it."*

Correct on both counts: 18 + 1 = 19 fits inside the cap (which is 22 per R111), so they are
**not** excluded by arithmetic — they are excluded because a 1-credit PE class carries no
requirement value and only adds occupied time, i.e. pure schedule cost. Keeping the SKIP.

**Full-field sweep result (companion to R123):** every field the ranker reads has now been
audited against its complete distinct-value list.
- `mode` vs our room-derived `kinds`: **0 contradictions across 712 sections.** The
  registrar's own 수업방식 independently confirms every 대면/온라인/동영상 call — validating
  R115 and R52 from a source the parser never reads.
- `lang`: **'10' = English · '20' = taught in the target language** (중국어/러시아어 drills)
  **· '' = Korean.** Verified three ways, incl. YCA1006 splitting 5 blank / 2 '10', which
  matches R58's "only two English chapel sections". `cc_ok` is correct.
- `dept`: SKIP covers 사회참여(R35 exempt) · RC자기주도활동(R36 auto) · RC심화 · 체육과건강(this rule).
- 28 ISE/나노 sections survive all filters (they say only "UIC students only", which Iden
  satisfies) but **never reach the top-50** — the 학년 penalty excludes them on merit rather
  than by a hard rule, which is the correct mechanism.

## R125. 4-YEAR STRUCTURE — pool scarcity, and why the current model is wrong
Prompted by Iden: *"the current timetables have courses completely not considering I have a
pool of major credits to complete."* Correct. Measured need vs reachable-at-국제 supply:

| pool | need | codes @국제 | ratio |
|---|---|---|---|
| **MR 전필** | 6 | **4** | **1.50** ⚠ |
| CC WCiv | 1 | 1 | 1.00 |
| ME 전선 | 8 | 16 | 0.50 |
| CC SciRD · CC Lang | 1 | 2 | 0.50 |
| UIC Seminar | 2 | 8 | 0.25 |
| CC LHP | 1 | 7 | 0.14 |
| 자유선택 | 13 | 439 | **0.03** |

**MR ratio > 1 ⇒ finishing MR at 국제 alone is IMPOSSIBLE.**
신촌-only: **ECO2101 거시 · ECO2102 미시 · QRM3005 수리통계**.
But requirement 5 is *"수리통계 **or** 회귀분석"* and **QRM3004 runs at 국제 in Spring** — the
or-pair buys out one commute. Forced set is therefore **ECO2101 + ECO2102** ⇒ **μ ≥ 1**
(at least one future semester must include 신촌 travel; μ = 1 if they can share one).

**The scoring error this exposes:** free electives (ratio 0.03, 439 codes, need 13) are
abundant; ME (ratio 0.50) and MR (1.50) are scarce. The model scores a 학년-2 ME course at
**−4** and an abundant 학년-0 free elective at **0**, i.e. it prefers the abundant resource.
Rank-1 spends both open slots on 창업204 and 사회학 while 13 ME sections go unused.

**Fall-2026 consequence:** only 2 MR courses are reachable at 국제 this term — QRM1001 and
**ECO1101**. ECO1101 is 학년 1, so it is the single course that is both in the scarcest pool
and free of the year penalty. It currently sits in the elective pool at +8 and appears
nowhere in the top 50.

**Design agreed with Iden (2026-08-06):** shadow price per pool
`value = f(need / reachable supply)`, replacing `ROLE_MR`, `ROLE_ME` and the whole `DEFER`
table — R117 was a proxy for exactly this. Hard feasibility as a cheap filter on top.
Soft per-timetable future-planning was rejected as 5000× too expensive.
⚠️ **OPEN: the 학년 penalty.** −10 on 학년-2 courses is what suppresses ME. QRM's own chart
calls those YR-2 courses and Iden is one semester away. Iden is deciding; do not assume.

## R126. ⭐ CAMPUS OBJECTIVE (Iden 2026-08-06) — and why it is invariant for Fall 2026
> "1) No commute. This is very important, no commute per individual semesters.
>  2) Maximize the amount of 신촌 semesters. 신촌 is much much much more preferable than 국제."
> "it is bigger than a mon + fri."

**This reverses a core assumption.** Everything before treated 신촌 as a *cost* (commute).
It is the opposite: 신촌 is the preferred campus.

- **HARD constraint:** every semester single-campus. **μ = 0**, no mixed semesters.
- **MAXIMISE:** count of pure-신촌 semesters (π).
- **Weight:** one 신촌 semester > a 월+금-free week = **63.07**, which is exactly SCHED_UB —
  the maximum the entire weekly-comfort model can produce (R121). So campus **dominates the
  whole weekly range**, and any value > 63 yields an identical ordering ⇒ implement as
  **lexicographic**: maximise 신촌 semesters first, optimise the weekly grid within that.
  No exact number needed.

### Campus availability
| pool | 국제 ONLY | 신촌 ONLY | both |
|---|---|---|---|
| MR | QRM1001 | ECO2101 · ECO2102 · QRM3005 | ECO1101 |
| ME | **9** (QRM2001·2002·2004·2102·3001·3007·4807·4808·4809) | 6 (ECO1105·3104·3130·3134·4115·STA2105) | ECO1103·ECO1104·STA2102 |
| CC | **all** — UIC courses are 국제 | — | — |
**All 8 ME credits are reachable at 신촌** (9 available) ⇒ the major never forces 국제.

### ⚠ Fall 2026 cannot change the campus outcome
8 국제-locked courses remain; only **5** are clearable now (QRM1001 + WCiv + LHP + SciRD +
Lang). QRM3003/3004 is Spring-only and not offered; both UIC Seminars are window-locked to
Sem 4–7. So ≥3 always remain ⇒ **exactly 1 more 국제 semester ⇒ π = 5, INVARIANT** over
every possible Fall-2026 timetable.

**What it does change:**
1. **Take QRM1001 now.** 국제-locked, available, in a forced-국제 semester. Deferring spends
   scarce 국제 capacity later on something clearable today. This alone flips the current #1,
   which defers it and spends two slots on 대학교양 electives available at either campus.
2. The later 국제 semester has **3 spare slots** → fill with 국제-only ME so 신촌 semesters
   need not carry ME.

⚠️ **Depends on VERIFY 28** (UIC Seminar window Sem 4–7 for HASS — R87: stated for UD,
silent for HASS). If HASS has no window, the invariance arithmetic changes. Now load-bearing.

---

## R127. Chapel bonus = +10 (Iden 2026-08-06) — *logged late, 2026-08-07*
Intrinsic desirability ("chapel is pretty desirable in itself", "easy to catch, finish
offline chapels now"), genuinely **separate** from the −4.2 competition-based deferral
cost — unlike the language +8, which turned out to be the same logic twice (R119).
Taking chapel: +10. Not taking it: −4.2 and no +10 ⇒ a 14.2-point swing.
⚠️ **This rule and R128 existed only as code comments until 2026-08-07.** `HANDOFF_2026-08-06`
claimed "132 rules"; the file stopped at R126. Log the same turn the decision is made.

## R128. 학년 penalty rescaled −10 → −4 (Iden 2026-08-06) — *logged late, 2026-08-07*
`YEAR_PEN(y) = -4.0*(y-1)**2.5`.  1 yr early −4 · 2 −22.6 · 3 −62.4. Shape unchanged;
only the first step was wrong. Senior courses stay unreachable, next-year courses compete.
**R128b:** for QRM-pool courses use QRM's own curriculum-chart year (대학요람 pp.246–7),
not the registrar's 학년 — the registrar labels ECO1103/1104 학년 2 from *Economics'*
perspective while QRM's chart places them at YR 1. Same category error as R102.

## R129. ⭐⭐ TRIP and REST ARE TWO GOODS — the free-day model was built on a false premise
**Iden 2026-08-07, unprompted context that is in no file:** *"actually 국제 is a dorm, and
신촌 is commute from home, so next semester will be auto-dorm. But I do go home in weekends,
or, if consecutive, fridays, mondays, or any other weekday that is connected-ly free. But,
a wednesday with online class, but tuesday and thursday offline classes around it, i don't
commute. So wednesday doesn't really count as a free day, in that sense."*
And: *"'rest' should apply to every single weekday (genuinely free days). Days connected to
the weekend (number of days) should just scale sharply by day."*

**Every free-day weight was elicited under "commute to campus" (D-7/D-10/R50). Iden LIVES
at 국제.** The good was never "commutes avoided" — it is **"can I go home?"**, and home is
~2h away (HANDOFF §1). Two goods were conflated into one:

| | trigger | mask | value |
|---|---|---|---|
| **TRIP** — going home | days with **no campus presence**, **connected to the weekend** | PRESENCE | `DAY_CONTIG*(run−2)^RUN_EXP`, run counted outward from 토+일 |
| **REST** — a day off | a **genuinely** free weekday: nothing holding a fixed hour | TIME | `REST = 4.70` per day, **equal for every weekday** |

An online class does **not** block TRIP (he can attend from home) but **does** block REST.
This finally reconciles two statements that were each ruled on separately and never met:
- **R57** *"nothing on Wednesday still feels good"* → an **empty** Wednesday is rest.
- **R91** *"I still put in effort to listen to it… that effort is just gone"* → a Wednesday
  with an online class is **work**, so it is not rest. R91 fixed only the Friday event
  bonus and explicitly declined a general discount; this is the general case.

### What changed in the output
- Best score **40.51 → 45.21**; **11 of the old top-50 dropped out**; new #1 = old #2.
- Old top-50 free-day shapes `{월금: 40, 월수금: 10}` → new `{월금: 50}`. **Every 월수금
  timetable was collecting a fake Wednesday.** Verified mechanism on the old rank-5:
  its Wednesday was occupied *only* by `UIC1561-01`'s 수7 `동영상(중복수강불가)` block —
  campus-free, so the old model paid ISOLATED +4.70 for a day he is working.
- An online-only mid-week day now scores **identically to an in-person one**, which is
  exactly what Iden said it should.
- A genuinely empty 월/금 now earns REST **on top of** TRIP — the old model never paid it.
- A mid-week run not touching the weekend no longer earns TRIP value at all.
- `ISOLATED` is retired as a category (kept as a deprecated alias so R57's elicited 25%
  ratio still ties to a live constant). `test_weights.py`: **19/19**, with 4 new R129 cases.

### ⚠️ Consequence not yet resolved — the SCALE moved
`SCHED_UB` rises from 63.07 to a true bound of **276.0** (empty week; the reachable figure
for a real 6-course week is far lower but still well above 63). **R117's deferral costs
were fitted against a 63-point schedule range and have not been refitted.** Iden's anchors
(WCiv −12, LHP −13) mean something different against a wider range. Requirements are now
relatively *cheaper* to postpone than his anchors implied. **This is a value, not a fix.**

## R130. ⚠️ `mileage_history.json` DESCRIBES UPPERCLASSMEN ONLY — never infer freshman odds
**Iden 2026-08-07, correcting me:** *"western civ is open to a lot of freshman. The
'oversubscribed' you are seeing is just for 2nd-year students. The professor just didn't
accept those students. Western Civilization, and Chinese, are MEANT for 1st-year students.
The so-called 'seats' you are seeing are completely individual from freshmen seats."*

The 마일리지 round (8.10–8.11) is **2학년 이상 only**; 신입생·1학년 register 8.25 on
대기순번제 (수강편람 다-3). So `atnlcPercpCnt`/`cnt` in that file describe a **different
seat pool** from the one Iden draws on. Consistent with the data: `sy1PercpCnt` (1학년 몫)
is 0 on every UIC1561 / UIC1805 / QRM1001 row. **A 배율 > 1 there does NOT mean Iden is at
risk.** I built a whole availability analysis on this and it was measuring the wrong
population. R118 remains true about *what the fields are*; this rule bounds *who they cover*.

## R131. ✅ VERIFY 28 CLOSED — the UIC Seminar window is Underwood Division only
Read from the primary source rather than recalled. The "one seminar per semester, 2nd sem
sophomore → 1st sem senior" sentence sits in **§11.1 "Common Curriculum Course for 2026 UD
freshmen"** (Enrollment Guide l.873–881). Iden's section is **§11.3 "…for 2026 HASS
freshmen"** (l.979), whose seminar entry reads in full: *"UIC Seminars (6 credits): HASS
students are required to take two UIC seminars. Courses with course codes of UIC35(XX) and
UIC36(XX) are UIC Seminars."* — **no window.** Confirms R87, retires R15/R23 for Iden.
**Iden 2026-08-07 confirms personally:** *"I am HASS, and yes, I can take two UIC seminars
with no window."*
⚠️ **The model still disagrees with him.** `REQUIREMENTS_AUDIT` A6 marks seminars
"❌ NO — window-locked Sem 4–7" and the pools discard **4 eligible 국제 sections this Fall**
(UIC3527 · UIC3643 · UIC3649 · UIC3657; the other 3 are barred by the UIC-ICU filter).
R126's π-invariance arithmetic explicitly rests on their being unavailable. **Open.**

## R132. ⚠️ `defer2_check.py` had drifted away from the thing it certifies
R121 ("MAX_DEFER=1 is PROVEN sufficient") is only as good as this script, and the script
had three staleness bugs: `INCUMBENT` three optima out of date (29.34 vs 45.21); `year_of()`
where rank3 uses `eff_year()`, silently dropping R128b; and no `CHAPEL_BONUS`, scoring every
chapel-taking timetable 10 low. All three fixed 2026-08-07.
**Status after R129: 1 of 10 pairs re-verified.** The cheapest and most dangerous pair
(WCiv+LHP, cost −25.0, 20.9M nodes) **cannot beat** the 45.214 incumbent. The other nine
pairs are **not yet re-run**, so R121 is downgraded to *partially re-verified* until they
are. Any pair costing more than −25 is *probably* safe, but the freed slots differ by pair,
so this is not a proof — do not record it as one.

## R133. ⚠️ THE 대학요람 IS NOT THE UNIVERSE — the live JSON is. Iden 2026-08-07.
*"the 대학요람 omits a few courses that are inside the json file that contains all the data
for the courses."* Verified against `canonical_2026F.json`:

| direction | courses |
|---|---|
| **offered Fall 2026, `qcat`=ME, but ABSENT from the 대학요람 QRM chart** | **QRM2102** 선형대수및미분방정식 · **QRM3007** FINANCIAL MACHINE LEARNING · **QRM4808** FINANCIAL TIME SERIES ANALYSIS · **QRM4809** CORPORATE FINANCE STRATEGIES (+ ECO1105, not offered) |
| **in the chart but absent from `rank2.QRM_CHART_YEAR`** | **STP3007** SOCIAL INNOVATION SEMINAR (ME, YR3) — not offered 국제 Fall 2026, so no current effect, but the map is incomplete |

**Rule:** `qcat` (QRM's own live listing, R102) decides **membership**; the 대학요람 chart
decides **year placement**; where a course is in the data but not the chart, the year is
**inferred from the code digit** and must be labelled as an inference, not chart data.
Never use the 대학요람 as an eligibility filter — it is dated 2026-04-28 and lags the offering.
Confirms and generalises R120, which noticed the omission but not the direction of authority.

## R134. ⚠️⚠️ 학년별 정원 = 0 makes registration OUTRIGHT IMPOSSIBLE — not merely hard
수강신청 제도안내 §4 참고사항 lists the conditions under which 수강신청이 **불가**:
> - 예외과목을 제외하고 … 학점 초과 · **강의시간이 겹치는 경우** · 학정번호가 동일한 경우
> - **학년별 정원이 0이거나, 전공자정원값과 정원값이 동일한 상황에서 타학과 학생이 신청하는 경우**
> - 수강제한학과로 설정된 학과의 학생이 신청하는 경우

and separately: *"대기순번제 기간 중에는 … 과목별로 설정된 전공자정원/학년별정원에 따라
**대기순번 1번인 학생이 수강신청되지 않을 수 있음**"*.

**Nuance that must not be lost (this is where R130's mistake would recur):** per-year quotas
are **optional** (FAQ 라: *학과 선택사항임*). 124 of 142 rows in `mileage_history.json` have
sy1..sy6 all zero because **the system is not in use for that section**, not because 1학년 is
barred. "학년별 정원이 0" means *a quota scheme is in force AND this year's share is 0*.
Diagnostic: some sy_i is non-zero ⇒ the scheme is in force ⇒ sy1 = 0 really does bar Iden.
Under that test, **ECO1101-05 in 2026-1 had sy1=0 with sy2=32/sy3=14/sy4=8** — a live scheme
with zero freshman share — while the same section in 2025-2 and 2025-1 had sy1=28 and 43.
It varies by semester, so **nothing can be concluded about Fall 2026 from history.**
⏳ Actionable: Fall 2026 quotas become observable once the 2학년+ round closes (8.11–8.14).
Re-pull `findMlgAppcsResltList.do` then and apply the diagnostic before the 8.25 slot.
This does **not** contradict R130: R130 says 배율 tells you nothing about Iden; R134 says the
per-학년 quota field, when in force, is a hard gate. Different fields, different force.

## R135. ✅ VERIFY 23 CLOSED — no prerequisite chain forces 원론 before ECO2101/ECO2102
대학요람 붙임3 states prerequisites explicitly where they exist — e.g. ECO3123 계약및조직
*"(선수과목 : 미시경제학, 경제수학)"*, ECO4110 *"(선수과목 : 미시경제학)"*. **ECO2101 and
ECO2102 declare none**, and neither does any QRM MR course (QRM1001/3003/3004/3005 carry
descriptions only). So 원론 (ECO1103/1104) is **not** on the critical path to the MR chain;
it is an ME in its own right (R102) and an Econ 이중전공 필수 (R64), nothing more.
Consequence for R129's successor question: the 학년 penalty cannot be a *formal* gate — there
are no gates. Iden 2026-08-07 defines it as **"I'm not ready for it"**, i.e. substantive
readiness. It is a difficulty estimate, and it is NOT commensurable with the MR/ME role bonus
(degree progress). The retired `test_weights` assertion was comparing two different accounts.

## R136. ⭐ NEVER ELICIT A WEIGHT FROM THE RANKED OUTPUT — Iden 2026-08-07
I proposed that Iden read the top 50 and say where the ordering felt wrong, and derive the
weights from that. **He rejected it, correctly, on two grounds:**
> *"me looking at the timetable and deriving things is unreliable if multiple numbers are
> clashing together and I'm only looking at the result + it creates bias"*

1. **Not identifiable.** A timetable's score is ~20 weights summed. One "that ordering is
   wrong" observation constrains the *sum*, not any single term. Two weights that are both
   wrong in opposite directions produce output that looks right, and one wrong weight can be
   blamed on any of the others. This is exactly how R117's deferral table went wrong: five of
   its seven values were **fitted to reproduce two anchors** instead of elicited, and the
   preference embedded in those anchors leaked into pools where it did not belong.
2. **Anchoring.** Showing him the current ranking, or the current constants, biases the
   answer toward what the model already does. `DECISIONS_NEEDED.md` §1 prints the live values
   — **that file anchors, and must not be used as the elicitation instrument.**

**Method to use instead.** Elicit from *scenarios*, not from output:
- each question isolates **one** comparison, so the answer identifies **one** ratio;
- questions are posed in lived terms (days at home, 9am starts, a course postponed), never
  in points, and never showing the current value;
- the scale stays pinned to the standing anchor (one 1교시 day = −10) so every answer is a
  **ratio**, and I do the arithmetic;
- the resulting constant is then **checked against**, never fitted to, the ranked output.

Iden: *"I know I'm not good at numbers; but you are."* The division of labour is: he supplies
preferences over situations he can actually picture, I turn them into constants and carry the
identification burden. Asking him for a number, or for a verdict on a ranking, is offloading
my half of the job onto him.

## R137. NO PER-COURSE QUESTIONS — and no question that bundles two quantities
Iden 2026-08-07, rejecting my elicitation of the deferral cost via QRM입문:
> *"that's a complex question measuring different numbers. I don't like answering individual
> course questions"*

Two separate constraints, both standing:
1. **One quantity per question.** My question bundled (a) how much a requirement is worth,
   (b) the shape of the free-day curve, and (c) one specific course. An answer to that
   constrains a sum, which is the R136 failure over again — in the very instrument built to
   avoid R136.
2. **Ask at the level of the MECHANISM, never the course.** Consistent with R64/R66/R69
   ("no per-course points") — Iden allows category-level values but not per-course verdicts.

**Design consequence for the deferral table.** Do NOT elicit seven per-requirement costs.
Elicit **one** generic "what does carrying an unfinished requirement forward cost", then let
**measured** scarcity (need ÷ reachable supply, already computed: MR 1.50 · WCiv 1.00 ·
ME/SciRD/Lang 0.50 · Seminar 0.25 · LHP 0.14 · 자유선택 0.03) scale it per requirement.
That is one value from Iden and six from data, instead of two anchors from Iden and five
fitted to them — which is precisely how R117 went wrong.

## R138. Elicitation hygiene — do not report implied values mid-instrument
Corollary of R136. Telling Iden what his previous answer implied in points anchors every
later answer in the same session. Collect the full set first, do the arithmetic afterwards,
then show him the derivation and let him reject it. Stated to him 2026-08-07 and adopted.

## R139. Elicitation round 1 — results, brackets, and what is still empty (2026-08-07)
Scale anchors held fixed: 1교시 start = **−10**, no-lunch day = **−6**, missing dinner = **−8**.

| # | question | Iden's answer | what it pins |
|---|---|---|---|
| E1 | blocks of 1 day/week vs 2 days/fortnight, **same total** | *"Thu+Fri off, every other week"* | free-day value is **CONVEX** in run length — `RUN_EXP > 1` confirmed **[E]**. Magnitude still **[P]** |
| E2 | how many 9am starts to buy a free Friday | *"Two 9am starts"* | a free Friday ≈ **2 × 10 = 20**. ⚠️ ambiguous *what* he priced — trip only, or trip + blank day + Friday events. **Disambiguate before using** |
| E3 | blank weekday vs one 9am start | *"the 9am start is worse"* | `REST` **< 10** |
| E4 | blank weekday vs no-lunch day | *"losing the blank weekday"* is worse | `REST` **> 6** |
| E5 | cost of carrying a requirement forward | **"I'm not sure yet"** | **NOTHING — left empty.** A UI misclick registered an option; Iden corrected it. Void. |

**Derived so far:** `REST` ∈ **(6, 10)**. The live value is **4.70**, which is *below the
bracket* — it must rise. 4.70 came from R57/R114, where it was elicited as "25% of a
weekend-attached day" while describing an **isolated Wednesday only**. Under R129 it is a
different quantity (the value of not working that day, on any weekday), and Iden prices it
higher than a missed lunch. **Not yet changed in code — pending one more bracketing answer.**

**Method note:** E2's ambiguity is my error, not his. "Getting Friday free" bundles three
live terms (`DAY_CONTIG` trip value, `FRI_EVENT` school-events bonus, `REST`), which is the
R137 violation again. Asking one clean follow-up rather than guessing the split.

## R140. Elicitation round 2 — REST is SOLVED, the free-day CURVE is not (and conflicts)
Scale held fixed: 1교시 = **10** · no-lunch = **6** · dinner = **8**.

| # | question | answer | implication |
|---|---|---|---|
| E6 | blank weekday vs no-dinner day | *"the no-dinner day"* is worse | `REST` **< 8** |
| E7 | same total free weekdays, blocks of 1 / 2 / 3 / 5 | **blocks of 2** | interior optimum at n=2 |
| E9 | what "a free Friday" priced | *"the trip plus a blank day"* | E2 = trip(1) + REST, **excludes** FRI_EVENT |
| E8 | 3-day → 4-day weekend, every week, in 9am starts | *"one more"* | increment = 10, incl. a 2nd blank day |

### ✅ SOLVED — `REST = 7.0`
Three independent comparisons bracket it: **> 6** (E4, worse than a missed lunch), **< 8**
(E6, better than a missed dinner), **< 10** (E3, better than a 9am start). Bracket **(6, 8)**,
midpoint **7.0**. Live value is **4.70** — too low by ~50%. 4.70 was R57/R114's "25% of a
weekend-attached day", elicited when it described an *isolated Wednesday only*; R129 made it
a different quantity and Iden prices the new one higher. **7.0 is a bracket midpoint, not an
elicited point — Iden may move it inside (6,8) at will.**

### 🔴 CONFLICT — E7 and E8 cannot both be true
With REST = 7: E2 gives trip(1) = 20 − 7 = **13.0**; E8 gives trip(2) = 13 + (10 − 7) = **16.0**.
So the 1st weekend-attached day is worth 13 and the 2nd only 3 → **strongly diminishing**.
Test that against E7 at constant total free days:

| grouping | value per week |
|---|---|
| blocks of 1 (금 every week) | **20.0** |
| blocks of 2 (목금 every 2nd week) | **15.0** |

E2+E8 say **blocks of 1 wins by 5/week**. E7 says blocks of 2 wins. **Direct contradiction.**

### Structural finding, valid either way
Checked numerically: `v(n) = D·n^p` has per-week average `D·n^(p−1)`, **monotone in n for
every p** — a power law can never produce an interior optimum. Adding the Friday bonus
(`+B/n`) does not rescue it: **no exponent in [0.5, 3.0]** satisfies both `g(2)>g(1)` and
`g(2)>g(3)`. Therefore:
- if **E7** stands → the *functional form* is wrong, not the exponent. The natural
  replacement is **days-at-home with diminishing returns MINUS a fixed cost per trip**
  (the ~2h journey, paid once per trip), which does generate an interior optimum;
- if **E8** stands → the curve is **concave** (p < 1), and short frequent trips win.

Either way **the live `RUN_EXP = 1.6` is wrong**: it predicts blocks of 5 > 3 > 2 > 1, which
contradicts E7 *and* E8. It was always flagged magnitude-**[P]** (R114); only its *direction*
was ever elicited, and E7/E8 now dispute the direction too.

**Not resolved by me.** Per Iden's standing instruction, a conflict between two of his own
answers is surfaced, not adjudicated. `REST` is likewise **not yet written to code** —
changing it while the curve is unresolved would mix a settled value into an unsettled one.

## R141. ⚠️ LEVELS vs INCREMENTS — my questions mixed the two, and that made the "conflict"
Iden 2026-08-07, catching it himself:
> *"arithmetically, I realized the first. 2->3 is bigger than 3->4. The reason I said upgrade
> two felt bigger initially was because it felt much much better, you know what I mean? Like
> having three days off just is heavenly. Wait I'm confused."*

**Diagnosis: the R140 contradiction is probably not a contradiction in his preferences.**
- **E7** asked him to compare *states* (which semester would you rather live through).
- **E2 and E8** asked him to price *increments* (what would you pay for one more day).

An increment is small **by construction** once the first day has already bought the trip
home, so a four-day weekend can be genuinely wonderful *as a state* while its fourth day is
the least valuable *as an increment*. Both of his answers can be right about different
quantities. I compared them as if they were one currency.

**Standing method rule, alongside R136/R137/R138:** elicit **states**, never increments.
Iden can judge "which semester would I rather have"; asking him to price a marginal day
requires him to hold the rest of the week fixed in his head and mentally subtract, which is
the arithmetic half of the job and therefore **mine**. Differences get computed, never asked.

⚠️ **Do not treat his "arithmetically, I realized the first" as the settled answer.** He
reached it while reasoning inside my framing and then said he was confused — adopting it
would be R136 anchoring with extra steps. Re-asked as a pure state comparison instead.
Consequently E8 is **withdrawn as an increment measurement**; only E2 (which E9 confirmed he
read as a whole-state judgement: trip + blank day) survives from the increment questions.

## R142. ✅ FREE-DAY CONSTANTS RE-ELICITED — and the QRM입문 trade is NOT about weekends
Closing R140's open items. Two of Iden's framings had to be discarded first:
- **E7 (block groupings) is WITHDRAWN.** It offered "Thu+Fri off every *other* week", but a
  timetable is **the same every week for 15 weeks** — alternating schedules are not in the
  choice set. Iden could not make sense of the follow-up trade ("i don't understand what
  exactly I'm giving up here") because *you cannot give up a weekend* — 토/일 are free
  regardless. Only the number of free **weekdays** varies. My error, twice.
- **E8 (increment pricing) is WITHDRAWN** per R141.

### Final constants
| constant | was | now | basis |
|---|---|---|---|
| `REST` | 4.70 | **7.00** | R140 bracket (6,8) from three anchors — **[E]** |
| `DAY_CONTIG` | 18.75 | **13.00** | E2 "free Friday = two 9am starts" = 20, minus REST — **[E]** |
| `FRI_EVENT` | 6.25 | **4.333** | preserves the older elicited "월 = 금의 75%" (R45/R57) — **[E]** |
| `RUN_EXP` | 1.6 | **1.4** | bracket **[1.2, 1.6]**, midpoint — **[P]** |

`DAY_CONTIG = 13` and `FRI_EVENT = 13/3` satisfy *both* the new E2 answer and the old 75%
ratio simultaneously — an independent cross-check that neither elicitation drifted.
`RUN_EXP` stays [P]: Iden said *"can't quantify tbh"*. His two ratio answers pull opposite
ways (V(2)/V(1) "about twice or slightly more" → ~1.2; V(3)/V(2) "more than twice" → >1.6).
**Direction (convex) is settled; magnitude is not, and further questioning is not warranted
until the sensitivity check shows it changes the answer.** `test_weights.py`: **20/20**.

### ⭐ What postponing QRM입문 actually buys — measured, not asserted
Best timetable that postpones QRM입문 vs best that postpones **nothing**:

| | postpones QRM입문 | postpones nothing |
|---|---|---|
| free-day value | **45.64** | **45.64** |
| free-day shape | 월금 | 월금 |
| day-level penalties | **−12.88** | **−50.08** |
| 9am starts · no-lunch days · longest run · worst gap | 1 · 0 · — · 1 | 2 · 1 · 6h · 3 |

**The weekends are IDENTICAL.** Postponing QRM입문 buys **zero** extra time at home. The
entire +37.2 gap is *day-level misery*: QRM1001 meets 목4,5,6, and forcing that block in
drags two 9am starts, a no-lunch day, a six-hour marathon and a three-period hole in with it.

This reframes D-1 completely. The question was posed as "a day at home vs a requirement";
it is actually **"one semester's delay on a required major course, vs roughly four extra 9am
starts plus a skipped lunch plus a six-hour marathon, every week for fifteen weeks."**
Deferral cost is −17.7 against a measured −37.2, which is why 47 of 50 postpone it.
⚠️ Stated as a *measurement of the mechanism*, not as grounds for Iden to reverse-engineer a
weight from the ranking — R136 still binds.

## R143. ⭐⭐⭐ THE 4-YEAR LAYER — D-1 was never a preference, and the answer is computed
Iden 2026-08-07: *"I'm pretty sure there's a big important thing left — the 4-year"*. Correct.
The cost of postponing a requirement is **not** something he should have to feel. It is a
fact about whether the requirement fits later and what postponing does to the campus plan.
R125 said this (*"R117 was a proxy for exactly this"*); I asked him anyway. Same error as
R136/R137 in a new place. **D-1 is withdrawn as a question for Iden.**

### The data that was sitting unused
`raw_2026F.json` holds **783 신촌 sections** alongside the 717 국제 ones. Every campus claim
in R126 was built from the 국제-only `canonical` file. Re-derived from the full data:

| requirement | 국제 | 신촌 | forces a 국제 semester? |
|---|---|---|---|
| **QRM1001** (MR) | 1 | **0** | **YES** |
| **WCiv UIC1561** | 1 | **0** | **YES** |
| **Lang UIC1805/1806** | 4 | **0** | **YES** |
| LHP pool | 16 | 2 | no |
| SciRD UIC2151 | 13 | 1 | no |
| **UIC Seminars** | 7 | **38** | **no** |
| ME pool | 12 | 9 | no |

⚠️ **R126's "CC: all — UIC courses are 국제" is FALSE.** Seminars are overwhelmingly 신촌
(38 vs 7); LHP and SciRD are reachable there too.

### Chapel dissolves — the constraint I expected to bind
Chapel needs 3 more passes at **1 per semester**, which looked like it forced three 국제
semesters. It does not. Enrollment Guide §14.4:
> *"UIC **sophomores** may only enroll in the English Chapel Class in the International Campus
> **and Sinchon campus**."* · *"Juniors and above in the **HASS**/ISE Divisions … during the
> additional course registration/course change period, they may enroll in **all chapel classes
> opened in the Sinchon campus**"*

and §14.2: 신촌 Chapel (YCA1007-03, Chapel C) is **"Online Chapel" — no class time, no
classroom assigned**. An online chapel consumes **no campus presence**, so from 2학년 onward
chapel neither forces a 국제 semester nor breaks campus purity. Only *this* semester is
constrained (§14.4: *"UIC freshman may only enroll … in the International Campus"* — R58).

### ⭐ The result
Semesters 2–8 = **7 remaining**. Fall 2026 is forced 국제 (R8). Exactly **three** 국제-only
requirements remain: **QRM1001 · WCiv · Lang** — and this semester has **6 slots**.

| Fall 2026 clears… | further 국제 semesters needed | **신촌 semesters** |
|---|---|---|
| all three | **0** | **6 of 7** |
| defers any one | **1** | **5 of 7** |

**Postponing QRM입문 costs exactly one 신촌 semester.** Per R126 a 신촌 semester outranks the
entire weekly-schedule range lexicographically, so this is not a trade-off to be priced — it
is a **dominance**. No weekly improvement can compensate, and the −37.2 of daily misery
measured in R142 is irrelevant to it.

**The live #1 postpones QRM입문. The best non-postponing timetable currently sits at rank
3394.** The ranking is wrong at the top, and R117's whole deferral table is superseded by
this computation rather than by any answer from Iden.

### ⚠️ Open, and genuinely load-bearing
1. **QRM3003** (Principles of Financial Engineering, MR, Spring-only) — campus **unknown**;
   not offered Fall 2026 so it is absent from the data. If 국제-only it forces one 국제
   semester regardless, and the table above shifts by one. **Check before freezing.**
2. Availability above is **Fall 2026**. 38 신촌 seminar sections is robust; **1** 신촌 SciRD
   and **2** 신촌 LHP sections are thin and may not recur — deferring those carries risk even
   though the nominal count does not move.
3. Requirement 5 is a disjunction: QRM3005 (신촌) **or** QRM3004 (국제, Spring, R74). Taking
   the 신촌 branch keeps the count at 0.

## R144. ❌ R143's CONCLUSION IS WITHDRAWN — QRM3003 forces a 국제 semester anyway
**Iden 2026-08-07:** *"QRM3003 — it's only 국제 and it only opens in the spring semester as
per the list."* This was R143's own flagged unknown, and it inverts the result.

### Corrected structure
Semesters 2–8 = 7. Springs are sems 3 · 5 · 7; Falls are 2 · 4 · 6 · 8.
- **sem 2 (Fall 2026)** is forced 국제 (R8, RC freshman).
- **QRM3003** is MR, 국제-only, Spring-only ⇒ **one Spring must also be 국제**, whenever taken.

⇒ **minimum 2 국제 semesters · maximum 5 신촌** — and that holds *no matter what Iden takes
this Fall.* The R143 table (6 vs 5 신촌 depending on deferral) is **wrong and withdrawn.**

### The consequence, which runs OPPOSITE to R143
There are **4** 국제-only items in total — QRM1001 · WCiv · Lang · QRM3003 — to be placed in
**2 국제 semesters × 6 slots = 12 slots**. Verified from `mileage_history.json` that all three
of the currently-available ones also run **at 국제 in Spring** (QRM1001, UIC1561, UIC1805 all
appear in S25 and S26 국제 rows), so deferring them into the QRM3003 semester is feasible.

**국제 capacity is not scarce; it is 3× oversupplied.** So deferring QRM입문 does **not** cost
a 신촌 semester. R143 asserted it did, on the strength of a gap R143 itself flagged. My error
— I should have resolved the flag before drawing the conclusion, not after.

### What the deferral cost actually is
Not a campus count. Measured from the live ranker, removing one requirement from a 6-slot
semester that is carrying 5 of them is worth **+14 to +33 raw schedule points** (MR +33.2,
Lang +31.2, WCiv +19.6, SciRD +15.6, LHP +14.1). The cost of *fitting* a requirement is
therefore **convex in how many the semester already carries**. That gives the real trade:

> spreading the four 국제-only items across the two 국제 semesters yields a better week in
> **both**, versus cramming them into Fall 2026 and leaving the other 국제 semester nearly empty.

So the four-year layer may well **endorse** deferring — the opposite of R126's and R143's
reading. What remains genuinely costly about deferral is **risk**, not crowding: thin future
supply (1 신촌 SciRD section, 2 신촌 LHP), and Iden's first-model point that deferring loses
option value even when the nominal count is unchanged.

### Iden's note, recorded
*"that was why the 시간표 program originally had a defer cost, but I didn't include it because
I wanted to make it better with you."* The original deferral cost was doing this job by hand.
R117 replaced it with elicited anchors; the correct replacement is **this computation**.

## R145. ⭐ THE 학년 PENALTY IS ONE-SIDED AND SHOULD BE TWO-SIDED — and that IS the defer cost
**Iden 2026-08-07:** *"taking a 학년 3 at 학년 1 has a penalty, but taking a 학년 1 and 학년 3..?
Also not too desirable."*

Live: `YEAR_PEN(y) = 0 if y <= 1 else -4*(y-1)**2.5` — it charges only for being **early**
(R77/R128, purpose = *"I'm not ready for it"*, R135). Being **late** is free. But taking a
chart-year-1 course in year 3 is off-sequence and Iden says it is also undesirable.

### Why this collapses the deferral problem
Let `c` = the course's chart year (R128b / 대학요람), `y` = the year Iden takes it in.
The penalty should be a two-sided, asymmetric function of `(y − c)`:

| | meaning | live | should be |
|---|---|---|---|
| `y < c` | **not ready** — missing background | −4·(c−y)^2.5 | unchanged |
| `y = c` | on sequence | 0 | 0 |
| `y > c` | **off-sequence** — behind the chart | **0** | **negative** |

**Deferring a requirement IS taking it late.** QRM1001 has chart year 1; postponing it one
year means sitting a year-1 course as a 2nd-year, two years means as a 3rd-year. So the cost
of deferral is *already* expressed by the `y > c` arm — it does not need a separate table.

This is exactly the design R137 called for: **one mechanism from Iden, scaled per requirement
by structure** (here, each course's own chart-year distance) rather than seven elicited
anchors. It supersedes R117 the same way R143/R144's campus analysis was meant to, but
unlike those it needs no assumption about future offerings — the chart year is a fixed fact.

⚠️ Two arms, two different purposes, so **they need not be symmetric**: early = *cannot do
the work*; late = *awkward and delays everything downstream*. The ratio between them is a
value only Iden can set. `RISK` (thin future supply) is a **separate, measurable** term and
must not be folded into this one.

## R146. ✅ THE DEFERRAL COST IS NOW DERIVED, NOT ELICITED — R117 is superseded
Elicited 2026-08-07 for R145's second arm:
- **asymmetry** — *"early is somewhat worse"* ("roughly half again as bad") ⇒ `EARLY/LATE = 1.5`
- **scaling** — *"sharply worse"* ⇒ the late arm takes the same convex exponent (2.5)

`EARLY_K = 4.0` · `LATE_K = 4.0/1.5 = 2.667` · `YEAR_EXP = 2.5`:

| gap | 3 early | 2 early | 1 early | on seq | 1 late | 2 late | 3 late |
|---|---|---|---|---|---|---|---|
| penalty | −62.35 | −22.63 | −4.00 | 0 | **−2.67** | **−15.08** | **−41.57** |

### Deferring QRM입문, priced by where it lands
Fall 2026 is 국제; QRM3003 (국제, Spring-only, chart yr 3) forces exactly one 국제 Spring (R144).
So the deferred item lands in whichever Spring that is:

| 국제 Spring | QRM1001 (chart yr 1) | QRM3003 (chart yr 3) | total |
|---|---|---|---|
| sem 3 · Spring 2027 · yr 2 | −2.67 | −4.00 | **−6.67** |
| sem 5 · Spring 2028 · yr 3 | −15.08 | 0 | **−15.08** |
| sem 7 · Spring 2029 · yr 4 | −41.57 | −2.67 | **−44.24** |
| **take QRM1001 now, QRM3003 in yr 3** | **0** | **0** | **0** |

**So deferring QRM입문 costs 2.67–15.08, not the fitted −17.7, and not zero.** The number is
now a consequence of the chart and the plan rather than an anchor. Note it reproduces R117's
order of magnitude — the old fit was not wrong so much as unexplained.

⚠️ **Still not decisive.** R142 measured the *schedule* gain from deferring MR at +33.2 raw,
which exceeds even the worst-case −15.08. The missing term is the schedule cost in the
**receiving** semester, which is not yet computed — see M-7. Until that exists the ranker's
deferral behaviour is not trustworthy, and I should stop drawing conclusions from it.

### Test-suite note
Changing `RUN_EXP` 1.6 → 1.4 (R142) silently broke the `월+금` assertion, which hard-coded a
total. Rewritten to assert the **structure** (an empty 월+금 pays REST on both days on top of
the trip) so it is invariant to a parameter that is still [P]. **Hard-coding a total derived
from a provisional constant makes the suite fail on correct changes.** 20/20.

## R147. ✅ DOUBLE MAJOR CONFIRMED · ME quota drops 24→18 · 2교시 confirmed (Iden 2026-08-07)
> *"One thing is clear: I will do a double major."*
> *"ME is still 'Required', but no one exactly chooses the courses for you. It is still
>  required (15? credits idk)"*
> *"2교시 penalty seems fine as it is."*

### 1. Double major — the FACT is settled, the CHOICE is not
Which one (Mathematics · Economics · low-chance CS) is still open, so **R103 stands**: all
double-major *bonuses* remain scrapped until the target is known. But the *quota* effect is
now certain, because it does not depend on which major is chosen. QRM grad table: *"Major
credits will be reduced to **36** if a student completes a double major."*

| | single major | **double major (now live)** |
|---|---|---|
| QRM MR | 18 | 18 |
| QRM **ME** | 24 | **18** |
| QRM total | 42 | **36** |
| free electives | ~39 (after R109) | **~12–15** |

**Free electives collapse from ~39 credits to ~12–15.** The model treats them as effectively
unlimited (measured scarcity 0.03, R125) and that premise is now much weaker.

### 2. ME is a REQUIRED QUOTA, not a deferrable slot — a structural distinction
Iden: required, but *"no one exactly chooses the courses for you"*. So ME is **18 credits
(6 courses) of a pool**, unlike the five CC/MR requirements which are each one specific
course. **V-2 is answered: ME competes.** But it must NOT be bolted on as a sixth deferrable
slot — it is exactly the *pool with a quota* that R125 described and that `defer_costs.json`'s
unused −8.43 was a placeholder for. Correct mechanism: shadow price on the remaining ME
credits, which falls out of the same four-year layer as B-1.

### 3. Slack, stated as arithmetic and NOT as a re-raise of R111
106.5 credits remain over 7 semesters. At Iden's chosen 6 courses / 18 cr that is
**42 slots for 35.5 courses — 6.5 spare across the entire remaining degree.**
⚠️ `PLANS.md` §E forbids re-raising the 6-vs-7-course choice, and this is not that. R111 was
decided 2026-08-06 when the double major was *"~85% likely, undecided"*. The premise has now
changed. Recording the arithmetic; the decision remains Iden's and is not reopened here.

### 4. 2교시 = −5 CONFIRMED
Carried `[P] 미확인 추정치` since the first session — the last schedule constant with nothing
behind it. Iden reviewed and accepted it. Now **[E-confirmed]**. **V-1 closed.**

## R148. ✅ B-1 MEASURED — the crowding curve, and the deferral question finally closes
Built the missing third term. Method: for every subset of the five requirements, search the
best achievable week using **only** those courses + chapel (pool product ≈ 3.6k, exhaustive).
This isolates **crowding** — how much schedule quality each additional *fixed-section* course
destroys — with no elective freedom to mask it.

| forced requirements | best achievable week | marginal cost | best subset |
|---|---|---|---|
| 0 | 122.87 | — | chapel only |
| 1 | 116.25 | −6.62 | SciRD |
| 2 | 102.25 | −14.00 | WCiv + SciRD |
| 3 | 49.14 | −53.11 | LHP + SciRD + Lang |
| 4 | 30.39 | −18.75 | WCiv + LHP + SciRD + Lang |
| 5 | **−7.66** | −38.05 | all five |

**Steeply convex: the 5th forced course costs ~6× the 1st.** (Non-monotone in the middle
because the *optimal subset* changes at each n, not because the trend reverses.) Total cost
of carrying all five rather than none: **−130.5**. This is the quantitative basis for
"spread the fixed courses across semesters" and it was never measured before.

### The deferral verdict, all three terms present
| term | value |
|---|---|
| gain in Fall 2026 (5 forced → 4) | **+38.05** |
| crowding in the receiving 국제 Spring (1 forced → 2) | **−14.00** |
| year gap, lands yr 2 / yr 3 (R146) | **−6.67 / −15.08** |
| **NET** | **+17.38 / +8.97** |

**Deferring QRM입문 wins on all three terms simultaneously.** The ranker's behaviour — 47 of
the top 50 deferring MR — is therefore *justified*, not an artefact of R117's stale table.
R143's "it costs a 신촌 semester" stays withdrawn; R144's "spreading is better" is confirmed
with numbers.

### ⚠️ Two ways this is optimistic — the margin is smaller than +17
1. **−14.00 is a best case.** It is the *cheapest* 2-subset in the Fall 2026 국제 pool
   (WCiv+SciRD). The real receiving pair is QRM3003 + QRM1001, whose actual times will crowd
   differently and almost certainly worse.
2. **Fall data proxies a Spring semester.** Different sections, different times.
Both push the same direction, so **+8.97 is the safer figure and the sign is not in doubt.**

### Also found
The 4 eligible UIC Seminar sections (UIC3527 · 3643 · 3649 · 3657) were **already in the OPEN
pool all along** — only `REQUIREMENTS_AUDIT.md` A6 claims otherwise (B-3 was a documentation
bug, not a code one). But they carry `_role = 0.0`, so **6 credits of required CC score
identically to a free elective**, against a −22.63 readiness penalty. They can never be
chosen. Same defect as ME (R147): a required *quota* priced at zero. Fixing it needs the pool
shadow price, not another constant.

## R149. ✅ POOL ROLES MEASURED — and the formula independently reproduces Iden's ROLE_MR
The five CC/MR requirements are **named courses** (take it or defer it) and the slot mechanism
handles them. ME · Seminar · free electives are **quotas** — N credits from a pool, Iden's
words: *"no one exactly chooses the courses for you"* (R147). They had no valuation at all.

**Formula:** `role = 8 × min(1, credits still needed ÷ reachable supply)`, on the same scale
Iden used when he set ROLE_MR.

| pool | need | distinct courses | supply | ratio | measured role | elicited |
|---|---|---|---|---|---|---|
| **MR** | 18 | 6 | 18 | **1.00** | **8.00** | **8.0 ✓** |
| WCiv | 3 | 1 | 3 | 1.00 | 8.00 | (named slot) |
| Lang | 3 | 2 | 6 | 0.50 | 4.00 | (named slot) |
| LHP | 3 | 7 | 21 | 0.14 | 1.14 | (named slot) |
| SciRD | 3 | 14 | 42 | 0.07 | 0.57 | (named slot) |
| **ME** | 18 | 28 | 84 | 0.21 | **1.71** | **6.0 ⚠ conflict** |
| **Seminar** | 6 | 45 | 135 | 0.04 | **0.36** | none |
| Free elective | 15 | 719 | 2157 | 0.01 | 0.06 | none (live 0.0) |

### The formula validates itself on the one case where Iden gave a number
MR needs 18 credits from exactly 18 credits of named courses ⇒ ratio 1.00 ⇒ **8.00**,
reproducing his elicited **+8** exactly. That is the only independent check available on this
construction and it passed. Free electives land at 0.06, so the live **0.0 was already right**.

### ⚠ ME: measured 1.71 vs elicited 6.0 — NOT silently changed
Iden's 6.0 came from *"MR slightly higher than ME"* — a statement about **major progress
being desirable**, which is a preference. 1.71 measures **how hard ME is to satisfy later**,
which is structure. R127 (chapel) established these can legitimately be separate accounts.
**His value stands. Logged for him to resolve, not overwritten.**

### Correcting my own overreach from earlier in the session
I first set Seminar = ROLE_ME = 6.0 on the reasoning "same kind of thing as ME". Measured, it
is **0.36** — a ~17× overvaluation. Seminars *are* required, but they are also the **easiest**
requirement to satisfy later: 6 credits against 45 distinct courses, 38 of them at 신촌 (R143).
Being required and being scarce are different properties and I conflated them.

**Net effect on the ranking: none.** Best score 23.07 unchanged, top-50 deferral pattern
unchanged (47 MR / 3 Lang). Seminars still lose to the −22.63 readiness penalty either way —
but they now lose for the right reason. `test_weights.py` 20/20.

## R150. ✅ IDEN RETIRES HIS OWN ROLE_ME — the measured value replaces it
> *"although I said MR is slightly higher than ME, I don't think that holds. The timing I said
> that was before the sophisticated 4-year plan implementation. I naturally thought MEs (I
> have many selections) would be easier to get than MRs (fixed), but if the numbers contradict
> that, then the numbers are probably right."*

`ROLE_ME 6.0 -> 1.71` (R149's measured value). His stated intuition — *MEs are easier to get
than MRs because there are many to choose from* — is **exactly the quantity R149's formula
computes**. He was reaching for scarcity and expressed it as a gap of 2 points; the formula
puts the gap at 6.3. Same claim, measured properly. Not a change of mind, a sharpening.

**This is the correct direction of authority** (his standing instruction #2): where a value is
really a fact about structure, the measurement wins; where it is a preference, he wins. R127
(chapel +10, intrinsic) remains on the preference side and is untouched.

Effect: best score 23.07 -> **21.80**; top-50 deferral pattern **unchanged** (47 MR / 3 Lang).
`test_weights.py` **22/22** — the "MR slightly higher than ME" assertion is retired and
replaced by three that survive: the formula reproduces ROLE_MR=8.00, ME is measured at 1.71,
and MR still ranks above ME.

## R151. 📘 `MODEL.md` created — the single organised account of every live number
Iden 2026-08-07: *"Can you tell me all the logic behind the numbers rn? I need a clean
organization to see what's working and what's not."*

`RULES.md` is 151 chronological rules — a history, not a reference, and unreadable as one.
`MODEL.md` is the **cross-section**: what the model believes *today*, in nine sections
(scale · day · week · year gap · pool value · deferral · crowding · four-year · gaps), each
number tagged **[E]** elicited / **[M]** measured / **[D]** derived / **[P]** provisional.
§8 lists the nine things NOT modelled, ordered by how much they could change the answer.

**Keep both.** `RULES.md` answers *why did this change* and holds the evidence; `MODEL.md`
answers *what is true now*. When they disagree, `RULES.md` is the record and `MODEL.md` is
the bug.

## R152. ⚠️ ME SUPPLY WAS OVERSTATED — the Korean cap was missing from R149's count
R149 put ME supply at 84 cr (28 courses × 3) and ignored the QRM grad table's cap:
> *"Of the QRM courses taken from the School of Economics and Department of Applied
> Statistics, which are taught in Korean, only up to 4 courses (12 credits) can be counted
> as Major Credits."*

**R105 already established the subtlety I then dropped: the cap attaches to the SECTION's
offering department, not the course code.** STA2102 in the current #1 is offered by
계량위험관리 — QRM's own department — so it is *not* capped; the same code from 응용통계학과
at 신촌 would be.

| | credits | capped? |
|---|---|---|
| QRM-dept ME courses (14) | 42 | no |
| ECO/STA codes with a UIC/QRM-offered section (ECO1103 · ECO1104 · STA2102) | 9 | no |
| ECO/STA reachable only from 상경대학/응용통계 (11 codes, 33 cr) | **min(12, 33) = 12** | **yes** |
| **corrected supply** | **63** | |

`ROLE_ME`: ratio 18/63 = 0.286 ⇒ **2.29** (was 1.71). Top-50 unchanged; best score 21.80.
Credit for the catch goes to the review; its magnitude estimate (54 cr, all ECO/STA capped)
was too aggressive because it applied the cap at course level.

## R153. ⚠️⚠️ THE GPA LOOP — the early 학년 arm is the only GPA protection, and R128 halved it
`HANDOFF.md` 191–194: double-major selection is **competitive on cumulative GPA**, and *"At
application time Iden's GPA = Sem 1 + Sem 2 only. Fall 2026 grades directly determine
double-major admission."* Separately, GPA ≥ 3.75 buys **+3 credits** of load (R86/R111).

**This is the only genuinely self-referential thing in the model:** Fall 2026 course choice →
Fall 2026 grades → cumulative GPA → December admission → *which second major* → the quotas
§4 prices against → the ranking. Everything else in §8 is exogenous.

**The consequence nobody drew.** The model has **no difficulty axis at all**. The early arm of
R145 is the only term that penalises reaching above one's level, so it is silently doing
double duty as GPA protection. **R128 rescaled it 10 → 4 on purely readiness grounds** — and
thereby halved the GPA protection in the exact semester where GPA is decisive. The live #1
takes STA2102 (chart yr 2, −4); pre-R128 that was −10.

**Not reversed.** The −4 was Iden's call on readiness and stands; and no difficulty data
exists to model the loop properly. But the early arm now carries a documented second job and
must not be weakened again without it being weighed. Logged in `MODEL.md` §3.

## R154. AI Concentration + double major does NOT fit in 126 credits
Iden 2026-08-07: *"I am actually considering the AI concentration slightly, but I don't know
what benefits it brings beyond just taking a few AI courses."* Answered with arithmetic:

| path | CC | QRM | AI | 2nd | total |
|---|---|---|---|---|---|
| double major only | 39 | **36** | — | 36 | **111** ✓ |
| AI concentration only | 39 | **42** | 18 | — | **99** ✓ |
| both | 39 | **42** | 18 | 36 | **135** ❌ over by 9 |

The AI Concentration keeps the major at 42 (R106 note 6), so it forfeits the double-major
reduction *and* adds 18 credits. QRM4807 serves as both an AI requirement and a QRM ME but
R104 lets it count once, recovering ≤3 cr. **Doing both needs an overload or a 9th semester.**
The benefit beyond the courses themselves is the credential line on the transcript — Iden's
call, but it is a 24-credit decision, not a "few AI courses" one.

## R155. ❌ I REPORTED "TOP 50 UNCHANGED" WITHOUT CHECKING — it changed 33 of 50 places
Iden 2026-08-07: *"do you mean the timetable didn't change or the numbers didn't change?
cause if it's the latter it doesn't make sense."* He was right; the claim was false.

I read "unchanged" off `rank3.py`'s summary line, which prints only **the best score and the
deferral-pattern counts**. Neither is a statement about the top 50. Checked properly by
reconstructing the previous ranking exactly (subtract the +0.58 ME delta from entries
containing an ME course):

| | |
|---|---|
| top-50 membership identical | **NO** |
| top-50 order identical | **NO** |
| entries that changed rank | **33 of 50** |
| rank 1 identical | yes — it contains **no ME course**, so the ME change could not move it |

Only **4 of the top 50** contain an ME course. That is why the *best score* held at 21.795
while a third of the list reshuffled underneath it. **A stable headline number is not evidence
of a stable ranking**, and the summary line must never again be quoted as if it were.

## R156. ⚠️⚠️ THE DERIVED DEFERRAL COST WAS NEVER WIRED IN — and `MODEL.md` claimed it was
Found while checking R155. `rank3.py:31` still loads `defer_costs.json` — R117's seven fitted
values. R146/R148's derived scheme exists **only on paper**. `MODEL.md` §5 asserted it
"replaces the old table entirely". **That was false**; corrected in place.

**And B-2 is blocked on more than I said.** Every outstanding CC requirement is chart-year 1,
so under the derived scheme they all take the same year gap (−2.67) and the same crowding cost
(−14.00) — **≈ −16.7 each, undifferentiated.** R117's fitted table, whatever its provenance,
*does* discriminate. What would legitimately separate them under the new scheme is **risk from
thin future supply**, which is unbuilt (§8.2). ⇒ **do B-4 before B-2**, or the swap loses
information.

**Pattern to watch:** this is the third documentation-vs-code divergence today (seminars
"excluded" in the audit but present in the pool; `ranking_weights.md` stale for two rules;
now this). Every one ran the same direction — **the document claimed more than the code did.**

## R157. 🔍 FULL CODE-vs-DOCUMENT AUDIT — 13/13 constants matched, 4 other things did not
Iden 2026-08-07: *"So the code is matching everything now?"* Not answered from memory —
audited programmatically, because three document-vs-code divergences had already surfaced
today and all three ran the same direction (the document claiming more than the code).

**Numeric constants: 13 of 13 in `MODEL.md` match the live code.** W_E1 · W_E2 · W_LUNCH ·
W_DINNER · DAY_CONTIG · RUN_EXP · REST · FRI_EVENT · ROLE_MR · ROLE_ME · ROLE_SEMINAR ·
year-gap early arm · year-gap late arm. No drift.

**Four non-constant divergences found:**

| # | what | fixed? |
|---|---|---|
| 1 | `rank.py:run_value/score` still contained a **working copy of the pre-R129 single-good model** — dead but callable, and any future caller would silently get the superseded scoring | ✅ now raises `NotImplementedError`; the dead import removed from `rank2.py` |
| 2 | `ranking_weights.md` stale for `FRI_EVENT` and `ROLE_ME` | ✅ regenerated |
| 3 | `defer2_check.py` `INCUMBENT = 45.214` vs live optimum **21.795** — stale *again*, having been re-synced earlier today, because four weight changes followed | ✅ re-synced + warned in-line |
| 4 | `MODEL.md` §3 asserted *"the current #1 takes STA2102"* — true when written, false after R150 flipped the #1 | ✅ reworded, with the rank-9 pointer |

**#1 is the one that mattered.** A superseded model left callable in the tree is exactly how
drift starts; deleting the *document's* claim while leaving the *code* intact fixes nothing.
Superseded code should refuse to run, not sit quietly.

**#3 is a recurring class, not an incident.** `defer2_check.py` hard-codes an optimum that
every weight change invalidates. It went stale twice in one day. The durable fix is to read
the incumbent from `FINAL_ranked3.csv` at runtime rather than store it — logged as a follow-up.

⚠️ **Known and deliberate, NOT fixed:** `rank3.py` still loads R117's fitted `defer_costs.json`.
`MODEL.md` §5 now states this plainly. Blocked on B-4 (risk), per R156 — swapping today would
replace a discriminating-but-fitted table with a principled-but-flat one.

## R158. ⚠️ THE RANKER COLLAPSES INTERCHANGEABLE ELECTIVES — the output implied a choice it never made
Iden 2026-08-07: *"If YCE1253 is a pure schedule fit, why aren't #1~#4 all same timetables with
just that substitute? What's the logics???"*

**Modelling is correct; presentation was wrong.** `rank3` groups electives by
`(time, presence, bonus, credits)` signature, searches over **signatures**, and on output takes
`esig[g][0]` — the **first section in the group, by pool iteration order**. So four
identically-scoring courses appear as one timetable with an *arbitrary* representative printed.
That is why they don't occupy ranks 1–4: the model knows they are the same timetable.

Correct behaviour (50 distinct grids, not 50 relabelings) with dangerous output — Iden would
have registered for YCE1253 believing it was selected. **Fixed:** `render_top50.py` now recovers
each signature group and prints *"N equal swaps — same score, pick on interest"* under the slot.
**59 slots across the top 50 turned out to be interchangeable.**

Worked example, #1's YCE1253 slot — all score **21.80**, model indifferent:
YCE1253 서양문명 · YCI1704 Russian Culture and Art · MAT1001 Calculus & Vector Analysis(1) ·
YCK1998 Distinguished Professor Course.

**General lesson:** an optimiser that collapses equivalence classes must say so at output, or
the reader mistakes a representative for a recommendation.

## R159. ⭐ ECO1101 IS 월수 IN FALL, BUT A 화목 SECTION HAS APPEARED IN BOTH RECORDED SPRINGS
Iden asked whether ECO1101's Monday meeting is structural or incidental. Checked against every
semester in `mileage_history.json`:

| semester | section | time | days | campus |
|---|---|---|---|---|
| Fall 2024 | -05 | 월9,10/수9 | 월수 | 국제 |
| **Spring 2025** | **-05** | **화4/목5,6** | **화목** | **국제** |
| Spring 2025 | -06 | 월7,8/수8 | 월수 | 국제 |
| Fall 2025 | -05 · -06 | 월7,8/수8 · 월9,10/수10 | 월수 | 국제 |
| **Spring 2026** | **-05** | **화2,3/목1** | **화목** | 신촌 |
| Spring 2026 | -06 | 월7,8/수8 | 월수 | 국제 |
| Fall 2026 | -05 · -06 | 월7,8/수8 · 월9,10/수10 | 월수 | 국제 |

**Every Fall on record: 월수 only. Both Springs on record: one 월수 + one 화목 section.**

Consequence for the deferral question. Taking ECO1101 this Fall **certainly** costs the free
Monday — the trip run collapses 4 → 3 (34.3 → 13.0) plus the lost rest day, ≈ **−28**, against
its **+8** role. Deferring to a Spring has, 2 for 2, offered a 화목 section that would drop into
the existing 화/목 load at **no schedule cost at all**.

⚠️ **n = 2 Springs.** The Fall/Spring split is clean but the sample is tiny, and the Spring-2026
화목 section was at **신촌** (fine from 2학년, R143). Treat as a strong prior, not a guarantee —
and note it is the *opposite* of the "take required courses as early as possible" instinct.
This is the first case where a course's **term-by-term timetable history**, not just its
existence, changes the decision. Nothing in the model uses that signal yet.

## R160. ✅ RUN_EXP SENSITIVITY CLOSED — it cannot change the top of the ranking. D-2 dies.
Promised to Iden as B-7: test whether the unpinned trip-curve exponent matters before asking
him about it again. Ran the ranker at both ends of the bracket:

| RUN_EXP | #1 score | #1 postpones | best MR-deferral | **gap** |
|---|---|---|---|---|
| **1.4** | 21.795 | Lang | 21.065 | **0.730** |
| **1.2** | 17.354 | Lang | 16.624 | **0.730** |

**The gap is identical to three decimals.** Both contenders have the same free-day shape (월금),
so the trip term is a *common* term and cancels exactly in the comparison. `RUN_EXP` rescales
every 월금 timetable together and cannot reorder them.

⇒ **D-2 is dead. Iden never has to answer it.** He said *"can't quantify tbh"* and he was right
not to bother. It stays [P] at 1.4 and that is fine, with one caveat: it *does* move the gap
*between* free-day shapes (월금 vs 월수금), so if the top ever stops being all-월금 it must be
re-tested. Guard: **if the top 50 contains more than one free-day shape, re-run this.**

This is the pattern worth keeping — **test whether an unknown matters before spending the
user's effort resolving it.**

## R161. 📊 WHAT THE 5000 ACTUALLY CONTAINS — 84% is one family, 49% is duplicate rows
Iden 2026-08-07: *"What's your take on the 5000"*. Measured rather than opined.

| | |
|---|---|
| rows | 5000, scores 21.80 → 5.37 |
| **distinct course-sets** | **2553 — 49% of the file is duplicate rows** |
| **largest single family** | **4196 rows (84%) = 월금 + postpone QRM입문** |
| distinct (shape × deferral) families | **12** |

Best of each family — the only genuinely distinct choices in the file:

| free days | postpones | best | rows |
|---|---|---|---|
| **월금** | **Lang** | **21.80** | 93 |
| **월금** | **MR** | **21.07** | 4196 |
| 월금 | WCiv | 15.19 | 132 |
| 월수금 | MR | 17.19 | 448 |
| 금 | MR | 9.38 | 50 |
| 월금 | **nothing** | 7.34 | 20 |
| 월금 | SciRD | 6.20 | 12 |

### Three findings
1. **The whole 5000 reduces to one question worth 0.73 points** — postpone Chinese (21.80) or
   postpone QRM입문 (21.07). Everything else is 4+ points back. And R160 shows 0.73 survives
   the entire `RUN_EXP` bracket unchanged, while `REST`'s own bracket (6–8) is worth ±1 —
   **so the model cannot actually distinguish the top two options.** They are a tie.
2. **A sanity check passed that I did not construct.** 월수금 — *three* free weekdays — tops out
   at 17.19, **below** 월금's 21.80. Correct under R129: Wednesday is isolated, so it earns REST
   but no TRIP, while degrading the packing of the two remaining campus days. Three free days
   being worth less than two is exactly the behaviour the dorm model predicts.
3. **Deferral is not really an open choice.** SciRD 6.20 · LHP 8.71 · nothing 7.34 are all far
   back. Only **MR and Lang** are live, WCiv marginal at 15.19.

### ⇒ TOPN=5000 is the wrong artifact
It was a proxy for coverage. What registration day needs is **the best of each family plus its
interchangeable alternates** (R158) — roughly 12 rows and their swap sets, not 5000 near-copies.
Logged as the shape `PLANS.md` §A (Plan B / click order) should actually take.

## R162. ✅ ONLY ONE PER-COURSE BONUS IS LIVE — chapel +10. Two dead dicts removed.
Iden 2026-08-07: *"is there anything in our model that gives bonus to individual courses"* —
a check against his own standing rule (R64/R66/R69/R137: value the **mechanism**, never the
course). Audited all three `BONUS`-shaped constants in the tree:

| where | contents | live? |
|---|---|---|
| `rank.py BONUS` | ECO1101 +10 · ECO1103/1104 +5 · STA1002 +5 | ❌ **dead** — imported into rank2 as `_B` and never applied |
| `rank2.py BONUS` | UIC1805/1806 +8 (language) | ❌ **unreachable** — see below |
| `rank3.py CHAPEL_BONUS` | **+10** | ✅ **LIVE** |

**The language +8 is unreachable, and that is correct.** `rank3` pulls language sections out of
`ELEC` into `REQ['Lang']` and scores them as a **requirement slot**; the elective-bonus line is
only reached by `ELEC`. Verified on the live pool: **0 of 303 elective sections** receive a
non-zero `BONUS`. This is exactly what R119 intended — the +8 and the −16.97 deferral cost are
one logic, not two — but the constant survived the fix and looked live.

**Both dead dicts emptied** so they cannot silently re-activate. If `rank.py BONUS` were ever
applied, ECO1101 would receive **+10 on top of ROLE_MR +8** — precisely the per-course thumb
Iden's rule forbids, and it would have been invisible.

**So the answer is: one.** Chapel +10, which is a *deliberate* exception (R127 — Iden stated it
as intrinsic desirability, *"chapel is pretty desirable in itself"*, and R127 kept it on the
preference side of the line on purpose). Everything else that looks per-course is category
machinery: `ROLE_MR/ME/SEMINAR` by **pool scarcity** (R149), the year gap by **chart year**.

⚠️ `test_weights.py` had been asserting `R2.BONUS['UIC1805'] == 8` — **a test guarding a
constant nothing consulted.** Retired and replaced by the claim that matters: the total number
of live per-course bonus entries is **0**, and `CHAPEL_BONUS` is 10. **23/23.**

**Third instance today of the same failure mode** (after R157's `run_value` and the stale
`defer2_check` incumbent): superseded values left resident in the tree, looking authoritative.
The rule that keeps falling out — **delete or disable superseded values; do not merely stop
calling them.**

## R163. Display: professor names, full section codes, and TWO distinct kinds of alternate
Iden 2026-08-07: *"the display only shows the course codes, but I would like to know the
professor's name/the full code. If there's multiple at the same time (same course, different
prof, same time), I would like to know that too."*

`canonical_2026F.json` already carried the professor in field **`p`** (present on 710 of 712
sections) — it had simply never been rendered. Now shown, along with the full 학정번호-분반,
and in the grid tooltip.

**The second request turned out to be a genuinely different object from R158's swaps**, and the
output now separates them because they mean different things on registration day:

| | what | why it matters |
|---|---|---|
| **other 분반, same time** (**24** slots) | *same* course, *same* hours, different professor | a **professor choice** — and a **fallback**: if one 분반 is full at 09:00 on 8/25, another may not be |
| **equal swap** (**86** slots) | *different* course, same slot, identical score | the model is **indifferent** — pick on interest (R158) |

Keyed on `(course code, time mask, presence mask)`, not on the display string, so it is exact.
**56 such groups exist across the 국제 pool**; 24 land inside the top 50.

⚠️ **This is the first piece of Plan-B machinery to exist.** `PLANS.md` §A wants per-slot
fallback chains for 8/25; the "other 분반" list is exactly that, for the subset of fallbacks
that cost *nothing* — same course, same hours, so the timetable is unchanged and the score is
identical. Those should be the first fallback tried before any that alter the grid.

## R164. ⭐⭐ LANGUAGE × CAMPUS × TIMETABLE × KOREAN-CAP — a four-way interaction, unmodelled
Iden 2026-08-07: *"if I were to take [ECO1101] in the 신촌 semester, and if I were to take it in
English, it lands in a very bad timetable placing."* **Correct, and it is worse than a placing
problem — it decides the shape of the whole 신촌 semester.**

### The three 신촌-side MR courses, Fall 2026
| course | ENGLISH sections (dept 1013 = 언더우드국제대학) | KOREAN sections (dept 0201 = 상경대학) |
|---|---|---|
| **ECO1101** | **04 · 월1,2/수2 — 월수 AND a 9am start** *(only one)* | 01 화8,9/목7 · 02 화2,3/목1 · 03 수1/금1,2 |
| ECO2101 | 05 **화5,6/목4** · 06 월3,4/수4 · 03 월3,4,수4 | 01 화4,목5,6 · 02 화1,목2,3 · 04 월1,2/수2 |
| ECO2102 | 01 **화5,6/목4** · 02 **화8,9/목7** · 05 월5,6,수6 | 03 수1,금1,2 · 04 화1,목2,3 |

**The problem is specific to ECO1101, not general.** Macro and Micro both have good English 화목
sections. ECO1101's *only* English section at 신촌 is 월1,2/수2 — it puts class on Monday **and**
starts at 9:00, the −10 anchor.

### Enumerated: can a 신촌 semester carry all three on 화/목 only?
| campus days | 9am starts | English | how |
|---|---|---|---|
| **화목** | **0** | 1 of 3 | ECO1101-01 **KR** 화8,9/목7 · ECO2101-01 **KR** 화4,목5,6 · ECO2102-01 EN 화5,6/목4 |
| 월수 | 1 | **3 of 3** | ECO1101-04 · ECO2101-06 · ECO2102-05 |
| 화목 | 1 | 1 of 3 | ECO1101-01 KR · ECO2101-05 EN · ECO2102-04 KR |

**A perfect 화목 신촌 semester — 월+금 free, zero 9am starts — exists, but requires taking two
of the three in Korean.** Insisting on all-English forces 월수 *and* a 9am start, i.e. it costs
the Monday free day outright.

### ⚠️ And the Korean sections are not free either — they eat the 12-credit cap
English sections are **dept 1013 (언더우드국제대학)**; Korean ones are **dept 0201 (상경대학)**.
R105/R152's cap — *"only up to 4 courses (12 credits)"* of Korean 상경대학/응용통계 courses may
count as **Major Credits** — therefore applies to the Korean ones. Two Korean MR courses consume
**6 of the 12**, leaving 6 for everything else including ME.

**So the real trade is:** English = no cap consumption but a wrecked 신촌 week; Korean = a clean
화목 week but half the Korean allowance spent on MR before any ME is taken.

### The gap this exposes
HANDOFF §1 records *"Language of instruction (Korean vs English) does not matter to Iden"* —
true as a *preference*, and irrelevant, because language is not acting as a preference here. It
is acting as a **selector over sections**, and through the section it selects campus day,
start time, offering department and cap consumption at once.

**The model sees none of it.** `canonical_2026F.json` is 국제-only and single-semester; every
figure above was hand-queried from `raw_2026F.json`. Generalises R159: the four-year layer needs
per-course **(term × campus × language × department × time)** availability, not just "does this
course exist". That is the same missing signal, one level bigger.

## R165. ⭐⭐⭐ THE RISK TERM FLIPS THE #1 — defer QRM입문, not Chinese
Iden 2026-08-07: *"if you just look at this semester, the weights are placed correctly. But
when you really think about the future… I'm not entirely sure."* Tested rather than reassured.

### First result: the four-year layer does NOT move the top two apart
| | #1 defer Chinese (21.80) | #2 defer QRM입문 (21.07) |
|---|---|---|
| Fall 2026 clears | QRM1001 · WCiv | WCiv · Language |
| the one 국제 Spring must carry | Language · QRM3003 | QRM1001 · QRM3003 |
| items in the receiving semester | **2 of 6** | **2 of 6** |
| crowding cost there (R148) | −14.00 | −14.00 |
| chart year of the deferred item | **1** | **1** |
| year gap when it lands (R146) | identical | identical |

**Every four-year term is symmetric and cancels.** The 0.73 gap is untouched by the gaps in
§8. Iden's unease is right about the *model* and wrong about *this decision* — on the terms
that are modelled.

### Second result: ⚠️ THE ONE THING THAT IS **NOT** SYMMETRIC — and it reverses the order
**R130 exempted Iden from the mileage round only as a 1학년.** From 2학년 he *is* in it, so the
competition data starts applying to him — **for anything he defers.**

| deferred course | 정원 | 배율 across 4 semesters | oversubscribed |
|---|---|---|---|
| **QRM1001** (what #2 defers) | **58–80** | 0.44 · 0.53 · 0.88 · 0.98 | **0 of 4** |
| **UIC1805 Chinese** (what #1 defers) | **2–18** | 0.94 · 1.00 · 1.17 · 2.00 · 2.00 · 3.00 · 3.00 | **5 of 7** |
| UIC1806 Japanese (the fallback) | **2** | 1.00 – 5.50 | **7 of 8** |

**Deferring Chinese defers a course that is oversubscribed 5 times out of 7, with 2-seat
분반 and average winning bids of 14–28 mileage. Deferring QRM입문 defers a course that has
never once been oversubscribed, with 78 seats.** The language requirement is the scarcest
thing on Iden's whole remaining list; Intro to QRM is among the most abundant.

⇒ **#1 (defer Chinese) buys 0.73 points of weekly comfort and pays for it with the single
riskiest deferral available.** Under any risk weighting above roughly zero, **#2 wins.**

### Why the model cannot see this
`RISK` is `MODEL.md` §8.2 — logged as unbuilt all session, never quantified. This is the first
case where it does not merely refine the ranking but **reverses it**, and it took a direct
question from Iden to surface. **Consequence: B-4 (risk) is promoted above every other
outstanding item**, and no ranking should be treated as final until it exists.

⚠️ Note this is *not* the R130 error repeating. R130 says mileage 배율 says nothing about a
**1학년's** access on 대기순번제 — true, and still true for Fall 2026. R165 is about the
**2학년+ rounds**, where Iden is a bidder and the same numbers describe exactly his race.

## R166. ⭐⭐ THE LANGUAGE POOL IS 5× BIGGER THAN THE MODEL ALLOWS — D-3 was a preference
Iden 2026-08-07: *"UIC's language requirement isn't necessarily restricted to language offers
from its department (Chinese and Japanese). I can take language from any other department. And
any language I can take (except Korean and English). The tradeoff is that those are really
learning the language, pretty hard. The courses we were originally aiming are 'Beginning
Chinese, Beginning Japanese' and are much easier."*

**Confirmed verbatim in the QRM graduation table, footnote 1:** *"Students admitted in 2022 and
thereafter should take 1 course from Language & Arts courses in UIC **or 1 course from Non-UIC
language courses**."*

The model has `LANG = {'UIC1805','UIC1806'}` — **4 sections**. That came from **D-3**, Iden's
own 2026-08-05 restriction, which was recorded as if it were a rule. It was a **preference for
the easier courses**. R56 had already measured the true pool at 83 sections and the restriction
was applied anyway.

### Level-1 language courses at 국제 this Fall (sequels excluded per R112/R122)
**10 courses · 20 sections**, of which **10 sections keep 월+금 free**:

| tier | courses | 화목 sections (preserve 월+금) |
|---|---|---|
| **EASY** — UIC "Beginning" | UIC1805 Chinese · UIC1806 Japanese | **4 of 4** |
| **HARD** — 언어와표현 | YCF1301 Chinese · 1351 Japanese · 1451 German · 1501 French · 1551 Russian · 1601 Latin · 1603 Spanish · 1607 Italian | 6 of 16 (YCF1301-07/08 · 1501-03 · 1551-05 · 1603-04 · 1607-02) |

### What this does to R165 — it **sharpens** the conclusion rather than reversing it
R165 argued: don't defer Chinese, it is oversubscribed 5 of 7 semesters. With the wider pool,
"cannot satisfy the language requirement" is no longer the risk — there are 10 entry points.
**The risk is narrower and worse:**

- The **easy** tier is exactly the contested one (2-seat 분반, avg winning bid 14–28 mileage).
- It is **cheapest to obtain right now**: Beginning Chinese/Japanese are *meant for freshmen*
  (Iden, R130), and this Fall he registers on 대기순번제 with freshman seats. From 2학년 he is
  bidding mileage against those same 2-seat 분반.
- Deferring therefore means **either** fighting for the easy tier as a 2학년, **or** taking a
  genuinely hard language later.

⇒ **Three independent arguments now point the same way: take the language NOW, defer QRM입문.**
That is family **#2 (21.07)**, not #1 (21.80). Scarcity (R165) · access-timing (this rule) ·
and the GPA loop (R153 — a hard language course in Fall 2026 is a risk in the one semester that
gates the double major, whereas in a later semester it is not).

### ⚠️ Actions
1. **The `LANG` pool must be widened** to the 10 level-1 courses, with the easy/hard tier
   carried as an attribute. **Not done** — it changes the requirement pool and needs Iden's
   difficulty weighting, which does not exist (the model has **no difficulty axis**, R153).
2. **D-3 must be re-labelled** from a rule to a preference in `RULES.md`. It has been silently
   narrowing the search for three days.
3. Second time today that **difficulty** turned out to be decision-relevant (after R153). It is
   the largest single thing the model cannot represent.

## R167. Session close 2026-08-07 — handoff written, four factors scoped
Iden paused the session to return ~08-10 and prepare *"a big project update encompassing these
different factors."* `HANDOFF_2026-08-07.md` written; `INDEX.md` points at it first;
`DECISIONS_NEEDED.md` stamped with what closed today.

**The four factors, in the order they should be built** (handoff §2):
**A risk** (already reversed an answer, R165) · **B difficulty** (decision-relevant twice,
representable zero times) · **C availability across term × campus × language × dept × time**
(R159/R164, both hand-queried) · **D quota enforcement** (priced, not enforced).

**Standing recommendation to carry forward: family B — take the language now, defer QRM입문.**
It scores **0.73 lower** and wins on three things the score cannot see. Anyone presenting the
21.80 as "the answer" has dropped R165 and R166.

**Session shape worth recording.** Almost every substantive correction today came from Iden
pushing on something that looked settled — the online Wednesday (R129), the four-year layer
(R143), the two-sided year penalty (R145), "does the code match" (R157), "any per-course
bonuses" (R162), and the language pool (R166). The model's biggest single error — pricing
*commutes* for someone who lives in the dorm — had survived four sessions of internal checking
and fell to one sentence from him. **The checks that work are the ones that come from outside
the model's own frame.**

## R168. ⭐⭐⭐ DESIGN v2 — the four factors are one data layer, one mechanism, one consequence
Iden 2026-08-09 chose *"design all four together first"* over building risk end-to-end. Correct
call: R117 and R129 were both caused by fitting pieces separately and finding later they were
one thing. `DESIGN_v2.md` written; nothing built.

### The collapse
| named factor | what it actually is |
|---|---|
| **availability over time** | **not a factor — the state space.** Data, no weight, nothing to elicit. Everything else consumes it. |
| **risk** | P(acquire a section at a registration) |
| **quota enforcement** | **the same mechanism aggregated** — P(finish a pool) is derived from per-attempt risk over the availability landscape, not separately specified |
| **difficulty** | the only genuinely separate object: a cost *given* success, and the only one with a **feedback edge** (→ GPA → double-major admission and the +3-credit cap) |

### ⚠️ The consequence that matters most
**The risk mechanism SUBSUMES both `ROLE` (R149) and the `DEFER` table (R117).** Both are static
proxies for "how hard will this be to complete later" — `ROLE_MR = 8.00` precisely because MR's
supply exactly equals its need, i.e. **zero slack**, which is a feasibility statement wearing a
preference's clothing. **Adding risk alongside them double-counts.** This is the single most
likely way to repeat R117 and it is now written down before any code exists.

### The object of choice changes — and Plan A and Plan B turn out to be one thing
With acquisition risk there is no "choose a timetable"; on 8/25 Iden chooses an **order of
attempts with fallbacks** — a policy. `PLANS.md` has tracked Plan A (the ranking) and Plan B
(click order + fallbacks) as separate work items since session 1. **They are the same object;
the ranking is the policy's first branch.**

**Measured today, which sharpens it:** free fallbacks barely exist. Of the top 50, **26 have
zero** same-course/same-time alternates and 24 have exactly one; none has two. **#1 has zero.**
So fallbacks are *not* free — nearly every real one changes the grid and costs score. Listing
alternates (R163) is not enough; degraded branches must be **scored and probability-weighted**.

### Objective
`value of a plan = E[utility over acquisition outcomes]`, utility of a realised semester being
the existing score. **Robustness and quota-completion then need no new terms** — they fall out.
That three separate things drop out of one formulation is the test that the decomposition is
right. ⚠️ v2 scores will be **lower and not comparable** to today's 21.80; flag at switchover.

### Sequencing
Buildable now: the availability table · deferred-side risk (regime 2, `mileage_history.json`) ·
the difficulty-carrier test. Blocked to **8/15**: Fall-2026 risk. Out of reach before 8/25: a
full stochastic DP — a two-stage approximation is the honest cut.

**Iden owes exactly two things, and neither is askable yet**: the difficulty tier (only after a
carrier exists) and risk appetite. Asking before the mechanism exists produces answers that get
thrown away — R136/R137/R141.

## R169. ✅ DIFFICULTY IS NOT A GLOBAL AXIS — it is one within-pool question, and only one pool has it
`DESIGN_v2.md` §3 said the difficulty *carrier* had to be designed before Iden could be asked
anything. Three candidates tested; two are dead and the third collapses the problem.

### Candidate 1 — course level (the 1000/2000/3000 digit) ❌ DEAD
Tested against QRM's chart year across all 35 mapped courses: **34 of 35 agree (97%)** — only
ECO1105 differs, and by one. **Level and chart year are the same signal**, so adding level as a
difficulty carrier would **double-count the early arm of the 학년 gap** (R145). Exactly the
R119 failure mode, caught before building rather than after.

### Candidate 2 — grading scheme (`grade`, already in the data) ❌ DEAD, but a clean null
`상대평가` (curved) is a real GPA-risk signal and costs **zero elicitation**. Measured:

| campus | 절대평가 | P/NP | **상대평가** |
|---|---|---|---|
| 국제 | 569 | 121 | **27** |
| 신촌 | 626 | 114 | **43** |

But the 27 curved 국제 sections are **AST1003 · BIO1012 · CHE1001/1002/1011/1012 · POL1004** —
science general-ed and one politics course. **None is in any of Iden's pools**, and none appears
anywhere in the top 50. The signal exists, is free, and **does not discriminate in his choice
set**. Recorded so nobody spends time on it again; re-check if the SciLit path ever revives
(R113 declared it dead).

### Candidate 3 — tier within a pool ✅ AND IT SHRINKS THE PROBLEM
Difficulty only needs modelling where a pool's options come from **different course families** —
if every option is the same kind of course, they are comparable and no attribute is needed.
Tested on every live pool:

| pool | sections | families | |
|---|---|---|---|
| MR · WCiv · LHP · SciRD · Chapel | 1 · 1 · 16 · 14 · 2 | one each | homogeneous |
| Lang **as currently modelled** | 8 | 언더우드국제대학 only | homogeneous |
| Lang **widened per R166** | 20 | **UIC "Beginning" (4) + 대학교양 언어와표현 (16)** | ⚠️ **heterogeneous** |

**Every pool is homogeneous except the language one — and only after R166 widens it.**

⇒ **Difficulty is not a global axis. It is a within-pool substitution question, and it currently
arises in exactly ONE pool.** That turns "rate 700 courses" — which R137 forbids and which was
the main obstacle in `DESIGN_v2` §3 — into **one question for Iden**, about one tier boundary he
has already described in his own words (*"much easier"* vs *"really learning the language,
pretty hard"*, R166).

⚠️ **This is contingent, not permanent.** It holds because the other pools happen to be single-
family *right now*. Re-run the homogeneity test whenever a pool is widened — the 신촌 pools were
never tested, and R164 already showed ECO1101's English and Korean sections come from different
departments with different consequences.

## R170. ⚠️ R159 IS NARROWED — "ECO1101 is 월수 every Fall" was true only of 국제/English
`build_availability.py` (DESIGN_v2 §1) reproduced R159 automatically **and immediately
contradicted half of it.** R159 measured Fall/Spring day patterns from `mileage_history.json`,
which is **overwhelmingly 국제**. Once the 783 신촌 sections in `raw_2026F.json` are included:

**Fall 2026, ECO1101, all six sections:**

| campus | lang | time | days |
|---|---|---|---|
| 국제 | EN | 월7,8/수8 | 월수 |
| 국제 | EN | 월9,10/수10 | 월수 |
| 신촌 | EN | 월1,2/수2 | 월수 · **9am** |
| 신촌 | **KR** | 수1/금1,2 | 수금 |
| 신촌 | **KR** | 화8,9/목7 | **화목** |
| 신촌 | **KR** | 화2,3/목1 | **화목** |

**화목 ECO1101 exists in Fall — it is 신촌 and Korean.** R159's "defer it to a Spring to get a
화목 section" was reasoning from a 국제-shaped sample. The real structure is R164's:
**English selects 월수; Korean selects 화목.** Term was a proxy for the thing that actually
varies, which is language×campus.

**R159 is narrowed, not withdrawn** — its Spring 화목 observations stand, and it remains true
that *at 국제* every recorded Fall is 월수. But the recommendation built on it was too strong.

### Why this matters beyond ECO1101
This is the first output of the availability table and it corrected a hand-derived rule on its
first run. **The table also flags 8 more courses whose day pattern varies by term** — ASP2033 ·
ECO1103 · ECO1104 · UIC1251 · UIC1401 · UIC1551 · UIC1751 · UIC2151 — none of which anyone had
looked at. Each is a place where "defer it, the timetable may be better later" might or might
not hold, and until now there was no way to tell.

⚠️ **Standing correction to method:** `mileage_history.json` is not a neutral sample of the
world. It covers 21 course codes and is 131 국제 / 11 신촌. Any claim of the form *"course X is
always Y"* drawn from it is a claim about **국제 sections of X**, not about X. Same class of
error as R130 — right data, wrong population, third instance.

## R171. ⭐⭐⭐ RISK IS A BUDGET CONSTRAINT, NOT A SCORE TERM — and it needs nothing from Iden
`DESIGN_v2.md` §2 built. The design decision that matters is not obvious and it removes an
elicitation nobody had noticed was coming:

**마일리지 is not a cost Iden feels — it is a budget he cannot overspend.** He gets **76** as a
1학년 and **72** from 2학년 (제도안내 대학별 마일리지 table), max **36** on one course and never
36 on two. Spending 30 on a contested course is not a "penalty"; it is 42% of a budget that then
cannot buy anything else.

⇒ **risk enters as FEASIBILITY, not as a weighted term:**
> a future semester is affordable ⟺ Σ required bids ≤ 72

**This needs no preference from Iden at all.** `DESIGN_v2` §8 listed "risk appetite" as one of
two things he still owed. **It is now one — the other has dissolved.** A plan whose backlog
cannot be bought is excluded, not discounted, and exclusion needs no weight.

### ⚠️ What the data can and cannot say (R116, sharpened)
`avgMlg` is the average bid of everyone who **applied**, not the winning cutoff; `minMlg` is the
lowest bid among applicants, also not the cutoff. **The true price is unknowable from this
feed.** Every figure is therefore a **bracket**, planning for the worst recorded term (R6):
`배율 ≤ 1` ⇒ cost 1 (everyone fits) · `배율 > 1` ⇒ cost between `avgMlg` and `min(36, maxMlg)`.

### The deferral question, in the units that actually bind
| defer | mileage cost | share of a future semester's budget |
|---|---|---|
| **Intro to QRM** | **1.0 – 9.5** | **1–13%** — never oversubscribed in 4 terms |
| **Chinese** | **17.7 – 36.0** | **25–50%** |
| Japanese (the fallback) | 34.0 – 36.0 | **47–50%** |

**R165's conclusion survives and is now quantified in the right currency.** Deferring Chinese
consumes a quarter to a half of a future semester's entire mileage budget; deferring QRM입문
consumes almost none. Japanese is worse still — half the budget, oversubscribed 7 terms of 8.

### Also visible for the first time
**UIC2151 (SciRD, 32 observations) costs 31.6–36.0 — 44–50% of the budget.** It sits in *every*
top-50 timetable. It is currently being taken **now**, which is free (대기순번제), and that turns
out to be worth far more than the model knows. Same for UIC1351/UIC1401 at 41–50%.

### ⚠️ Coverage — the honest limit
21 courses have evidence. **16 required or candidate courses have none** — QRM3003 · QRM3004 ·
QRM3005 · ECO2101 · ECO2102 · STA2102 · QRM2004 · QRM2102 and all 8 widened-language courses.
Every one is 신촌, Spring-only, or from R166's widened pool. **So the full budget check cannot
yet be run on a real future semester.** It can compare the two live deferral options, which is
what the 8/25 decision needs — and nothing more should be claimed from it.

**Does NOT yet replace `ROLE`/`DEFER`.** That swap is the next step and must be done in one
move, not alongside them (R168).

## R172. ⛔ R168 WAS WRONG — risk does NOT subsume ROLE. They are orthogonal.
`DESIGN_v2.md` §2 and R168 both asserted, in bold, that the risk mechanism **subsumes** the
pool-value formula (R149) and the deferral table (R117), and that adding risk alongside them
would double-count. **Tested before swapping, and the claim is false.** Caught at
implementation, which is the only reason the substitutability signal still exists.

| course | substitutability (ROLE) | competition (mileage) |
|---|---|---|
| **QRM1001** — MR, 1 section, no alternative | **1.00 — no substitutes** | **1–10** (1–13% of budget) |
| **UIC1561** — WCiv, 1 section, no alternative | **1.00 — no substitutes** | 8–36 (12–50%) |
| **UIC2151** — SciRD, 14 sections | **0.07 — highly substitutable** | **32–36 (44–50%)** |
| UIC1551 — LHP, 16 sections | 0.14 — substitutable | 14–31 (20–43%) |

**QRM1001 has no substitutes but is cheap. UIC2151 has fourteen substitutes but is the most
contested course on the list.** The two measures rank them in opposite orders.

### They are two different failure modes
- **substitution risk** — there is *no other way* to fill this requirement
- **competition risk** — there *are* other ways, but everyone wants them

Swapping as designed would have **deleted the substitutability signal**, leaving the model blind
to single-section requirements — exactly the courses it must never drop. The correct structure
combines them: a requirement is safe when it has **many options AND those options are winnable**;
it is at risk when either fails.

### Why the design got it wrong
R168 reasoned that `ROLE_MR = 8.00` "because MR's supply exactly equals its need, i.e. zero
slack, which is a feasibility statement wearing a preference's clothing." That much is right.
The error was concluding that *because both are feasibility statements, they are the same
feasibility statement.* **Two things can both be about feasibility and still be independent** —
here, one is about the existence of alternatives and the other about winning any given one.

⚠️ **This is the mirror image of the session's other lesson.** R129/R146 collapsed things that
looked separate and were one. This is something that looked like one and is two. **The test is
the same either way: check whether they rank the same cases in the same order — do not reason
about it from the definitions.** R119 (language +8 vs −17) collapsed correctly; R127 (chapel
bonus vs deferral cost) stayed separate correctly; both were settled by looking, not arguing.

`DESIGN_v2.md` §2 corrected in place. **No swap performed.** `ROLE` and `DEFER` stay; risk is a
third, independent axis.

## R173. 🔍 THIRD-PARTY MATHEMATICAL AUDIT — three claimed validations are not validations
Iden 2026-08-09: *"look at what we've built at a third person's view, and apply mathematics to
see if everything logically checks out."* Six checks run. **The model's behaviour survives; three
of its stated JUSTIFICATIONS do not.**

### ⛔ 1. The `MODEL.md` §2 "cross-check" is vacuous
Claimed: *"13.00 and 4.333 satisfy both today's 'free Friday = two 9am starts' and the older
'월 = 금의 75%'. Two elicitations months apart, no drift — the only independent check available
on §2, and it passed."*

Written as a system: **3 unknowns** (REST, DAY_CONTIG, FRI_EVENT), **2 equations**
(`DC + REST = 20`; `DC/(DC+FE) = 0.75`). **One degree of freedom**, closed by *choosing*
REST = 7. Verified: **both equations hold for every REST in (6,8)** —
REST=6→(14.00, 4.667), 7→(13.00, 4.333), 8→(12.00, 4.000), all exact.

**The system is under-determined, so there is no residual and nothing could have failed.**
It is a solved system reported as a passed test. ⚠️ A *real* consistency check does exist
nearby and did pass: R140's E3 (REST < 10) and E6 (REST < 8) independently bound REST above and
agree. That is the check; the DAY_CONTIG/FRI_EVENT relation is not.

### ⛔ 2. `ROLE`'s "the formula validates itself" is circular
`ROLE = BASE × ratio`, and R149 set `BASE = 8` *to match Iden's elicited* `ROLE_MR`. With
ratio_MR = 1.00 it returns 8 — **by construction**. Had ratio_MR been 0.5, BASE would have been
set to 16 and it would still have "reproduced" 8. One equation, one free parameter.
✅ **The structural fact underneath is real and non-trivial**: ratio_MR = 1.00 computed from
independent data means MR has *exactly zero slack*. The claim is true; the validation is not.

### ⛔ 3. The `late` arm of the 학년 gap is UNREACHABLE
`MODEL.md` §3 presents a two-sided table (late = −2.67 / −15.08 / −41.57) as live.
`YEAR_PEN = lambda y: year_gap_pen(1, y)` — `taken_in_year` is **hardcoded to 1**, so
`gap = 1 − chart_year ≤ 0` always and **only the early arm can ever fire.** R146 built the late
arm as the principled replacement for the deferral table; R156 found the swap was never done.
**Both remain true and the documentation still describes the unreachable half as live.**
The deferral cost is carried entirely by R117's fitted table.

### ⚠️ 4. `W_DINNER` breaks the symmetry it was derived from
`W_LUNCH = −6` was **fitted knowing MARATHON co-occurs** ("lunch+marathon=13.75").
`W_DINNER = −8` was set *"by symmetry with lunch"* from Iden's *"slightly bigger than lunch"*.
But the two are **not symmetric in what they co-trigger**: a 3-hour dinner block (9,10,11)
always also fires `LATE` (11 ≥ 9), while a 3-hour lunch block (3,4,5) fires nothing else.

| block | model charges |
|---|---|
| 3,4,5 over lunch | **−6.00** (lunch alone) |
| 9,10,11 over dinner | **−12.82** (dinner −8 + LATE −4.82) |

Iden said *slightly* bigger — a 1.33× gap. **The model delivers 2.14×.** Not a bug in either
constant; a bug in transferring "by symmetry" across two situations with different co-triggers.

### ⚠️ 5. Uncertainty is never propagated
REST is a bracket (6,8) and `DAY_CONTIG = 20 − REST` **inherits it**, as does every trip value.
With `RUN_EXP`'s own [1.2, 1.6] bracket, a 월금-free week is worth anywhere in
**47.6 – 59.1**. The model reports **57.7**. Every figure in `MODEL.md` is a point estimate of
a quantity with a known interval, and nothing downstream carries the interval.

### ✅ 6. …AND NONE OF IT CHANGES THE DECISION
Perturbed every questionable constant to both bracket ends, singly and jointly:

| perturbation | A (defer Chinese) | B (defer QRM입문) | **gap** |
|---|---|---|---|
| baseline | 21.80 | 21.07 | **0.73** |
| REST 6 / REST 8 | 23.77 / 19.82 | 23.04 / 19.09 | **0.73** |
| RUN_EXP 1.2 / 1.6 | 17.35 / 26.90 | 16.62 / 26.17 | **0.73** |
| W_DINNER −6 / −3 | 21.80 | 21.07 | **0.73** |
| all three at once, both extremes | 18.99 / 24.53 | 18.26 / 23.80 | **0.73** |

**The gap is invariant to three decimal places in every case**, because both candidates share a
free-day shape and a dinner/late profile, so every perturbed term is common and cancels.

⇒ **the model is far more robust than its justifications are sound.** What actually decides
A vs B is mileage cost and access timing (R165/R166) — neither of which is in the score at all.

## R174. ✅ AUDIT FIXES — and the dinner asymmetry is REAL but INERT, so it stays unasked
Acting on R173. Four documentation corrections applied to `MODEL.md`; one modelling issue
tested and deliberately **not** escalated to Iden.

### Fixed in place (no input needed — these were false claims, not open questions)
1. **The §2 "cross-check"** — withdrawn, with the algebra shown and the *real* check named
   (E3 and E6 independently bounding REST above, and agreeing).
2. **`ROLE` "validates itself"** — withdrawn as a validation; the underlying structural fact
   (MR has exactly zero slack) restated as what is actually true.
3. **The late arm** — now marked unreachable, with the reason (`taken_in_year` hardcoded to 1)
   and the condition for it becoming live (the four-year layer, not before).
4. **Uncertainty** — the 47.6–59.1 interval for a 월금 week is now stated, together with the
   fact that it does **not** affect ordering.

### ⚠️ The dinner asymmetry: measured, and it never fires
R173 found `W_DINNER = −8` was set *"by symmetry with lunch"* but always co-triggers `LATE`,
turning Iden's *"slightly bigger"* (1.33×) into **2.14×** in practice. Before asking him:

| penalty | timetables (of 5000) triggering it |
|---|---|
| **no dinner (9·10·11 all busy)** | **0 — 0.0%** |
| late finish (ends 9교시+) | 4800 — 96.0% |
| no lunch | 1066 — 21.3% |

**The dinner penalty fires in zero of five thousand timetables.** Nothing Iden can build at 국제
this Fall has classes at 9, 10 *and* 11. The asymmetry is real and the reasoning that produced
it was faulty, but the constant is **inert**.

⇒ **Not asked.** Logged as a latent bug with a trigger condition: **re-open if the pool ever
widens to a 신촌 semester**, where evening sections are common — R164 already showed the 신촌
side has a very different time distribution.

**This is the discipline R160 established, applied a second time: test whether an unknown can
change anything before spending Iden's attention on it.** Two questions have now been retired
this way (`RUN_EXP` magnitude, `W_DINNER`), and neither cost him a moment.

## R175. ✅ THE DIFFICULTY QUESTION IS NOT NEEDED FOR FALL 2026 — third question retired unasked
R169 reduced difficulty to one within-pool question about one tier boundary. Before asking it,
tested whether it can change anything — the R160/R174 discipline.

**First attempt was a badly built test and gave the wrong answer.** It held QRM1001 fixed while
swapping the language slot, but QRM1001 (목4,5,6) **conflicts with UIC1805-02 (화5,6,목4)** — so
the easy tier was silently excluded and a hard-tier course appeared to win by 18.85. That
timetable is neither of the live candidates. **Rebuilt against family B as it actually is**
(defer QRM입문, take the language):

| score | section | tier | time |
|---|---|---|---|
| **21.07** | **UIC1805-02 Beginning Chinese** | **EASY** | 화5,6,목4 |
| 6.89 | YCF1603-04 Spanish(1) | hard | 화8,9,목7 |
| −0.18 | YCF1601-02 Latin(1) · UIC1805-01 · UIC1806-01 | both | 화1,목2,3 |
| −6.43 | YCF1301-07 Chinese(1) | hard | 화1,2,목1 |

**The easy tier wins on schedule alone by 14.18, before difficulty is modelled at all.**
A difficulty penalty points the same way and can only widen it.

⇒ **The difficulty question cannot change which language Iden takes this Fall. Not asked.**
It becomes live only as a **fallback value** — if the easy tier turns out to be unavailable on
8/25 (the seat check), the choice among 언어와표현 courses would then need it.

**Third question retired by testing rather than asking** (after `RUN_EXP` R160 and `W_DINNER`
R174). ⚠️ And the near-miss is the lesson: **the first test was wrong because of a time
conflict I did not check.** A test that silently drops the option it is meant to evaluate
returns a confident, inverted answer. Verify that every candidate in a comparison is actually
*feasible* before reading the comparison.

## R176. 📋 `GAPS.md` created — gaps ordered by decision impact, not by interest
Iden 2026-08-09: *"Fix what you can, ask input from me when it is needed. Identify known gaps."*
Fixes applied (R174), three questions retired by testing (R160/R174/R175), and the gap list
rewritten as its own file, superseding `MODEL.md` §8.

**15 gaps, in three tiers by whether they can change the 8/25 decision:**
- **Tier 1 (3)** — Fall-2026 availability ⏳8/15 · the still-fitted deferral table · risk
  evidence missing for 16 key courses
- **Tier 2 (7)** — quota enforcement · the plan-object (Plan A ≡ Plan B) · robustness pricing ·
  the 신촌 free-day rule · a thin availability table · the crowding curve's wrong population ·
  the un-widened language pool
- **Tier 3 (5)** — real but inert, each with a **trigger condition** rather than a to-do

### What Iden owes has SHRUNK to two live items
| retired | why |
|---|---|
| risk appetite | dissolved — mileage is a constraint, not a preference (R171) |
| `RUN_EXP` magnitude | cannot reorder the top (R160) |
| `W_DINNER` | fires in 0 of 5000 (R174) |
| language difficulty tier | easy tier wins on schedule by 14.18 (R175) |

**Still open and genuinely his:** the 신촌 free-day rule (4-year layer only) and re-confirming
campus dominance. Neither blocks 8/25.

**Four questions retired by testing rather than asking.** That is now the project's default:
before spending his attention, check whether the unknown can change the answer. It usually
cannot. ⚠️ Balanced against R175's near-miss — a test that silently drops the option it is
meant to evaluate returns a confident, inverted answer. **Check feasibility of every candidate
before reading a comparison.**

## R177. ⚠️ A BARE `except: return {}` HID A REAL BUG — and the output silently lost a column
Adding the mileage chips to `TOP50.html`, `deferral_risk()` returned `{}` and **50 chips
rendered as 0** with no error, no warning, and a perfectly normal-looking file.

The swallowed exception was **`NameError: name 'os' is not defined`**. `render_top50.py`
imported `csv, json, collections, html, io, contextlib` — **no `os`** — and I had written the
new function using a `P()` path helper that **the file never defined** (0 occurrences). Both
mistakes were mine; the `try/except Exception: return {}` turned them into silence.

**Fixed properly rather than patched:** `os` imported, `HERE`/`P` defined, all three other file
opens switched to `P()` for consistency, and the fallback replaced with an explicit
`FileNotFoundError("risk.json missing — run build_risk.py first")`.

⚠️ **This is the same failure family as R157 and R162** — superseded or broken code that keeps
running quietly instead of stopping. Those were *values left resident*; this is an *exception
swallowed*. The rule generalises: **a fallback that cannot be distinguished from success is not
a fallback, it is a hidden failure.** If a computation cannot do its job, it must say so.

## R178. ✅ `TOP50.html` NOW STATES THE RECOMMENDATION — the output no longer contradicts it
Iden asked whether recalculating would improve the timetable. **Verified: re-running produces a
byte-identical ranking** — every 2026-08-09 output was *data* (`availability.json`, `risk.json`)
or *documentation*; none of it is wired into `rank3.py`. Nothing changed and nothing should have.

But that exposed a live contradiction: **the file showed rank 1 = "postpones Chinese" while
every finding since R165 says take the language and postpone QRM입문.** A reader would have
registered from the top row. Same class as R158 — output implying a choice the model never made.

**Added to `TOP50.html`:**
1. A banner at the top: *the top-scoring timetable is not the recommended one*, with the three
   reasons the score cannot see (mileage cost · freshman-seat timing · the GPA loop) and the
   note that the 0.73 gap is inside the model's own uncertainty.
2. A **mileage chip on every card** showing what that timetable's deferral costs later —
   *"costs 18–36 mileage later = 25–50% of a future budget"* in red for Chinese, *"1–10 = 1–13%"*
   in grey for QRM입문. **50 of 50 rendered.**

⚠️ Deliberately **not** folded into the score. Mileage is a budget constraint, not a preference
(R171); converting it to points would invent an exchange rate nobody has. It sits *beside* the
score, in its own units, where it can be read but not silently traded away.

## R179. ⛔ I PUT A VERDICT IN THE OUTPUT THAT NO COMPUTATION PRODUCED — removed
Iden 2026-08-09: *"I trust the numbers, not some intuition based on so-called 'what we've
learned so far'. No telling 'the first one is not to pick'. The first one is not to pick only
when the numbers actually say so once we compute anything, otherwise, we have the bias before
the compute."*

**Correct, and the banner is removed.** R178 added a block to `TOP50.html` asserting the
top-scoring timetable was not the one to pick, justified by three arguments — mileage cost,
freshman-seat timing, the GPA loop. **None of the three is computed by anything.** They are
readings assembled across R165/R166/R171 and asserted over a ranking that says the opposite.
That is bias inserted ahead of the calculation, in the one artifact meant to carry the
calculation's answer.

**Kept:** the per-card mileage chip. It is *measured* data displayed in its own units, labelled
as not folded into the score and not reordering anything. Data next to a rank is information;
a verdict over a rank is not.

**Standing rule:** a recommendation may appear in an output **only** when a computation
produced it. Findings that live outside the model belong in `GAPS.md` as gaps, not in
`TOP50.html` as conclusions.

## R180. ⭐⭐⭐ THE 0.73 GAP *IS* THE DEFER TABLE — the two Fall timetables are exactly equal
Ran the computation Iden asked for instead of asserting. Decomposing the top-two gap:

| | week | bonuses | DEFER | chapel | total |
|---|---|---|---|---|---|
| **A** defer Chinese | **32.765** | **−4.000** | −16.97 | +10 | 21.795 |
| **B** defer QRM입문 | **32.765** | **−4.000** | −17.70 | +10 | 21.065 |
| difference | **0.0000** | **0.0000** | **+0.7300** | 0 | **+0.7300** |

**The two Fall timetables are identical on everything Fall 2026 measures — the week and the
bonuses, to four decimal places.** The entire ordering of the top two comes from the difference
between two numbers in R117's fitted `DEFER` table (Lang −16.97 vs MR −17.70).

**Those are precisely the constants R156 flagged as a superseded inheritance**, fitted to two
anchors on a scale that has since moved twice (R129, R142). ⇒ **the top of the ranking is
decided entirely by the least-trustworthy numbers in the model**, and it is not a schedule
result at all.

### And the receiving-semester term does NOT rescue it
Built `build_receiving.py` from **real Spring 국제 observations** (59 mileage rows, 16 courses,
actual Spring times) rather than R148's Fall-pool proxy. The two options differ in the receiving
Spring by exactly one forced course — UIC1805 (화1,목2,3 · 화4,목5,6) vs QRM1001 (금1,2,3 · 목4,5,6):

| shared courses also in that Spring | defer Chinese | defer QRM입문 | difference |
|---|---|---|---|
| 0 | 59.64 | 122.87 | **+63.23** |
| 1 | 59.64 | 84.85 | +25.21 |
| 2 | 50.02 | 50.02 | **0.00** |
| 3 | 16.71 | 19.21 | +2.50 |
| 4 | 6.58 | 4.26 | −2.32 |
| **5 (realistic load)** | **−16.37** | **−40.38** | **−24.01** |

**The sign flips.** On a near-empty Spring, deferring QRM입문 is much better; at a realistic
six-course load, deferring Chinese is better by 24. R148's "+38 gain / −14 crowding" was
measured on a near-empty proxy and sits at the left end of this curve.

⇒ **the third term is load-dependent and does not break the tie either.**

### The honest state of the decision
- Fall 2026 rates the two **exactly equal**.
- The 0.73 that separates them is **two superseded fitted constants**.
- The receiving semester **flips sign with load** and cannot resolve it.
- The mileage difference is real but is **in a different unit and is not scored** (R171).

**Nothing computed currently prefers B over A.** R165/R166's arguments remain interesting and
uncomputed; presenting them as a recommendation (R178) was exactly the error Iden named.
**A is #1 and stays #1 until a computation says otherwise.**

---

## R181. ⭐⭐⭐ IDEN FOUND A MISSING CONSTRAINT: THE FREE-ELECTIVE BUDGET IS NEVER CHECKED
**2026-08-09.** Iden, unprompted:
> "BIZ1101 is a pure elective, also is YCE1253-01-00. But that timetable is considered #1,
> right? So I was curious, because considering the double major, I have like about 5 pure
> electives to fit within 7 semesters. But I already have 2 this semester."

**His arithmetic is exactly right.** Recomputed from R31's table:

| | credits |
|---|---|
| total | 126 |
| Sem 1 done | −19.5 |
| CC remaining | −19.5 |
| QRM major (double-major reduced) | −36 |
| 2nd major | −36 … −39 |
| **= free electives for the whole degree** | **15.0 … 12.0 cr = 5 … 4 courses** |

**#1 spends 6.0 cr of that — two of four-to-five courses — in semester 1 of 7.**

### The model has no line for this
A pure free elective gets `_role = 0.0` (`rank2.py:318`). So does the **Language
requirement**, which lives in the OPEN pool (`rank2.py:288`) and is priced only through
`DEFER['Lang']`. The model neither rewards a free elective nor **charges** it. With six
academic slots, five reachable requirements and `MAX_DEFER = 1`, four slots go to
requirements and **the leftover two are filled by whatever fits the grid best.**
Two of #1's six courses are therefore selected on shape alone.

### MEASURED — the price of the constraint the model doesn't have
Best achievable score at each level of free-elective spend, over all 5000:

| pure free-elective credits | best rank | score | cost vs #1 |
|---|---|---|---|
| **6.0 (2 courses)** | **#1** | **21.795** | — |
| 3.0 (1 course) | #9 | 19.355 | **−2.44** |
| 0.0 | #1214 | 10.464 | −11.33 |

Distribution over 5000: **6cr in 3949 · 3cr in 994 · 0cr in 57.** Top 50: **46 spend 6cr.**

### ⭐ The comparison that matters
**Giving back one elective slot costs 2.44 — that is 3.3× the entire 0.73 gap separating
#1 from #2 (R180).** The last two sessions optimised inside a margin one-third the size of
a term the model does not contain. Iden found it by reading the output; nothing in the
model could have.

### What it does NOT show — do not overclaim (R179 discipline)
Feasibility is **not** broken. After Fall 2026: 87.0 cr over 6 semesters = **14.50/sem
against an 18 cap**. He does not run out of credits. The real exposure is **placement, not
volume** — the deferred MR courses are campus- and term-locked (ECO2101 · ECO2102 · QRM3005
신촌-only; QRM3003 국제-Spring-and-year-3-only), and **nothing checks that they fit.**
That is G-4, unbuilt.

### Also surfaced
**ECO1101** (MR, `_role = 8.0`, one of only **two** MR courses reachable this Fall) first
appears at **rank 145, score 16.674** — it loses on schedule by **5.12**. The model does
value it; it is outbid by grid shape.

**Standing lesson:** every constraint in this project that binds across semesters has been
found by Iden reading the output, not by the model. R129 (the dorm), R130 (the freshman
regime), R152 (the Korean cap), and now R181.

---

## R182. ⭐⭐⭐ THE CONTINUATION VALUE IS BUILT — `ROLE` AND `DEFER` ARE BOTH GONE
**2026-08-09.** Iden set the design, not just the scope:
> "Full everything is the answer I've been giving you for a while, hence the reason I called
> this a 'big project'. Electives not costing anything is probably right. Because the real
> cost comes from choosing the elective over some other thing, the opportunity cost. I've
> been trying to tell you, not only this, but different costs and benefits all over that is
> not inside the model."

**He is right that an elective should score 0.** Charging electives would have been a hack
that double-counts: the cost of putting BIZ1101 in a slot *is* that something else isn't in
it. The defect was never the elective's price — it was that the ALTERNATIVES were priced by
static proxies (`ROLE = 8.0 / 2.29 / 0.36`, `DEFER` = 7 fitted numbers) instead of by what
having them done is worth to the six semesters that follow.

### What was built
| file | what it is |
|---|---|
| `plan_model.py` | the 8-semester skeleton + the remaining-requirement ledger. **Reconciles exactly: 106.5 = 126 − 19.5.** |
| `_crowd_curve.py` → `crowding.json` | the crowding curve, **measured** over all 32 subsets |
| `continuation.py` | `V(remainder)` — best feasible placement into sems 3–8 |
| `defer_value2.py` | the computed replacement for `defer_costs.json` |
| `rank4.py` → `FINAL_ranked4.csv` | the ranker, scoring `week + year penalty + chapel + ΔV` |
| `verify_rank4.py` | independent reconstruction + feasibility of every candidate |

### The measured crowding curve (`_crowd_curve.py`, exhaustive over all 32 subsets)
Best achievable week vs. how many low-supply courses the semester must carry:

| n | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| best week | 96.66 | 96.66 | 77.02 | 59.73 | 35.52 | **4.34** |
| marginal cost of the n-th | — | 0.00 | 19.64 | 17.29 | 24.22 | **31.18** |

**The first constrained course is free; the fifth costs 31.** Convex, as R144 predicted from
a single measured point. Two exact accelerations made the search tractable and both are
proved, not assumed: `fast_score` is **monotone non-increasing** in the occupied mask
(verified 0 violations / 4000 random pairs, and the run aborts if violated), and
`best(S) ≥ best(S ∪ {x})`, which lets each subset seed its incumbent from a superset.

### The computed deferral cost vs R117's fitted table
| defers | **computed ΔV** | R117 fitted | difference |
|---|---|---|---|
| **MR (QRM1001)** | **−39.175** | −17.700 | −21.475 |
| WCiv | −31.175 | −12.000 | −19.175 |
| LHP | −28.508 | −13.000 | −15.508 |
| SciRD | −28.508 | −14.990 | −13.518 |
| Lang | −28.508 | −16.970 | −11.538 |

**Every fitted value understated the cost by roughly half.** And the ordering is now
structural: QRM1001 is dearest because it is 국제-only, single-section, **and** chart-year 1
(so deferring it fires the late arm). Lang is cheapest because it has no chart year at all —
it cannot be off-sequence.

⭐ **The gap that decided #1 vs #2 was 0.73 under the fitted table (R180). It is 10.667
under the computed one — 14× larger, and derived.**

### ⭐ THE ANSWER TO R181
Fall 2026 keeps all five requirements; what should the spare slot hold?

| 6th slot | V(remainder) | vs a free elective |
|---|---|---|
| free elective | −403.391 | 0.000 |
| **ECO1101 (MR)** | −372.216 | **+31.175** |
| **a QRM Major Elective** | −372.216 | **+31.175** |

**A slot spent on a pure elective forgoes 31.175 of continuation value — and nothing is
charged to the elective, exactly as Iden specified.** The number is the marginal crowding
saved in a future semester by retiring one low-supply requirement early.

### ⛔ THE LATE ARM IS FINALLY LIVE
`YEAR_PEN` hardcodes `taken_in_year = 1`, so only the "too early" arm could ever fire
(R173) — the late arm built in R146 has been dead code for two sessions. `continuation.py`
calls `year_gap_pen(year_of_semester, chart_year)` with the real landing year. **R146's
replacement for R117 is, at last, actually doing its job.**

## R183. ⛔ I OVERRODE THE DATA WITH A HAND-WRITTEN LIST AND IT FLIPPED #1
**2026-08-09.** The first `rank4` run returned a #1 that **deferred Intro to QRM** and
filled both spare slots with `ECO1104-07-00` + `STA2102-05-00`.

The cause was mine. `defer_value2.ELECTIVE_TO_ITEM` was a hand-typed dict, and it contained:

```python
'ECO1103': 'ME', 'ECO1104': 'ME',   # ⚠ UNVERIFIED as QRM ME (VERIFY 22)
```

**The pool already knew better.** `ECO1104-07-00` carries `qcat=None`, `_qrm_me=False`,
`cat='전기'`, `dept='상경대학 경제학전공'` — QRM does not list that section. My dict promoted
it to a Major Elective worth +31.175, twice, and that manufactured the entire result.

### This is R102's error run backwards
R102 established that `qcat` — **QRM's own listing** — is authoritative, precisely because
`cat` reflects whichever 개설전공 query ran first. I then bypassed `qcat` with a code list.
And `VERIFY.md` item **22b** had the exact question parked and open the whole time:
*"Do sections QRM did not list still count (ECO1104-07)?"* — I had written the flag into the
code as a comment and then read past it.

### Fixed
`rank4.item_of_section()` reads `qcat` / `_qrm_me` **off the section**, writes the mapping to
`elective_items.json`, and `verify_rank4.py` loads that file rather than re-deriving it.
Counts from the pool: **288 FREE · 13 ME · 2 ECO1101.**

### What it cost, and what it changed
| | with the bad list | corrected |
|---|---|---|
| #1 | defer **QRM1001**, ECO1104 + STA2102, 50.190 | defer **Lang**, ECO1101 + STA2102, **46.640** |

**Standing rule: never map a course to a requirement from a list typed by hand when the
catalogue carries the field.** If a comment in the code says a value is unverified, that is
not a disclaimer — it is a blocker.

## R184. ⭐⭐⭐ THE RANKING INVERTED — Iden's observation was worth ~4000 places
**2026-08-09.** With `V` replacing `ROLE` + `DEFER`:

**New #1 (46.640):** `QRM1001` · `UIC1561` WCiv · `UIC1551` LHP · `UIC2151` SciRD ·
**`ECO1101`** · **`STA2102`** — defer **Language** — **월금 free**.

It takes **both** MR courses reachable this Fall, a real Major Elective, keeps the
Monday+Friday shape, and defers the one requirement that has no chart year to be off from.

| | rank under the other model |
|---|---|
| rank3's #1 (two pure electives) → | **rank 4037** |
| rank4's #1 → was | **rank 4114** in rank3 |
| of rank3's top 50, appearing in rank4's top 5000 | **4**, at ranks 1136–1240 |

**The two rankings are essentially disjoint.** All 50 of the new top 50 still hold 월금 free,
so the week was not sacrificed to buy the quota progress — the old model was simply blind to
half the objective. Verified: all 15 top rows reconstruct exactly from
`week + year penalty + chapel + ΔV`, and every distinct remainder in the top 200 admits a
legal 6-semester plan (`verify_rank4.py`). `test_weights.py` still **23/23**.

⚠️ **The scale changed. 46.640 and 21.795 are different objects** (DESIGN_v2 §5) — a rank4
score contains the value of the rest of the degree. Never put them in one column.

---

## R185. 📋 WHAT IS *NOT* IN THE MODEL — and the retirements that went stale with it
**2026-08-09.** Iden: *"what did you not put in? For example: language difficulty"*

### His example is worse than "missing"
Language difficulty was **retired**, and the test that retired it no longer applies.

| | |
|---|---|
| R175 retired it | *"the easy tier wins on schedule alone by 14.18"* |
| measured under | **rank3** — superseded today by R182/R184 |
| under rank4 | **#1 defers Language entirely**, so the tier question is not a Fall-2026 question any more |
| where V puts it | **sem 3 · Spring 2027 · 신촌** — a semester with no difficulty term at all |
| what the ranker's pool actually is | `LANG = {'UIC1805','UIC1806'}` — **4 sections** |
| what the ledger claims | `supply = 20` |

**The ledger and the ranker disagree about the language pool by 5×.** G-10 (the widened
10-course pool, R166) was never implemented, and `plan_model.py` was written against the
*real* pool while `rank2.py` still holds the narrow one.

### ⚠️ FOUR QUESTIONS WERE RETIRED BY TESTING AGAINST A MODEL THAT NO LONGER EXISTS
`GAPS.md` closes these with "cannot change the answer." All four were measured on rank3.
**Every one needs re-running against rank4 before it stays closed.**
R160 `RUN_EXP` · R171 risk appetite · R174 `W_DINNER` · R175 language difficulty tier.

### Verified absent from every live file (`grep` count = 0)
| | `rank4` | `continuation` | `plan_model` |
|---|---|---|---|
| **difficulty** — any axis | 0 | 0 | 0 |
| **risk / seats** — `risk.json` is built and unused | 0 | 0 | 0 |

**V assumes every future course is obtained.** It is a feasibility-and-quality model with no
probability in it. `risk.json` (21 courses, mileage brackets) exists and nothing reads it.

### Absent from every DOCUMENT in the project — never once considered
- **계절학기 (summer / winter session)** — 0 mentions in any file. A whole mechanism for
  absorbing requirements outside the 8 semesters.
- **휴학 / 병역 (leave of absence, military service)** — 0 mentions. Every number produced
  today assumes **8 consecutive semesters**. For a Korean male 2026 entrant this is a live
  possibility that would restructure the entire skeleton. **Must be asked, not assumed.**
- exchange / study abroad semester
- graduation thesis or capstone — not in the ledger; not checked against the 졸업요건 table

### Still open and known
Korean 12-cr ME cap (priced, unenforced) · 신촌 free-day rule (G-7 — **now more
load-bearing**: V just assigned 4 신촌 semesters and scored them with the 국제 dorm rule) ·
professor quality (G-15) · exam clashes (G-14) · which double major · interest in the
subject matter, which the model has never contained in any form.

### ⛔ ONE I CREATED TODAY — the other half of R183
Demoting `ECO1103/ECO1104` to plain electives is correct **for ME credit** (QRM does not
list those sections). But **R64: 원론 are 경제학 이중전공 필수 in their own right.** If Iden
double-majors in Economics they advance the 36-credit second-major quota, which the ledger
carries as 12 abstract 신촌 courses. So they may be genuinely valuable — for a reason
different from the one my bad dict asserted. Same for **ECO1101**, whose `BONUS_ECON2ND`
was dropped when the role bonuses were removed and never re-expressed inside V.
**Do not treat R183 as closing this. It closed the ME claim, not the DM claim.**

### ✅ One robustness result, in the other direction
The provisional "Language exists at 신촌" assumption was flipped to R143's 국제-only reading
and the whole ranking rescored: **#1 is unchanged**, 46.640 → 43.974. The top four keep their
order. The assumption moves the level, not the decision.

---

## R186. ✅ 휴학 AND 계절학기 BOTH ADDED — and NEITHER changes the 8/25 decision
**2026-08-09.** Iden confirmed a **휴학 for 병역** at some point, and asked for **계절학기**
as an escape valve. Neither had been mentioned once in four sessions (R185).

### 계절학기 — one sourced number, one honest blank
> 수강편람 2026-2, 사회봉사/사회참여 §4-①: *"계절학기에는 계절학기 수강신청 **최대이수학점인
> 7학점**에 포함됨"*

**Cap = 7 credits = 2 courses.** ⚠️ **What is OFFERED in a 계절학기 is in none of the five
official PDFs held here.** Eligibility is a parameter with no data behind it, defaulted to
the plausible 교양 set {LHP, Lang, SciRD, FREE} and flagged `[P]`.

### ⭐ WHAT A 휴학 DOES — the intuition is wrong
| | |
|---|---|
| does it advance 학년? | **NO.** 학년 tracks registered semesters, not calendar time. |
| so the year-gap penalty… | is **completely invariant** to the leave. |
| what actually moves | **TERM PARITY.** Leave after a Fall, return in a Fall, and the Springs shift from sems 3/5/7 to 3/6/8. |
| why that could matter | **QRM3003 is Spring-only AND 국제-only AND chart-year 3.** Parity decides whether it has a legal home. |

### The sweep — 10 break configurations × the top 800 candidates
Only ΔV can move; week, year penalty and chapel are Fall-2026 properties.

| | #1 | top 5 |
|---|---|---|
| no break | 46.640 | — |
| 휴학 after sems 2/3/4/5/6 × return Spring **or** Fall — **all ten** | **46.640** | **identical** |
| 계절학기, no break | 70.855 | #1–#4 identical; only #5 changes |
| 계절학기 + 휴학 | 70.855 | same as above |

**The Fall 2026 answer is invariant to the leave. Not approximately — the score is identical
to three decimal places in all ten cases.**

### ⚠️ VERIFIED THAT THE COMPARISON IS REAL (R175 discipline)
"Identical to 3dp across ten configurations" is exactly the shape of a broken test, so
`build_semesters` was inspected directly. **5 of the 10 configurations do genuinely flip
parity** (`break_after=4, return_term='F'` → `3:S 4:F 5:F 6:S 7:F 8:S`); the other 5 return
in the term that preserves it, and correctly produce the baseline calendar. The variation
is real; the invariance is a result, not an artefact of a dead parameter.

### ⛔ BUT THE MECHANISM IS THIN, AND THAT IS THE THING TO REMEMBER
The model is invariant **because only 1 of 15 ledger items carries any term restriction at
all** — QRM3003. Every parity arrangement still offers it a legal 국제 Spring, so nothing
binds. That is a statement about the **data**, not about the degree: G-8 records that only
21 of 789 courses have more than one term of evidence. **The model cannot see term
restrictions it does not have.** If any other requirement turns out to be single-term, this
result must be re-run before it is trusted.

### 계절학기 is worth +24.215, and it makes deferring Language safer
V goes −369.549 → −345.334 using **one** session (2 slots: Lang + a free elective). It does
not change #1; it widens #1's margin, because the thing #1 defers is exactly the kind of
thing a summer can absorb.

---

## R187. ⭐⭐⭐ "DOESN'T CHANGE THE ANSWER" IS NOT A REASON TO OMIT — and the language tier proves it
**2026-08-09.** Iden, rejecting the triage principle this project has used since `GAPS.md`
was written:
> "even if something 'does not change the answer', it should still be in the model in case
> of future model changes. Like why are we treating the model like some kind of already
> finished thing with only minimal changes to make."

**He is right, and the deeper reason is that a measurement was being stored as a
conclusion.** "Cannot change the answer" is true only of the model that was measured. R185
found four such retirements that had silently outlived their model. A conclusion that decays
without announcing it is worse than an open gap, because an open gap is at least visible.

### The proof arrived within the hour
`G-10` — widen the language pool from 2 courses to R166's 10 — was closed as *"✅ Tested:
this cannot change Fall 2026, the easy tier wins on schedule alone by 14.18 (R175)."*
**Widened. It changes the answer immediately, at zero difficulty weight:**

| | before (2 courses) | after (10 courses, R166) |
|---|---|---|
| #1 | 46.640 · defer **Lang** · easy tier | **47.565 · defer SciRD · takes YCF1603 (Spanish, HARD tier)** |
| #2 | — | 47.299 · defer WCiv · YCF1603 |

R175's 14.18 margin was measured against a pool that did not contain the eight 언어와표현
courses. Their **time slots**, not their difficulty, are what beat it.

### The difficulty axis is now IN the model — with the weight unelicited, on purpose
`difficulty.py`. Carrier = the tier Iden volunteered himself (R166): UIC "Beginning"
*"much easier"* = 0 steps; 언어와표현 *"really learning the language, pretty hard"* = 1 step.
`D_LANG` (points per step) has **never been elicited**, so it is a swept parameter, not a
guess. Default 0.0 reproduces the model exactly as it was without the axis.

### ⭐ TWO CHANNELS — deferring does not avoid the hard tier, it makes it PROBABLE
Measured from `mileage_history.json`, 13 국제 observations of the easy tier:

| | |
|---|---|
| seats per 분반 | **2** |
| sections won only at the 36-mileage cap | **9 of 13** |
| average winning bid range | 12.5 – 34 (of a 36 cap) |
| ⇒ **P(hard tier \| Language deferred)** | **0.692** |

This Fall he is a freshman on 대기순번제 and the easy tier is free (R130). From 2학년 he bids
mileage against a 2-seat 분반 and would be spending one of his only two max-36 bids on a
3-credit CC requirement. **So deferring Language costs 0.692 × D_LANG, not zero.**

### ⭐ THE RESULT — three regimes, and the third IS R166
`sweep_difficulty.py`, over all 7200 candidates. Scale reminder: one 9:00 start = 10.

| D_LANG | #1 |
|---|---|
| **< 3.25** | defer **SciRD**, take **YCF1603** (hard) — 47.565 |
| **3.25 – 10.25** | defer **Language** — 46.640 |
| **> 10.25** | defer **MR (QRM1001)**, take **UIC1805** (easy) — 39.715 |

**The top regime is exactly R166's conclusion** — *"three independent arguments now point the
same way: take the language NOW, defer QRM입문"* — which had lived as prose in a rule file
since 2026-08-07. It is now a computed consequence of a weight, reachable when a hard
language is worth more than one 9:00 start.

### The only question left for Iden, and it is now answerable
> Is one step of *"really learning the language, pretty hard"* worth more or less than
> **3.25** points — and is it more or less than **10.25**?

That is a comparison between states, which R141 permits. "What is difficulty worth in
schedule points" is not, and was never going to be asked.

### Method, to be reused
**For any un-elicited parameter: put the mechanism in, sweep the weight, report the
switching threshold.** It is strictly better than omitting (which decays), better than
guessing (which hides), and better than asking cold (which R136/R137/R141 all forbid).

### Engineering note
Widening the pool multiplied the requirement product by ~2.5 and pushed a full search past
the wall clock. `rank4_branch.py` now runs **one deferral branch per invocation**, carrying
the branch-and-bound incumbent through `_rank4_parts/incumbent.json`. The branches partition
the space, so this is exact; `merge` refuses to run if any branch is missing.
(A recursive conflict-pruned combo builder was tried first and was **1.8× slower** — the
requirement pools rarely conflict, so generator overhead exceeded the pruning gain.)

---

## R188. ⭐⭐⭐ THE ELICITED DIFFICULTY LANDS EXACTLY ON THE SWITCHING THRESHOLD — a real tie
**2026-08-09.** Asked to compare two identical semesters differing only in whether the
language slot held Beginning Chinese or a 언어와표현 course, Iden answered:

> **"About the same as a 9am start."**

One 9:00 start = 10 (MODEL.md §0). ⇒ **`D_LANG = 10.0`**, now live in `difficulty.py`.

### The sweep put the boundary at 10.25. He answered 10.
| `D_LANG` | #1 | margin over the next strategy family |
|---|---|---|
| 9.00 | defer **Language** | 0.694 |
| 9.50 | defer **Language** | 0.348 |
| **10.00 — elicited** | defer **Language** — 39.717 | **0.002** |
| 10.25 | defer **QRM1001**, take UIC1805 — 39.715 | 0.171 |
| 11.00 | defer **QRM1001** | 0.683 |

**39.717 against 39.715.** Two thousandths of a point, on a scale where one 9:00 start is
10 and the whole ranking spans ~50.

### This is a genuine tie, and it must not be dressed up as a winner
R179 is the standing rule: no verdict the computation did not produce. The computation
produced **a tie**, and it did so from an elicited value rather than from stale constants —
so unlike R180's 0.73, this margin is real. It is simply zero.

**Two strategies survive, and the model cannot choose between them:**

| | A — defer **Language** | B — defer **QRM1001** |
|---|---|---|
| Fall 2026 | QRM1001 · WCiv · LHP · RDQM · ECO1101 · STA2102 | WCiv · LHP · RDQM · **UIC1805** · ECO1101 · STA2102 |
| score at D_LANG=10 | **39.717** | **39.715** |
| the bet | the easy language tier is still winnable as a 2학년 | Intro to QRM is still winnable as a 2학년 |

Both take ECO1101 and STA2102. Both keep 월+금 free. They differ in **one slot**.

### ⭐ WHAT BREAKS THE TIE IS THE THING THE MODEL DOES NOT HAVE
Each option is a bet on obtaining something later, and the two bets have measured but
UNMODELLED odds:
- **A** bets on the easy language tier: a **2-seat 분반**, won only at the 36-mileage cap in
  **9 of 13** observed 국제 sections (R187).
- **B** bets on QRM1001: **a single section**, and no mileage evidence at all (G-3).

`test_retired.py` flagged this hours earlier and independently: **R171 EXPIRED — `risk.json`
is read by nothing, and V assumes every future course is obtained with probability 1.**

⇒ **The tie-breaker is acquisition risk, and it is the one major layer still unbuilt.** The
model has done its job: it narrowed a 7,200-candidate space to two options that differ in a
single slot, and then named exactly which missing mechanism decides between them.

### Method note — the threshold-first elicitation worked
The sweep was run BEFORE the question, so the question could be a comparison between two
states (R141-safe) instead of "what is difficulty worth in points" (which R136/R137/R141 all
forbid). It also meant the answer's *precision requirement* was known in advance — and this
answer needed more precision than a human can supply, which is itself the finding.

## R189. ⛔ ASKING "IS EVERYTHING IN?" FOUND TWO MORE DEFECTS IN WHAT WAS JUST BUILT
**2026-08-09.** Iden: *"ok, so... everything is in? or"* — checked before answering, and the
check found two, both in code written the same hour.

### 1. The published ranking was scored at a constant the model no longer held
`FINAL_ranked4.csv` was generated at `D_LANG = 0`. R188 then set `D_LANG = 10.0`. **The
ranking file and the live model disagreed, and `verify_rank4.py` passed anyway** — because
the verifier did not reconstruct the difficulty term at all, so it could not see it. Adding
`dif` to the reconstruction turned a silent pass into **11 of 15 rows FAIL**, which is what
it should always have said.
> A verifier that omits a term cannot detect an error in that term. Every term in the score
> must appear in the reconstruction, including ones that are currently zero.

### 2. The ranker had ONE of the two difficulty channels; the sweep had both
`sweep_difficulty.py` charged (a) taking a hard language and (b) `P_hard × D_LANG` for
*deferring* Language. `rank4_branch.py` charged only (a) — it iterates over courses actually
taken, and a deferred requirement is by definition not among them. So **the ranker
overstated "defer Language" by 6.92** while the sweep had it right.

Both wired. The ranker now reproduces the sweep exactly:

| | |
|---|---|
| #1 | **39.717** defer Language · QRM1001 WCiv LHP RDQM · ECO1101 STA2102 |
| #2 | **39.715** defer QRM1001 · WCiv LHP RDQM UIC1805 · ECO1101 STA2102 |

**margin 0.002** — R188's tie, now produced by the search itself rather than by a rescore.
`verify_rank4.py` 15/15 · `test_weights.py` 23/23 · `test_retired.py` 5 hold, 1 uncheckable,
**1 still broken (R171 — risk is wired into nothing), which is correct and should stay red
until it is built.**

### Standing lesson
Two of today's three worst defects (R183, and both above) were **my own new code
contradicting data or itself**, found only because something was checked rather than
assumed. The harness caught the second class only after it was taught to look. **A test
suite is not evidence of correctness for the terms it does not mention.**

---

## R190. ⭐⭐⭐ minMlg/avgMlg/maxMlg ARE OVER APPLICANTS, NOT WINNERS — and it breaks R188's tie
**2026-08-09.** Iden reframed the work correctly:
> "I know you are worried about the seat data, but that is data. As long as we finalize the
> logic, it will fit in quite neatly."

Right — and building the logic first immediately found an error in the logic already shipped.

### The internal check that settles the field semantics
The natural reading of a section's `minMlg / avgMlg / maxMlg` is *"statistics of the students
who won the seat"*. **That reading is false, and it is falsifiable with no external document:**

> For a section with exactly **2 seats**, if the stats described the 2 winners then
> `avg` must equal `(min+max)/2` **exactly**.

Measured over all **28** two-seat sections in `mileage_history.json`:
**9 match. 19 do not.** And `avgMlg` values of `19.33` (=58/3), `17.18`, `24.4` have
denominators far larger than 2.

⇒ **They are statistics over APPLICANTS.**

### Why that matters more than it sounds
For a 2-seat section you must finish in the **top two of the applicant bid distribution**. So
the relevant quantity is proximity to `maxMlg`. **`minMlg` is merely the most timid
applicant — beating them means nothing.**

### Three of my own estimates were wrong, in both directions
| version | estimator | P(hard tier \| Language deferred) | verdict |
|---|---|---|---|
| R187/R188 | share of sections with `maxMlg` >= 36 | **0.692** | too pessimistic — reads "someone bid the cap" as "you must" |
| first `risk.py` | share with `minMlg` <= bid | ~**0.05** | far too optimistic — beats the weakest applicant |
| **now** | bracket, strict-beat vs weakest-beat | **[0.000, 0.350]** | honest |

**0.692 is outside the bracket entirely**, and it was the live constant in the ranker.

### ⛔ AND A THIRD MECHANISM SURFACED: THE TIE-BREAK WALL
The first bracket returned `[0.000, 0.000]` — a fabricated certainty. At a bid of 36 you do
not *beat* the top applicant, you **match** them, which enters the 이수학점/학년 tie-break
ladder. **Nothing in this project models that ladder**, and it decides:
- **7 of 8** observed UIC1806 국제 sections
- **2 of 5** observed UIC1805 국제 sections

`p_win_bracket` now surfaces those as unmodelled rather than scoring them 1.0.
Related, and previously unused: **R3's cap-12 class** (which includes **ECO1101**, a Major
Required course) is decided *entirely* by that ladder — bidding more buys nothing.

### ⭐ THE RESULT — R188's tie is broken, by fixing an error rather than by new data
Live ranker rebuilt with the **pessimistic** arm (0.350) — deliberately the arm that argues
*against* deferring, so a win under it is a win across the whole bracket:

| | | |
|---|---|---|
| **#1** | **43.140** | defer **Language** · QRM1001 · WCiv · LHP · RDQM · ECO1101 · STA2102 |
| #5 | 39.715 | defer QRM1001 · WCiv · LHP · RDQM · UIC1805 · ECO1101 · STA2102 |
| margin | **3.422** | (6.92 under the optimistic arm — the ordering never flips) |

R188 reported these as separated by 0.002. **That tie was an artefact of my own bad
estimator, not a property of the problem.** Deferring Language wins, and now the numbers
say so.

`verify_rank4.py` 15/15 · `test_weights.py` 23/23 · `test_retired.py` 5 hold / 1 uncheckable /
1 still broken (R171 — risk is now *built* but not yet *wired into V*, which is correct: the
test should stay red until the continuation value actually consumes it).

### Standing lesson
**Never take the arm of a bracket that flatters the incumbent.** And when a probability comes
out at exactly 0.000 or 1.000, that is not confidence — it is almost always a mechanism the
model has silently assumed away.

---

## R191. ✅ THE REMAINING LOGIC GAPS ARE CLOSED — what is left is DATA
**2026-08-09.** Iden: *"let's finish up the remaining gaps."* Worked through them; the
mechanism side is now complete and the residue is genuinely just numbers to fetch.

### Closed this pass
| gap | what was done |
|---|---|
| **risk wired into V** | `continuation.solve()` now rejects any plan whose semesters cannot be **bought** — 72 mileage, per-course ceiling, ≤2 bids at 36. R171's "a budget, not a preference" is finally a constraint rather than a sentence. |
| **Korean ME cap (R152/R105)** | **ENFORCED**, not priced. QRM's electives are 국제-only, so a Major Elective taken at 신촌 must be a Korean 상경·응통 section — capped at 4 courses. `solve()` rejects plans exceeding it. |
| **the DM channel R183 half-closed (R185)** | `rank4.DM_ADVANCING` — under an Economics double major, ECO1103/1104 advance the **36-credit second-major quota** (R64), not ME. `DM_MAJOR = None` until December, so currently inert. |
| **the GPA gate (R153)** | `difficulty.GPA_GATE_MULT` — difficulty taken in Fall 2026 is multiplied, because these grades decide December's double-major admission; deferred difficulty lands after the gate. Default 1.0 = inert, sweepable. |
| **R174 made checkable again** | `rank4_branch.py` had dropped `early1/lunch_fail/dinner_fail/late/runs/holes`, which silently disabled a test for a whole session. Restored. **`test_retired.py` now reports 0 uncheckable.** |

### ⛔ TWO MORE SILENT FALSEHOODS FOUND WHILE CLOSING THEM
1. **`min_bid_for` priced un-observed courses at 1 mileage.** `p_win_*` returns `1.0 / 'NO
   DATA'` so that consumers stay numerically unchanged — but a *bid* of 1 for a course
   nobody has ever observed is a fabricated fact. **ECO2102, a Major Required course with
   zero mileage rows, was reported as costing 1 mileage.** Now returns `None` (unpriced).
2. **I claimed "#1 takes STA2102, which spends one of your four Korean ME slots." False.**
   Measured: `STA2102-05-00` is `언더우드국제대학 융합사회과학부-계량위험관리` — UIC-offered.
   **0 of the 13 ME-eligible sections in the Fall 2026 국제 pool are Korean-capped.** The cap
   does not bind this term at all; it binds across the 신촌 semesters.

### The test that was checking the wrong thing
`test_retired.r171` searched the source for the string `'risk.json'`. The live wiring
imports `risk.py` and calls `budget_check`; `risk.json` (the old summary table) is genuinely
dead. Corrected to assert the **mechanism**, with R171b separately asserting it can **bind**.
*Fixing a test that tests the wrong thing is not the same as editing a test to make it pass —
the distinction is whether the claim or the instrument was wrong.*

### State
`verify_rank4.py` 15/15 · `test_weights.py` 23/23 · `test_retired.py` **8 hold · 0
uncheckable · 1 broken**, and the one broken is correct and should stay red:

> **R171b — only 3 of 15 ledger items are priceable** (Chapel 11, LHP 17, SciRD 34 mileage).
> The other 12 have no mileage evidence, so the 72-point budget is enforced but **cannot yet
> bind**. That is G-3, and it is a data gap, not a logic gap.

### The ranking is unchanged by all of it
**#1 = 43.140 · defer Language · QRM1001 · WCiv · LHP · RDQM · ECO1101 · STA2102 · 월+금 free.**
Every new constraint was checked against it and none binds. **That is the correct outcome
for constraints added late: they should mostly not bind, and the ones that do should be
loud.** The value is that they will now catch a future plan that violates them.

## R192. ⛔ THE DELIVERABLE ITSELF WAS STALE — TOP50.html read rank3 all session
**2026-08-09.** Asked "what's left?", audited instead of reciting, and the first thing the
audit found was the worst one:

> **`render_top50.py` read `FINAL_ranked3.csv`.** The ranker was replaced at ~15:00 (R182)
> and revised twice more (R187, R190). `TOP50.html` was last written at **13:41** from the
> **13:34** rank3 output. **The one artefact Iden actually opens was showing a #1 that had
> since fallen to roughly rank 4000.**

Every number reported in conversation was from the live CSV, so nothing said was wrong — but
the *file he would have opened* disagreed with all of it. Repointed and rebuilt: `TOP50.html`
now carries QRM1001 · WCiv · LHP · RDQM · ECO1101 · STA2102 at 43.14, and the old
YCE1253/BIZ1101 pair is gone from the top 50 entirely.

### Same failure class as two others today
| | |
|---|---|
| R189 | a **verifier** that omitted a term could not detect an error in that term |
| R191 | a **test** that searched for `'risk.json'` tested the wrong thing |
| R192 | a **renderer** that read a superseded input showed a superseded answer |

**All three passed silently.** A green suite means only that the assertions that exist hold.
`INDEX.md` now marks `FINAL_ranked3.csv` as SUPERSEDED and points at `FINAL_ranked4.csv`.

### ⚠️ Standing check to run before ever trusting the HTML again
`ls -l TOP50.html FINAL_ranked4.csv` — **if the CSV is newer than the HTML, the HTML is a
lie.** This deserves to be an assertion in `test_retired.py`, not a habit.

---

## R193. ⭐⭐⭐ THE TIE-BREAK LADDER IS DOCUMENTED — and two of its rungs run through Fall 2026
**2026-08-09.** The largest unmodelled mechanism turned out not to need modelling at all —
it is written down, in two official documents that agree verbatim.

> `수강편람` §2-1-① and `수강신청 제도안내` §3-3:
> ⓐ 높은 마일리지 · ⓑ 특수교육대상자 · ⓒ **전공자·복수전공생 우선** · ⓓ **신청과목수(최대 6)** ·
> ⓔ 졸업/수료 신청자 · ⓕ 초수강자 · ⓖ 총이수학점/졸업이수학점 · ⓗ **직전학기이수학점/수강가능학점** ·
> ⓘ 난수

This decides **7 of 8** observed UIC1806 국제 sections, **2 of 5** UIC1805, and **every**
cap-12 course including **ECO1101**, a Major Required course (R3).

### ⭐ ⓗ CONNECTS FALL 2026 TO EVERY FUTURE ACQUISITION — and nothing knew
ⓗ is **직전학기** — the PREVIOUS semester's load. **The credits Iden takes this Fall set his
tie-break rank in the Spring 2027 mileage round and every round after.** The ranker has
always treated total credits as a free choice inside `[17, 21]` with no consequence
attached. There is a consequence, and it is permanent.

### ✅ AND THE ALLOWANCE CONFLICT IS RESOLVED, AGAINST R86
> 수강편람, 학기당 수강학점: *"졸업이수학점이 126학점인 대학·학과·전공 **전 학년** … **1∼18**"*

QRM is 126 credits ⇒ the allowance is **18**, not R86's 19. And the GPA-3.75 bonus is
**초과신청**, which 제도안내 explicitly excludes from ⓗ's denominator (*"직전학기이수학점의
분모에는 초과신청 가능학점을 포함하지 않습니다"*) — so taking 21 would not dilute the ratio.

**⇒ 18 credits gives exactly 18/18 = 1.00. Rung ⓗ MAXED.**

### The live #1 maxes both controllable rungs, by accident
| rung | live #1 | |
|---|---|---|
| ⓓ 신청과목수 | **6 of 6 counted** | MAXED — chapel/RC are 수강허용학점 예외 and do not count |
| ⓗ 직전학기 비율 | **18/18 = 1.00** | MAXED |

Iden chose "6 courses, 18 credits" as a *preference* in R111, declining 21. It turns out to
be **optimal on the ladder as well**. That is luck, and it should be recorded as luck — had
he chosen 5 courses, he would have silently lowered his standing in every future contested
registration, and nothing in the model would have said a word.

### ⭐ ⓒ IS A CONSEQUENCE OF THE DECEMBER DECISION
제도안내 wording: **"전공생 및 복수전공생 우선"**. A declared **Economics** double major lifts
him above non-majors on **ECO2101 and ECO2102** — both Major Required, both 신촌-only, both
currently unpriceable for want of mileage data (G-3). The December choice is not only a quota
decision; it is an **acquisition** decision for two required courses.

### ⚠️ ⓖ RUNS THE OTHER WAY — a genuine counterweight
총이수학점/졸업이수학점 rises monotonically, so his tie-break position **improves every
semester**. 제도안내 states the intent outright: *"총 이수학점이 높은 학생들(고학년)이 우선권을
갖는 것은 졸업을 위한 수강신청을 배려하기…"*. So on this rung, **later is strictly better**,
and the model must not assume deferral is uniformly worse for acquisition. It bites only at
equal mileage, so it does not overturn ⓐ.

**Two of the three most load-bearing mechanisms found today were sitting in the official PDFs
the whole time** (this, and 계절학기's 7-credit cap in R186). Reading beats inferring.

---

## R194. ⛔ "free 월금" MEANT CAMPUS-FREE, AND IT READ AS DAY-OFF — Iden caught it on sight
**2026-08-09.** Iden, looking at the rebuilt HTML:
> *"#1 has free 월금. are all the classes on 월 online?"*

**Yes — all three of them.** And that is the whole point, but the label never said so.

### #1, day by day
| day | campus presence | genuinely empty | what is on it |
|---|---|---|---|
| **월** | **NO** | **no** | UIC1561 · ECO1101 · STA2102 — **three courses, all online** |
| 화 | yes | no | chapel · UIC1551 |
| 수 | yes | no | UIC2151 · ECO1101 · STA2102 (+UIC1561 online) |
| 목 | yes | no | QRM1001 · UIC1551 |
| **금** | **NO** | **YES** | nothing at all |

`det['free']` is `{d for d in range(5) if pres_free[d]}` — the **PRESENCE** mask. So the
column labelled `free_days` has always meant *no trip to campus*, never *no work*. R129 built
that distinction deliberately and then the display threw it away.

### What #1 actually earns
```
TRIP  금·토·일·월 = 4 consecutive campus-free days -> 13.00 x (4-2)^1.4 = 34.31
REST  genuinely empty weekdays = 1 (금 only)       ->  7.00 x 1        =  7.00
                                                       week total      = 45.64
```
**Monday earns the trip home and earns no rest.** Exactly as R129 specifies — a Monday of
online classes is a Monday you work through, at home. The number was right; the word was not.

### Fixed
`TOP50.html` now shows **two** labels per timetable: **`home`** (no trip) and
**`no class at all`** (genuinely empty), with a note that only the second earns REST.
For #1: home 월금 · no class at all 금.

**Lesson: a display that collapses two modelled goods into one word will be read as the good
the reader cares about.** The model had them separate for two sessions; the output did not.

---

## R195. ⭐⭐⭐ THE 신촌 FREE-DAY RULE **DOES** CHANGE THE 8/25 DECISION — G-7 was misfiled
**2026-08-09.** Elicited, in Iden's words:
> *"신촌 rule is, yes, as per the purpose, days of the week have no difference from each
> other, isolated or not. Or maybe minimal difference, since connected days do still give
> some merit. (Friday event bonus still holds.)"*

He gave the **shape**, which is what was actually needed. At 국제 he dorms, so a free day only
pays inside a weekend-connected block — hence the convex TRIP term and the convex measured
crowding curve. At 신촌 he commutes from home daily, so **every** free day saves a round trip.
Structurally: the marginal cost of occupying one more day is **constant** at 신촌 and
**convex** at 국제. Encoded in `continuation.solve()` as a campus-dependent crowding curve.

### ⛔ AND THE SWEEP OVERTURNED A STANDING CLAIM
`GAPS.md` G-7 has said since it was written: *"Doesn't affect Fall 2026 (국제 either way)."*
**False.** Fall 2026 is 국제 either way, but the rule prices the SIX SEMESTERS AFTER it, and
that is now inside every score.

| 신촌 step | #1 |
|---|---|
| 0 – 5 | defer **Language** — and a pure free elective reappears at the top ⚠️ |
| **10 – 14** | **⭐ THE ANSWER CHANGES** |
| 14 – 45 | defer **QRM1001**, take **UIC1805 (Beginning Chinese) now** |

**The neutral default (18.46 — the mean 국제 increment, chosen so a full semester costs the
same and only its distribution moves) sits ABOVE the threshold.** So merely encoding the
shape Iden gave, with a deliberately neutral size, flips #1 from *defer Language* to
*defer Intro to QRM*.

### What this means
The size now has to be elicited — but the sweep says exactly how much precision is needed:
**only whether one free weekday at 신촌 is worth more or less than roughly 10–14**, on the
scale where one 9:00 start = 10 and a free Friday at 국제 = 20. That is a comparison between
states, which R141 permits.

⚠️ **Reported honestly:** the sweep rescores the top 600 of a candidate set generated at the
default step. The threshold's LOCATION is reliable; the exact scores at the extremes are not,
and a full branch re-run is required before any of this is treated as final.

⚠️ **Degeneracy at the bottom:** at step 0 a 신촌 semester absorbs everything at no cost, V
explodes, and a pure free elective returns to #1 — which would break R181's assertion. Very
low values are not merely unlikely, they are structurally unsound.

### Method note
This is case 2 of the three sweep outcomes: **one threshold**, so an unanswerable question
("what is a commute worth in schedule points?") collapses into an answerable one. It is also
the first sweep to *overturn* a claim rather than retire a question — R160 and R174 killed
questions, R187 killed a retirement, and this one killed a scoping assumption.

## R196. ⭐⭐⭐ THE 신촌 SIZE WAS *DERIVED*, NOT ASKED — and #1 CHANGED
**2026-08-09.** Asked how much a free weekday at 신촌 is worth, Iden answered **"not sure."**
That is the correct answer to that question, and it should not have been pushed. It was
derived instead, from two values he had already given:

```
  a free weekday at 신촌  =  not working  +  not travelling
      not working    = REST                                      =  7.00   [E]
      not travelling = a 4-hour round trip (2h each way, HANDOFF §1)
                       his own price for 4 dead hours: HOLE(4)   = 10.00   [E]
                                                                   ------
                                                                   17.00   [D]
```
Bracket **[12, 22]** — transit may be worse than a campus hole (tiring, twice daily, no rest)
or better (can read on the train). **Swept at 12, 17 and 22: #1 is identical at all three.**
The conclusion does not depend on where inside the bracket the truth lies.

This is the R146 move — derive from existing anchors rather than elicit an nth constant.
It is now the second time a "cannot be asked" parameter was resolved without asking.

### ⛔ THE ANSWER CHANGED. Full re-run, all six branches, D_LANG = 10, 신촌 = 17.

| | | |
|---|---|---|
| **#1 — 39.164** | defer **Intro to QRM** | WCiv · LHP · RDQM · **UIC1805 Beginning Chinese** · **ECO1101** · **STA2102** · chapel · 월+금 |
| previously | defer **Language** | QRM1001 · WCiv · LHP · RDQM · ECO1101 · STA2102 |

**It now takes Beginning Chinese this Fall and postpones Intro to QRM.** That is R166's
conclusion — *"three independent arguments point the same way: take the language NOW, defer
QRM입문"* — reached for a fourth, independent reason it never had: **the easy language tier is
free to him this semester on 대기순번제, and Intro to QRM is cheap to re-acquire later**
(4 of 4 observed mileage sections, and it is a large course — 58 to 80 seats).

`verify_rank4` 15/15 · `test_weights` 23/23 · `test_retired` 10 hold / 0 uncheckable /
1 broken (the mileage-data one) · `TOP50.html` rebuilt from the new ranking.

### ⚠️ What this rests on, stated plainly
The **shape** is elicited (Iden: *"days of the week have no difference from each other,
isolated or not"*). The **size** is derived, not elicited, and the derivation treats a
commute as equivalent to a dead campus hour. That equivalence is an assumption — a
reasonable one, made from his own numbers, and robust across a 12–22 bracket, **but it is the
single load-bearing assumption under the current #1.** If it is wrong by enough to push the
value below ~10, #1 reverts to deferring Language.

---

## R197. ⛔ "EQUAL SWAPS" WERE NOT EQUAL — Iden caught a dead model inside the renderer
**2026-08-09.** Iden, reading the rebuilt HTML:
> *"i'm 100% sure these are not equal swaps. Language is a requirement. ... if you swap any
> of those and the timetable gets an equal score, that's wrong right?"*

**Right.** `TOP50.html` offered `YCB1101 WRITING`, `YCD1103 WORLD LITERATURE`, `ECO1001
INTRO TO ECONOMICS` and four others as "equal swaps" for **`UIC1805 BEGINNING CHINESE`**.
They do share a time slot. But **UIC1805 fills the Language requirement and none of them do.**

And it is worse than unequal. On the live #1 — which already defers Intro to QRM — making
that swap leaves Language unsatisfied too, giving **two deferrals**, outside `MAX_DEFER = 1`.
**The suggestion was outside the space the ranking was computed over.**

### Three faults in one key, and two are the R192 class
The old grouping was `(tm, pm, bonus, cr)` where `bonus = R2.BONUS + _role + YEAR_PEN`:
1. **no requirement membership** — a Language course and a plain elective were interchangeable;
2. **`_role`** — a term rank4 **deleted** (R182). The renderer was scoring with a dead model,
   exactly like R192's stale CSV read;
3. **no ledger item** — a Major Elective and a free elective in the same slot were called
   equal, though they differ by ~31 of continuation value.

### And the first fix was still wrong — same test, one level down
After adding requirement membership and the ledger item, it offered **`YCF1601 LATIN`** as an
equal swap for **Beginning Japanese**. Both satisfy Language, both fit the slot — but Latin is
언어와표현, the **HARD tier**, worth `−D_LANG = −10` (R187/R188). Applying Iden's own test to
the corrected output caught it.

### An equal swap now requires ALL of
same time mask · same presence mask · same credits · same year penalty ·
**same requirement membership** · **same ledger item** · **same difficulty tier**

**Result: `UIC1805-02-00` has NO equal swaps at all** (it had seven). Beginning Japanese and
Beginning Chinese remain genuine twins of each other, which is correct — same tier, same
requirement, same slot. Sections with any genuine equal swap: **155**.

### Standing lesson, now three for three
R192 (renderer read a superseded CSV), R189 (verifier omitted a live term), and now R197
(renderer scored with a deleted term). **Every derived view must be rebuilt from the current
scoring function, not from a copy of an old one.** The tests never caught any of the three,
because none of them asserted anything about derived views — they asserted about the ranking.

⚠️ **This one was reachable only by a human reading the output and knowing the domain.** A
swap can be arithmetically equal under the wrong function and still be nonsense. Iden has now
found five such things by inspection (R129, R130, R152, R181, R197).

## R198. ⛔ SHOWING ONLY THE *FREE* MOVES IMPLIED THE PRICED ONES DID NOT EXIST
**2026-08-09.** Iden, on being told Beginning Japanese is not an equal swap:
> *"oh really? I thought beginning japanese would be an equal swap"*

**He was right about the COURSE. The display was right about the SECTION.** The gap between
those two true statements was invisible, and that gap is the defect.

```
UIC1805-01  Beginning Chinese    화1,목2,3   ┐ share a slot -> genuinely equal
UIC1806-01  Beginning Japanese   화1,목2,3   ┘
UIC1805-02  Beginning Chinese    화5,6,목4   <- what #1 holds; NO Japanese section matches
```
So Japanese is fully interchangeable as a course, and is **not free** against the section #1
holds: its only compatible section is **−21.250**, because it starts at 화1 — a 9:00.

### The real fault
`TOP50.html` displayed exactly two things: swaps with delta **exactly 0**, and same-course
different-분반 alternates. **Every priced option was omitted**, and an omitted option reads as
a nonexistent one. For the Language slot alone there are **nineteen**.

### Built: `ALTERNATIVES.html`
For each of #1's six slots, **every** course that can legally fill it — time, professor,
difficulty tier, resulting total, and delta — with time-conflicting options listed and marked
rather than dropped. Language slot, top of the list:

| option | time | tier | vs #1 |
|---|---|---|---|
| UIC1806-01 Beginning Japanese | 화1,목2,3 | easy | **−21.250** |
| UIC1805-01 Beginning Chinese | 화1,목2,3 | easy | −21.250 |
| YCF1603-04 Spanish | 화8,9,목7 | HARD | −24.175 |
| YCF1601-02 Latin | 화1,목2,3 | HARD | −31.250 |
| … 9 more, then 9 time-conflicts | | | |

**The 21.25 is almost entirely the 화1 9:00 start plus the grid damage** — not the language.

### Standing lesson, and it is the fourth of this kind today
R189 · R192 · R197 · R198 are one failure repeated: **a derived view that quietly disagrees
with the live model.** This one did not even disagree — every number it printed was correct.
It was **incomplete in a way that carried an implication**, which is harder to test for and
was caught only because Iden's domain intuition contradicted the output.

## R199. ✅ THE LATE ARM SURVIVED — it was never the arm that became difficulty
**2026-08-09.** Iden:
> *"taking QRM, a 학년:1 class, does it have any penalty taking it in the future? I know we
> decided '학년' was nothing, and that's right, but we changed it into difficulty. I was
> wondering if it got lost"*

**It did not get lost, and the reason is that the two arms were never the same object.**

| arm | condition | Iden's own words | what it is |
|---|---|---|---|
| **early** | y < c | *"I'm not ready for it"* (R135) | a **readiness/difficulty** claim |
| **late** | y > c | *"off-sequence, everything downstream slides"* (R145) | a **sequencing** claim |

Only the **early** arm was ever doing difficulty's job — MODEL.md §3 says so outright
(*"the early arm has been silently substituting for a difficulty axis"*). The **late** arm was
elicited separately in R145/R146 for a different purpose and has nothing to do with how hard
a course is. So building `difficulty.py` could not have consumed it.

### It is live, and it is charging right now
QRM1001 has chart year 1:

| taken in academic year | penalty |
|---|---|
| 1 (now) | 0.000 |
| **2** | **−2.667** |
| 3 | −15.085 |
| 4 | −41.569 |

`continuation.solve()` calls `year_gap_pen(semester_year, chart_year)` with the **real landing
year**, so the late arm fires there. **The live #1 defers QRM1001, V places it in sem 3
(academic year 2), and it is charged −2.667.** That is exactly the mechanism R146 built and
R173 found unreachable — reachable at last because V knows which semester things land in.

⚠️ The **Fall-2026** scorer still uses `YEAR_PEN = year_gap_pen(1, chart)` with
`taken_in_year` hardcoded to 1, so only the early arm can fire *there*. That is correct — in
Fall 2026 he IS in year 1 — but it remains a trap for anyone reading `rank2.py` alone.

### ⭐ WHAT THE QUESTION EXPOSED — a double-count that does not exist YET
Measured: **0 courses** carry both a difficulty step and a chart year. The two axes are
disjoint today purely because difficulty has exactly one carrier — the language tier — and
every language course has `chart_year = None`.

**They will not stay disjoint.** The very first task of this session tested whether *course
level* and *chart-year distance* are the same signal. If course level becomes difficulty's
second carrier, every QRM and ECO course acquires **both** a difficulty step and a year gap,
and the early arm — which is *already* a difficulty proxy — would be counted twice.

Now an assertion in `test_retired.py`, so it fails the moment the overlap appears.

## R200. ⭐⭐ "MAXIMISE 신촌" WAS NEVER IN THE MODEL — and it flips #1 at a bonus of 30
**2026-08-09.** Iden: *"does campus-purity and the 4-year plan (maximize sinchon) get
considered?"*

| | |
|---|---|
| **campus purity** | ✅ enforced — but **by construction**, not by choice. `solve()` assigns one campus per semester, so mixing is impossible. That is an unexamined assumption, not a rule. |
| **maximise 신촌** | ❌ **absent entirely.** |

Left free, V chose **4 국제 / 3 신촌** when the minimum FORCED is **2 국제** (Fall 2026 +
one 국제 Spring for QRM3003). It was voluntarily spending two extra 국제 semesters, because
nothing in the objective preferred 신촌 — while R126 records Iden calling a 신촌 semester
**"much much much more preferable"**, strong enough that one was said to outrank the entire
weekly-schedule range.

**A stated preference that lived only in prose for four sessions.**

### Built and swept — `SINCHON_SEMESTER_VALUE`, default 0.0 (inert)
| bonus per 신촌 semester | campus plan | #1 |
|---|---|---|
| 0 | 4 국제 / 3 신촌 | defer **QRM1001** |
| 10 | 4 / 3 | defer QRM1001 |
| 20 | 3 / 4 | defer QRM1001 |
| **30** | 2 / 5 | ⭐ **defer Language** |
| 40 – 120 | 2 / 5 (the forced minimum) | defer Language |

**Two thresholds, and they are different:** the campus plan reaches max-신촌 between 20 and
40, but the **Fall 2026 decision** flips at **30**.

### The question this reduces to
Is one 신촌 semester worth more or less than **30**? Scale: one 9:00 start = 10, a free Friday
at 국제 = 20, an entire empty week ≈ 96.

⚠️ **R126 already answers it — at ≥96, far above the threshold.** If that statement still
holds, **#1 reverts to deferring Language and taking Intro to QRM now.** But R126 is flagged
in `VERIFY.md` as V-4, *"pinned to a ceiling that has since moved"*, and the ceiling has moved
twice since. So it is a confirmation, not an assumption to act on.

## R201. ✅ 신촌 CONFIRMED AT 96+ — #1 REVERTS, and the 4-year plan hits its floor
**2026-08-09.** Shown the scale (9:00 start = 10 · free Friday at 국제 = 20 · empty week ≈ 96)
and told the threshold was 30, Iden reaffirmed R126: **a 신촌 semester is worth 96+.**

`SINCHON_SEMESTER_VALUE = 96.0`, set as a LOWER bound on what he said.
✅ **Robust:** every value ≥ 40 yields the identical campus plan and the identical Fall 2026
answer, so the exact size is immaterial — only that it clears 30.

### The answer reverted
| | | |
|---|---|---|
| **#1 — 31.632** | defer **Language** | QRM1001 · WCiv · LHP · RDQM · ECO1101 · STA2102 |
| #2 — 31.532 | defer QRM1001 | … UIC1805 … |
| margin | **0.100** | ⚠️ thin |

**Take Intro to QRM now; postpone Language.** This is where the model stood before R196, but
reached through a different route and now against an explicitly confirmed preference.

⚠️ **The margin is 0.100.** Two of today's constants are large and only one is elicited: the
신촌 semester value (96, confirmed) and `SINCHON_PER_COURSE` (17, *derived* from equating a
commuting hour with a dead campus hour — R196's named structural assumption). A 0.1 margin
under a derived 17 is **not a settled answer**, and it should not be presented as one.

### The 4-year plan finally sits at its floor
`['신촌','신촌','국제','신촌','신촌','신촌']` — **2 국제 / 5 신촌**, exactly the forced minimum
(Fall 2026 + one 국제 Spring for QRM3003). Before this constant existed V was voluntarily
choosing 4 국제.

`verify_rank4` 15/15 · `test_weights` 23/23 · `test_retired` 12 hold / 0 uncheckable /
1 broken (mileage data) · both HTML views rebuilt.

## R202. ⛔ I ASKED A QUESTION THE RULE LOG ALREADY ANSWERED — language of instruction
**2026-08-09.** Having found that 173 of 307 OPEN-pool sections are Korean-taught and that no
scoring term touches the field, I presented it as a gap and asked Iden which is harder.

> *"I think I already mentioned this about five times. I explicitly mentioned language does
> not matter, except for you know the CC (has to be english) and Majors (max credit limit to
> Korean)."*

**He is right. It is settled, twice over, and both exceptions are already implemented:**

| exception | rule | live? |
|---|---|---|
| CC requirements must be **English** | **R92** — his own default-assume rule, corroborated by 7 of 7 completed CC courses at 언어='10' | ✅ `rank2.cc_ok` enforces `lang == '10'`. **Measured: 0 Korean-taught sections in WCiv / LHP / SciRD / MR.** |
| Korean 상경·응통 sections cap at 4 courses / 12 cr of **Major Credit** | **R152/R105** — and the cap attaches to the SECTION's offering department, not the language | ✅ `continuation.KOREAN_ME_COURSE_CAP = 4`, enforced in `solve()` |

**Everywhere else language of instruction is NEUTRAL.** There is nothing to add — the correct
size of the term is zero, and zero was already what the model used.

### ⚠️ The finding was real; the conclusion was not
"173 of 307 sections are Korean-taught and nothing prices it" is true and was worth
measuring. **The error was inferring an unpriced factor from an unused field.** A field can be
unused because it is genuinely neutral, and this one is neutral *by explicit instruction,
recorded, more than once.*

### The two things that are NOT the same, and must not be conflated
- **Language of instruction** (`lang == '10'`) — what R92 governs.
- **Offering department** (상경대학 / 응용통계) — what the R152 credit cap governs.
`STA2102-05` in the live #1 is **Korean-taught but QRM-offered**, so R92 does not apply (it is
not filling a CC slot) and the R152 cap does not apply (wrong department). Both correct.

### Standing lesson
Today's five real gaps were all *"a preference stated in prose, absent from the objective."*
That pattern is now so well-established that I applied it to a case where the prose says
**"this does not matter"** — and read the absence of a term as an omission rather than as
compliance. **Before proposing a gap, search the log for the case where the answer is zero.**

## R203. 📦 AUDIT PACKAGE BUILT — generated from source, not written from memory
**2026-08-09.** Iden: *"we can strictly organize the numbers (the code, the data) and the
rules, to the other AI, and see if they can find anything."*

`build_audit_package.py` → `audit/`. **Generated at build time, because every serious defect
today was prose and code disagreeing** — so a hand-written package would reproduce exactly
the failure it is meant to catch.

| file | what |
|---|---|
| `AUDIT_BRIEF.md` | the decision, where to attack, and **the six failure modes already observed** so the auditor goes past them rather than re-deriving them |
| `CONSTANTS.md` | **60** live constants with value, provenance tag and `file:line` |
| `ELICITED.md` | **285** recorded statements by Iden, with rule numbers |
| `OBJECTIVE.md` | the scoring function written out term by term, with each big constant's status |
| `MANIFEST.md` | every file, live vs **superseded** |

The brief's first instruction is the one that matters: **`RULES.md` is evidence of what was
said, never of what the model does.** Those came apart four times today, each time silently,
each time under a green suite.

### ⛔ THE GENERATOR WAS WRONG TWICE, AND BOTH FAULTS WERE THE AUDIT'S OWN DISEASE
1. **53 of 90 "constants" were noise** — `HERE = os.path.dirname(...)`, comprehensions,
   derived objects. An inventory that costs more attention than it returns is worse than
   none. Now filtered to values an auditor can argue with: **60**.
2. **Provenance was read from a fixed 4-line window**, so every constant with a *long*
   rationale came out `[?]` — precisely the constants that most need a correct tag.
   `D_LANG`, `SINCHON_PER_COURSE` and `SINCHON_SEMESTER_VALUE` were all mistagged. Now walks
   the contiguous comment block upward. `[?]` fell 53 → 26.

### ⭐ AND BUILDING IT FOUND A REAL ONE
**`LOW_SUPPLY_MAX = 40` had no justification anywhere and has never been swept.** It decides
*which* items incur a crowding cost at all, so it silently gates the largest term in `V`. The
ledger's supplies are 1, 2, 3, 4, 9, 15, 20, 35, 38, 422 — nothing has ever been tested
between 40 and 300. Now tagged `[P]` and flagged for audit in source.
`GPA_GATE_MULT` was likewise untagged; also `[P]` now.

**Final tally: [E] 18 · [M] 9 · [D] 3 · [P] 4 · [?] 26.** The 26 are mostly structural
(pool sizes, slot counts); the 4 `[P]` are where an auditor should start.

---

## R204. ⚖️ EXTERNAL AUDIT ADJUDICATED — 4 confirmed, 2 refuted, and the refutations are the finding
**2026-08-09.** An independent model audited the `audit/` package **without the source** and
returned ten findings as explicit predictions with one-line checks. All ten were run.

### ✅ CONFIRMED
**F1 — provenance closure fails (its own axiom "A3").** Five rule IDs cited as provenance for
live constants — **R111, R117, R121, R128, R201** — exist in `RULES.md` and have **zero rows**
in `ELICITED.md`. `SINCHON_SEMESTER_VALUE = 96` is tagged `[E] "confirmed (R201)"` and R201 is
unlocatable in the package. The tag is currently unfalsifiable. (The value is separately known
robust for any ν ≥ 40, so the defect is epistemic, not numerical.)

**F2 — `ELICITED.md` is the fifth broken derived view, and it is the one the method runs on.**
Confirmed and **worse than reported: R86, R87, R88, R89, R90 and R91 are ALL duplicated** —
six colliding IDs, not three. Rule IDs are not unique keys, and `test_retired.py` addresses
claims by ID.
⚠️ The 302→285 gap it flagged was my own de-dup fix between builds, not loss. But the
extractor genuinely drops any rule with **no quoted text** — which is how F5 below happened.

**F4 — `RUN_EXP = 1.4` implements the curvature Iden retracted.** Measured increments per
extra free weekday: **13.00 → 21.31 → 26.21 → 30.02 — increasing.** Iden (R141): *"2->3 is
bigger than 3->4"* — decreasing. And **R141's own conclusion agrees with him**: *"the fourth
day is the least valuable as an increment."* The code contradicts the rule written to resolve
it, and the `[1.2, 1.6]` bracket cannot express concavity.
✅ **Swept 0.8 → 1.6: #1 is unchanged at every point.** A real defect that does not move the
answer — which by R187 is a reason to fix it, not to close it.

**F8 — `SINCHON_PER_COURSE` is derived in one unit and applied in another.** R196 derives 17
as *per free weekday* (REST 7 + a round trip 10); the crowding term spends it *per course*.
These differ by the courses-per-day factor. **Correct catch, and the bracket [12,22] is
downstream of it — a bracket cannot detect a unit error.**

**F9a** — `CHAPEL_BONUS`, `N_ACADEMIC`, `MAX_DEFER` are each defined in **both** `rank3.py`
and `rank4.py`. Values currently agree; the duplication is latent, and `rank3.build()` execs
`rank2` source, so a divergence would fail silently.

### ❌ REFUTED
**F5 — the 30% 단순 동영상 cap.** Predicted to be a missing hard constraint that would
invalidate #1. **`R108` refutes it explicitly:** the rule is titled *외국인 학생 단순 동영상
강의 수강 제한 안내*, applies to 외국인 유학생 only, and Iden is not one — *"checked because it
would otherwise have invalidated most of the top-50."* Only 비대면(동영상) counts; 블렌디드 and
비대면(실시간+동영상) are unrestricted.
⭐ **The auditor guessed the exact caveat and could not see the refutation, because R108
contains no quoted statement and `ELICITED.md` extracts only quotes. F2 caused F5.** The
lossy view hid its own refutation — the cleanest possible demonstration of why A1 matters.

**F3 — P(hard) ≡ 0.** The premise is right: `rank2.LANG` and `difficulty.LANG_EASY` **are**
byte-identical narrow sets. The inference is wrong: `p_hard_if_deferred` does not sample from
Λ — it computes `1 − P(win either easy course)` from mileage brackets. **Live value 0.350**,
so the defer term is **−3.50**, not 0.
⚠️ But the observation underneath is a real latent bug: the widened pool reaches the ranker
**only because `rank4_branch.py` sets `R2.LANG` at runtime.** Anything importing `rank2`
without that override silently gets the 2-course pool. Convention, not construction.

### ◐ PARTIAL
**F6** — the `GPA_GATE_MULT` asymmetry is deliberate (deferred difficulty lands *after* the
December gate) but the conclusion stands: **μ cannot argue against the incumbent**, so a sweep
on it is structurally one-sided. And μ multiplies `D_LANG` alone, so the model does assert
that GPA risk is a function of language tier and nothing else.

**F7** — the arithmetic worry is real but does not bite: the ledger reconciles **exactly**
(106.5 = 106.5) because chapel carries the 1.5 at 3 × 0.5, and **`solve()` does not gate on
credits at all** — it gates on slots. No off-by-one exists.

**F10 — the structural test it proposed, run:** `V*` = **86.068** (defer Language) vs
**79.377** (defer QRM1001) — **a 6.691 gap under a 0.100 score margin.** The continuation
*is* discriminating strongly; the near-tie is the immediate term almost exactly cancelling it.
That is a much better description of the decision than "0.100 apart" and it came from the
audit.

### The lesson that generalises
**The two refutations were both caused by the package, not by the auditor.** F5 was refuted by
a rule the extraction dropped; F3 rested on a literal that is true in source and false at
runtime. An auditor given documents can only audit the documents — which is exactly what §0 of
the brief warned, and exactly what the package then made unavoidable by shipping no code.

---

## R205. ⭐⭐⭐ ACTING ON THE EXTERNAL AUDIT — a unit error was real, and the answer flipped
**2026-08-09.** All confirmed findings from R204 fixed. One of them moved the decision.

### ⛔ F8 — THE UNIT ERROR WAS REAL AND MINE
R196 derived `17.0` as the value of **one free weekday** at 신촌 (REST 7 + a 4-hour round trip
priced at his own dead-gap anchor, 10). The crowding term then spent it **per course**.

**A course is not a day. MEASURED over the 341 live sections: a course occupies 1.551
distinct weekdays** — 45% meet on one day, 55% on two. And six courses need **9.3 day-slots
against only 5 weekdays**, so days *saturate*.

⇒ 신촌 crowding is **CONCAVE**, not flat. With each course covering `d/5` of the week,
`E[days | n] = 5(1 − (1 − d/5)ⁿ)`, and the n-th course costs `17 × (the marginal day it opens)`:

| n-th course | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| 국제 (convex, measured) | 0.00 | 17.29 | 19.64 | 24.21 | 31.17 | 38.14 |
| **신촌 (concave, corrected)** | **26.37** | **18.19** | **12.55** | **8.65** | **5.97** | **4.12** |

**A full 신촌 semester: 75.8, not the 102.0 the flat model charged — a 26-point overcharge on
every 신촌 semester, and there are five of them.**
(Convex minorant taken for the slot expansion, exactly as the 국제 curve already gets; the
per-semester total is preserved.)

Pleasingly, the corrected 신촌 shape is **decreasing increments** — the same curvature Iden
described in R141 and that F4 shows `RUN_EXP` still contradicts.

### ⭐ THE ANSWER FLIPPED, AND THE MARGIN IS NO LONGER KNIFE-EDGE
| | before | **after** |
|---|---|---|
| #1 | defer **Language** · 31.632 | **defer Intro to QRM · 152.577** |
| margin over the next family | **0.100** | **2.287** |

The 0.100 tie was an artefact of overcharging 신촌 semesters by 26 points each. **A margin
that thin was never a close decision — it was a wrong constant.**

### Other confirmed findings, fixed
- **F3** — the widened language pool reached the ranker only because `rank4_branch.py` set
  `R2.LANG` at runtime. `rank4.py` now sets it at import: **construction, not convention.**
- **F4** — `RUN_EXP` bracket widened `[1.2,1.6]` → **`[0.8,1.6]`** so a sweep can express the
  concavity Iden stated, with the contradiction recorded at the constant. (Swept: #1 unchanged.)
- **F1/F2** — the extractor now emits a row for **every** rule heading and flags duplicated
  IDs (**R86–R91**). 285 → **374** rows. `test_retired.A3` asserts every rule ID cited in code
  resolves in the log.

### ⛔ AND A3 CAUGHT ME TWICE WITHIN MINUTES OF WRITING IT
1. It failed on **R205** — I cited this rule in a code comment *before writing it*.
2. It then failed on **R95** and **R145**, because my first fix ran the "no quoted statement"
   fallback **before** de-duplication, so a rule whose only quotes duplicated an earlier
   rule's still ended with zero rows. Fixed by moving the fallback after dedup.

**Both were caught by the assertion, not by inspection.** That is the entire argument for
assertions over prose, demonstrated on the assertion written to make that argument.

⚠️ `test_retired` reports **2 broken**: R171b (mileage data, expected) and A3 (this rule,
until this text lands). Re-run after.

## R206. ⛔ I SHOWED A DEGENERATE TIE AS A PLAN — and repeated a false claim twice
**2026-08-09.** Iden, on the 국제 Spring 2027 picture: *"huh? I thought there were many MEs
that were 국제-only"*.

### Two errors, both mine
**1. I told him "QRM electives are 국제-only" — twice.** (When explaining the Korean cap, and
again in the 국제-semester walkthrough.) **False.** Measured in `raw_2026F.json`:

| ME route | where | count | capped? |
|---|---|---|---|
| UIC/QRM-offered sections | **국제** | **13** | no |
| QRM-dept sections | **신촌** | **5** | no |
| 상경대학 경제학전공 | 신촌 | 34 | **yes — 4 courses total** |
| 상경대학 응용통계학전공 | 신촌 | 13 | **yes — same cap** |

So `ME campus='any'` is **correct** and my verbal claim was wrong. His intuition ("many MEs
are 국제") is right about the *composition* — 13 of the uncapped route is 국제 — but not
about exclusivity.

**2. ⭐ THE REAL DEFECT: the plan I displayed was a degenerate optimum.**
`FREE` has supply **422 > LOW_SUPPLY_MAX = 40**, so it incurs **no crowding cost in any
semester**. The solver is completely indifferent to where free electives land. The
"국제 Spring 2027 carrying 4 free electives" I showed him was an **arbitrary tie-break of the
assignment algorithm**, and I presented it as a recommendation.

That is the R179 error in a new place: **a verdict the computation did not produce.** It did
not produce it because on that question the computation *has no opinion*.

### Fixed
`continuation.describe()` now separates **binding** from **free** placements and marks
cost-indifferent items with `*`:

```
sem 3   Spring yr2 국제  (2 binding + 4 free)  FREE* FREE* FREE* FREE* QRM1001 QRM3003
sem 4   Fall   yr2 신촌  (5 binding + 1 free)  DM DM ECO1101 ECO2101 ECO2102 FREE*
* = costs nothing in ANY semester; placement is an arbitrary tie, not a recommendation.
```

**The honest reading of that semester is "2 binding items", not "6 courses".**

### Standing lesson
An optimiser reports *an* argmax, not *the* argmax. Where the objective is flat, the output
is arbitrary — and arbitrary output rendered without a marker is indistinguishable from a
recommendation. **Every display of an optimiser's solution must distinguish the parts the
objective actually determined.** Four of today's defects were derived views disagreeing with
the model; this is the first where the view agreed with the model and the *model had nothing
to say*.

---

## R207. ⭐⭐⭐ QRM1001 MOVES TO FRIDAY MORNING IN SPRING — and V cannot see it
**2026-08-09.** Iden: *"what would my semester actually look like, the last 국제 semester"* —
asking for a real timetable, not ledger items. Answering it with real data found the largest
un-priced quantity in the model.

### The observation, from `mileage_history.json` — two independent terms, same slot
| term | campus | section | **time** | seats |
|---|---|---|---|---|
| 2024-2 | 국제 | QRM1001-01 | **금1,2,3** | 58 |
| **2025-1 (Spring)** | 국제 | QRM1001-01 | **금1,2,3** | 80 |
| 2026-2 (this Fall) | 국제 | QRM1001-01 | 목4,5,6 | — |

**Intro to QRM sits at Friday 09:00–11:50 in the terms on record, and at Thursday afternoon
this Fall.** The live #1 **defers it into a 국제 Spring**, which is exactly the term where the
observed slot is 금1,2,3.

### What that costs, isolating the slot from everything else
Same course, same skeleton week, only the time differs:

| | week | cost |
|---|---|---|
| skeleton, no QRM1001 | 85.855 | — |
| + QRM1001 at **목4,5,6** (its Fall slot) | 52.640 | −33.215 |
| + QRM1001 at **금1,2,3** (its Spring slot) | 27.000 | **−58.855** |
| **the term shift alone** | | **−25.640** |

It kills the free Friday *and* adds a 9:00 start — the two most expensive things in the
weekly model, in one course.

### ⛔ WHY V IS BLIND TO IT — and it is NOT simply "V has no times"
V *does* charge for constrained courses: the crowding curve is a measured "best achievable
week with n low-supply courses". But **that curve was measured with every course at its
FALL 2026 time.** QRM1001 contributed to it at 목4,5,6, which is benign. Its Spring slot is
not. So the curve systematically **under-prices deferring a course whose other-term slot is
worse**, and QRM1001 is the worst case available.

This is G-9 sharpened: not "right instrument, wrong campus" but **"right instrument, wrong
TERM"** — and the error has a sign, because a deferred course is by definition being priced
in a term the measurement did not observe.

### ⚠️ THE MAGNITUDE EXCEEDS THE MARGIN BY AN ORDER
**#1 leads the defer-Language family by 2.287. The un-priced term shift is ~25.6.**
Nothing in the model currently opposes the finding that #1's deferral is under-charged, and
if it were charged anywhere near its measured size, **#1 would flip back to taking Intro to
QRM this Fall.**

⚠️ **Stated as what it is, not more:** Spring 2027's catalogue does not exist. Two prior terms
put QRM1001 at 금1,2,3; one puts it elsewhere. This is evidence about a slot, not a fact about
2027. **It is not a verdict — it is the largest measured quantity the objective does not
contain**, and the honest response is to build the term-aware curve, not to hand-adjust the
ranking.

### What this makes concrete about "the last 국제 semester"
Under #1 there is exactly **one** 국제 semester left (Spring 2027) and it holds **two binding
items**: QRM1001 (deferred, 1 year late, −2.667) and QRM3003 (Spring-and-국제-only, taken a
year EARLY at −4.000). Everything else in it is cost-indifferent filler (R206). If QRM1001
lands at 금1,2,3, that semester also loses the 월+금 shape entirely.

---

## R208. ⭐⭐⭐ THE CORE PROBLEM — the objective has a seam, and deferral crosses it
**2026-08-09.** Iden: *"can we analyze the core problem behind it?"* R205 (unit error),
R206 (degenerate placement) and R207 (term shift) are not three bugs. They are **three
symptoms of one structural fact**, and it is measurable.

### The seam
```
   F(x)  =        r(x)              +      V(σ(x)) − V(ref)
            ┌──────────────┐            ┌────────────────────┐
            │ SECTIONS     │            │ ITEMS              │
            │ real times   │            │ a scalar `supply`  │
            │ exact        │            │ a counting proxy   │
            └──────────────┘            └────────────────────┘
```
**Fall 2026 is scored over sections with real time masks. The continuation is scored over
abstract ledger items with one number each.** The two halves of the objective live in
different spaces, and everything that went wrong in the continuation lives on that seam:

| symptom | the seam showing through |
|---|---|
| **R205** unit error (per-day spent per-course) | items have no days, so day/course could be conflated |
| **R206** degenerate FREE placement | items have no times, so nothing distinguishes where they go |
| **R207** term shift unpriced | items carry one supply, not a per-term slot |

### ⭐ FAULT 1 — `supply` is NOT a sufficient statistic for schedule damage
The crowding curve asserts that *the number of low-supply courses* predicts week quality.
**Measured, within a single requirement pool — identical supply, identical ledger item:**

| pool | n | week damage of one section | spread |
|---|---|---|---|
| LHP | 16 | −107.76 … −40.20 | **67.56** |
| SciRD | 14 | −107.76 … −40.20 | **67.56** |
| Lang | 24 | −107.76 … −103.43 | 4.33 |

**Two sections the ledger cannot tell apart differ by 67.6 in what they do to the week.**
The same fact one level up is R207: QRM1001 at 목4,5,6 vs 금1,2,3 — same course, same
supply, **25.6 apart**. `supply` cannot carry this. It is the wrong statistic, not a
badly-calibrated one.

### ⭐ FAULT 2 — V is an UPPER BOUND, and deferral moves weight into it
V is a **max over placements**, of a curve that is itself the **exhaustive max over
timetables**, with every acquisition at **probability 1.0**. Measured, for a semester
carrying the 4 requirements:

| | week |
|---|---|
| the value the curve uses (exhaustive best) | **35.52** |
| best found in 1,931 random feasible drawings | 22.52 |
| **median** | **−33.50** |
| 10th percentile | −62.05 |

**A typical such semester is ~69 points worse than the number V assumes.**

⇒ `r(x)` is a value he can actually realise; `V` is a best case. **They are not the same
kind of number, and F(x) adds them.** Deferring anything moves weight from the measured
half into the optimistic half — so **the objective systematically flatters deferral**, and
it does so more the more it defers.

That is the core problem. R207 is not "a missing term"; it is this bias becoming visible
because QRM1001 happens to be the course where the term-shift is largest.

### What follows — and what does NOT
- The fix is **not** a hand-adjustment to the ranking (R179).
- The fix is a **sufficient statistic**: replace `supply` with a per-course, per-term
  **schedule footprint** — the actual time mask where known, and a distribution where not.
  Sections already carry it; `mileage_history.json` carries `lctreTimeNm` for other terms.
- And V must stop being a max: a **certainty-equivalent or a quantile**, not the optimum.
  The external auditor reached the same place from Jensen's inequality without the data.
- ⚠️ Both changes push the same direction — **against deferral** — so they must be built and
  reported together, and neither may be adopted because it produces a preferred answer.

**The honest status of the live #1 is therefore: it leads by 2.287 on an objective now known
to be biased in its favour by an amount larger than that margin.**

---

## R209. ⭐⭐⭐ THE FIX — score future semesters from REAL SECTIONS (`semester_sim.py`)
**2026-08-09.** Iden: *"What's the fix?"* R208 established the core problem: Fall 2026 is
scored over real sections at real times, the continuation is scored by **counting**, and
deferring moves a course across that seam into the optimistic half.

**The fix is to delete the seam: score both halves with the same function, on real sections.**

### What `semester_sim.py` does
For a semester's item list, term and campus:
1. Items that map to real course codes contribute their **actual sections**, preferring
   **direct evidence for that term** (`mileage_history.lctreTimeNm`) and falling back to the
   Fall 2026 catalogue **with the substitution reported, never silent**.
2. Filler slots draw from the real catalogue for that campus — **775 real 신촌 sections**,
   not a transplanted 국제 curve.
3. The week is computed with **`fast_score` — the same function Fall 2026 uses.**
4. Pinned requirements are **enumerated**, filler is optimised. The spread across pinned
   choices is the honest uncertainty, not a single point.

### ⛔ FIRST, A CORRECTION TO R207 — I overstated it
R207 said QRM1001 sits at 금1,2,3 in *"two independent terms"*. **One of those (2024-2) is a
FALL term.** The actual **Spring 국제** evidence is **split**:

| term | day |
|---|---|
| 2025-1 | **금** (Friday) |
| 2026-1 | **목** (Thursday) |

So it is not reliably Friday. The simulation handles this correctly by enumerating both and
taking the median — which is the whole point of not collapsing to one number.

### ⭐ THE MEASURED RESULT — and it survives the correction
The 국제 Spring is the ONE place the two live candidates differ, and it is now scorable:

| that semester holds | best week |
|---|---|
| QRM3003 only, 5 filler | **114.37** |
| + QRM1001 at 목 (2026-1) | 88.71 |
| + QRM1001 at 금 (2025-1) | 91.66 |
| **median with QRM1001** | **90.19** |

> **Cost of deferring Intro to QRM into that semester: −24.18**
> The model charges **−2.667** (year gap) plus crowding.
> Fall 2026 favours deferring by **+2.29**.

**The correction is roughly ten times the margin, and points the other way.** Even the
*better* of the two observed Spring slots (Thursday, −22.7) exceeds the margin by 10×.

### ⛔ AND THE SIMULATOR'S OWN FIRST BUG, CAUGHT BY ITS OWN SANITY CHECK
The first version shuffled the filler pool **randomly** and truncated to 140. That made
branches incomparable: a pinned course could be lighter than anything surviving in the pool,
so **adding a constraint appeared to IMPROVE the week** — impossible, since `fast_score` is
monotone. It produced a headline number (`B beats A by 34.18`) that was **not reported**,
because the monotonicity check ran first and failed.
Fixed by keeping the **lightest** distinct masks — what an optimiser would use anyway.

*The check that caught it is the same monotonicity property proved for `_crowd_curve.py`.
A property proved once for performance turned out to be the correctness test.*

### What remains before this replaces V
`semester_sim` currently scores **one semester in isolation**. Wiring it into `continuation.
solve()` means the placement search can no longer use the Hungarian (the cost stops being
separable per slot) — it needs a local search over placements. That is the next build, and
until it lands the live ranking still uses the counting proxy.
⚠️ **Do not hand-adjust the ranking by 24.18 in the meantime (R179).** The number is
evidence that the objective is biased, not a correction to paste into a score.

---

## R210. ⭐ 동영상콘텐츠 HOURS ARE SHIFTABLE — three masks, each with one job
**2026-08-09.** Iden, on whether a recorded-video hour is a real commitment:
> *"let's treat it as it is — it is a real commitment, but it exists at the best possible
> hour (maybe even saturday)."*

That is not "it costs nothing". It is **"it costs, but it does not pin the shape of the
week"** — he moves it to whatever hour is cheapest, and at the optimum that is an
already-busy day or the weekend.

### The model had two masks and needed three
| mask | job |
|---|---|
| `tm` nominal hours | **conflict detection only** — registration blocks overlaps regardless |
| **`fm` FIXED hours** ⭐ new | **all comfort scoring**: 9am starts, lunch, runs, REST, the Friday event |
| `pm` presence | the trip home |

`fm = pm | (online hours IF the mode is 실시간)`. In-person hours are always fixed; a **live**
online hour is fixed; a **recorded** one is not.

| mode | sections | shiftable? |
|---|---|---|
| 대면강의 | 283 | no |
| 블랜디드(동영상) | 55 | **9 of them** |
| 비대면(동영상) | 2 | **yes** |
| 비대면(실시간+동영상) | 1 | no — treated conservatively, the live half cannot be separated |

**Effect on the live #1: +8.000.** Its Major Elective (STA2102-05, 블랜디드) has shiftable
hours that were pinning the week for no reason.

⚠️ `fast_score(tm, pm, fm=None)` falls back to `fm = tm`, so every un-updated caller keeps
the OLD behaviour rather than silently mixing conventions. `rank4_branch` and `verify_rank4`
now pass it explicitly; the sweeps still use the old default and are flagged.

## R211. ⭐⭐⭐ V REBUILT ON REAL SECTIONS — and the answer flips to TAKING Intro to QRM
`continuation_sim.py`. The Hungarian had to go: it needs the cost to be separable per slot,
and once a semester is scored from real sections a course's damage depends on what shares its
days. Replaced with **steepest-ascent local search**, same feasibility rules, seeded from the
old solution.

### ⛔ FOUR BUGS, ALL CAUGHT BY READING ITS OWN OUTPUT
1. **Mutating `assign` mid-iteration** — the swap loop `.remove()`d from a stale list. Fixed
   with snapshot neighbour generation.
2. **Courses with no section data VANISHED.** QRM3003 and MR5 have codes but no observed
   times anywhere, so they were "pinned", contributed nothing, and then **occupied no slot
   and cost nothing** — a 국제 Spring holding four requirements scored like an empty one.
   Fixed: an untimeable course is still a course; it becomes filler.
3. **Empty semesters were REWARDED.** Scoring the raw week means an empty semester earns the
   maximum, and the search duly emptied one. Fixed by scoring **damage relative to the empty
   week**, so an empty semester is exactly 0.
4. **⭐ THE COMPARISON BUG — the same shape as the filler-pool bug.** The local search moves
   items but inherited the campus pattern from its seed, so the two candidates were compared
   under **different campus patterns** (2 국제 vs 3). At 96 per 신촌 semester that alone
   dwarfed everything being measured. Fixed by enumerating all minimal-국제 patterns — R144
   fixes the minimum at 2, so exactly one of sems 3-8 is 국제 and it must be a Spring:
   **three patterns, all evaluated.**

### ⭐ THE RESULT, end to end, both candidates rebuilt under R208 + R210
| | Fall week | Fall r(x) | simulated V | **TOTAL** |
|---|---|---|---|---|
| **A** defer Intro to QRM *(the live #1)* | 17.89 | 23.89 | 29.56 | **53.45** |
| **B** defer Language | 17.89 | 16.39 | **66.72** | **83.11** |

> **B − A = +29.66.** Fall favours A by 7.5; the future favours B by 37.2.

**The corrected objective says: take Intro to QRM this Fall and defer Language** — the
opposite of the live ranking, and the same direction as the isolated measurement (R209, 24.18)
and the raw term-shift (R207).

### ⚠️ WHAT IS AND IS NOT SETTLED
- `continuation_sim` is **not yet wired into the branch search.** Running a local search
  inside a 7,200-candidate enumeration is not tractable as built, so `FINAL_ranked4.csv` still
  ranks on the counting proxy. **The live #1 is therefore still A**, and it is now known to be
  ranked by the objective R208 proved biased.
- Local search returns a **lower bound** on each candidate, not a proof of optimality.
- QRM3003 and MR5 have **no observed times anywhere** — they are filler in every branch, so
  they cannot distinguish the candidates. Symmetric, but it means the 국제 Spring is scored
  with two of its courses untimed.

**Artifacts re-run under R210:** `verify_rank4` 15/15 · `test_weights` 23/23 ·
`test_retired` 13 hold / 2 broken (mileage data, and A3 pending this text) ·
`TOP50.html` + `ALTERNATIVES.html` rebuilt.

---

## R212. ⛔ THE COMPARISON WAS TWO CASES; THE SPACE IS NOT TWO CASES
**2026-08-09.** Iden:
> *"You are just comparing A and B traditionally, right? The scorer doesn't treat the two
> like C doesn't exist? (both defer / both keep)"*

Right on both halves, and the second half is worse than the first.

### (a) 'defer nothing' existed and I never re-measured it
`continuation_sim.__main__` hand-wrote **two** cases. The ranker has **six** branches. Since
R208's finding is that the old objective *flatters deferral*, the branch that defers nothing
is exactly the one the correction should help most — and it was the one left out.
`compare_branches.py` now runs the corrected V on **every** branch, reading r(x) and the
elective items **from the CSV** rather than retyping them.

⛔ And the retyping had already bitten: the hand-written B used elective items
`('ECO1101','ME')`, which belong to the **WCiv** branch, not Lang. It happened not to move
the number, which is luck, not method.

| branch | ranked (proxy) | r(x) | **V (simulated)** | **TOTAL** |
|---|---|---|---|---|
| defer Lang | 158.290 | 16.391 | 66.721 | **83.111** |
| defer LHP | 151.790 | 9.891 | 66.721 | **76.611** |
| defer WCiv | 157.552 | 18.319 | 43.284 | **61.603** |
| defer MR *(ranked #1)* | 160.577 | 23.890 | 29.559 | **53.449** |
| **defer nothing** | 149.548 | 10.315 | 42.396 | **52.711** |
| defer SciRD | 155.090 | 13.191 | 35.625 | **48.816** |

'Defer nothing' lands **5th of 6** — it is not the answer, but that is now a measurement
instead of an omission.

### (b) ⭐ 'defer two' was not ranked low — it was NOT IN THE ENUMERATION
`BRANCHES = ['-', 'MR', 'WCiv', 'LHP', 'SciRD', 'Lang']`, and `defer = (name,)`. The search
space was *defined* as "defer at most one requirement." Nothing chose that; it was never a
decision. Fall holds `N_ACADEMIC = 6` courses either way — 4 requirements + 2 electives, or
**3 requirements + 3 electives** — so the remainders hold the same NUMBER of items and the
branches are directly comparable.

A branch name may now be a `+`-joined set. Two of the ten pairs have been run:

| branch | proxy | r(x) | V (sim) | **TOTAL** |
|---|---|---|---|---|
| **defer Lang+LHP** | 175.046 | **51.335** | 78.106 | **129.441** |
| defer Lang+SciRD | 168.260 | 23.694 | 81.806 | **105.500** |

> **Deferring two beats every single-deferral branch by 46.3.** The Fall week improves by
> 35 points, because a requirement pool offers a handful of sections at fixed hours while an
> elective can be cherry-picked.

⚠️ **Eight pairs, and every triple/quadruple, are still unenumerated.** Removing a large
requirement empties the Fall timetable, so the 3-elective recursion explodes and the branch
exceeds the wall-clock limit. `BRANCH_FLOOR` and `NO_INCUMBENT` were added to control the
prune, and an empty branch now reports its floor instead of raising `IndexError`.
The pair parts are deliberately **NOT** in `BRANCHES`, so they do not enter
`FINAL_ranked4.csv` — `TOP50.html` still shows the single-deferral world.

### ⛔⛔ THE OPEN QUESTION THIS RAISES, UNANSWERED
If swapping a requirement for an elective gains 35 points of Fall week and the future absorbs
it, **what stops the model from deferring all five?** Defer-5 is a legal branch: 0
requirements, 6 electives. If it wins, there is a leak; if it loses, the trade-off is real
and has a turning point. **That test has not been run.** Until it is, the defer-two result is
a measured lower bound on the space, not a recommendation.

## R213. ⭐ V IS MONOTONE — the defer-two result is not the seam bug wearing a new hat
`test_v_monotone.py`. A constraint must never improve the objective. Adding one required item
to the remainder, measured:

| added | ΔV | | added | ΔV |
|---|---|---|---|---|
| +LHP | −12.333 | | +MR5 | −15.000 |
| +WCiv | −59.919 | | +ME | −38.325 |
| +SciRD | −46.096 | | +ECO1101 | −62.615 |
| +FREE | −12.333 | | | |

**0 violations.** Every added item costs; deferring more can only lower V. So `defer Lang+LHP`
having a *higher* V than `defer Lang` (78.106 vs 66.721) is not non-monotonicity — the two
remainders differ in composition, and the step-by-step decomposition says exactly why:

```
defer Lang   66.721
  +LHP       54.388   -12.333   the extra deferred requirement
  +ME        23.054   -31.334   the elective slot given back
  -ECO1101   64.106   +41.052   ⭐ taking ECO1101 NOW is worth 41 to the future
  -FREE      78.106   +14.000
defer Lang+LHP 78.106
```

The whole of the pair branch's continuation advantage is **taking ECO1101 in Fall**, not
deferring more. ⚠️ Note also that removing one ECO1101 is worth +41.05 while adding a second
costs −62.62: the item is **not** linear, which is the same crowding non-linearity that killed
the Hungarian (R211).

---

## R214. ⭐⭐ IT WAS NOT IMPLEMENTED — and the branch set was PREDECIDED
**2026-08-10.** Iden, on the last report:
> *"are you saying you didn't implement the logic yet? Because #1 shows up as A. And why were
> the branches biased? Every possibility should just be numerically computed, not predecided."*

Both charges land.

### (a) The corrected V was never in the ranker
R211 measured the corrected objective for two candidates **beside** the ranker and left
`FINAL_ranked4.csv` ranking on the proxy. So `TOP50.html` displayed a #1 the model itself put
4th. I had written that wiring it in was intractable. **That was wrong, and the reason is
embarrassing:** `rank4.V` is memoised on `(deferral subset, elective item multiset)`, and the
items take only three values — so the key space is **417 states**, not thousands of
candidates. One local search per state, cached to `vsim_table.json`, and the ranker optimises
the corrected objective directly. `build_vsim_table.py`, resumable, ~7 minutes total.
`V_SIM=1` switches it on and a missing key **raises** rather than falling back to the proxy.

### (b) `MAX_DEFER = 1` — a proof that had expired
The branch list was `['-', 'MR', 'WCiv', 'LHP', 'SciRD', 'Lang']` and `defer = (name,)`.
That came from **R121**, which proved 2-deferrals could not win — and whose own last line
reads: *"this proof is incumbent-dependent and must be re-run whenever the pool or the
optimum changes."* The objective has changed twice since (rank4's computed V, then R208's
simulated V). The proof expired; the cap survived. That is how a computed result turns into
a predecision.
`BRANCHES` is now the **generated powerset — 32 branches**, and `MAX_DEFER` defaults to 5.

## R215. ⛔ 145 OF 417 CONTINUATION STATES WERE POISONED
`continuation_sim.semester_week` scored **−1e6** whenever `SIM.semester_week` returned None —
i.e. whenever every choice of the pinned sections conflicted. A third of the table came back
poisoned, and the local search was navigating a landscape of −1,000,000 cliffs.

The inference was wrong. Two courses colliding is a fact about the **Fall 2026 catalogue
standing in for a future term** — `semester_sim` flags exactly that as `stand-in ⚠️` — not a
fact about 2028. Correct handling is the rule already in the same function: *a course we
cannot time is still a course*. Pinned courses are now demoted to filler until the semester
resolves. **Poisoned states after the fix: 0 / 416.**

⚠️ **R212's defer-two numbers were computed on the poisoned table and are RETRACTED.**
`Lang+LHP = 129.441` was a comparison against poisoned alternatives. Under the clean table
every 2-deferral branch loses.

## R216. ⛔ MERGE ACCEPTED AN EMPTY WINNING BRANCH IN SILENCE
An empty part file is legitimate — a branch whose ceiling is below the incumbent keeps
nothing. Which is exactly why it must be loud. A timed-out re-run left `rows: []` in the
**winning** branch's part file, `merge` took it without comment, and the global optimum
vanished from `FINAL_ranked4.csv`; #1 reverted to a branch scoring 24 points lower and every
downstream artifact agreed with it. `merge` now prints rows / best / floor for all 32 branches
and flags any branch that is empty while its floor sits below the merged winner.

## R217. ⛔⛔ I INTRODUCED AN UNSOUND PRUNE, AND THE SEARCH PRODUCED THE COUNTEREXAMPLE
The branch-and-bound used a stand-in ceiling of 276.0 for the weekly score — true but
useless, since real weeks are 10–30. I replaced it with `fast_score(t, p, f)` at the node,
arguing fast_score is monotone decreasing in occupancy. Branch times fell from >160 s to 1 s.

**It is not monotone, and the search said so out loud:** branch `WCiv+LHP+Lang` returned
**101.544 with the floor at 64.779** and **EMPTY with the floor at 100**. A bound that
discards a candidate the same code can find is unsound. The cause is obvious in hindsight —
**adding a course can FILL A HOLE**, and hole penalties are in the score. The monotonicity
"proof" (0 violations / 4,000 random pairs) *sampled*; it did not prove.

⚠️ **101.544 was never achievable.** That branch's true ceiling is
`VMAX_FULL − V_REF = 35.71`, and its real best is **85.865**. An unsound bound does not only
lose candidates — it can report a score no timetable has.

**The sound tight bound.** `fast_score = week_value(pm, fm) + Σ day_pen`, and the halves
differ: `day_pen` is a penalty (max over 200,000 random days = exactly **0**), while
`week_value` IS monotone decreasing (0 violations / 20,000). So the node's own **free-day
value alone** bounds every completion below it — tight, and true, because the hole-filling
that breaks `fast_score` lives entirely in the half this bound throws away.

⚠️ `semester_sim.best_week` still prunes on `fast_score` and inherits the same unsoundness.
Its 60,000-node budget already makes it approximate, so V is a **lower bound** either way —
but this is now a known defect, not an assumption. **OPEN.**

## R218. ⭐⭐⭐ THE POWERSET OPTIMUM EXPLOITS R210 — 동영상 COURSES ARE FREE
With all 32 branches searched under the corrected V, #1 is:

```
88.970  defer LHP+SciRD+Lang   free 월화수금   chapel deferred
        QRM1001-01  UIC1561-01 | UCB1105-02  YCG1804-01  YCG1853-01  UCD1101-01
        items: FREE FREE FREE FREE          week 96.670
```

A week of **96.670** against a typical 22. The reason is in the modes:

| section | mode | nominal | **fixed (fm)** |
|---|---|---|---|
| YCG1804-01 | 비대면(동영상) | 3h | **0h** |
| YCG1853-01 | 비대면(동영상) | 3h | **0h** |

R210 implements "a 동영상 hour is shiftable" as `fm = 0` — the course occupies **no** fixed
hour, so it costs the comfort score **nothing at all**. The optimiser found the two sections
in the entire catalogue for which that is true and stacked them.

**This is the model behaving correctly and thereby exposing a hole in itself.** Iden's rule
was *"a real commitment, but at the best possible hour (maybe even Saturday)"* — and under the
model's own accounting a Saturday recorded hour costs exactly zero: it takes no presence
(no trip lost) and no weekday fixed hours (no REST lost). The cost of a 동영상 course is
**workload**, and workload is not in the model. Nothing prices six courses' worth of effort.

Its four electives are `FREE FREE FREE FREE` — **four free electives in one semester**, out of
roughly five for the whole degree. That is R181's test, and it now FAILS. It is also precisely
the objection Iden raised at the start of this project about *two*.

> **⛔ #1 IS NOT A RECOMMENDATION. It is a measurement of a missing cost.** Do not register
> from it. The powerset search did its job — it found the corner of the space where the model
> stops describing reality.

**Retirements broken by this run: R160, R174, R181, R171b, A3** — five, listed and not
edited away.

---

## R219. ⛔⛔⛔ REVERTED — and the reason is a lesson about the last four rules
**2026-08-10.** Iden: *"uh… don't you think something has gone very wrong?"* — then
*"can we revert back to the last 50."*

Yes. Reverted. `FINAL_ranked4.csv`, `TOP50.html` and `ALTERNATIVES.html` are back to the
R210 proxy ranking, and every branch best reproduces to the digit:

| branch | best |
|---|---|
| **MR** | **160.577** ← #1, `UIC1561 UIC1551 UIC2151 UIC1805 \| ECO1104-06 STA2102-05`, items ME ME, free 월금 |
| Lang | 158.290 |
| WCiv | 157.552 |
| SciRD | 155.090 |
| LHP | 151.790 |
| – | 149.548 |

`verify_rank4` 15/15 · `test_weights` 23/23 · `test_retired` 14 hold / 1 broken (R171b,
mileage data — the same one that was broken before any of this).

### WHAT ACTUALLY WENT WRONG
**1. V degenerated back into the counting proxy.** 416 states, **70 distinct values**;
27 states share exactly −50.419, 22 land exactly on V_REF. The cause is in the ledger, not
the search: **DM×12 and FREE×5 carry no course codes**, so 17 of ~40 future courses are
interchangeable filler from one lightest-first pool; and **every ME pins the same code
QRM2004**, so two MEs in a semester collide and R215 demotes one to filler. What survives is
"how many identifiable courses per semester" — which is the statistic R208 condemned.
**I rebuilt V out of real sections and it collapsed back into counting, and I checked it for
monotonicity and poisoning but never for whether it DISCRIMINATES.**

**2. A flat V leaves the ranker nothing to maximise but the week** — so it found the two
비대면(동영상) sections that cost the comfort score exactly zero and stacked them. R218 called
that "a measurement of a missing cost." It is better described as **a flat objective meeting a
zero-cost loophole**, and dressing it up as a finding was wrong.

**3. Three of my four "improvements" to the search were defects.** `fast_score` as a bound —
unsound, and it reported 101.544 for a branch whose ceiling is 35.71 + week. `week_value` as a
bound — sound, and it STILL lost candidates: 'defer nothing' fell from 149.548 to 76.116 with
one row kept. Rewritten `gains`/`VMAX` — same. All restored verbatim. The scoring was never
at fault: the old #1's dV still reconstructs to 136.687 through every version.

> ⛔ **THE RULE THIS SESSION EARNS.** A change to a SEARCH'S BOUNDS is not verified by
> arguing it is sound. It is verified by re-deriving a KNOWN ranking. Three separate bound
> rewrites survived my reasoning and died instantly against 149.548.

### WHAT IS KEPT, AND WHAT IT IS WORTH
Kept and OFF by default: `V_SIM=1` (the 417-state simulated table), `POWERSET=1` (32
branches), `build_vsim_table.py`, `continuation_sim.py`, `compare_branches.py`,
`test_v_monotone.py`. The powerset machinery is right in principle — R121's cap really had
expired — and it is **useless until V discriminates**. Fixing V means giving DM, FREE and the
individual MEs real identities, not another optimiser.

⚠️ **The live #1 is the pre-R208 objective.** It is known to favour deferral, measured at
roughly **−24 per deferred course** (R209). Deferring Intro to QRM is exactly the decision
that bias flatters. **That caveat rides with the artifact.**


---

## R220. ⛔ RESIDENCE RESTATED — the fact was in the model, the paraphrase was not
**2026-08-10.** Iden: *"I do not live at the 국제 campus right now."* Then: *"I think I
specified that connected days to the weekend had high score ESPECIALLY DUE TO THEM BEING
RELATED TO ME BEING ABLE TO BE AT HOME, SPECIFICALLY WHY ONLINE CLASSES DON'T COUNT FOR
'HOME', within the timetable. How do you forget what YOU made"*

**The record, R129, 2026-08-07:**
> *"actually 국제 is a dorm, and 신촌 is commute from home, so next semester will be
> auto-dorm. But I do go home in weekends, or, if consecutive, fridays, mondays, or any other
> weekday that is connected-ly free."*

**Correct statement.** Iden lives at HOME. 국제 is a dorm, auto-assigned for semesters spent
at 국제. 신촌 semesters are commuted from home daily. Home is ~2h from 국제. He is not at 국제
between semesters.

**The model already encodes this and needs no change.** TRIP is measured on the PRESENCE mask
precisely because the good is being at home, so an online class cannot break a trip; REST is
measured on the FIXED-HOUR mask because an online class is still work. The 국제 convex /
신촌 saturating crowding split (R195) rests on the same fact.

**What was wrong was one sentence I wrote in `HANDOFF_2026-08-10.md`:** *"Lives at the 국제
campus (dorm)"* — copied from my own paraphrase at the top of `rank2.week_value`'s docstring,
which reads *"Iden lives at 국제 (dorm)"*. Iden never said that. On being corrected I treated
it as a possible threat to the TRIP/REST foundation and drafted a question about re-deriving
those constants, when the foundation is built on the opposite of what I had written.

⚠️ The `rank2.py` docstring cannot be fixed: it is **above** the exec marker
`    heap = []; cnt=[0]`, which `rank3.build()` execs. An attempted edit was refused by an
index check before it was written. `HANDOFF_2026-08-10.md` §10 now flags the docstring as
wrong and points to §1.

⭐ **The general rule.** Elicited facts are stored in `RULES.md` as QUOTES. Every restatement
in a docstring, handoff or summary is a lossy copy, and the copies are what get read next
session. When a fact about Iden is repeated anywhere, quote R-number and words — the two
places this went wrong were both paraphrases with no quote attached.

---

## R221. ✅ W_E2 CONFIRMED — the last unelicited schedule constant is now elicited
**2026-08-10.** Asked, after `PURPOSE_CHECK_2026-08-10.md` measured that `W_E2` fires in
**34 of the top 50** while carrying a `[P] 미확인 추정치` flag since session 1:

> *"3. 10am about half is right."* — Iden, 2026-08-10

**`W_E2 = -5.0` (`rank.py:12`) is correct and is now [E], not [P].** Half of `W_E1 = -10.0`.
No code change: the live value already equals the elicited one.

**Closes:** `DECISIONS_NEEDED.md` V-1 · the `[P]` tag on `rank.py:12` in `audit/CONSTANTS.md`.
This was the **only** schedule constant with no statement behind it. Every weight in
`day_pen` now traces to something Iden said.

---

## R222. ⭐ SUBJECT INTEREST IS OUT OF SCOPE — BY INSTRUCTION, AND THE DELIVERABLE CHANGES SHAPE
**2026-08-10.** Asked whether "whether you want the subject" (G-15, `GAPS.md` Tier 3,
`PURPOSE_CHECK` §6-E) should enter the objective:

> *"4. Just give me the best 50 schedules structurally, and I'll personally choose based on
> which courses sound interesting."* — Iden, 2026-08-10

**Do not model subject interest, professor quality, or course appeal. Ever.** They are applied
by Iden, by hand, to a shortlist. G-15 is CLOSED as out-of-scope, not deferred.

⚠️ **But the instruction has a second half that the model currently fails.** If Iden picks on
course identity, the shortlist must offer distinct course identities. Measured on the live
`FINAL_ranked4.csv` top 50:

| | |
|---|---|
| distinct section sets | 28 / 50 |
| **distinct COURSE sets (section number ignored)** | **9 / 50** |
| distinct weekly grids | 13 / 50 |
| distinct (deferral, free-days) | 4 / 50 |
| free days | 월금 in **50 / 50** |

**28 of the 50 rows are the same courses on the same grid as an earlier row.** The shortlist
presents 50 options and contains 9.

Cost of fixing it, measured over the full 7,200:

| shortlist keyed on | 50 reached at rank | score there | cost vs #1 |
|---|---|---|---|
| distinct COURSE SET | 342 | 146.767 | **13.810** |
| distinct COURSE SET + GRID | 108 | 151.590 | 8.987 |
| distinct GRID | 215 | 148.777 | 11.800 |

**13.810 is smaller than the model's own known deferral bias (≈24, R209)** and is 27% of the
total spread of the entire candidate set (51.836). The ranking is not precise enough to
justify spending 41 of Iden's 50 choices on relabelings.

⭐ **`render_top50.py` must deduplicate on the COURSE SET, not the row.** The ranking itself
does not change; the view does.

---

## R223. ⭐ THE OBJECTIVE IS RIGHT IN SHAPE — AND THE COMFORT TERM IS INCOMPLETE BY HIS ACCOUNT
**2026-08-10.** Asked whether the reconstructed objective (`PURPOSE_CHECK_2026-08-10.md`) is
the thing he wants maximised:

> *"1. Yes. My objectives are comfortable current week + good long-term degree planning +
> avoiding undesirable course timing/difficulty. However, I'm not sure the code entirely
> supports that at the moment."* — Iden, 2026-08-10

Three objectives, mapped to the live terms:

| his words | live term | status |
|---|---|---|
| comfortable current week | `week_value` + `day_pen` | ⚠️ **incomplete — see below** |
| good long-term degree planning | `ΔV` | ⚠️ 7 distinct values over 7,200 candidates |
| avoiding undesirable course **timing** | `day_pen` | same gap as row 1 |
| avoiding undesirable course **difficulty** | `difficulty.py` | **10 courses of ~700 carry any difficulty at all** |

And on what should separate two timetables that both give him 월+금 free — the question
`PURPOSE_CHECK` §6-B raised after measuring that `week_value` spans only 7.000 across two
values in the top 50, while `day_pen` spans 19.700:

> *"2. A lot of factors, actually. Holes, 9am starts, and late finishes are only a part of
> it."* — Iden, 2026-08-10

⛔ **`day_pen` is INCOMPLETE and he has said so.** Its seven terms (E1, E2, LUNCH, DINNER,
MARATHON, HOLE, LATE) are not the whole comfort model. **The factors have not been named
yet** — asking for their weights before their identity would be R136 anchoring. Elicit the
LIST first (existence, not magnitude), then price by state comparison per R141.

**This is now the largest open item that is not blocked on data**, because it governs the
term with the widest measured spread inside the shortlist.

---

## R224. ✅ `day_pen` IS ADEQUATE — a NULL result, banked deliberately
**2026-08-10.** `PURPOSE_CHECK` §6-B measured that `week_value` spans only 7.000 across two
values inside the top 50 while `day_pen` spans 19.700, and Iden had said (R223) that holes,
9am starts and late finishes are *"only a part of it"*. Asked to name the rest:

> *"I genuinely can't think of another factor abstractly right now, and I don't want to invent
> one just because we expect `day_pen` to be incomplete. … don't treat my earlier statement
> … as proof that another factor must exist. If nothing consistently surfaces from actual
> comparisons, I'm fine concluding that `day_pen` may already capture most of what I care
> about."* — Iden, 2026-08-10

Then, after the instrument was scrapped (below):

> *"1. I feel like `day_pen` is adequate."* — Iden, 2026-08-10

**`day_pen`'s seven terms are the comfort model. Do not add an eighth without a statement.**
R223's "only a part of it" is **withdrawn as evidence of a missing factor** — it was an
impression, offered abstractly, and he declined to convert it into one. This closes the
largest item that was not blocked on data, as a null.

### ⛔ AND THE INSTRUMENT I BUILT TO TEST IT WAS INVALID — two separate faults
`WEEK_PAIRS.html` (8 blind matched pairs, course set held constant) was **scrapped unused**.

1. **The pairs were drawn from the shortlist he registers from.** Pair 5 held rank 1; pair 7
   was rank 1 against rank 2. "Which week do you prefer" was therefore literally "pick your
   timetable", and any weight fitted afterwards would have been a rationalisation of that
   pick, spread over 7,200 rows to look computed.
2. **I narrated the stratification** — that some pairs were exact model ties, and what a
   preference on a tie would imply. That makes the judge reason about the instrument.

> *"The exact point is that I shouldn't know. The point of this system is to find the optimal
> timetable through numbers, not find the timetable first. If that was the case, I don't need
> this program."* — Iden, 2026-08-10

⭐ **THE RULE THIS EARNS.** *An elicitation is valid only if the object judged is NOT in the
decision set.* A preference over states may constrain a weight; it may never select an
outcome. If a probe week could be registered, the elicitation is circular. Probes must be
unregistrable by construction — wrong credit count, missing requirements, any shape that
cannot be an answer. Alongside R136 (don't anchor), R137 (don't offload modelling) and R141
(elicit states, never increments).

---

## R225. ⛔⛔ THE FOUR-YEAR LAYER IS NOT ADEQUATE — AND IT ALONE DECIDES #1's DEFERRAL
**2026-08-10.** Iden: *"is the 4-year plan adequate?"* Measured, three ways.

### 1 · V discriminates the Fall 2026 decision into SEVEN buckets
Over all 7,200 ranked candidates, ΔV takes **7 distinct values** across **12 reachable
states**. Its composition, per state: `96.0 × 5 신촌 = +480.000` — **identical in every one**,
so the largest constant in the model does no ranking work — minus crowding (−210 to −230)
minus future year-gaps (−2.67 to −20.42). The variation is crowding, and crowding is gated by
`LOW_SUPPLY_MAX = 40`, under which every ledger item except `FREE` (supply 422) is "scarce".
**So V ≈ count of non-FREE courses per future semester** — R208's condemned statistic, live.

### 2 · Three treatments of V give three different #1s
| treatment of V | #1 defers |
|---|---|
| as shipped (counting proxy) | **MR — Intro to QRM** |
| flattened (ΔV := 0 for all) | **Language** |
| corrected for R209's measured bias | **nothing** |

**The deferral — the most consequential feature of the recommendation — is decided entirely
by the weakest term in the model.**

### 3 · The live #1 does not survive its own model's documented error
R209 measured the proxy's pro-deferral bias at **≈24 per deferred course** (the proxy counts
the future while Fall 2026 is scored over real sections at real hours; deferral crosses that
boundary). Sweeping a correction `k` per deferred requirement:

| k | winner | margin |
|---|---|---|
| 0 | defer MR 160.577 | 2.287 over defer Lang |
| 9 | defer MR 151.577 | 2.029 over defer nothing |
| **11.029** | **SWITCHES** | |
| 24 (measured) | **defer nothing 149.548** | **12.971** over defer MR |

**Exact switching threshold k = 11.029, against a measured bias of ≈24.** The live #1
survives less than half of the error its own documentation records.

⭐ **The 'defer nothing' branch is the only one not exposed to this bias** — it moves no
requirement across the real-hours/counted-items boundary. Its best row is **rank 179,
149.548**, 월+금 free, 18 credits, and it takes the **hard-tier** language YCF1603 (−10
difficulty) because filling all five requirements plus an elective leaves no easy-tier fit.
The best defer-nothing row with an easy-tier language is rank 785/786 at 140.798.

### What would make V adequate
Not an optimiser change (R219 proved that three times). `plan_model.ITEMS` must give course
identities to the placeholders: **`DM` (12 courses — 36 credits, the largest single block of
the remaining degree, `codes=[]`)**, `FREE` (5, `codes=[]`), and the six `ME` slots which
resolve to two codes. `DM` cannot be filled before the December decision (R147). **So V
cannot be made adequate before 8/25, and the 8/25 decision should not rest on it.**

---

## R226. ⭐⭐⭐ V's THREE TERMS: TWO ARE PROVABLY INERT, THE THIRD IS THE WORST-EVIDENCED
**2026-08-10.** Iden: *"how do we really rethink V. Right now it's a half-broken deferral cost
model. It doesn't even need to be fixed, it can be divided into multiple factors, or upgraded,
reworked… etc to match the actual purpose."*

Each scoring term in `continuation.solve` switched off in turn; all 7,200 candidates re-ranked.

| variant | #1 defers | margin | branch order |
|---|---|---:|---|
| A current (crowd + year + campus) | MR | 2.288 | MR > Lang > WCiv > SciRD > LHP > – |
| B campus bonus off | MR | 2.288 | MR > Lang > WCiv > SciRD > LHP > – |
| C crowding off | **Lang** | 7.450 | Lang > SciRD > WCiv > LHP > MR > – |
| D year-gap only | **Lang** | 2.196 | Lang > MR > SciRD > WCiv > LHP > – |
| E V flat | **Lang** | 2.196 | Lang > MR > SciRD > WCiv > LHP > – |

- **A ≡ B to three decimals** ⇒ `SINCHON_SEMESTER_VALUE = 96.0` (+480.000 per candidate,
  the largest constant in the model) is **inert**. R126 already said π = 5 is INVARIANT; the
  code priced it anyway. It belongs in `test_retired.py` as an assertion, not in the score.
- **D ≡ E** ⇒ the **future year-gap is inert for branch order** too.
- **A ≠ C** ⇒ **crowding alone decides the deferral**, i.e. the whole registration verdict
  rests on a curve measured on the Fall 2026 국제 catalogue, applied to 신촌 2029 (G-9), gated
  by `LOW_SUPPLY_MAX = 40` which `continuation.py:185` itself calls *"never justified or
  swept"*, and reducing to a count of non-free courses per semester — R208's condemned
  statistic.

### ⛔ A REPLACEMENT THAT FAILED — recorded so it is not retried
Proposed: score **flexibility** (how many futures survive) instead of the value of the best
future plan — no catalogue, no proxy, documented constraints only. Measured over the 12
reachable states: current ΔV **7** distinct values · feasible campus patterns **3** ·
tightest-item slack **1**. **It discriminates worse.** With 29 units into 36 slots the degree
is nowhere near infeasible, so slack carries no signal, and deferring MR / Lang / LHP / SciRD
leaves **structurally identical** futures.

⭐ **But that is itself the finding:** if the deferrals are structurally equivalent, V's
confident 7-bucket separation of them is not measuring structure. It is measuring the proxy.

### THE REDESIGN — `DESIGN_V3.md`
Delete V as a score. Split it into: **Φ** feasibility (hard filter, documented constraints) ·
**Π** campus (assert the invariant, score nothing) · **Γ** sequencing (exact, elicited,
reported not added) · **K** congestion (unmeasurable — bracket it, never point-estimate it).

Rank on the present week alone, which is measured in real hours and fully elicited. Replace
the congestion estimate with the **robustness margin**

> k*(x) = the largest per-deferred-course congestion cost at which x still wins

computable exactly from the existing candidate set, no new model. **k\*(#1) = 11.029 against a
measured k̄ ≈ 24 ⇒ #1 is not robust.** Non-deferring candidates have k\* = ∞.

⚠️ **v3 does not trivially favour deferring nothing.** On the current candidate set it reduces
to variants D/E, whose #1 **defers Language** at a margin of 2.196. That answer is contingent
on the lower end of the congestion interval, and v3's job is to say so rather than hide it.

---

## R227. ⭐⭐ B-1 STARTED: THE RECEIVING SEMESTER, MEASURED — plus two structural findings and one hard blocker
**2026-08-10.** `b1_receiving.py` built at Iden's instruction (DESIGN_V3 §7 step 4). B-1 has
been the stated blocker since 2026-08-07.

### The search bound was unsound and is now PROVED
`semester_sim.best_week` prunes on `fast_score`, which R217 showed is not monotone
(hole-filling), so the shipped search can discard the true optimum — `GAPS.md`: "not fixed".
Replaced with `week_value`, and the replacement is a proof, not a sample:

    fast_score(final) = week_value(final) + Σ day_pen(final)
                     ≤ week_value(final)     — day_pen ≤ 0, verified EXHAUSTIVELY on all
                                               65,536 day masks, 0 exceptions
                     ≤ week_value(partial)   — every component of week_value is non-increasing
                                               in occupancy (0 violations / 20,000 measured)

### K(MR) independently reproduces R209
Best achievable week of the 국제 Spring that receives QRM1001, over real sections:
**with 90.187 · without 114.370 ⇒ K = 24.183, bracket [22.708, 25.658]**. R209's isolated
≈24, recovered through a different code path with a sound bound. **The ≈24 figure is real.**

### ⭐ FINDING 1 — 국제-only requirements have exactly ONE legal receiving semester
`MR` and `WCiv` are 국제-only, and the campus plan leaves exactly one further 국제 semester.
Deferring either has **no placement flexibility at all** — one home, take it or leave it.
`LHP`/`SciRD`/`Lang` have 5–6 legal semesters and their K varies over them by a factor of ten
(LHP 5.6–59.7 · SciRD 14.4–76.7 · Lang 12.8–56.7). **K is not a per-requirement constant.**

### ⭐⭐ FINDING 2 — THE `Lang` LEDGER ITEM IS INTERNALLY INCONSISTENT
`plan_model.ITEMS['Lang']`: `campus='any'`, `codes=['UIC1805','UIC1806']`. Measured over
`raw_2026F.json`:

| tier | 국제 | 신촌 |
|---|---:|---:|
| easy — UIC1805, UIC1806 (the `codes` list) | 20 | **0** |
| hard — 8 × YCF 언어와표현 | — | **17** |

**The two courses the ledger names exist only at 국제, while the item claims campus 'any'.**
Its own note admits it: *"NEEDS CONFIRMING"*. Consequences, both live:

1. `semester_sim.sections_for('UIC1805','F','신촌')` returns nothing, so the first pass scored
   **K(Lang) = 0.000** — deferring Language priced as costing the receiving semester *nothing*,
   purely from a data gap.
2. Worse: `rank4_branch` charges deferring Language `p_hard × D_LANG = −3.5`, where
   `p_hard_if_deferred()` is measured from **mileage competition at 국제** (R190). But if the
   deferred Language lands in a **신촌** semester the easy tier does not exist there at all —
   P(hard) is **1.0**, not 0.35, and the charge should be **−10.0**. The model prices a
   competition it would not be entering.

⚠️ Split `Lang` into two ledger items — easy (국제-only) and hard (any) — before any V work.
And note the direction: measured at low load, **Lang·easy is the most expensive requirement a
semester can receive** (K = 98.60 at n=0; its two 국제 sections have bad times), while
**Lang·hard is the cheapest** (K = 0.00). The current single item averages a 98-point spread
into one number.

### ⛔ BLOCKER — the inner search cannot reach realistic semester loads
K(req, n) = damage from adding `req` to a semester already holding n courses. Measured with
both the shipped lightest-first filler and a representative ≥3h filler (the pool's lightest
entries are **1-hour** sections; the median real section is **3 hours**, so every receiving
semester was being modelled far emptier than it will be):

| requirement | n=0 | n=1 | n=2 | n≥3 |
|---|---:|---:|---:|---|
| Lang·hard 신촌 | 0.00 | 6.48 | 23.28 | unstable, goes negative |
| MR 국제 | 35.03 | 23.01 | 19.17 | unstable |
| LHP 신촌 | 63.23 | 59.91 | 50.96 | unstable |
| SciRD 신촌 | 78.23 | 74.91 | 65.34 | unstable |
| WCiv 국제 | 91.10 | 77.10 | 61.35 | unstable |
| Lang·easy 국제 | 98.60 | 84.91 | 69.88 | unstable |

**n ≤ 2 is stable across both filler pools and is trustworthy. n ≥ 3 is not.** Choosing 6
free sections from 139–184 distinct time-masks is ~7.7 × 10⁹ combinations; the node budget
returns a *lower* bound whose bias differs between the two arms of the comparison, which is
why K turns negative — an artefact, not hole-filling.

**A real receiving semester holds 5 other courses.** So K is currently measurable only in the
regime that does not occur.

⭐ **The engine already exists.** `_crowd_curve.py` solved this exact problem — best achievable
week over subsets — exhaustively in ~5 s, using two accelerations that were *proved* rather
than assumed (schedule monotonicity verified on 4,000 random pairs with the run aborting on
violation, and superset seeding). B-1 must reuse that search, not `semester_sim`'s naive
recursion. **This is the next step, and until it is done no K at realistic load may be quoted.**

---

## R228. ⭐⭐⭐ B-1 COMPLETE — K MEASURED EXACTLY AT REALISTIC LOAD. THE CROWDING CURVE HAS THE WRONG CURVATURE, AND ≈24 WAS AN ARTEFACT
**2026-08-10.** `b1_curve.py`. B-1 open since 2026-08-07, closed.

### The engine
`_crowd_curve`'s ideas (signature collapse · strong incumbent first · branch and bound),
with its unsound `fast_score` prune replaced by the proved `week_value` bound (R227), plus
two new exact accelerations:

1. **Free-day decomposition with a closed-form branch ceiling.** Every timetable has a
   presence-free weekday set F. Branch on F with *exact* semantics (days outside F must be
   occupied, so branches are disjoint), and cap the branch before expanding a node:
   `ub(F) = trip(F) + 7·|F| + 4.333·[4∈F]`, valid because Σ day_pen ≤ 0 and a fixed-free day
   must also be presence-free. With no free weekday `ub(∅) = 0`, so the branch holding the
   entire unrestricted pool is discarded outright.
2. **The least-bad day.** `G[h] = max day_pen over all 16-bit masks of popcount h`,
   computed exhaustively; a small DP bounds Σ day_pen for H hours over d days. Monotone
   decreasing in H, so the minimum hours still to be placed keeps it valid.

**Validated against every value the naive exhaustive search had proved exact** (국제 m=3/5/6,
신촌 m=3/5) — all match. 신촌 m=6, which the naive search never completed (BOUND 52.404 after
28.9M nodes / 88 s), now completes **EXACT at 52.404 in 12 s**: the truncated value had been
optimal all along. Speed-ups of 15–75×. **Every K below is exact, not a bound.**

### K(req, n) — points of weekly comfort lost by adding this requirement to a semester already holding n courses
| requirement | n=0 | n=1 | n=2 | n=3 | n=4 | **n=5** |
|---|---:|---:|---:|---:|---:|---:|
| MR (QRM1001) | 35.03 | 23.01 | 19.17 | 11.96 | 15.46 | **15.94** |
| WCiv | 91.10 | 77.10 | 61.35 | 45.63 | 33.33 | **27.86** |
| LHP | 63.23 | 59.91 | 50.96 | 34.44 | 17.21 | **10.35** |
| SciRD | 78.23 | 74.91 | 65.34 | 43.42 | 28.89 | **25.78** |
| Lang·easy (국제 only) | 98.60 | 84.91 | 69.88 | 49.14 | 40.02 | **30.91** |
| Lang·hard (신촌) | 63.23 | 59.91 | 52.00 | 33.81 | 18.25 | **13.48** |

### ⛔ FINDING 1 — THE LIVE CROWDING CURVE IS CONVEX; THE MEASURED ONE IS CONCAVE
`continuation.INC = [0.00, 17.29, 19.64, 24.22, 31.18, 38.14]` — **increasing**, i.e. each
extra low-supply course costs MORE than the last, the shape R144 predicted from one point and
`_crowd_curve` confirmed under the unsound prune.

**Every one of the six measured curves DECREASES in n.** Once a week is already compromised,
one more course does less further damage. The live model has the curvature backwards, and it
is the term R226 showed decides the entire deferral verdict.

### ⭐ FINDING 2 — R209's ≈24 FOR QRM1001 IS SUPERSEDED. It was an artefact.
`b1_receiving` reproduced ≈24 (24.183) and so did the lightest-filler curve at n=4 (24.18) —
but only because `semester_sim.filler_pool` keeps the **lightest** masks, which are **1-hour**
sections, while the median real section is **3 hours**. With representative filler the same
cell is **15.46**, and at a full semester **15.94**.

**The receiving semester was being modelled emptier than it can be, and that inflated K by
~55%.** Every conclusion resting on ≈24 — including `PURPOSE_CHECK`'s "#1 is not robust" and
`DESIGN_V3` §2's k̄ — is superseded by this table.

### ⭐⭐ THE VERDICT — defer MR, and it survives every corner
v3 ranking (present week only) minus the measured K, swept over receiving-semester load and
over both Lang-tier routes:

| load | MR | Lang | SciRD | WCiv | LHP | – | winner |
|---|---:|---:|---:|---:|---:|---:|---|
| n=3 | **19.24** | −6.92 | −17.48 | −21.69 | −15.55 | 10.32 | defer MR (+8.92) |
| n=4 | **15.73** | 8.64 | −2.95 | −9.39 | 1.68 | 10.32 | defer MR (+5.42) |
| n=5 | **15.25** | 13.41 | 0.16 | −3.92 | 8.54 | 10.32 | defer MR (+1.84) |

(Lang shown on the R227-corrected route — 신촌, hard tier certain. Pricing it as shipped at
p_hard = 0.35 makes Lang *worse*, and MR's margin at n=5 grows to 4.94.)

**Deferring Intro to QRM wins under every combination of semester load and Lang tier.**
The narrowest corner is +1.84. `defer nothing` is beaten at every load.

⭐ **The live #1's deferral was right; the reason given for it was not.** QRM1001 is cheap to
defer because its single section (목4,5,6) is compact and drops into an already-busy week for
little marginal cost — a property of real sections at real hours, which the counting proxy
could not see and only reproduced by accident.

⚠️ Still outstanding: `crowding.json` and `continuation.INC` remain convex and are still read
by the live ranker; the ledger placeholders (R225) are untouched; and workload remains
unpriced (R218), so the n-axis assumes six courses cost the same whatever they are.

---

## R229. ⛔⛔⛔ THE K MEASUREMENT'S INPUT IS BIMODAL, AND THE MEDIAN HID A VERDICT-FLIPPING SPLIT
**2026-08-10.** Iden, before accepting R228's verdict:

> *"if QRM1001 is deferred into Spring, its Spring section times may differ from its Fall
> section times. The new argument for deferring it depends specifically on its current section
> geometry being compact and cheap to add to an already-busy week. So are the K curves using
> section data matched to the actual receiving campus and season, or are they reusing the
> current Fall section pattern as a proxy?"* — Iden, 2026-08-10

**He was right to stop it. Both halves of the question expose a defect.**

### ✅ Q1 — QRM1001 IS intrinsically 국제-only, not an artefact of the receiving semester
Every observation, both seasons: 2024 Fall 국제 · 2025 Spring 국제 · 2025 Fall 국제 ·
2026 Spring 국제 · Fall 2026 catalogue 1 section, 국제. `raw_2026F.json` holds **no** 신촌
section. The campus restriction is a property of the course. R227's "국제-only requirements
have exactly one legal receiving semester" stands.

### ⛔ Q2 — THE DEFERRED COURSE'S OWN GEOMETRY IS TERM-MATCHED, AND IT IS BIMODAL
`sections_for('QRM1001','S','국제')` correctly prefers Spring evidence — and that evidence
contains **two different timetables**:

| Spring geometry | K n=0 | n=1 | n=2 | n=3 | n=4 | **n=5** |
|---|---:|---:|---:|---:|---:|---:|
| 목4,5,6 | 27.87 | 17.19 | 12.52 | 3.80 | 3.11 | **4.77** |
| 금1,2,3 | 42.20 | 28.83 | 25.82 | 20.11 | 27.82 | **27.11** |
| **median — what R228 used** | 35.03 | 23.01 | 19.17 | 11.96 | 15.46 | **15.94** |

**R228 reported the median of a bimodal input as if it were a measurement.** Carried into the
verdict at n=5 (defer-MR base 31.194; runners-up Lang 13.41, defer-nothing 10.32, LHP 8.54):

| assumed Spring geometry | defer MR scores | verdict |
|---|---:|---|
| 목4,5,6 | 31.194 − 4.77 = **26.42** | defer MR wins by 13.01 |
| 금1,2,3 | 31.194 − 27.11 = **4.08** | **defer MR LOSES** to Lang, defer-nothing AND LHP |

**Base rate: 3 of the 4 observed offerings are 금1,2,3** (2024F, 2025S, 2025F); only the most
recent, 2026 Spring, is 목4,5,6. 금1,2,3 is Friday 09:00–11:50 — it destroys the Friday trip
day *and* fires the 1교시 penalty, i.e. it attacks precisely the two things Iden values most.

⭐ **R228's narration was also wrong.** It explained the result by "its single section 목4,5,6
is compact" — that is the **Fall 2026** geometry. The measurement did not use it; it used both
Spring geometries and averaged them. The number and the story did not describe the same object.

### ⛔ THE FILLER IS NOT TERM-MATCHED, AND CANNOT BE
The other n courses in every receiving semester are drawn from the **Fall 2026** catalogue —
109 masks at 국제, 147 at 신촌 — including for Spring receiving semesters. A real Spring pool
cannot be built from what is held: `mileage_history` yields only **19** distinct 국제 Spring
time-masks and **5** 신촌 Spring masks. So G-9 is baked into every K in R228 and is not
removable with current data.

Term-matching of each requirement's own sections, for the record: MR ✅ 2026-1 · WCiv ✅ 2026-1
· Lang·easy ✅ 2026-1 · SciRD ✅ 2025-2 · **LHP ⚠️ Fall 2026 catalogue stand-in** ·
**Lang·hard ⚠️ Fall 2026 catalogue stand-in**.

### ⚠️ A separate inconsistency found on the way
`sections_for('QRM1001','F','국제')` returns **금1,2,3** from 2025-2 evidence, though the
Fall 2026 catalogue plainly shows **목4,5,6**. `term_evidence` outranks the current catalogue
unconditionally. Right for an unknown future term, wrong whenever the present one is known.

### ⛔ STANDING CONCLUSION
**"Defer QRM1001" is a hypothesis, not a result.** It is decided by an unknown — next Spring's
section geometry — whose historical majority overturns it. No rerank may report a single K for
MR; the geometry must be an explicit scenario axis, and per R190 the arm that argues against
the incumbent (금1,2,3) is the one that must be shown.

---

## R230. ⭐⭐ THE UNCERTAINTY IS NOT PER-COURSE — K IS A FUNCTION OF THE TIME MASK, AND THE EVIDENCE IS ~EMPTY
**2026-08-10.** Iden, refusing to let QRM1001 become the scenario axis:

> *"The questions I raised seem to expose general gaps in the future model, not a
> QRM1001-specific uncertainty. QRM1001 just happened to reveal them. … Can we handle this as
> a sampling/uncertainty problem instead?"* — Iden, 2026-08-10

`k_inventory.py` (cheap, no search) profiles every deferrable requirement's receiving
term/campus, evidence source, observation count, geometry variation and Good–Turing novel mass.

### The inventory kills the premise of stratifying by course
| requirement / code | receiving | evidence source | obs | geometries | p(novel) |
|---|---|---|---:|---:|---:|
| MR / QRM1001 | 국제 Spring | term-matched | 2 | **2** | **1.00** |
| WCiv / UIC1561 | 국제 Spring | term-matched | 2 | 1 | 0.00 |
| LHP / UIC1551 | 신촌 Fall | **NO DATA** | 0 | 0 | 1.00 |
| LHP / UIC1251 | 신촌 Fall | current-catalogue stand-in | 0 | 0 | 1.00 |
| SciRD / UIC2151 | 신촌 Fall | term-matched | 1 | 1 | 1.00 |
| Lang·easy / UIC1805 | 국제 Spring | term-matched | 2 | 2 | 1.00 |
| Lang·easy / UIC1806 | 국제 Spring | term-matched | 4 | 2 | 0.00 |
| Lang·hard / **all 8 YCF** | 신촌 Fall | **current-catalogue stand-in** | **0** | 0 | 1.00 |

**Only 2 of 18 course×route cells carry evidence that assigns any confidence to next term's
geometry.** There are no strata to form — there is one stratum, "almost no evidence", plus two
weak cells. Stratifying courses by hand would invent structure the data does not contain.

Filler pools: `K` used **107 국제 / 147 신촌** masks from the **Fall 2026** catalogue, for BOTH
seasons. Actually observed: 19 국제 Spring · 25 국제 Fall · 5 신촌 Spring · 4 신촌 Fall. A
term-matched filler pool cannot be built from what is held.

### ⭐ THE REFORMULATION — sample MASKS, not courses
**K(section, n) depends only on the section's time mask, never on which course it is.** So
every requirement reduces to one question — *which mask in its receiving term?* — and the cost
of any mask is a single exactly-computable function shared across all of them. The sample
space becomes the mask pool (107 국제 / 147 신촌): enumerable, not hand-picked. `k_reference.py`
measures the reference distribution of K over it.

### First evidence — 49 of 107 국제 masks, exact
| load | min | p10 | p25 | median | p75 | p90 | max |
|---|---:|---:|---:|---:|---:|---:|---:|
| n=3 | 0.00 | 3.80 | 4.61 | 20.11 | 49.65 | 55.25 | 71.94 |
| n=4 | 0.00 | 2.70 | 5.18 | 27.82 | 39.33 | 45.03 | 61.96 |
| n=5 | 0.00 | 1.77 | 9.48 | 25.79 | 29.43 | 38.72 | 50.05 |

**QRM1001's two observed Spring geometries sit at the 12th and 57th percentiles of this
distribution** (목4,5,6 K=4.77 · 금1,2,3 K=27.11). The two observations do not narrow the
uncertainty — they sample it twice, near opposite ends.

⭐ **So the bimodality is not a QRM1001 property. It is what two draws from a wide distribution
look like, and every other requirement has fewer draws than that.** `defer nothing` is the only
branch with K = 0 by construction and therefore the only one not exposed to this at all.

⚠️ Branch margins under debate are **1.84–8.92**. The interquartile spread of K at n=5 is
**~20** and the full range **50**. Complete the reference distribution before any rerank.

---

## R231. ⭐ THE SEASON MISMATCH IS CONFINED TO ONE CAMPUS, AND IT MEASURES AT ONLY ≈ +2
**2026-08-10.** Before asking Iden to supply past timetables, measure whether the substitution
he offered to fix actually matters.

### Only half the filler substitution is a season mismatch
| receiving semester | branches | filler drawn from | verdict |
|---|---|---|---|
| **국제 Spring** | MR · WCiv · Lang·easy | Fall 2026 국제 | ⛔ **season mismatch** |
| 신촌 Fall | LHP · SciRD · Lang·hard | Fall 2026 신촌 | ✅ season matches; only the year differs |

The 신촌 branches were never season-mismatched. **The defect is confined to the 국제 Spring
branches — which is exactly where the contested MR deferral lands.**

### And the mismatch is small, measured
Observed 국제 masks, Spring vs Fall (mileage_history, ≥3h): mean hours **3.00 vs 3.00**;
weekday spread similar in shape (수 heaviest in both); Spring's first-period histogram tops out
at 8교시 where Fall reaches 10.

K over the 19 observed **Spring** masks against the Fall stand-in pool, at n=5:

| pool | n | p10 | median | p90 | max |
|---|---:|---:|---:|---:|---:|
| observed 국제 **Spring** | 19 | 4.77 | **27.86** | 41.10 | 50.05 |
| Fall 2026 국제 stand-in | 49 | 1.77 | **25.79** | 38.72 | 50.05 |

**Median shift +2.07 — the Fall stand-in UNDERSTATES K.** Same maximum, similar shape. So the
systematic substitution is worth roughly 2 points, not 20 — but the narrowest branch margin
under debate is **1.84**, so it is not negligible either, and the estimate itself rests on only
19 Spring masks.

### ⭐ WHAT DATA WOULD ACTUALLY HELP — and what would not
Because K is a function of the **mask**, not the course (R230), the useful unit is a **whole
past catalogue**, not per-course history. One file does most of the work:

1. **A 국제 SPRING course-list export** — the Spring twin of `강의목록_2026F.xlsx` (columns
   학기·캠퍼스·학정번호·강의시간 are the ones that matter). Spring 2026 preferred, Spring 2025
   also fine. It replaces the mismatched filler pool on the contested branches, lifts the
   Spring mask pool from 19 to ~100+, firms up the +2.07 estimate, and incidentally adds Spring
   observations for QRM1001, UIC1561 and UIC1805/1806.
2. A past **신촌 Fall** catalogue — lower value; season already matches, addresses year drift only.
3. **Per-course timetable history is NOT needed.** Under the mask formulation it adds nothing
   a catalogue does not.

**What no timetable data can fix:** the ledger placeholders (R225 — `DM` 12 units, `FREE` 5,
`ME` 6→2 codes), unpriced workload (R218), and drift from 2026 to 2029.

---

## R232. ⭐⭐⭐ FIVE PAST TERMS FETCHED — THE GEOMETRY QUESTION IS A TIME SERIES, NOT A LOTTERY
**2026-08-10.** `fetch_past_terms.py` (parameterised on `smtDivCd`: 10 = Spring, 20 = Fall —
the existing fetchers had it hardcoded to 20 and were one constant away from this). Iden ran
it: **all five targets complete.**

| term | listings | sections | 국제 | 신촌 | ≥3h masks 국제 / 신촌 |
|---|---:|---:|---:|---:|---|
| 2024-1 | 1795 | 1626 | 877 | 918 | 105 / 171 |
| 2024-2 | 1739 | 1557 | 830 | 909 | 103 / 150 |
| 2025-1 | 1790 | 1610 | 900 | 890 | 111 / 150 |
| 2025-2 | 1695 | 1515 | 812 | 883 | 100 / 147 |
| 2026-1 | 1804 | 1622 | 914 | 890 | 110 / 143 |

With Fall 2026 that is **six terms, three of them Springs**. The 국제 Spring mask pool goes
from **19** (scraped out of `mileage_history`) to **110**. G-9's substitution can now be
retired for the 국제 Spring branches rather than merely bounded.

### ⭐⭐ FINDING 1 — QRM1001 DID NOT DRAW TWICE FROM A DISTRIBUTION. IT MOVED, ONCE.
| term | 2024-1 | 2024-2 | 2025-1 | 2025-2 | **2026-1** | **2026-2** |
|---|---|---|---|---|---|---|
| QRM1001 | 금1,2,3 | 금1,2,3 | 금1,2,3 | 금1,2,3 | **목4,5,6** | **목4,5,6** |

Four consecutive terms at 금1,2,3, then a step change to 목4,5,6 which has now held for
**both** terms of 2026. **This overturns R230's reading** that the bimodality was "two draws
from a wide distribution" — with two observations that was the honest inference; with six it is
plainly a regime change with two terms of persistence.

⚠️ **And it points the opposite way to the pessimistic arm R229 demanded.** 목4,5,6 is the
CHEAP geometry — K(n=5) = **4.77** against 27.11 for 금1,2,3. Last-value-carried-forward makes
the cheap geometry the expected one for Spring 2027, which strengthens *defer MR* considerably.
It is still only two terms of persistence, and a course that moved once can move again — but
the prior is no longer 50/50 and must not be modelled as if it were.

### ⭐ FINDING 2 — R227's "the easy tier does not exist at 신촌" IS SEASONAL, NOT ABSOLUTE
| term | UIC1805 |
|---|---|
| 2024-1 · 2025-1 · 2026-1 (**Spring**) | 신촌 1 · 국제 3 |
| 2024-2 · 2025-2 · 2026-2 (**Fall**) | 국제 2 · **신촌 0** |

Perfect alternation across all six terms: **UIC1805 runs one 신촌 section every Spring and none
in Fall.** UIC1806 is 국제-only in all six. R227 measured this on `raw_2026F` — a *Fall*
catalogue — and generalised a seasonal fact into a permanent one. The operational conclusion
survives, because Lang's receiving semester in the plan is **신촌 Fall** (sem 4), where the
easy tier genuinely is absent — but the stated reason was wrong, and if the plan ever routes
Lang to a 신촌 **Spring** the P(hard) = 1.0 correction must not be applied.

### ⭐ FINDING 3 — "Lang·hard has zero observations" WAS A COVERAGE ARTEFACT
All 8 YCF courses are offered at **both campuses in all six terms**, several with identical
geometry sets every single term (YCF1301: the same 6 masks six times; YCF1601 and YCF1607:
2 masks each, every term). The inventory's `p_novel = 1.00` for these came from
`mileage_history` being thin, not from the courses being unpredictable. **They are the most
stable items in the whole ledger.**

### Geometry stability now measurable, and it is wildly uneven
`UIC1561` — one mask, all six terms, 국제 only: **zero uncertainty**.
`UIC2151` — 17 distinct masks across six terms, only 3 present in every term.
`UIC1805` — 4 masks, none in all six.

⚠️ **Consequence for the design:** the per-item uncertainty is real but is now *estimable per
item* from six terms. R230's mask-level reformulation still holds — K is still a function of
the mask — but the predictive distribution over masks is no longer a shrug; for several items
it is nearly a point mass, and for QRM1001 it is a persistence question.

---

## R233. ⭐⭐⭐ K RE-MEASURED ON REAL CATALOGUES — AND THE VERDICT REVERSES TO **DEFER LANGUAGE**
**2026-08-10.** `pools_past.py` + `k_real.py`. Every substitution R229 exposed is now removed
for the branches it affected.

### What changed in the inputs
* **Filler pool** is now the right campus in the right **season**, and **per-year** — a single
  future semester offers one year's catalogue, not three unioned. 국제 Spring: 125/137/133
  masks for 2024/25/26. 신촌 Fall: 167/162/164. (`b1_curve` used 109 국제 and 147 신촌, all
  Fall 2026, for both seasons.)
* **Each requirement's own geometry** is drawn from what it was actually observed with at that
  campus in that season, across three years. The spread across years IS the uncertainty.

### The Fall stand-in was OVERSTATING K, not understating it
R231 predicted +2.07 from 19 scraped masks. Against the real Spring catalogues, K falls hard:
MR 금1,2,3 27.11 → **14.88**; WCiv 27.86 → **12.93** (n=5). R231's sign was wrong because 19
masks is not a pool — a real catalogue gives the optimiser far better filler.

### ⭐⭐ THE STRUCTURAL FACT THE MODEL NEVER HAD: HOW MANY SECTIONS HE CAN CHOOSE FROM
| requirement | receiving | median sections/term | K over them (n=4) min / median / max |
|---|---|---:|---|
| **MR** | 국제 S | **1** | 1.51 / 8.20 / 14.88 |
| WCiv | 국제 S | 1 | 23.25 / 23.25 / 23.25 |
| LHP | 신촌 F | 1 | 16.61 / 16.61 / 16.61 |
| SciRD | 신촌 F | 2 | 28.29 / 28.91 / 29.52 |
| **Lang·hard** | 신촌 F | **10** | **−4.72** / 16.61 / 28.11 |

**With several sections he PICKS; with one he TAKES WHAT IS OFFERED.** Nothing in the model
ever represented that, and it dominates the deferral decision.

⭐ And K < 0 for Lang·hard is real, not an artefact: **YCF language courses are 3 credits
taught in 2 hours/week** (verified: YCF1301·1451·1501·1551 all `credits=3, hours=2`). Deferring
Language and picking a 2-hour section costs the receiving week *less* than the 3-hour course
that would otherwise occupy that slot.

### THE CHOICE-AWARE RERANK (n=4, Lang→신촌 Fall so P(hard)=1 per R227/R232)
| scenario | Lang | MR | – | LHP | WCiv | SciRD | winner |
|---|---:|---:|---:|---:|---:|---:|---|
| QRM1001 keeps 목4,5,6 (current regime) | **31.62** | 29.68 | 10.32 | 2.28 | 0.69 | −2.35 | **defer Lang** +1.93 |
| QRM1001 reverts to 금1,2,3 | **31.62** | 16.31 | 10.32 | 2.28 | 0.69 | −2.35 | **defer Lang** +15.30 |

> **⭐ "Defer QRM1001" does not survive the corrected inputs. The answer is DEFER LANGUAGE,
> and — the point of the whole exercise — it is robust to the QRM1001 regime question that
> R229/R232 were worried about.** The thing we spent the most effort on turned out not to be
> the deciding factor; section *count* was.

### ⚠️ WHAT IS STILL NOT DONE — do not bank this either
1. **The candidate set was generated under the OLD objective.** This is a rescoring of the
   existing 7,200 rows, not a re-search. `rank4_branch` pruned with a bound involving V and
   kept only 1,200 rows per branch; under the new objective it may have discarded rows that
   would now rank high. **A full re-search is required before this is an answer.**
2. **신촌 at n=5 is computationally out of reach** — 167 masks × 6 free choices exceeded every
   budget tried. n=4 (a 5-course semester) is the common load used. 국제 reaches n=5.
3. The ≥3h filler filter means the counterfactual course is ≥3h. If other ledger items are
   also 3-credit/2-hour, Lang's advantage narrows. Unchecked.
4. `crowding.json` / `continuation.INC` are still convex and still read by the live ranker.

---

## R234. ⭐⭐⭐ FULL RE-SEARCH UNDER v3 — **DEFER LANGUAGE**, IN ALL 18 CELLS. AND v3 HAS LOST THE ELECTIVE BUDGET.
**2026-08-10.** `research_v3.py`. Objective = week + year-pen + chapel + difficulty − K(deferred).
`continuation.py` is not imported; **`crowding.json` influences nothing.** The 276.0 constant
bound is replaced by the sound `week_value(partial)` ceiling, verified per R219 by re-deriving
a known ranking rather than by argument.

### The old candidate set was incomplete in EVERY branch
| branch | v3 re-search | rescored old set | gain |
|---|---:|---:|---:|
| MR | 40.390 | 31.194 | **+9.196** |
| Lang | 38.765 | 33.390 | +5.375 |
| WCiv | 35.940 | 23.940 | **+12.000** |
| SciRD | 29.940 | 25.940 | +4.000 |
| LHP | 21.715 | 18.890 | +2.825 |
| – | 14.315 | 10.315 | +4.000 |

R233's rescoring was therefore not a result, exactly as suspected. Every branch improved.

### THE VERDICT — defer Language, robust across all three axes
Per catalogue year (variation preserved, never medianed), both QRM1001 regimes, and with the
two guards below on or off — **`Lang` wins all 18 cells.** Margin over the runner-up:

| guards | 2024 | 2025 | 2026 |
|---|---|---|---|
| none, QRM1001 목4,5,6 | +14.38 | +5.44 | +3.10 |
| no fm=0 loophole | +16.00 | +7.07 | +4.73 |
| **+ zero free electives** | +11.50 | +2.57 | **+0.22** |
| (QRM1001 reverts to 금1,2,3) | +21.38…+27.64 | +10.69…+15.19 | +15.11…+19.61 |

**Direction is stable; the tightest corner is +0.22** — 2026 catalogue, current QRM1001 regime,
both guards on. There, defer-Lang and defer-MR are a tie.

### ⛔ GUARD 1 — the re-search walked into R218's loophole, as the handoff predicted
With V flat, 4 of 6 branches put `YCG1804`/`YCG1853` (비대면 동영상, `fm = 0`, costing the
comfort score nothing) in their top row. Inflation: MR +1.625, WCiv +2.500, others 0.
`Lang`'s top row never used them, so closing the loophole *widens* its margin. Workload
remains unpriced.

### ⛔⛔ GUARD 2 — DELETING V REINTRODUCED THE DEFECT THAT CREATED V
Every v3 top row spends **FREE+FREE** — two of the ~5 pure free electives available for the
entire degree. That is R181 verbatim, Iden's original objection, the thing `continuation.py`
was built to fix. **DESIGN_V3 removed V as a score and took the free-elective opportunity cost
with it.**

Cost of forbidding free electives entirely: – 4.00 · MR 7.57 · LHP 11.83 · Lang 12.07 ·
SciRD 12.32 · WCiv 15.12. It does not flip the verdict, but it collapses the 2026 margin to
0.22.

⭐ **The fix is v3-shaped and not a return to V:** the elective budget is a **constraint**
(≤ N free electives this semester), not a reward. Constraints were always the part of the
four-year layer that worked (R226 Φ). Add it as a filter and re-search.

### ASSUMPTIONS, VISIBLE AND NOT BAKED IN
1. **n = 4** — a 5-course receiving semester. 신촌 at n=5 (167 masks × 6 free choices) exceeded
   every budget tried; 국제 reaches n=5. Not an approximation of choice.
2. **Filler ≥3 scheduled hours — tested, and appropriate.** Every identifiable remaining
   ledger item of Iden's is a **3-hour** course (LHP·Lang·SciRD·WCiv·Seminar·QRM1001·ECO1101·
   ECO2101·ECO2102·MR5·QRM3003·ME, all median 3h), and only ~10% of 3-credit sections
   catalogue-wide run in 2 hours. ⚠️ But **17 of 38 remaining units (DM ×12, FREE ×5) have no
   course identity**, so their hours are assumed, not known. Lang·hard's advantage comes
   precisely from being 3 credits in 2 hours — an exception among his courses, not the rule.
3. **No crowding.** `crowding.json` and `continuation.INC` are untouched by this search.
4. **Per-year variation preserved** throughout; 2024/2025/2026 never collapsed to one number.

---

## R235. ⭐⭐⭐ THE ELECTIVE OPPORTUNITY COST, PRICED FROM THE SEARCH — AND THE VERDICT HOLDS IN ALL 18 CELLS
**2026-08-10.** Iden: *"The opportunity cost should be clearly reflected."*

Implemented the v3 way — **as a constraint, not a weight**. `research_v3.py` takes `MAX_FREE`,
the number of pure free electives allowed this semester, and the ledger item is now part of the
elective signature (two sections at the same hours are NOT interchangeable if one advances a
Major Elective and the other burns a free elective — the old signature collapsed them).

Re-searched at MAX_FREE = 0, 1, 2. **The opportunity cost is then read off the frontier rather
than assumed**, which is exactly R181's own diagnosis: *"the real cost comes from choosing the
elective over some other thing, the opportunity cost."*

### The measured price of a free elective (fm=0 loophole sections excluded throughout)
| branch | 0 free | 1 free | 2 free | 1st buys | 2nd buys |
|---|---:|---:|---:|---:|---:|
| – | 10.315 | 14.315 | 14.315 | +4.00 | **+0.00** |
| MR | 31.194 | 37.069 | 38.765 | +5.88 | +1.70 |
| WCiv | 18.319 | 26.244 | 33.440 | +7.93 | +7.20 |
| LHP | 9.890 | 18.890 | 21.715 | +9.00 | +2.83 |
| SciRD | 17.619 | 25.940 | 29.940 | +8.32 | +4.00 |
| **Lang** | 26.694 | 36.890 | 38.765 | **+10.20** | +1.88 |

Budget: **5 free electives for the whole degree over 7 semesters ⇒ 0.71 per semester.** So
MAX_FREE=1 is roughly fair share and MAX_FREE=2 is 2.8× it. The second elective buys **+1.88**
for Lang and **+0.00** for '–' — i.e. for most branches the second one is nearly worthless
*and* costs a fifth of the degree-long budget. **The old #1 spent two.**

### THE VERDICT — `defer Language` wins all 18 cells
| budget | QRM1001 regime | 2024 | 2025 | 2026 |
|---|---|---|---|---|
| 0 (strict) | keeps 목4,5,6 | +11.50 | +2.57 | **+0.22** |
| 0 | reverts 금1,2,3 | +21.38 | +10.69 | +15.11 |
| **1 (fair share)** | keeps 목4,5,6 | +15.82 | +6.89 | **+4.55** |
| **1** | reverts 금1,2,3 | +27.46 | +15.01 | +19.43 |
| 2 | keeps 목4,5,6 | +16.00 | +7.07 | +4.73 |
| 2 | reverts 금1,2,3 | +27.64 | +15.19 | +19.61 |

⭐ **Enforcing the budget makes the answer MORE robust, not less** — Lang gains the most from
its first free elective (+10.20, the largest of any branch), so the tightest margin rises from
+0.22 at budget 0 to +4.55 at fair share.

### THE RECOMMENDATION AT FAIR SHARE — score 36.890, defer Language
```
chapel  YCA1006-02-00
REQ     QRM1001-01-00   Introduction to Quantitative Risk Management
REQ     UIC1561-01-00   Western Civilization
REQ     UIC1551-01-00   World History: Group II
REQ     UIC2151-12-00   Research Design and Quantitative Methods
FREE    YCE1253-01-00   Western Civilization in the Perspective of T…
ME      STA2102-05-00   Linear Algebra
```
Spends **1 of 5** free electives. **Takes QRM1001 now** — which is what R126 argued by hand in
the first week and what the counting proxy talked us out of.

### ⚠️ STILL OPEN — this is a result, not a registration
1. **The 8/14 seat pull.** A `sy1PercpCnt` of 0 makes a section impossible, not merely hard
   (R134). Nothing above survives that check failing. **This is the only thing with a deadline.**
2. **n = 4.** 신촌 at a full 6-course load is computationally out of reach.
3. **17 of 38 remaining ledger units (DM ×12, FREE ×5) have no course identity**, so the K
   baseline assumes their hours.
4. **Workload is still unpriced** (R218). The fm=0 sections are excluded as a guard, not fixed.
5. Lang's K assumes the deferred Language lands in a **신촌 Fall** semester (hard tier certain).
   If the plan ever routes it to a 신촌 **Spring**, the easy tier exists there (R232) and the
   P(hard)=1 charge must not be applied.

---

## R236. ⛔→⭐ THE `FREE` BUDGET WAS THE WRONG MODEL. IDEN WAS RIGHT, AND THE LEDGER SAID SO.
**2026-08-10.** Iden, rejecting R235's constraint:

> *"Why does taking a free elective have an opportunity cost merely because I have about five
> free-elective courses remaining? If those are credits I need to fill toward graduation
> anyway, taking one now isn't 'spending' a scarce resource… the actual opportunity cost comes
> from what the free elective displaces. … `5 electives / 7 semesters = 0.71 per semester` by
> itself [doesn't establish] a 'fair-share' constraint, because there's no reason those
> electives need to be distributed evenly across semesters."*

**He is right, and `plan_model.ITEMS['FREE']`'s own note already said it:**
`"[D] RESIDUAL, not a quota: 126 − 19.5 done − 19.5 CC − 36 QRM − 36 2nd major = 15.0 cr"`.
Verified: 126 − 19.5 − 19.5 − 18 − 18 − 36 = **15.0**. FREE is fifteen credits he must fill
with *something* to reach 126 — not an allowance whose preservation has value. `supply = 422`,
`chart_year = None`: **the least constrained item in the entire ledger.**

R235's `MAX_FREE` constraint modelled it as exactly the thing the ledger says it is not.
**Retired.** (And note the original R181 statement was already the displacement argument —
*"the real cost comes from choosing the elective over some other thing"*. The project converted
his displacement reasoning into a quota, twice.)

### WHAT THE FREE ACTUALLY DISPLACED — measured, per branch
| branch | 0 FREE holds | 1 FREE holds | displaced | gain |
|---|---|---|---|---:|
| **Lang** | ECO1101 + ME | FREE + ME | **ECO1101 — a MAJOR REQUIRED course** | +10.20 |
| SciRD | ECO1101 + ME | FREE + ME | **ECO1101** | +8.32 |
| MR | ECO1101 + ME | FREE + ECO1101 | ME | +5.88 |
| WCiv | ECO1101 + ME | FREE + ECO1101 | ME | +7.93 |
| LHP | ME + ME | FREE + ME | ME | +9.00 |

**The free elective was not displacing another elective. In the winning branch it displaced
ECO1101, Mathematics for Economics 1 — one of the six Major Required courses.** v3 charged
nothing for that, because its deferral term only covered the five CC/MR requirements the
branch structure enumerates. Elective-slot contents were free to defer.

### THE CORRECT PRICING — symmetric, same engine, no quota
Every unit not taken now is deferred and costs K at its cheapest legal placement plus its best
year-gap. Equivalently: **taking a unit now SAVES that cost.**

| unit taken now | saves (2024 / 2025 / 2026) |
|---|---|
| ECO1101 (chart yr 1, supply 2) | 19.01 / 16.19 / **27.31** |
| ME (chart yr 3, supply 9) | 23.25 / 15.59 / 23.02 |
| **FREE** (chart yr —, supply 422) | **0.00 / 0.00 / 0.00** |

FREE saves nothing because with 422 sections and no chart year it can always be placed cheaply
later. **That — and only that — is why FREE differs from ME. Not scarcity: placeability.**

### THE RESULT — the quota's answer, now DERIVED instead of imposed
| QRM1001 regime | 2024 | 2025 | 2026 |
|---|---|---|---|
| keeps 목4,5,6 | Lang +11.50 | Lang +2.57 | Lang **+0.22** |
| reverts 금1,2,3 | Lang +23.14 | Lang +10.69 | Lang +15.11 |

**`defer Language`, all six cells.** The optimum now holds **zero free electives as an OUTPUT**,
because taking ECO1101 and ME saves 27.31 + 23.02 of future cost — not because anything
forbade FREE.

```
TOP (2026 catalogue):  defer Language
  reqs  QRM1001-01 · UIC1561-01 · UIC1551-01 · UIC2151-12
  elec  ECO1101-06 (MR) · STA2102-05 (ME)
```
Five of six courses are Major Required or Major Elective progress.

⭐ **This is V rebuilt correctly** — per item, over real sections at real hours, with measured
K applied symmetrically to everything deferred. Not the counting proxy R208 condemned, and not
a fitted table. The four-year layer is back, and it is now made of measurements.

⚠️ Unchanged and still open: the **8/14 seat pull** (R134, the only thing with a deadline) ·
n=4 · 17 of 38 units without course identity · workload unpriced (R218) · Lang's K assumes a
신촌 **Fall** receiving semester.

---

## R237. ⚠️ THE POOLS CARRY DUPLICATE SECTION ROWS — harmless to the ranking, wrong for anything that iterates
**2026-08-10.** Iden, reading card #17 of `TOP50_v3.html`:

> *"why do I see two classes? Are they dupes, or are they actually different? (Prob not dupes,
> but like the display doesn't really tell)"* — showing
> `2 equal swaps … UIC1806 BEGINNING JAPANESE (1) · UIC1806 BEGINNING JAPANESE (1)`

**They were dupes.** `rank3.build()`'s `OPEN` pool holds **311 entries over 307 distinct
sections** — exactly 4 redundant rows, all four language sections: UIC1805-01/02 and
UIC1806-01/02.

**Cause, and it is not a bug to fix upstream.** `refetch_listings` v4 deliberately keeps one
record per **(section, query)** so that 과목종별 is not collapsed across the majors that list a
course — that collapse was its v3 defect and it mislabelled 129 sections. A course listed by
two majors therefore legitimately appears twice. **Correct for the catalogue; wrong for any
consumer that iterates a pool.**

- **The ranking is unaffected**: electives are collapsed by signature before enumeration, so a
  repeated section id lands in the same signature bucket and is never double-counted.
- **The equal-swap scan iterated the pool** and so listed the same section twice.

Fixed in `render_v3_top50.py` by deduplicating on section id before scanning, and asserted in
`test_v3.py` so a future consumer meets it as a failure rather than as a surprise.

⭐ **And a display rule the near-miss earns:** a replacement must be identified by its **분반
and its hours**, never by course code alone. Two 분반 of one course rendered identically, which
is exactly what made a genuine duplicate indistinguishable from a real alternative. Every
listing now carries section id, time and professor.

---

## R238. ⭐ STOCKTAKE — THREE CATALOGUE FIELDS THE RANKER HAS NEVER READ, AND THE LARGEST UNEXAMINED ASSUMPTION
**2026-08-10.** Iden: *"a good time to stop and organize what's still missing beyond our eyes."*
Written up in `MISSING_2026-08-10.md`; the checkable half was run rather than listed.

### Checked, and clean — but by luck
| field | catalogue | candidate pool | top 50 |
|---|---:|---:|---:|
| `rmvlcYnNm` = 폐강 | 7 | **2** | 0 |
| 유의사항 with a prerequisite | 9 | 4 | 0 |
| 유의사항 with an eligibility limit | 328 | — | all "UIC only", satisfied |

**`CTM2012-01-00` and `CTM2018-01-00` are CANCELLED and sit in the candidate pool right now.**
They did not reach the top 50, and nothing would have said so if they had — **no part of
rank3/rank4/research_v3 reads any of these three fields.** R61's eligibility audit was run once,
against a SciLit pool belonging to a model since replaced.

⭐ **Cheap fix: drop 폐강 sections in `rank3.build()`.** Minutes of work, currently load-bearing
on luck.

The #1 timetable itself is clean: no cancellation, no prerequisite, every restriction is
"UIC students only" which he satisfies, and STA2102 carries explicit cross-registration
permission.

### ⛔ THE LARGEST UNEXAMINED ASSUMPTION — the ledger presumes an unconfirmed double major
`plan_model.ITEMS` encodes **ME = 18 cr (not 24), `DM` = 12 units, `FREE` = the 15-cr residual
of that arithmetic**. All three follow from *obtaining a double major*, which is a **December,
competitive decision made on Semesters 1–2 GPA — which this semester determines.**

So the recommendation optimises a degree shape that is not confirmed, through a gate this very
semester feeds. If admission fails: ME → 24 cr, `DM` disappears, `FREE` changes, and every
deferral cost in R236 moves with them. **The failure branch is not represented anywhere.**
`GPA_GATE_MULT` exists for exactly this feedback loop and sits at 1.0, inert.

**This needs no new data — only a second `ITEMS` and a re-run.** It is the highest-value
remaining check that is not blocked on a date.

### And the honest meta-item
Self-caught inside this one session: a sign error on the season bias (R231→R233), a median
reported over a bimodal input (R228→R229), a quota that contradicted the ledger's own note
(R235→R236), a display that made a duplicate indistinguishable from a real alternative (R237).
**Every one was found by Iden asking, or by a check run afterwards — none by the model noticing
on its own.** The rate is not zero now, and the next one will look exactly as settled as those
did.

---

## R239. ⭐ THE FOUR TEACHING MODES — tm AND pm WERE RIGHT, fm WAS KEYED OFF THE WRONG FIELD
**2026-08-10.** Iden: *"실시간온라인, 동영상, 동영상(중복수강불가) are all different. Are they being
treated differently logically?"*

### What each mask does with each mode — verified against all 341 국제 sections
| room segment | blocks conflicts `tm` | on campus `pm` | fixed hour `fm` | sections |
|---|:---:|:---:|:---:|---:|
| 강의실 (대면) | ✔ | ✔ | ✔ | 283 |
| 실시간온라인 | ✔ | ✘ | **✔** — live, it pins the hour | 1 |
| 동영상(중복수강불가) | ✔ | ✘ | **✘** — recorded; blocks *registration*, not the week | 11 |
| 동영상콘텐츠 | **✘** | ✘ | ✘ — explicitly overlappable (R52) | 46 |

**`build_canonical.classify()` gets all four right, per SEGMENT**, and `tm`/`pm` are correct
everywhere. The distinction Iden is asking about is real and is implemented — for two of the
three masks.

### ⛔ THE DEFECT — `fm` is built from the COURSE-LEVEL mode string
`rank2.py:340`: `fm = pm | (tm & ~pm if '실시간' in mode else 0)`.

When a section **mixes** a live segment with a recorded one, the whole non-presence time is
marked fixed — including the recorded half. `HANDOFF_2026-08-10` describes this as
*"treated conservatively, the live half cannot be separated"*. **It can.** `build_canonical`
already stores a per-segment classification in `kinds`; the course-level string was simply the
wrong field to read.

**Exactly one section is affected in Fall 2026 — and it is in the recommended timetable:**
```
UIC1561-01-00  WESTERN CIVILIZATION   월7,8/수7   rooms 실시간온라인/동영상(중복수강불가)
   fm as shipped   월7,8/수7      <- the 수7 recorded hour counted as fixed
   fm per segment  월7,8          <- only the live half pins the week
```
The model was crediting 수7 with filling a Wednesday hole that a **shiftable recorded hour does
not actually fill** — R217's hole-filling effect, earning points in the wrong direction.

### Impact — corrected, and the verdict is unchanged
Score on the recommended timetable **−3.125**. Re-searched all six branches with the corrected
mask: `Lang 78.62 · MR 78.40 · WCiv 44.00 · LHP 40.03 · SciRD 36.53 · – 33.33`.
**Same winner, same margin (+0.22).** `WCiv` is unaffected because that branch defers UIC1561.

⚠️ **Applied as a runtime override (`fm_fix.py`), not an edit.** `rank2.py:340` sits ABOVE the
literal `    heap = []; cnt=[0]` at line 353 which `rank3.build()` execs — changing even its
whitespace breaks the ranker silently (INDEX trap #1). Same pattern R166/F3 used for the
widened language pool. Wired into `research_v3`, `render_v3_top50` and `render_v3`.

---

## R240. ⭐ ELIGIBILITY IS NOW A FILTER — 10 SECTIONS DROPPED, 8 OF THEM GENUINELY BARRED
**2026-08-10.** `eligibility.py`, closing R238 tier 0. Three catalogue fields the ranker had
never read are now checked on every build.

**Dropped (Iden cannot register for these at all):**
| section | reason |
|---|---|
| CTM2012-01-00 · CTM2018-01-00 | **폐강** — cancelled |
| SCT4315 · SCT4316 · IIT4002 · IIT4311 | *"2026학번부터는 3학년 이상만 수강 가능"* — he **is** 2026학번 and 1학년 |
| SIT4204 · SIT4313 | *"3학년 이상만 수강 가능"* |
| CAS1102-01/02 | department allow-list: 첨단컴퓨팅학부 전공자 + 진리자유학부 only — **UIC is not on it** |

**Kept deliberately:** "UIC students only" (328 sections — satisfied), `BIZ2129` *"1학년만 수강
가능"* (he IS 1학년), and 4 sections whose 유의사항 says *"(Recommended) Prerequisite"* — a
recommendation, not a gate, so flagged and kept.

⭐ **Only the unambiguous, machine-checkable conditions are filters.** Filtering on free text
is how a legal option disappears silently, so anything needing judgement stays a flag.

R61 audited eligibility once, against a SciLit pool belonging to a model since replaced. This
re-runs against whatever the pool actually holds, every build. Verdict unchanged after
re-searching: **Lang wins all six cells, +0.22 tightest.**

⚠️ Also fixed: `research_v3`'s R219 floor check was comparing a **constrained** run
(`MAX_FREE=0`) against an **unconstrained** floor and reporting "THE BOUND IS UNSOUND" on every
such run. A check that cries wolf is worse than no check. It now applies only when the run is
itself unconstrained.

---

## R241. ⭐⭐ THE DOUBLE-MAJOR ASSUMPTION TESTED — THE ANSWER IS INVARIANT, FOR A REASON WORTH KNOWING
**2026-08-10.** R238 named this the largest unexamined assumption: the ledger encodes ME = 18 cr,
`DM` = 12 units and `FREE` = 15 cr, all three of which follow from **obtaining a double major**
— a December, competitive decision made on the GPA this very semester produces.

`ledger_nodm.py` derives the single-major ledger the same way the live one was derived (R31:
Major credits reduce to 36 *only* with a double major):

| item | with a double major | without |
|---|---:|---:|
| ME | 6 units (18 cr) | **8 units (24 cr)** |
| DM | 12 units (36 cr) | **0** |
| FREE | 5 units (15 cr) | **15 units (45 cr)** |

Both reconcile to **106.5 cr** over **38 units**. What changes is the mix — and one structural
fact: **units that MUST be taken at 신촌 fall from 14 to 2.** `DM` is the only bulk 신촌-only
item, so without it the campus plan is barely forced at all.

### Where each deferred requirement lands, under both ledgers
| requirement | with DM | without DM | |
|---|---|---|---|
| MR | sem 3 · Spring · 국제 | sem 3 · Spring · 국제 | same |
| **WCiv** | sem 7 · Spring · 국제 | **sem 3** · Spring · 국제 | moves semester, **same campus + season** |
| LHP | sem 4 · Fall · 신촌 | sem 4 · Fall · 신촌 | same |
| SciRD | sem 4 · Fall · 신촌 | sem 4 · Fall · 신촌 | same |
| **Lang** | sem 4 · Fall · **신촌** | sem 4 · Fall · **신촌** | same — **P(hard)=1 survives** |

Campus patterns do change (ISSSSS → ISISII: fewer 신촌 semesters without DM), but **every
deferred requirement keeps its receiving campus AND season.**

⭐ **So the Fall 2026 verdict is invariant to whether the double major is obtained.** That is a
real result and it removes the largest flagged risk.

⚠️ **But know why it is invariant.** K is keyed on **(campus, season)**, and those do not move.
It is *not* invariant because the degree shape is unimportant — the shape changes enormously —
but because none of the changed quantities reach the Fall 2026 decision through a channel v3
models. Two channels it would reach if the model were finer:
- K is measured against a generic ≥3h filler pool, **not against the actual remaining ledger**.
  A degree that is one third free electives has easier future semesters than one carrying 12
  신촌 major courses, and K would fall. Unmodelled.
- The 신촌 preference (R126) has nothing left to bite on when only 2 units force 신촌.

---

## R242. ⭐⭐ THE CLICK ORDER, COMPUTED — G-5 CLOSED WITHOUT SEAT DATA
**2026-08-10.** `fallback.py`. G-5/G-6 have been open since session one: the model emits a
ranked SET, but on 8/25 Iden clicks in an ORDER on 대기순번제 and finds out what he got. R168
recorded that the ranking and the click-order are one object; they were never joined.

**The equal-swap lists were not the answer.** By construction the optimum has no equal-score
alternative, so every course in the recommendation reports "no fallback" — tautological, not
informative. What G-5 actually asked for is *"degraded branches must be scored, not merely
listed"*.

### Method — needs no seat data
For each section in the recommendation, delete that 분반 from every pool and re-run the full
v3 search. `cost(section) = best score with it − best score without it`.

| section | cost of losing it | best fallback |
|---|---:|---|
| **UIC1561-01-00** Western Civilization | **35.72** | 28.91 · switch to deferring WCiv |
| QRM1001-01-00 Intro to QRM | 0.25 | 64.38 · switch to deferring MR |
| UIC1551-01-00 World History | 0.25 | 64.38 · take UIC1551-**04** instead |
| UIC2151-12-00 RDQM | 0.25 | 64.38 · take UIC2151-06/07/08 |
| STA2102-05-00 Linear Algebra | 0.25 | 64.38 |
| YCA1006-02-00 Chapel | 0.25 | 64.38 · take YCA1006-**01** |
| YCE1253-01-00 (free elective) | **0.00** | 64.63 · YCI1704-02-00 is an exact substitute |

### ⭐ THE RESULT IS EXTREMELY LOPSIDED, AND THAT IS THE USEFUL PART
**UIC1561 is the whole timetable.** It is the ONLY Western Civilization section in the
catalogue (supply 3 → 1 after eligibility), so losing it forces the WCiv-deferred branch and
costs **35.72** — 143× the next-worst loss. Everything else costs 0.25 or nothing, because
每 one has either another 분반 at equal quality or a near-identical substitute.

> **CLICK ORDER on 8/25: UIC1561-01-00 FIRST, without hesitation.** The remaining six are
> effectively interchangeable in urgency — any of them can be lost for a quarter of a point.

### What the 8/14 pull adds, and what it does not
The seat data supplies the **probability** each section is gone. It changes none of the costs
above. Cost × probability is the full picture; this is the cost half and it was computable all
along. ⚠️ It also means the highest-value thing the 8/14 pull can tell us is narrow and
specific: **is UIC1561-01-00 obtainable by a 1학년?** If its `sy1PercpCnt` is 0, the plan does
not degrade — it collapses to a 28.91 timetable.

---

## R243. ⭐⭐ THE 유의사항 CENSUS — 52 NOTICE TYPES NOTHING READ, AND ONE OVER-FILTER I CAUGHT
**2026-08-10.** Iden: *"Are we still tracking all the 기타 tabs, like UIC only…"*

### First: is the section universe even complete?
Checked the fetch against the official `강의목록_2026F.xlsx` (1,690 rows → **1,500 distinct
sections**; the extra 190 are the same duplicate-listing effect as R237). Fetched: **1,500**.
**Exactly one section is missing: `YCA1004-01-00` 채플(4)(비대면), 신촌, 일0.** A Sunday online
chapel at the wrong campus. Coverage is otherwise complete — the 37 embedded queries in
`refetch_listings` do reach the whole catalogue.

### Then: what do the notices actually say?
212 of the 341 pool sections carry a 유의사항. Coverage before this rule:

| | |
|---:|---|
| 148 | "UIC students only" — satisfied |
| 8 | excluded by a rule |
| 4 | flagged |
| **52** | **⚠ examined by nothing at all** |

⛔ **The patterns were Korean-only.** Restriction text is bilingual, and two real exclusions
were written in English or in a bracketed tag:

- `CDM4004-01-00` — *"CDM students only"*. Unconditional. **Now excluded.**
- `CHE1011-01-00` — *"[수강대상] 공학계열 9월 신입생"* (engineering track, September entrants).
  Too varied a form to filter safely, so **flagged with its text shown**, not dropped.

### ⚠️ AND THE OVER-FILTER I NEARLY SHIPPED — scope matters
The widened English rule first excluded `IID1001`, `IID2005`, `IID3004` on *"only IID first
major and double major students can enroll"*. Reading the **full** notice:

> *"**During the mileage course registration period**, only IID first major and double major
> students can enroll for the course. **The remaining spots will be available to all students
> during the additional course enrollment/add&drop period.**"*

That binds the **mileage round — 2학년+ only (R130)**. Iden registers 8/25 on 대기순번제, so it
does not exclude him at all. It is a **seat-competition fact for the 8/14 pull**, not an
eligibility gate. Reverted to a flag (`mileage-round priority`, 6 sections).

⭐ **The rule this earns:** an "only X" clause must be read **with its scope clause**. Matching
the restriction and ignoring the sentence that lifts it is how a legal option disappears
silently — the exact failure mode `eligibility.py`'s own docstring warns about, committed by
its own author within the hour.

**Final: 10 sections dropped, 11 flagged.** Verdict unchanged — Lang wins 6/6.

---

## R244. ⭐ RE-AUDITING IDEN'S OWN STATEMENTS AGAINST v3 — one constraint fell out of the model when V did
**2026-08-10.** Iden: *"anything else missing? From what I said, or… something written somewhere."*
Re-ran the audit package's own standing question against all **468** quoted statements in
`audit/ELICITED.md`: *is this expressed anywhere in the objective, and if not, should it be?*

Almost everything unmatched is methodological (R208–R240 are about how the model is built, not
what it should contain). **One is a live constraint**, and it names its own exception:

> *"I explicitly mentioned language does not matter, except for you know the CC (has to be
> English) and Majors (max credit limit)."* — Iden, R202

**(a) CC/MR pools stay English** — re-verified on the current, filtered pool:
WCiv 1 · LHP 16 · SciRD 14 · MR 1 sections, **0 non-English in any of them.** Holds.

**(b) The Korean ME cap** (R152/R105: at most 4 courses / 12 cr of Korean 상경·응통 sections
count as Major Credit) — **this one was enforced inside `continuation.solve()`, and v3 does not
import `continuation` (R226). It fell out of the model when V did.**

Measured now: 13 ME-eligible sections, 2 non-English, and **0 offered by 상경대학/응용통계** —
every one comes from UIC itself (11 계량위험관리 + 2 경제학). So the cap **does not bind in Fall
2026** and the answer is unaffected. R152's original measurement survives the pool changes.

⚠️ But it is unenforced rather than satisfied-by-construction. Added to `test_v3.py` so that if
the count ever exceeds 4, something says so — because nothing in the v3 path would.

### ⚠️ AND A MISREAD I MADE ON THE WAY
First pass reported "16 of 16 LHP sections Korean-taught", contradicting R92 which
`test_retired` says still holds. The field `lang` is `srclnLctreLangDivCd`, a **code** where
`'10'` = 영어 — I compared it against the *name* `'영어'`, so every section looked non-English.
Caught only because it contradicted a passing assertion.

⭐ **That is the third time in this session a test's disagreement caught my analysis rather than
the other way round** (R237's duplicate, R240's floor false-alarm, this). The suite is not
decoration.

---

## R245. ⭐⭐ THE DOUBLE MAJOR WAS NEVER GIVEN COURSE IDENTITIES — AND IDEN FOUND THE CONSEQUENCE
**2026-08-10.** Iden: *"how did we handle the double major? I was sort of worried about linear
algebra, because if I happen to double in mathematics, then Mathematics has that as a
requirement? I wasn't sure if I would have to listen to it twice."*

### How it was handled: it wasn't
`plan_model.ITEMS['DM']` is **12 units with `codes=[]`** (R225). R241 tested that the Fall 2026
*verdict* is invariant to whether the double major is obtained — but **nothing has ever
represented what the second major would CONTAIN.** Overlap between the QRM major and a
Mathematics 이중전공 is therefore structurally invisible to every version of the model.

### He is right, and here is the documentation
**수학전공 전공필수** (대학요람 p.65): *"해석학(1), 현대대수(1), 선형대수(1) (9학점)"*.
Observed codes across six terms: **`MAT2102 선형대수(1)`** (이과대학 수학전공, **Spring-only** —
2024-1, 2025-1, 2026-1), `MAT3109 현대대수(1)`, `MAT3104 해석학(1)`.

**`STA2102 선형대수` is a different course.** Cross-listed as
언더우드국제대학 융합사회과학부-계량위험관리 (과목종별 **ME**) and 상경대학 응용통계학전공
(과목종별 **전기**) — its own notice reads *"UIC-QRM Cross(응용통계학과 및 타학과도 수강신청
가능)"*. It is **not** listed under 이과대학 수학전공 in any of the six terms.

> ⇒ **Taking `STA2102` does NOT satisfy Mathematics' `선형대수(1)`.** If Iden takes it now as a
> QRM Major Elective and later double-majors in Mathematics, he must also take `MAT2102`.
> Same subject, two courses. His instinct was correct.

### The cost of avoiding it is 0.25
Excluding every linear-algebra ME in the Fall 2026 국제 pool (`STA2102-04/05`, `QRM2102-01` —
*Linear Algebra and Differential Equations*, which duplicates the same content):

| | score | timetable |
|---|---:|---|
| as recommended | **64.63** | defer Lang · … `STA2102-05` |
| no linear-algebra ME | **64.38** | defer MR · … `ECO1101-06` |

**Cost: 0.25.** The same figure as every other single-section loss in R242 — the ME slot is
the least load-bearing thing in the timetable.

⭐ **So this is a genuinely free choice, and it is Iden's to make.** The model cannot make it,
because it has no representation of what a Mathematics 이중전공 requires. It can only report
that hedging against the duplication costs a quarter of a point.

⚠️ Do not read this as "avoid STA2102". A 응용통계 linear algebra and a 수학과 proof-based
`선형대수(1)` are different treatments of the subject and taking both may be worth it. The
finding is that **the choice exists, is nearly free, and was invisible until he asked.**

### What it would take to model properly
Give `DM` real course codes per candidate major (Mathematics / Economics / CS), then the
overlap and the 교차인정 rules become computable. That is blocked on the December decision —
but note the ledger could carry a *provisional* Mathematics course list now, since the
requirements are published.

---

## R246. ⭐⭐ OFFICIAL SOURCES ON DECLARATION AND CROSS-DEPARTMENT CREDIT — read from uic.yonsei.ac.kr, not from a wiki
**2026-08-10.** Iden challenged a 나무위키-based answer as an inadequate source. Correct. The
site is JavaScript-rendered so `web_fetch` returns an empty shell; read via the browser tools.

### ⭐ DECLARATION HAS NO REQUIREMENTS. Settled.
**[HASS Only] Declaring/Changing Major and Double Major** (UIC Announcements, Dec 5 2024):

> "UIC HASS Division students can choose their 1st major among the following 8 majors. … ⑥
> Quantitative Risk Management (QRM) …
> **\* Students will be accepted to the major of their choice without any selection process.**"

No course prerequisite, no GPA gate, no 선수과목. Declaration happens in the **2nd semester**;
the major may be changed once within HASS by the end of the 7th. **`통계학입문` is NOT required
to declare QRM** — it is a QRM *graduation* requirement (the UICE row, R100). Iden had believed
otherwise and had taken 통입 partly for that reason; the action was right, the stated reason was
not, and the distinction is graduation-requirement vs declaration-gate.

⚠️ **AND ONE LINE IN IT TOUCHES THE MODEL:** *"during the registration period, students' mileage
will be vetted according to the major they applied for."* The **declared major changes mileage
standing**. Nothing in the model represents that; it sits next to R130 and the tie-break ladder.

### ⭐⭐ THE SAME-SUBJECT / TWO-DEPARTMENTS TRAP IS OFFICIAL AND ALREADY BIT ONCE
**Important Updates regarding Double Major / Minor in Applied Statistics for QRM students**
(UIC Announcements, Jul 1 2024) — from **Fall 2024**:

| QRM | | 응용통계학과 | |
|---|---|---|---|
| REGRESSION ANALYSIS `QRM3004` | MR | 회귀분석 `STA3125` | 전공선택 |
| MATHEMATICAL STATISTICS 1 `QRM3005` | MR | 수리통계학(1) `STA3126` | 전공필수 |
| STATISTICAL ANALYTIC METHODS `QRM2004` | ME | 통계방법론 `STA2105` | 전공기초 |

**Only the QRM-coded versions count as QRM major credit**, and taking the QRM version does
**not** count toward an Applied Statistics double major. The reverse held only for courses taken
before Fall 2024.

⭐ **This is R245's linear-algebra finding, but official and already enacted:** one subject,
two departments, and the code you pick determines which degree it counts for. `STA2102 선형대수`
vs `MAT2102 선형대수(1)` is the same shape. **Any second-major analysis must check code-level
credit recognition, not subject overlap.**

### Provenance note
`uic.yonsei.ac.kr` degree-requirement downloads (`/undergraduate.php?mid=m02_06_02`) confirm
the local `QRM_Graduation_Requirement_table (2022~) (1).pdf` is the official QRM (2022~) file.

---

## R247. The 8/16 seat pull SUCCEEDED — and `UIC1561-01-00` does NOT bar a 1학년
`fetch_fall2026.py`, run on Iden's machine 2026-08-16, 179 sections, Fall 2026 (`2026`/`20`).
The 2학년+ mileage round (8/10–8/11) and 추가수강신청 (8/13–8/14) were both closed, so this
is final. Wrote `fall2026_seats.json`.

```
⭐ UIC1561-01-00   sy1..sy6 = [0,0,0,0,0,0]  ->  NO per-year scheme  ->  NOT BARRED (R2/R134)
```

**The 35.72 question (R242) is answered and the v3 recommendation survives it.** This is the
single check INDEX carried as "the only thing with a deadline" since session one. It is closed.

**Two sections bar 1학년 outright** — scheme in force, 1학년 share 0:

| section | 정원 | 신청 | sy1..sy6 | |
|---|---|---|---|---|
| `YCG1804-01-00` 인간의감정,감정의인간 | 260 | 263 | `[0,86,87,87,0,0]` | 목11,12,13 국제 |
| `YCG1853-01-00` 문명과질병 | 190 | 177 | `[0,63,63,64,0,0]` | 금7,8,9 국제 |

Neither is in the recommendation or in any `fallback.json` chain, but **both are reachable
candidates** (they came out of the v3 rows), so they must be excluded before any re-search.
Two more run a scheme *with* a non-zero 1학년 share and are fine: `EDU2002-01-00` (몫 70/80),
`SOC1004-01-00` (몫 45/60).

## R248. ⛔ `atnlcPercpCnt` IS NOT SECTION CAPACITY — do not compute 여석 from it
The instinct on reading the pull is `여석 = atnlcPercpCnt − cnt`. That is wrong, and it would
have produced the false headline "`UIC1551-01-00` is oversubscribed at 정원 3 / 신청 4".

**Proof it is not room capacity.** Of 18 courses with more than one 분반 fetched, **17 hold
`atnlcPercpCnt` constant across every 분반**, independent of 강의실:

| course | 정원 | 분반 | distinct 강의실 |
|---|---|---|---|
| `UIC2151` | 3 | 9 | 4 |
| `UIC1501` | 3 | 5 | 3 |
| `UIC1551` | 3 | 3 | 2 |
| `YCF1201` | 2 | 3 | 2 |

Nine sections in four different rooms do not all seat exactly three people. The number is
attached to the **course**, not the room — it is an administrative allocation. 55 of 141
returned rows have `atnlcPercpCnt ≤ 5`.

**Most likely reading (NOT confirmed):** seats released *to the mileage round*, with UIC's own
requirement courses holding nearly everything back for the 8/25 신입생 first-come round —
which would explain why UIC requirement courses show 2–3 while `QRM1001` shows 78, `STA2102`
60 and 채플 696. That is consistent with R7/R130 (freshmen are structurally outside this
table) but **is not established by this data and must not be scored.**

⚠️ Therefore the pull answers the **eligibility** question (R134) and **not** the seat-competition
question. `fallback.py` remains the cost half of `cost × probability`; the probability half is
still unmeasured. Do not let `정원`/`신청` from this file enter any score.

## R249. A blank mileage row is not a bar
38 of 179 sections returned no row at all, including `YCE1253-01-00`, which is **in the
recommendation**. Freshmen are invisible in this table (R7) and per-year quotas are optional
(R134), so absence is absence of evidence. `fetch_fall2026.py` reports blanks separately from
barred for exactly this reason.

---

## R250. ⛔ The branch cache was keyed on `MAX_FREE` alone — every constant sweep was a no-op
`research_v3.STATE = _v3_parts_f{MAX_FREE}`. The scoring constants were not part of the key:

```
$ D_LANG=999.0 MAX_FREE=2 python research_v3.py Lang
branch Lang: cached
```

So any sensitivity analysis run through `research_v3.py` **returned the baseline at every grid
point**, and a sweep that did nothing was indistinguishable from a sweep that found the model
robust. This held for the entire life of the v3 model, for both unelicited constants.

**Fixed 2026-08-16:** `run_branch` stamps `{D_LANG, GPA_GATE_MULT, MAX_FREE}` into each part
file; `cache_is_valid()` rejects a stale or pre-stamp cache and prints why. Two assertions in
`test_v3.py` lock it, one by perturbing `D_LANG` and requiring rejection.

Compounding it: **`sweep_difficulty.py` has raised `TypeError` since R190** (it adds
`p_hard_if_deferred()`'s bracket as a scalar), reads the superseded `FINAL_ranked4.csv`, and
rescores a fixed candidate set rather than re-searching. Replaced by `sweep_holes.py`.

## R251. The verdict survives `D_LANG`; `GPA_GATE_MULT` is DORMANT, not dead
`sweep_holes.py` re-searches at every grid point (no cache reuse):

| `D_LANG` | 0 | 5 | 10 ⭐ | 20 | 45 |
|---|---|---|---|---|---|
| defer | **MR** | Lang | Lang | Lang | Lang |

Refined, the flip is **between 1.0 and 2.0** against a default of **10.0**. The deferral
verdict is robust to the constant that was never elicited, by 5–10×.

`GPA_GATE_MULT` is identical at 1.0 and 2.0 across the whole grid — **because the winning
branch defers Language, so the timetable holds no language course, so
`sum(DIFF.steps(...)) = 0` and `dif` is zero.** The multiplier multiplies nothing.

⚠️ **It is inert only while Language is deferred.** Below `D_LANG ≈ 2` the verdict flips to
TAKING a language and `GPA_GATE_MULT` becomes live, unelicited scoring. Classify it as
dormant, never as dead.

## R252. A neutral default is a value choice, not an abstention
From the shaped-hole audit (`SHAPED_HOLES_2026-08-16.md`). `risk.p_win_bracket` returns
`(1.0, 1.0, 'NO DATA')` for the **6 of 12** required courses with no mileage history
(`ECO2101 ECO2102 QRM3003 QRM3004 QRM3005 STA2102`). A probability of 1.0 is not "unknown" —
it is **certain acquisition**, the most optimistic value available. Nothing consumes it today.

The general rule, earned by `risk.p_get_freshman` (R247/§0.1): **"the model is numerically
unchanged today" describes code that has never run, and is not a safety property.** A
placeholder's first real execution happens when the data lands, which is exactly when nobody
is watching it. Assume every dormant path is wrong until it has been forced to run.

---

## R253. ⛔⛔ "DEFER LANGUAGE" DEPENDS ON AN UNJUSTIFIED OPTIMISTIC AGGREGATOR
Asked why the model defers Language, the decomposition gives an answer that is **not** the
difficulty axis:

```
BEST TOTAL PER BRANCH at D_LANG = 10        (total = score + Σunit_cost − K)
  defer Lang    K = −4.725    64.633    language taken: none
  defer MR      K =  0.000    64.379    language taken: UIC1806-02-00 (EASY, 0 steps)
  ⭐ margin 0.254 — on a scale where one 9:00 start = 10.0
```

**`K(Lang)` is NEGATIVE, and that — not difficulty — is what wins.** Difficulty only
eliminates the *hard* tier: at `D_LANG = 0` the winner is "defer MR, take hard Spanish
`YCF1603`" at 66.329. Above `D_LANG ≈ 2` the contest is between **no language** and **easy
language**, both of which charge zero difficulty steps, so `D_LANG` cannot separate them.
That is why R251's flip is at 1–2 and not at R188's old 10.25 boundary.

### The aggregator is the whole verdict
`fallback.kdefer()` returns `min(d.values())` — the single most favourable of the receiving
geometries. For Language there are **eleven**:

| item | year | n | MIN (used) | median | MAX | spread |
|---|---|---:|---:|---:|---:|---:|
| `Lang·hard` | 2026 | 11 | **−4.725** | 16.615 | 27.525 | **32.250** |
| `MR` | 2026 | 2 | 0.000 | 7.441 | 14.881 | 14.881 |

**The 0.254 margin is 0.8% of the spread of the number that produces it.** Re-running the
branch comparison with the aggregator swapped:

| aggregator | winner | margin |
|---|---|---|
| **MIN (in force)** | defer **Lang** | 0.254 |
| MEDIAN | defer **MR** | 13.645 |
| MAX | defer **MR** | 16.165 |

⇒ **The recommendation survives only under the most optimistic aggregation, and only by
0.254. Under any weaker assumption it inverts, and by 50–60× the margin.**

### What MIN actually assumes
It is not indefensible: Iden *chooses* his future timetable, so "best geometry" is arguably
his to take. But it assumes he **acquires his first choice**, and language sections are the
most contested things in the ledger (R6, R190) — precisely where that assumption is least
safe. MIN is a claim about acquisition, and acquisition probability is exactly what R248
showed we cannot measure.

**Nothing elicited this choice. It must not stand as a default.** The alternative to picking
an aggregator is to report the deferral verdict as UNRESOLVED between Lang and MR, which is
what the numbers actually support.

---

## R254. ⭐⭐ THE DEFERRAL VERDICT RESTS ON A PROBABILITY THAT WAS NEVER FETCHED
Chasing "why does the model defer Language" to the bottom. Three facts, in order.

### 1. It is not the difficulty axis
```
BEST TOTAL PER BRANCH at D_LANG = 10
  defer Lang   K = −4.725   64.633   language taken: none
  defer MR     K =  0.000   64.379   language taken: UIC1806-02 (EASY, 0 steps)
```
`K(Lang)` being **negative** is what wins. Difficulty only eliminates the *hard* tier — above
`D_LANG ≈ 2` the contest is **no language** vs **easy language**, both at 0 steps, so `D_LANG`
cannot separate them at all (R251/R253).

### 2. `min()` is not uniform, and where it is uniform it is not neutral
`kdefer()` special-cases MR to a fixed geometry (`KD['MR'][y].get('목4,5,6')`) and uses
`min()` for the other four. And `min()` is an **n-dependent estimator**:

| item | n geometries | min (used) | E[min] at n=1 |
|---|---:|---:|---:|
| `Lang·hard` | **11** | −4.725 | **+13.567** |
| `WCiv` · `LHP` | 1 | = the value | = the value |

An 18.3-point swing from sample size alone, against a 0.254 margin.

**But this is not simply a bug.** Lang has 11 geometries because many language sections exist;
WCiv has 1 because `UIC1561` has one section. That is **real optionality** — `min()` correctly
says "I can pick the best-fitting slot." What it additionally assumes is that he **gets** it.

### 3. ⭐ So the verdict is a bet on acquisition, and the bet has a threshold
Modelling each of the 11 geometries as independently obtainable with probability `p` and
taking `E[min over the obtainable ones]`:

| p | 1.00 | 0.95 | **0.90** | 0.80 | 0.50 | 0.20 |
|---|---|---|---|---|---|---|
| verdict | Lang | Lang | **MR** | MR | MR | MR |

**Crossover at p = 0.901.** "Defer Language" requires a ~90%+ chance of getting a wanted
language slot as a 2학년+ mileage bidder.

### And p was never measured — because the hard tier was never fetched
`risk.p_win_bracket` returns `NO DATA -> p = 1.0` for **all eight** hard-tier courses. Root
cause: `fetch_mileage.REQ['Lang']` listed only `UIC1805, UIC1806` — the easy tier. Zero YCF
rows exist in `mileage_history.json`.

⇒ **The verdict rests on `p = 1.0`, a value that is not a measurement but R252's optimistic
default, sitting exactly above the 0.901 threshold it needs to clear.**

**FIXED 2026-08-16:** the eight YCF codes are now in `fetch_mileage.REQ['Lang']` (60 → 108
sections). Running it on Iden's machine measures `p` directly and settles Lang-vs-MR by
arithmetic. **This is the highest-value fetch remaining and it needs one cookie.**

## R255. The late arm never fires on a deferred requirement — but it cannot change the verdict
R145/R146 designed the two-sided year penalty so the LATE arm fires on deferred courses.
In the v3 path it does not: `fallback.total()` charges `kdefer(b)` (a comfort measure) plus
`unit_cost()` over the ELECTIVE ledger items, and `unit_cost` applies a year-gap term to only
`ECO1101` and `ME`. No deferral branch carries a sequencing penalty.

Measured, it does not matter: every deferrable pool is chart-year 1 (`MR` 1, `WCiv` 1,
`SciRD` 1, `LHP` 14×1 + 2×2, `Lang` 8×1 + 16×year-0), so the late arm would be a uniform
−2.667 across all five branches and cannot separate them. **A missing term, not a missing
verdict** — record it, do not re-derive the answer from it.

Also noted: the year axis is **difficulty-blind** and the difficulty axis is **time-blind**.
`DIFF.steps()` charges a hard language identically in Fall 2026 and Spring 2029. `GPA_GATE_MULT`
exists precisely to couple them (R153 — difficulty → GPA → December admission, both edges
through THIS semester) and is inert at 1.0 (R251).

---

## R256. ⭐⭐ THE ACQUISITION PROBABILITY WAS BEING MEASURED AT THE WRONG CAMPUS
The 2026-08-16 refetch (R254) added the eight hard-tier YCF codes and worked: `mileage_history.json`
went 142 → 187 rows, and all eight now have 국제 history, mean `p_lo = 0.849`, `p_hi = 1.000`.
The verdict threshold is `p = 0.901`, so that bracket **straddles** it — no resolution.

**But 국제 is the wrong campus.** `k_real.CASES` receives `Lang·hard` at **신촌, season F**.
At 신촌, seven of eight hard languages still returned NO DATA.

### Root cause: 분반 numbering differs by campus
`fetch_mileage.sections_from_files()` derived its `(subjtnb, 분반)` probes from
`canonical_2026F.json` — the **국제** Fall catalogue — plus a Spring xlsx absent on the machine.

| course | probed 분반 (국제) | 신촌 분반 | overlap |
|---|---|---|---|
| `YCF1301` | 05,06,07,08 | 01,02,03,04 | **NONE** |
| `YCF1351` `YCF1451` `YCF1501` `YCF1603` | 03,04 | 01,02 | **NONE** |
| `YCF1601` `YCF1607` | 02 | 01 | **NONE** |
| `YCF1551` | 04,05 | 01,02,03,04 | **04** |

⇒ 7 of 8 had zero overlap. `YCF1551` matched **by coincidence**, and was therefore the only
hard language with any 신촌 history at all.

### What the measured evidence says, once the campus is matched
The geometry the whole verdict rests on — `월3,4`, `K = −4.725` — is owned by
`YCF1301`/`YCF1451`/`YCF1501`, **all three unmeasured at 신촌**. The only 신촌-measured hard
language, `YCF1551` (`p_lo = 1.00`), owns `화3,4` at `K = −2.487`.

| K(Lang) source | verdict | margin |
|---|---|---|
| `min()` over all 11 geometries (in force) | defer **Lang** | 0.254 |
| best geometry whose acquisition is **MEASURED** | defer **MR** | **1.984** |
| E[min] at the crossover `p = 0.901` | defer MR | 0.003 |

⇒ **On measured evidence the answer is defer MR. "Defer Language" survives only on
geometries whose obtainability has never been observed.**

⚠️ Restricting to one measured course is itself conservative, exactly as `min()` over all
eleven is optimistic. The honest statement is that the verdict is **bracketed and the
bracket straddles the flip**, with the measured side favouring MR.

**FIXED:** `sections_from_files()` now also seeds probes from `past_terms.json`, which
carries 신촌 rows. Probe set 76 → 164 sections; hard-tier courses with all 신촌 분반 covered
went **1/8 → 8/8**. Re-running `fetch_mileage.py` measures `p` where `k_real` actually
receives, and settles Lang vs MR on evidence.

## R257. ⛔ R250 REINTRODUCED, BY ME, THE SAME DAY — the fetch cache omitted its probe set
`fetch_mileage.py`'s resume logic (written 2026-08-16) stored `_mlg_state/{term}.json` as a
bare **list of rows**. It recorded what came back but not **which sections were asked for**.

So when R256 added the 88 신촌 probes, the next run printed

```
  2026-2학기: cached (4 rows)
  2026-1학기: cached (46 rows)
  ...
wrote mileage_history.json — 187 rows
```

— five "cached" lines, **zero new fetches**, and an output file identical to the previous run.
The fix that was supposed to settle Lang-vs-MR silently did nothing.

**This is R250 exactly** — a cache key that omits what determines the contents — written into
new code hours after R250 was recorded and asserted against. Knowing the failure mode did not
prevent committing it; only running the thing did.

**Fixed:** the state file is now `{"_probed": [...section ids...], "rows": [...]}` and only
un-probed sections are fetched. Legacy list-format caches are credited for the sections that
returned data and the rest re-probed once, so nothing already fetched is lost. Partial
progress is written before the stale/offline break, so an expired cookie mid-run keeps
everything.

Dry run after the fix: **561 requests (~1.9 min)**, of which **128 are hard-tier language**
probes that had never been issued.

### The rule
A cache is a claim that *inputs unchanged ⇒ outputs unchanged*. If the key does not contain
every input, the claim is false and the failure is **silent and confirmatory** — it reports
success and returns the old answer. Both instances here were found only by comparing a fetch
count against expectation. **Any cache in this project must record its inputs, and any
"cached"/"unchanged" message must be treated as a claim to verify, not a result.**

---

## R258. ⭐⭐ p IS NOW MEASURED AT 신촌 — "defer Language" survives, but the margin is ≤ 0.29 everywhere
The R257 fix worked: `mileage_history.json` 187 → **476 rows**, `Lang` 56 → **149**, and YCF
rows at 신촌 **0 → 86**. All eight hard-tier languages now have 신촌 history.

### The measurement
`p_win_bracket(code, 36, '신촌')` — `p_lo` = must MATCH the top applicant, `p_hi` = need only
beat the weakest:

| course | n | p_lo | | course | n | p_lo |
|---|---:|---:|---|---|---:|---:|
| `YCF1301` | 20 | 0.650 | | `YCF1551` | 16 | 0.875 |
| `YCF1351` | 10 | 0.000 | | `YCF1601` | 5 | 0.600 |
| `YCF1451` | 10 | 0.000 | | `YCF1603` | 10 | 0.200 |
| `YCF1501` | 10 | 0.400 | | `YCF1607` | 5 | 1.000 |

mean `p_lo` = 0.466, `p_hi` = 1.000 throughout.

### R254's single-`p` model was too crude — geometries have MULTIPLE owners
A geometry is obtainable if **any** course offering it is. `월3,4` (the `K = −4.725` slot) is
offered by `YCF1301`, `YCF1451` **and** `YCF1501`, so even on the pessimistic arm
`p_g = 1 − (1−0.65)(1−0.00)(1−0.40) = 0.79`. Averaging `p` across courses (R254) destroyed
exactly this structure and is superseded.

With `p_g = 1 − Π(1−p_course)` and `E[min over obtainable geometries]`, verified **through the
model**, not the hand-derived flip point:

| t | arm | E[K(Lang)] | verdict | margin |
|---|---|---:|---|---:|
| 0.00 | pessimistic (match top bid) | −4.178 | defer **MR** | 0.293 |
| 0.25 | | −4.509 | defer **Lang** | 0.038 |
| 0.50 | midpoint | −4.664 | defer **Lang** | 0.193 |
| 1.00 | optimistic (beat weakest) | −4.725 | defer **Lang** | 0.254 |

**Crossover at t = 0.210.** "Defer Language" holds across ~79% of the measured bracket, and
fails only near the fully-pessimistic corner where he must match the top bid on every course
simultaneously — which even then only enters an unmodelled tie-break (R190).

### ⚠️ What this does NOT establish
The margin never exceeds **0.293 in either direction**, on a scale where one 9:00 start = 10.
The measurement moved the *reason* from a default to evidence; it did not separate the two
strategies. **Lang and MR remain within noise of each other, and R253 stands: the model does
not resolve this.** What changed is that the answer no longer rests on `p = 1.0` fabricated by
a missing fetch (R252/R254) — it rests on 86 observed 신촌 rows, and it survives 79% of them.

## R259. A bracket whose two arms are equal asserts knowledge — NO DATA must widen, not collapse
`risk.p_win_bracket` returned `(1.0, 1.0, 'NO DATA')` for any course with no mileage history.
Both arms equal is a **point estimate**, and the point chosen was the most optimistic value
available: certain acquisition. R254 caught it deciding the deferral verdict — every hard-tier
language was unfetched, so every one reported "certain", so deferring Language looked free.

**Fixed:** `(0.0, 1.0, 'NO DATA … (widest bracket)')`. Could fail, could succeed. This matches
the function's own contract ("the truth is inside; do not collapse it to a point estimate")
and the existing CAP-12 convention of surfacing unmodellable cases rather than defaulting them.

After the R257/R258 refetch only **6 of 42** (course, campus) pairs still have no history:
`QRM1001@신촌 · ECO2101@국제 · QRM3003@신촌 · UIC1561@신촌 · UIC1551@신촌 · UIC1806@신촌`.
`p_hard_if_deferred()` now brackets at [0.000, 0.292]. Locked by an R259 assertion that queries
a non-existent course and requires the arms to be 0 and 1.

**General form (with R252):** a neutral default must be neutral *in the estimator's own terms*.
For a bracket that means widening to the full range. Collapsing to either endpoint — however
labelled — is a claim.

## R260. ⛔⛔ `fallback.py` TRUNCATES BEFORE IT MAXIMISES — the recommendation is not the argmax
Found incidentally while building `prof_compare.py`, which ranked all 3000 rows per branch
instead of `fallback.py`'s `rows[:60]`.

`fallback.search()` reads `rows[:60]` — the top 60 by **raw `score`** — then maximises
`total(row,b) = score + Σunit_cost(items) − kdefer(b)`. But `unit_cost` is a large positive
credit for electives that discharge a constrained ledger item, and it is **not** part of
`score`. So the row maximising `total` need not rank highly by `score` at all.

```
best total within rows[:60]   :  64.633   (defer Lang, rank 2)
best total over ALL 3000 rows :  78.622   (defer Lang, rank 115)   <- the real argmax
missed gain                   :  13.989
```

The true maximiser swaps `YCE1253-01-00` for **`ECO1101-06-00`** (Major Required, carrying
both a displacement credit and a year-gap term) and sits at **rank 115** by score.

**13.989 points — larger than every margin argued over this entire session** (the Lang-vs-MR
gap is 0.254; the aggregator swing 13.6; one 9:00 start is 10).

⚠️ Consequences, none yet re-derived:
* the standing recommendation, `fallback.json`, the click order, and every 0.254-margin
  statement in R253/R254/R258 were computed on the truncated set;
* `prof_compare.py` reports **78.622** for the same reason and is the correct figure;
* the deferral verdict itself may move — the truncation was applied per branch, so branches
  are not equally penalised by it.

**Do not act on `fallback.json` or `TOP50_v3.html` until `search()` maximises over the full
row set.** The fix is one slice; the re-derivation is not.

## R261. R260 FIXED — the recommendation moves to 78.622 and the click order stops being degenerate
`fallback.search()` set `RV.TOPN = 60` *and* read `rows[:60]`, so the winner was never even
kept by the search. Now `FB_TOPN = 3000` and every row is maximised over.

| | before (truncated) | after |
|---|---|---|
| base total | 64.633 | **78.622** |
| elective | `YCE1253-01-00` | **`ECO1101-06-00`** |
| defer | Lang | Lang (unchanged) |

```
chapel  YCA1006-02
reqs    QRM1001-01 · UIC1561-01 · UIC1551-01 · UIC2151-12
elec    ECO1101-06 (Major Required) · STA2102-05 (Major Elective)
```

**The click order was the real casualty.** Truncated, every section except `UIC1561` cost
≤ 0.25 to lose — a degenerate result that made the ordering meaningless below rank 1:

| | cost to lose (old) | cost to lose (NEW) |
|---|---:|---:|
| `UIC1561-01` | 35.72 | **34.62** |
| `QRM1001-01` | 0.25 | **14.24** |
| `STA2102-05` | 0.25 | **9.08** |
| `ECO1101-06` | — | **7.97** |
| `UIC1551-01` · `UIC2151-12` · `YCA1006-02` | 0.25 | 0.22 |

Four sections now carry real loss, not one. R242's "losing anything else costs ≤0.25" is
**withdrawn**.

✅ `render_v3_top50.py` was NEVER affected — it reads every row and ranks on the full
objective. Only `fallback.py` truncated. `TOP50_v3.html` regenerated: 25141 structurally
distinct candidates → 110 cards; `DECISION_v3.html` still Lang in 6/6 cells.

⚠️ Not yet re-derived on the fixed basis: the Lang-vs-MR margin quoted in R253/R254/R258
(0.254, and the p-crossover 0.901 built on it). The verdict direction is unchanged but those
specific numbers came from the truncated set.

## R262. ⭐⭐ RE-DERIVED ON THE FIXED BASIS — the deferral verdict is far stronger than R253 claimed
Every margin in R253/R254/R258 was computed through `fallback.search()`, i.e. on the
truncated 60-row set (R260). Recomputed over all 3000 rows per branch:

### 1. Lang vs MR is NOT within noise
| branch | best total |
|---|---:|
| defer **Lang** | **78.622** |
| defer MR | 64.379 |
| defer WCiv | 44.004 |
| defer LHP | 40.032 |
| defer SciRD | 36.528 |
| defer nothing | 33.333 |

**Margin 14.243, not 0.254** — 56× larger, and 1.4 × one 9:00 start.
⇒ **R253's "Lang and MR remain within noise of each other" is WITHDRAWN.** It was an artefact
of truncation, not a property of the model.

### 2. The acquisition bet is settled
Per-geometry availability, pessimistic → optimistic arm of the measured 신촌 brackets:

| t | 0.00 | 0.25 | 0.50 | 1.00 |
|---|---|---|---|---|
| verdict | **Lang** | Lang | Lang | Lang |
| margin | 13.696 | 14.028 | 14.182 | 14.243 |

**Crossover t = 0.000** (was 0.210). Defer-Language now wins across the **entire** measured
bracket, including the fully-pessimistic corner where he must match the top bid everywhere.
⇒ **R254's `p ≥ 0.901` threshold and R258's "79% of the bracket" are both superseded.** The
acquisition probability no longer changes the answer at all.

### 3. The aggregator DOES still flip it — and is now the only live sensitivity
| aggregator | K(Lang) | verdict | margin |
|---|---:|---|---:|
| **MIN (in force)** | −4.725 | defer **Lang** | 14.243 |
| MEDIAN | 16.615 | defer **MR** | 7.097 |
| MAX | 27.525 | defer **MR** | 18.007 |

R253's central finding survives: the verdict inverts under a different aggregator. But the
choice is no longer between two near-tied options — it is between two well-separated regimes,
and the question is sharper: **`min()` models "he picks the best geometry still available",
`median()` models "he lands on a typical one without choosing".** Registration is a choice,
and §2 shows the best geometry is ≥79% obtainable even pessimistically, so `min()` is the
defensible model. That is an argument, not a measurement, and it is now the single load-
bearing modelling assumption behind the recommendation.

## R263. The renderer unions three searches — they must share their constants
`render_v3_top50.py` builds its card set from `_v3_parts_f0` + `_f1` + `_f2`. Those are three
separate searches that are *supposed* to differ in `MAX_FREE` and in nothing else. Nothing
checked that.

Found while adding the professor axis: `f2` was regenerated with the prof term and `f0`/`f1`
were not. Harmless **only** because `PROF_UNRATED = 0` with an empty sheet makes the term
identically zero. **The first rating entered into `prof_ratings.csv` would have made `f2`
candidates carry professor bonuses while `f0`/`f1` candidates did not — and the renderer
ranks them against each other.** Every professor bonus would have read as a free win, and
nothing would have said so.

**Fixed:** the renderer now collects each part file's `consts` (minus `MAX_FREE`, the one they
may legitimately differ in) and **refuses to render** if they disagree, printing the offending
files. Verified by running it against the mixed state — it exited rather than producing a
plausible-looking page.

⚠️ **Operational consequence: after editing `prof_ratings.csv`, ALL of `MAX_FREE` 0/1/2 must
be re-run**, not just one:
```
for mf in 0 1 2 99; do MAX_FREE=$mf D_LANG=10.0 python research_v3.py; done
python fallback.py && python render_v3_top50.py && python render_v3.py
```

### Also checked at this checkpoint, and clean
* **No other truncate-then-maximise** in the live path (R260 was the only one).
* **No rows silently dropped**: 0 of 18000 have `total() == None`; `kdefer` resolves for all
  six branches.
* **`unit_cost` uses `min()` over (국제S, 신촌F)** — the *opposite* optimism to `kdefer`'s
  `min()`, since it is a credit. Tested: `max()` gives defer **Lang** at 83.404 (margin
  18.750) vs `min()`'s 78.622 (margin 14.243). Conservative and **does not bind**.
* **`FREE` unit_cost = 0.0** is R236's measured residual, not a missing-data default.

---

## R264. ⛔⛔⛔ `pools_past.parse` DROPPED AND FABRICATED HOURS — the verdict inverts to defer MR
Found by the external red-team review (`REDTEAM_REPLY_2026-08-16.md`, F1). **Independently
reproduced here before acceptance.**

### The defect
`pools_past.parse` split on commas. `'월3,4,수3(수4)'.split(',')` yields the token `'수3(수4)'`;
`.strip('()')` strips nothing (neither end is a paren) and the digit-join gives `'34'`, which
fails the `1..15` range test — so the block was discarded. It also **invented** hours:

| source | parsed as | correct |
|---|---|---|
| `월3,4,수3(수4)` | `월3,4` | `월3,4/수3,4` |
| `화1,2,목1(목2)` | `화1,2/목12` ← period 12 does not exist | `화1,2/목1,2` |
| `수6,7(수8,9)` | `수6,9` ← 수7,8 lost, 수9 invented | `수6,7,8,9` |
| `금7(금8,9,10,11)` | `금9,10,11` | `금7,8,9,10,11` |

Its own docstring said *"Parenthesised blocks are kept (they hold a nominal slot)."* They were
not. **1,047 of 10,159 sections (10.3%) across six terms.** R54 settles the convention;
**R49 records this exact defect being found and fixed once already** in `fetch_2026_fall.py`
(2026-08-04, 101 of 661 sections) — with a char-scan parser that `pools_past` never adopted.

### Why it decided the answer
`Lang·hard` receives at 신촌 Fall, where **35 of 53 section-observations (66%)** were
mis-parsed — 3-credit courses written `월3,4,수3(수4)` read as 2 hours. That manufactured four
cheap 2-hour geometries, and `kdefer()` takes `min()` over geometries, so it selected one:

| K | geometry | observations, as shipped | observations, corrected |
|---:|---|---:|---:|
| **−4.725** | `월3,4` | 7 | **0 ⛔ artefact** |
| −2.487 | `화3,4` | 5 | **0 ⛔ artefact** |
| 0.209 | `월5,6` | 11 | **0 ⛔ artefact** |
| 5.688 | `화7,8` | 9 | **0 ⛔ artefact** |
| 16.615 | `월5,6/수6` | 4 | 4 real |

`min` over geometries that survive correct parsing = **16.615**, matching the reviewer's
independent full recompute. `kdefer('Lang')` was wrong by **+21.340**.

### The verdict inverts
```
SHIPPED    defer Lang  78.622   (2nd MR 64.379, margin 14.243)
CORRECTED  defer MR    64.379   (2nd Lang 57.282, margin  7.097)
```
New optimum: `UIC1561-01 · UIC1551-01 · UIC2151-06 · UIC1805-02 · YCK1998-03 · ECO1101-06 ·
YCA1006-01` — QRM1001 comes out, **Beginning Japanese/Chinese goes in**, and Language is
taken now rather than deferred.

⇒ **R253, R258, R262 are all withdrawn.** Every margin they quote was computed on fabricated
geometries. R262's "single load-bearing assumption is `min()`" is also withdrawn: once the
parser is fixed, defer-MR wins under min, median AND mean, so the aggregator stops deciding.
`min()` only ever looked load-bearing because four fake geometries manufactured a 21-point
left tail that only `min()` could reach.

### Fixed
Both `pools_past.parse` and `semester_sim.parse_time` now delegate to
`build_canonical.seg_blocks` (char-scan, parentheses transparent), with an inline fallback of
identical semantics. Verified: **0/10,159 mismatches** (was 1,047) and **0/775 신촌 sections**
in `raw_2026F` (was 194 — F2: `_INTL` came from canonical and was correct, `_SIN` came from
raw through the broken parser, so 국제 was right and 신촌 was wrong).

⚠️ **`k_real.json` and `b1_K.json` are STALE** — both were computed through the broken parser.
`k_real.py` must be re-run to completion before `fallback.py` or the renderers are trusted.
The 57.282 / 64.379 figures above use the shipped table restricted to surviving geometries,
which agrees with the reviewer's full recompute but is not itself a full recompute.

## R265. `prof_compare.py`'s two arms differ by a CONSTANT — its agreement proved nothing
Red-team F3. Every candidate timetable holds exactly 7 sections, so `PROF_UNRATED = 1.0` adds
exactly `7 × PROF_W = +70.000` to **every** row. The two arms are related by an additive
constant and **cannot reorder anything by construction**.

So "identical top timetable under both, therefore no unrated professor can change the answer"
was **vacuous** — it is a property of the arithmetic, not a measurement. Error class 4 again,
committed while documenting error class 4.

The real consequence: a uniform professor bonus can never matter. Only **differential**
ratings can. The correct instrument is leave-one-out per professor (the shape `fallback.py`
uses for sections), not a global default sweep.

## R266. K(Lang·hard, 2026) recomputed EXACTLY on the fixed parser — 16.615 confirmed
All 11 geometries, `node_cap = 4,000,000`, every value `exact` (no bound truncation):

| geometry | K | | geometry | K |
|---|---:|---|---|---:|
| `월3,4/수3,4` | **16.615** | | `화4/목5,6` | 18.685 |
| `월5,6/수6` | **16.615** | | `화5,6/목4` | 18.685 |
| `월7,8/수8` | **16.615** | | `화3,4/목3,4` | 21.186 |
| `화8,9/목7` | 24.919 | | `화7/목8,9` | 25.919 |
| `월5,6/수5,6` | 27.240 | | `화7,8/목7,8` | 30.728 |
| `화1,2/목1,2` | 32.935 | | | |

`min = 16.615`, against the shipped `−4.725`. Agrees with both the red-team's independent
recompute and the surviving-geometry estimate. **Every cheap geometry is gone; the corrected
minimum is 16.615 and nothing is below it.** Baseline `신촌|F|2026|5 = 64.684` is unchanged
from the shipped table even though the pool grew 147 → 175 signatures.

⇒ `total(Lang) = 73.897 − 16.615 = 57.282`, `total(MR) = 64.379`. **Defer MR, by 7.097.**

## R267. ⛔ `k_real.json['disp']` HAS NO PRODUCER — it cannot be regenerated
`disp` feeds `unit_cost()`, a live term in the objective (the displacement credit for an
elective that discharges a constrained ledger item). It is **read** by `fallback.py`,
`render_v3.py` and `render_v3_top50.py`, and **written by nothing in the repo**.
`k_real.py` never touches it — `grep -l "'disp'" *.py` returns only the three readers.

So the 12 `disp` entries were produced by a script that no longer exists, **through the broken
parser (R264)**, and there is no way to recompute them with the fix. Truncating `k_real.json`
destroyed them; they were restored from `_k_shipped_backup.json` and are therefore **stale by
construction**.

Measured exposure: 0 of the 8 course codes feeding `disp` hit the parse bug in any term, so
the *geometries* are clean — but the *pools* they were measured against were not, and 25.4%
of all sections carry a parenthesised block. **`unit_cost` is the last term still carrying
R264 contamination, and it is unfixable without rewriting its producer.**

## R268. The corrected pools OOM `b1_curve` at the shipped node cap
`k_real.py` hardcodes `node_cap = 30_000_000`. With the fixed parser the 신촌 pools grow
(147 → 175 signatures for 2026 alone; +17.7% measured by the red-team on `b1_curve.pool_for`),
and a full `k_real.py` run is now **Killed (OOM)** partway through 신촌.

`node_cap = 4_000_000` completes and still returns `exact=True` on every Lang·hard geometry,
so the cap was oversized rather than necessary. **`k_real.py` needs the cap parameterised
before the full table can be rebuilt.** Current `k_real.json` is therefore MIXED provenance:
`MR`/`WCiv` recomputed on the fixed parser, `LHP`/`SciRD`/`Lang·easy` and all non-2026 years
absent, `disp` stale (R267). Do not run `fallback.py` against it yet.

## R269. ⛔ R260 WAS ONLY HALF-FIXED — `TOPN = 3000` truncated below the argmax too
R260 removed `rows[:60]`. It left `RV.TOPN = 3000`, which is the identical defect one level
up: `run_branch` keeps the top-N by **`score`**, while the objective is
`score + Σunit_cost − K`. Any score-ranked prefix can miss the argmax.

Dormant until the R264/R267 rebuild widened the `disp` spread; then the argmax moved past
rank 3000. **The symptom was NEGATIVE loss costs** in the click order — `−10.46`, i.e. losing
a section appeared to *improve* the optimum, which is only possible if the base search never
found it. Measured convergence:

```
TOPN   3000 -> 57.838      12000 -> 68.299      40000 -> 68.299
```

**Fixed:** `FB_TOPN` and `RV_TOPN` default to 20000. All loss costs are now ≥ 0.

⚠️ **A negative loss cost is a soundness alarm, not a curiosity.** `cost(s) = best − best_without_s`
is non-negative by construction. Anything below zero means the base search is not returning
the maximum. Worth a permanent assertion.

## R270. `k_real.json` fully rebuilt on the fixed parser
`disp` regenerated by the new `build_disp()` (R267) — 12 entries, all `exact`. Values moved:
`ECO1101|신촌F|2026` 24.919 → **16.615**, `ME|국제S|2026` 23.018 → **20.948**,
`ME|신촌F|2026` 27.525 → **25.919**.

`k` rebuilt for all six cases; 2026 n=4 minima:

| MR | WCiv | LHP | SciRD | Lang·easy | Lang·hard |
|---:|---:|---:|---:|---:|---:|
| 0.000 | 24.643 | 16.615 | 28.294 | 23.018 | **16.615** |

`NODE_CAP` parameterised (R268); 4M OOMed on the n=5 신촌 loads, 1.2M completes with every
value still `exact=True`.

## R271. Pipeline fully rebuilt at TOPN = 20000 — verdict is defer MR, 68.299, 5/6 scenario cells
`TOPN` added to the cache stamp (it determines WHICH rows survive, so it is an input — R250's
rule). Without it the rebuild would have silently no-opped: every part file reported
`RECOMPUTING — stale: TOPN None->20000.0`.

| dir | rows (was, at TOPN 3000) | now |
|---|---:|---:|
| `_v3_parts_f0` | 9 000 | 27 021 |
| `_v3_parts_f1` | 18 000 | 98 188 |
| `_v3_parts_f2` | 18 000 | 113 278 |
| `_v3_parts_f99` | 18 000 | 113 278 |

Renderer candidate set **25 141 → 107 209** structurally distinct timetables; cards 110 → 94
(the union tightened because the true top-50s are now reachable).

```
BASE 68.299 · defer MR
  UIC1561-01-00 UIC1551-01-00 UIC2151-09-00 UIC1806-02-00
  ECO1101-06-00 STA2102-05-00 YCA1006-01-00

CLICK ORDER   UIC1561-01 34.39 · STA2102-05 6.64 · ECO1101-06 2.51
              YCA1006-01 1.18 · UIC1551-01 / UIC2151-09 / UIC1806-02 0.00
```

`DECISION_v3.html`: **MR wins 5 of 6 scenario cells** (was Lang 6/6 before R264). All loss
costs ≥ 0 — the R269 alarm is clear. `test_v3.py` 21 hold / 3 broken, the same three
documented failures.

⚠️ Still carried: `Lang·easy`/`Lang·hard` n=5 K values are absent (OOM at every cap tried);
only n=4 is populated, which is what `fallback` reads. The 1 of 6 scenario cells that does not
pick MR should be identified before 8/25.

---

## R272. ⭐ ONE RULE FOR EVERY BRANCH — the kdefer asymmetry is removed
Iden, 2026-08-16: *"I don't understand why there is an assymetry at all (except things I
explicitly mentioned, like language difficulty)."* He is right; nobody chose it. `kdefer` had
two code paths — `MR` pinned to a named geometry and enumerated as a scenario axis, everything
else collapsed by `min()`. The split was an accident of authoring order.

It also ran one direction: `min()` rewards whichever item has the most observed geometries
(`min` over 11 draws is an extreme; over 1 it is the value). Geometry counts: `WCiv` 1,
`LHP` 1, `MR` 2, `SciRD` 2, `Lang·easy` 3, `Lang·hard` **11**.

### The rule
You choose your future slot but may not get your first pick. Cheapest geometry first:

```
P(geometry obtainable) = 1 − Π (1 − p_course)     over the courses offering that shape
E[K] = Σ K_g · P(g) · Π (1 − P(cheaper g'))  +  P(none) · worst
```

Applied identically to all five deferrable items. **min-vs-median was a false choice** — both
guessed at the same unmeasured quantity, and it is measurable:

* `p = 1` reduces the estimator **exactly** to `min()` (verified: MR 0.00, SciRD 28.29,
  Lang 16.61 reproduce the old values bit-for-bit)
* `p → 0` reduces to the worst geometry
* measured `p` sits between, per item, on evidence

`t` walks the measured bracket: 0 = must MATCH the top bidder, 1 = need only beat the weakest.
No-history courses contribute the widest bracket (R259).

### Result — the verdict is stable across the ENTIRE bracket
```
   t     arm                    -      MR    WCiv     LHP   SciRD    Lang
0.00  pessimistic            0.00    3.83   24.64   16.61   28.45   17.15
0.50  midpoint               0.00    1.92   24.64   16.61   28.37   16.62
1.00  optimistic = min()     0.00    0.00   24.64   16.61   28.29   16.61

t=0.00  defer MR  64.464  (2nd Lang 46.65, margin 17.814)
t=0.50  defer MR  66.382  (2nd Lang 47.18, margin 19.203)
t=1.00  defer MR  68.299  (2nd Lang 47.18, margin 21.115)
```
**Defer MR at every point, margin 17.8–21.1.** The aggregator question is closed: it no longer
matters which end you believe.

### ⚠️ SCOPE — the purpose check that bounded this work
Measured before building, across the top 50: `score` (week+year+chapel+difficulty) spread
**5.354**, `Σunit_cost` spread **1.666**, `K` spread **0.000**. K is *constant within a branch*,
so it decides only WHICH requirement is deferred — never the ranking Iden actually browses,
which he chooses from himself (R: "give me the best 50 structurally, I'll pick").

PURPOSE_CHECK §B's warning applies directly: the model can drift into optimising a speculative
future term while the present-week comfort he named first contributes a fifth of the spread.
**This estimator must stay one number per branch.** Do not grow it into a registration
forecaster. `K_T` (default 0.5) selects the bracket point; `_KCACHE` memoises per (branch,
year, t) — uncached it was called once per row over 113,278 rows and never finished.

---

## R273. ⛔⛔ `MAX_DEFER = 1` IS A LIVE BIAS — deferring TWO beats deferring one by 9.52
Iden, 2026-08-16, on being told the model chooses "which of the five requirements gets
postponed": *"you just created two biases: 'something has to be postponed', and 'no more than
one can be postponed'."*

**First claim — not a bias.** `'-'` (defer nothing) IS a searched branch. It scores 33.333 and
loses, but it is on the table and always was.

**Second claim — correct, and the proof that licensed it is stale.**
R121 proved `MAX_DEFER = 1` sufficient by branch-and-bound against incumbent 32.51 (re-verified
at 29.34), with ceiling `week_value ≤ 63.1` and a cost table where every pair ran −25 to −34.
**That proof predates `unit_cost` entirely.** Deferring two requirements frees a *third*
elective slot, and every elective now carries a displacement credit worth up to ~27 points that
never appears in R121's ceiling.

Searched directly (`run_branch` already accepts `'A+B'`; only `BRANCHES` excluded them):

| pair | score | ΣK | Σunit_cost | TOTAL |
|---|---:|---:|---:|---:|
| **MR+Lang** | 54.209 | 18.537 | 40.230 | **75.902 ⬅** |
| MR+LHP | 44.194 | 18.532 | 40.230 | 65.892 |
| LHP+Lang | 54.209 | 33.235 | 40.230 | 61.204 |
| MR+WCiv | 44.894 | 26.560 | 40.230 | 58.564 |
| MR+SciRD | 46.069 | 30.289 | 40.230 | 56.009 |
| WCiv+Lang | 27.894 | 41.263 | 61.178 | 47.809 |
| …6 more, all lower | | | | |

**Single-deferral optimum 66.382 → two-deferral optimum 75.902, a gain of 9.520.**

```
defer QRM1001 AND Language        K = 1.92 + 16.62 = 18.54
  UIC1561-01  WESTERN CIVILIZATION            월7,8/수7
  ASP2033-01  NORTH KOREA: HISTORY, CULTURE   화2,3,4
  UIC2151-14  RESEARCH DESIGN AND QUANT       화7,8,9
  YCK1998-03  명예특임교수강의시리즈                     월7,8/수8
  ECO1101-06  MATHEMATICS FOR ECONOMICS I     월9,10/수10
  STA2102-05  선형대수                            월5,6/수6
  ledger items filled: FREE · ECO1101 · ME
```

⚠️ **The whole branch set must be widened**: `BRANCHES = ['-','MR','WCiv','LHP','SciRD','Lang']`
covers ndef ∈ {0,1} only. `research_v3.run_branch` already parses `'A+B'`; nothing but the
list stopped it. 3-deferral must also be re-checked — R121 eliminated it analytically using
the same stale ceiling.

**The general lesson.** R121 was a real proof, correctly done, and it decayed silently when the
objective gained a term. A proof is only valid against the objective it was run on, and nothing
in the project re-checks proofs when the objective changes. R185 said exactly this about
retired questions; it applies to proofs too.

## R274. PURPOSE_CHECK §B was misapplied (mine)
I quoted *"the model already achieved that at rank ~50 and is now optimising something else"*
as a caution about `K`. Iden: *"this is NOT the purpose that is related with K, and an outdated
quote from me anyway (before I knew about K)."* Correct — §B is about the trip-home/commute
terms saturating, which is a **current-week** concern. It is not evidence about `K`, which
serves long-term degree planning. The measured spreads in R272 stand on their own; the quote
should not have been attached to them.

---

## R275. ⛔⛔ `ΣK` ASSUMES DEFERRALS ARE INDEPENDENT — measured superadditivity +14.675
Iden, 2026-08-16, on R273's two-deferral result: *"That's true, unless deferring makes the next
semester uncomfortable, which would be basically the same thing, just sequencing."*

Correct, and the model does not price it. `fallback.total` charges `kdefer(a) + kdefer(b)` for
a two-deferral branch. Each `K` is measured by pinning **one** geometry into a semester of
otherwise free-choice fillers. Two pinned courses constrain a week far more than twice one.

Measured directly (`b1_curve.best_week([g_a, g_b], 4, pool)` against the 6-course baseline),
receiving semester 국제S 2026, pool 145 signatures:

```
baseline 5 free = 69.017     6 free = 51.392
K(QRM1001) alone         0.000
K(Language) alone       23.018
sum, as the model uses  23.018
JOINT, both pinned      37.693
superadditivity        +14.675
```

### What it does to R273
R273's `MR+Lang` gain of **+9.520** used `ΣK = 1.92 + 16.62 = 18.54`, which silently assumes
the two deferred courses land in **different future semesters**. If they land in the same one:

```
score + Σunit_cost                 94.439
  − ΣK (independent, as modelled)  −18.537  ->  75.902   beats MR alone (66.382)
  − joint K (co-located)           −33.212  ->  61.227   LOSES to MR alone
```

⇒ **The two-deferral result is conditional on being able to spread the deferrals across
different semesters, and nothing in the model checks that.** The degree plan
(`plan_model.ITEMS`, 38 units over 7 remaining semesters) determines whether they can be
spread; `Φ` feasibility was only ever checked per-branch, never for placement.

### The general form
`K` is a **marginal** cost measured against an unconstrained filler semester. Summing
marginals is valid only when the things summed do not interact. Deferred requirements interact
by construction — they compete for the same weekly grid. Any multi-deferral branch needs a
**joint** K, not a sum. This also means R273's pair table is an upper bound on every pair, not
a ranking: pairs whose members must co-locate are overstated by up to ~15.

⚠️ Do not widen `BRANCHES` to pairs until joint K is implemented. R273 stands as a proof that
`MAX_DEFER = 1` is unjustified; it does **not** stand as a recommendation to defer two.

## R276. Renderers unified onto the single estimator; a THIRD truncation found and fixed
Finalisation pass, 2026-08-16. Both renderers were still computing K their own way — the
same three-path asymmetry `fallback.kdefer` had before R272 (0 for `'-'`, pinned geometry for
`MR`, bare `min()` for the rest). They now call `fallback.kdefer` directly, so the
recommendation and the browsable ranking can no longer disagree about what K is.

**`render_v3.py` carried the R260/R269 defect a third time:** `rows(f, b)[:400]` — a
score-ranked prefix, then maximised on `score + Σunit_cost − K`. Fixed to scan every row.
Three independent instances of one mistake (`rows[:60]`, `TOPN = 3000`, `rows[:400]`); the
pattern is *any* prefix taken by one key and then optimised by another.

**The scenario grid collapsed from 6 cells to 3.** Geometry uncertainty now lives inside K as
an expectation over which slot is obtained, so it is no longer an axis — and it was only ever
an axis for `MR` anyway (R272). What remains is the three catalogue years, the one thing the
model genuinely cannot know.

```
DECISION_v3.html   winner MR in 3/3 cells      (was Lang 6/6 before R264)
TOP50_v3.html      107,209 candidates -> 88 cards, union of top 50 over 3 scenarios
```

## R277. Two-deferral: UNRESOLVED, not ruled out
Iden asked whether the pair result is "basically out". Recorded precisely because the
distinction matters: the `MR+Lang` gain is **+9.520** and the measured co-location penalty is
**+14.675** (R275). The penalty can erase the gain, but only if the two deferred courses land
in the **same** future semester. The model cannot currently determine that.

⇒ **Not adopted, and not eliminated.** `MAX_DEFER = 1` remains in force as the operating
choice, *not* as a proven optimum — R121's proof is stale (R273) and has not been replaced.
Closing this needs joint K (R275) plus a placement check against `plan_model.ITEMS`.

## R278. Interchangeable courses were rendering as separate cards instead of equal swaps
Iden, 2026-08-16: *"why do I see multiple timetables with the same geometry… originally it
showed 'Beginning Chinese' and then 'different course: Beginning Japanese'… but only if the
courses have the same score & same geometry."*

The card dedup key was `(branch, COURSE CODES, occupied cells)`. Two timetables with the
identical week shape and identical score but interchangeable courses have different codes, so
they became **separate cards** — and the equal-swap scan then ran inside each, so each listed
the other as a swap. The collapsing the swap list exists to perform was undone one step earlier.

Measured before the fix: 88 cards held only 55 distinct (shape, score) groups. One group had
**five** cards; another had three differing solely by `UIC1805-01` Beginning Chinese vs
`UIC1806-01` Beginning Japanese — exactly the case Iden described.

**Fixed:** key on the scenario-invariant identity — `(branch, cells, round(score,3),
sorted(items))`. Two rows matching on all four are identical under every scenario, so one card
represents them and the equal-swap list names the alternatives.

```
candidates 107,209 -> 62,216 distinct
cards 88 -> 84, and all 84 are now distinct (shape, score) combinations  [verified: 0 duplicates]
```

## R279. ⚠️ Every card in the top 50 defers the same requirement
Not truncation — measured best per branch over all candidates:
`MR 66.382 · Lang 47.179 · LHP 35.171 · WCiv 33.906 · '-' 31.263 · SciRD 26.714`.
MR beats the runner-up by 19.2, so all three scenario top-50s are entirely MR.

This works against the stated use — *"give me the best 50 schedules structurally and I'll
personally choose"* — because 84 cards are rearrangements of one deferral decision. A card set
built as **best N per branch** rather than global top 50 would surface the best defer-Language
week (47.179) and the best defer-nothing week (31.263) as browsable structures with their cost
shown. Not implemented; recorded as the open display question.

## R280. The R218 zero-fixed-hours guard changes REALITY to match the code, not the reverse
Iden, 2026-08-16: *"why are we treating like instead of changing the code to match the reality,
we are changing the reality to match the code… Besides, they are pretty good, for not having a
fixed slot. It's fine if they get some many plus points."*

He is right, and two things were conflated in my answer — they are independent:

1. **`YCG1804-01` / `YCG1853-01` are barred by 학년별정원** — a 1학년 quota of 0 with a scheme
   in force (R247). That is an external fact about registration and it is the real reason they
   cannot be taken.
2. **The `fm == 0` guard would drop them anyway** — an internal workaround, because workload is
   unpriced (R218) so a no-fixed-hours section looks like a free slot.

(2) is not a correctness fix. **A section with no fixed hours genuinely IS more flexible, and
genuinely SHOULD score well for it.** Deleting it because the model cannot price the effort is
treating a modelling gap as though the world were wrong. The correct fix is to price workload
and let such sections compete honestly — not to remove them and call the result clean.

Status: **inert today.** These are the only two `fm == 0` sections in the Fall 2026 pool and
both are barred independently, so the guard removes nothing that was available. It becomes
live — and wrong — the moment a fully-recorded section exists that a 1학년 may take.

Do not cite R218's guard as evidence that recorded courses are overvalued. 동영상 sections are
still winning on merit: three of the six recommended courses carry recorded segments
(`ECO1101-06`, `STA2102-05`, `UIC1561-01`), and that is the flexibility being correctly
rewarded, not an exploit.

## R281. ⭐ Deferring does not escape the professor — carry term added, measured not assumed
`prof.bonus()` is charged in the semester a course is TAKEN. `kdefer` carried no professor
term, so a deferral branch dodged the penalty **permanently**. Measured before the fix, rating
`UIC1561`'s sole professor at −1:

```
MR −10.000 · Lang −10.000 · LHP −10.000 · '-' −10.000 · SciRD −10.000 · WCiv +0.000
```

Every branch that takes Western Civ lost 10; the branch that defers it lost nothing. A bad
professor bought exactly `PROF_W` points toward postponing a course whose single section has
**the same professor every year**.

This is the bug `difficulty.p_hard_if_deferred()` already fixes for the language tier — it
charges `P(hard | deferred) × D_LANG` **on the deferral branch**. The professor axis had no
equivalent.

### The fix
```
carry(requirement) = P(same professor when taken) × E[bonus of the section obtained]
kdefer(b) −= carry(b)
```

`P(same professor)` is **measured** from consecutive same-season terms in `past_terms.json`,
asking whether a course retained at least one professor:

| overall | MR | WCiv | LHP | SciRD | Lang |
|---|---|---|---|---|---|
| **83.7%** (2098/2508) | 2/4 | **4/4** | 11/12 | 4/4 | 8/8 |

`PERSIST_DEFAULT = 0.837` for requirements never observed twice — the measured global rate,
not a guess.

### Verified
With `UIC1561` persistence = 1.0 and carry = −10.000, rating that professor −1 now moves
**every branch by exactly −10.000**. The deferral ranking is unchanged and the WCiv-to-MR gap
stays at 32.48.

That is the correct behaviour and worth stating plainly: **if a professor never changes, when
you take the course is irrelevant to who teaches it, so the rating must not move the deferral
decision at all — it should only make the whole degree slightly worse.** It now does exactly
that. Where persistence is genuinely below 1 (MR at 0.5), deferring earns a partial, honest
credit for the chance of a different professor.

## R282. The "identical hours" check was in the comment, not the code
The equal-swap scan documented type (a) as *"same course code, different 분반, **identical
hours** → a professor choice, and a fallback if this 분반 fills on 8/25."* The implementation
tested equality by **rescoring alone**:
```python
v = _score_of(cand, items)
if v is None or abs(v - base) > 1e-6: continue
(same if s2['code'] == byc[c]['code'] else others).append(s2)
```
No hours comparison. So `UIC1551-04` (화8,9/목7) and `UIC1551-01` (화7/목8,9) — mirror-image
weeks worth the same score — were labelled a drop-in replacement. Clicking that "fallback" on
8/25 gives a **different timetable**, not the same one with another professor.
Measured: **23 of 61** same-course swaps had different hours.

## R283. ⛔ ONE IDENTITY, ONE PLACE — the swap list and the dedup contradicted each other
Iden: *"Why isn't it consistent? #1 shows 'different hours' as a swappable object. But your
explanation seems to suggest that if cells genuinely differ, the dedup correctly keeps both."*

Exactly right, and R282's relabel did not fix it. Two rules were deciding the same question
in opposite directions:

* **dedup (R278):** different `(cells, score, items)` ⇒ a separate card
* **swap list:** equal score ⇒ an alternative *inside* a card

Verified on the live page — the `UIC1551-04 → UIC1551-01` swap offered on #1 yields cells
**identical to #2**:
```
#1                        … 화8 화9 … 목7
#1 with the offered swap  … 화7 … 목8 목9      ← identical to
#2                        … 화7 … 목8 목9
```
So the same outcome appeared twice: as card #2, and as a hidden alternative on card #1.

⚠️ **R283's fix was rejected by Iden and is SUPERSEDED by R284** — see below. Cross-referencing
kept a category that should not exist. Recorded only because the diagnosis was right.
The (withdrawn) intermediate state was:
```
other 분반, same hours              38   true drop-ins
also reachable from here           22   "swapping a 분반 gives you #2, already listed above"
equal-scoring, DIFFERENT hours      1   genuinely not on the page
different course, identical score  37   unchanged
```
22 of the 23 R282 cases were duplicates of cards already shown. Only one was new information.

## R284. ⭐ THE SWAP RULE, stated by Iden — same cells or it is not a swap
> *"instead of a weird, unintuitive 'also reachable from here' that is pretending to be a fix,
> can we actually fix a rule? … it has to have the same cells to be considered swappable.
> Otherwise, it shows up as a different timetable. The other usual rules all still apply for
> scores, items."*

This supersedes both R282 (relabel) and R283 (cross-reference). Both preserved a category that
should never have existed; only this deletes it.

**A swap is a claim that you can substitute the section and still be looking at THE SAME
timetable.** That is true only if the week is unchanged. If the cells move it is a different
timetable, and the dedup (R278) already governs what happens to those — it becomes its own
card, or it misses the top 50. Either way it is not that card's business.

```python
if not (s2['tm'] == byc[c]['tm'] and s2['pm'] == byc[c]['pm'] and s2['fm'] == byc[c]['fm']):
    continue
(same if s2['code'] == byc[c]['code'] else others).append(s2)
```

Every other condition is untouched: identical rescored total, same ledger item for electives,
same difficulty tier for language, no time conflict, verified by substitution not by signature
(R197).

Result — the two categories that remain are both genuine drop-ins:
```
other 분반, same hours              38
different course, identical score  37
also reachable from here            0   (category deleted)
equal-scoring, DIFFERENT hours      0   (category deleted)
```

**The lesson, and it is mine to learn.** Told the swap list and the dedup disagreed, I first
relabelled the symptom (R282), then built a cross-reference so the two wrong answers could
coexist politely (R283). Both were elaborations on a rule that was simply wrong. The fix was
to state the rule correctly and delete what it excluded. **When two rules contradict, do not
build a bridge between them — find which one is wrong.**

---

# ⛔⛔⛔ R285. THE RELOCATION GAP — the model prices AVOIDANCE where only RELOCATION is possible

Iden, 2026-08-16, and this is the largest open defect in the project:

> *"it's not 'nothing to act for'. This is the biggest, largest, most difficult gap that I've
> found. For all courses, we don't know if we're applying a penalty to this semester that will
> just be pushed over to the next one. For required components especially, this is important."*

## The error, stated generally
Every ledger item **must** be taken eventually — that is what a ledger is. So for a required
course, a schedule penalty is not avoidable, only **relocatable**. The objective nevertheless
scores this semester's discomfort and treats a penalty pushed into the future as *removed*.
`K` was built to catch exactly this and does not, because it measures the damage of adding one
course to a **free-choice filler semester**, not to the actual remaining obligation set.

This is not specific to 금. It applies to **every** term in `fast_score` — 9am starts, occupied
lunches, late finishes, holes — and to `difficulty` as well. Whenever the model "saves" points
by deferring a required item, the correct question is *how many semesters end up carrying that
penalty in total*, and the model never asks it.

## The 금 case, measured
```
minimum 금-broken semesters over the whole remaining degree: 1
items that can NEVER avoid 금:  QRM3003   (3 of 3 observed sections run 금)
every other item has 금-free options:
  Chapel 25/25 · Seminar 16/16 · WCiv 6/6 · ECO2101 66/68 · ECO1101 58/68
  ME 34/36 · Lang 230/239 · LHP 59/71 · SciRD 55/68 · ECO2102 46/62 · MR5 3/6 · QRM1001 2/6
```
⇒ **At least one future semester has 금 broken no matter what.** The Fall-2026 금 bonus — worth
**32–43 points per hour**, the single largest term in the current ranking — is priced as if 금
freedom were achievable in every semester forever. It is not.

## And the marginal cost inverts once it is broken
```
clean semester (5 free-choice courses), baseline 69.017
   K(a 금 course)       +8.137
   K(a non-금 course)   +4.179

semester with QRM3003 pinned (금 unavoidable), best 38.111
   + another 금 course   −2.321   ← NEGATIVE: cheaper than not taking it
   + a non-금 course    +22.307
```
A second 금 course in an already-broken semester is **better than free**: it uses hours on a day
you are already commuting to, instead of committing a new day.

⇒ The correct plan is **exactly one 금-broken semester that absorbs every 금-ish obligation**
(`QRM3003`, and preferably `MR5`, `QRM1001`, `ECO2102` — the items with the fewest 금-free
options). Nothing in the model can currently express this, because `K` is per-course and
per-semester-in-isolation.

## Relationship to R275
Same root cause, opposite sign. R275 measured deferrals as **super**additive (+14.675) when two
pinned courses compete for a clean grid. This measures them as **sub**additive (−2.321) when
they share an already-broken day. `ΣK` is wrong in both directions because it assumes
independence, and the interaction can be either sign depending on whether the courses collide
or share a sacrifice.

## What a correct model would do
Optimise over the **partition** of the 38 remaining units across 7 semesters, scoring
`Σ discomfort(semester)`, rather than optimising semester 1 and subtracting a per-course proxy.
Choosing this Fall's six courses is choosing the first block of that partition; the rest is
constrained by what is left. Under that formulation, "avoid 금 now" is only a saving if it does
not force an **extra** 금-broken semester later.

⚠️ **This does not invalidate the 8/25 answer** — `QRM3003` is a year-3 item and no candidate
this Fall contains it, so nothing in the current top 50 is affected. It invalidates the *reason*
the model gives for its answer, and it is the first thing to fix after registration.

## R286. R285 measured — K collapses when the receiving semester is REALISTIC, and the margin nearly vanishes
First correction built (`relocation.py`). Only the filler pool changes; same `b1_curve` engine,
same exactness reporting, so the delta isolates the defect.

### The remaining ledger
```
after Fall 2026: Chapel x2 · Seminar x2 · QRM1001 · ECO2102 · ECO2101 · MR5 · QRM3003 · ME x5
= 14 units over 6 semesters = 2.33 obligations per semester
```
So neither extreme is right. `k_real` fills the receiving semester with **5 free-choice**
courses (dodges every penalty); an all-obligation pool would be **5 forced** (dodges none).
The honest measurement pins **2 obligations** and fills the other 3 freely.

### K under the three assumptions
| branch | all-free (shipped) | 2 obligations pinned | all-obligation |
|---|---:|---:|---:|
| MR | 0.000 | **2.000** | 2.500 |
| WCiv | 24.643 | **2.400** | −19.633 |
| LHP | 16.615 | **0.000** | 14.157 |
| SciRD | 28.294 | **4.375** | 7.025 |
| Lang | 16.615 | **0.000** | 0.000 |

**K spread across branches: 24.643 → 4.375.** Deferring almost anything is nearly free once
the receiving semester already carries real obligations. The large K values were an artefact
of measuring against a pristine semester that will never exist.

### Effect on the verdict
```
             pre_K   K shipped    total  |  K realistic    total
  -         31.263       0.000   31.263  |       0.000   31.263
  LHP       51.786      15.698   36.088  |       0.000   51.786
  Lang      63.799      16.620   47.179  |       0.000   63.799
  MR        68.299       1.917   66.382  |       2.000   66.299
  SciRD     55.086      21.372   33.714  |       4.375   50.711
  WCiv      58.549      24.643   33.906  |       2.400   56.149

SHIPPED    : defer MR 66.382   (2nd Lang 47.18, margin 19.203)
RELOCATION : defer MR 66.299   (2nd Lang 63.80, margin  2.500)
```

⇒ **The verdict SURVIVES — defer QRM1001 — but the margin falls from 19.203 to 2.500.**
Everything that made the choice look decisive was K, and K was measuring against a fiction.
What remains is a genuine but thin 2.5-point preference driven by `pre_K` (this semester's
week quality plus elective credit), which is the part of the model with real elicitation
behind it.

⚠️ **Still not the full model.** This corrects the *pool* K is measured against; it does not
optimise the partition of all 14 remaining units across 6 semesters, and it still treats
deferrals as independent (R275/R285). The 2-obligation pin is an average, not a plan — the
real semester might hold 1 or 4. Next step is the partition, not another pool tweak.
