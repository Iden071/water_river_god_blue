import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.fall2026_preferences import (  # noqa: E402
    fall2026_preference_profile,
)
from timetable_optimizer.sections import section_from_raw  # noqa: E402
from timetable_optimizer.timetable_quality import extract_timetable_quality  # noqa: E402
from timetable_optimizer.timetable_utility import (  # noqa: E402
    evaluate_timetable_utility,
    timetable_preference_quantities,
)


def row(section_id, time, room="강의실A"):
    return {
        "subjtnbCorsePrcts": section_id,
        "subjtnb": section_id.split("-")[0],
        "subjtEngNm": "TEST COURSE",
        "subjtNm": "테스트",
        "campsDivNm": "국제",
        "cdt": 3,
        "cgprfNm": "Professor",
        "srclnLctreLangDivCd": "10",
        "atntnMattrDesc": "",
        "gradeEvlMthdDivNm": "절대평가",
        "rmvlcYn": "0",
        "rmvlcYnNm": " ",
        "lctreTimeNm": time,
        "lecrmNm": room,
        "subjtClNm": "대면",
    }


class TimetablePreferenceQuantityTests(unittest.TestCase):
    def test_exact_observations_are_mapped_without_utility(self):
        sections = (
            section_from_raw(row("TEST1001-01-00", "화1,2,3,4")),
            section_from_raw(row("TEST1002-01-00", "목9")),
        )
        facts = extract_timetable_quality(sections)
        quantities = timetable_preference_quantities(facts)

        self.assertEqual(quantities["start_period_1_day"], 1.0)
        self.assertEqual(quantities["four_fixed_period_run"], 1.0)
        self.assertEqual(quantities["late_finish_period_9"], 1.0)
        self.assertEqual(quantities["rest_fixed_free_weekday"], 3.0)
        self.assertEqual(quantities["weekend_attached_presence_free_day"], 1.0)
        # Monday and Friday are both connected to the weekend around the weekly cycle.
        # The extra value beyond the known first attached weekday is represented as one
        # exact-state correction, not as one linear marginal unit.
        self.assertEqual(
            quantities["weekend_attached_presence_free_extra_total_2"], 1.0
        )
        self.assertNotIn("dead_gap_quadratic_unit", quantities)

    def test_non_four_gap_and_long_run_preserve_known_anchor_plus_state_delta(self):
        sections = (
            section_from_raw(row("TEST1001-01-00", "화3,4,5,6,7")),
            section_from_raw(row("TEST1002-01-00", "수3,7")),
        )
        facts = extract_timetable_quality(sections)
        quantities = timetable_preference_quantities(facts)

        # A five-period run contains the confirmed four-period anchor plus one unresolved
        # state-specific correction.  No assumption says the correction is linear or even
        # monotone with run length.
        self.assertEqual(quantities["four_fixed_period_run"], 1.0)
        self.assertEqual(quantities["long_fixed_run_delta_5"], 1.0)
        # 수3,7 leaves periods 4,5,6 as a three-period dead gap: l^2 = 9.
        self.assertEqual(quantities["dead_gap_quadratic_unit"], 9.0)

    def test_different_long_run_lengths_are_not_collapsed_to_one_shape_scalar(self):
        five = timetable_preference_quantities(
            extract_timetable_quality(
                (section_from_raw(row("FIVE-01-00", "화3,4,5,6,7")),)
            )
        )
        six = timetable_preference_quantities(
            extract_timetable_quality(
                (section_from_raw(row("SIX-01-00", "화3,4,5,6,7,8")),)
            )
        )
        self.assertIn("long_fixed_run_delta_5", five)
        self.assertNotIn("long_fixed_run_delta_6", five)
        self.assertIn("long_fixed_run_delta_6", six)
        self.assertNotIn("long_fixed_run_delta_5", six)


