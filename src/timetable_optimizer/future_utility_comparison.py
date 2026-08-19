"""Safe comparison rules for Stage 4D future utility histories.

The future optimizer must not recreate the old pattern of ranking with one proxy score and
then optimizing a different objective.  This module defines the deliberately conservative
comparison relation that an exact search may use before any branch-and-bound logic exists.

A strict preference claim is allowed only when:

* both histories cover the same academic horizon;
* both use the same explicitly sourced temporal aggregation policy;
* both whole-history utilities have complete numerical bounds; and
* one history's lower bound is strictly above the other's upper bound.

Overlapping intervals are not ordered.  Heuristic or unresolved evidence is not coerced to
zero.  Histories ending in different terms are not compared here because doing so would
implicitly assign a value to earlier/later graduation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .future_utility import (
    AggregatedFutureUtility,
    FutureUtilityHistory,
    TemporalUtilityAggregation,
    aggregate_future_utility,
)


class FutureUtilityComparisonError(ValueError):
    """Future utility comparison inputs violate the Stage 4D comparison contract."""


class FutureUtilityComparisonStatus(str, Enum):
    LEFT_STRICTLY_BETTER = "left_strictly_better"
    RIGHT_STRICTLY_BETTER = "right_strictly_better"
    EXACT_TIE = "exact_tie"
    BOUNDS_OVERLAP = "bounds_overlap"
    UNRESOLVED_UTILITY = "unresolved_utility"
    INCOMPATIBLE_HORIZON = "incompatible_horizon"
    INCOMPATIBLE_AGGREGATION = "incompatible_aggregation"


@dataclass(frozen=True)
class FutureUtilityComparison:
    status: FutureUtilityComparisonStatus
    left: AggregatedFutureUtility | None
    right: AggregatedFutureUtility | None
    reason: str

    @property
    def proves_strict_order(self) -> bool:
        return self.status in {
            FutureUtilityComparisonStatus.LEFT_STRICTLY_BETTER,
            FutureUtilityComparisonStatus.RIGHT_STRICTLY_BETTER,
        }

    @property
    def left_strictly_dominates(self) -> bool:
        return self.status is FutureUtilityComparisonStatus.LEFT_STRICTLY_BETTER

    @property
    def right_strictly_dominates(self) -> bool:
        return self.status is FutureUtilityComparisonStatus.RIGHT_STRICTLY_BETTER

    @property
    def safe_for_pruning(self) -> bool:
        """Only a proved strict order can eliminate the worse complete history."""

        return self.proves_strict_order


def _aggregation_signature(
    aggregation: TemporalUtilityAggregation,
) -> tuple[str, tuple[tuple[str, float], ...]]:
    return (
        aggregation.source_id,
        tuple(sorted((weight.term_id, weight.weight) for weight in aggregation.weights)),
    )


def compare_future_utility_histories(
    left_history: FutureUtilityHistory,
    left_aggregation: TemporalUtilityAggregation,
    right_history: FutureUtilityHistory,
    right_aggregation: TemporalUtilityAggregation,
) -> FutureUtilityComparison:
    """Compare two future histories using only proof-safe whole-history evidence."""

    if left_history.term_ids != right_history.term_ids:
        return FutureUtilityComparison(
            status=FutureUtilityComparisonStatus.INCOMPATIBLE_HORIZON,
            left=None,
            right=None,
            reason=(
                "future histories end on different academic horizons; graduation timing has not been assigned utility"
            ),
        )

    if _aggregation_signature(left_aggregation) != _aggregation_signature(right_aggregation):
        return FutureUtilityComparison(
            status=FutureUtilityComparisonStatus.INCOMPATIBLE_AGGREGATION,
            left=None,
            right=None,
            reason=(
                "future histories use different temporal weighting assumptions and cannot be ranked on one objective"
            ),
        )

    left = aggregate_future_utility(left_history, left_aggregation)
    right = aggregate_future_utility(right_history, right_aggregation)
    left_bounds = left.complete_bounds
    right_bounds = right.complete_bounds

    if left_bounds is None or right_bounds is None:
        return FutureUtilityComparison(
            status=FutureUtilityComparisonStatus.UNRESOLVED_UTILITY,
            left=left,
            right=right,
            reason=(
                "at least one whole-history utility contains heuristic or unresolved evidence; no pruning order is justified"
            ),
        )

    left_lower, left_upper = left_bounds
    right_lower, right_upper = right_bounds

    if left_lower > right_upper:
        return FutureUtilityComparison(
            status=FutureUtilityComparisonStatus.LEFT_STRICTLY_BETTER,
            left=left,
            right=right,
            reason="left whole-history lower bound is strictly above right upper bound",
        )

    if right_lower > left_upper:
        return FutureUtilityComparison(
            status=FutureUtilityComparisonStatus.RIGHT_STRICTLY_BETTER,
            left=left,
            right=right,
            reason="right whole-history lower bound is strictly above left upper bound",
        )

    if (
        left_lower == left_upper
        and right_lower == right_upper
        and left_lower == right_lower
    ):
        return FutureUtilityComparison(
            status=FutureUtilityComparisonStatus.EXACT_TIE,
            left=left,
            right=right,
            reason="both whole-history utilities are the same exact value",
        )

    return FutureUtilityComparison(
        status=FutureUtilityComparisonStatus.BOUNDS_OVERLAP,
        left=left,
        right=right,
        reason=(
            "complete whole-history intervals overlap; available preference evidence does not prove an order"
        ),
    )
