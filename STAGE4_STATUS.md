# STAGE 4 OPERATIONAL STATUS — 2026-08-19

This is an **operational checkpoint**, not a truth source.

Authority order remains:

1. `SPEC.md`
2. explicit current user confirmations
3. provisional evidence (official sources, `RULES.md`, prior research)
4. legacy implementation

If this file disagrees with `SPEC.md` or a later explicit user correction, **this file is wrong**.
Its purpose is to prevent workflow drift: what is frozen, what is actually blocking the next
proof step, what belongs to another model, and what must not be re-elicited merely because an
old file still says "unresolved."

---

## 1. Current objective

Build a defensible Fall 2026 timetable recommendation with a proof-safe path from the complete
catalogue to the recommendation.  The immediate engineering objective is narrower:

> make exact Fall search practical with admissible branch-and-bound while preserving every
> unresolved alternative that could still win.

Preference elicitation is **not** a goal by itself.  Ask the user only when a genuinely
load-bearing quantity remains after structural derivation, old-evidence audit, coarse safe
bounding, and sensitivity analysis.

---

## 2. Frozen — do not reopen without a contradiction

### Timetable preference facts

- period-1 start: `-10`
- period-2 start: `-5`
- four-period continuous fixed run anchor: `-8`
- late-finish curve: `-(p-8)^a`, `a = ln(10)/ln(5)`
  - p9 `-1`
  - p10 `-2.695731032073513`
  - p11 `-4.815109795572117`
  - p12 `-7.266965797284128`
  - p13 `-10`
  - p14 `-12.980240898764906`
  - p15 `-16.183108844566643`
- dead-gap curve: `-10*(l/4)^2 = -0.625*l^2`
- missing lunch: `-6`
- missing dinner: `-8`
- true fixed-time-free weekday: `[+6,+8]`
- first weekend-attached campus-free weekday trip/home component: `[+12,+14]`

### Conservative course-quality search envelopes

These are **proof envelopes, not point scores**:

- professor / teaching: `[-8,+8]`
- intrinsic subject interest: `[-3,+3]`
- workload / opportunity cost: `[-15,0]`
- pure cognitive difficulty / stress: `[-5,0]`

The raw professor rating is not required merely to bound professor utility.
Do not revive the legacy `PROF_W=10` conversion.

### Temporal objective

Intrinsic academic-semester utility is **time-neutral**.  Equal utility differences in Fall and
later academic semesters carry equal intrinsic weight.  The earlier apparent Fall preference
was information asymmetry / future recourse, not present bias.

Therefore:

- no generic Fall premium or future discount;
- future uncertainty is epistemic uncertainty, not a utility penalty by itself;
- ability to re-optimize later is recourse, modeled separately;
- irreversible GPA/admissions/scholarship/study-abroad/career effects belong in state
  consequences rather than temporal weights.

`temporal_policy.py` encodes explicit unit weights; it is not a hidden library default.

### Chapel

- at least two offline Chapel passes required;
- Spring 2026 completed one offline pass;
- at least one offline pass remains entering Fall 2026;
- freshman Chapel is offline, so a qualifying Fall 2026 Chapel is definitively offline;
- total-pass and offline-pass requirements remain separate state constraints.

### Registration interpretation

Registration obtainability is **not a personal preference weight**.

- known eligibility/year gate -> feasibility;
- unknown chance of acquiring a permitted section -> risk/contingency;
- do not invent success probabilities;
- fallback/backup structure belongs to a registration-strategy layer.

---

## 3. Structural search checkpoint

### Fall universe

Real Fall 2026 catalogue audit:

- 1,500 source observations
- 1,500 physical sections
- 7 explicit cancellations
- 1,493 searchable before freshman-gate screening
- 0 global catalogue-coverage unknowns

Registration screen (provisional evidence outside SPEC/user confirmation):

- 2 exact observed freshman-gate exclusions
- 1,491 searchable after screen
- 176 gate-resolved nonblocking
- 1,315 year-gate unresolved
- 23 unresolved-schedule overlaps

Local-hard partition:

- resolved core: 176 sections
- unresolved-family anchors: 1,315 sections

The unresolved families remain part of the proof obligation.  Searching the 176-section core
alone can never prove a global optimum.

### Exact search implementation

Available:

- exact reference powerset semantics
- resumable exact enumeration
- bitset exact backend
- checkpoint/resume
- SQLite streaming accumulator
- full model fingerprint / stale-writer protection
- exact reference parity tests

Observed core enumeration is still too large for blind exhaustive completion.  Branch-and-bound
is the next scalability dependency, not another raw-enumeration benchmark.

---

## 4. Corrected utility-blocker boundary

`fall_pruning_readiness.py` used to iterate over every preference-like placeholder in the broad
profile.  That was wrong: it both invented blockers and could miss dimensions generated
implicitly by timetable geometry.

The timetable evaluator now owns an explicit activation contract.  Course burden, Chapel
timing, registration risk, travel, and target-credit placeholders do **not** become timetable
geometry blockers merely because they share a profile object.

The late-finish contract covers every possible p9..p15 output, all of which are now derived
from the confirmed curve.

---

