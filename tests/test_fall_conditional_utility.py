import unittest

from timetable_optimizer.fall_conditional_utility import (
    FallConditionalComparisonStatus,
    compare_whole_plans_conditional_on_fall_shape,
)
from timetable_optimizer.present_utility import PresentTermUtilityAssessment
from timetable_optimizer.timetable_utility import UnresolvedUtilityDimension
from timetable_optimizer.whole_plan_optimization import WholePlanUtilityCandidate


class DummyFutureCandidate:
    def __init__(self, complete=True):
        self.utility_complete = complete


def present(*, shape_terms=(), other_unresolved=(), heuristic=False):
    unresolved_shape_ids = {term.dimension_id for term in shape_terms}
    return PresentTermUtilityAssessment(
        term_id="2026F",
        section_ids=("A-01",),
        contributions=(),
        measured_lower=0.0,
        measured_upper=0.0,
        heuristic_point_delta=0.0,
        unresolved_dimensions=frozenset(unresolved_shape_ids | set(other_unresolved)),
        unresolved_timetable_terms=tuple(shape_terms),
        known_infeasible=False,
        hard_feasibility_resolved=True,
    )


def shape(dimension, quantity):
    return UnresolvedUtilityDimension(
        dimension_id=f"timetable::{dimension}",
        quantity=quantity,
        reason="test unresolved shape",
    )


def whole(
    name,
    *,
    lower,
    upper,
    shape_terms=(),
    other_present_unresolved=(),
    other_whole_unresolved=(),
    future_complete=True,
    fall_weight=1.0,
    objective="user:time-neutral",
):
    present_utility = present(
        shape_terms=shape_terms,
        other_unresolved=other_present_unresolved,
    )
    unresolved = set(other_whole_unresolved)
    if fall_weight > 0:
        unresolved.update(
            f"2026F::{term.dimension_id}" for term in shape_terms
        )
        unresolved.update(
            f"2026F::{dimension}" for dimension in other_present_unresolved
        )
    return WholePlanUtilityCandidate(
        candidate_id=name,
        fall_candidate_id=name,
        present_utility=present_utility,
        future_candidate=DummyFutureCandidate(future_complete),
        term_ids=("2026F",),
        measured_lower=lower,
        measured_upper=upper,
        heuristic_point_delta=0.0,
        unresolved_dimensions=frozenset(unresolved),
        aggregation_source_id=objective,
        aggregation_weights=(("2026F", fall_weight),),
    )


class FallConditionalUtilityTests(unittest.TestCase):
    def test_same_symbolic_shape_can_prove_strict_order_without_pricing_it(self):
        terms = (
            shape("friday_event_window_free", 1.0),
            shape("three_fixed_period_run", 3.0),
        )
        left = whole("left", lower=10.0, upper=11.0, shape_terms=terms)
        right = whole("right", lower=5.0, upper=6.0, shape_terms=terms)

        result = compare_whole_plans_conditional_on_fall_shape(left, right)
        self.assertEqual(
            result.status,
            FallConditionalComparisonStatus.LEFT_STRICTLY_BETTER,
        )
        self.assertTrue(result.proves_strict_order)
        self.assertIsNotNone(result.shared_shape)
        self.assertEqual(
            result.shared_shape.coefficients,
            (("friday_event_window_free", 1.0), ("three_fixed_period_run", 3.0)),
        )

    def test_different_shape_quantity_is_not_cancelled(self):
        left = whole(
            "left",
            lower=10.0,
            upper=10.0,
            shape_terms=(shape("three_fixed_period_run", 1.0),),
        )
        right = whole(
            "right",
            lower=0.0,
            upper=0.0,
            shape_terms=(shape("three_fixed_period_run", 2.0),),
        )
        result = compare_whole_plans_conditional_on_fall_shape(left, right)
        self.assertEqual(
            result.status,
            FallConditionalComparisonStatus.SHAPE_INCOMPARABLE,
        )

    def test_non_shape_present_unknown_blocks_conditional_dominance(self):
        terms = (shape("friday_event_window_free", 1.0),)
        left = whole(
            "left",
            lower=10.0,
            upper=10.0,
            shape_terms=terms,
            other_present_unresolved=("course::A-01::workload",),
        )
        right = whole("right", lower=0.0, upper=0.0, shape_terms=terms)
        result = compare_whole_plans_conditional_on_fall_shape(left, right)
        self.assertEqual(result.status, FallConditionalComparisonStatus.INPUT_BLOCKED)
        self.assertIn("non-shape present", result.reason)

    def test_incomplete_future_blocks_conditional_dominance(self):
        terms = (shape("friday_event_window_free", 1.0),)
        left = whole(
            "left",
            lower=10.0,
            upper=10.0,
            shape_terms=terms,
            future_complete=False,
        )
        right = whole("right", lower=0.0, upper=0.0, shape_terms=terms)
        result = compare_whole_plans_conditional_on_fall_shape(left, right)
        self.assertEqual(result.status, FallConditionalComparisonStatus.INPUT_BLOCKED)
        self.assertIn("future utility is incomplete", result.reason)

    def test_identical_numeric_point_and_symbolic_expression_is_exact_tie(self):
        terms = (
            shape("weekend_attached_presence_free_extra_total_2", 1.0),
        )
        left = whole("left", lower=7.0, upper=7.0, shape_terms=terms)
        right = whole("right", lower=7.0, upper=7.0, shape_terms=terms)
        result = compare_whole_plans_conditional_on_fall_shape(left, right)
        self.assertEqual(result.status, FallConditionalComparisonStatus.EXACT_TIE)

    def test_same_shape_but_overlapping_numeric_intervals_is_not_forced(self):
        terms = (shape("three_fixed_period_run", 2.0),)
        left = whole("left", lower=4.0, upper=8.0, shape_terms=terms)
        right = whole("right", lower=6.0, upper=9.0, shape_terms=terms)
        result = compare_whole_plans_conditional_on_fall_shape(left, right)
        self.assertEqual(
            result.status,
            FallConditionalComparisonStatus.NUMERIC_BOUNDS_OVERLAP,
        )

    def test_different_temporal_objective_is_not_compared(self):
        terms = (shape("three_fixed_period_run", 2.0),)
        left = whole("left", lower=10.0, upper=10.0, shape_terms=terms)
        right = whole(
            "right",
            lower=0.0,
            upper=0.0,
            shape_terms=terms,
            objective="different-policy",
        )
        result = compare_whole_plans_conditional_on_fall_shape(left, right)
        self.assertEqual(
            result.status,
            FallConditionalComparisonStatus.OBJECTIVE_INCOMPARABLE,
        )


if __name__ == "__main__":
    unittest.main()
