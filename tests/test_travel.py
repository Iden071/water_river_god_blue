import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.sections import section_from_raw  # noqa: E402
from timetable_optimizer.travel import (  # noqa: E402
    TravelPathError,
    extract_travel_path_facts,
)


def row(section_id, time, campus="국제", room="강의실A"):
    return {
        "subjtnbCorsePrcts": section_id,
        "subjtnb": section_id.split("-")[0],
        "subjtEngNm": "TEST COURSE",
        "subjtNm": "테스트",
        "campsDivNm": campus,
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


class TravelPathFactTests(unittest.TestCase):
    def test_cross_campus_transition_is_structural_not_scored(self):
        sections = (
            section_from_raw(row("TEST1001-01-00", "화3,4", "국제")),
            section_from_raw(row("TEST1002-01-00", "화7,8", "신촌")),
        )
        facts = extract_travel_path_facts(sections)
        transitions = facts.cross_campus_transitions

        self.assertEqual(len(transitions), 1)
        transition = transitions[0]
        self.assertEqual(transition.from_campus, "국제")
        self.assertEqual(transition.to_campus, "신촌")
        self.assertEqual(transition.depart_after_period, 4)
        self.assertEqual(transition.arrive_by_period, 7)
        self.assertEqual(transition.free_periods_between, 2)
        self.assertEqual(transition.fixed_periods_between, ())
        self.assertTrue(facts.requires_travel_model)

    def test_live_online_commitment_inside_transfer_gap_is_preserved(self):
        sections = (
            section_from_raw(row("TEST1001-01-00", "화3,4", "국제")),
            section_from_raw(row("TEST1002-01-00", "화7,8", "신촌")),
            section_from_raw(
                row("TEST1003-01-00", "화5", "국제", room="실시간온라인")
            ),
        )
        transition = extract_travel_path_facts(sections).cross_campus_transitions[0]

        self.assertEqual(transition.free_periods_between, 2)
        self.assertEqual(transition.fixed_periods_between, (5,))
        self.assertTrue(transition.has_intervening_fixed_commitment)

    def test_video_free_does_not_create_location_or_fixed_transfer_commitment(self):
        sections = (
            section_from_raw(row("TEST1001-01-00", "화3,4", "국제")),
            section_from_raw(row("TEST1002-01-00", "화7,8", "신촌")),
            section_from_raw(
                row("TEST1003-01-00", "화5", "국제", room="동영상콘텐츠")
            ),
        )
        transition = extract_travel_path_facts(sections).cross_campus_transitions[0]
        self.assertEqual(transition.fixed_periods_between, ())

    def test_same_campus_gap_does_not_invent_a_travel_transition(self):
        sections = (
            section_from_raw(row("TEST1001-01-00", "화3,4", "국제")),
            section_from_raw(row("TEST1002-01-00", "화7,8", "국제")),
        )
        facts = extract_travel_path_facts(sections)

        self.assertEqual(facts.cross_campus_transitions, ())
        self.assertFalse(facts.requires_travel_model)

    def test_simultaneous_physical_presence_on_two_campuses_is_exposed(self):
        sections = (
            section_from_raw(row("TEST1001-01-00", "화3", "국제")),
            section_from_raw(row("TEST1002-01-00", "화3", "신촌")),
        )
        facts = extract_travel_path_facts(sections)

        self.assertEqual(len(facts.location_conflicts), 1)
        conflict = facts.location_conflicts[0]
        self.assertEqual(conflict.day, 1)
        self.assertEqual(conflict.period, 3)
        self.assertEqual(conflict.campuses, ("국제", "신촌"))

    def test_nonparsed_schedule_is_not_treated_as_no_travel(self):
        section = section_from_raw(row("TEST1001-01-00", "", "국제", room=""))
        with self.assertRaises(TravelPathError):
            extract_travel_path_facts((section,))


if __name__ == "__main__":
    unittest.main()
