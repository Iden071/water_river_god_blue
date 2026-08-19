# SPEC — Timetable Optimization

**Status:** Provisional specification v0.7  
**Stage:** Stage 4 repair in progress

This document defines what the program is supposed to do.

It is authoritative over implementation choices, old model descriptions, historical handoffs, and superseded rules. `RULES.md` remains an evidence/history archive rather than the governing specification.

The user has manually validated this specification. Material outside `SPEC.md` — including `RULES.md`, prior research notes, historical handoffs, old implementations, and interpretations of institutional documents — remains provisional until the user manually double-checks it or directly confirms the specific fact and it is promoted into this specification. Such material may identify evidence to investigate, but it must not silently override `SPEC.md` or be described as user-confirmed.

This specification is intentionally amendable. If later auditing reveals an omitted purpose, preference, constraint, or consequence, this document should be corrected explicitly before the model is changed to match it.

---

## 1. Purpose

The program exists to:

> **Optimize the user's timetable, considering both the present semester and its consequences for future semesters.**

The present and future are not separate optimization goals. They are different parts of the same timetable-planning problem.

Choosing a course now changes both the quality of the present timetable and what remains to be taken, scheduled, satisfied, or made possible later.

Therefore a course is not valuable merely because it is a requirement, major course, elective, etc. Its value comes from the consequences of taking it now rather than taking something else now and moving that obligation or opportunity into the future.

---

## 2. General Model

Conceptually, the program solves:

    maximize desirability(timetable, resulting future state)

    subject to genuine hard constraints

The present-semester timetable and its downstream consequences form one decision object.

The program must preserve the finite structure of the degree and other materially affected future opportunities. Required courses, major credits, second-major credits, residual graduation credits, Chapel, and other obligations do not disappear when omitted from the current semester; they remain in the future state.

A penalty avoided now but necessarily created later is therefore generally **relocated, not eliminated**.

The future state is broader than the remaining course ledger. When relevant and defensibly representable, it may include effects on GPA, later admission or declaration opportunities, registration standing, future eligibility, available credit capacity, and other consequences materially affected by the current timetable.

---

## 3. Hard Constraints and Preferences

This distinction is fundamental.

### 3.1 Hard constraints

A hard constraint determines whether a candidate is possible at all.

Examples include:

- institutional eligibility;
- cancellation;
- credit and graduation rules;
- genuine prerequisites or enrollment restrictions;
- time conflicts;
- physical impossibility of travelling between two classes in time;
- other sufficiently established institutional, logical, or physical restrictions.

A candidate may be removed from the feasible set only on sufficiently established grounds. An uncertain restriction is uncertainty, not a hard constraint.

### 3.2 Preferences

A preference affects desirability numerically.

Examples include:

- early starts;
- late finishes;
- holes;
- lunch or dinner disruption;
- long continuous class blocks;
- free weekdays;
- ability to go home;
- campus and travel burden;
- workload;
- course difficulty;
- professor quality;
- subject interest;
- sequencing preferences;
- other subjective costs or benefits.

Registration obtainability itself is **not** a personal preference weight. Eligibility and known registration gates are feasibility. Uncertain obtainability is a risk/contingency problem about whether a desired plan can be acquired and what fallback plans exist. It still belongs in the overall registration-planning problem, but it must not be converted into an arbitrary subjective utility coefficient merely because the optimizer needs a number.

A preference remains a preference even if its numerical weight is extremely large. A very large preference must not be silently converted into a hard constraint merely because the optimizer almost never violates it.

This distinction must remain internally consistent so future preference changes can be made without changing the structure of the feasible set.

### 3.3 User-selected scope is not automatically a hard constraint

A temporary modeling choice made to reduce search or cognitive load does not become part of the conceptual problem merely because an earlier implementation enforced it.

In particular, **six academic courses is not a conceptual hard constraint**. Credit load is the relevant dimension. Conceptually, loads from 1 credit up to the applicable 22-credit maximum may be considered, subject to the actual credit rules. Course count itself is not the governing quantity.

Nonstandard credits must be handled according to their actual rules. For example, Chapel is 0.5 credit and does not count toward the ordinary maximum-credit calculation.

---

## 4. Preference Provenance

Every subjective numerical value must trace to either:

1. explicit user input; or
2. a transparent derivation from user-supplied inputs or comparisons.

