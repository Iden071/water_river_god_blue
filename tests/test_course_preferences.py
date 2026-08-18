import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.course_preferences import (  # noqa: E402
    CoursePreferenceError,
    ProfessorRatingStatus,
    assess_section_course_preferences,
    parse_professor_ratings_csv,
)
from timetable_optimizer.preferences import (  # noqa: E402
    PreferenceEstimate,
    PreferenceProvenance,
    PreferenceSourceKind,
    PreferenceValue,
)
from timetable_optimizer.sections import section_from_raw  # noqa: E402


def row(section_id="TEST1001-01-00", professor="Professor"):
    return {
        "subjtnbCorsePrcts": section_id,
        "subjtnb": section_id.split("-")[0],
        "subjtEngNm": "TEST COURSE",
        "subjtNm": "테스트",
        "campsDivNm": "국제",
        "cdt": 3,
        "cgprfNm": professor,
        "srclnLctreLangDivCd": "10",
        "atntnMattrDesc": "",
        "gradeEvlMthdDivNm": "절대평가",
        "rmvlcYn": "0",
        "rmvlcYnNm": " ",
        "lctreTimeNm": "화3,4,5",
        "lecrmNm": "강의실A",
        "subjtClNm": "대면",
    }


class ProfessorRatingSheetTests(unittest.TestCase):
    def test_explicit_zero_is_rated_but_blank_is_unrated(self):
        book = parse_professor_ratings_csv(
            "name,rating,note\nNeutral,0,explicit neutral\nUnknown,,not rated yet\n"
        )

        neutral = book.lookup("Neutral")
        unknown = book.lookup("Unknown")

        self.assertEqual(neutral.status, ProfessorRatingStatus.RATED)
        self.assertEqual(neutral.rating, 0.0)
        self.assertEqual(unknown.status, ProfessorRatingStatus.LISTED_UNRATED)
        self.assertIsNone(unknown.rating)
        self.assertIn("Neutral", book.rated_names)
        self.assertIn("Unknown", book.listed_unrated_names)

    def test_absent_and_missing_professor_are_distinct_states(self):
        book = parse_professor_ratings_csv("name,rating\nKnown,1\n")

        self.assertEqual(
            book.lookup("Other").status,
            ProfessorRatingStatus.NOT_LISTED,
        )
        self.assertEqual(
            book.lookup("").status,
            ProfessorRatingStatus.NO_PROFESSOR_LISTED,
        )

    def test_out_of_range_rating_is_rejected_not_clamped(self):
        with self.assertRaises(CoursePreferenceError):
            parse_professor_ratings_csv("name,rating\nTooGood,1.2\n")

    def test_duplicate_professor_is_rejected(self):
        with self.assertRaises(CoursePreferenceError):
            parse_professor_ratings_csv(
                "name,rating\nDuplicate,0.5\nDuplicate,0.7\n"
            )

    def test_shortlist_metadata_is_not_treated_as_rating(self):
        book = parse_professor_ratings_csv(
            "name,rating,in_top50,share_top5000,courses\n"
            "Candidate,,50,0.972,TEST1001\n"
        )
        lookup = book.lookup("Candidate")
        self.assertEqual(lookup.status, ProfessorRatingStatus.LISTED_UNRATED)
        self.assertIsNone(lookup.rating)


class SectionCoursePreferenceEvidenceTests(unittest.TestCase):
    def test_unknown_course_dimensions_remain_explicitly_unmeasured(self):
        book = parse_professor_ratings_csv("name,rating\nProfessor,0.85\n")
        evidence = assess_section_course_preferences(
            section_from_raw(row()),
            book,
        )

        self.assertEqual(evidence.professor.status, ProfessorRatingStatus.RATED)
        self.assertEqual(evidence.professor.rating, 0.85)
        self.assertNotIn("professor_rating", evidence.unresolved_dimensions)
        self.assertIn("professor_rating_to_utility", evidence.unresolved_dimensions)
        self.assertIn("subject_interest", evidence.unresolved_dimensions)
        self.assertIn("workload", evidence.unresolved_dimensions)
        self.assertIn("difficulty", evidence.unresolved_dimensions)

    def test_unrated_professor_does_not_receive_zero(self):
        book = parse_professor_ratings_csv("name,rating\nProfessor,\n")
        evidence = assess_section_course_preferences(
            section_from_raw(row()),
            book,
        )

        self.assertIsNone(evidence.professor.rating)
        self.assertIn("professor_rating", evidence.unresolved_dimensions)

    def test_manual_subject_input_is_preserved_without_title_inference(self):
        book = parse_professor_ratings_csv("name,rating\nProfessor,0\n")
        subject = PreferenceValue(
            "subject_interest::TEST1001",
            PreferenceEstimate.exact(4.0),
            PreferenceProvenance(
                PreferenceSourceKind.USER_INPUT,
                "manual-subject-TEST1001",
                "User manually supplied course-interest utility.",
            ),
            "Subject interest for TEST1001",
        )
        evidence = assess_section_course_preferences(
            section_from_raw(row()),
            book,
            subject_interest={"TEST1001": subject},
        )

        self.assertEqual(evidence.subject_interest.estimate.require_exact(), 4.0)
        self.assertNotIn("subject_interest", evidence.unresolved_dimensions)
        self.assertIn("workload", evidence.unresolved_dimensions)
        self.assertIn("difficulty", evidence.unresolved_dimensions)


if __name__ == "__main__":
    unittest.main()
