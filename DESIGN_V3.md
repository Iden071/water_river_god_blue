# DESIGN v3 — RETHINKING V

**2026-08-10. Paper stage. Nothing built.**
Supersedes nothing yet; `DESIGN_v2.md` is a different document about risk/difficulty/quotas.
Read `PURPOSE_CHECK_2026-08-10.md` first — this builds on its measurements.

---

## 0 · THE MEASUREMENT THAT FORCES A REDESIGN

V has three scoring terms. I switched each off and re-ranked all 7,200 candidates.

| variant | #1 defers | margin | branch order |
|---|---|---:|---|
| **A** current: crowding + year-gap + campus | **MR** | 2.288 | MR > Lang > WCiv > SciRD > LHP > – |
| **B** campus bonus removed | **MR** | 2.288 | MR > Lang > WCiv > SciRD > LHP > – |
| **C** crowding removed | **Lang** | 7.450 | Lang > SciRD > WCiv > LHP > MR > – |
| **D** year-gap only | **Lang** | 2.196 | Lang > MR > SciRD > WCiv > LHP > – |
| **E** V flat (feasibility only) | **Lang** | 2.196 | Lang > MR > SciRD > WCiv > LHP > – |

Three facts, each exact:

1. **A ≡ B.** The campus bonus — `SINCHON_SEMESTER_VALUE = 96.0`, contributing +480.000, the
   largest constant in the model — changes **nothing**. Same winner, same margin to three
   decimals, same branch order.
2. **D ≡ E.** The future year-gap changes **nothing about the branch order** either.
3. **A ≠ C.** Removing crowding flips the answer from *defer Intro to QRM* to *defer Language*.

> **The four-year layer has three terms. Two are provably inert. The one that decides
> everything is the one with the worst evidence in the project:** a curve measured on the
> Fall 2026 국제 catalogue and applied to 신촌 semesters in 2029 (G-9), gated by
> `LOW_SUPPLY_MAX = 40` — a threshold `continuation.py:185` itself flags as
> *"never justified or swept"* — under which every ledger item except free electives counts
> as scarce, so the term reduces to **a count of non-free courses per future semester**.

That is R208's condemned statistic, deciding the registration.

### A failed idea, recorded so nobody retries it
I first proposed replacing "value of the best future plan" with **flexibility** — how many
futures survive the choice, counted over documented constraints only, needing no catalogue and
no proxy. Measured over the 12 reachable states:

| measure | distinct values over 12 states |
|---|---:|
| current ΔV | 7 |
| feasible campus patterns | **3** |
| tightest item's legal-slot count | **1** |

**It discriminates worse, not better.** With 29 units into 36 slots and most items
campus/term-flexible, feasibility is loose: deferring MR, Lang, LHP or SciRD leaves
structurally *identical* futures. Flexibility is the right instinct and the wrong instrument
here — the degree is not close enough to infeasible for its slack to carry a signal.

**But the negative result is itself informative:** if the deferrals are structurally
equivalent, then V's confident 7-bucket discrimination between them is not measuring
structure. It is measuring the proxy.

---

## 1 · IDENTIFY THE STRUCTURE

**Objects.** A decision epoch $t \in \{1,\dots,7\}$ (Fall 2026 = 1). A state
$s_t = (\rho_t, y_t, \tau_t)$: the remaining-requirement multiset, academic year, term parity.
An action $a_t$: a set of ≤6 courses drawn from that term's catalogue $\mathcal{C}_t$.
A reward $r(a_t \mid \mathcal{C}_t)$: the week score, measured in real hours.

**What changes.** $\rho$ shrinks; $y,\tau$ advance deterministically.

**What is preserved.** The degree ledger — every unit must land somewhere.

**What is uncertain.** $\mathcal{C}_2,\dots,\mathcal{C}_7$ — the future catalogues. **Nobody
has them.** Also $\rho$ itself: `DM` is 12 units (36 credits, the largest single block of the
remaining degree) whose identity is not decided until December.

**The type of thing this is.** A finite-horizon sequential decision problem with a **known
constraint structure** and an **unknown reward kernel**. The current model treats it as a
one-shot optimisation by collapsing the tail into a scalar $V$.

> **The collapse is where the information dies.** $V = \max$ over placements of a *proxy*
> reward, on catalogues nobody has, for a ledger that is 30% placeholders. A scalar cannot
> carry its own error bar, so a term with an unknown sign gets added to a term measured in
> real hours, and the sum is reported to three decimals.

---

## 2 · CHOOSE THE FRAMEWORK

Not dynamic programming — that needs the transition kernel.
Not expected utility — that needs a distribution over $\mathcal{C}_t$ that cannot be estimated
from one term of data.

**Robust satisficing** (info-gap / ε-constraint). Formally, replace

$$x^\star = \arg\max_x \Big[\, r(x) + V(\rho(x)) \,\Big]$$

with

