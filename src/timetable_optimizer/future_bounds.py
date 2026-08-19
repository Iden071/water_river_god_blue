"""Admissible continuation bounds for the Stage 4D future objective.

The exhaustive completion-history search remains the reference implementation. This module
adds only proof-safe optional bounds. For each remaining term it relaxes state-dependent
constraints and evaluates every subset of the explicit scenario opportunity set. Because the
real feasible choices are contained in that relaxed universe, its minimum and maximum are
valid lower/upper utility bounds. If completeness, utility evidence, or enumeration is
unresolved, no bound is returned and no pruning is justified.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from itertools import combinations
from typing import Mapping

from .course_preferences import ProfessorRatingBook
from .future_opportunities import FutureTermOpportunitySet, OpportunitySetStatus
from .future_problem import FuturePlanningProblem
from .future_scenarios import FutureTermScenario, TermActivity
from .future_utility import (
    FutureUtilityHistory,
    TemporalUtilityAggregation,
    TemporalUtilityWeight,
    aggregate_future_utility,
    assess_future_term_utility,
)
from .preferences import PreferenceProfile, PreferenceValue


class FutureBoundError(ValueError):
    """Future-bound inputs violate the Stage 4D objective contract."""


class FutureBoundStatus(str, Enum):
    AVAILABLE = "available"
    INPUT_BLOCKED = "input_blocked"
    EVALUATION_LIMIT = "evaluation_limit"
    UTILITY_UNRESOLVED = "utility_unresolved"


@dataclass(frozen=True)
class FutureTermRelaxedUtilityEnvelope:
    term_id: str
    lower_bound: float
    upper_bound: float
    evaluated_subsets: int
    total_subsets: int
    opportunity_source_id: str


@dataclass(frozen=True)
class FutureTermEnvelopeAssessment:
    term_id: str
    status: FutureBoundStatus
    envelope: FutureTermRelaxedUtilityEnvelope | None
    blocker_codes: frozenset[str]
    evaluated_subsets: int
    total_subsets: int

    @property
    def available(self) -> bool:
        return self.status is FutureBoundStatus.AVAILABLE and self.envelope is not None


@dataclass(frozen=True)
class FutureContinuationUtilityBound:
    status: FutureBoundStatus
    target_term_ids: tuple[str, ...]
    prefix_term_ids: tuple[str, ...]
    lower_bound: float | None
    upper_bound: float | None
    term_envelopes: tuple[FutureTermRelaxedUtilityEnvelope, ...]
    blocker_codes: frozenset[str]
    evaluated_subsets: int
    total_subsets: int
    aggregation_source_id: str
    aggregation_weights: tuple[tuple[str, float], ...]

    @property
    def available(self) -> bool:
        return (
            self.status is FutureBoundStatus.AVAILABLE
            and self.lower_bound is not None
            and self.upper_bound is not None
        )


class FuturePruningStatus(str, Enum):
    PRUNE_PROVEN = "prune_proven"
    KEEP_BOUND_UNAVAILABLE = "keep_bound_unavailable"
    KEEP_INCUMBENT_UNRESOLVED = "keep_incumbent_unresolved"
    KEEP_HORIZON_MISMATCH = "keep_horizon_mismatch"
    KEEP_AGGREGATION_MISMATCH = "keep_aggregation_mismatch"
    KEEP_NOT_DOMINATED = "keep_not_dominated"


@dataclass(frozen=True)
class FuturePruningDecision:
    status: FuturePruningStatus
    reason: str

    @property
    def prune(self) -> bool:
        return self.status is FuturePruningStatus.PRUNE_PROVEN


def _powerset(items):
    items = tuple(items)
    for size in range(len(items) + 1):
        yield from combinations(items, size)


def _aggregation_signature(
    aggregation: TemporalUtilityAggregation,
    term_ids: tuple[str, ...],
) -> tuple[str, tuple[tuple[str, float], ...]]:
    return (
        aggregation.source_id,
        tuple((term_id, aggregation.weight_for(term_id)) for term_id in term_ids),
    )


def _validate_full_aggregation(
    problem: FuturePlanningProblem,
    aggregation: TemporalUtilityAggregation,
) -> None:
    timeline_ids = tuple(term.term_id for term in problem.timeline.terms)
    weight_ids = tuple(weight.term_id for weight in aggregation.weights)
    if set(weight_ids) != set(timeline_ids) or len(weight_ids) != len(timeline_ids):
        raise FutureBoundError(
            "temporal aggregation must cover the full planning timeline exactly"
        )


def _timeline_term(problem: FuturePlanningProblem, term_id: str) -> FutureTermScenario:
    hits = [term for term in problem.timeline.terms if term.term_id == term_id]
    if len(hits) != 1:
        raise FutureBoundError(
            f"expected exactly one future timeline term {term_id!r}, found {len(hits)}"
        )
    return hits[0]


def derive_relaxed_term_utility_envelope(
    term: FutureTermScenario,
    opportunity_set: FutureTermOpportunitySet,
    preference_profile: PreferenceProfile,
    professor_ratings: ProfessorRatingBook,
    *,
    subject_interest: Mapping[str, PreferenceValue] | None = None,
    workload_utility: Mapping[str, PreferenceValue] | None = None,
    difficulty_utility: Mapping[str, PreferenceValue] | None = None,
    max_subset_evaluations: int = 100_000,
) -> FutureTermEnvelopeAssessment:
    """Bound one term over a relaxed universe containing every scenario subset."""

    if max_subset_evaluations <= 0:
        raise FutureBoundError("max_subset_evaluations must be positive")
    if opportunity_set.term_id != term.term_id:
        raise FutureBoundError("term and opportunity-set ids do not match")
    if opportunity_set.status is not OpportunitySetStatus.EXPLICIT_SCENARIO:
        return FutureTermEnvelopeAssessment(
            term.term_id,
            FutureBoundStatus.INPUT_BLOCKED,
            None,
            frozenset({"opportunity_set_not_complete"}),
            0,
            0,
        )

    offerings = tuple(
        sorted(opportunity_set.offerings, key=lambda offering: offering.offering_id)
    )
    if term.activity is TermActivity.LEAVE:
        subsets = ((),)
        total_subsets = 1
    else:
        total_subsets = 2 ** len(offerings)
        if total_subsets > max_subset_evaluations:
            return FutureTermEnvelopeAssessment(
                term.term_id,
                FutureBoundStatus.EVALUATION_LIMIT,
                None,
                frozenset({"term_subset_evaluation_limit"}),
                0,
                total_subsets,
            )
        subsets = _powerset(offerings)

    lower: float | None = None
    upper: float | None = None
    evaluated = 0
    for subset in subsets:
        if evaluated >= max_subset_evaluations:
            return FutureTermEnvelopeAssessment(
                term.term_id,
                FutureBoundStatus.EVALUATION_LIMIT,
                None,
                frozenset({"term_subset_evaluation_limit"}),
                evaluated,
                total_subsets,
            )
        assessed = assess_future_term_utility(
            term,
            tuple(subset),
            preference_profile,
            professor_ratings,
            subject_interest=subject_interest,
            workload_utility=workload_utility,
            difficulty_utility=difficulty_utility,
        )
        evaluated += 1
        bounds = assessed.complete_bounds
        if bounds is None:
            blockers = {"term_utility_incomplete"}
            if assessed.has_heuristics:
                blockers.add("term_utility_heuristic")
            blockers.update(
                f"utility::{dimension}" for dimension in assessed.unresolved_dimensions
            )
            return FutureTermEnvelopeAssessment(
                term.term_id,
                FutureBoundStatus.UTILITY_UNRESOLVED,
                None,
                frozenset(blockers),
                evaluated,
                total_subsets,
            )
        selection_lower, selection_upper = bounds
        lower = selection_lower if lower is None else min(lower, selection_lower)
        upper = selection_upper if upper is None else max(upper, selection_upper)

    assert lower is not None and upper is not None
    envelope = FutureTermRelaxedUtilityEnvelope(
        term.term_id,
        lower,
        upper,
        evaluated,
        total_subsets,
        opportunity_set.source_id,
    )
    return FutureTermEnvelopeAssessment(
        term.term_id,
        FutureBoundStatus.AVAILABLE,
        envelope,
        frozenset(),
        evaluated,
        total_subsets,
    )


def derive_future_continuation_utility_bound(
    problem: FuturePlanningProblem,
    prefix_history: FutureUtilityHistory,
    target_term_ids: tuple[str, ...],
    temporal_aggregation: TemporalUtilityAggregation,
    preference_profile: PreferenceProfile,
    professor_ratings: ProfessorRatingBook,
    *,
    subject_interest: Mapping[str, PreferenceValue] | None = None,
    workload_utility: Mapping[str, PreferenceValue] | None = None,
    difficulty_utility: Mapping[str, PreferenceValue] | None = None,
    max_subset_evaluations_per_term: int = 100_000,
) -> FutureContinuationUtilityBound:
    """Bound every extension of one utility prefix to one fixed graduation horizon."""

    _validate_full_aggregation(problem, temporal_aggregation)
    timeline_ids = tuple(term.term_id for term in problem.timeline.terms)
    if timeline_ids[: len(target_term_ids)] != target_term_ids:
        raise FutureBoundError("target horizon must be a prefix of the planning timeline")
    if target_term_ids[: len(prefix_history.term_ids)] != prefix_history.term_ids:
        raise FutureBoundError("utility history must be a prefix of the target horizon")

    signature = _aggregation_signature(temporal_aggregation, target_term_ids)
    if not problem.exact_search_ready:
        return FutureContinuationUtilityBound(
            FutureBoundStatus.INPUT_BLOCKED,
            target_term_ids,
            prefix_history.term_ids,
            None,
            None,
            (),
            problem.blocker_codes,
            0,
            0,
            signature[0],
            signature[1],
        )

    prefix_aggregation = TemporalUtilityAggregation(
        source_id=temporal_aggregation.source_id,
        weights=tuple(
            TemporalUtilityWeight(term_id, temporal_aggregation.weight_for(term_id))
            for term_id in prefix_history.term_ids
        ),
        note="Prefix used for admissible continuation bound.",
    )
    prefix_aggregate = aggregate_future_utility(prefix_history, prefix_aggregation)
    prefix_bounds = prefix_aggregate.complete_bounds
    if prefix_bounds is None:
        blockers = {"prefix_utility_incomplete"}
        blockers.update(
            f"utility::{dimension}"
            for dimension in prefix_aggregate.unresolved_dimensions
        )
        if prefix_aggregate.heuristic_point_delta != 0.0:
            blockers.add("prefix_utility_heuristic")
        return FutureContinuationUtilityBound(
            FutureBoundStatus.UTILITY_UNRESOLVED,
            target_term_ids,
            prefix_history.term_ids,
            None,
            None,
            (),
            frozenset(blockers),
            0,
            0,
            signature[0],
            signature[1],
        )

    lower, upper = prefix_bounds
    envelopes: list[FutureTermRelaxedUtilityEnvelope] = []
    evaluated_total = 0
    subset_total = 0
    start_index = len(prefix_history.term_ids)

    for term_id in target_term_ids[start_index:]:
        weight = temporal_aggregation.weight_for(term_id)
        if weight == 0.0:
            continue
        assessed = derive_relaxed_term_utility_envelope(
            _timeline_term(problem, term_id),
            problem.opportunities.term(term_id),
            preference_profile,
            professor_ratings,
            subject_interest=subject_interest,
            workload_utility=workload_utility,
            difficulty_utility=difficulty_utility,
            max_subset_evaluations=max_subset_evaluations_per_term,
        )
        evaluated_total += assessed.evaluated_subsets
        subset_total += assessed.total_subsets
        if not assessed.available:
            return FutureContinuationUtilityBound(
                assessed.status,
                target_term_ids,
                prefix_history.term_ids,
                None,
                None,
                tuple(envelopes),
                assessed.blocker_codes,
                evaluated_total,
                subset_total,
                signature[0],
                signature[1],
            )
        assert assessed.envelope is not None
        envelopes.append(assessed.envelope)
        lower += weight * assessed.envelope.lower_bound
        upper += weight * assessed.envelope.upper_bound

    return FutureContinuationUtilityBound(
        FutureBoundStatus.AVAILABLE,
        target_term_ids,
        prefix_history.term_ids,
        lower,
        upper,
        tuple(envelopes),
        frozenset(),
        evaluated_total,
        subset_total,
        signature[0],
        signature[1],
    )


def compare_continuation_bound_to_incumbent(
    bound: FutureContinuationUtilityBound,
    incumbent_history: FutureUtilityHistory,
    incumbent_aggregation: TemporalUtilityAggregation,
) -> FuturePruningDecision:
    """Prove pruning only when an incumbent lower bound exceeds the relaxed upper bound."""

    if not bound.available:
        return FuturePruningDecision(
            FuturePruningStatus.KEEP_BOUND_UNAVAILABLE,
            "continuation bound is unavailable; branch cannot be pruned",
        )
    if incumbent_history.term_ids != bound.target_term_ids:
        return FuturePruningDecision(
            FuturePruningStatus.KEEP_HORIZON_MISMATCH,
            "incumbent and partial branch do not share one graduation horizon",
        )
    signature = _aggregation_signature(incumbent_aggregation, incumbent_history.term_ids)
    if signature != (bound.aggregation_source_id, bound.aggregation_weights):
        return FuturePruningDecision(
            FuturePruningStatus.KEEP_AGGREGATION_MISMATCH,
            "incumbent and continuation bound use different temporal objectives",
        )

    incumbent = aggregate_future_utility(incumbent_history, incumbent_aggregation)
    incumbent_bounds = incumbent.complete_bounds
    if incumbent_bounds is None:
        return FuturePruningDecision(
            FuturePruningStatus.KEEP_INCUMBENT_UNRESOLVED,
            "incumbent whole-history utility is incomplete and cannot justify pruning",
        )

    incumbent_lower, _ = incumbent_bounds
    assert bound.upper_bound is not None
    if incumbent_lower > bound.upper_bound:
        return FuturePruningDecision(
            FuturePruningStatus.PRUNE_PROVEN,
            "incumbent lower bound is strictly above every continuation allowed by the relaxed upper bound",
        )
    return FuturePruningDecision(
        FuturePruningStatus.KEEP_NOT_DOMINATED,
        "continuation upper bound is not strictly below the incumbent lower bound",
    )
