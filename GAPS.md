# KNOWN GAPS — what the model does not do

> ## ⭐ STATUS 2026-08-09 (R191): THE LOGIC IS CLOSED. WHAT REMAINS IS DATA.
> Split the list the way Iden did — *"that is data. As long as we finalize the logic, it
> will fit in quite neatly."*
>
> **Mechanisms now present:** continuation value · free-elective opportunity cost ·
> 휴학 parity · 계절학기 · difficulty axis + GPA gate · widened language pool ·
> acquisition risk (both regimes) · mileage budget · Korean ME cap · second-major channel ·
> the retirement harness.
>
> **Data still missing, in priority order:**
> 1. **Fall 2026 seats** — `fetch_fall2026.py` after 8/14 into `fall2026_seats.json`.
>    `risk.p_get_freshman()` already reads that path and returns 1.0/'NO DATA' until it
>    exists. A `sy1PercpCnt` of 0 makes registration impossible (R134).
> 2. **Mileage evidence for 12 of 15 ledger items** (G-3) — only Chapel, LHP and SciRD are
>    priceable, so the 72-point budget is enforced but cannot bind.
> 3. **계절학기 offerings** — the 7-credit cap is sourced; what is *offered* is in no document.
> 4. **Which second major** — December (R147). `rank4.DM_MAJOR = None` until then.
> 5. **The tie-break ladder** (이수학점/학년) — decides 7 of 8 observed UIC1806 sections and
>    every cap-12 course including ECO1101. Not modelled; may need a rule, not data.
>
> **Still genuinely unmodelled logic:** the 신촌 free-day rule (G-7, needs Iden) · difficulty
> beyond the language tier · professor quality · exam clashes · prerequisite chains ·
> uncertainty propagation · whether he wants the course.
**Current 2026-08-09.** Registration **8.25 09:00 KST — 15 days.**
Supersedes `MODEL.md` §8, which is now the older and shorter list.

Ordered by **whether it can change the 8/25 decision**, not by how interesting it is.

---

## TIER 1 · CAN CHANGE THE 8/25 DECISION

### G-1 ⏳ Fall-2026 availability — the only gap with a deadline
Nothing models whether a section still has seats on 8/25. A per-학년 quota of **0** makes
registration *impossible*, not merely hard (R134). **This is the one check that can invalidate
the whole plan.**
- **Blocked until 8/15**, after the 2학년+ rounds close. Data does not exist before then.
- **Iden must pull it** — the sandbox gets proxy 403 on every Yonsei host. `fetch_fall2026.py`
  is written and waiting; it needs one fresh `JSESSIONID` and takes ~2 minutes.
- ⚠️ Do **not** substitute mileage 배율 for this. That describes the 2학년+ round Iden is not in
  (R130), and the whole point of the check is a different field entirely.

### G-2 ✅ CLOSED 2026-08-09 (R182) — the deferral cost is now COMPUTED
`continuation.py` places every deferred requirement into a real semester and prices it by
the year gap it opens plus the crowding it adds. `defer_costs.json` is no longer read by the
live ranker (`rank4.py`). The fitted values understated the true cost by roughly half, and
the top-two gap went from 0.73 to 10.667. **The late arm of the 학년 penalty is finally
live** — it needed the landing semester, which is exactly what V computes.

<details><summary>the original gap, kept for the record</summary>

#### G-2 The deferral cost is still R117's fitted table
`rank3.py:31` loads `defer_costs.json` — seven values fitted to two of Iden's anchors, on a
scale that has since moved twice. The principled replacement (the late arm of the 학년 gap,
R146) is **implemented but unreachable**: `taken_in_year` is hardcoded to 1, so only the early
arm can fire (R173). It becomes live only when the ranker knows *which semester* a deferred
course lands in — i.e. with the four-year layer, not before.
**This sits directly under the live decision**, which is a choice between two deferrals.
</details>

### G-4 ✅ CLOSED 2026-08-09 (R181/R182) — quotas are now enforced, not just priced
The ledger in `plan_model.py` reconciles to the degree exactly (106.5 = 126 − 19.5) and
`continuation.py` returns −∞ when no legal placement of the remainder exists.
⚠️ **One quota is still priced-but-unenforced: the Korean 12-credit ME cap (R152/R105).**
Same class of gap Iden caught in R181. Next.

### G-16 🆕 Quota progress is FLAT at +31.175
Retiring any low-supply requirement early saves the same marginal crowding, so the model
cannot currently tell a scarce requirement from an abundant one. R172 warned specifically
about losing that substitutability signal when merging `ROLE` into something else.
Scarcity still enters through feasibility and the year gap — but not through the margin.

