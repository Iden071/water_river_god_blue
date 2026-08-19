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
    PreferenceSourceKind,
)


class Fall2026PreferenceProfileTests(unittest.TestCase):
    def setUp(self):
        self.profile = fall2026_preference_profile()

    def test_anchor_and_current_confirmed_points_are_preserved(self):
        expected = {
            "start_period_1_day": -10.0,
            "start_period_2_day": -5.0,
            "four_fixed_period_run": -8.0,
            "late_finish_period_9": -1.0,
            "late_finish_period_13": -10.0,
            "missing_lunch": -6.0,
            "missing_dinner": -8.0,
        }
        for dimension, point in expected.items():
            self.assertEqual(
                self.profile.value(dimension).estimate.require_exact(),
                point,
            )

    def test_derived_late_finish_curve_covers_every_dynamic_period(self):
        expected = {
            10: -2.695731032073513,
            11: -4.815109795572117,
            12: -7.266965797284128,
            14: -12.980240898764906,
            15: -16.183108844566643,
        }
        for period, point in expected.items():
            value = self.profile.value(f"late_finish_period_{period}")
            self.assertAlmostEqual(value.estimate.require_exact(), point)
            self.assertEqual(value.provenance.source_kind, PreferenceSourceKind.DERIVED)

        for period in range(9, 16):
            self.assertEqual(
                self.profile.value(f"late_finish_period_{period}").estimate.status,
                EstimateStatus.EXACT,
            )

    def test_confirmed_quadratic_gap_curve_is_proof_numeric(self):
        gap = self.profile.value("dead_gap_quadratic_unit")
        self.assertEqual(gap.estimate.status, EstimateStatus.EXACT)
        self.assertEqual(gap.estimate.require_exact(), -0.625)
        self.assertEqual(gap.provenance.source_kind, PreferenceSourceKind.DERIVED)

    def test_old_midpoints_are_not_frozen_when_original_evidence_was_bounded(self):
        rest = self.profile.value("rest_fixed_free_weekday")
        trip = self.profile.value("weekend_attached_presence_free_day")
        self.assertEqual(rest.estimate.status, EstimateStatus.BOUNDED)
        self.assertEqual(rest.estimate.bounds, (6.0, 8.0))
        self.assertEqual(trip.estimate.status, EstimateStatus.BOUNDED)
        self.assertEqual(trip.estimate.bounds, (12.0, 14.0))
        self.assertEqual(trip.provenance.source_kind, PreferenceSourceKind.DERIVED)

    def test_hard_language_comparison_remains_heuristic(self):
        self.assertEqual(
            self.profile.value("hard_language_course").estimate.status,
            EstimateStatus.HEURISTIC,
        )

    def test_nonlinear_shape_states_are_explicitly_unmeasured_not_collapsed(self):
        for length in range(5, 16):
            self.assertEqual(
                self.profile.value(f"long_fixed_run_delta_{length}").estimate.status,
                EstimateStatus.UNMEASURED,
            )
        for count in range(2, 6):
            self.assertEqual(
                self.profile.value(
                    f"weekend_attached_presence_free_extra_total_{count}"
                ).estimate.status,
                EstimateStatus.UNMEASURED,
            )
        self.assertNotIn("weekend_run_curvature", self.profile.unmeasured_dimensions)

    def test_separate_non_timetable_placeholders_remain_unmeasured(self):
        expected = {
            "friday_event_window_free",
            "course_workload",
            "course_difficulty_general",
            "chapel_timing_advantage",
            "registration_obtainability",
            "mixed_campus_travel_disutility",
            "target_credit_load_18",
        }
        self.assertTrue(expected <= self.profile.unmeasured_dimensions)
        self.assertNotIn("start_period_2_day", self.profile.unmeasured_dimensions)
        for period in range(9, 16):
            self.assertNotIn(
                f"late_finish_period_{period}", self.profile.unmeasured_dimensions
            )
        self.assertNotIn("missing_lunch", self.profile.unmeasured_dimensions)
        self.assertNotIn("missing_dinner", self.profile.unmeasured_dimensions)

    def test_redundant_qualitative_relations_are_removed_after_numeric_resolution(self):
        self.assertEqual(self.profile.relations, ())


if __name__ == "__main__":
    unittest.main()
