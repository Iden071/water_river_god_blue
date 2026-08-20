"""Proof-safe whole-plan comparison conditional on unresolved Fall timetable shape.

Some Fall timetable preferences are intentionally still symbolic: Friday-event value,
three-period-run burden, longer-run corrections, and the extra value of multi-day
weekend-attached no-campus runs.  Two whole plans can nevertheless be ordered without pricing
those terms when they contain **exactly the same symbolic coefficients**.  The unknown additive
expression then cancels.

This module is deliberately narrow.  It refuses comparison when:

* the graduation horizon or temporal objective differs;
* either future utility is incomplete;
* present hard feasibility is unresolved;
* any heuristic utility remains;
* any unresolved utility exists besides the recognized Fall shape terms; or
* the Fall shape coefficient vectors differ.

Thus a successful strict comparison is valid for every possible numerical assignment to the
shared symbolic Fall-shape terms.  The module does not turn symbolic terms into zero and is
not yet wired into streaming retention or branch pruning.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite

from .fall_unresolved_shape import is_fall_unresolved_shape_dimension
from .whole_plan_optimization import WholePlanUtilityCandidate


class FallConditionalUtilityError(ValueError):
    """A whole-plan candidate violates the conditional-comparison contract."""


class FallConditionalComparisonStatus(str, Enum):
    LEFT_STRICTLY_BETTER = "left_strictly_better"
    RIGHT_STRICTLY_BETTER = "right_strictly_better"
    EXACT_TIE = "exact_tie"
    NUMERIC_BOUNDS_OVERLAP = "numeric_bounds_overlap"
    SHAPE_INCOMPARABLE = "shape_incomparable"
    OBJECTIVE_INCOMPARABLE = "objective_incomparable"
    INPUT_BLOCKED = "input_blocked"


@dataclass(frozen=True)
class FallShapeCoefficientVector:
    """Weighted coefficients multiplying the unresolved Fall-shape scalar values."""

    term_id: str
    coefficients: tuple[tuple[str, float], ...]

    def __post_init__(self) -> None:
        if not self.term_id.strip():
            raise FallConditionalUtilityError("shape vector requires a nonblank term id")
        previous = ""
        for dimension, coefficient in self.coefficients:
            if not is_fall_unresolved_shape_dimension(dimension):
                raise FallConditionalUtilityError(
                    f"non-shape dimension in Fall shape vector: {dimension!r}"
                )
            if dimension <= previous:
                raise FallConditionalUtilityError(
                    "shape vector dimensions must be unique and sorted"
                )
            if not isfinite(coefficient) or coefficient <= 0:
                raise FallConditionalUtilityError(
                    "stored symbolic shape coefficients must be finite and positive"
                )
            previous = dimension


@dataclass(frozen=True)
class FallConditionalComparison:
    status: FallConditionalComparisonStatus
    shared_shape: FallShapeCoefficientVector | None
    reason: str

    @property
    def proves_strict_order(self) -> bool:
        return self.status in {
            FallConditionalComparisonStatus.LEFT_STRICTLY_BETTER,
            FallConditionalComparisonStatus.RIGHT_STRICTLY_BETTER,
        }


def _present_weight(candidate: WholePlanUtilityCandidate) -> float:
    term_id = candidate.present_utility.term_id
    hits = [
        weight
        for weighted_term, weight in candidate.aggregation_weights
        if weighted_term == term_id
    ]
    if len(hits) != 1:
        raise FallConditionalUtilityError(
            f"whole-plan candidate must contain exactly one weight for present term {term_id!r}"
        )
    return hits[0]


def _shape_vector_and_blocker(
    candidate: WholePlanUtilityCandidate,
) -> tuple[FallShapeCoefficientVector | None, str | None]:
    present = candidate.present_utility
    if present.known_infeasible:
        return None, "present candidate is known infeasible"
    if not present.hard_feasibility_resolved:
        return None, "present hard feasibility is unresolved"
    if present.has_heuristics or candidate.heuristic_point_delta != 0.0:
        return None, "heuristic utility remains"
    if not candidate.future_candidate.utility_complete:
        return None, "future utility is incomplete"

    weight = _present_weight(candidate)
    shape_present_ids: set[str] = set()
    coefficients: list[tuple[str, float]] = []
    for term in present.unresolved_timetable_terms:
        prefix = "timetable::"
        if not term.dimension_id.startswith(prefix):
            return None, "present unresolved timetable term lacks canonical timetable prefix"
        raw_dimension = term.dimension_id[len(prefix) :]
        if not is_fall_unresolved_shape_dimension(raw_dimension):
            return None, f"non-shape timetable uncertainty remains: {raw_dimension}"
        shape_present_ids.add(term.dimension_id)
        coefficient = weight * term.quantity
        if coefficient > 0:
            coefficients.append((raw_dimension, coefficient))

    other_present = set(present.unresolved_dimensions) - shape_present_ids
    if other_present:
        return None, "non-shape present utility remains unresolved: " + ", ".join(
            sorted(other_present)
        )

    expected_whole_shape_ids = (
        {
            f"{present.term_id}::{dimension_id}"
            for dimension_id in shape_present_ids
        }
        if weight > 0
        else set()
    )
    other_whole = set(candidate.unresolved_dimensions) - expected_whole_shape_ids
    missing_whole = expected_whole_shape_ids - set(candidate.unresolved_dimensions)
    if other_whole:
        return None, "non-shape whole-plan utility remains unresolved: " + ", ".join(
            sorted(other_whole)
        )
    if missing_whole:
        raise FallConditionalUtilityError(
            "whole-plan unresolved set lost active present shape terms: "
            + ", ".join(sorted(missing_whole))
        )

    coefficients.sort()
    return (
        FallShapeCoefficientVector(
            term_id=present.term_id,
            coefficients=tuple(coefficients),
        ),
        None,
    )


def compare_whole_plans_conditional_on_fall_shape(
    left: WholePlanUtilityCandidate,
    right: WholePlanUtilityCandidate,
) -> FallConditionalComparison:
    """Compare two plans for every assignment to one shared symbolic Fall-shape vector."""

    if left.term_ids != right.term_ids:
        return FallConditionalComparison(
            FallConditionalComparisonStatus.OBJECTIVE_INCOMPARABLE,
            None,
            "graduation horizons differ",
        )
    left_objective = (left.aggregation_source_id, left.aggregation_weights)
    right_objective = (right.aggregation_source_id, right.aggregation_weights)
    if left_objective != right_objective:
        return FallConditionalComparison(
            FallConditionalComparisonStatus.OBJECTIVE_INCOMPARABLE,
            None,
            "temporal objectives differ",
        )

    left_shape, left_blocker = _shape_vector_and_blocker(left)
    right_shape, right_blocker = _shape_vector_and_blocker(right)
    if left_blocker or right_blocker:
        pieces = []
        if left_blocker:
            pieces.append("left: " + left_blocker)
        if right_blocker:
            pieces.append("right: " + right_blocker)
        return FallConditionalComparison(
            FallConditionalComparisonStatus.INPUT_BLOCKED,
            None,
            "; ".join(pieces),
        )
    assert left_shape is not None and right_shape is not None
    if left_shape != right_shape:
        return FallConditionalComparison(
            FallConditionalComparisonStatus.SHAPE_INCOMPARABLE,
            None,
            "unresolved Fall-shape coefficient vectors differ",
        )

    if left.measured_lower > right.measured_upper:
        return FallConditionalComparison(
            FallConditionalComparisonStatus.LEFT_STRICTLY_BETTER,
            left_shape,
            "left numeric lower bound exceeds right numeric upper bound after shared symbolic terms cancel",
        )
    if right.measured_lower > left.measured_upper:
        return FallConditionalComparison(
            FallConditionalComparisonStatus.RIGHT_STRICTLY_BETTER,
            left_shape,
            "right numeric lower bound exceeds left numeric upper bound after shared symbolic terms cancel",
        )
    if (
        left.measured_lower == left.measured_upper
        == right.measured_lower
        == right.measured_upper
    ):
        return FallConditionalComparison(
            FallConditionalComparisonStatus.EXACT_TIE,
            left_shape,
            "numeric components are exactly equal and symbolic Fall-shape expressions are identical",
        )
    return FallConditionalComparison(
        FallConditionalComparisonStatus.NUMERIC_BOUNDS_OVERLAP,
        left_shape,
        "shared symbolic terms cancel, but remaining numeric intervals overlap",
    )
