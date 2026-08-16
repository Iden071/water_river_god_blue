# DESIGN v2 — how the four factors fit together
**Drafted 2026-08-09. Nothing built yet. This is the paper stage Iden asked for.**

The four factors are **risk**, **difficulty**, **availability-over-time**, **quota enforcement**.
The instruction was to work out how they interact *before* writing code, because the project's
worst errors — R117's fitted deferral table, R129's conflated free-day value — both came from
building pieces separately and discovering later they were one thing.

**Result: they are not four factors. They are one data layer, one mechanism, and one
consequence with a feedback edge.**

---

## 1 · AVAILABILITY IS NOT A FACTOR — IT IS THE STATE SPACE

"When/where/in what language does this course exist" is **data**, not a term in a score.
Every other factor consumes it. It has no weight, no elicitation, nothing for Iden to set.

What it must contain, per course:

| dimension | why it is load-bearing | evidence |
|---|---|---|
| **term** | ECO1101 is 월수 every Fall on record; both recorded Springs offered a 화목 section | R159 |
| **campus** | 4 items are 국제-only; the 신촌 side is invisible to `canonical_2026F.json` | R143/R144 |
| **language** | ECO1101's *only* English 신촌 section is 월1,2/수2 — Monday **and** a 9am | R164 |
| **offering dept** | decides whether a section eats the 12-credit Korean cap | R152/R105 |
| **time shape** | the thing the whole weekly model runs on | — |

⚠️ Every one of those was **hand-queried** in the last session and none is in the model.
Build this first. Everything else is blocked on it, and it needs no decisions from Iden.

---

## 2 · RISK AND QUOTA ENFORCEMENT ARE ONE MECHANISM AT TWO SCALES

- **Risk** = P(I get this section at this registration).
- **Quota** = P(I finish 18 ME / 6 Seminar / 15 free-elective credits by graduation).

The second is the first, aggregated over the remaining semesters against the availability
landscape of §1. **If per-attempt acquisition probability is modelled over real availability,
quota completion is derived — not separately specified.**

⚠️ **Building them separately would be R117 all over again**: two mechanisms fitted apart, later
found to be one logic.

### ⛔ CORRECTED 2026-08-09 (R172) — it does NOT replace them. They are orthogonal.
This section originally claimed the risk mechanism subsumes `ROLE` and `DEFER`. **Tested at
implementation: false.** `ROLE` measures **substitutability** (are there other ways to fill this
requirement); risk measures **competition** (will I win any given one). QRM1001 has *no*
substitutes but is *cheap*; UIC2151 has *fourteen* substitutes and is the *most contested course
on the list*. They rank cases in opposite orders. Swapping would have deleted the
substitutability signal and blinded the model to single-section requirements.
**Both stay. Risk is a third, independent axis.** The original (wrong) reasoning is kept below
because the *shape* of the argument — that a value can be a feasibility statement in disguise —
was correct and is still worth applying elsewhere.

<details><summary>original claim, wrong</summary>

Both of these are **static proxies for exactly this quantity**:

| currently live | what it actually measures | verdict |
|---|---|---|
| `ROLE = 8 × (credits needed ÷ reachable supply)` (R149) | how hard a pool is to fill later — MR gets 8.00 because supply exactly equals need, i.e. **zero slack** | a crude feasibility estimate |
| R117's fitted `DEFER` table | what it costs to push a requirement into a future with less room | the same, per requirement |

**So the risk mechanism subsumes R149 *and* R117.** Do not add risk as a fourth additive term
alongside them — that double-counts. This is the same collapse that happened when TRIP and REST
turned out to be one elicitation done twice.
</details>

### Two regimes, never to be conflated (R130 vs R165)
| | Fall 2026 | everything deferred |
|---|---|---|
| Iden is | **1학년**, 대기순번제, freshman seats | **2학년+**, a mileage bidder |
| mileage 배율 | says **nothing** about him | describes **exactly** his race |
| data | **does not exist until 8/15** | already in `mileage_history.json` |

⇒ the deferred-side risk is **buildable today**; the Fall-2026 side has a date on it.

---

## 3 · DIFFICULTY IS A DIFFERENT KIND OF OBJECT — AND THE ONLY ONE WITH A FEEDBACK EDGE

Risk and quota are about **whether you get the course**. Difficulty is about **what it costs you
once you have it**. Those cannot be added into the same account.

And difficulty is the only factor that changes the *problem* rather than the score:

```
difficulty → GPA → double-major admission (Dec, on Sem 1+2 only)  → which quotas apply
                 → GPA ≥ 3.75                                     → +3 credits of capacity
```

Both edges run through Fall 2026 specifically. **This is the only genuine feedback loop in the
whole model** (R153), and the model has no difficulty axis at all — the early arm of the 학년
gap has been silently substituting for one.

### ⚠️ The elicitation problem must be solved before any question is asked
R137 forbids per-course questions, and rightly: Iden cannot rate 700 courses, and asking him to
would be offloading the modelling. So difficulty has to be a **category**, and the category has
to be designed first. Candidate carriers, in order of how much they are already known:

