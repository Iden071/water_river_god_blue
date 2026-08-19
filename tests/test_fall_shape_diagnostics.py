import unittest

from timetable_optimizer.fall_shape_diagnostics import (
    FallShapeDiagnosticError,
    archived_shape_sensitivity_scenarios,
    assess_archival_shape_sensitivity,
)


class ArchivedShapeScenarioTests(unittest.TestCase):
    def setUp(self):
        self.low, self.mid, self.high = archived_shape_sensitivity_scenarios()

    def test_archival_endpoints_preserve_old_coupling(self):
        self.assertEqual(
            (self.low.rest_value, self.low.first_attached_trip_value),
            (8.0, 12.0),
        )
        self.assertEqual(
            (self.mid.rest_value, self.mid.first_attached_trip_value),
            (7.0, 13.0),
        )
        self.assertEqual(
            (self.high.rest_value, self.high.first_attached_trip_value),
            (6.0, 14.0),
        )
        for scenario in (self.low, self.mid, self.high):
            self.assertAlmostEqual(
                scenario.rest_value + scenario.first_attached_trip_value,
                20.0,
            )
            self.assertAlmostEqual(
                scenario.friday_event_value,
                scenario.first_attached_trip_value / 3.0,
            )
            self.assertIn("Diagnostic only", scenario.note)
            self.assertTrue(scenario.source_id.startswith("provisional:"))

    def test_weekend_extra_is_old_total_trip_minus_known_first_day(self):
        expected = 13.0 * (2.0**1.4 - 1.0)
        self.assertAlmostEqual(self.mid.weekend_extra_total(2), expected)
        with self.assertRaises(FallShapeDiagnosticError):
            self.mid.weekend_extra_total(1)
        with self.assertRaises(FallShapeDiagnosticError):
            self.mid.weekend_extra_total(6)

    def test_legacy_long_run_correction_is_flat_zero_beyond_four_period_anchor(self):
        points = self.mid.unresolved_shape_points()
        for length in range(5, 16):
            self.assertEqual(points[f"long_fixed_run_delta_{length}"], 0.0)
        self.assertEqual(points["friday_event_window_free"], 13.0 / 3.0)


class ShapeSensitivityAssessmentTests(unittest.TestCase):
    def test_irrelevant_known_dimensions_are_ignored(self):
        result = assess_archival_shape_sensitivity(
            {
                "start_period_1_day": 2.0,
                "dead_gap_quadratic_unit": 9.0,
            }
        )
        self.assertEqual(result.spread, 0.0)
        self.assertEqual(
            set(result.scenario_points),
            {
                "archival-low-trip-curve",
                "archival-midpoint",
                "archival-high-trip-curve",
            },
        )
        self.assertEqual(set(result.scenario_points.values()), {0.0})

    def test_friday_and_weekend_state_show_archival_sensitivity(self):
        result = assess_archival_shape_sensitivity(
            {
                "friday_event_window_free": 1.0,
                "weekend_attached_presence_free_extra_total_3": 1.0,
            }
        )
        points = result.scenario_points
        self.assertLess(
            points["archival-low-trip-curve"],
            points["archival-midpoint"],
        )
        self.assertLess(
            points["archival-midpoint"],
            points["archival-high-trip-curve"],
        )
        self.assertGreater(result.spread, 0.0)
        self.assertFalse(result.unresolved_shape_dimensions_not_covered)

    def test_flat_archival_marathon_has_zero_sensitivity_by_itself(self):
        result = assess_archival_shape_sensitivity(
            {"long_fixed_run_delta_9": 1.0}
        )
        self.assertEqual(result.spread, 0.0)
        self.assertEqual(set(result.scenario_points.values()), {0.0})

    def test_unknown_future_shape_dimension_remains_visible_not_silently_zero(self):
        result = assess_archival_shape_sensitivity(
            {"long_fixed_run_delta_16": 1.0}
        )
        self.assertEqual(
            result.unresolved_shape_dimensions_not_covered,
            ("long_fixed_run_delta_16",),
        )


if __name__ == "__main__":
    unittest.main()
