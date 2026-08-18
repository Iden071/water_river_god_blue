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
        self.assertNotIn("dead_gap_shape", quantities)

    def test_longer_runs_and_non_four_gaps_do_not_use_legacy_curves(self):
        sections = (
            section_from_raw(row("TEST1001-01-00", "화3,4,5,6,7")),
            section_from_raw(row("TEST1002-01-00", "수3,7")),
        )
        facts = extract_timetable_quality(sections)
        quantities = timetable_preference_quantities(facts)

        self.assertEqual(quantities["long_fixed_run_shape"], 1.0)
        self.assertEqual(quantities["dead_gap_shape"], 1.0)
        self.assertNotIn("four_fixed_period_run", quantities)
        self.assertNotIn("four_period_hole", quantities)


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
        self.assertEqual(assessment.measured_lower, -1.0)
        self.assertEqual(assessment.measured_upper, 5.0)

        # Weekend attachment and Friday-event dimensions remain active but
        # incomplete, so the interval above is not a whole-timetable bound.
        self.assertIsNone(assessment.complete_bounds)
        self.assertTrue(assessment.has_unresolved)
        self.assertIn(
            "weekend_run_curvature",
            assessment.unresolved_dimensions,
        )
        self.assertIn(
            "friday_event_window_free",
            assessment.unresolved_dimensions,
        )

    def test_heuristic_gap_is_not_added_to_measured_interval(self):
        sections = (
            section_from_raw(row("TEST1001-01-00", "화3,8")),
        )
        assessment = evaluate_timetable_utility(
            extract_timetable_quality(sections),
            fall2026_preference_profile(),
        )

        # Periods 3 and 8 leave a four-period dead gap (4,5,6,7).
        self.assertEqual(assessment.heuristic_point_delta, -10.0)
        heuristic = [
            c for c in assessment.contributions if c.dimension_id == "four_period_hole"
        ]
        self.assertEqual(len(heuristic), 1)
        self.assertEqual(heuristic[0].status.value, "heuristic")
        self.assertIsNone(assessment.complete_bounds)

    def test_active_qualitative_relation_is_reported(self):
        sections = (
            section_from_raw(row("TEST1001-01-00", "화3,4,5,9,10,11")),
        )
        assessment = evaluate_timetable_utility(
            extract_timetable_quality(sections),
            fall2026_preference_profile(),
        )

        self.assertIn("missing_lunch", assessment.unresolved_dimensions)
        self.assertIn("missing_dinner", assessment.unresolved_dimensions)
        labels = {relation.label for relation in assessment.active_relations}
        self.assertIn("Dinner loss is worse than lunch loss", labels)

    def test_22_50_relation_survives_without_fake_numeric_value(self):
        sections = (
            section_from_raw(row("TEST1001-01-00", "화14")),
        )
        assessment = evaluate_timetable_utility(
            extract_timetable_quality(sections),
            fall2026_preference_profile(),
        )

        self.assertIn("late_finish_period_14", assessment.unresolved_dimensions)
        labels = {relation.label for relation in assessment.active_relations}
        self.assertIn("22:50 finish worse than 21:50 anchor", labels)


if __name__ == "__main__":
    unittest.main()
