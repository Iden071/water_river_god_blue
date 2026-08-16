# THE MODEL — every number, where it came from, and whether it's trustworthy
**Current as of 2026-08-07.** Live values only. Regenerate the summary table with
`python gen_weights.py`; run `python test_weights.py` (22/22) after any edit.

### Status codes
| | meaning |
|---|---|
| **[E]** | **Elicited** — Iden stated it. His words are in `RULES.md` next to the constant. |
| **[M]** | **Measured** — computed from data. No judgement involved. |
| **[D]** | **Derived** — follows from [E] and [M] together. |
| **[P]** | **Provisional** — a placeholder nobody has confirmed. |
| ⚠️ | Known to be wrong or missing. |

---

## 0 · THE SCALE
Everything is a ratio to one anchor. Absolute scores are meaningless; only differences rank.

> **one class day starting at 9:00 = −10** **[E]**

Two secondary anchors, both used to bracket other values: **no lunch = −6**, **no dinner = −8**.

---

## 1 · THE DAY — how unpleasant each class day is
Applies to every day with a class. Uses the **TIME** mask, so an online class *does* count —
it holds an hour whether or not you go anywhere.

| what | value | status |
|---|---|---|
| starts 9:00 (1교시) | **−10** | [E] anchor |
| starts 10:00 (2교시) | **−5** | [E] confirmed 2026-08-07 |
| no lunch — 11:00–14:00 all busy | **−6** | [D] |
| no dinner — 17:00–20:00 all busy | **−8** | [E] "slightly bigger than lunch" |
| L hours back-to-back (L≥4) | **−(8 + 0.8(L−4)²)** | [E] 4h = −8, convex |
| day ends late, last period L | **−(L−8)^1.4307** | [E] 17:50 = −1, 21:50 = −10 |
| dead gap of ℓ periods | **−10·(ℓ/4)²** | [E] a 4-hour hole ≈ one 9am |

**All seven trace to something Iden said.** 2교시 was the last holdout and closed today.

---

## 2 · THE WEEK — two separate goods, not one
The single biggest correction of the session (**R129**). The old model priced "commutes
avoided". Iden **lives at 국제**. The good was never commuting — it is *can I go home*, and
home is ~2h away. That splits into two things that were being added together as one:

### TRIP — going home
Needs days with **no campus presence**, **connected to the weekend**. Uses the **PRESENCE**
mask, so an online class does **not** block it — you can attend from home.

> **13.00 × (run − 2)^1.4** where `run` = consecutive campus-free days including 토·일

| free weekdays attached to the weekend | trip value |
|---|---|
| 1 (금) | 13.00 |
| 2 (목+금) | 34.3 |
| 3 (수–금) | 62.4 |

- **13.00** **[E]** — "a free Friday = two 9am starts" (=20), minus REST.
- **1.4** **[P]** — Iden: *"can't quantify tbh"*. Bracket **[1.2, 1.6]**; this is the midpoint.
  Direction (convex) is solid; magnitude is not. ✅ **Sensitivity tested (R160): it cannot
  reorder the top**, because every leading candidate shares the 월금 shape so the term is
  common and cancels. Re-test if the top ever contains more than one free-day shape.

### ⚠️ UNCERTAINTY IS NOT PROPAGATED (R173)
`DAY_CONTIG = 20 − REST` **inherits REST's bracket**, and every trip value inherits it in turn.
Combined with `RUN_EXP`'s own bracket, a 월금-free week is worth anywhere in **47.6 – 59.1**;
this file reports **57.7**. Every figure here is a point estimate of an interval-valued quantity.

✅ **This does not affect any ranking decision** — R173 perturbed both brackets to both extremes,
singly and jointly, and the top-two gap stayed at **0.73 to three decimals** in all eight cases,
because the perturbed terms are common to both candidates. **It affects the meaning of the
absolute numbers, not their order.** Never quote a score as if it were precise.

### REST — a day off
Needs a **genuinely** free day: nothing holding a fixed hour. Uses the **TIME** mask, so an
online class **does** kill it. Equal on every weekday, weekend-attached or not.

> **7.00 per genuinely empty weekday** **[E]**

Bracketed by three of Iden's comparisons: worse to lose than a missed lunch (>6), better than
a missed dinner (<8), better than a 9am start (<10). **7.0 is the bracket midpoint.**

### Friday events bonus
> **+4.333**, **void** if a fixed-hour class sits in 14:00–19:50 **[D]**

Set so that Monday = 75% of Friday, an older elicited ratio.