Implementation convenience is not evidence.

Missing preference information remains missing. The program must not invent a weight merely because an optimizer requires a number.

When possible, meaningful state comparisons are preferable to asking for abstract marginal weights; arithmetic differences may then be derived transparently from those comparisons.

---

## 5. Present-Semester Timetable Quality

The present timetable should be evaluated according to the user's actual lived experience, not merely occupied cells.

Relevant concepts include:

- campus presence;
- fixed-time commitments;
- registration conflicts;
- free weekdays;
- weekend-connected opportunities to be at home;
- Friday availability;
- start and finish times;
- holes;
- meals;
- consecutive class duration;
- workload;
- travel between locations.

These concepts may require different representations.

For example, an online recorded class may consume work without requiring campus presence or a fixed hour, and may behave differently again for registration-conflict purposes. The implementation must preserve such distinctions rather than collapsing every kind of occupied time into one variable.

### 5.1 Current confirmed Fall 2026 timetable preference evidence

The values below have been explicitly confirmed by the user or transparently derived from confirmed anchors. Positive values mean better; negative values mean worse.

- one weekday starting at period 1 / 09:00: **-10**;
- one weekday starting at period 2 / 10:00: **-5**;
- one four-period continuous fixed-time run: **-8**;
- missing the lunch window: **-6**;
- missing the dinner window: **-8**;
- one genuinely fixed-time-free weekday: **[+6,+8]**;
- the first weekday attached to the weekend-connected no-campus-presence run: **[+12,+14]**.

The confirmed dead-gap curve is:

    GapPenalty(l) = -10 * (l / 4)^2 = -0.625 * l^2

where `l` is the dead-gap length in periods.

The confirmed late-finish curve is:

    LatePenalty(p) = -(p - 8)^a
    a = ln(10) / ln(5) ≈ 1.4306765580733933

with the original anchors period 9 = -1 and period 13 = -10. Therefore the derived period-9..15 values are approximately:

- p9: **-1**;
- p10: **-2.6957310321**;
- p11: **-4.8151097956**;
- p12: **-7.2669657973**;
- p13: **-10**;
- p14: **-12.9802408988**;
- p15: **-16.1831088446**.

These confirmations do **not** establish a complete shape for every timetable feature. In particular, the additional utility of continuous fixed-time runs longer than four periods, the Friday-event-window bonus, and the extra value of two or more weekend-attached campus-free weekdays remain unresolved. The optimizer must preserve those missing shapes rather than silently reviving an old linear or nonlinear formula as authority.

---

## 6. Campus, Residence, and Travel

For practical timetable purposes, **국제 campus is the dorm environment**. Classes there are essentially local to the dorm: normally about a 5-minute walk and at most roughly 7 minutes.

Mixed-campus semesters are **not inherently impossible**. Their cost arises from travel, residence state, and the sequence of locations throughout the day.

Possible paths include:

- dorm/국제 → 신촌;
- home → 신촌;
- 국제 → 신촌 → home;
- other sequences created by class ordering.

A 국제 ↔ 신촌 transfer may require roughly 1.5 hours each way under favorable transportation and can be substantially worse if the preferred transport is unavailable. Home → 신촌 is also roughly a 1.5-hour trip by subway.

The model should therefore evaluate travel at the **path/transition level**, not merely attach a fixed value to a campus label.

It must distinguish:

1. **Physical feasibility** — if a transition cannot realistically be completed before the next class, the timetable is infeasible.
2. **Travel disutility** — if the transition is possible but costly in time or effort, that cost is numerical.

Campus preference should be represented as far as possible through actual residence, commuting, transitions, and lost time. A separate intrinsic campus preference may exist, but should not be introduced merely to compensate for missing travel effects.

---

## 7. Future Degree Consequences

Future semesters belong inside the timetable optimization problem.

The model should evaluate how the present choice changes the finite remaining degree.

It must conserve, where applicable:

- remaining credits;
- remaining requirement units;
- major-required units;
- major-elective units;
- second-major units;
- residual/free graduation credits;
- Chapel and similar nonstandard-credit requirements;
- campus and term restrictions;
- sequencing constraints.

The future must not be artificially filled with nonexistent courses merely to make every semester reach a preferred or maximum course count. A future semester may legitimately contain fewer courses if that is what the finite degree remainder requires.

