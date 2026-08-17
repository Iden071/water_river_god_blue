# Stage 3 Implementation Audit

**Status:** Provisionally complete  
**Date:** 2026-08-17  
**Governing spec:** `SPEC.md` v0.3  
**Previous stage:** `STAGE2_LOGIC_AUDIT.md`  
**Next stage:** Stage 4 — repair, dependency layer at a time

This document is the canonical record of the Stage 3 code audit. It classifies the existing implementation against the target model established in `SPEC.md` and `STAGE2_LOGIC_AUDIT.md`.

It is not a repair commit, not a cleanup plan, and not a claim that the current recommendation is trustworthy. `SPEC.md` remains authoritative for purpose; `RULES.md` remains historical evidence.

---

## 1. Stage 3 question

Stage 3 asked:

> **Given the target model from Stage 2, which existing implementation pieces are reusable, which encode the wrong semantics, and which dependencies/caches/search shortcuts make the current result unsound?**

The answer is mixed.

The repository contains substantial reusable domain knowledge and several good algorithmic ideas. However, the current live pipeline does not implement the Stage 2 model end-to-end. The largest problems are structural rather than local: data construction has hidden side effects, degree recognition has multiple authorities, Fall search optimizes/prunes under an intermediate objective, the future partition uses a six-course/one-campus state that drops large parts of the degree, and uncertainty metadata is frequently discarded by downstream consumers.

The historical `defer Language / 352.569` result should therefore be treated as an incumbent produced by a superseded model, not as a verified recommendation under `SPEC.md`.

---

## 2. Target dependency direction for the repair

Stage 3 establishes the following desired dependency direction:

    canonical data
        -> degree / recognition state
        -> utility + evidence modules
        -> future continuation solver
        -> Fall search on the same final objective
        -> registration / output consumers

No downstream layer should define or patch upstream semantics.

In particular:

- renderers must not score or filter candidates;
- registration code must not redefine the optimizer;
- search code must not own degree-recognition dictionaries;
- importing a parser must not mutate generated files;
- cache keys must be derived from complete input provenance rather than selected hand-written knobs.

---

## 3. Stage 3A — shared data and ledger layer

### 3.1 `build_canonical.py`

**Classification:** keep parser ideas, replace pipeline architecture.

Reusable:

- segment-level time parsing;
- distinction between in-person, live online, recorded non-overlap, and freely overlappable video;
- construction of separate conflict/presence semantics.

Problems:

- importing `build_canonical` can write `canonical_2026F.json` because data rewriting occurs at module top level after the `__main__` block;
- the canonical dataset is restricted to 국제 and therefore cannot be the shared cross-campus representation;
- rows with no listed time are discarded rather than represented as no-fixed-time sections;
- malformed time/room segment alignment may be guessed rather than surfaced as uncertainty.

**Repair requirement:** library imports must be pure/read-only. Generated data is written only by an explicit build command.

### 3.2 `pools_past.py`

**Classification:** split historical evidence from old generic-filler semantics.

Reusable:

- historical-term access;
- course offering observations;
- geometry evidence after parser repair.

Problems:

- historical presence parsing does not consistently use the actual room/delivery segment and can misclassify recorded/live-online hours;
- historical geometries are later collapsed too aggressively;
- generic anonymous future filler pools should not represent the finite degree.

### 3.3 `fm_fix.py`

**Classification:** retire after migration.

The segment-level fixed-hour correction is conceptually correct, but it exists because the underlying builder cannot safely be edited. Its logic should move into canonical ingestion so every consumer receives correct `tm`, `pm`, and `fm` directly.

### 3.4 `rank3.build()` source execution

**Classification:** retire.

`rank3.build()` opens `rank2.py` as text and executes only its prefix up to a literal marker. This creates hidden dependencies on formatting, working directory, and source layout, and is the reason later fixes are applied as runtime mutations.

The rebuilt pipeline must use ordinary imports and explicit data construction.

### 3.5 `plan_model.py`

