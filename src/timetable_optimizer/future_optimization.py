"""Proof-safe future utility frontier for Stage 4D.

This is the first optimization layer above exhaustive completion-history enumeration.  It is
intentionally conservative and performs **no branch-and-bound pruning** yet.

For one explicit temporal weighting policy it:

1. maps every exact completion witness to its non-lossy utility history;
2. keeps different graduation horizons in separate frontiers because graduation timing has
   not been assigned utility;
3. retains every heuristic/unresolved candidate;
4. among complete candidates on the same horizon, discards a candidate only when another
   candidate's whole-history lower bound is strictly above its upper bound.

Thus a reported optimum is a proof about the same final utility objective, not a preliminary
ranking proxy.  Search truncation or unresolved feasibility prevents an optimum claim even
if a strong known candidate has already been found.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
from typing import Mapping

from .course_preferences import ProfessorRatingBook
from .future_completion_search import (
    FutureCompletionSearchResult,
    FutureCompletionSearchStatus,
)
from .future_problem import FuturePlanningProblem
from .future_reachability import FutureReachabilityWitness
from .future_utility import (
    AggregatedFutureUtility,
    FutureUtilityHistory,
    TemporalUtilityAggregation,
    TemporalUtilityWeight,
    aggregate_future_utility,
)
from .future_utility_comparison import compare_future_utility_histories
from .future_witness_utility import assess_future_witness_utility
from .preferences import PreferenceProfile, PreferenceValue


class FutureOptimizationError(ValueError):
    """Future optimization inputs violate the Stage 4D objective contract."""


class FutureOptimizationStatus(str, Enum):
    OPTIMUM_PROVEN = "optimum_proven"
    BOUNDED_FRONTIER = "bounded_frontier"
    UTILITY_UNRESOLVED = "utility_unresolved"
    HORIZON_INCOMPARABLE = "horizon_incomparable"
    SEARCH_INCOMPLETE = "search_incomplete"
    PROVEN_UNREACHABLE = "proven_unreachable"
    INPUT_BLOCKED = "input_blocked"


@dataclass(frozen=True)
class FutureUtilityCandidate:
    candidate_id: str
    witness: FutureReachabilityWitness
    history: FutureUtilityHistory
    aggregation: TemporalUtilityAggregation
    aggregate: AggregatedFutureUtility

    @property
    def term_ids(self) -> tuple[str, ...]:
        return self.history.term_ids

    @property
    def complete_bounds(self) -> tuple[float, float] | None:
        return self.aggregate.complete_bounds

    @property
    def utility_complete(self) -> bool:
        return self.complete_bounds is not None


@dataclass(frozen=True)
class FutureUtilityHorizonFrontier:
    term_ids: tuple[str, ...]
    candidates: tuple[FutureUtilityCandidate, ...]
    undominated_complete: tuple[FutureUtilityCandidate, ...]
    unresolved_candidates: tuple[FutureUtilityCandidate, ...]
    strictly_dominated_candidate_ids: frozenset[str]

    @property
    def completion_term_id(self) -> str | None:
        return self.term_ids[-1] if self.term_ids else None

    @property
    def unique_proven_best(self) -> FutureUtilityCandidate | None:
        if self.unresolved_candidates or len(self.undominated_complete) != 1:
            return None
        return self.undominated_complete[0]

    @property
    def utility_order_fully_resolved(self) -> bool:
        return not self.unresolved_candidates and len(self.undominated_complete) == 1


@dataclass(frozen=True)
class FutureOptimizationAssessment:
    status: FutureOptimizationStatus
    search: FutureCompletionSearchResult
    candidates: tuple[FutureUtilityCandidate, ...]
    frontiers: tuple[FutureUtilityHorizonFrontier, ...]
    blocker_codes: frozenset[str]

    @property
    def optimum_proven(self) -> bool:
        return self.status is FutureOptimizationStatus.OPTIMUM_PROVEN

    @property
    def proven_best(self) -> FutureUtilityCandidate | None:
        if not self.optimum_proven or len(self.frontiers) != 1:
            return None
        return self.frontiers[0].unique_proven_best


def _candidate_id(witness: FutureReachabilityWitness) -> str:
    payload = tuple(
        (step.term_id, step.offering_ids, step.action_ids) for step in witness.steps
    )
    digest = hashlib.sha256(repr(payload).encode("utf-8")).hexdigest()[:16]
    return f"future-history-{digest}"


def _validate_master_aggregation(
    problem: FuturePlanningProblem,
    aggregation: TemporalUtilityAggregation,
) -> None:
    timeline_ids = tuple(term.term_id for term in problem.timeline.terms)
    weight_ids = tuple(weight.term_id for weight in aggregation.weights)
    if set(weight_ids) != set(timeline_ids) or len(weight_ids) != len(timeline_ids):
        missing = sorted(set(timeline_ids) - set(weight_ids))
        extra = sorted(set(weight_ids) - set(timeline_ids))
        pieces: list[str] = []
        if missing:
            pieces.append("missing=" + ",".join(missing))
        if extra:
            pieces.append("extra=" + ",".join(extra))
        raise FutureOptimizationError(
            "master temporal aggregation must cover the full planning timeline exactly"
            + (": " + "; ".join(pieces) if pieces else "")
        )


def _prefix_aggregation(
    master: TemporalUtilityAggregation,
    term_ids: tuple[str, ...],
) -> TemporalUtilityAggregation:
    weights = tuple(
        TemporalUtilityWeight(term_id, master.weight_for(term_id))
        for term_id in term_ids
    )
    return TemporalUtilityAggregation(
        source_id=master.source_id,
        weights=weights,
        note=(
            "Prefix of master temporal policy for one degree-completion horizon. "
            + master.note
        ).strip(),
    )


def _build_frontier(
    candidates: tuple[FutureUtilityCandidate, ...],
) -> FutureUtilityHorizonFrontier:
    if not candidates:
        raise FutureOptimizationError("cannot build a frontier from zero candidates")
    term_ids = candidates[0].term_ids
    if any(candidate.term_ids != term_ids for candidate in candidates):
        raise FutureOptimizationError(
            "future utility frontier candidates must share one completion horizon"
        )

    complete = tuple(candidate for candidate in candidates if candidate.utility_complete)
    unresolved = tuple(
        candidate for candidate in candidates if not candidate.utility_complete
    )
    dominated: set[str] = set()

    for candidate in complete:
        for challenger in complete:
            if challenger.candidate_id == candidate.candidate_id:
                continue
            comparison = compare_future_utility_histories(
                challenger.history,
                challenger.aggregation,
                candidate.history,
                candidate.aggregation,
            )
            if comparison.left_strictly_dominates:
                dominated.add(candidate.candidate_id)
                break

    undominated = tuple(
        candidate
        for candidate in complete
        if candidate.candidate_id not in dominated
    )
    return FutureUtilityHorizonFrontier(
        term_ids=term_ids,
        candidates=candidates,
        undominated_complete=undominated,
        unresolved_candidates=unresolved,
        strictly_dominated_candidate_ids=frozenset(dominated),
    )


def build_safe_future_utility_frontiers(
    candidates: tuple[FutureUtilityCandidate, ...],
) -> tuple[FutureUtilityHorizonFrontier, ...]:
    """Group candidates by horizon and apply only strict complete-bound dominance."""

    by_horizon: dict[tuple[str, ...], list[FutureUtilityCandidate]] = {}
    for candidate in candidates:
        by_horizon.setdefault(candidate.term_ids, []).append(candidate)

    return tuple(
        _build_frontier(tuple(by_horizon[horizon]))
        for horizon in sorted(by_horizon, key=lambda ids: (len(ids), ids))
    )


def assess_future_completion_utility(
    search: FutureCompletionSearchResult,
    problem: FuturePlanningProblem,
    preference_profile: PreferenceProfile,
    professor_ratings: ProfessorRatingBook,
    temporal_aggregation: TemporalUtilityAggregation,
    *,
    subject_interest: Mapping[str, PreferenceValue] | None = None,
    workload_utility: Mapping[str, PreferenceValue] | None = None,
    difficulty_utility: Mapping[str, PreferenceValue] | None = None,
) -> FutureOptimizationAssessment:
    """Evaluate all discovered completion histories and build proof-safe frontiers."""

    _validate_master_aggregation(problem, temporal_aggregation)

    candidates: list[FutureUtilityCandidate] = []
    seen_ids: set[str] = set()
    for witness in search.witnesses:
        assessed = assess_future_witness_utility(
            problem,
            witness,
            preference_profile,
            professor_ratings,
            subject_interest=subject_interest,
            workload_utility=workload_utility,
            difficulty_utility=difficulty_utility,
        )
        history = assessed.utility_history
        aggregation = _prefix_aggregation(temporal_aggregation, history.term_ids)
        aggregate = aggregate_future_utility(history, aggregation)
        candidate_id = _candidate_id(witness)
        if candidate_id in seen_ids:
            # Identical action/offering histories have identical future utility and degree
            # transitions; collapse exact duplicate enumeration artifacts only.
            continue
        seen_ids.add(candidate_id)
        candidates.append(
            FutureUtilityCandidate(
                candidate_id=candidate_id,
                witness=witness,
                history=history,
                aggregation=aggregation,
                aggregate=aggregate,
            )
        )

    candidate_tuple = tuple(candidates)
    frontiers = build_safe_future_utility_frontiers(candidate_tuple) if candidate_tuple else ()
    blockers: set[str] = set()

    if search.status is FutureCompletionSearchStatus.INPUT_BLOCKED:
        blockers.update(search.input_blocker_codes)
        return FutureOptimizationAssessment(
            status=FutureOptimizationStatus.INPUT_BLOCKED,
            search=search,
            candidates=candidate_tuple,
            frontiers=frontiers,
            blocker_codes=frozenset(blockers),
        )

    if search.status is FutureCompletionSearchStatus.PROVEN_UNREACHABLE:
        return FutureOptimizationAssessment(
            status=FutureOptimizationStatus.PROVEN_UNREACHABLE,
            search=search,
            candidates=(),
            frontiers=(),
            blocker_codes=frozenset(),
        )

    if not search.enumeration_complete:
        blockers.add("completion_history_search_incomplete")
        blockers.update(unknown.code for unknown in search.unknowns)
        return FutureOptimizationAssessment(
            status=FutureOptimizationStatus.SEARCH_INCOMPLETE,
            search=search,
            candidates=candidate_tuple,
            frontiers=frontiers,
            blocker_codes=frozenset(blockers),
        )

    if len(frontiers) > 1:
        blockers.add("graduation_timing_utility_unresolved")
        if any(frontier.unresolved_candidates for frontier in frontiers):
            blockers.add("future_utility_unresolved")
        return FutureOptimizationAssessment(
            status=FutureOptimizationStatus.HORIZON_INCOMPARABLE,
            search=search,
            candidates=candidate_tuple,
            frontiers=frontiers,
            blocker_codes=frozenset(blockers),
        )

    if not frontiers:
        # COMPLETE search with no witnesses should normally be PROVEN_UNREACHABLE; guard
        # against inconsistent externally constructed search results.
        raise FutureOptimizationError(
            "complete completion-history search contains no witness and is not marked unreachable"
        )

    frontier = frontiers[0]
    if frontier.unresolved_candidates:
        blockers.add("future_utility_unresolved")
        return FutureOptimizationAssessment(
            status=FutureOptimizationStatus.UTILITY_UNRESOLVED,
            search=search,
            candidates=candidate_tuple,
            frontiers=frontiers,
            blocker_codes=frozenset(blockers),
        )

    if frontier.unique_proven_best is not None:
        return FutureOptimizationAssessment(
            status=FutureOptimizationStatus.OPTIMUM_PROVEN,
            search=search,
            candidates=candidate_tuple,
            frontiers=frontiers,
            blocker_codes=frozenset(),
        )

    blockers.add("complete_utility_bounds_overlap")
    return FutureOptimizationAssessment(
        status=FutureOptimizationStatus.BOUNDED_FRONTIER,
        search=search,
        candidates=candidate_tuple,
        frontiers=frontiers,
        blocker_codes=frozenset(blockers),
    )