Future timetable allocations are planning instruments used to evaluate today's choice. They are **not predictions of exact future schedules**, because future catalogues, future course availability, residence/timeline state, leaves, military service, summer use, and other conditions may be uncertain or change.

Such future timeline assumptions should therefore be explicit scenarios rather than silently fixed facts.

### 7.1 Chapel timing preference

The user's Chapel preference is **timing-specific**, not a generic intrinsic bonus attached to every Chapel whenever it is taken.

The degree requires **at least two offline Chapel passes**. The user completed **one offline Chapel pass in Spring 2026**, so entering Fall 2026 at least one additional offline pass remains required. **Freshmen are required to take Chapel offline, so any qualifying Chapel taken by the user in Fall 2026 is definitively an offline pass.** Outside the freshman context, Chapel modality must still be established by the relevant evidence rather than assumed.

The relevant reason for preferring Chapel now is that the degree requires offline Chapel passes, and completing those offline passes while the freshman/international-campus Chapel setup is appropriate is desirable. A Chapel taken now may therefore carry a real timing advantage over postponing that same obligation.

The optimizer must not interpret this as "every Chapel is worth +10 whenever taken" or duplicate the same value once in the present and again when the obligation is eventually completed. The numerical magnitude should be re-established or sensitivity-tested when the model is rebuilt.

### 7.2 Temporal weighting, future uncertainty, and recourse

The user has explicitly clarified that **intrinsic academic-semester utility is time-neutral**. Holding all other consequences fixed, +10 utility in Fall and -10 utility in a later academic semester cancel rather than receiving different weights merely because one semester is closer in time.

The earlier apparent preference for the current semester was not present bias. It came from an asymmetry of information and control:

- Fall 2026 is known much more concretely than later catalogues and schedules;
- future circumstances and preferences may change;
- future decisions can be re-optimized when better information arrives.

These facts must be represented as **epistemic uncertainty and future recourse**, not as an automatic discount on future intrinsic utility.

Likewise, irreversible downstream effects such as GPA changes, admissions or declaration eligibility, scholarships, study-abroad options, and career-relevant consequences belong in the evolving state and downstream objective. They must not be hidden inside a generic "Fall matters more" weight.

Therefore the optimizer should use equal intrinsic weights across academic semesters unless a later explicit user preference changes that conclusion, while preserving uncertainty, recourse, and irreversible state effects separately.

---

## 8. Difficulty and Workload

Difficulty and workload are legitimate parts of timetable desirability.

When defensible information exists, they should be represented numerically.

However:

    unknown difficulty != zero difficulty
    unknown workload   != zero workload

Lack of measurement must not give a course an artificial advantage.

Unknown burden may instead be:

- left unresolved;
- represented by a range;
- represented through scenarios;
- requested as user input;
- explicitly flagged.

The program must not invent difficulty or workload estimates merely to complete the model.

---

## 9. Professor Quality and Subject Interest

Professor quality and subject interest are valid preference inputs.

Their numerical values are supplied **manually by the user**.

The system may optimize using those values, but it should not independently infer a professor or subject rating from course titles, reviews, reputation, or similar material unless the user explicitly asks for such a mechanism.

Manual input means:

    user supplies value -> optimizer uses value

not:

    system invents value -> optimizer uses value

### 9.1 Current proof-safe global course envelopes

For Fall 2026 search, the user has confirmed a **neutral-zero convention** for the course-level preference dimensions below. Zero means no meaningful positive or negative effect on desirability.

The user also supplied conservative ceilings on the true best-to-worst impact span of one course:

- professor / teaching quality: **span ≤ 8**;
- workload: **span ≤ 15**;
- intrinsic subject interest: **span ≤ 3**;
- pure cognitive difficulty: **span ≤ 5**.

Workload and pure cognitive difficulty are one-sided burdens: a very light/easy course approaches 0, while additional workload or cognitive difficulty is negative. Therefore their proof-safe per-course utility envelopes are:

- workload: **[-15, 0]**;
- pure cognitive difficulty: **[-5, 0]**.

Professor quality and subject interest may be either beneficial or harmful relative to neutral. The span ceilings do not establish where zero lies inside the true range. For proof-safe branch bounds, the model may therefore use the conservative outer envelopes:

