import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.degree import (  # noqa: E402
    DegreeRuleError,
    DegreeState,
    RecognitionEffect,
    SecondMajorSpec,
    SecondMajorStatus,
    SpecificCourseRequirement,
    apply_recognition,
    qrm_double_major_shell_2026,
)
from timetable_optimizer.recognition import recognize_section  # noqa: E402
from timetable_optimizer.second_majors import (  # noqa: E402
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


def overlapping_qrm_second_major_scenario():
    """Synthetic evidence fixture for the documented exclusive-major rule.

    QRM2004 is a real QRM ME.  The synthetic second-major requirement deliberately uses the
    same course so the assignment engine must branch instead of double-counting it.  This is
    a mechanics test, not a claim that any current named second major recognizes QRM2004.
    """

    base = qrm_double_major_shell_2026()
    overlap = SpecificCourseRequirement(
        "second_test_overlap",
        "Synthetic overlapping second-major requirement",
        ("QRM2004",),
        3.0,
        source="synthetic exclusive-assignment regression fixture",
    )
    return replace(
        base,
        scenario_id="qrm-double-synthetic-overlap-2026",
        requirements=base.requirements + (overlap,),
        second_major=SecondMajorSpec(
            status=SecondMajorStatus.RESOLVED,
            name="Synthetic Test Major",
            requirements=(overlap,),
        ),
    )


class PhysicsRecognitionTests(unittest.TestCase):
    def setUp(self):
        self.scenario = qrm_double_major_candidate_2026("physics")
        self.state = DegreeState()

    def test_physics_required_course_is_recognized_by_canonical_authority(self):
        assessment = recognize_section(section("PHY3101"), self.scenario, self.state)
        self.assertEqual(len(assessment.options), 1)
        effect = assessment.options[0].effect
        self.assertIn("second_physics_quantum_1", effect.satisfy)

    def test_physics_elective_receives_physics_bucket_credit(self):
        assessment = recognize_section(section("PHY2103"), self.scenario, self.state)
        self.assertEqual(len(assessment.options), 1)
        effect = assessment.options[0].effect
        self.assertIn(("second_physics_electives", 3.0), effect.bucket_credit_claims)

    def test_physics_required_course_is_not_also_physics_elective(self):
        assessment = recognize_section(section("PHY3101"), self.scenario, self.state)
        effect = assessment.options[0].effect
        self.assertNotIn(("second_physics_electives", 3.0), effect.bucket_credit_claims)


class ExclusiveMajorAssignmentTests(unittest.TestCase):
    def setUp(self):
        self.scenario = overlapping_qrm_second_major_scenario()
        self.state = DegreeState()
        self.course = section("QRM2004")

    def test_recognition_branches_instead_of_counting_course_to_both_majors(self):
        assessment = recognize_section(self.course, self.scenario, self.state)
        self.assertEqual(len(assessment.options), 2)

        claim_sets = {
            (
                frozenset(option.effect.satisfy),
                frozenset(req_id for req_id, _ in option.effect.bucket_credit_claims),
            )
            for option in assessment.options
        }
        self.assertIn((frozenset(), frozenset({"qrm_me"})), claim_sets)
        self.assertIn((frozenset({"second_test_overlap"}), frozenset()), claim_sets)

        for option in assessment.options:
            major_claims = set(option.effect.satisfy) | {
                req_id for req_id, _ in option.effect.bucket_credit_claims
            }
            self.assertFalse(
                {"qrm_me", "second_test_overlap"}.issubset(major_claims),
                "no recognition option may assign one completion to both majors",
            )

    def test_each_assignment_option_earns_unique_graduation_credit_once(self):
        assessment = recognize_section(self.course, self.scenario, self.state)
        for option in assessment.options:
            state = apply_recognition(DegreeState(), self.scenario, option.effect)
            self.assertEqual(state.earned_credits, 3.0)

    def test_degree_state_rejects_handcrafted_cross_major_double_assignment(self):
        illegal = RecognitionEffect.course(
            completion_id=self.course.section_id,
            course_code=self.course.course_code,
            credits=3.0,
            satisfy=("second_test_overlap",),
            bucket_credit_claims=(("qrm_me", 3.0),),
        )
        with self.assertRaises(DegreeRuleError):
            apply_recognition(self.state, self.scenario, illegal)

    def test_same_physical_completion_cannot_be_applied_under_both_branches(self):
        assessment = recognize_section(self.course, self.scenario, self.state)
        first = apply_recognition(self.state, self.scenario, assessment.options[0].effect)
        with self.assertRaises(DegreeRuleError):
            apply_recognition(first, self.scenario, assessment.options[1].effect)


if __name__ == "__main__":
    unittest.main()
