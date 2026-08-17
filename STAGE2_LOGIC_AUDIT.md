# Stage 2 Logic Audit

**Status:** Provisionally complete  
**Date:** 2026-08-17  
**Governing spec:** `SPEC.md` v0.3  
**Next stage:** Stage 3 — code audit against the target model

This document records the Stage 2 conceptual audit. It is not a bug list and not an implementation plan. Its purpose is to state the mathematical model the code is supposed to implement, record the major conceptual mismatches found, and preserve the unresolved assumptions that Stage 3 must not silently decide.

`SPEC.md` remains authoritative for purpose. `RULES.md` remains historical evidence. This file is the canonical record of the Stage 2 logic audit.

---

## 1. Stage 2 question

Stage 2 asked:

> **If the code were implemented perfectly, is the mathematical problem it is solving actually the problem described by `SPEC.md`?**

The answer for the current live pipeline is **no**.

The strongest idea in the current project survives: a Fall timetable should be evaluated together with the future degree state it creates. The current partition model is an important step toward that idea. However, the live state space, objective, uncertainty semantics, and degree mechanics are still materially narrower or different from the specified problem.

---

## 2. Target mathematical model

Let `x` be a present-semester timetable.

Let `ω` denote a future scenario, which may include second-major identity, future catalogue/availability, leave or military timing, summer use, residence state, and other uncertain future conditions.

For each scenario, the value of the present decision is conceptually:

    V_ω(x) = U_Fall(x) + max_{π in F_ω(x)} U_future(π)

where:

- `F_ω(x)` is the set of genuinely feasible continuations of the finite degree after taking `x`;
- `π` is a future degree/timetable plan;
- the present and future are parts of one optimization problem, not separate purposes.

Because the rule for aggregating different possible second majors is not yet specified, the system should preserve scenario-specific values rather than silently choosing an expectation, worst case, or other aggregation rule.

### Core relocation invariant

A known property of a course or obligation does not disappear merely because it is moved to another semester.

For example:

- difficulty now → difficulty later;
- workload now → workload later;
- professor effect now → expected professor effect later when defensible;
- sequencing cost can move from early to late rather than vanish;
- required credits remain required credits;
- travel occurs in whichever semester actually creates the travel;
- broader state effects such as GPA-dependent opportunities remain attached to the state transition they cause.

Avoiding a required cost now often **relocates** it rather than eliminating it.

---

## 3. State representation

### 3.1 Credit-based, not course-count based

The conceptual model is based on credits and actual institutional credit rules.

`exactly six academic courses`, `SLOTS_DEFAULT = 6`, and similar constructs are implementation restrictions, not truths about the feasible set.

Chapel and other nonstandard-credit items must follow their actual counting rules rather than being forced into generic 3-credit slots.

### 3.2 Finite degree conservation

The degree is finite. The state must conserve all remaining graduation obligations and credits.

The future must not be padded with fictional filler courses merely to make every semester contain six academic courses.

`FREE` is a residual credit amount, not a quota of generic courses.

### 3.3 Requirement alternatives retain their own properties

A requirement such as:

    MR5 = QRM3005 OR QRM3004

must not be flattened into one fictional item whose campus, term, difficulty, or availability properties are the union of both alternatives.

The same applies to Language, Science Literacy/RDQM, and any other disjunctive requirement.

Each alternative should retain its own attributes; satisfying any valid alternative discharges the requirement according to the degree rules.

### 3.4 Second major remains explicit uncertainty

An undecided second major is not twelve anonymous generic courses.

Each actual second-major possibility should eventually carry its own:

- credit requirement;
- required/elective structure;
- course identities or requirement alternatives;
- campus/term structure;
- prerequisites;
- overlap and cross-recognition with QRM;
- downstream consequences.

Until the identity is known, unknown structure should remain explicit rather than disappearing or being converted into unlimited generic filler.

---

## 4. Feasibility semantics

A plan is infeasible only when an established institutional, logical, or physical rule is violated.

Hard feasibility includes, where applicable:

- actual credit ceilings and counting rules;
- cancellation and true eligibility restrictions;
- time conflicts;
- genuine prerequisites;
- valid requirement/credit recognition;
- course-specific term/location restrictions when established;
- Chapel mechanics including its per-semester limit;
- the QRM Korean-course major-credit cap;
- mileage institutional budgets and course bid ceilings;
- physical impossibility of travelling between two in-person commitments;
- prevention of invalid duplicate or double counting.

The following are **not** conceptual hard constraints unless independently established:

- exactly six academic courses;
- exactly one deferred requirement;
- one campus per semester;
- a minimum number of whole 국제 semesters derived from that one-campus assumption;
- `MAX_OBLIG = 3`;
- an arbitrary acquisition-probability target such as 80%;
- old catalogue absence treated as permanent impossibility;
- a high numerical preference treated as a ban.

