import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.degree import (  # noqa: E402
    RecognitionEffect,
    apply_recognition,
    qrm_double_major_shell_2026,
    qrm_single_major_2026,
    spring_2026_initial_state,
)
from timetable_optimizer.degree_remainder import (  # noqa: E402
    AnyOfRemainder,
    CategoryCountRemainder,
    ChapelRemainder,
    CreditBucketRemainder,
    SpecificCourseRemainder,
    degree_remainder,
)
from timetable_optimizer.second_majors import (  # noqa: E402
    qrm_double_major_candidate_2026,
)


class DegreeRemainderTests(unittest.TestCase):
    def test_initial_single_major_remainder_preserves_real_requirement_shapes(self):
        scenario = qrm_single_major_2026()
        state = spring_2026_initial_state(scenario)
        remainder = degree_remainder(state, scenario)

        self.assertEqual(remainder.graduation_credit_deficit, 106.5)
        self.assertNotIn("cc_fwis", remainder.requirement_ids)
        self.assertNotIn("cc_eastern_civ", remainder.requirement_ids)
        self.assertNotIn("qrm_intro_statistics", remainder.requirement_ids)

        lhp = remainder.requirement("cc_lhp")
        self.assertIsInstance(lhp, CategoryCountRemainder)
        self.assertEqual(lhp.remaining_count, 1)
        self.assertEqual(lhp.remaining_categories, ("literature", "history"))

        chapel = remainder.requirement("cc_chapel")
        self.assertIsInstance(chapel, ChapelRemainder)
        self.assertEqual(chapel.remaining_passes, 3)
        self.assertEqual(chapel.offline_passes_required, 0)

        language = remainder.requirement("cc_language")
        self.assertIsInstance(language, CreditBucketRemainder)
        self.assertEqual(language.remaining_credits, 3.0)

        mathstat = remainder.requirement("qrm_mr_mathstat_or_regression")
        self.assertIsInstance(mathstat, AnyOfRemainder)
        self.assertEqual(set(mathstat.course_codes), {"QRM3004", "QRM3005"})

        qrm_me = remainder.requirement("qrm_me")
        self.assertIsInstance(qrm_me, CreditBucketRemainder)
        self.assertEqual(qrm_me.remaining_credits, 24.0)

    def test_applying_specific_course_removes_only_that_obligation_and_reduces_credit_deficit(self):
        scenario = qrm_single_major_2026()
        state = spring_2026_initial_state(scenario)
        state = apply_recognition(
            state,
            scenario,
            RecognitionEffect.course(
                completion_id="2026F-QRM1001",
                course_code="QRM1001",
                credits=3.0,
                satisfy=("qrm_mr_intro",),
            ),
        )
        remainder = degree_remainder(state, scenario)

        self.assertNotIn("qrm_mr_intro", remainder.requirement_ids)
        self.assertEqual(remainder.graduation_credit_deficit, 103.5)
        self.assertIn("qrm_mr_micro", remainder.requirement_ids)

    def test_partial_bucket_credit_reduces_bucket_without_creating_filler_courses(self):
        scenario = qrm_single_major_2026()
        state = spring_2026_initial_state(scenario)
        state = apply_recognition(
            state,
            scenario,
            RecognitionEffect.course(
                completion_id="2026F-QRM2004",
                course_code="QRM2004",
                credits=3.0,
                bucket_credit_claims=(("qrm_me", 3.0),),
            ),
        )
        remainder = degree_remainder(state, scenario)
        qrm_me = remainder.requirement("qrm_me")

        self.assertIsInstance(qrm_me, CreditBucketRemainder)
        self.assertEqual(qrm_me.remaining_credits, 21.0)
        self.assertFalse(any(req.requirement_id == "FREE" for req in remainder.requirements))

    def test_unresolved_second_major_stays_structurally_unknown_not_generic_bucket(self):
        scenario = qrm_double_major_shell_2026()
        state = spring_2026_initial_state(scenario)
        remainder = degree_remainder(state, scenario)

        self.assertIn("second_major_structure::unspecified", remainder.structural_unknowns)
        self.assertFalse(remainder.structurally_resolved)
        self.assertFalse(any("dm" == req.requirement_id.lower() for req in remainder.requirements))

    def test_resolved_physics_second_major_is_concrete_in_remainder(self):
        scenario = qrm_double_major_candidate_2026("physics")
        state = spring_2026_initial_state(scenario)
        remainder = degree_remainder(state, scenario)

        self.assertTrue(remainder.structurally_resolved)
        quantum = remainder.requirement("second_physics_quantum_1")
        self.assertIsInstance(quantum, SpecificCourseRemainder)
        self.assertEqual(quantum.course_codes, ("PHY3101",))

        electives = remainder.requirement("second_physics_electives")
        self.assertIsInstance(electives, CreditBucketRemainder)
        self.assertEqual(electives.remaining_credits, 9.0)

    def test_named_requirement_deficits_are_not_claimed_to_sum_to_graduation_deficit(self):
        scenario = qrm_single_major_2026()
        state = spring_2026_initial_state(scenario)
        remainder = degree_remainder(state, scenario)

        # The API intentionally exposes no additive "free credits" remainder because
        # named obligations also reduce the same graduation-credit deficit when taken.
        self.assertFalse(hasattr(remainder, "free_credits"))
        self.assertFalse(hasattr(remainder, "anonymous_fillers"))


if __name__ == "__main__":
    unittest.main()