⛔ **A previous version of this file claimed the two elicitations "cross-check" each other with
no drift. That claim was false and is withdrawn (R173).** Written out it is 3 unknowns
(REST · DAY_CONTIG · FRI_EVENT) against 2 equations — **one degree of freedom**, closed by
*choosing* REST = 7. Both equations hold for **every** REST in (6,8): 6→(14.00, 4.667),
7→(13.00, 4.333), 8→(12.00, 4.000). Under-determined systems have no residual, so nothing
could have failed. It was a solved system reported as a passed test.

✅ **A real consistency check does exist and did pass**, just not this one: R140's E3 (REST < a
9am start) and E6 (REST < a missed dinner) bound REST from above independently and agree
(8 < 10). Two of Iden's answers constraining the same quantity compatibly — that is the check.

### Why this matters concretely
A Wednesday between two campus days, whose only class is online, used to score as a free day.
It now scores **identically to an in-person Wednesday** — no trip (not weekend-connected) and
no rest (you're working). That killed all ten 월수금 timetables in the old top 50.

---

## 3 · BEING OFF-SCHEDULE — the 학년 gap
Every course sits at a year in QRM's curriculum chart (`c`). You take it in your year (`y`).

> **early** (y < c): **−4.0 × (c−y)^2.5**  ·  **late** (y > c): **−2.67 × (y−c)^2.5**

| 3 early | 2 early | 1 early | on schedule | 1 late | 2 late | 3 late |
|---|---|---|---|---|---|---|
| −62.35 | −22.63 | −4.00 | 0 | −2.67 | −15.08 | −41.57 |

- **Early** = *"I'm not ready for it"* **[E]**. Confirmed: the 대학요람 lists **no formal
  prerequisites** on any QRM required course, so this is a difficulty estimate, not a gate.
- **Late** = off-sequence; everything downstream slides **[E]**, added 2026-08-07.
- Asymmetry **1.5** and the shared exponent **2.5** are both **[E]**.
- Chart year comes from **QRM's own chart**, not the registrar's — the registrar labels
  ECO1103/1104 as year 2 from *Economics'* point of view; QRM places them at year 1.

### ⛔ THE LATE ARM IS UNREACHABLE IN LIVE CODE (R173)
`YEAR_PEN = lambda y: year_gap_pen(1, y)` — `taken_in_year` is **hardcoded to 1**, so
`gap = 1 − chart_year ≤ 0` always and **only the early arm can ever fire.** The late column of
the table above describes a code path that never executes.

R146 built the late arm as the principled replacement for R117's fitted `DEFER` table; R156
found the swap was never performed. **Both are still true.** The deferral cost is carried
*entirely* by `defer_costs.json`. The late arm becomes live only when the ranker learns *which
semester* a deferred course lands in — i.e. together with the four-year layer, not before.

### ⚠️ The EARLY arm is the model's only GPA protection — and it was halved
Double-major admission is **competitive on cumulative GPA** (`HANDOFF.md` 191–194), and at
application time in December that GPA is **Sem 1 + Sem 2 only** — so Fall 2026 grades decide
it. Separately, a GPA ≥ 3.75 buys **+3 credits** of load next semester. Both loops run through
this semester's choices, and **nothing else in the model represents difficulty at all.**

The early arm is therefore doing double duty: it is a readiness penalty *and* the only thing
stopping the ranker recommending courses that could cost the GPA. **R128 rescaled it 10 → 4**
purely as a readiness judgement, without anyone noticing it also halved the GPA protection in
the one semester where GPA is decisive. The #1 at the time this was written took **STA2102** (chart year 2, −4); at the pre-R128
weight that would have been −10. (That timetable is now rank 9 — see R155.)

**Not a proposal to change it** — the −4 was Iden's call on readiness grounds and stands. But
the early arm must not be weakened again without that second job being considered, and no
difficulty data exists to model the GPA loop properly.

---

## 4 · POOL VALUE — how much a course is worth for what it counts toward
Two different kinds of requirement, and only one was ever modelled:

- **Named** (MR·WCiv·LHP·SciRD·Lang) — one specific course. Handled by the slot mechanism.
- **Quota** (ME 18cr · Seminar 6cr · free electives ~15cr) — *N* credits from a pool, you
  choose which. Iden: *"no one exactly chooses the courses for you."* Had **no value at all**
  until today.

> **role = 8 × min(1, credits still needed ÷ reachable supply)** **[M]**

| pool | need | courses | supply | ratio | role |
|---|---|---|---|---|---|
| **MR** | 18 | 6 | 18 | 1.00 | **8.00** |
| **ME** | 18 | 28 | **63** (Korean cap, R152) | 0.29 | **2.29** |
| **Seminar** | 6 | 45 | 135 | 0.04 | **0.36** |
| free elective | 15 | 719 | 2157 | 0.01 | 0.06 → **0** |

⛔ **This file previously said "the formula validates itself". It does not (R173).**
`ROLE = BASE × ratio`, and R149 set `BASE = 8` *to match* Iden's elicited `ROLE_MR`. With
ratio_MR = 1.00 it returns 8 **by construction** — had the ratio been 0.5, BASE would have been
set to 16 and it would still have "reproduced" 8. One equation, one free parameter.

✅ **The structural fact underneath is real and was computed independently:** MR needs 18
credits from exactly 18 credits of named courses ⇒ **ratio 1.00 ⇒ MR has zero slack.** That is
non-trivial and true. It is the *formula* that is unvalidated, not the observation.

⚠️ ME supply is **63 cr, not 84** — up to 12 credits only of Korean-taught 상경대학/응용통계
sections may count (R152/R105). The cap attaches to the **section's offering department**, not
the course code: STA2102 offered by 계량위험관리 is uncapped, the same code from 응용통계학과
is not.

**Iden retired his own ME value (6.0) in favour of the measured value**, 2026-08-07: *"I
naturally thought MEs would be easier to get than MRs, but if the numbers contradict that,
then the numbers are probably right."* His intuition and the formula were measuring the same
thing; the formula measures it properly.

Also live and NOT derived from the formula — both are Iden's stated preferences, kept
deliberately on the preference side of the line:
- **language course +8** [E] — a requirement bonus, unrelated to any second major.
- **chapel +10** [E] — *intrinsic* desirability (*"chapel is pretty desirable in itself",
  "easy to catch, finish offline chapels now"*), separate from its deferral cost. Lives in
  `rank3.py` as `CHAPEL_BONUS`. Chapel is cap-exempt, so it never competes for a slot.

---

## 5 · DEFERRAL — derived, no longer elicited
Postponing a requirement out of Fall 2026 has **three** terms. Only the first was ever
modelled, which is why the answer flip-flopped three times in one session.

| term | source |
|---|---|
| **+ gain here** — the week improves | [M] §6 crowding curve |
| **− crowding there** — the receiving semester gets worse | [M] §6 |
| **− year gap** — you take it off-sequence | [D] §3 |

Worked through for QRM입문: **+38.05 − 14.00 − 6.67 = +17.38** (lands year 2), or **+8.97**
(lands year 3). **Deferring wins on all three terms at once.**

⚠️ Optimistic in two ways: −14.00 is the *cheapest* pair in the pool, and Fall data stands in
for a Spring semester. **+8.97 is the number to trust; the sign is not in doubt.**

### ⚠️⚠️ THIS IS NOT WIRED IN. The ranking still uses the OLD table.
`rank3.py` line 31 still reads `defer_costs.json` — R117's seven hand-fitted values
(WCiv −12 · MR −17.7 · LHP −13 · SciRD −14.99 · Lang −16.97 · Chapel −4.21 · ME −8.43).
**Everything above is derivation, not live behaviour.** An earlier draft of this file claimed
the table was "replaced entirely"; that was false and is corrected here.

**Why it is not yet wired in — and it is not just B-1.** Under the derived scheme every
outstanding CC requirement is chart-year 1, so they all defer to the same year and take the
same year-gap cost (−2.67), plus the same crowding cost (−14.00): **about −16.7 each, with no
differentiation between them.** The old fitted table *did* differentiate, using measured
competition. What would legitimately separate them under the new scheme is **risk — thin
future supply** (1 신촌 SciRD section, 2 신촌 LHP), and that term does not exist yet (§8.2).

⇒ **B-2 is blocked on B-4 (risk), not only on B-1.** Swapping the table in today would trade a
crudely-fitted but discriminating set of costs for a principled but flat one. Do B-4 first.

---

## 6 · CROWDING — why spreading requirements out matters
Best achievable week using **only** the forced requirements + chapel, exhaustive:

| forced | best week | marginal |
|---|---|---|
| 0 | 122.87 | — |
| 1 | 116.25 | −6.62 |
| 2 | 102.25 | −14.00 |
| 3 | 49.14 | −53.11 |
| 4 | 30.39 | −18.75 |
| 5 | **−7.66** | −38.05 |

**Steeply convex — the 5th forced course costs ~6× the 1st.** Carrying all five rather than
none costs **−130.5**. (Non-monotone in the middle because the *optimal subset* changes at
each step, not because the trend reverses.)

---

## 7 · THE FOUR-YEAR FRAME
| fact | status |
|---|---|
| 7 semesters remain (sem 2–8); 106.5 credits | [M] |
| Fall 2026 forced 국제 (RC freshman) | [M] official |
| QRM3003 is 국제-only **and** Spring-only ⇒ one Spring must be 국제 | [E] Iden, 2026-08-07 |
| ⇒ **minimum 2 국제 semesters · maximum 5 신촌** — regardless of this Fall | [D] |
| 4 국제-only items (QRM입문·WCiv·Lang·QRM3003) into 12 국제 slots ⇒ **not scarce** | [M] |
| Chapel does **not** force 국제 after this year — 신촌 chapel is online | [M] official |
| Seminars are mostly **신촌** (38 vs 7) — the old "all CC is 국제" was wrong | [M] |
| 42 slots for 35.5 courses ⇒ **6.5 spare in the whole degree** | [M] |

### The credit budget — three mutually-constraining paths
Graduation is **126 credits** and CC is 39 of them. QRM is **36 with a double major**, but
**42 with the AI Concentration**, which explicitly does *not* get the reduction (R106,
QRM table note 6: *"AI Concentration major requirements remain unchanged, even with a double
major. (1st Major – 42 credits)"*).

| path | CC | QRM | AI | 2nd major | total | vs 126 |
|---|---|---|---|---|---|---|
| **double major only** | 39 | 36 | — | 36 | **111** | fits, 15 spare |
| **AI concentration only** | 39 | 42 | 18 | — | **99** | fits, 27 spare |
| **both** | 39 | 42 | 18 | 36 | **135** | ⚠️ **over by 9** |

**Doing both does not fit in 126 credits.** QRM4807 counts as an AI requirement *and* a QRM
ME, but R104 allows it to serve only one, so that recovers 3 credits at most — still ~6 over.
Both would need an overload semester or a 9th semester.

---

## 8 · ⚠️ WHAT IS NOT IN THE MODEL
Ordered by how much it could change the answer.

1. **Quotas are priced but not enforced.** §4 gives ME/Seminar/free a per-course value, but
   nothing checks you actually reach 18 / 6 / 15 credits by graduation. A real shadow price
   needs the full four-year optimiser.
2. **Risk.** Thin future supply is uncounted — 1 신촌 SciRD section, 2 신촌 LHP. Deferring
   those is riskier than the semester count shows. Measurable; not yet measured.
3. **Availability.** Nothing models whether a section still has seats on 8/25. A per-학년 quota
   of 0 makes registration *impossible*, not merely hard. **Checkable after 8/14.**
   ⚠️ **Trap for whoever builds this:** every competition figure available
   (`mileage_history.json`) comes from the **마일리지 round, which only 2학년+ students bid
   in**. Iden registers on **대기순번제** — first-come, no bidding. Those numbers are evidence
   about *demand*, never about *his access* (R130). Use `sy1PercpCnt`, not 배율.
4. **신촌 semesters use the 국제 free-day rule.** At 신촌 you commute daily from home, so every
   free day saves a trip and the weekend-connection logic doesn't apply. Doesn't affect Fall
   2026 (국제 either way); does affect every 4-year comparison.
5. **`RUN_EXP` sensitivity untested.** If the top 50 is stable across [1.2, 1.6], the question
   dies and Iden never has to answer it.
6. **Second major unknown.** Quota effect is live (ME 24→18, free 45→~15); the *choice* gates
   all second-major bonuses, still scrapped.
   ⚠️ **R104 governs the choice and is not in the arithmetic above.** 과목인정 means overlap
   between two majors satisfies a *requirement* but yields **no credits** — 대학요람: *"counted
   towards fulfilling only one of the majors."* So high overlap does **not** make a second
   major cheaper; you make the shortfall up elsewhere. This **inverts** the intuitive case for
   Economics, the highest-overlap candidate.
   ⚠️ **The AI Concentration is a second, independent fork** (R106). It **cancels** the 42→36
   reduction, so it and a double major are substitutes on credits, not additions — see §7.
7. **Exam clashes** from overlapping video courses — 49 of the top 50 carry ≥1 overlap.
8. **Professor ratings** — 56 names, column empty. Deliberately post-hoc.
9. **MAX_DEFER=1 only partly re-verified** — 1 of 10 two-deferral pairs re-run since §2 changed.
10. **The crowding curve (§6) is measured on the wrong semester.** It uses the Fall 2026 국제
    pool as a stand-in for the Spring semester that would receive a deferred course. §5 admits
    this; it belongs here too. Same class of error as gap 3 — right instrument, wrong
    population.

---

## 9 · THE HONEST SUMMARY
**Trustworthy:** the day model (§1), the week model (§2), the year gap (§3), the pool
formula (§4 — it reproduces an independently elicited value), the crowding curve (§6), the
campus arithmetic (§7).

**Not yet trustworthy:** anything depending on future *availability* (§8.2, §8.3), the
four-year optimiser that would turn §4 into real shadow prices (§8.1), and the exact sharpness
of the trip curve (§8.5, probably harmless).

**Not ready to register from.** Gaps 2 and 3 are the ones with a deadline.
