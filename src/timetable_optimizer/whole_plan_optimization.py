"""One-objective Fall 2026 + finite-continuation optimization for Stage 4E.

This module is the first place where the current semester and Stage 4D continuation are
placed on the *same* objective.  It does not rank Fall first, truncate candidates, and then
repair the future.  Instead, a selected Fall degree transition rebases the future problem,
all exact continuation histories are enumerated, and current/future utility evidence is
combined under one explicitly sourced temporal policy.

No default Fall weight is invented.  The supplied temporal aggregation must cover the current
term and the entire future planning timeline.  Different graduation horizons remain separate
frontiers because no value for earlier graduation has been elicited.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from .course_preferences import ProfessorRatingBook
from .fall_continuation import FallContinuationBridge, FallContinuationStatus
from .future_actions import FutureRecognitionEvidence
from .future_completion_search import (
    FutureCompletionSearchResult,
    FutureCompletionSearchStatus,
    enumerate_future_degree_completion_histories,
)
from .future_optimization import (
    FutureOptimizationAssessment,
    FutureUtilityCandidate,
    assess_future_completion_utility,
)
from .future_utility import TemporalUtilityAggregation, TemporalUtilityWeight
from .preferences import PreferenceProfile, PreferenceValue
from .present_utility import PresentTermUtilityAssessment


class WholePlanOptimizationError(ValueError):
    """Whole-plan optimization inputs violate the Stage 4E objective contract."""


class WholePlanOptimizationStatus(str, Enum):
    OPTIMUM_PROVEN = "optimum_proven"
    BOUNDED_FRONTIER = "bounded_frontier"
    UTILITY_UNRESOLVED = "utility_unresolved"
    HORIZON_INCOMPARABLE = "horizon_incomparable"
    SEARCH_INCOMPLETE = "search_incomplete"
    PROVEN_UNREACHABLE = "proven_unreachable"
    FALL_BLOCKED = "fall_blocked"
    FUTURE_INPUT_BLOCKED = "future_input_blocked"


@dataclass(frozen=True)
class WholePlanUtilityCandidate:
    """One concrete Fall choice followed by one concrete degree-completion history."""

    candidate_id: str
    fall_candidate_id: str
    present_utility: PresentTermUtilityAssessment
    future_candidate: FutureUtilityCandidate
    term_ids: tuple[str, ...]
    measured_lower: float
    measured_upper: float
    heuristic_point_delta: float
    unresolved_dimensions: frozenset[str]
    aggregation_source_id: str
    aggregation_weights: tuple[tuple[str, float], ...]

    @property
    def complete_bounds(self) -> tuple[float, float] | None:
        if self.heuristic_point_delta != 0.0 or self.unresolved_dimensions:
            return None
        return (self.measured_lower, self.measured_upper)

    @property
    def utility_complete(self) -> bool:
        return self.complete_bounds is not None


@dataclass(frozen=True)
class WholePlanHorizonFrontier:
    term_ids: tuple[str, ...]
    candidates: tuple[WholePlanUtilityCandidate, ...]
    undominated_complete: tuple[WholePlanUtilityCandidate, ...]
    unresolved_candidates: tuple[WholePlanUtilityCandidate, ...]
    strictly_dominated_candidate_ids: frozenset[str]

    @property
    def completion_term_id(self) -> str | None:
        # term_ids always includes the current term; a one-term history means graduation is
        # complete after Fall itself.
        return self.term_ids[-1] if self.term_ids else None

    @property
    def unique_proven_best(self) -> WholePlanUtilityCandidate | None:
        if self.unresolved_candidates or len(self.undominated_complete) != 1:
            return None
        return self.undominated_complete[0]


@dataclass(frozen=True)
class WholePlanOptimizationAssessment:
    status: WholePlanOptimizationStatus
    bridge: FallContinuationBridge
    future_search: FutureCompletionSearchResult | None
    future_assessment: FutureOptimizationAssessment | None
    candidates: tuple[WholePlanUtilityCandidate, ...]
    frontiers: tuple[WholePlanHorizonFrontier, ...]
    blocker_codes: frozenset[str]

    @property
    def optimum_proven(self) -> bool:
        return self.status is WholePlanOptimizationStatus.OPTIMUM_PROVEN

    @property
    def proven_best(self) -> WholePlanUtilityCandidate | None:
        if not self.optimum_proven or len(self.frontiers) != 1:
            return None
        return self.frontiers[0].unique_proven_best


def _validate_whole_plan_aggregation(
    bridge: FallContinuationBridge,
    aggregation: TemporalUtilityAggregation,
) -> tuple[str, ...]:
    if bridge.future_problem is None:
        future_ids: tuple[str, ...] = ()
    else:
        future_ids = tuple(term.term_id for term in bridge.future_problem.timeline.terms)
    present_id = bridge.present_utility.term_id
    if present_id in future_ids:
        raise WholePlanOptimizationError(
            "present term id must not also appear in the future planning timeline"
        )
    expected = (present_id,) + future_ids
    supplied = tuple(weight.term_id for weight in aggregation.weights)
    if set(supplied) != set(expected) or len(supplied) != len(expected):
        missing = sorted(set(expected) - set(supplied))
        extra = sorted(set(supplied) - set(expected))
        pieces: list[str] = []
        if missing:
            pieces.append("missing=" + ",".join(missing))
        if extra:
            pieces.append("extra=" + ",".join(extra))
        raise WholePlanOptimizationError(
            "whole-plan temporal aggregation must cover Fall plus the full future timeline exactly"
            + (": " + "; ".join(pieces) if pieces else "")
        )
    return future_ids


def _future_aggregation(
    future_ids: tuple[str, ...],
    master: TemporalUtilityAggregation,
) -> TemporalUtilityAggregation:
    return TemporalUtilityAggregation(
        source_id=master.source_id,
        weights=tuple(
            TemporalUtilityWeight(term_id, master.weight_for(term_id))
            for term_id in future_ids
        ),
        note=(
            "Future-only projection of the Stage 4E whole-plan temporal policy. "
            + master.note
        ).strip(),
    )


def _whole_candidate(
    bridge: FallContinuationBridge,
    future: FutureUtilityCandidate,
    master: TemporalUtilityAggregation,
) -> WholePlanUtilityCandidate:
    present = bridge.present_utility
    present_weight = master.weight_for(present.term_id)

    lower = future.aggregate.measured_lower
    upper = future.aggregate.measured_upper
    heuristic = future.aggregate.heuristic_point_delta
    unresolved = {
        f"{term_id}::{dimension}"
        for term_id in future.history.term_ids
        for dimension in future.history.unresolved_dimensions
        if not dimension.startswith(f"{term_id}::")
    }
    # Future aggregate already carries correctly scoped unresolved dimensions.  Prefer those
    # directly; the comprehension above is only defensive for hand-built histories.
    unresolved.update(future.aggregate.unresolved_dimensions)

    if present_weight != 0.0:
        lower += present_weight * present.measured_lower
        upper += present_weight * present.measured_upper
        heuristic += present_weight * present.heuristic_point_delta
        unresolved.update(
            f"{present.term_id}::{dimension}"
            for dimension in present.unresolved_dimensions
        )
        if present.has_heuristics and present_weight != 0.0 and present.heuristic_point_delta == 0.0:
            # A zero-valued heuristic remains heuristic evidence rather than exact evidence.
            unresolved.add(f"{present.term_id}::heuristic_status")

    term_ids = (present.term_id,) + future.term_ids
    weights = tuple((term_id, master.weight_for(term_id)) for term_id in term_ids)
    return WholePlanUtilityCandidate(
        candidate_id=f"{bridge.candidate_id}::{future.candidate_id}",
        fall_candidate_id=bridge.candidate_id,
        present_utility=present,
        future_candidate=future,
        term_ids=term_ids,
        measured_lower=lower,
        measured_upper=upper,
        heuristic_point_delta=heuristic,
        unresolved_dimensions=frozenset(unresolved),
        aggregation_source_id=master.source_id,
        aggregation_weights=weights,
    )


def _build_frontier(
    candidates: tuple[WholePlanUtilityCandidate, ...],
) -> WholePlanHorizonFrontier:
    if not candidates:
        raise WholePlanOptimizationError("cannot build whole-plan frontier from zero candidates")
    term_ids = candidates[0].term_ids
    signature = (
        candidates[0].aggregation_source_id,
        candidates[0].aggregation_weights,
    )
    for candidate in candidates:
        if candidate.term_ids != term_ids:
            raise WholePlanOptimizationError(
                "whole-plan frontier candidates must share one graduation horizon"
            )
        if (
            candidate.aggregation_source_id,
            candidate.aggregation_weights,
        ) != signature:
            raise WholePlanOptimizationError(
                "whole-plan frontier candidates must use the same temporal objective"
            )

    complete = tuple(candidate for candidate in candidates if candidate.utility_complete)
    unresolved = tuple(candidate for candidate in candidates if not candidate.utility_complete)
    dominated: set[str] = set()
    for candidate in complete:
        assert candidate.complete_bounds is not None
        _, candidate_upper = candidate.complete_bounds
        for challenger in complete:
            if challenger.candidate_id == candidate.candidate_id:
                continue
            assert challenger.complete_bounds is not None
            challenger_lower, _ = challenger.complete_bounds
            if challenger_lower > candidate_upper:
                dominated.add(candidate.candidate_id)
                break

    undominated = tuple(
        candidate
        for candidate in complete
        if candidate.candidate_id not in dominated
    )
    return WholePlanHorizonFrontier(
        term_ids=term_ids,
        candidates=candidates,
        undominated_complete=undominated,
        unresolved_candidates=unresolved,
        strictly_dominated_candidate_ids=frozenset(dominated),
    )


def build_safe_whole_plan_frontiers(
    candidates: tuple[WholePlanUtilityCandidate, ...],
) -> tuple[WholePlanHorizonFrontier, ...]:
    """Apply strict complete-bound dominance only within one graduation horizon/objective."""

    by_horizon: dict[tuple[str, ...], list[WholePlanUtilityCandidate]] = {}
    for candidate in candidates:
        by_horizon.setdefault(candidate.term_ids, []).append(candidate)
    return tuple(
        _build_frontier(tuple(by_horizon[horizon]))
        for horizon in sorted(by_horizon, key=lambda ids: (len(ids), ids))
    )


def assess_fall_candidate_whole_plan(
    bridge: FallContinuationBridge,
    degree_scenario,
    preference_profile: PreferenceProfile,
    professor_ratings: ProfessorRatingBook,
    temporal_aggregation: TemporalUtilityAggregation,
    *,
    recognition_evidence: Mapping[str, FutureRecognitionEvidence] | None = None,
    subject_interest: Mapping[str, PreferenceValue] | None = None,
    workload_utility: Mapping[str, PreferenceValue] | None = None,
    difficulty_utility: Mapping[str, PreferenceValue] | None = None,
    max_selection_evaluations: int = 100_000,
) -> WholePlanOptimizationAssessment:
    """Enumerate and evaluate every continuation of one selected Fall candidate."""

    future_ids = _validate_whole_plan_aggregation(bridge, temporal_aggregation)

    if bridge.status is FallContinuationStatus.FALL_INFEASIBLE:
        return WholePlanOptimizationAssessment(
            status=WholePlanOptimizationStatus.FALL_BLOCKED,
            bridge=bridge,
            future_search=None,
            future_assessment=None,
            candidates=(),
            frontiers=(),
            blocker_codes=bridge.blocker_codes,
        )
    if bridge.status in {
        FallContinuationStatus.FALL_HARD_UNRESOLVED,
        FallContinuationStatus.DEGREE_TRANSITION_UNRESOLVED,
    }:
        return WholePlanOptimizationAssessment(
            status=WholePlanOptimizationStatus.FALL_BLOCKED,
            bridge=bridge,
            future_search=None,
            future_assessment=None,
            candidates=(),
            frontiers=(),
            blocker_codes=bridge.blocker_codes,
        )
    if bridge.status is FallContinuationStatus.FUTURE_INPUT_BLOCKED:
        return WholePlanOptimizationAssessment(
            status=WholePlanOptimizationStatus.FUTURE_INPUT_BLOCKED,
            bridge=bridge,
            future_search=None,
            future_assessment=None,
            candidates=(),
            frontiers=(),
            blocker_codes=bridge.blocker_codes,
        )
    if not bridge.future_search_ready or bridge.degree_transition is None or bridge.future_problem is None:
        raise WholePlanOptimizationError(
            "READY Fall continuation bridge is missing an exact future problem or degree transition"
        )

    search = enumerate_future_degree_completion_histories(
        bridge.future_problem,
        degree_scenario,
        bridge.degree_transition.resulting_state,
        recognition_evidence=recognition_evidence,
        max_selection_evaluations=max_selection_evaluations,
    )
    future_policy = _future_aggregation(future_ids, temporal_aggregation)
    future_assessment = assess_future_completion_utility(
        search,
        bridge.future_problem,
        preference_profile,
        professor_ratings,
        future_policy,
        subject_interest=subject_interest,
        workload_utility=workload_utility,
        difficulty_utility=difficulty_utility,
    )
    candidates = tuple(
        _whole_candidate(bridge, future, temporal_aggregation)
        for future in future_assessment.candidates
    )
    frontiers = build_safe_whole_plan_frontiers(candidates) if candidates else ()
    blockers: set[str] = set(bridge.blocker_codes)

    if search.status is FutureCompletionSearchStatus.INPUT_BLOCKED:
        blockers.update(search.input_blocker_codes)
        return WholePlanOptimizationAssessment(
            WholePlanOptimizationStatus.FUTURE_INPUT_BLOCKED,
            bridge,
            search,
            future_assessment,
            candidates,
            frontiers,
            frozenset(blockers),
        )
    if search.status is FutureCompletionSearchStatus.PROVEN_UNREACHABLE:
        return WholePlanOptimizationAssessment(
            WholePlanOptimizationStatus.PROVEN_UNREACHABLE,
            bridge,
            search,
            future_assessment,
            (),
            (),
            frozenset(blockers),
        )
    if not search.enumeration_complete:
        blockers.add("completion_history_search_incomplete")
        blockers.update(unknown.code for unknown in search.unknowns)
        return WholePlanOptimizationAssessment(
            WholePlanOptimizationStatus.SEARCH_INCOMPLETE,
            bridge,
            search,
            future_assessment,
            candidates,
            frontiers,
            frozenset(blockers),
        )
    if len(frontiers) > 1:
        blockers.add("graduation_timing_utility_unresolved")
        return WholePlanOptimizationAssessment(
            WholePlanOptimizationStatus.HORIZON_INCOMPARABLE,
            bridge,
            search,
            future_assessment,
            candidates,
            frontiers,
            frozenset(blockers),
        )
    if not frontiers:
        raise WholePlanOptimizationError(
            "complete reachable future search produced no whole-plan candidate"
        )

    frontier = frontiers[0]
    if frontier.unresolved_candidates:
        blockers.add("whole_plan_utility_unresolved")
        return WholePlanOptimizationAssessment(
            WholePlanOptimizationStatus.UTILITY_UNRESOLVED,
            bridge,
            search,
            future_assessment,
            candidates,
            frontiers,
            frozenset(blockers),
        )
    if frontier.unique_proven_best is not None:
        return WholePlanOptimizationAssessment(
            WholePlanOptimizationStatus.OPTIMUM_PROVEN,
            bridge,
            search,
            future_assessment,
            candidates,
            frontiers,
            frozenset(blockers),
        )

    blockers.add("complete_whole_plan_bounds_overlap")
    return WholePlanOptimizationAssessment(
        WholePlanOptimizationStatus.BOUNDED_FRONTIER,
        bridge,
        search,
        future_assessment,
        candidates,
        frontiers,
        frozenset(blockers),
    )