**Classification:** preserve verified facts; replace state structure.

Useful facts include 126-credit conservation, completed credits, known QRM requirements, Chapel counts/rules, residual FREE intent, and leave/summer concepts.

The current structure embeds obsolete assumptions such as:

- `CREDIT_CAP = 18`;
- `SLOTS_DEFAULT = 6`;
- whole-semester campus state;
- `MIN_INTL_SEMESTERS`;
- flattened disjunctive requirements.

`ledger_check()` is a useful arithmetic invariant, but must be evaluated inside explicit degree scenarios rather than after assuming `DM = 36` and making FREE absorb the remainder.

### 3.6 Recognition has multiple authorities

**Classification:** replace with one canonical recognition function.

Requirement/course classification is duplicated across `rank2.py`, `rank4.py`, `defer_value2.py`, `partition_verdict.py`, and related files.

The rebuilt model needs one authority of the form:

    recognition(section, degree_scenario) -> valid degree-state effects

This authority must handle QRM requirements, seminars, free credits, second-major scenarios, valid overlap, and no invalid double counting.

---

## 4. Stage 3B — Fall candidate search

### 4.1 Search-space architecture

**Classification:** replace.

`research_v3.py` searches:

    exactly six academic courses
    x zero or one deferred named requirement

This does not represent the credit-based feasible set specified in Stage 2. Multi-deferral and variable-load plans should emerge from selected sections rather than branch names.

### 4.2 Branch-and-bound objective mismatch

**Classification:** current bound cannot certify the final objective.

The recursive pruning bound is a bound on the Fall score. The final comparison later adds a continuation value that depends on the remainder created by the Fall timetable.

Therefore a partial timetable with a lower Fall ceiling but a much better future state can be pruned before its future advantage is evaluated.

This remains true even if `TOPN` were infinite.

### 4.3 `TOPN` truncation

**Classification:** retire as a correctness-critical step.

After the Fall-only search, each branch retains a Fall-score-ranked prefix and the partition verdict later maximizes `Fall + future` only over those stored rows.

This is another `rank by A -> retain N -> optimize by B` pipeline without a proof that discarded candidates cannot win B.

Top-N is acceptable only after the actual final objective has been evaluated, for presentation.

### 4.4 Signature compression

**Classification:** preserve the idea, rebuild the equivalence relation.

Current elective signatures collapse sections on timetable masks, one numerical bonus, credits, and one coarse ledger item. The search then uses the union of all course codes in a signature as though every represented code were chosen, while output often selects the first representative.

This can both remove legal combinations and reconstruct the wrong concrete section.

The rebuilt compression may collapse alternatives only when they are equivalent on every property relevant to the final objective/state, and must preserve concrete compatible alternatives and multiplicity.

### 4.5 Credit pruning

**Classification:** replace slot-based assumptions.

The recursion contains a lower-bound assumption of `3.0 * remaining slots` even though lower-credit OPEN courses can exist. More broadly, credits should be tracked directly rather than inferred from a fixed number of nominal 3-credit slots.

### 4.6 Fall cache

**Classification:** rebuild provenance.

The branch-cache stamps improved over earlier versions, but still do not fingerprint all relevant inputs. For example, professor cache identity can depend on the count of ratings rather than the actual rating contents.

---

## 5. Stage 3C — future partition implementation

### 5.1 Partition concept

**Classification:** keep the idea, replace the state representation.

The central idea survives:

> condition on the Fall-created remainder and solve the best feasible continuation.

Dynamic programming/memoization over a correctly represented future state remains a suitable algorithmic family.

### 5.2 DM/FREE disappear

**Classification:** foundational defect.

`partition.table_items()` includes only ledger items with concrete course codes. Anonymous `DM` and `FREE` therefore disappear from the live future state, removing a large block of degree credits.

The missing load is implicitly replaced by anonymous filler courses.

### 5.3 Six fictional academic courses per semester

**Classification:** retire.

