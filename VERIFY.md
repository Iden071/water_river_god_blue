# VERIFICATION LOG — Fall 2026 수강신청
**Started:** 2026-08-05 · **Deadline:** 2026-08-25 09:00 KST (신입생 first-come)
**2026-08-06 — PLAN A CLOSED.** Every data- and rules-layer item is resolved or formally
unobtainable. Remaining entries are ⏳ parked in `PLANS.md` by Iden's decision, not open work.
**Purpose:** every assumption behind the timetable numbers, tracked to closure.
Companion to `RULES.md` (verified rules) — this file tracks what is NOT yet verified.

**Protocol:** nothing moves to ✅ without stated evidence. Decisions get logged the same
turn they are made (Iden's standing instruction, 2026-08-05). Rebuild rankings only
after Layer 1 is closed.

---

## STATUS BOARD

| # | Item | Layer | Status |
|---|---|---|---|
| 1 | Reconcile 661 / 709 / 821 section counts | data | ✅ CLOSED |
| 2 | Rebuild pools from xlsx, not all_kj.json | data | ✅ CLOSED (build_canonical.py) |
| 3 | 동영상콘텐츠 — does it block its listed hour? | data | ✅ CLOSED (R52) |
| 4 | Parenthesized times "(월9)수1,2,3" — real meetings? | data | ✅ CLOSED (R54) |
| 5 | 강의실 ↔ 강의시간 slash alignment holds generally? | data | ✅ **CLOSED (R115)** — 712/712 segment counts match; 128/128 paren patterns mirror; 0 contradictory segments |
| 6 | Language pool 83 vs handoff's 93 | data | ✅ CLOSED — 83 correct (R56) |
| 17 | Elicit cyclic free-day params A (run) and B (isolated day) | pref | ✅ **CLOSED (R114)** — both live and asserted: ISOLATED/DAY_CONTIG = 25% [E]; RUN_EXP = 1.6 (direction [E], magnitude [P]) |
| 7 | UIC1805/1806 seat counts | rules | ✅ **CLOSED (R118)** — UIC1805 정원 18, 배율 1.17×, avg bid 16 |
| 8 | Chapel B eligibility + which types count | rules | ✅ CLOSED (R58) — pool 7→2 |
| 9 | SciLit list (R41) current & exhaustive? | rules | ✅ **CLOSED (R113)** — all 55 SciLit+RDQM 국제 sections audited; only **UIC1751** is usable |
| 19 | Rebuild everything at **6 courses / 18cr** | data | ✅ CLOSED (R62) |
| 21 | Choose 6th course | pref | ✅ CLOSED — superseded: both open slots now compete freely, no pre-selection |
| 30 | Course count: 6 vs 7 | pref | ✅ **CLOSED (D-21)** — **6 courses / 18cr BY CHOICE.** Cap is 22, so 7 courses (21cr) is legal; Iden declined it. The 7-course branch is **deliberately excluded**, not overlooked |
| 22 | What counts as QRM ME? | rules | ✅ **RE-CLOSED (R102/R105)** — the earlier closure was WRONG. `subsrtDivNm` is per-(section × 개설전공), so the old reading used 경제학's label. QRM's own listing (`qcat`) gives **MR 5 · ME 18**; **ECO1103/1104 ARE ME**. STA1002 is not a QRM course at all. |
| 22b | Do sections QRM did *not* list still count (ECO1104-07)? | rules | ⏳ **PARKED** — `PLANS.md` §D. Worth 1 grid variant |
| 29 | ECO1101 = QRM MR? | rules | ✅ **CLOSED (R99)** — the MB courses tagged 전필 by 상경대학 are exactly ECO1101/2101/2102, i.e. QRM's three Economics MR courses. +10 bonus justified |
| 23 | Prerequisite chain: does ECO2102/2101 require 원론 first? | rules | 🟡 no explicit prereq found, but 원론 are **Econ 이중전공 필수** in their own right (R64) |
| 26 | Econ 이중전공 requirement table | rules | ✅ CLOSED (R64) — closes HANDOFF open Q3 |
| 27 | Does 미분적분학 (Econ 필수) = MAT1001/1002? | rules | ⏳ **PARKED** — moot while R103 has the double-major layer scrapped. `PLANS.md` §C |
| 20 | 정원 (capacity) | rules | ✅ **REOPENED THEN CLOSED (R118)** — IS obtainable via findMlgAppcsResltList.do: 정원·신청인원·전공자정원·학년별정원. 142 rows in `mileage_history.json` |
| 24 | RC자기주도활동(2) — need to register? | rules | ✅ CLOSED — **auto-enrolled**, no action (수강편람 VI-3-바) |
| 25 | Build requirement coverage audit (top-down) | data | ✅ CLOSED — `REQUIREMENTS_AUDIT.md` |
| 10 | Credit cap | rules | ✅ CLOSED (R86) — **19** for a HASS freshman (+3 w/ GPA 3.8 ⇒ 22). R59's "18" was my error; handoff was right |
| 28 | UIC Seminar window Sem 4–7 — applies to HASS? | rules | ✅ **CLOSED (R131)** — window sits in §11.1 *UD freshmen*; Iden's §11.3 *HASS freshmen* has none. Iden confirms. ⚠️ **but the pools still discard 4 eligible sections** — see R131 |
| 18 | Iden's Spring 2026 GPA ≥3.75? (→ cap 22) | rules | ✅ **CLOSED (D-20)** — YES. Cap = **19 + 3 = 22** |
| 11 | Fit new weight answers, then re-test fit | pref | ✅ **RE-CLOSED (R129)** — was silently **15/16** after R128; now **19/19** with 4 new R129 cases. `ranking_weights.md` regenerated (it had been stale since R119/R128) |
| 12 | Presence semantics beyond free days? | pref | ⚠️ **REOPENED THEN RE-CLOSED (R129)** — D-10's premise ("commute to campus") was wrong; Iden dorms at 국제. TRIP uses PRESENCE, REST uses TIME |
| 13 | Slot-deferral values, chapel bonus | pref | ✅ **CLOSED (R117)** — measured + fitted to Iden's anchors; `defer_costs.json` |
| 13b | Professor ratings | pref | ⏳ PARKED — `PLANS.md` §C, post-hoc on shortlist |
| 14 | Is Iden 외국인 유학생? (30% async cap) | rules | ✅ CLOSED — no (D-12) |
| 16 | SciLit pool is 93% sequels — reconsider vs RDQM | rules | ✅ **CLOSED (R113)** — nothing to reconsider; SciRD is **100% RDQM across the top-50** |
| 31 | Science (2) sequels unfiltered in SciRD pool | data | ✅ CLOSED (R112) |
| 32 | Sequels reachable as free ELECTIVES | data | ✅ **CLOSED (R122)** — MAT1002 had reached rank 1; OPEN 451→362, optimum 32.51→29.34 |
| 33 | Full 유의사항 audit (all 88 distinct texts) | rules | ✅ **CLOSED (R123)** — 84 ineligible sections removed, incl. 59 saying 언더우드국제대학 소속 학생 수강 불가 |
| 15 | Exam-time clashes for 동영상콘텐츠 overlaps | rules | ⏳ **PARKED** — `PLANS.md` §D, shortlist stage |

---

## LAYER 1 — DATA

### ✅ 1. Section-count reconciliation — CLOSED 2026-08-05
Exact arithmetic, from `강의목록_2026F.xlsx`:

| Quantity | Count |
|---|---|
| 국제 rows | 827 |
| − duplicate rows (same 학정번호 listed under 2 분류) | −112 |
| = distinct 국제 학정번호 | **715** |
| − sections with empty 강의시간 | −6 |
| = distinct 국제 sections with a time | **709** |
| `all_kj.json` | 661 |
| **missing from all_kj.json** | **48** |

- **Duplicates explained:** e.g. YCA1102-13-00 appears under both `교양기초 기독교의이해`
  and `UIC 공통교과과정(국제)` — same section, two catalogue classifications. 72 학정번호
  are affected, contributing 112 extra rows. Not real extra sections.
- **The 6 timeless sections:** UIC1101 ×5 (FWIS) + UIC1901 ×1 (World Philosophy) —
  both already ✅ completed by Iden (R27), so irrelevant to Fall 2026 planning.
- **The 48 missing:** 41 PE (체육과건강) · **2 SciLit-relevant (MAT1002-07-00, -08-00)** ·
  5 UIC/AI-college ELEC sections.
- **Conclusion:** `all_kj.json` is not trustworthy as a universe. Deduplicated xlsx
  (709 sections) is the correct one. R51 residual is now fully accounted for.

### ✅ 2. Canonical rebuild — DONE 2026-08-05
Script: **`build_canonical.py`** → **`canonical_2026F.json`** (709 국제 sections, dual
TIME/PRESENCE masks per R52+D-10, parens counted per R54). Reproducible; re-run anytime.
**Validation: zero warnings** — time-segment ↔ room-segment counts align in all 709,
and 과목종별 agrees with the room markers 709/709 (closes item 5 at section level).
Segment kinds: inperson 783 · video_free 79 · video_block 37 · live_online 2.

**Canonical pool sizes:** MR 1 · WCiv 3 · LHP 15 · RDQM 13 · SciLit 42 · Chapel 7 ·
CN 2 · JP 2 · ME 9.

**Committed family (D-3/D-4, Chinese) recount: 2,326 timetables** (was ~1,331 under the
wrong semantics — **+75%**). By path: SciLit 1,672 · RDQM 654.
Cause of the increase: YCE1253's 목4 is 동영상콘텐츠, so it no longer collides with
QRM1001 목4,5,6; likewise the MAT1001/MAT1002 free halves.

**Free-day distribution (presence-based):**
| Free days | Count |
|---|---|
| **월수금 (2-day campus week)** | **12** |
| 월금 | 102 |
| 수금 | 12 |
| 금 | 1,282 |
| 월 | 242 |
| none | 676 |

**NEW: 12 timetables need campus only on 화 + 목.** Two mechanisms produce them —
(a) YCE1253 WestCiv with its video Thursday, or (b) UIC1561 WestCiv fully online.
All 12 use a SciLit science course (MAT1001-02 or MAT1002-06), i.e. they interact with
R55 (sequel/prereq caution) — Iden's call, not a filter.

### ⬜ 3–5. Time semantics — ONE syllabus check settles 3 and 4
**Discovered 2026-08-05: the xlsx has a `과목종별` (delivery mode) column** — a
categorical, authoritative field, better than regex on 강의실. 국제 values:

| 과목종별 | count | meaning |
|---|---|---|
| 대면강의 | 688 | fully in-person |
| 블랜디드(동영상) | 126 | mixed: some blocks in-person, some on-demand video |
| 비대면(동영상) | 5 | fully remote, on-demand |
| 비대면(실시간) | 1 | fully remote, synchronous |
| 비대면(실시간+동영상) | 1 | fully remote, mixed sync/async |
| (empty) | 6 | the timeless UIC1101/UIC1901 rows |

**Cross-check result: 과목종별 ≠ 대면강의 ⟺ 강의실 contains an online marker — 133/133,
zero exceptions.** The two sources agree perfectly, which *validates item 5's alignment
assumption at the section level* (still unproven at the per-block level — that is what
the slash-alignment claim needs).

**Pool-relevant delivery modes (all verified 2026-08-05):**
- QRM1001, all 7 Chapel, all 13 RDQM, UCB1103, UIC1805 ×2, UIC1806 ×2 → **대면강의**
- YCE1253 (WestCiv) → **블랜디드(동영상)**: 화5,6 in-person / 목4 video
- **UIC1561 (WestCiv) → 비대면(실시간+동영상)**: 월7,8 실시간온라인 / 수7 동영상.
  This single section is what makes 월+금 free possible (R50).

### ✅ 3. 동영상콘텐츠 blocking — CLOSED 2026-08-05 by official 수강편람 (see R52)
"동영상콘텐츠" blocks **do NOT occupy time** (explicitly overlappable);
"동영상(중복수강불가)" blocks **do**; "실시간온라인" blocks time but not presence.
133 국제 block-cells across 79 sections were wrongly treated as conflicts. Effect is
purely loosening: every prior valid timetable stays valid, new ones appear.
Notably **YCE1253 WestCiv effectively occupies only 화5,6** (its 목4 is free).

### ✅ 4. Parentheses — CLOSED 2026-08-05 (R54), from two 강의계획서 Iden pulled
- **Pattern A (different room) = weekly in-person LAB.** CHE1002-06 syllabus states
  강의 2h/week + 실험 2h/week in the chem lab. Real, weekly, with its own
  1/3-absence-F rule. Conservative treatment PROVEN correct.
- **Pattern B (same room) = extra period.** MAT1002-05; nothing indicates 격주 or
  optional. Treated as occupied — unrefuted, conservative.
→ **Keep parenthesized periods as occupied time.** No change to any prior count.

### ⬜ 6. Language pool 83 vs 93
Irrelevant to Iden's committed CN choice (R48); keep open for record integrity only.

---

## LAYER 2 — RULES
7. **UIC1805/1806 seats + UIC First status** — portal only; sandbox gets 403, so Iden
   pulls manually. Determines how safe the Aug 25 first-come grab is.
8. **Chapel B** — eligibility for a 2nd-semester freshman; which chapel types count
   toward the 4 × 0.5cr passes. All 7 국제 sections are 대면강의, 1 period each.
9. **SciLit list (R41)** — provided by Iden; confirm it is current and complete.
10. **19-credit cap** — from the guide; confirm against Iden's actual record.
    (Chapel + RC자기주도활동 are cap-exempt per R37.)

---

## LAYER 3 — PREFERENCES (Iden's values; assistant never fills these)
11. **Weight refit** — 4 new scenario answers collected 2026-08-05 (see Decision Log
    D-4). Not yet fitted. After fitting, re-test against real grids before trusting.
12. ✅ **Presence semantics scope — CLOSED 2026-08-05 by Iden.** Rationale in Iden's
    words: free days matter *because of the bus to 국제 campus* — an online block means
    no commute, so it does not break a free day. But an online block still costs time,
    so **early-start / lunch / gap / late penalties count ALL time-blocking cells**
    (대면 + 실시간온라인 + 동영상(중복수강불가)), online or not.
    → free days use the PRESENCE mask; all other penalties use the TIME mask.
    (동영상콘텐츠 cells are in neither mask — they occupy nothing, per R52.)
13. **Still empty:** slot-deferral values, chapel bonus size, professor ratings.

---

## DECISION LOG
| # | Date | Decision | Rule |
|---|---|---|---|
| D-1 | 08-04 | Enumeration approach **B** (pattern-level), stratified by type | R42/R43 |
| D-2 | 08-04 | Type map: 9 types (WCiv/LHP/RDQM/SciLit/Chapel/Lang/MR/ME/ELEC) | R43 |
| D-3 | 08-04 | Language = UIC beginner courses only; **take it NOW, not deferred** | R46/R48 |
| D-4 | 08-04 | **Chinese(1) UIC1805-01** primary; JP-01 = identical-grid fallback | R48 |
| D-5 | 08-04 | Ranking = weighted points; N = 50 manual / 5000 analysis | R44 |
| D-6 | 08-04 | Collapse geometrically identical timetables; deliver as visual HTML | R48 |
| D-7 | 08-05 | Online/blended blocks do NOT count as campus presence for free days | R50 |
| D-8 | 08-05 | **Slow down**: verify every rule before rebuilding the artifact | this file |
| D-9 | 08-05 | Canonical source = **deduplicated xlsx (709)**, not all_kj.json | R51 |
| D-10 | 08-05 | Online blocks discount **free days only** (commute logic); early/lunch/gap/late penalties still count them | item 12 |
| D-11 | 08-05 | 동영상콘텐츠 cells occupy **nothing** — not time, not presence (official) | R52 |
| D-12 | 08-05 | Iden is **not** an 외국인 유학생 → no 30% async cap | R53 |
| D-13 | 08-05 | Parenthesized periods **stay counted** as occupied time (lab, proven) | R54 |
| D-14 | 08-05 | Free days scored **cyclically** (week = Z₇, weekend always free): longest free run + smaller bonus per isolated free day | R57 |
| D-15 | 08-05 | Friday gets an **extra** bonus on top of contiguity (school events) | R57 |
| D-16 | 08-05 | Chapel restricted to English sections YCA1006-01/02 → family 2,326 → **1,310** | R58 |
| D-17 | 08-05 | **Target = 18 credits = 6 academic courses** + exempt chapel (cap is 21 via GPA 3.8, but 18 is the goal) | R59/R60 |
| D-18 | 08-05 | Eligibility filter = 유의사항 patterns, not 언어 field; SciLit 42 → **22** | R61 |
| D-19 | 08-05 | **Iden confirms**: taking Intro to QRM + all available CCs this semester is "the usual optimal strategy" → the 5-course base is now Iden-stated, not an assistant assumption. Only the 6th course is open | REQUIREMENTS_AUDIT §F |

| 34 | R121 re-verification after R129 | data | 🟡 **PARTIAL (R132)** — cheapest pair WCiv+LHP re-run, cannot beat 45.214. **9 of 10 pairs still to run** |
| 35 | Refit R117 deferral costs to the new schedule scale | pref | 🔴 **OPEN (R129)** — Iden's anchors were set against a 63-point range; the range moved. **His call, not mine** |
| 36 | Add the 4 eligible UIC Seminar sections to the pools | data | 🔴 **OPEN (R131)** — model still contradicts Iden |
