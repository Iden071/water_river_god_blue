import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.degree import (  # noqa: E402
    AnyOfRequirement,
    CreditBucketRequirement,
    DegreeState,
    SecondMajorStatus,
    SpecificCourseRequirement,
)
from timetable_optimizer.recognition import recognize_section  # noqa: E402
from timetable_optimizer.second_majors import (  # noqa: E402
    EEE_ELECTIVE_2026_CODES,
    EEE_EXPERIMENT_2026_CODES,
    qrm_double_major_candidate_2026,
)
from timetable_optimizer.sections import NoListedSchedule, Section  # noqa: E402


def section(course_code: str, *, credits: float = 3.0) -> Section:
    return Section(
        section_id=f"{course_code}-01-00",
        course_code=course_code,
        name=course_code,
        korean_name="",
        campus="신촌",
        credits=credits,
        professor="",
        language_code="",
        note="",
        grading="",
        cancelled=False,
        mode_text="",
        schedule=NoListedSchedule("", ""),
        language_name="영어",
    )


class EEEDoubleMajorEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.scenario = qrm_double_major_candidate_2026(
            "electrical-electronic-engineering"
        )

    def test_eee_is_resolved_as_current_2018_plus_36_credit_structure(self):
        self.assertEqual(self.scenario.second_major.status, SecondMajorStatus.RESOLVED)
        requirements = self.scenario.second_major.requirements

        fixed = [req for req in requirements if isinstance(req, SpecificCourseRequirement)]
        choice = [req for req in requirements if isinstance(req, AnyOfRequirement)]
        buckets = [req for req in requirements if isinstance(req, CreditBucketRequirement)]

        self.assertEqual(sum(req.credits for req in fixed), 27.0)
        self.assertEqual(len(choice), 1)
        self.assertEqual(choice[0].credits, 3.0)
        self.assertEqual(len(buckets), 1)
        self.assertEqual(buckets[0].target_credits, 6.0)
        self.assertEqual(27.0 + 3.0 + 6.0, 36.0)

    def test_eee_fixed_courses_match_published_table(self):
        codes = {
            req.course_codes[0]
            for req in self.scenario.second_major.requirements
            if isinstance(req, SpecificCourseRequirement)
        }
        self.assertEqual(
            codes,
            {
                "EEE2020",
                "EEE2030",
                "EEE2010",
                "EEE2040",
                "EEE2060",
                "EEE2050",
                "EEE2111",
                "EEE3313",
                "EEE4610",
            },
        )

    def test_eee_experiment_choice_matches_published_eight_course_list(self):
        choice = next(
            req
            for req in self.scenario.second_major.requirements
            if isinstance(req, AnyOfRequirement)
        )
        self.assertEqual(set(choice.course_codes), set(EEE_EXPERIMENT_2026_CODES))
        self.assertEqual(len(EEE_EXPERIMENT_2026_CODES), 8)

    def test_eee_elective_catalogue_does_not_include_fixed_or_experiment_courses(self):
        fixed_codes = {
            req.course_codes[0]
            for req in self.scenario.second_major.requirements
            if isinstance(req, SpecificCourseRequirement)
        }
        self.assertTrue(fixed_codes.isdisjoint(EEE_ELECTIVE_2026_CODES))
        self.assertTrue(set(EEE_EXPERIMENT_2026_CODES).isdisjoint(EEE_ELECTIVE_2026_CODES))
        self.assertIn("EEE2001", EEE_ELECTIVE_2026_CODES)
        self.assertIn("EEE4420", EEE_ELECTIVE_2026_CODES)

    def test_eee_fixed_experiment_and_elective_flow_through_canonical_recognition(self):
        state = DegreeState()

        fixed = recognize_section(section("EEE2030"), self.scenario, state)
        self.assertIn("second_eee_electromagnetics_1", fixed.options[0].effect.satisfy)

        experiment = recognize_section(section("EEE4423"), self.scenario, state)
        self.assertIn("second_eee_experiment", experiment.options[0].effect.satisfy)

        elective = recognize_section(section("EEE4420"), self.scenario, state)
        self.assertIn(
            ("second_eee_electives", 3.0),
            elective.options[0].effect.bucket_credit_claims,
        )


class RemainingEvidenceBoundaryTests(unittest.TestCase):
    def test_unresolved_candidates_do_not_become_generic_credit_buckets(self):
        for candidate_id in (
            "mathematics",
            "industrial-engineering",
            "computer-science",
            "applied-statistics",
        ):
            scenario = qrm_double_major_candidate_2026(candidate_id)
            self.assertEqual(scenario.second_major.status, SecondMajorStatus.UNRESOLVED)
            self.assertEqual(scenario.second_major.requirements, ())
            self.assertIsNone(DegreeState().is_degree_complete(scenario))


if __name__ == "__main__":
    unittest.main()
