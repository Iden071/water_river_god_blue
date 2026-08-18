import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.sections import section_from_raw  # noqa: E402
from timetable_optimizer.timetable_quality import (  # noqa: E402
    TimetableQualityError,
    extract_timetable_quality,
)


def row(section_id, course_code, *, time, room, campus="국제"):
    return {
        "subjtnbCorsePrcts": section_id,
        "subjtnb": course_code,
        "subjtEngNm": course_code,
        "subjtNm": course_code,
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
        "subjtClNm": "",
    }


class TimetableQualityFactTests(unittest.TestCase):
    def test_fixed_time_and_presence_are_kept_distinct(self):
        sections = (
            section_from_raw(row("A-01", "A", time="화3,4", room="강의실A")),
            section_from_raw(row("B-01", "B", time="수5,6", room="실시간온라인")),
        )
        facts = extract_timetable_quality(sections)

        self.assertNotIn(1, facts.presence_free_weekdays)
        self.assertNotIn(1, facts.fixed_free_weekdays)
        self.assertIn(2, facts.presence_free_weekdays)
        self.assertNotIn(2, facts.fixed_free_weekdays)

    def test_video_free_does_not_destroy_fixed_free_day(self):
        sections = (
            section_from_raw(
                row("V-01", "V", time="수7", room="동영상콘텐츠")
            ),
        )
        facts = extract_timetable_quality(sections)
        self.assertIn(2, facts.presence_free_weekdays)
        self.assertIn(2, facts.fixed_free_weekdays)

    def test_day_geometry_extracts_holes_runs_meals_and_late_finish(self):
        sections = (
            section_from_raw(
                row("A-01", "A", time="화1,2,3,4/화7,8,9,10,11", room="강의실A/강의실B")
            ),
        )
        facts = extract_timetable_quality(sections)
        tuesday = facts.days[1]

        self.assertEqual(tuesday.first_fixed_period, 1)
        self.assertEqual(tuesday.last_fixed_period, 11)
        self.assertEqual(tuesday.holes, (2,))
        self.assertEqual(tuesday.fixed_runs, (4, 5))
        self.assertTrue(tuesday.lunch_fully_blocked)
        self.assertTrue(tuesday.dinner_fully_blocked)

    def test_friday_event_window_uses_fixed_not_presence_time(self):
        live_online = section_from_raw(
            row("L-01", "L", time="금7", room="실시간온라인")
        )
        video_free = section_from_raw(
            row("V-01", "V", time="금8", room="동영상콘텐츠")
        )

        self.assertFalse(extract_timetable_quality((live_online,)).friday_event_window_free)
        self.assertTrue(extract_timetable_quality((video_free,)).friday_event_window_free)

    def test_weekend_connected_presence_run_counts_both_sides(self):
        sections = (
            section_from_raw(row("T-01", "T", time="화3", room="강의실A")),
            section_from_raw(row("W-01", "W", time="수3", room="강의실A")),
            section_from_raw(row("R-01", "R", time="목3", room="강의실A")),
        )
        facts = extract_timetable_quality(sections)
        # Friday + weekend + Monday = 4-day cyclic no-presence run.
        self.assertEqual(facts.weekend_connected_presence_free_run, 4)

    def test_nonparsed_schedule_is_not_silently_free(self):
        unresolved = section_from_raw(
            row("U-01", "U", time="미정", room="강의실A")
        )
        with self.assertRaises(TimetableQualityError):
            extract_timetable_quality((unresolved,))

        no_time = section_from_raw(
            row("N-01", "N", time="", room="")
        )
        with self.assertRaises(TimetableQualityError):
            extract_timetable_quality((no_time,))


if __name__ == "__main__":
    unittest.main()