Computational limits must be reported as computational limits, not transformed into infeasibility.

---

## 5. Campus, residence, and travel

A semester should not have one global campus label.

Courses have locations. The user has a residence/context state. The relevant object is the path created by the ordered classes.

For practical purposes:

- `국제 ≈ dorm` for local movement;
- international-campus classes are normally about 5 minutes from the dorm and at most roughly 7 minutes;
- mixed-campus semesters are possible;
- a transition can be either physically impossible or merely costly.

Therefore:

    impossible transition -> hard constraint
    possible expensive transition -> numerical disutility

A blanket `SINCHON_BONUS` should not be used to compensate for a missing travel/residence model. Any residual intrinsic campus preference should only be considered after concrete travel/lifestyle effects are represented.

`MIN_INTL_SEMESTERS` is not a fundamental rule once mixed-campus semesters are allowed. Course-level restrictions such as a genuine 국제-only offering remain relevant.

---

## 6. Objective semantics

The current live objective is asymmetric: Fall contains more preference dimensions than the future.

The target model should allow the same categories of real-world consequence to exist in any semester where they occur.

Conceptually a semester may contain terms such as:

    U_schedule
    + U_travel/residence
    + U_difficulty/workload
    + U_professor/subject
    + U_sequence
    + U_other material consequences

Not every term must be measured today. Missing measurement must remain missing rather than turning into zero.

### 6.1 Present-week geometry survives

The existing distinction between:

- nominal/visible class blocks;
- fixed-time conflict blocks;
- campus-presence blocks;

is conceptually valuable and should be preserved.

The existing present-week ideas such as early starts, holes, meal disruption, long runs, late finish, true rest days, weekend-connected home trips, and Friday-event value remain valid model components where their semantics match the user's actual context.

### 6.2 Difficulty and workload

Known difficulty/workload should remain attached to a course in whichever semester it is taken.

`unknown difficulty = 0` and `unknown workload = 0` are invalid semantics.

### 6.3 Professor and subject interest

These are numerical model inputs supplied by the user.

They belong inside the optimizer. The system should not infer them automatically unless the user changes the scope.

Unrated does not mean neutral unless that is explicitly selected as a scenario assumption.

### 6.4 Sequence timing

The conceptual year/sequence preference is two-sided: taking a course too early and taking it too late can both be undesirable.

There should be one canonical source of the intended curriculum timing of an obligation/alternative rather than different modules reconstructing chart year differently.

### 6.5 Chapel timing preference

The Chapel preference is timing-specific.

The reason for preferring Chapel now is to complete required **offline Chapel passes** while the freshman/international-campus Chapel setup makes doing so appropriate. This is not a generic permanent reward for every Chapel whenever taken.

The old `+10` therefore must not be interpreted as an intrinsic reward that follows Chapel forever. The timing effect is real; its eventual numerical magnitude may be retained only if justified or re-swept under the rebuilt model.

---

## 7. Registration layer

Registration obtainability belongs conceptually inside the decision problem, but evidence quality must be explicit.

The registration sequence is **static within one attempt**. The click-click-click cycle finishes too quickly and the interface lags too much to observe one result before choosing the next click. The optimizer may be rerun after the entire first cycle once outcomes are known.

The existing leave-one-section-out quantity remains useful:

    loss(section) = best plan value with section available
                    - best plan value with section unavailable

This is a **cost-of-loss** measure.

It is not yet a complete optimal click-order model because a complete model also needs evidence about how click position and competition affect acquisition probability.

Third-party timetable-app data such as 노크 may provide a useful noisy demand signal, but it must not be treated as literal enrollment probability without calibration. Potential distortions include other timetable apps, users using multiple apps, nonusers, and users creating multiple alternative schedules.

---

## 8. Uncertainty semantics

Uncertainty must be part of the mathematical value, not merely a comment beside a float.

Conceptually the system needs values/states such as:

    Exact(value)
    Bounded(lower, upper, reason)
    Unknown(reason)
    Scenario(...)
    Impossible(reason)

The following distinctions must survive all the way to the final verdict:

- exact vs bounded;
- measured vs heuristic;
- complete vs truncated;
- unknown vs impossible;
- stale historical evidence vs documented restriction;
- eligible vs probability of obtaining;
- placeholder sensitivity value vs elicited value.

Examples of required propagation:

- an exact value plus a bounded value produces a bounded total;
- a plan that depends on an unmeasured future offering is unresolved, not automatically impossible;
- if two candidates' uncertainty ranges overlap, the program may have no proven winner;
- an approximate partition cell cannot silently become an exact whole-degree score.