1. **course level** — 1000 / 2000 / 3000 / 4000 (already in the data)
2. **tier within a pool** — Iden volunteered exactly this for languages: UIC "Beginning"
   courses vs 언어와표현 courses, *"much easier"* vs *"really learning the language, pretty
   hard"* (R166)
3. **years-ahead-of-chart** — what the early arm already encodes

**Note (1) and (3) are nearly the same signal.** If they are, difficulty may need only one new
input from Iden: the tier attribute. That would be the cheapest possible resolution and it
should be tested before anything else is asked of him.

---

## 4 · THE OBJECT OF CHOICE HAS TO CHANGE — AND THIS UNIFIES PLAN A AND PLAN B

The model currently chooses a **timetable**: a set of six courses, assumed obtainable.
With acquisition risk that object does not exist. On 8/25 Iden does not choose a set — he
chooses an **order of attempts, with fallbacks**. That is a *policy*.

**Plan A and Plan B have been tracked as separate work items since the first session
(`PLANS.md` §A). They are one object.** The ranking is the policy's first branch.

### Measured today, and it sharpens this
How many courses in each top-50 timetable have a **zero-cost** fallback — same course, same
hours, different 분반, so swapping changes nothing?

| free fallbacks per timetable | count |
|---|---|
| **0** | **26 of 50** |
| 1 | 24 of 50 |
| 2+ | **none** |

**#1 (21.80) has zero.** The most robust timetable in the top 50 has one, and scores 18.49.

⇒ **Fallbacks are not free.** Almost every real fallback changes the grid and costs score. So a
policy cannot be evaluated by listing alternates (R163's display) — the degraded branches have
to be **scored**, and their probability weighed. Robustness is a real property, it varies, it
costs, and nothing in the model sees it.

---

## 5 · THE OBJECTIVE

> **value of a plan = expected utility over acquisition outcomes**

where the utility of any realised semester is the **existing** score (schedule + pool + year
gap), and the continuation is the value of the remaining degree.

Three things fall out for free, which is the test that the decomposition is right:

- **Robustness gets priced with no new term.** A plan with good fallbacks has higher expected
  value automatically.
- **Quota completion gets priced with no new term** — it is the probability the continuation is
  feasible (§2).
- **Semester-level and degree-level use one formalism**, instead of the current split between a
  scored timetable and a hand-built four-year argument.

⚠️ **The scale changes meaning.** Today's scores are "utility if you get everything." Expected
values will be lower and **not comparable to the current numbers.** Anyone comparing a v2 score
to 21.80 is making a category error — flag it loudly when the switch happens.

---

## 6 · WHAT IS ACTUALLY BUILDABLE — 15 days, seat data on the 15th

| | | when |
|---|---|---|
| **§1 availability table** | pure data, no decisions, unblocks everything | **now** |
| **§2 deferred-side risk** | from `mileage_history.json`, regime 2 only | **now** |
| **§3 difficulty carrier test** | check whether level ≈ chart-distance; only then ask Iden | **now** |
| **§2 Fall-2026 risk** | needs the seat data | **8/15** |
| **policy evaluation over the 12 families** | the actual registration-day artifact | after the above |
| full stochastic DP over the degree | out of reach before 8/25 | **after registration** |

**The honest cut:** a two-stage approximation — this registration modelled stochastically, the
rest of the degree as a deterministic feasibility check — is reachable. A full dynamic program
is not, and pretending otherwise would put the 25th at risk for a model nobody needs yet.

---

## 7 · TRAPS THIS DESIGN COULD STILL WALK INTO

1. ~~Adding risk alongside `ROLE` and `DEFER` instead of replacing them~~ — **inverted by R172.**
   The real trap was the opposite: *replacing* them would have deleted the substitutability
   signal. Test whether two measures rank the same cases the same way before merging them;
   do not argue it from the definitions.
2. **Letting difficulty become per-course questions** — R137. Design the category first.
3. **Fitting anything to reproduce an existing anchor.** R117 leaked a preference into pools
   where only structure belonged; R152 inherited the same error one level down.
4. **Conflating the two risk regimes** — R130 and R165 point in opposite directions and both
   are correct.
5. **Double-counting risk against the late arm of the year gap.** Deferring is *risky* (P of
   failing to get it) **and** *off-sequence* (a cost given you do get it). Those are genuinely
   different accounts — but check, do not assume. R119 is the precedent for exactly this
   mistake, and it survived undetected for two sessions.

---

## 8 · WHAT IDEN OWES — and not yet

Only two things, and **neither is answerable until the mechanism above exists**:

- **the difficulty tier** — once §3 has a carrier, one question, category-level
- **risk appetite** — how much score he will trade for certainty. A genuine preference, and the
  one number in v2 that cannot be measured.

Everything else in this document is data or derivation. **Do not ask him anything until §1 and
§3's carrier test are done** — the last session established that asking before the mechanism
exists produces answers that have to be thrown away (R136/R137/R141).
