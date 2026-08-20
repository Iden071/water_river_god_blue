import unittest

from timetable_optimizer.fall2026_preferences import fall2026_preference_profile
from timetable_optimizer.fall_unresolved_shape import unresolved_shape_signature
from timetable_optimizer.sections import section_from_raw
from timetable_optimizer.timetable_quality import extract_timetable_quality
from timetable_optimizer.timetable_utility import timetable_preference_quantities


def row(section_id, time):
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
        "lecrmNm": "강의실A",
        "subjtClNm": "대면",
    }


class FallUnresolvedShapeSignatureTests(unittest.TestCase):
    def test_signature_keeps_three_and_long_run_states_without_scoring_them(self):
        sections = (
            section_from_raw(row("THREE-01-00", "화1,2,3")),
            section_from_raw(row("FIVE-01-00", "수4,5,6,7,8")),
            section_from_raw(row("SIX-01-00", "목4,5,6,7,8,9")),
        )
        facts = extract_timetable_quality(sections)
        signature = unresolved_shape_signature(facts)

        self.assertEqual(signature.three_fixed_period_run_count, 1)
        self.assertEqual(signature.long_fixed_run_counts, ((5, 1), (6, 1)))
        self.assertEqual(
            signature.active_dimension_quantities["three_fixed_period_run"], 1.0
        )
        self.assertEqual(
            signature.active_dimension_quantities["long_fixed_run_delta_5"], 1.0
        )
        self.assertEqual(
            signature.active_dimension_quantities["long_fixed_run_delta_6"], 1.0
        )

    def test_one_and_two_period_runs_are_absent_from_unresolved_shape(self):
        sections = (
            section_from_raw(row("ONE-01-00", "화3")),
            section_from_raw(row("TWO-01-00", "수3,4")),
        )
        signature = unresolved_shape_signature(extract_timetable_quality(sections))

        self.assertEqual(signature.three_fixed_period_run_count, 0)
        self.assertEqual(signature.long_fixed_run_counts, ())
        self.assertFalse(
            any("run" in key for key in signature.active_dimension_quantities)
        )

    def test_signature_exactly_matches_active_unmeasured_geometry_dimensions(self):
        sections = (
            section_from_raw(row("THREE-01-00", "화3,4,5")),
            section_from_raw(row("FIVE-01-00", "수4,5,6,7,8")),
            # Friday period 7 blocks the event window while leaving the rest of Friday open.
            section_from_raw(row("FRI-01-00", "금7")),
        )
        facts = extract_timetable_quality(sections)
        profile = fall2026_preference_profile()
        quantities = timetable_preference_quantities(facts)
        signature = unresolved_shape_signature(facts)

        active_unmeasured = {
            dimension: quantity
            for dimension, quantity in quantities.items()
            if dimension in profile.unmeasured_dimensions
            and (
                dimension == "three_fixed_period_run"
                or dimension == "friday_event_window_free"
                or dimension.startswith("long_fixed_run_delta_")
                or dimension.startswith(
                    "weekend_attached_presence_free_extra_total_"
                )
            )
        }
        self.assertEqual(dict(signature.active_dimension_quantities), active_unmeasured)
        self.assertFalse(signature.friday_event_window_free)

    def test_weekend_attached_state_is_one_exact_mutually_exclusive_count(self):
        # Tuesday is the only campus-presence day.  Monday is attached through the preceding
        # weekend and Wed/Thu/Fri are attached through the following weekend, for four attached
        # weekdays total.  Stage 4 represents that as one exact extra-total state, not three
        # linear marginal units.
        facts = extract_timetable_quality(
            (section_from_raw(row("TUE-01-00", "화6")),)
        )
        signature = unresolved_shape_signature(facts)

        self.assertEqual(signature.weekend_attached_presence_free_days, 4)
        weekend_keys = [
            key
            for key in signature.active_dimension_quantities
            if key.startswith("weekend_attached_presence_free_extra_total_")
        ]
        self.assertEqual(
            weekend_keys,
            ["weekend_attached_presence_free_extra_total_4"],
        )


if __name__ == "__main__":
    unittest.main()
