import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.future_utility import (  # noqa: E402
    FutureTermUtilityAssessment,
    FutureUtilityHistory,
    TemporalUtilityAggregation,
    TemporalUtilityWeight,
)
from timetable_optimizer.future_utility_comparison import (  # noqa: E402
    FutureUtilityComparisonStatus,
    compare_future_utility_histories,
)
from timetable_optimizer.timetable_utility import (  # noqa: E402
    PartialUtilityAssessment,
    UnresolvedUtilityDimension,
)


def complete_timetable(lower=0.0, upper=0.0):
    return PartialUtilityAssessment(
        contributions=(),
        unresolved=(),
        active_relations=(),
        measured_lower=lower,
        measured_upper=upper,
        heuristic_point_delta=0.0,
    )


def assessment(term_id, lower, upper, *, heuristic=0.0, unresolved=()):
    return FutureTermUtilityAssessment(
        term_id=term_id,
        offering_ids=(),
        timetable_facts=None,
        timetable_utility=complete_timetable(),
        course_preferences=(),
        course_contributions=(),
        unresolved=tuple(unresolved),
        measured_lower=lower,
        measured_upper=upper,
        heuristic_point_delta=heuristic,
        academic_utility_applicable=True,
    )


def aggregation(*term_ids, source_id="user:temporal-policy", weights=None):
    if weights is None:
        weights = (1.0,) * len(term_ids)
    return TemporalUtilityAggregation(
        source_id=source_id,
        weights=tuple(
            TemporalUtilityWeight(term_id, weight)
            for term_id, weight in zip(term_ids, weights)
        ),
    )


class FutureUtilityComparisonTests(unittest.TestCase):
    def test_disjoint_complete_bounds_prove_strict_order(self):
        left = FutureUtilityHistory((assessment("2027S", 5.0, 7.0),))
        right = FutureUtilityHistory((assessment("2027S", 1.0, 4.0),))
        policy = aggregation("2027S")

        comparison = compare_future_utility_histories(
            left, policy, right, policy
        )
        self.assertEqual(
            comparison.status,
            FutureUtilityComparisonStatus.LEFT_STRICTLY_BETTER,
        )
        self.assertTrue(comparison.safe_for_pruning)

    def test_overlapping_complete_bounds_do_not_prove_order(self):
        left = FutureUtilityHistory((assessment("2027S", 3.0, 6.0),))
        right = FutureUtilityHistory((assessment("2027S", 5.0, 8.0),))
        policy = aggregation("2027S")

        comparison = compare_future_utility_histories(
            left, policy, right, policy
        )
        self.assertEqual(
            comparison.status,
            FutureUtilityComparisonStatus.BOUNDS_OVERLAP,
        )
        self.assertFalse(comparison.safe_for_pruning)

    def test_unresolved_or_heuristic_utility_never_prunes(self):
        missing = UnresolvedUtilityDimension(
            dimension_id="unknown",
            quantity=1.0,
            reason="test unknown",
        )
        left = FutureUtilityHistory(
            (assessment("2027S", 100.0, 100.0, unresolved=(missing,)),)
        )
        right = FutureUtilityHistory((assessment("2027S", 0.0, 0.0),))
        policy = aggregation("2027S")

        comparison = compare_future_utility_histories(
            left, policy, right, policy
        )
        self.assertEqual(
            comparison.status,
            FutureUtilityComparisonStatus.UNRESOLVED_UTILITY,
        )
        self.assertFalse(comparison.safe_for_pruning)

        heuristic = FutureUtilityHistory(
            (assessment("2027S", 100.0, 100.0, heuristic=5.0),)
        )
        comparison = compare_future_utility_histories(
            heuristic, policy, right, policy
        )
        self.assertEqual(
            comparison.status,
            FutureUtilityComparisonStatus.UNRESOLVED_UTILITY,
        )

    def test_different_completion_horizons_are_incomparable(self):
        early = FutureUtilityHistory((assessment("2027S", 5.0, 5.0),))
        late = FutureUtilityHistory(
            (
                assessment("2027S", 5.0, 5.0),
                assessment("2027F", 100.0, 100.0),
            )
        )

        comparison = compare_future_utility_histories(
            early,
            aggregation("2027S"),
            late,
            aggregation("2027S", "2027F"),
        )
        self.assertEqual(
            comparison.status,
            FutureUtilityComparisonStatus.INCOMPATIBLE_HORIZON,
        )
        self.assertFalse(comparison.safe_for_pruning)

    def test_different_temporal_weights_are_incomparable(self):
        left = FutureUtilityHistory(
            (
                assessment("2027S", 1.0, 1.0),
                assessment("2027F", 2.0, 2.0),
            )
        )
        right = left

        comparison = compare_future_utility_histories(
            left,
            aggregation("2027S", "2027F", weights=(1.0, 1.0)),
            right,
            aggregation("2027S", "2027F", weights=(1.0, 0.5)),
        )
        self.assertEqual(
            comparison.status,
            FutureUtilityComparisonStatus.INCOMPATIBLE_AGGREGATION,
        )

    def test_same_exact_value_is_an_exact_tie(self):
        left = FutureUtilityHistory((assessment("2027S", 3.0, 3.0),))
        right = FutureUtilityHistory((assessment("2027S", 3.0, 3.0),))
        policy = aggregation("2027S")

        comparison = compare_future_utility_histories(
            left, policy, right, policy
        )
        self.assertEqual(
            comparison.status,
            FutureUtilityComparisonStatus.EXACT_TIE,
        )
        self.assertFalse(comparison.safe_for_pruning)


if __name__ == "__main__":
    unittest.main()
