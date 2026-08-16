# PURPOSE CHECK — what the code actually rewards

**Built 2026-08-10 by reading the source, not the documentation.**
Every number below was recomputed from `rank.py` / `rank2.py` / `rank4.py` / `rank4_branch.py` /
`continuation.py` / `plan_model.py` / `difficulty.py` and measured against all 7,200 rows of
`FINAL_ranked4.csv`. No claim here is quoted from `MODEL.md`, `GAPS.md`, `STOCKTAKE`, or any
`HANDOFF`. Where a code comment claims something, that claim is marked as a *claim* and tested
separately.

**How to use this.** Every term has a box. Mark it:

- `[ok]` — this is what I want
- `[no]` — this is not what I want
- `[?]` — I can't tell / I don't recognise this as a preference of mine

You do not have to justify a `[no]`. Finding them is the point.

---

## 0 · Read this first: the number 160.577 is mostly a constant

$$F(x) \;=\; \underbrace{w(x)}_{\text{week}} \;+\; \underbrace{\textstyle\sum_c \pi(c)}_{\text{year gap}} \;+\; \underbrace{\kappa(x)}_{\text{chapel}} \;+\; \underbrace{\delta(x)}_{\text{difficulty}} \;+\; \underbrace{\big[V(\rho(x)) - V(\rho_0)\big]}_{\Delta V,\ \text{continuation}}$$

where $x$ is a timetable, $\rho(x)$ is everything the degree still owes after $x$, and $\rho_0$ is a
fixed reference remainder.

For the live #1:

| term | value | what it is |
|---|---:|---|
| $w$ week | **17.890** | this semester's weekly comfort |
| $\sum\pi$ year gap | **−4.000** | courses sat off their chart year |
| $\kappa$ chapel | **+10.000** | chapel taken |
| $\delta$ difficulty | **0.000** | no hard-tier language |
| $\Delta V$ continuation | **+136.687** | the next six semesters |
| **total** | **160.577** | |

And $\Delta V$ itself decomposes as:

| | value |
|---|---:|
| 96.0 × 5 신촌 semesters | **+480.000** |
| crowding in future semesters | **−210.110** |
| year gaps in future semesters | **−9.330** |
| minus the reference $V(\rho_0)$ | **−123.874** |
| $= \Delta V$ | **+136.687** |

**Measured over all 7,200 candidates, the whole score spans only 51.836 points.** The rest of
160.577 is an additive constant that every timetable receives. In particular:

> **The 신촌 term contributes exactly +480.000 to every single one of the 7,200 candidates.**
> All 12 distinct continuation states reachable by the ranking produce 5 신촌 semesters. The
> constant `SINCHON_SEMESTER_VALUE = 96.0` — the largest number in the model, and the one
> traced to *"much much much more preferable"* — **does no ranking work at all this semester.**

`[ ]` I understand the headline score is not on a meaningful scale.

---

## 1 · THE WEEK — $w(x)$

Spread across the 7,200: **73.432**. Across the top 50: **19.700**. This is the largest
discriminating term.

It splits into two parts that behave very differently.

### 1a · `week_value` — the two goods

$$w_{\text{val}} = \underbrace{13.00\,(r-2)^{1.4}}_{\text{TRIP}} \;+\; \underbrace{7.00\,\big|\{d : \text{fm}_d = 0\}\big|}_{\text{REST}} \;+\; \underbrace{4.333\cdot\mathbb{1}[\text{Friday event window free}]}_{\text{FRI\_EVENT}}$$

$r$ = length of the weekend-connected run of days with **no campus presence** (`pm`).
$\text{fm}_d$ = day $d$'s **fixed-hour** mask.

| what it rewards | constant | file:line | traced to |
|---|---|---|---|
| going home — a weekend-connected block with no campus presence | `DAY_CONTIG = 13.00` | `rank.py:32` | R142 — *"a free Friday = two 9am starts"* |
| a genuinely empty weekday — nothing holding a fixed hour, attached or not | `REST = 7.00` | `rank.py:67` | R140, bracketed (6,8) by three comparisons; midpoint taken |
| Friday afternoons/evenings free, for school events | `FRI_EVENT = 4.333` | `rank.py:69` | R57 *"a lot of school events are held on Friday"*; size = 25% of Friday, cross-check on *"월 = 금의 75%"* |
| how sharply extra free days compound | `RUN_EXP = 1.4` | `rank.py:39` | ⚠️ see §6-G |

**#1's week_value = 45.640** = trip 34.307 (a 4-day block) + REST 7.000 (**one** genuinely
empty weekday) + FRI_EVENT 4.333.