The cost table is built around `best_week(pins, 6 - |pins|, pool)` and an empty semester still receives a six-course filler baseline.

This violates finite-degree conservation and prevents legitimate light semesters.

### 5.4 Weekend/free-item slot bug

**Classification:** concrete implementation bug in the old architecture.

The `free_items` adjustment can produce seven academic filler slots when Chapel has a free/weekend geometry. A no-weekday-cost course also does not imply zero credits or zero academic load.

### 5.5 One campus per semester

**Classification:** retire.

`partition_solve.py` chooses one of `국제` or `신촌` for an entire semester and counts whole 국제 semesters. Mixed-campus timetables are impossible by construction.

The replacement must assign locations to actual courses and compute travel/path feasibility and disutility.

### 5.6 `SINCHON_BONUS`

**Classification:** retire as a structural patch.

A blanket per-semester bonus is compensating for missing residence/commuting/path semantics. The repair should model those underlying consequences directly before considering any residual intrinsic campus preference.

### 5.7 `MAX_PIN` / `MAX_OBLIG`

**Classification:** computational limits incorrectly acting as feasibility.

The table/DP only evaluate up to three named obligations per semester. The inability to evaluate four is not an institutional rule.

A future computational cap must produce truncated/unresolved status, not impossibility.

### 5.8 Cost-table approximation

**Classification:** unsafe exactness semantics.

Problems include:

- `PRODUCT_CAP` can truncate raw placement products without recording that truncation;
- cheap screening ranks placements using values whose searches may themselves be incomplete;
- `completed` status from the screening search is discarded;
- a surviving placement may be solved exactly even though better discarded placements were never bounded, yet the cell can still be marked exact.

### 5.9 Solver discards uncertainty metadata

**Classification:** replace scalar table interface.

`partition_solve.table()` consumes numeric values but discards exactness/verdict status. `UNMEASURED`, `STALE`, and `IMPOSSIBLE` all become effectively unplaceable because only `OK` transitions are admitted.

The replacement continuation solver must propagate structured exact/bounded/unknown/impossible states to the whole-plan result.

### 5.10 Year semantics

**Classification:** centralize.

`partition_solve.item_year()` reconstructs chart year from codes and defaults missing values to year 1, despite `plan_model` already storing chart-year information. The DP also prices early placement but not late placement.

One canonical sequencing function should be used everywhere.

### 5.11 Historical future geometry

**Classification:** rebuild after parser migration.

Future geometry currently reduces evidence to `(tm, pm)` and can key geometries only by rendered time mask, losing distinct presence/fixed-time behavior. The future solver should use the same canonical `tm/pm/fm` semantics as the Fall scorer.

### 5.12 `b1_curve.best_week()`

**Classification:** salvage algorithmic pieces.

Useful ideas include strong feasible incumbents, branch-and-bound, free-day-pattern decomposition, proven upper bounds, and explicit completion status.

These should be reused only after the candidate representation is rebuilt around actual sections/alternatives rather than anonymous fillers.

### 5.13 Do not rebuild the old 1,640-cell table

The committed `partition.json` is partial, while `build_sinchon.py` expects a 1,640-cell old-model table and advertises a long rebuild.

Because that table encodes the superseded six-course/one-campus state, the expensive rebuild should not be run before the new model exists.

---

## 6. Stage 3D — utility, evidence, eligibility, and risk

This is the strongest reusable layer.

### 6.1 Timetable geometry scorer

**Classification:** keep/refactor.

The distinction among:

- `tm` — registration-conflict/nominal time;
- `pm` — campus presence;
- `fm` — genuinely fixed personal time;

is valuable and should become part of the canonical section representation.

Early starts, late finishes, meals, holes, long runs, rest days, and weekend-connected home opportunities remain useful preference components where they match the residence context.

The current `week_value()` is specifically tied to the Fall 국제-dorm context and must not be reused as a universal future-semester residence model.

### 6.2 Preference provenance

**Classification:** make status explicit.

