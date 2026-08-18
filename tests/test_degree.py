import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.degree import (  # noqa: E402
    AnyOfRequirement,
    CategoryCountRequirement,
    ChapelRequirement,
    CreditBucketRequirement,
    DegreeRuleError,
    MajorMode,
    RecognitionEffect,
    SecondMajorStatus,
    SpecificCourseRequirement,
    apply_recognition,
    qrm_double_major_shell_2026,
    qrm_single_major_2026,
    spring_2026_initial_state,
)


class DegreeScenarioStructureTests(unittest.TestCase):
    def test_graduation_credit_rule_is_minimum_126(self):
        scenario = qrm_single_major_2026()
        self.assertEqual(scenario.graduation_min_credits, 126.0)

    def test_common_curriculum_preserves_lhp_and_chapel_structure(self):
        scenario = qrm_single_major_2026()
        lhp = scenario.requirement("cc_lhp")
        chapel = scenario.requirement("cc_chapel")

        self.assertIsInstance(lhp, CategoryCountRequirement)
        self.assertEqual(lhp.required_count, 2)
        self.assertEqual(set(lhp.categories), {"literature", "history", "philosophy"})
        self.assertEqual(lhp.credits_per_category, 3.0)

        self.assertIsInstance(chapel, ChapelRequirement)
        self.assertEqual(chapel.passes_required, 4)
        self.assertEqual(chapel.credits_per_pass, 0.5)
        # The ordinary graduation sources establish four passes but do not establish
        # the separate offline-pass threshold. Keep that threshold unresolved here.
        self.assertIsNone(chapel.offline_passes_required)

    def test_mr5_is_an_any_of_requirement_not_a_flattened_course(self):
        scenario = qrm_single_major_2026()
        mr5 = scenario.requirement("qrm_mr_mathstat_or_regression")
        self.assertIsInstance(mr5, AnyOfRequirement)
        self.assertEqual(set(mr5.course_codes), {"QRM3005", "QRM3004"})

    def test_qrm_me_target_depends_on_major_mode(self):
        single = qrm_single_major_2026()
        double = qrm_double_major_shell_2026()

        self.assertEqual(single.major_mode, MajorMode.SINGLE)
        self.assertEqual(single.qrm_major_credit_target, 42.0)
        self.assertEqual(single.requirement("qrm_me").target_credits, 24.0)

        self.assertEqual(double.major_mode, MajorMode.DOUBLE)
        self.assertEqual(double.qrm_major_credit_target, 36.0)
        self.assertEqual(double.requirement("qrm_me").target_credits, 18.0)

    def test_double_major_shell_does_not_invent_generic_dm_courses(self):
        scenario = qrm_double_major_shell_2026()
        self.assertEqual(scenario.second_major.status, SecondMajorStatus.UNRESOLVED)
        self.assertIsNone(scenario.second_major.name)
        self.assertEqual(scenario.second_major.requirements, ())
        self.assertFalse(any(req.requirement_id.startswith("DM") for req in scenario.requirements))

    def test_free_is_not_a_primitive_requirement(self):
        scenario = qrm_double_major_shell_2026()
        ids = {req.requirement_id for req in scenario.requirements}
        self.assertNotIn("FREE", ids)
        self.assertNotIn("free", ids)

    def test_sta1001_is_required_but_outside_qrm_major_credit(self):
        scenario = qrm_single_major_2026()
        stats = scenario.requirement("qrm_intro_statistics")
        self.assertIsInstance(stats, SpecificCourseRequirement)
        self.assertEqual(stats.course_codes, ("STA1001",))
        self.assertFalse(stats.counts_toward_qrm_major)

    def test_korean_major_credit_cap_and_cross_major_assignment_are_explicit(self):
        scenario = qrm_single_major_2026()
        self.assertEqual(scenario.qrm_korean_credit_cap.max_courses, 4)
        self.assertEqual(scenario.qrm_korean_credit_cap.max_credits, 12.0)
        self.assertTrue(scenario.exclusive_major_assignment)