Note the gap: #1 has **two** presence-free weekdays but only **one** rest-free weekday. One of
월/금 carries an online class — it still lets him go home, it does not count as a day off. That
is the R129 split working as designed.

**Measured influence:** across the top 50, `week_value` takes only **2 distinct values** and
spans **7.000** — exactly one REST unit. All 50 have 월+금 free.

> **At the top of the ranking, the trip home is already saturated. It is not what separates
> the candidates.**

`[ ]` Going home is worth 13.00 per the first weekend-connected day, compounding.
`[ ]` A genuinely free weekday is worth 7.00, and an online class destroys it.
`[ ]` An online class does *not* destroy a trip home.
`[ ]` Friday afternoon free is worth an extra 4.333.

### 1b · `day_pen` — the within-day penalties

This is what actually orders the top of the list: spread **19.700** across the top 50, against
week_value's 7.000.

| what it punishes | constant | file:line | traced to | fires in top 50 |
|---|---|---|---|---|
| a day starting 1교시 (09:00) | `W_E1 = −10.0` | `rank.py:11` | **the anchor** — every other number is denominated in this | 25 / 50 |
| a day starting 2교시 (10:00) | `W_E2 = −5.0` | `rank.py:12` | ⚠️ **never elicited.** The only schedule constant with no statement behind it | **34 / 50** |
| 3·4·5교시 all busy (no lunch) | `W_LUNCH = −6.0` | `rank.py:13` | fitted, lunch+marathon = 13.75 | 15 / 50 |
| 9·10·11교시 all busy (no dinner) | `W_DINNER = −8.0` | `rank.py:26` | *"slightly bigger than missing lunch"*, set by symmetry | **0 / 50** |
| a run of $L\ge4$ consecutive hours: $-(8+0.8(L-4)^2)$ | `MARATHON` | `rank.py:17` | R72 — *"convex-like but generally all lower than steady; 4h = −8 still holds"* | 40 / 50 |
| a dead gap of $L$ periods: $-10(L/4)^2$ | `HOLE` | `rank.py:27` | R66 — *"big hole ≈ small holes"*; 4-hole = one 9am | 49 / 50 |
| how late a day ends: $-(\text{last}-8)^{1.4307}$ | `LATE` | `rank.py:21` | *"17:50 should start at −1, 21:50 should be −10"* — solved through both points | **50 / 50** |

`[ ]` A 10:00 start is half as bad as a 9:00 start. *(this has never been confirmed)*
`[ ]` A 4-hour run is worth about −8, growing quadratically.
`[ ]` A 4-period gap between classes is as bad as a 9am start.
`[ ]` Ending at 21:50 is worth −10.

---

## 2 · THE YEAR GAP — $\sum_c \pi(c)$

$$\pi(c) = \begin{cases} 0 & d = 0\\ -4.0\,|d|^{2.5} & d < 0 \ \ (\text{early})\\ -2.667\,|d|^{2.5} & d > 0 \ \ (\text{late})\end{cases} \qquad d = y_{\text{taken}} - y_{\text{chart}}$$

| what it rewards | constant | file:line | traced to |
|---|---|---|---|
| sitting a course in its chart year | `EARLY_K = 4.0` | `rank2.py:90` | R128 rescale |
| early is worse than late, by half again | `LATE_K = 4.0/1.5` | `rank2.py:91` | R146 — *"early is somewhat worse"*, *"roughly half again as bad"* |
| both arms scale sharply | `YEAR_EXP = 2.5` | `rank2.py:92` | R145 — *"sharply worse"* |

Chart years come from **QRM's own curriculum chart**, not the registrar's 학년 (`rank2.py:108`).

**Measured influence:** spread 26.627 over all rows, **4.000 over the top 50** (two values only:
−4 and −8). Inside the top 50 this term distinguishes almost nothing.

`[ ]` Taking a course a year early is worth −4; two years early −22.6; three −62.4.
`[ ]` Taking a 1st-year course in 3rd year is a real cost (−2.67 per year late, compounding).

---

## 3 · CHAPEL — $\kappa(x)$