- professor / teaching quality: **[-8, +8]**;
- intrinsic subject interest: **[-3, +3]**.

These outer envelopes are deliberately looser than the user's true span ceilings. In particular, `[-8,+8]` does **not** assert that professor quality actually has a 16-point best-to-worst span, and `[-3,+3]` does **not** assert a 6-point interest span. They are admissible outer bounds derived from `min <= 0 <= max` together with `max - min <= span ceiling`, without assuming symmetry or inventing a midpoint.

These values are intended first as **proof-safe fallback bounds**, not as final per-course ratings. Missing detailed ratings may remain visibly unknown for final ranking while still being bounded for exact search pruning. A course-specific user value, when supplied, should replace or tighten the relevant fallback evidence rather than being silently averaged with it.

---

## 10. Registration Obtainability and Competition

Registration obtainability belongs conceptually inside the overall registration-planning problem rather than being merely decorative output, but the user has clarified that obtainability is **not itself a personal preference dimension**.

A high-quality desired timetable may be a poor registration plan if it is difficult to acquire and has weak fallbacks. The model should therefore distinguish:

1. **Eligibility / hard registration gates** — known prohibitions or permissions that affect feasibility;
2. **Obtainability uncertainty** — risk that an otherwise permitted section is not acquired;
3. **Fallback structure** — what strong alternative plan remains if a desired section is unavailable.

The optimizer must not ask for or invent an arbitrary utility weight for "registration difficulty." Probability estimates may be used only when supported by defensible evidence. Otherwise obtainability should be represented through ranges, scenarios, robust/fallback planning, or explicit unresolved risk.

Third-party timetable apps such as **노크** can provide useful competition signals because many students place intended courses into their schedules. Such data is not ground truth. It may be biased by:

- students who use other apps such as 에브리타임;
- students who use no timetable app;
- unequal app adoption across student groups;
- students creating multiple alternative timetables;
- duplicate or exploratory course selections;
- differences between stated interest and actual registration behavior.

Therefore app-based competition should be treated as a noisy observation with explicit uncertainty, not as literal enrollment probability unless validated.

When no reliable obtainability estimate exists, the model must preserve that uncertainty rather than fabricate certainty.

---

## 11. Registration-Day Action

The registration click order is **static within one registration attempt**.

The first registration cycle happens too quickly, and the system lags too much, for the user to observe success/failure and adapt between individual clicks. The practical sequence is approximately:

    precomputed order -> click through the whole sequence within seconds -> wait for results

After the outcome becomes visible, the program may be run again for a second cycle using the newly known state.

Therefore the program should optimize a static first-cycle click order rather than an unrealistic per-click adaptive policy.

For each desired section, the useful quantity is the best achievable result if that section is unavailable. This supports a cost-of-loss measure and the static order.

---

## 12. Second Major and Other Future Choices

An undecided second major is an uncertain future state, not a known block of generic courses.

Different possible second majors should eventually be represented as distinct scenarios with their actual:

- course requirements;
- campus structure;
- sequencing;
- credit-recognition rules;
- overlap or non-overlap with QRM;
- downstream effects on the remaining degree.

Course similarity is not sufficient evidence of cross-recognition. Credit recognition must be evaluated at the actual course/code/rule level.

### Unresolved

The rule for converting multiple possible second-major scenarios into one present-day decision is **not yet specified**.

Possible approaches might later include robustness, weighted scenarios, worst-case treatment, or presenting scenario-specific outcomes separately.

No approach may be silently chosen as the default before this is resolved.

---

## 13. Uncertainty

Unknown information must remain visibly unknown.

The program must not silently translate uncertainty into convenient point values.

In particular:

    unknown != zero
    unknown != one
    unknown != impossible
    unknown != available
    unknown != exact

Depending on the quantity, uncertainty should instead be represented by:

- scenarios;
- intervals or bounds;
- explicit unresolved states;
- flags;
- sensitivity analysis.

Approximate computations must also preserve their epistemic status.

Results should distinguish, where relevant:

- exact;
- bounded;
- truncated;
- heuristic;
- unmeasured;
- impossible.

A downstream calculation must not silently treat these categories as equivalent.

---

## 14. Search and Optimization Correctness

The returned recommendation should represent the objective actually specified here.

A candidate must not be discarded merely because it performs poorly under a different, intermediate, or older objective.

