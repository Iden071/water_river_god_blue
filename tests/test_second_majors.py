import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.degree import (  # noqa: E402
    CreditBucketRequirement,
    DegreeRuleError,
    DegreeState,
    MajorMode,
    SecondMajorStatus,
    SpecificCourseRequirement,
)
from timetable_optimizer.second_majors import (  # noqa: E402
    PHYSICS_ELECTIVE_2026_CODES,
    SECOND_MAJOR_CANDIDATES_2026,
    qrm_double_major_candidate_2026,
)


class SecondMajorCandidateRegistryTests(unittest.TestCase):
    def test_candidate_set_is_finite_and_identity_specific(self):
        self.assertEqual(
            {candidate.candidate_id for candidate in SECOND_MAJOR_CANDIDATES_2026},
            {
                "mathematics",
                "industrial-engineering",
                "electrical-electronic-engineering",
                "computer-science",
                "applied-statistics",
                "physics",
            },
        )
        self.assertTrue(all(candidate.spec.name for candidate in SECOND_MAJOR_CANDIDATES_2026))
        self.assertEqual(
            len({candidate.spec.name for candidate in SECOND_MAJOR_CANDIDATES_2026}),
            len(SECOND_MAJOR_CANDIDATES_2026),
        )

    def test_no_candidate_reintroduces_anonymous_dm_requirements(self):
        for candidate in SECOND_MAJOR_CANDIDATES_2026:
            for requirement in candidate.spec.requirements:
                self.assertFalse(requirement.requirement_id.upper().startswith("DM"))

    def test_unknown_candidate_is_rejected(self):
        with self.assertRaises(DegreeRuleError):
            qrm_double_major_candidate_2026("generic-dm")


class CandidateScenarioSemanticsTests(unittest.TestCase):
    def test_each_candidate_keeps_qrm_double_major_rules(self):
        for candidate in SECOND_MAJOR_CANDIDATES_2026:
            scenario = qrm_double_major_candidate_2026(candidate.candidate_id)
            self.assertEqual(scenario.major_mode, MajorMode.DOUBLE)
            self.assertEqual(scenario.qrm_major_credit_target, 36.0)
            self.assertEqual(scenario.requirement("qrm_me").target_credits, 18.0)
            self.assertEqual(scenario.second_major.name, candidate.spec.name)
            self.assertEqual(
                scenario.scenario_id,
                f"qrm-double-{candidate.candidate_id}-2026",
            )

    def test_unresolved_named_candidate_stays_unresolved_for_degree_completion(self):
        scenario = qrm_double_major_candidate_2026("mathematics")
        self.assertEqual(scenario.second_major.status, SecondMajorStatus.UNRESOLVED)
        self.assertEqual(scenario.second_major.name, "Mathematics")
        # The unresolved second-major structure blocks any whole-degree completion claim.
        self.assertIsNone(DegreeState().is_degree_complete(scenario))

    def test_second_major_requirements_are_visible_to_current_evaluation_engine(self):
        scenario = qrm_double_major_candidate_2026("physics")
        owned = scenario.second_major.requirements
        self.assertTrue(owned)
        for requirement in owned:
            self.assertIn(requirement, scenario.requirements)
            self.assertIs(scenario.requirement(requirement.requirement_id), requirement)


class PhysicsSecondMajorTests(unittest.TestCase):
    def setUp(self):
        self.scenario = qrm_double_major_candidate_2026("physics")

    def test_physics_degree_structure_is_27_required_plus_9_elective(self):
        self.assertEqual(self.scenario.second_major.status, SecondMajorStatus.RESOLVED)
        requirements = self.scenario.second_major.requirements
        required = [req for req in requirements if isinstance(req, SpecificCourseRequirement)]
        electives = [req for req in requirements if isinstance(req, CreditBucketRequirement)]

        self.assertEqual(len(required), 9)
        self.assertEqual(sum(req.credits for req in required), 27.0)
        self.assertEqual(len(electives), 1)
        self.assertEqual(electives[0].target_credits, 9.0)
        self.assertEqual(electives[0].qualification_rule_id, "physics_major_elective_2026")

    def test_physics_required_course_codes_match_department_curriculum(self):
        required_codes = {
            req.course_codes[0]
            for req in self.scenario.second_major.requirements
            if isinstance(req, SpecificCourseRequirement)
        }
        self.assertEqual(
            required_codes,
            {
                "PHY2105",
                "PHY3101",
                "PHY3102",
                "PHY3103",
                "PHY3104",
                "PHY3106",
                "PHY3107",
                "PHY3110",
                "PHY3111",
            },
        )

    def test_current_physics_elective_codes_exclude_required_courses(self):
        required_codes = {
            req.course_codes[0]
            for req in self.scenario.second_major.requirements
            if isinstance(req, SpecificCourseRequirement)
        }
        self.assertTrue(PHYSICS_ELECTIVE_2026_CODES)
        self.assertTrue(required_codes.isdisjoint(PHYSICS_ELECTIVE_2026_CODES))

    def test_recommended_prerequisites_are_not_promoted_to_degree_requirements(self):
        requirement_codes = {
            code
            for req in self.scenario.second_major.requirements
            if isinstance(req, SpecificCourseRequirement)
            for code in req.course_codes
        }
        # Mathematics/intro-physics courses appear as recommendations on the curriculum
        # page but are not part of the published 27-credit Physics required-major block.
        self.assertNotIn("MAT1001", requirement_codes)
        self.assertNotIn("PHY1001", requirement_codes)


if __name__ == "__main__":
    unittest.main()