`+10.0` taken (`rank4.py:49`, R127 — *"chapel is pretty desirable in itself"*),
`−4.2` not taken (`rank4.py:50`, inherited from R117's superseded scale).

**Measured influence:** **+10.000 in every one of the top 50.** Zero discrimination there.

`[ ]` Chapel is worth +10 in itself, separately from where it sits in the week.

---

## 4 · DIFFICULTY — $\delta(x)$

$$\delta(x) = -10.0 \cdot \big|\{c \in x: c \in \text{LANG\_HARD}\}\big| \;-\; \mathbb{1}[\text{Lang deferred}] \cdot p_{\text{hard}}^{\text{hi}} \cdot 10.0$$

| what it punishes | constant | file:line | traced to |
|---|---|---|---|
| a 언어와표현 language instead of Beginning Chinese/Japanese | `D_LANG = 10.0` | `difficulty.py:58` | R188 — *"About the same as a 9am start."* |
| the GPA feedback loop | `GPA_GATE_MULT = 1.0` | `difficulty.py:67` | never elicited; 1.0 = inert |

**Only ten courses in the entire catalogue carry any difficulty at all** — the 10 level-1
language courses. Roughly 700 others sit at exactly 0.

**Measured influence:** 3 distinct values in the top 50 (0.0, −3.5, −10.0), spread 10.000.
`D_LANG = 10.0` sits **on a switching threshold** (boundary at 10.25); the two surviving
strategies differ by 0.002 there.

`[ ]` A hard language course costs the same as one 9am start.
`[ ]` No other course in the degree is harder or easier than any other.

---

## 5 · THE CONTINUATION — $\Delta V$

$$V(\rho) = \max_{\text{campus pattern},\ \text{assignment}} \Big[ 96.0\,n_{신촌} + \sum \pi(\text{item}) - \sum \text{crowd}(\text{slot}) \Big]$$

subject to: one campus per semester · 국제 Spring exists (QRM3003) · ≥2 국제 semesters ·
≤6 courses/semester · ≤1 chapel/semester · ≤4 Korean ME at 신촌 · 72-point mileage budget.
$-\infty$ if no legal placement exists.

| what it rewards | constant | file:line | traced to |
|---|---|---|---|
| every 신촌 semester | `SINCHON_SEMESTER_VALUE = 96.0` | `continuation.py:183` | R126/R200 — *"신촌 is much much much more preferable"*, *"it is bigger than a mon + fri"* |
| not piling scarce courses into one future semester | `crowding.json`, measured | `continuation.py:99` | measured over all 32 subsets, not assumed |
| a free weekday at 신촌 | `SINCHON_PER_DAY = 17.0` | `continuation.py:136` | **derived**, not asked: REST 7.00 + HOLE(4) 10.00 for a 4-hour round trip |
| which items count as "scarce" | `LOW_SUPPLY_MAX = 40` | `continuation.py:191` | ⚠️ **never justified, never swept** |

### What this term actually does

**Across all 7,200 candidates, $\Delta V$ takes 7 distinct values.** Across the 12 reachable
continuation states, it takes 7. The full list:

| state | $\Delta V$ | best rank |
|---|---:|---:|
| defer MR, electives ME+ME | 136.687 | 1 |
| defer Lang, ME+ME | 141.899 | 7 |
| defer WCiv, ECO1101+ME | 139.233 | 9 |
| defer MR, ECO1101+ME | 124.148 | 20 |
| defer SciRD, ME+ME | 141.899 | 36 |
| defer Lang, FREE+ME | 121.045 | 40 |
| defer WCiv, ME+ME | 140.687 | 101 |
| defer LHP, ME+ME | 141.899 | 105 |
| defer nothing, ME | 139.233 | 179 |
| defer SciRD / LHP / WCiv, FREE+ME | 121.045 / 118.378 | 326+ |

The 신촌 component is +480.000 in **all** of them. So the variation in $\Delta V$ — the entire
four-year layer's contribution to the ranking — is crowding plus future year-gaps, and
crowding is gated by `LOW_SUPPLY_MAX = 40`.

The ledger's supply values are: 1, 2, 2, 2, 3, 4, 4, 9, 15, 20, 20, 35, 38, **422**. Everything
except `FREE` (422) is below 40. So:

> **The crowding term reduces to "how many non-FREE courses land in each future semester."**
> A course with 1 section (QRM3003) and one with 38 (Seminar) are charged identically.

`[ ]` A 신촌 semester is worth more than any weekly schedule.
`[ ]` A free weekday at 신촌 is worth 17.00 (7.00 rest + 10.00 for four hours of travel).
`[ ]` Concentrating scarce courses in one future semester should be penalised.
`[ ]` It is acceptable that a 1-section course and a 38-section course cost the same.

### What the continuation cannot see

`plan_model.py` `ITEMS` is the whole four-year model. Three of its fifteen entries have **no
course identity at all**:

| item | count | codes |
|---|---:|---|
| `DM` (second major) | 12 | `[]` — empty |
| `FREE` (free elective) | 5 | `[]` — empty |
| `ME` (major elective) | 6 | `['QRM2004','STA2102']` — 6 slots, 2 codes |
| `MR5`, `QRM3003` | 1 each | no observed sections in any term |

17 of ~40 remaining courses are interchangeable placeholders. This is the mechanism by which
$\Delta V$ collapses to 7 values.

---

## 6 · WHERE THE CODE AND THE STATED PURPOSE ALREADY DISAGREE

Separated deliberately. §1–§5 describe the model; this section is my own reading.

### A · #1 defers the one course R126 says to take now

R126 (your words, 2026-08-06) concluded, in its own text:

> *"**Take QRM1001 now.** 국제-locked, available, in a forced-국제 semester. Deferring spends
> scarce 국제 capacity later on something clearable today. This alone flips the current #1,
> which defers it…"*

The live #1 **defers QRM1001**. The continuation layer built later disagrees with that
reasoning — which is legitimate, it computes what R126 argued by hand. But the measured bias
runs the same direction: the counting proxy is biased by roughly **−24 per deferred course**,
and #1 defers one. Its margin over the best non-deferring alternative is **11.029**, and over
the best "defer Lang" alternative **2.287**. Both are inside the bias.

### B · The stated purpose is saturated where the decision is made

Everything in §1a — the trip home, the two-good split, the 2-hour commute, the dorm — is the
part of the model with the most elicitation behind it and the most careful reasoning. Across
the top 50 it contributes **7.000 points of spread across 2 values**. The decision is being
made by `day_pen` (19.700), $\Delta V$'s 7 buckets (20.855) and `D_LANG` (10.000).

If your purpose is "get home as much as possible," the model already achieved that at rank ~50
and is now optimising something else on your behalf.

### C · The largest constant does nothing

`SINCHON_SEMESTER_VALUE = 96.0` contributes +480.000 identically to all 7,200 candidates.
R126 itself said the right implementation is *lexicographic* — "maximise 신촌 semesters first,
optimise the weekly grid within that. **No exact number needed.**" The code instead spends a
number, and `continuation.py:181` claims the plan is "2 국제 / 5 신촌, the forced minimum."
Measured: the reachable states give **5 신촌 / 3 국제 total**, not 2 국제. The comment's
arithmetic and the code's behaviour do not match.

### D · Workload is not in the model, and R218 already proved it exploitable

Nothing prices six courses' worth of effort. `N_ACADEMIC = 6` is fixed by your choice (R111),
so course *count* never varies and the omission is invisible in the current run — but the
powerset run walked straight into it, stacking the two 비대면(동영상) sections that hold zero
fixed hours and scoring a week of 96.670. The model called that #1. Difficulty exists for
exactly 10 language courses and nothing else.

### E · Whether you want the subject is nowhere in the objective

Not a gap in a term — there is no term. The model cannot distinguish a course you'd enjoy from
one you'd resent at equal schedule cost. `profs_in_top5000.csv` has 56 names and an empty
column.

### F · The reference point is an impossible semester

$V(\rho_0)$ is evaluated at `(defer nothing, ('FREE','FREE'))` — two spare elective slots. But
deferring nothing leaves exactly **one** spare slot. `rank4.py:110` acknowledges the state is
unreachable and keeps it "so old numbers stay comparable." Harmless to the ordering (it is a
constant), but the 160.577 is measured from a semester that cannot exist.

### G · `RUN_EXP` implements the curvature you retracted

`rank.py:39` sets `RUN_EXP = 1.4`, giving marginal values per extra free day of
13.00 → 21.31 → 26.21 → 30.02 — **increasing**. R141 records you saying *"2→3 is bigger than
3→4"* — **decreasing** — and R141's own conclusion agrees. The code comment at `rank.py:40`
admits the contradiction. Swept 0.8→1.6 without changing #1, so it is currently inert; it is
listed because it is a case where the code does the opposite of a recorded statement.

### H · One constant that fires constantly has never been confirmed

`W_E2 = −5.0` fires in **34 of the top 50** and has been flagged `[P] 미확인 추정치` since the
first session.

---

## 7 · WHAT I NEED FROM YOU

In rough order of how much it would change the answer:

1. **Is the objective above the thing you want maximised?** Not term by term yet — as a whole.
   If the answer is "no, my purpose is X," say X in your own words and I will check the code
   against X rather than against its own documentation.
2. **§6-B** — with the trip home saturated at the top, what *should* separate two timetables
   that both give you 월+금? Right now the answer is holes, 9am starts and late finishes.
3. **`W_E2`** (§6-H) — is a 10:00 start half as bad as a 9:00 start, or less than that?
4. **§6-E** — should wanting the subject be in the model at all, or is it something you would
   rather apply yourself to a shortlist at the end?

Nothing here needs to be answered to hit 8/25. The seat pull after 8/14 still does.