### G-3 Risk is built for deferred courses only, and 16 key courses have no evidence
`risk.json` covers **21 courses**. The following have **none**: QRM3003 · QRM3004 · QRM3005 ·
ECO2101 · ECO2102 · STA2102 · QRM2004 · QRM2102 and all 8 widened-language courses — every one
either 신촌, Spring-only, or from R166's widened pool. **So the mileage-budget feasibility check
cannot be run on a real future semester.** It can compare the two live deferral options, and
that is all that should be claimed from it (R171).

---

## TIER 2 · SHAPES THE FOUR-YEAR PLAN, NOT THIS SEMESTER

### G-4 Quotas are priced but not enforced
`ROLE` gives ME / Seminar / free electives a per-course value (R149/R152), but **nothing checks
he actually reaches 18 / 6 / ~15 credits by graduation.** Needs the four-year optimiser.

### G-5 The plan object does not exist — Plan A and Plan B are still separate
With acquisition risk there is no "choose a timetable"; on 8/25 Iden chooses an **order of
attempts with fallbacks** — a policy. `PLANS.md` has tracked the ranking and the click-order as
separate work items since session 1. **They are one object** (R168).
⚠️ And fallbacks are **not free**: of the top 50, **26 have zero** same-course/same-time
alternates and 24 have exactly one; **#1 has zero**. Almost every real fallback changes the grid
and costs score, so degraded branches must be *scored*, not merely listed.

### G-6 Robustness is unpriced
Follows from G-5. A plan with good fallbacks is worth more than an equal-scoring one without,
and the model cannot see the difference.

### G-7 ⛔ REOPENED AND RESCOPED 2026-08-09 (R195) — it DOES affect Fall 2026
The shape is now elicited and built (linear at 신촌, convex at 국제). But the old line
*"Doesn't affect Fall 2026 (국제 either way)"* is **wrong**: Fall 2026 is 국제 either way, yet
the rule prices the six semesters after it, which sit inside every score. Sweeping the step
size flips #1 between *defer Language* and *defer Intro to QRM* at a threshold of **10–14**.
**The size is now a live input for 8/25.**

<details><summary>original wording, wrong on scope</summary>

#### G-7 신촌 semesters use the 국제 free-day rule
At 국제 Iden dorms, so a free day pays only as part of a block worth travelling for. At 신촌 he
commutes daily from home, so *every* free day saves a round trip. **Opposite structures; only
the dorm one exists.** Doesn't affect Fall 2026 (국제 either way); affects every 4-year
comparison. **Needs Iden.**
</details>

### G-8 The availability table is thin where it matters most
`availability.json` covers 789 courses but only **21 have more than one term of evidence** —
and those 21 are 131 국제 rows against 11 신촌. Any claim of the form *"course X is always Y"*
drawn from it is a claim about **국제 sections of X** (R170, which corrected R159 on exactly
this). 8 further courses are flagged as varying by term and have never been looked at.

### G-9 The crowding curve is measured on the wrong semester
§6's curve uses the Fall 2026 국제 pool as a stand-in for the Spring semester that would receive
a deferred course. Same class of error as G-8 — right instrument, wrong population.

### G-10 The widened language pool is not implemented
`LANG` is still `{UIC1805, UIC1806}` — 4 sections. The real pool is **10 level-1 courses, 20
sections** (R166). ✅ Tested: this **cannot change Fall 2026** — the easy tier wins on schedule
alone by 14.18 (R175). It matters as a **fallback** if the easy tier is unavailable on 8/25.

---

## TIER 3 · REAL BUT INERT — logged with trigger conditions

### G-11 The dinner penalty is mis-derived, and never fires
`W_DINNER = −8` was set *"by symmetry with lunch"*, but always co-triggers `LATE`, turning
Iden's *"slightly bigger"* (1.33×) into **2.14×** (R173). Measured: it fires in **0 of 5000**
timetables — nothing at 국제 has classes at 9, 10 *and* 11.
🔔 **Re-open if the pool ever widens to a 신촌 semester**, where evening sections are common.

### G-12 Uncertainty is never propagated
`DAY_CONTIG = 20 − REST` inherits REST's (6,8) bracket; with `RUN_EXP`'s [1.2, 1.6] a 월금 week
is worth anywhere in **47.6 – 59.1** while the model reports **57.7**. ✅ Does not affect
ordering — perturbing both brackets to both extremes leaves the top-two gap at **0.73 to three
decimals** (R173). It affects what the absolute numbers *mean*. Never quote a score as precise.

### G-13 `MAX_DEFER = 1` is only partly re-verified
1 of 10 two-deferral pairs re-run since R129 (R132). The cheapest and most dangerous pair
(WCiv+LHP) cannot beat the incumbent; nine remain.