class Spring2026InitialStateTests(unittest.TestCase):
    def setUp(self):
        self.scenario = qrm_double_major_shell_2026()
        self.state = spring_2026_initial_state(self.scenario)

    def test_initial_state_has_19_5_unique_credits(self):
        self.assertEqual(self.state.earned_credits, 19.5)
        self.assertEqual(self.state.graduation_credit_deficit(self.scenario), 106.5)
        self.assertEqual(len(self.state.completions), 8)

    def test_initial_state_records_the_seven_known_course_codes(self):
        self.assertEqual(
            set(self.state.completed_course_codes),
            {
                "UIC1101",
                "YCA1101",
                "UIC1581",
                "UIC2101",
                "UIC1901",
                "STA1001",
                "UCR1007",
            },
        )

    def test_initial_state_requirement_progress_is_structural(self):
        self.assertTrue(self.state.is_requirement_satisfied(self.scenario, "cc_fwis"))
        self.assertTrue(self.state.is_requirement_satisfied(self.scenario, "cc_christianity"))
        self.assertTrue(self.state.is_requirement_satisfied(self.scenario, "cc_eastern_civ"))
        self.assertTrue(self.state.is_requirement_satisfied(self.scenario, "cc_critical_reasoning"))
        self.assertTrue(self.state.is_requirement_satisfied(self.scenario, "cc_rc101"))
        self.assertTrue(self.state.is_requirement_satisfied(self.scenario, "qrm_intro_statistics"))

        self.assertFalse(self.state.is_requirement_satisfied(self.scenario, "cc_western_civ"))
        self.assertFalse(self.state.is_requirement_satisfied(self.scenario, "cc_language"))
        self.assertFalse(self.state.is_requirement_satisfied(self.scenario, "cc_scird"))
        self.assertFalse(self.state.is_requirement_satisfied(self.scenario, "cc_uic_seminar"))

        # World Philosophy supplies one of the two required L-H-P categories.
        self.assertEqual(self.state.categories_for("cc_lhp"), frozenset({"philosophy"}))
        self.assertFalse(self.state.is_requirement_satisfied(self.scenario, "cc_lhp"))

    def test_chapel_pass_is_known_but_offline_status_remains_bounded(self):
        self.assertEqual(self.state.chapel.passes_completed, 1)
        self.assertEqual(self.state.chapel.offline_passes_min, 0)
        self.assertEqual(self.state.chapel.offline_passes_max, 1)
        self.assertFalse(self.state.is_requirement_satisfied(self.scenario, "cc_chapel"))


class DegreeTransitionInvariantTests(unittest.TestCase):
    def setUp(self):
        self.scenario = qrm_single_major_2026()
        self.state = spring_2026_initial_state(self.scenario)

    def test_duplicate_completion_id_cannot_earn_credit_twice(self):
        effect = RecognitionEffect.course(
            completion_id="future-qrm1001",
            course_code="QRM1001",
            credits=3.0,
            satisfy=("qrm_mr_intro",),
        )
        once = apply_recognition(self.state, self.scenario, effect)
        self.assertEqual(once.earned_credits, 22.5)
        with self.assertRaises(DegreeRuleError):
            apply_recognition(once, self.scenario, effect)

    def test_multiple_requirement_claims_do_not_multiply_unique_credits(self):
        effect = RecognitionEffect.course(
            completion_id="future-example",
            course_code="EXAMPLE1000",
            credits=3.0,
            satisfy=("cc_western_civ",),
            bucket_credit_claims=(("cc_language", 3.0),),
        )
        after = apply_recognition(self.state, self.scenario, effect)
        self.assertEqual(after.earned_credits - self.state.earned_credits, 3.0)

    def test_lhp_requires_two_distinct_categories(self):
        history = RecognitionEffect.course(
            completion_id="future-lhp-history",
            course_code="LHP-HISTORY",
            credits=3.0,
            category_claims=(("cc_lhp", "history"),),
        )
        after = apply_recognition(self.state, self.scenario, history)
        self.assertEqual(after.categories_for("cc_lhp"), frozenset({"philosophy", "history"}))
        self.assertTrue(after.is_requirement_satisfied(self.scenario, "cc_lhp"))

    def test_unknown_second_major_prevents_claiming_whole_degree_complete(self):
        scenario = qrm_double_major_shell_2026()
        state = spring_2026_initial_state(scenario)
        self.assertIsNone(state.is_degree_complete(scenario))


if __name__ == "__main__":
    unittest.main()