## 5. Nonlinear shape correction

Do **not** compress unknown nonlinear shapes into one scalar merely to make search convenient.

### Long continuous runs

For a run of 5+ periods:

- apply the confirmed four-period `-8` anchor;
- add one unresolved exact-state correction `long_fixed_run_delta_N` for the actual length N.

This is an exact reparameterization.  It assumes neither linearity nor monotonicity.

### Weekend-attached free-day run

For one attached weekday, retain the known `[12,14]` trip/home component.
For 2..5 attached weekdays, add one unresolved **total extra correction beyond the first** for
that exact attached-day count.

Do not revive one linear `weekend_run_curvature` coefficient.  The old evidence itself was
nonlinear and its exact curvature remained provisional.

Conceptually, the remaining intrinsic timetable uncertainty is still only three families:

1. Friday event-window value
2. long continuous-run shape beyond four periods
3. weekend-attached run shape beyond the first weekday

The state-specific implementation has 16 unresolved dimensions because it refuses to pretend
those two shapes are linear.

---

## 6. Two different readiness questions

### A. Complete utility readiness

Needed for exact interval ranking / final utility proof.  Current Fall complete-bound audit is
blocked by:

- registration obtainability for the 176 resolved-core sections (risk layer, not a preference);
- Friday event-window value;
- long-run state corrections;
- weekend-run state corrections.

### B. Intrinsic upper-bound readiness

Needed for deterministic Fall branch-and-bound.  This is a weaker requirement: every possible
utility contribution only needs a defensible optimistic ceiling.

`fall_upper_bound_readiness.py` now audits this separately.  It:

- automatically uses upper endpoints of exact/bounded preference evidence;
- uses the confirmed global course envelopes;
- accepts explicit one-sided proof ceilings without inventing lower bounds or point scores;
- deliberately leaves registration risk outside the intrinsic audit.

Current intrinsic upper-bound blockers are the same three conceptual timetable shape families.
Registration remains a separate proof problem for the eventual registration-strategy objective.

---

## 7. Separate models — important, but do not solve them by contaminating timetable utility

### Grades / GPA / downstream opportunities

The meaningful grade effect is downstream: admissions, scholarships, future career options,
study abroad, etc.  The user's rough central magnitude for a meaningful grade difference with
those consequences included was about 20, but no proof-safe outer ceiling has been confirmed.

Preferred architecture:

`expected grade -> GPA/state -> downstream opportunities`

Do not double-count the same effect inside professor, workload, difficulty, and a separate
"grade happiness" scalar.

### Registration strategy

A final registration recommendation should reason over acquisition uncertainty and fallbacks.
Until that layer is formalized, deterministic timetable quality and registration-strategy
quality are distinct proof claims.

---

## 8. Evidence still requiring later manual validation if load-bearing

Examples, not exhaustive:

- 1,315 missing Fall registration year-gate observations
- exact current total Chapel-pass requirement if final recommendation depends on it and it is
  not independently user/SPEC-confirmed
- unresolved second-major structures: Math / IE / CS / Applied Statistics
- retake/transcript nuances
- future catalogue assumptions
- campus/travel institutional facts
- any provisional RULES/official-source fact that becomes decisive between finalists

Do not stop the architecture to validate all of these now.  Preserve uncertainty, narrow the
candidate proof frontier, then manually validate load-bearing facts.

---

## 9. Do not ask again

Unless a contradiction appears, do not re-ask the user for:

- period-2 value
- period-14 value
- late-finish formula
- lunch / dinner values
- dead-gap formula
- professor / workload / interest / difficulty conservative search envelopes
- a Fall-vs-future preference weight
- a personal utility number for registration obtainability

Before any new preference question, first check whether the item was already derived or
elicited, whether it is actually activated by the current model, and whether a coarse one-sided
proof bound or sensitivity test can avoid the question entirely.

---

## 10. Next dependency order

1. Keep CI green after the nonlinear-state correction and upper-bound audit split.
2. Derive or sensitivity-test **one-sided optimistic ceilings** for the three remaining
   timetable shape families; provisional old formulas may be used only diagnostically, never
   as proof evidence.
3. Build a branch-specific Fall intrinsic upper-bound calculator and connect it to the bitset
   search without changing the exact candidate family.
4. Use provisional/diagnostic runs to find incumbents and determine which unresolved shape
   ceilings are actually load-bearing.
5. Only then ask the user for any remaining preference bound that changes the proof frontier.
6. Separately formalize registration strategy/fallback risk, then combine it with deterministic
   timetable candidates without inventing probabilities.
7. Resolve/validate future and institutional evidence that survives into the final frontier.
8. Run the final exact/proof-safe search and manually audit the winner(s).

---

## 11. Claim discipline

Never say "global optimum" merely because:

- the 176-section resolved core was exhausted;
- a top-N shortlist was exhausted;
- provisional preference points gave a stable winner;
- unresolved registration families were omitted;
- future opportunity sets were historical analogues rather than complete scenarios.

A global claim requires complete search coverage or a proof-safe exclusion/bound for every
omitted alternative, plus an objective whose decisive evidence is authoritative enough for the
claim being made.