### G-14 Exam clashes
49 of the top 50 carry ≥1 동영상콘텐츠 time overlap, and the 수강편람 warns exams may not
overlap. Needs per-syllabus checking — belongs on the shortlist, late.

### G-15 Professor ratings
`profs_in_top5000.csv`, 56 names, empty column. Deliberately post-hoc. ⚠️ its appearance counts
are from a superseded ranking; the **name list** is the useful part.

---

## WHAT IDEN OWES — and what has dissolved

| | status |
|---|---|
| **risk appetite** | ❌ **DISSOLVED** — mileage is a budget constraint, not a preference (R171). Nothing to weight. |
| **`RUN_EXP` magnitude** | ❌ **RETIRED** — cannot reorder the top (R160) |
| **`W_DINNER`** | ❌ **RETIRED** — fires in 0 of 5000 (R174) |
| **language difficulty tier** | ❌ **RETIRED for Fall 2026** — easy tier wins on schedule by 14.18 (R175). Live only as a fallback value. |
| **G-7 신촌 free-day rule** | ⏳ **OPEN** — needed for the 4-year layer, not for 8/25 |
| **campus dominance** | ⏳ **OPEN** — R126 pinned it to a ceiling that has since moved |
| **seminar deferral cost** | ⏳ **OPEN** — blocked behind G-2 |
| **double major choice** | ⏳ December. Quota effect already live; the *choice* gates the bonuses. |
| **G-15 professor ratings** | ⏳ post-hoc, after the shortlist |

## ⛔ RETIREMENTS ARE NO LONGER PROSE — 2026-08-09 (R187)

Iden: *"even if something 'does not change the answer', it should still be in the model in
case of future model changes."* He is right, and the reason is that **"cannot change the
answer" is a measurement against one version of the model, and it was being written down as
a conclusion.** Prose does not re-run.

**`test_retired.py` now re-measures every retired claim against the CURRENT model and exits
non-zero when one expires.** Nothing may be recorded as retired anywhere in this project
without a test in that file.

First run, immediately:

| claim | verdict |
|---|---|
| R160 `RUN_EXP` cannot reorder the top | ✅ still holds — top 50 all share 월금 |
| R144 국제 capacity is 3× oversupplied | ✅ still holds — best plan uses 4 of 7 |
| R186 a 휴학 cannot change 8/25 | ✅ holds **for this data** — only 1 item is term-restricted |
| R181 #1 respects the free-elective budget | ✅ #1 now spends **0** of ~5 |
| R174 the dinner penalty is inert | ⚠️ **uncheckable** — rank4's output dropped the column |
| **R175 / G-10 the widened language pool can't matter** | ❌ **EXPIRED** |
| **R171 risk dissolved into a budget constraint** | ❌ **EXPIRED** |

### ❌ G-10 REOPENED — widening the pool changed #1 immediately
2 courses → R166's 10. At zero difficulty weight the answer moved from *defer Language*
(46.640) to **defer SciRD and take YCF1603, a HARD-tier language** (47.565). R175's 14.18
margin was measured against a pool that did not contain the eight 언어와표현 courses; it is
their **time slots**, not their difficulty, that beat it.

### ❌ G-3 / R171 REOPENED — `risk.json` is read by nothing
`grep risk` returns 0 in `rank4.py`, `continuation.py`, `plan_model.py`. **V assumes every
future course is obtained with probability 1.** "Risk is only a budget constraint" is
currently *untested*, not true.

### ✅ G-16 / difficulty — the axis now EXISTS, unelicited on purpose
`difficulty.py`. Three regimes, swept over all 7200 candidates (one 9:00 start = 10):

| `D_LANG` | #1 |
|---|---|
| < 3.25 | defer SciRD, take YCF1603 (hard) |
| 3.25 – 10.25 | defer Language |
| > 10.25 | defer QRM1001, take UIC1805 (easy) — **this is R166's own conclusion** |

**Method to reuse: for any un-elicited parameter, build the mechanism, sweep the weight,
report the switching threshold.** Better than omitting (decays), than guessing (hides), and
than asking cold (R136/R137/R141 forbid it).

---

**Four questions were retired by testing rather than asking — and two have since expired.**
The discipline was: before spending Iden's attention, check whether the unknown can change
the answer. The missing half was: **re-check it every time the model moves.**

⚠️ **And the near-miss worth remembering (R175):** the first difficulty test was *wrong* — it
held a course fixed that time-conflicts with the option being evaluated, silently dropped that
option, and returned a confident inverted answer. **Verify every candidate in a comparison is
feasible before reading the comparison.**