$$x^\star = \arg\max_{x \in \mathcal{X}} \; r(x)
\qquad \text{s.t.} \qquad \Phi\big(\rho(x)\big) = 1 \ \ \forall\, u \in \mathcal{U}$$

where $\Phi$ is degree-feasibility and $\mathcal{U}$ is the uncertainty set over futures.
**The future stops contributing points and starts removing candidates.**

This dissolves R208/R209 at the root: the boundary between "real hours" and "counted items"
is never crossed, because nothing on the far side of it is ever added to anything on the near
side. There is no unit mismatch left to bias.

### The decision statistic that replaces V

We still owe an answer on deferral, and feasibility alone does not give one. So instead of
computing a congestion cost we cannot measure, compute **how large it would have to be to
matter** — and compare that against how large it could plausibly be.

For a candidate $x$ deferring $n(x)$ requirements, define the **robustness margin** $k^\star(x)$:

$$k^\star(x) = \sup\Big\{\, k \ge 0 \;:\; x = \arg\max_{x'} \big[\, r(x') - k\, n(x') \,\big] \Big\}$$

$k$ is the per-deferred-course congestion cost — the one quantity V is really trying to
estimate. $k^\star$ is the largest value of it under which $x$ still wins.

**A candidate is robust iff $k^\star(x) > \bar{k}$**, where $\bar{k}$ is the upper end of the
plausible range for $k$.

Measured today:

| | |
|---|---:|
| $k^\star$ for the live #1 (defers MR) | **11.029** |
| $\bar{k}$ from R209's isolated measurement | **≈ 24** |
| $k^\star$ for any non-deferring candidate | **$\infty$** (no term applies) |

> **#1 is not robust.** It survives less than half the error its own documentation records.
> The non-deferring branch is robust by construction — it is the only one on which the broken
> term has no purchase.

Note what this buys: $k^\star$ is **computable exactly** from the existing ranking with no new
model, no future catalogue, and no proxy. It is a property of the candidate set, not of a
guess.

---

## 3 · BUILD THE MODEL

$V$ is deleted. In its place, four separately-reported quantities. **None of them is summed
into the ranking score.**

### Φ · FEASIBILITY — a hard filter
$$\Phi(\rho) = \mathbb{1}\big[\exists \text{ a legal assignment of } \rho \text{ into } \Sigma\big]$$
Constraints: one campus per semester · a 국제 Spring exists (QRM3003) · ≥2 국제 semesters ·
≤6 courses and ≤1 chapel per semester · ≤4 Korean ME at 신촌 · the 72-point mileage budget.

Every constraint is a **documented fact**, not a proxy. This is the most trustworthy thing
`continuation.py` computes and it survives the redesign unchanged. Candidates with $\Phi=0$
are dropped, not penalised.

### Π · CAMPUS — an invariant, checked and asserted
$$n_{신촌}(\rho) = 5 \quad \text{for every reachable state}$$
Verified over all 12. R126 said it in prose — *"π = 5, INVARIANT over every possible Fall-2026
timetable"* — and the code spent 96.0 points on it anyway. **Becomes a `test_retired.py`
assertion**: if any candidate ever reduces $n_{신촌}$, fail loudly. It is worth everything
he said it is worth, and precisely because it cannot be lost, it should cost nothing.

### Γ · SEQUENCING — a reported term, exact
$$\Gamma(\rho) = \sum_{u \in \rho} \pi\big(y(\sigma^\star(u)),\, y_{\text{chart}}(u)\big)$$
Year-gap of each deferred unit in its earliest legal semester. Weights elicited (R145/R146),
arithmetic exact. Currently inert for branch ordering (D ≡ E) but **keep it** — it is correct,
cheap, and becomes live the moment the optimum moves. Report it; do not add it.

### K · CONGESTION — an interval, never a point
The real quantity: deferring $u$ into semester $\sigma$ degrades $\sigma$'s week. This is
`DECISIONS_NEEDED` B-1, the one build that was never completed, and it is unmeasurable
without $\mathcal{C}_\sigma$.

**Do not estimate it. Bracket it.** Report $k^\star(x)$ against a stated interval
$[\underline{k}, \bar{k}]$, and mark every candidate:

| condition | verdict |
|---|---|
| $k^\star > \bar{k}$ | **robust** — the congestion cost cannot change this |
| $\underline{k} < k^\star \le \bar{k}$ | **contingent** — the answer depends on an unmeasured quantity, say so |
| $k^\star \le \underline{k}$ | **dominated** — do not recommend |

Per R190, when reporting, take the arm that argues **against** the incumbent.

### The ranking rule
$$\text{rank by } \; r(x) = \underbrace{w(x)}_{\text{week, real hours}} + \underbrace{\textstyle\sum\pi}_{\text{this term's year gaps}} + \underbrace{\kappa}_{\text{chapel}} + \underbrace{\delta}_{\text{difficulty}}$$

subject to $\Phi = 1$ and $n_{신촌} = 5$, with $\Gamma$ and $k^\star$ reported alongside every
row. **Every term in the ranking score is now measured in the same currency and traces to
something Iden said.**

---

## 4 · DERIVE CONSEQUENCES

**C1 · The scale becomes meaningful.** The score loses the +480 campus constant and the
$V(\rho_0)$ reference offset. `fast_score(0,0,0) = 163.071` (the empty week) becomes a real
ceiling instead of an arbitrary anchor at an unreachable state (`PURPOSE_CHECK` §6-F).

**C2 · The deferral becomes an explicit, surfaced choice.** Today it is decided silently by
`LOW_SUPPLY_MAX = 40`. Under v3 it is presented as: *these candidates defer nothing and are
robust; these defer one requirement and win only if congestion is below 11.0.*

**C3 · A prediction that can falsify this design.** Under variants D and E — which is what the
v3 ranking reduces to on the current candidate set — **#1 defers Language, not MR**, at a
margin of 2.196 over MR. So v3 does *not* trivially reproduce "defer nothing". If the
congestion interval's lower end $\underline{k}$ exceeds 2.196, defer-Language dies too and the
non-deferring branch takes over. **The design's own recommendation is therefore contingent on
one number, and it says so instead of hiding it.** That is the whole point.

**C4 · The 동영상 loophole (R218) is untouched.** Workload remains unpriced, so a course
with `fm = 0` still costs nothing. v3 does not fix this. It is orthogonal and must be flagged,
not silently inherited.

**C5 · V_SIM and POWERSET become coherent again.** The blocking defect (HANDOFF §6) was that
simulated V collapsed to a step function. Under v3 nothing is simulated into a score, so the
defect stops being blocking. The machinery stays off, but it stops holding anything hostage.

---

## 5 · EVALUATE — where this breaks

**Honest weaknesses:**

- **It answers a narrower question.** v3 will not tell him the optimal four-year plan. It
  tells him which Fall 2026 timetables do not foreclose one. That is less than the current
  model *claims* and roughly equal to what the current model *delivers*.
- **$\bar{k}$ is one measurement (R209, isolated, on QRM1001).** The whole robustness verdict
  rests on it. It should be re-measured on at least two more requirements before being quoted.
- **Feasibility is loose** (§0), so $\Phi$ will rarely bind. Most of the work is done by the
  ranking, i.e. by this semester. Someone will object that the four-year layer has been
  effectively deleted. **That objection is correct, and it is the finding, not a side effect.**
- **`DM` is still 12 unidentified units.** v3 does not fix the ledger; it stops the ledger's
  emptiness from propagating into a score. After December, the ledger can be filled and a
  simulated V reconsidered on its merits.
- **Lexicographic filtering hides trade-offs.** A candidate barely failing $\Phi$ under one
  pessimistic future is discarded outright. With $\Phi$ this loose it should not bite, but it
  must be reported when it does.

**What it captures well:** it never adds an unmeasured quantity to a measured one; every
ranking term is in one currency; the unmeasured quantity is quantified as *how wrong it would
have to be*, which is computable exactly; and it is buildable in days, not weeks.

---

## 6 · EXTEND

- **Post-December**, with `DM` resolved to real course codes, `continuation_sim.py` can score
  future semesters over real sections at real hours — the same currency as Fall 2026 — and
  $K$ can graduate from an interval to a measurement. The code exists and is off.
- **$\bar{k}$ by direct measurement:** for each requirement, place it in its earliest legal
  semester and score that semester's best achievable week over the Fall 2026 국제 catalogue as
  an explicit stand-in. `semester_sim.py` already does this and is off by default. This is
  B-1, finally, and it converts $\bar{k}$ from one isolated number into five.
- **Seat data (8/14)** enters as a further restriction on $\mathcal{U}$ — a section with
  `sy1PercpCnt = 0` removes futures, which is exactly the shape $\Phi$ already takes.
- **Workload** (C4) is the largest genuinely absent term and is independent of all of this.

---

## 7 · WHAT WOULD BE BUILT

| # | change | file | effort |
|---|---|---|---|
| 1 | delete the campus bonus from the score; assert $n_{신촌}=5$ instead | `continuation.py`, `test_retired.py` | small |
| 2 | drop crowding from the score; report $\Gamma$ and $\Phi$ only | `continuation.py`, `rank4.py` | small |
| 3 | compute $k^\star$ per candidate and per branch | new, ~40 lines | small |
| 4 | re-measure $\bar{k}$ on all five requirements via `semester_sim` | `semester_sim.py` (exists, off) | medium |
| 5 | shortlist columns: $\Gamma$, $k^\star$, robust/contingent/dominated | `render_top50.py` | small |

Steps 1–3 and 5 are days. Step 4 is the only real build, and it is the one that decides
whether "defer Language" survives.

**Nothing here requires the December decision, the seat pull, or a new elicitation.**