The repository already documents differences among elicited, provisional, and contradictory/swept weights. The rebuilt utility layer should represent that status in data rather than exposing all values as ordinary constants.

### 6.3 Difficulty

**Classification:** keep category architecture; replace unknown default.

Language easy/hard categories and the elicited language-difficulty comparison are useful.

`steps(course) -> 0` for every unmeasured course is invalid because known baseline difficulty and unknown difficulty become indistinguishable.

### 6.4 Professor

**Classification:** keep manual-rating architecture.

Manual professor ratings, unrated sensitivity arms, and search-time integration are aligned with SPEC.

`PROF_W = 10` remains a provisional conversion factor rather than an authoritative preference value.

Professor persistence is a legitimate relocation question but should be re-estimated after the historical data layer is repaired.

### 6.5 Eligibility

**Classification:** keep core, strengthen provenance.

Good mechanics include cancellation, optional per-year quota logic, absence-of-data discipline, and keeping ambiguous restrictions as flags.

Free-text regex exclusions should carry explicit evidence/verification provenance rather than becoming hard truth merely because a pattern matched.

Eligibility flags must travel with candidate sections through output rather than being discarded after pool filtering.

### 6.6 Registration risk

**Classification:** keep mechanics/brackets, separate APIs.

Mileage budget/ceiling rules and empirical probability brackets are useful.

Fall `p_get_freshman() = 1` currently means "not barred", not a true acquisition probability. The rebuilt layer should have separate interfaces for:

    eligibility -> allowed / impossible / unresolved
    obtainability -> estimate / interval / unknown

Empirical mileage brackets should retain provenance as historical evidence rather than be presented as exact statistical probability bounds.

### 6.7 Subject interest

**Classification:** missing.

A manual subject/course-interest input mechanism still needs to be added. No automatic inference should be introduced.

---

## 7. Stage 3E — integration, outputs, caches, tests

### 7.1 Current "FINAL" result is not clean-clone reproducible

`INDEX.md` describes `partition.json` as a complete 1,640-entry table and presents `defer Language / 352.569` as final. The committed `partition.json` inspected during Stage 3 contains only 13 cost cells.

A clean clone therefore does not contain the data needed to reproduce the documented final continuation even under the old model.

The documented result is historical, not a current proof.

### 7.2 `INDEX.md`

**Classification:** eventually replace with a small current-state entry point.

It mixes historical generations and a live pipeline that no longer fully matches the actual cross-import structure. `SPEC.md` remains authoritative.

### 7.3 Partition verdict integration

`partition_verdict.py` calls its optimization joint, but the candidate universe has already been generated/pruned by the Fall-only search. It is joint only conditional on that stored subset.

### 7.4 Registration cost-of-loss

**Classification:** keep concept, recompute with true reoptimization.

`partition_clickorder.py` correctly computes leave-one-section-out cost, but searches only stored Fall rows. If exclusion makes a previously pruned timetable optimal, current loss can be overstated.

The replacement must rerun or query the true optimizer under section exclusion.

### 7.5 Renderer boundary

**Classification:** presentation only in the rebuild.

`render_v3_top50.py` currently removes zero-fixed-hour candidates as a workload guard and reconstructs partial scoring for swaps. Presentation code must not change the feasible set or own scoring logic.

### 7.6 Cache/provenance

**Classification:** replace with content-addressed provenance.

Current cache keys have fixed several historical bugs but still omit material epistemic/input information. For example, the future table fingerprint emphasizes numeric cell values rather than complete status/provenance.

Every generated artifact should record/hash the complete relevant inputs: source data, model/config version, preference inputs, scenario inputs, and uncertainty/exactness state.

### 7.7 Tests

**Classification:** preserve regressions, build a new zero-failure suite.

`test_partition.py` captures valuable historical failures, but many assertions are coupled to the partition architecture being retired. `test_v3.py` intentionally contains expected broken assertions and is therefore an audit notebook rather than a clean correctness gate.