class PartialTimetableUtilityTests(unittest.TestCase):
    def test_measured_interval_stays_separate_from_unresolved_terms(self):
        sections = (
            section_from_raw(row("TEST1001-01-00", "화1,2,3,4")),
            section_from_raw(row("TEST1002-01-00", "목9")),
        )
        assessment = evaluate_timetable_utility(
            extract_timetable_quality(sections),
            fall2026_preference_profile(),
        )

        # Exact measured pieces: 09:00 -10, four-period run -8,
        # 17:50 finish -1. Three fixed-free weekdays contribute [18,24].
        # The first weekend-attached presence-free day contributes [12,14].
        self.assertEqual(assessment.measured_lower, 11.0)
        self.assertEqual(assessment.measured_upper, 19.0)

        # The exact two-attached-weekday state has an unresolved *extra-total* correction,
        # and Friday-event value is also unmeasured. Therefore the interval above is not a
        # whole-timetable bound.
        self.assertIsNone(assessment.complete_bounds)
        self.assertTrue(assessment.has_unresolved)
        self.assertIn(
            "weekend_attached_presence_free_extra_total_2",
            assessment.unresolved_dimensions,
        )
        self.assertIn(
            "friday_event_window_free",
            assessment.unresolved_dimensions,
        )

    def test_long_run_keeps_four_period_anchor_numeric_but_delta_unresolved(self):
        sections = (
            section_from_raw(row("TEST1001-01-00", "화3,4,5,6,7")),
        )
        assessment = evaluate_timetable_utility(
            extract_timetable_quality(sections),
            fall2026_preference_profile(),
        )
        contributions = {c.dimension_id: c for c in assessment.contributions}
        self.assertEqual(contributions["four_fixed_period_run"].point, -8.0)
        self.assertIn("long_fixed_run_delta_5", assessment.unresolved_dimensions)

    def test_four_period_gap_is_exact_from_confirmed_quadratic_curve(self):
        sections = (
            section_from_raw(row("TEST1001-01-00", "화3,8")),
        )
        assessment = evaluate_timetable_utility(
            extract_timetable_quality(sections),
            fall2026_preference_profile(),
        )

        # Periods 3 and 8 leave a four-period gap (4,5,6,7):
        # -0.625 * 4^2 = -10.
        gap = [
            c
            for c in assessment.contributions
            if c.dimension_id == "dead_gap_quadratic_unit"
        ]
        self.assertEqual(len(gap), 1)
        self.assertEqual(gap[0].quantity, 16.0)
        self.assertEqual(gap[0].status.value, "exact")
        self.assertEqual(gap[0].point, -10.0)
        self.assertEqual(gap[0].lower, -10.0)
        self.assertEqual(gap[0].upper, -10.0)
        self.assertEqual(assessment.heuristic_point_delta, 0.0)

    def test_confirmed_meal_values_are_numeric_not_relations(self):
        sections = (
            section_from_raw(row("TEST1001-01-00", "화3,4,5,9,10,11")),
        )
        assessment = evaluate_timetable_utility(
            extract_timetable_quality(sections),
            fall2026_preference_profile(),
        )

        self.assertNotIn("missing_lunch", assessment.unresolved_dimensions)
        self.assertNotIn("missing_dinner", assessment.unresolved_dimensions)
        contributions = {c.dimension_id: c for c in assessment.contributions}
        self.assertEqual(contributions["missing_lunch"].point, -6.0)
        self.assertEqual(contributions["missing_dinner"].point, -8.0)
        self.assertEqual(assessment.active_relations, ())

    def test_22_50_is_numeric_from_confirmed_late_finish_curve(self):
        sections = (
            section_from_raw(row("TEST1001-01-00", "화14")),
        )
        assessment = evaluate_timetable_utility(
            extract_timetable_quality(sections),
            fall2026_preference_profile(),
        )

        self.assertNotIn("late_finish_period_14", assessment.unresolved_dimensions)
        contributions = {c.dimension_id: c for c in assessment.contributions}
        self.assertAlmostEqual(
            contributions["late_finish_period_14"].point,
            -12.980240898764906,
        )
        self.assertEqual(assessment.active_relations, ())


if __name__ == "__main__":
    unittest.main()