The current project already has useful producer-side concepts such as `UNMEASURED`, `STALE`, `IMPOSSIBLE`, exactness flags, probability brackets, and eligibility flags. Stage 2 found that these distinctions are often discarded by downstream consumers.

---

## 9. Major conceptual mismatches found in the live model

### Stage 2A — state space

The live model currently behaves roughly like:

    exactly six academic courses now
    -> defer at most one named requirement
    -> six future semesters of six academic courses each
    -> one campus per future semester
    -> at most three named obligations per semester
    -> future ledger contains mainly items with concrete codes

This is not the specified feasible universe.

Key consequences:

- six-course count is treated as structural;
- multi-deferral/variable-load plans do not exist;
- future semesters receive fictional filler load;
- `DM` and `FREE` are lost from the live partition remainder;
- mixed-campus plans are excluded structurally;
- `MAX_OBLIG` behaves like feasibility instead of computation.

### Stage 2B — objective

Fall and future are scored under materially different semantics.

Important asymmetries include:

- difficulty present in Fall but largely absent in the future;
- professor effects present in Fall but absent in the future;
- workload missing;
- subject interest missing;
- future late-sequence cost incomplete;
- registration obtainability machinery not part of the final total;
- campus/residence effects approximated by a coarse whole-semester bonus;
- broad future-state consequences only weakly represented.

### Stage 2C — uncertainty

The repository often detects uncertainty correctly upstream and then collapses it downstream.

Examples:

- `UNMEASURED`, `STALE`, and `IMPOSSIBLE` can all become "cannot place";
- non-exact and `SCREENTRUNC` cells become ordinary numeric values in the DP;
- whole-plan exactness is not propagated;
- eligibility and obtainability are sometimes represented with the same probability-shaped interface;
- ambiguous eligibility flags can disappear from user-facing output.

### Stage 2D — degree mechanics

There is no single canonical feasibility/degree engine.

Valid mechanics exist across different generations of the code but are not jointly enforced by the live partition path.

Important mechanics to preserve or rebuild include:

- 126-credit conservation;
- residual FREE semantics;
- alternative requirements;
- actual credit caps and cap-exempt items;
- Chapel special rules;
- QRM Korean-course major-credit cap;
- mileage institutional budget and ceilings;
- genuine prerequisites/eligibility;
- leave/summer scenario structure;
- valid cross-recognition and no invalid double counting.

The older `continuation.py` contains several mechanics that the newer partition model lost. It should not be deleted before those rules are deliberately migrated or replaced.

---

## 10. Settled Stage 2 conclusions

1. The present and future are one optimization problem.
2. The finite degree/remainder is the state being transformed by a current timetable choice.
3. Credits and requirements are primitive; generic course slots are not.
4. Requirement alternatives retain their own properties.
5. Hard constraints require established evidence.
6. Preferences remain numerical even when very strong.
7. Mixed-campus semesters are possible; course-level travel paths determine feasibility/cost.
8. Known properties do not disappear when a course is deferred.
9. Unknown quantities remain explicit rather than defaulting to zero, one, impossible, or exact.
10. Approximation status must propagate to the final result.
11. Second-major possibilities remain distinct future scenarios.
12. Registration click order is static within an attempt.
13. Cost-of-loss is useful but is not by itself a complete acquisition-risk model.
14. Chapel's special value is a timing preference for completing required offline passes while the freshman/international-campus setup is appropriate.
15. Search pruning must be valid for the actual final objective, not an older or intermediate score.

---

## 11. Explicitly unresolved after Stage 2

These are legitimate unresolved model inputs, not defects to be silently filled during Stage 3:

- how to aggregate different second-major scenarios into one present decision;
- exact second-major identities/requirements until those scenarios are selected and built;
- exact travel-cost function and residence-state valuation;
- calibration of noisy 노크/other timetable-app demand into obtainability probability;
- many course workload/difficulty values;
- professor/subject ratings not yet supplied;
- future catalogue/availability uncertainty;
- numerical magnitude of any timing-specific Chapel advantage if the old +10 is not retained directly;
- any other preference value not yet defensibly elicited or derived.

Stage 3 must preserve these as unresolved parameters/scenarios rather than choosing convenient defaults.

---

## 12. Stage 3 entry condition

Stage 2 is now **provisionally complete**.

Stage 3 should not redesign the purpose again unless implementation inspection reveals a genuinely omitted purpose-level assumption.

Stage 3 asks:

> **Given the target model above, which existing modules correctly implement reusable pieces, which modules implement the wrong semantics, which constraints were lost between generations, and which dependencies/caches/search shortcuts make the current result unsound?**

The expected output of Stage 3 is a code-level dependency and correctness map, not immediate repair.

No mass deletion, file moves, expensive partition rebuild, or full rewrite should occur before that map exists.