The rebuilt suite should have no expected failures and test at least:

- finite credit conservation;
- no phantom degree units;
- Chapel credit/cap semantics;
- arbitrary valid Fall credit loads;
- requirement-alternative properties;
- mixed-campus feasibility and travel impossibility;
- no invalid duplicate/double counting;
- two-sided sequencing semantics;
- unknown availability remains unknown;
- approximate continuation makes the whole result approximate;
- safe dominance when future-relevant state is equal;
- cache invalidation when any relevant input changes;
- section exclusion triggers true reoptimization;
- renderers do not alter scoring/feasibility.

### 7.8 Dependency/cleanup implication

The root directory still mixes current code, legacy code, generated outputs, data, audit documents, and historical artifacts. Hidden source execution and runtime patching mean cleanup now would risk deleting still-imported evidence or functionality.

Cleanup remains Stage 6, after dependencies are rebuilt explicitly.

---

## 8. Keep / modify / replace / retire summary

### Keep or salvage

- verified domain facts and institutional evidence;
- canonical segment-parser ideas;
- `tm/pm/fm` semantics;
- timetable preference formulas with provenance;
- manual professor-rating architecture;
- language-difficulty category evidence;
- eligibility hard-rule/flag distinction;
- mileage institutional mechanics and empirical brackets;
- branch-and-bound techniques with proven bounds;
- dynamic programming/memoization as a future-solver technique;
- leave/summer scenario concept;
- regression tests for historical bugs where still meaningful.

### Replace structurally

- canonical data build pipeline;
- degree requirement/scenario representation;
- course-to-requirement recognition authority;
- Fall search state and final-objective bounds;
- future continuation state;
- uncertainty/value type system;
- cache/provenance layer;
- renderer/optimizer boundary;
- clean correctness test suite.

### Retire after migration

- `rank3` source-splicing;
- runtime `fm_fix` patching;
- exactly-six/one-deferral search architecture;
- Fall-score TOPN before future evaluation;
- anonymous six-course future filler model;
- one-campus-per-semester DP;
- `SINCHON_BONUS` as compensation for missing travel;
- `MAX_OBLIG=3` as feasibility;
- legacy K/V/crowding pathways as active decision logic;
- scoring/filtering logic inside renderers.

Legacy files should remain untouched until their useful facts/tests are migrated and dependency removal is proven.

---

## 9. Stage 4 repair order

Stage 4 should proceed dependency-first and test-first:

1. **Repair branch + foundational tests.** No expensive rebuilds; no mass deletion.
2. **Pure canonical data layer.** One parser, cross-campus Section representation, `tm/pm/fm`, no import-time writes, explicit source/provenance fields.
3. **Degree-state/recognition layer.** Credits, requirements, alternatives, Chapel, recognition/overlap, residual credits, second-major scenarios, future calendar.
4. **Utility/evidence layer.** Timetable geometry, residence/travel, difficulty, professor, subject interest, eligibility, registration risk, structured uncertainty.
5. **Finite future optimizer.** Actual degree remainder, actual credit loads, course-level locations, uncertainty propagation.
6. **Fall search on the same final objective.** Safe dominance or valid whole-objective bounds only.
7. **Registration/output consumers.** True exclusion reoptimization, static cost-of-loss, renderers as pure consumers.
8. **Content-addressed provenance/caches, validation, expensive recomputation.**
9. **Cleanup only after dependency graph is explicit and tests pass.**

Each layer should become trustworthy before downstream layers are migrated onto it.

---

## 10. Stage 4 entry condition

Stage 3 is **provisionally complete**.

No additional user preference decision is required to begin the repair.

Stage 4 starts by making the foundation executable and testable without changing the final recommendation prematurely. The old outputs remain historical reference points until the repaired pipeline can recompute the recommendation under `SPEC.md`.

The first substantive repair milestone is therefore:

> **A pure, cross-campus canonical Section/data layer with zero-failure tests and no import-time side effects.**
