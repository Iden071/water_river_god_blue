import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.fall2026_preferences import (  # noqa: E402
    fall2026_preference_profile,
)
from timetable_optimizer.preferences import (  # noqa: E402
    EstimateStatus,
    PreferenceRelationKind,
    PreferenceSourceKind,
)


class Fall2026PreferenceProfileTests(unittest.TestCase):
    def setUp(self):
        self.profile = fall2026_preference_profile()

    def test_anchor_and_confirmed_points_are_preserved(self):
        self.assertEqual(
            self.profile.value("start_period_1_day").estimate.require_exact(),
            -10.0,
        )
        self.assertEqual(
            self.profile.value("four_fixed_period_run").estimate.require_exact(),
            -8.0,
        )
        self.assertEqual(
            self.profile.value("late_finish_period_9").estimate.require_exact(),
            -1.0,
        )
        self.assertEqual(
            self.profile.value("late_finish_period_13").estimate.require_exact(),
            -10.0,
        )

    def test_old_midpoints_are_not_frozen_when_original_evidence_was_bounded(self):
        rest = self.profile.value("rest_fixed_free_weekday")
        trip = self.profile.value("weekend_attached_presence_free_day")
        self.assertEqual(rest.estimate.status, EstimateStatus.BOUNDED)
        self.assertEqual(rest.estimate.bounds, (6.0, 8.0))
        self.assertEqual(trip.estimate.status, EstimateStatus.BOUNDED)
        self.assertEqual(trip.estimate.bounds, (12.0, 14.0))
        self.assertEqual(trip.provenance.source_kind, PreferenceSourceKind.DERIVED)

    def test_approximate_comparisons_remain_heuristic(self):
        self.assertEqual(
            self.profile.value("four_period_hole").estimate.status,
            EstimateStatus.HEURISTIC,
        )
        self.assertEqual(
            self.profile.value("hard_language_course").estimate.status,
            EstimateStatus.HEURISTIC,
        )

    def test_unresolved_dimensions_do_not_receive_legacy_defaults(self):
        expected = {
            "start_period_2_day",
            "late_finish_period_14",
            "missing_lunch",
            "missing_dinner",
            "friday_event_window_free",
            "weekend_run_curvature",
            "course_workload",
            "course_difficulty_general",
            "chapel_timing_advantage",
            "registration_obtainability",
            "mixed_campus_travel_disutility",
            "target_credit_load_18",
        }
        self.assertTrue(expected <= self.profile.unmeasured_dimensions)

    def test_dinner_vs_lunch_is_preserved_as_relation_not_invented_numbers(self):
        relation = next(
            relation
            for relation in self.profile.relations
            if relation.label == "Dinner loss is worse than lunch loss"
        )
        self.assertEqual(relation.relation, PreferenceRelationKind.LESS_THAN)
        self.assertEqual(relation.rhs, 0.0)

    def test_2250_statement_bounds_unmeasured_magnitude(self):
        relation = next(
            relation
            for relation in self.profile.relations
            if relation.label == "22:50 finish worse than 21:50 anchor"
        )
        self.assertEqual(relation.relation, PreferenceRelationKind.LESS_THAN)
        self.assertEqual(relation.rhs, -10.0)
        self.assertEqual(
            self.profile.value("late_finish_period_14").estimate.status,
            EstimateStatus.UNMEASURED,
        )


if __name__ == "__main__":
    unittest.main()
