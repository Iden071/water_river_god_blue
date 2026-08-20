"""Streaming Stage 4E Fall + future evaluation for long exact searches.

The reference :mod:`fall_search` implementation intentionally materializes the entire Fall
candidate universe before evaluating anything.  That is ideal as a correctness oracle but is
not suitable for a multi-hour exact run.

This module keeps the same proof contract while allowing candidates from
``fall_resumable_enumeration`` to be evaluated incrementally:

* every emitted Fall candidate receives the same CandidateAssessment -> stateful recognition
  -> rebased future -> whole-plan objective treatment as the reference solver;
* complete utility candidates are retained only on a strict, proof-safe interval frontier;
* unresolved utility candidates are never treated as dominated.  For scalability the
  accumulator retains counts/dimensions plus bounded examples; their mere existence blocks
  an optimum proof until the model is rerun with the missing evidence resolved;
* a PAUSED structural enumeration can expose an incumbent frontier but can never prove an
  optimum;
* only COMPLETE structural coverage may produce a global/scoped optimum claim.

No partial-Fall objective bound is used here, so this module introduces no new objective
pruning.  It is a memory/scalability refactor of exhaustive evaluation, not a heuristic.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
import hashlib
from typing import Mapping

from .candidate_assessment import (
    CandidateConstraintIssue,
    ConstraintEvidenceStatus,
    assess_candidate,
)
from .catalog import CatalogSnapshot
from .course_preferences import ProfessorRatingBook
from .degree import DegreeScenario, DegreeState
from .degree_remainder import degree_remainder
from .fall_actions import (
    FallDegreeTransitionBranch,
    FallRecognitionEvidence,
    generate_fall_degree_transitions,
)
from .fall_candidate_sets import FallCandidateSet, FallLoadPolicy
from .fall_continuation import build_fall_continuation_bridge
from .fall_resumable_enumeration import (
    FallEnumerationBatch,
    FallResumableEnumerationStatus,
)
from .fall_search import FallSearchUnknown, FallWholePlanBranchResult
from .fall_universe import FallSectionUniverse
from .future_actions import FutureRecognitionEvidence
from .future_problem import FuturePlanningProblem
from .future_utility import TemporalUtilityAggregation
from .preferences import PreferenceProfile, PreferenceValue
from .registration import RegistrationAssessment
from .verification import VerificationSummary
from .whole_plan_optimization import (
    WholePlanOptimizationStatus,
    WholePlanUtilityCandidate,
    assess_fall_candidate_whole_plan,
)


class FallStreamingSearchError(ValueError):
    """Streaming Fall search inputs or accumulated proof state are inconsistent."""


class FallCandidateEvaluationStatus(str, Enum):
    KNOWN_INFEASIBLE = "known_infeasible"
    EXACT_EVALUATED = "exact_evaluated"
    UNRESOLVED = "unresolved"
    SEARCH_INCOMPLETE = "search_incomplete"


class FallStreamingSearchStatus(str, Enum):
    PAUSED = "paused"
    GLOBAL_OPTIMUM_PROVEN = "global_optimum_proven"
    SCOPED_OPTIMUM_PROVEN = "scoped_optimum_proven"
    PROVEN_NO_REACHABLE_PLAN = "proven_no_reachable_plan"
    BOUNDED_FRONTIER = "bounded_frontier"
    UTILITY_UNRESOLVED = "utility_unresolved"
    HORIZON_INCOMPARABLE = "horizon_incomparable"
    UNRESOLVED_ALTERNATIVES = "unresolved_alternatives"
    SEARCH_INCOMPLETE = "search_incomplete"
    INPUT_BLOCKED = "input_blocked"


@dataclass(frozen=True)
class FallCandidateEvaluationContext:
    snapshot: CatalogSnapshot
    degree_scenario: DegreeScenario
    starting_state: DegreeState
    future_template: FuturePlanningProblem
    preference_profile: PreferenceProfile
    professor_ratings: ProfessorRatingBook
    temporal_aggregation: TemporalUtilityAggregation
    load_policy: FallLoadPolicy
    registration_assessments: Mapping[str, RegistrationAssessment] = field(
        default_factory=dict
    )
    fall_recognition_evidence: Mapping[str, FallRecognitionEvidence] = field(
        default_factory=dict
    )
    future_recognition_evidence: Mapping[str, FutureRecognitionEvidence] = field(
        default_factory=dict
    )
    subject_interest: Mapping[str, PreferenceValue] = field(default_factory=dict)
    workload_utility: Mapping[str, PreferenceValue] = field(default_factory=dict)
    difficulty_utility: Mapping[str, PreferenceValue] = field(default_factory=dict)
    resolved_present_dimensions: Mapping[str, PreferenceValue] = field(default_factory=dict)
    max_future_selection_evaluations: int = 100_000

    def __post_init__(self) -> None:
        if self.max_future_selection_evaluations <= 0:
            raise FallStreamingSearchError(
                "max_future_selection_evaluations must be positive"
            )
        baseline = degree_remainder(self.starting_state, self.degree_scenario)
        if self.future_template.degree_remainder != baseline:
            raise FallStreamingSearchError(
                "future template remainder does not match streaming Fall starting DegreeState"
            )


@dataclass(frozen=True)
class StreamingUtilityRecord:
    """One exact Fall branch / continuation utility candidate retained by the accumulator."""

    utility: WholePlanUtilityCandidate
    fall_set_id: str
    branch_id: str
    section_ids: tuple[str, ...]
    transition_option_ids: tuple[str, ...]

    @property
    def term_ids(self) -> tuple[str, ...]:
        return self.utility.term_ids

    @property
    def utility_complete(self) -> bool:
        return self.utility.utility_complete


@dataclass(frozen=True)
class FallCandidateEvaluation:
    fall_set_id: str
    section_ids: tuple[str, ...]
    status: FallCandidateEvaluationStatus
    known_infeasible: bool
    branch_results: tuple[FallWholePlanBranchResult, ...]
    utility_records: tuple[StreamingUtilityRecord, ...]
    proven_unreachable_branch_ids: frozenset[str]
    unresolved_alternatives: tuple[FallSearchUnknown, ...]
    blocker_codes: frozenset[str]


@dataclass(frozen=True)
class FallStreamingHorizonSummary:
    term_ids: tuple[str, ...]
    undominated_complete: tuple[StreamingUtilityRecord, ...]
    complete_candidates_seen: int
    dominated_complete_candidates: int
    unresolved_candidates_seen: int
    unresolved_dimension_counts: tuple[tuple[str, int], ...]
    unresolved_examples: tuple[StreamingUtilityRecord, ...]

    @property
    def unique_proven_best(self) -> StreamingUtilityRecord | None:
        if self.unresolved_candidates_seen or len(self.undominated_complete) != 1:
            return None
        return self.undominated_complete[0]


@dataclass(frozen=True)
class FallStreamingSearchSnapshot:
    status: FallStreamingSearchStatus
    structural_status: FallResumableEnumerationStatus
    processed_fall_sets: int
    exact_branches_seen: int
    known_infeasible_fall_sets: int
    proven_unreachable_branches: int
    unresolved_alternatives: int
    unresolved_alternative_counts: tuple[tuple[str, int], ...]
    unresolved_alternative_examples: tuple[FallSearchUnknown, ...]
    horizons: tuple[FallStreamingHorizonSummary, ...]
    blocker_codes: frozenset[str]
    verification: VerificationSummary | None

    @property
    def model_optimum_proven(self) -> bool:
        return self.status in {
            FallStreamingSearchStatus.GLOBAL_OPTIMUM_PROVEN,
            FallStreamingSearchStatus.SCOPED_OPTIMUM_PROVEN,
        }

    @property
    def user_verified_optimum(self) -> bool:
        return (
            self.model_optimum_proven
            and self.verification is not None
            and self.verification.manually_verified
        )

    @property
    def proven_best(self) -> StreamingUtilityRecord | None:
        if not self.model_optimum_proven or len(self.horizons) != 1:
            return None
        return self.horizons[0].unique_proven_best


@dataclass
class _MutableHorizon:
    term_ids: tuple[str, ...]
    objective_signature: tuple[str, tuple[tuple[str, float], ...]]
    undominated_complete: list[StreamingUtilityRecord] = field(default_factory=list)
    complete_candidates_seen: int = 0
    dominated_complete_candidates: int = 0
    unresolved_candidates_seen: int = 0
    unresolved_dimension_counts: Counter[str] = field(default_factory=Counter)
    unresolved_examples: list[StreamingUtilityRecord] = field(default_factory=list)


class FallStreamingAccumulator:
    """Memory-bounded proof state for a resumable exact Fall candidate stream."""

    def __init__(
        self,
        *,
        unresolved_example_limit: int = 5,
        verification: VerificationSummary | None = None,
    ) -> None:
        if unresolved_example_limit < 0:
            raise FallStreamingSearchError(
                "unresolved_example_limit cannot be negative"
            )
        self.unresolved_example_limit = unresolved_example_limit
        self.verification = verification
        self.processed_fall_sets = 0
        self.exact_branches_seen = 0
        self.known_infeasible_fall_sets = 0
        self.proven_unreachable_branches = 0
        self.unresolved_alternatives = 0
        self.unresolved_alternative_counts: Counter[str] = Counter()
        self.unresolved_alternative_examples: list[FallSearchUnknown] = []
        self.blocker_codes: set[str] = set()
        self.continuation_search_incomplete = False
        self._horizons: dict[tuple[str, ...], _MutableHorizon] = {}

    def _horizon_for(self, record: StreamingUtilityRecord) -> _MutableHorizon:
        candidate = record.utility
        signature = (candidate.aggregation_source_id, candidate.aggregation_weights)
        horizon = self._horizons.get(candidate.term_ids)
        if horizon is None:
            horizon = _MutableHorizon(candidate.term_ids, signature)
            self._horizons[candidate.term_ids] = horizon
            return horizon
        if horizon.objective_signature != signature:
            raise FallStreamingSearchError(
                "streaming candidates within one graduation horizon use different temporal objectives"
            )
        return horizon

    def _add_complete(self, horizon: _MutableHorizon, record: StreamingUtilityRecord) -> None:
        candidate = record.utility
        bounds = candidate.complete_bounds
        if bounds is None:
            raise FallStreamingSearchError("complete frontier received incomplete utility")
        candidate_lower, candidate_upper = bounds
        horizon.complete_candidates_seen += 1

        # If an existing undominated candidate strictly dominates the newcomer, the new
        # candidate can never be needed by a future dominance proof.
        for existing in horizon.undominated_complete:
            existing_bounds = existing.utility.complete_bounds
            assert existing_bounds is not None
            existing_lower, _ = existing_bounds
            if existing_lower > candidate_upper:
                horizon.dominated_complete_candidates += 1
                return

        survivors: list[StreamingUtilityRecord] = []
        removed = 0
        for existing in horizon.undominated_complete:
            existing_bounds = existing.utility.complete_bounds
            assert existing_bounds is not None
            _, existing_upper = existing_bounds
            if candidate_lower > existing_upper:
                removed += 1
            else:
                survivors.append(existing)
        horizon.dominated_complete_candidates += removed
        survivors.append(record)
        horizon.undominated_complete = survivors

    def _add_unresolved(self, horizon: _MutableHorizon, record: StreamingUtilityRecord) -> None:
        horizon.unresolved_candidates_seen += 1
        for dimension in record.utility.unresolved_dimensions:
            horizon.unresolved_dimension_counts[dimension] += 1
        if record.utility.heuristic_point_delta != 0.0:
            horizon.unresolved_dimension_counts["<heuristic-utility-present>"] += 1
        if len(horizon.unresolved_examples) < self.unresolved_example_limit:
            horizon.unresolved_examples.append(record)

    def add_evaluation(self, evaluation: FallCandidateEvaluation) -> None:
        self.processed_fall_sets += 1
        if evaluation.known_infeasible:
            self.known_infeasible_fall_sets += 1

        self.exact_branches_seen += len(evaluation.branch_results)
        self.proven_unreachable_branches += len(
            evaluation.proven_unreachable_branch_ids
        )
        self.blocker_codes.update(evaluation.blocker_codes)
        if evaluation.status is FallCandidateEvaluationStatus.SEARCH_INCOMPLETE:
            self.continuation_search_incomplete = True

        for unknown in evaluation.unresolved_alternatives:
            self.unresolved_alternatives += 1
            self.unresolved_alternative_counts[unknown.code] += 1
            if len(self.unresolved_alternative_examples) < self.unresolved_example_limit:
                self.unresolved_alternative_examples.append(unknown)

        for record in evaluation.utility_records:
            horizon = self._horizon_for(record)
            if record.utility_complete:
                self._add_complete(horizon, record)
            else:
                self._add_unresolved(horizon, record)

    def _summaries(self) -> tuple[FallStreamingHorizonSummary, ...]:
        return tuple(
            FallStreamingHorizonSummary(
                term_ids=horizon.term_ids,
                undominated_complete=tuple(horizon.undominated_complete),
                complete_candidates_seen=horizon.complete_candidates_seen,
                dominated_complete_candidates=horizon.dominated_complete_candidates,
                unresolved_candidates_seen=horizon.unresolved_candidates_seen,
                unresolved_dimension_counts=tuple(
                    sorted(horizon.unresolved_dimension_counts.items())
                ),
                unresolved_examples=tuple(horizon.unresolved_examples),
            )
            for _, horizon in sorted(
                self._horizons.items(), key=lambda item: (len(item[0]), item[0])
            )
        )

    def snapshot(
        self,
        *,
        structural_status: FallResumableEnumerationStatus,
        universe: FallSectionUniverse,
    ) -> FallStreamingSearchSnapshot:
        summaries = self._summaries()
        blockers = set(self.blocker_codes)

        if structural_status is FallResumableEnumerationStatus.INPUT_BLOCKED:
            status = FallStreamingSearchStatus.INPUT_BLOCKED
            blockers.add("fall_section_universe_input_blocked")
        elif structural_status is FallResumableEnumerationStatus.PAUSED:
            status = FallStreamingSearchStatus.PAUSED
            blockers.add("fall_structural_enumeration_paused")
        elif self.continuation_search_incomplete:
            status = FallStreamingSearchStatus.SEARCH_INCOMPLETE
            blockers.add("future_completion_search_incomplete")
        elif self.unresolved_alternatives:
            status = FallStreamingSearchStatus.UNRESOLVED_ALTERNATIVES
            blockers.add("fall_or_future_hard_alternative_unresolved")
        elif not summaries:
            status = FallStreamingSearchStatus.PROVEN_NO_REACHABLE_PLAN
        elif len(summaries) > 1:
            status = FallStreamingSearchStatus.HORIZON_INCOMPARABLE
            blockers.add("graduation_timing_utility_unresolved")
        elif summaries[0].unresolved_candidates_seen:
            status = FallStreamingSearchStatus.UTILITY_UNRESOLVED
            blockers.add("whole_plan_utility_unresolved")
        elif summaries[0].unique_proven_best is not None:
            status = (
                FallStreamingSearchStatus.GLOBAL_OPTIMUM_PROVEN
                if universe.eligible_for_global_optimum_claim
                else FallStreamingSearchStatus.SCOPED_OPTIMUM_PROVEN
            )
        else:
            status = FallStreamingSearchStatus.BOUNDED_FRONTIER

        return FallStreamingSearchSnapshot(
            status=status,
            structural_status=structural_status,
            processed_fall_sets=self.processed_fall_sets,
            exact_branches_seen=self.exact_branches_seen,
            known_infeasible_fall_sets=self.known_infeasible_fall_sets,
            proven_unreachable_branches=self.proven_unreachable_branches,
            unresolved_alternatives=self.unresolved_alternatives,
            unresolved_alternative_counts=tuple(
                sorted(self.unresolved_alternative_counts.items())
            ),
            unresolved_alternative_examples=tuple(
                self.unresolved_alternative_examples
            ),
            horizons=summaries,
            blocker_codes=frozenset(blockers),
            verification=self.verification,
        )


def stable_fall_set_id(candidate_set: FallCandidateSet) -> str:
    """Deterministic identity independent of batch boundaries or enumeration ordinal."""

    if not candidate_set.section_ids:
        return "fall-set:empty"
    payload = "\x1f".join(candidate_set.section_ids).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()[:24]
    return f"fall-set:{digest}"


def _credit_cap_unknown_issue(
    candidate_set: FallCandidateSet,
    load_policy: FallLoadPolicy,
) -> tuple[CandidateConstraintIssue, ...]:
    if not candidate_set.load.unknown_credit_section_ids:
        return ()
    return (
        CandidateConstraintIssue(
            code="ordinary_credit_cap_unresolved",
            status=ConstraintEvidenceStatus.UNRESOLVED,
            message=(
                "selected Fall section has unresolved credits, so compliance with the explicit ordinary-credit cap cannot be established"
            ),
            section_ids=candidate_set.load.unknown_credit_section_ids,
            source=load_policy.source_id,
        ),
    )


def _recognition_map(branch: FallDegreeTransitionBranch) -> dict[str, object]:
    out: dict[str, object] = {}
    for assessment in branch.recognitions:
        if assessment.section_id in out:
            raise FallStreamingSearchError(
                f"duplicate recognition assessment for {assessment.section_id!r} in Fall branch"
            )
        out[assessment.section_id] = assessment
    return out


def _unknown(
    code: str,
    message: str,
    *,
    fall_set_id: str,
    branch_id: str = "",
    section_ids: tuple[str, ...] = (),
) -> FallSearchUnknown:
    return FallSearchUnknown(
        code=code,
        message=message,
        fall_set_id=fall_set_id,
        branch_id=branch_id,
        section_ids=section_ids,
    )


def _dedupe_unknowns(items: list[FallSearchUnknown]) -> tuple[FallSearchUnknown, ...]:
    out: list[FallSearchUnknown] = []
    seen: set[FallSearchUnknown] = set()
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return tuple(out)


def evaluate_fall_candidate_set(
    candidate_set: FallCandidateSet,
    context: FallCandidateEvaluationContext,
) -> FallCandidateEvaluation:
    """Apply the reference Stage 4E semantics to exactly one emitted Fall candidate."""

    fall_set_id = stable_fall_set_id(candidate_set)
    static_extra = _credit_cap_unknown_issue(candidate_set, context.load_policy)

    preliminary = assess_candidate(
        candidate_set.sections,
        context.preference_profile,
        context.professor_ratings,
        subject_interest=context.subject_interest,
        workload_utility=context.workload_utility,
        difficulty_utility=context.difficulty_utility,
        registration_assessments=context.registration_assessments,
        degree_scenario=context.degree_scenario,
        external_constraint_issues=static_extra,
    )
    if preliminary.known_infeasible:
        return FallCandidateEvaluation(
            fall_set_id,
            candidate_set.section_ids,
            FallCandidateEvaluationStatus.KNOWN_INFEASIBLE,
            True,
            (),
            (),
            frozenset(),
            (),
            frozenset(),
        )

    unresolved: list[FallSearchUnknown] = []
    blockers: set[str] = set()
    if preliminary.hard_constraint_unknowns:
        for issue in preliminary.hard_constraint_unknowns:
            unresolved.append(
                _unknown(
                    f"fall_hard::{issue.code}",
                    issue.message,
                    fall_set_id=fall_set_id,
                    section_ids=issue.section_ids,
                )
            )
        return FallCandidateEvaluation(
            fall_set_id,
            candidate_set.section_ids,
            FallCandidateEvaluationStatus.UNRESOLVED,
            False,
            (),
            (),
            frozenset(),
            _dedupe_unknowns(unresolved),
            frozenset(),
        )

    selected_ids = set(candidate_set.section_ids)
    transition_evidence = {
        section_id: evidence
        for section_id, evidence in context.fall_recognition_evidence.items()
        if section_id in selected_ids
    }
    transitions = generate_fall_degree_transitions(
        candidate_set.sections,
        context.snapshot,
        context.degree_scenario,
        context.starting_state,
        evidence=transition_evidence,
    )
    if transitions.unresolved_issues:
        for issue in transitions.unresolved_issues:
            unresolved.append(
                _unknown(
                    f"fall_transition::{issue.code}",
                    issue.message,
                    fall_set_id=fall_set_id,
                    section_ids=(issue.section_id,),
                )
            )
    if not transitions.branches:
        if not transitions.unresolved_issues:
            raise FallStreamingSearchError(
                f"Fall set {fall_set_id} produced neither exact transition branches nor unresolved issues"
            )
        return FallCandidateEvaluation(
            fall_set_id,
            candidate_set.section_ids,
            FallCandidateEvaluationStatus.UNRESOLVED,
            False,
            (),
            (),
            frozenset(),
            _dedupe_unknowns(unresolved),
            frozenset(),
        )

    branch_results: list[FallWholePlanBranchResult] = []
    utility_records: list[StreamingUtilityRecord] = []
    proven_unreachable: set[str] = set()
    continuation_search_incomplete = False

    for branch_index, transition_branch in enumerate(transitions.branches):
        branch_id = f"{fall_set_id}::transition-{branch_index:03d}"
        raw_map = _recognition_map(transition_branch)
        recognition_map = {
            section_id: assessment
            for section_id, assessment in raw_map.items()
        }
        candidate = assess_candidate(
            candidate_set.sections,
            context.preference_profile,
            context.professor_ratings,
            subject_interest=context.subject_interest,
            workload_utility=context.workload_utility,
            difficulty_utility=context.difficulty_utility,
            registration_assessments=context.registration_assessments,
            recognition_assessments=recognition_map,  # type: ignore[arg-type]
            degree_scenario=context.degree_scenario,
            degree_transition=transition_branch.transition,
            external_constraint_issues=static_extra,
        )
        active_resolutions = {
            dimension_id: value
            for dimension_id, value in context.resolved_present_dimensions.items()
            if dimension_id in candidate.present_preference_unknowns
        }
        bridge = build_fall_continuation_bridge(
            branch_id,
            candidate,
            context.degree_scenario,
            context.future_template,
            resolved_present_dimensions=active_resolutions,
        )
        whole = assess_fall_candidate_whole_plan(
            bridge,
            context.degree_scenario,
            context.preference_profile,
            context.professor_ratings,
            context.temporal_aggregation,
            recognition_evidence=context.future_recognition_evidence,
            subject_interest=context.subject_interest,
            workload_utility=context.workload_utility,
            difficulty_utility=context.difficulty_utility,
            max_selection_evaluations=context.max_future_selection_evaluations,
        )
        branch_results.append(
            FallWholePlanBranchResult(
                branch_id=branch_id,
                fall_set_id=fall_set_id,
                section_ids=candidate_set.section_ids,
                transition_option_ids=transition_branch.transition.selected_option_ids,
                candidate=candidate,
                whole_plan=whole,
            )
        )

        if whole.status is WholePlanOptimizationStatus.PROVEN_UNREACHABLE:
            proven_unreachable.add(branch_id)
            continue
        if whole.status is WholePlanOptimizationStatus.SEARCH_INCOMPLETE:
            continuation_search_incomplete = True
            blockers.add("future_completion_search_incomplete")
            blockers.update(whole.blocker_codes)
        elif whole.status is WholePlanOptimizationStatus.FUTURE_INPUT_BLOCKED:
            unresolved.append(
                _unknown(
                    "future_input_blocked",
                    "future continuation inputs are insufficient for exact evaluation",
                    fall_set_id=fall_set_id,
                    branch_id=branch_id,
                    section_ids=candidate_set.section_ids,
                )
            )
            blockers.update(whole.blocker_codes)
            continue
        elif whole.status is WholePlanOptimizationStatus.FALL_BLOCKED:
            unresolved.append(
                _unknown(
                    "fall_branch_blocked",
                    "selected Fall transition branch remains unresolved at the continuation boundary",
                    fall_set_id=fall_set_id,
                    branch_id=branch_id,
                    section_ids=candidate_set.section_ids,
                )
            )
            blockers.update(whole.blocker_codes)
            continue

        for utility in whole.candidates:
            utility_records.append(
                StreamingUtilityRecord(
                    utility=utility,
                    fall_set_id=fall_set_id,
                    branch_id=branch_id,
                    section_ids=candidate_set.section_ids,
                    transition_option_ids=transition_branch.transition.selected_option_ids,
                )
            )

    if continuation_search_incomplete:
        status = FallCandidateEvaluationStatus.SEARCH_INCOMPLETE
    elif unresolved:
        status = FallCandidateEvaluationStatus.UNRESOLVED
    else:
        status = FallCandidateEvaluationStatus.EXACT_EVALUATED

    return FallCandidateEvaluation(
        fall_set_id=fall_set_id,
        section_ids=candidate_set.section_ids,
        status=status,
        known_infeasible=False,
        branch_results=tuple(branch_results),
        utility_records=tuple(utility_records),
        proven_unreachable_branch_ids=frozenset(proven_unreachable),
        unresolved_alternatives=_dedupe_unknowns(unresolved),
        blocker_codes=frozenset(blockers),
    )


def consume_fall_enumeration_batch(
    accumulator: FallStreamingAccumulator,
    batch: FallEnumerationBatch,
    context: FallCandidateEvaluationContext,
) -> FallStreamingAccumulator:
    """Evaluate one resumable structural batch and merge only proof-relevant state."""

    if batch.status is FallResumableEnumerationStatus.INPUT_BLOCKED:
        return accumulator
    for candidate_set in batch.candidates:
        accumulator.add_evaluation(evaluate_fall_candidate_set(candidate_set, context))
    return accumulator