In particular, any operation of the form:

    rank by A
    keep top N
    optimize by B

requires proof that the discarded candidates cannot win under B.

Otherwise the search is incomplete.

Safe pruning should rely on dominance, valid mathematical bounds, or another demonstrated property of the actual final objective.

---

## 15. Output

The program should not merely output one unexplained score.

The primary output should be a structurally diverse ranking of strong timetable candidates.

For each relevant candidate, the system should be able to expose:

- the timetable;
- its present-semester desirability;
- degree units completed now;
- the future state/remainder it creates;
- important downstream consequences;
- manually supplied preference contributions;
- registration obtainability evidence when available;
- material uncertainty or unresolved assumptions.

### Swaps

A section replacement is a true "swap" only when substitution leaves the timetable itself unchanged under the relevant structural definition.

If changing the section changes the timetable cells, it is another timetable candidate, not a hidden swap inside the original one.

---

## 16. Non-goals

The program is not intended to:

- predict exact future university catalogues;
- manufacture preferences the user has not supplied;
- equate missing information with zero cost;
- convert strong preferences into artificial hard constraints;
- treat temporary search-scope choices as permanent truths about the objective;
- maximize an arbitrary score whose terms no longer represent the stated purpose;
- force a confident winner when available evidence does not distinguish alternatives;
- treat historical model choices as authoritative merely because they are already in code.

"Unresolved under current information" is a valid program result.

---

## 17. Specification Status

### Settled

- Timetable optimization is one present-and-future problem.
- Hard constraints determine feasibility; preferences remain numerical.
- Registration obtainability is not a personal preference weight: eligibility/gates are feasibility, while uncertain obtainability is a risk/fallback-planning problem that remains inside the overall registration decision.
- A hard constraint requires sufficiently established evidence.
- Temporary scope choices are not automatically conceptual constraints.
- Credit load, not raw course count, is the relevant load dimension.
- Future degree obligations are finite and must be conserved.
- Avoided required-course costs may merely be relocated.
- Chapel requires at least two offline passes; one was completed in Spring 2026. Freshman Chapel is offline by rule, so a Fall 2026 Chapel taken by the user supplies the remaining offline-pass minimum. Chapel also has a timing-specific preference for completing that obligation while the freshman/international-campus setup is appropriate; it is not a generic permanent per-Chapel bonus.
- Intrinsic academic-semester utility is time-neutral. Future uncertainty and the ability to re-optimize later are epistemic/recourse effects, not a present-bias discount; irreversible GPA/admissions/etc. consequences belong in state transitions.
- The currently confirmed Fall 2026 timetable anchors and derived gap/late curves are listed in §5.1; the remaining Friday, >4-period-run, and multi-attached-weekday shapes stay unresolved rather than inheriting stale RULES values.
- 국제 is effectively the dorm environment for local travel.
- Mixed-campus semesters are possible and should be modeled through actual travel paths and feasibility.
- Difficulty and workload belong in the model when defensibly represented.
- Unknown difficulty/workload must not default to zero.
- Professor and subject values are manually supplied numerical inputs.
- For Fall 2026 proof search, neutral course impact is 0; conservative true best-to-worst spans are professor/teaching ≤8, workload ≤15, subject interest ≤3, and pure cognitive difficulty ≤5. The admissible fallback envelopes are professor [-8,+8], workload [-15,0], interest [-3,+3], and difficulty [-5,0], with the two symmetric-looking outer envelopes explicitly not interpreted as the true span.
- Registration click order is static within one attempt and may be recomputed between attempts.
- Future consequences may extend beyond credits to materially affected future opportunities.
- Search must optimize the actual final objective.
- Second-major possibilities should retain their distinct structure.

### Unresolved

- How multiple possible second-major futures should be aggregated into today's decision.
- Exact travel-cost representation and residence-state model.
- How noisy third-party competition data should be calibrated into obtainability probabilities or robust scenarios.
- The additional utility shape of continuous fixed-time runs longer than four periods.
- The Friday-event-window value.
- The extra value shape of two or more weekend-attached campus-free weekdays.
- Any additional preference dimension not yet identified or elicited.
- Numerical values for preferences that have not yet been defensibly established.

### Provisional

The purpose specification is stable enough to govern Stage 4 repair, but remains amendable if repair or validation work exposes a genuine omitted purpose-level assumption.
