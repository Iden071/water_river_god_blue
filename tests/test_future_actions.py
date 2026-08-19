import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.catalog import ListingStatus  # noqa: E402
from timetable_optimizer.degree import (  # noqa: E402
    RecognitionEffect,
    SecondMajorSpec,
    SecondMajorStatus,
    SpecificCourseRequirement,
    apply_recognition,
    qrm_double_major_shell_2026,
    qrm_single_major_2026,
    spring_2026_initial_state,
)
from timetable_optimizer.future_actions import (  # noqa: E402
    FutureActionError,
    FutureRecognitionEvidence,
    generate_future_academic_actions,
)
from timetable_optimizer.future_opportunities import (  # noqa: E402
    FutureOffering,
    FutureOfferingEvidence,
    FutureOfferingEvidenceKind,
)
from timetable_optimizer.sections import NoListedSchedule  # noqa: E402


def offering(
    offering_id="2027S:qrm1001",
    *,
    course_code="QRM1001",
    credits=3.0,
    term_id="2027S",
    campus="국제",
):
    return FutureOffering(
        offering_id=offering_id,
        term_id=term_id,
        course_code=course_code,
        credits=credits,
        campus=campus,
        schedule=NoListedSchedule("", ""),
        evidence=FutureOfferingEvidence(
            kind=FutureOfferingEvidenceKind.EXPLICIT_ASSUMPTION,
            source_id=f"scenario:{offering_id}",
        ),
    )


class FutureRecognitionActionTests(unittest.TestCase):
    def test_required_course_action_applies_to_current_degree_state(self):
        scenario = qrm_single_major_2026()
        state = spring_2026_initial_state(scenario)
        generated = generate_future_academic_actions(
            offering(), scenario, state
        )

        self.assertEqual(len(generated.actions), 1)
        action = generated.actions[0]
        self.assertIn("qrm_mr_intro", action.effect.satisfy)
        self.assertTrue(
            action.resulting_state.is_requirement_satisfied(
                scenario, "qrm_mr_intro"
            )
        )
        self.assertEqual(
            action.resulting_state.earned_credits,
            state.earned_credits + 3.0,
        )

    def test_future_completion_identity_is_scenario_offering_not_historical_identity(self):
        scenario = qrm_single_major_2026()
        state = spring_2026_initial_state(scenario)
        future = FutureOffering(
            offering_id="2027S:analog:qrm1001",
            term_id="2027S",
            course_code="QRM1001",
            credits=3.0,
            campus="국제",
            schedule=NoListedSchedule("", ""),
            evidence=FutureOfferingEvidence(
                kind=FutureOfferingEvidenceKind.HISTORICAL_ANALOG,
                source_id="history:2026F:QRM1001-01-00",
                source_term="2026F",
                source_section_id="QRM1001-01-00",
            ),
        )
        generated = generate_future_academic_actions(future, scenario, state)

        completion = generated.actions[0].effect.completion
        self.assertEqual(completion.completion_id, "2027S:analog:qrm1001")
        self.assertNotEqual(completion.completion_id, "QRM1001-01-00")

    def test_missing_future_credits_produce_no_invented_transition(self):
        scenario = qrm_single_major_2026()
        state = spring_2026_initial_state(scenario)
        generated = generate_future_academic_actions(
            offering(credits=None), scenario, state
        )

        self.assertFalse(generated.actions)
        self.assertTrue(
            any(issue.code == "missing_credits" for issue in generated.issues)
        )
        self.assertTrue(
            any(
                issue.code == "no_applicable_recognition_action"
                for issue in generated.issues
            )
        )

    def test_overlap_branches_qrm_vs_second_major_instead_of_double_counting(self):
        base = qrm_double_major_shell_2026()
        second_req = SpecificCourseRequirement(
            requirement_id="second_test_overlap",
            title="Test overlap",
            course_codes=("QRM2001",),
            credits=3.0,
            source="test scenario",
        )
        second = SecondMajorSpec(
            status=SecondMajorStatus.RESOLVED,
            name="Test Major",
            requirements=(second_req,),
        )
        scenario = replace(
            base,
            scenario_id="qrm-double-test-overlap",
            requirements=base.requirements + (second_req,),
            second_major=second,
        )
        state = spring_2026_initial_state(scenario)

        generated = generate_future_academic_actions(
            offering(
                offering_id="2027S:overlap",
                course_code="QRM2001",
            ),
            scenario,
            state,
        )

        self.assertEqual(len(generated.actions), 2)
        option_ids = {action.option_id for action in generated.actions}
        self.assertTrue(any("assign-qrm" in option_id for option_id in option_ids))
        self.assertTrue(
            any("assign-second-major" in option_id for option_id in option_ids)
        )
        for action in generated.actions:
            self.assertEqual(
                action.resulting_state.earned_credits,
                state.earned_credits + 3.0,
            )

    def test_korean_qrm_cap_is_explicit_allocation_choice_then_stateful_gate(self):
        scenario = qrm_single_major_2026()
        initial = spring_2026_initial_state(scenario)
        korean_econ = offering(
            offering_id="2027S:eco2102",
            course_code="ECO2102",
        )
        evidence = FutureRecognitionEvidence(
            source_id="scenario:korean-econ",
            departments=("School of Economics",),
            korean_taught=True,
        )

        fresh = generate_future_academic_actions(
            korean_econ, scenario, initial, evidence=evidence
        )
        self.assertEqual(len(fresh.actions), 2)
        counted = [
            action
            for action in fresh.actions
            if action.effect.qrm_korean_major_credits == 3.0
        ]
        reserved = [
            action
            for action in fresh.actions
            if action.effect.qrm_korean_major_credits == 0.0
        ]
        self.assertEqual(len(counted), 1)
        self.assertEqual(len(reserved), 1)
        self.assertIn("qrm_mr_micro", counted[0].effect.satisfy)
        self.assertNotIn("qrm_mr_micro", reserved[0].effect.satisfy)
        self.assertIn("decline-qrm-korean", reserved[0].option_id)

        capped = initial
        for index in range(4):
            capped = apply_recognition(
                capped,
                scenario,
                RecognitionEffect.course(
                    completion_id=f"prior-korean-{index}",
                    course_code=f"TEST{index}",
                    credits=3.0,
                    bucket_credit_claims=(("qrm_me", 3.0),),
                    qrm_korean_major_credits=3.0,
                    label="test prior Korean QRM credit",
                ),
            )
        self.assertEqual(capped.qrm_korean_major_credits, 12.0)

        after_cap = generate_future_academic_actions(
            korean_econ, scenario, capped, evidence=evidence
        )
        self.assertEqual(len(after_cap.actions), 1)
        self.assertNotIn("qrm_mr_micro", after_cap.actions[0].effect.satisfy)
        self.assertEqual(after_cap.actions[0].effect.qrm_korean_major_credits, 0.0)
        micro = [
            decision
            for decision in after_cap.recognition.decisions
            if decision.requirement_id == "qrm_mr_micro"
        ]
        self.assertEqual(len(micro), 1)
        self.assertEqual(micro[0].status.value, "not_qualified")

    def test_future_qrm_listing_evidence_flows_through_canonical_authority(self):
        scenario = qrm_single_major_2026()
        state = spring_2026_initial_state(scenario)
        generated = generate_future_academic_actions(
            offering(
                offering_id="2027S:scenario-me",
                course_code="ZZZ1000",
            ),
            scenario,
            state,
            evidence=FutureRecognitionEvidence(
                source_id="scenario:qrm-program-listing",
                qrm_listing_status=ListingStatus.OK,
                qrm_listed_category="ME",
            ),
        )

        self.assertEqual(len(generated.actions), 1)
        self.assertIn(
            ("qrm_me", 3.0),
            generated.actions[0].effect.bucket_credit_claims,
        )

    def test_scenario_recognition_evidence_requires_provenance(self):
        with self.assertRaises(FutureActionError):
            FutureRecognitionEvidence(korean_taught=True)

        with self.assertRaises(FutureActionError):
            FutureRecognitionEvidence(
                source_id="scenario",
                qrm_listed_category="ME",
            )

    def test_same_future_offering_cannot_be_applied_twice(self):
        scenario = qrm_single_major_2026()
        state = spring_2026_initial_state(scenario)
        generated = generate_future_academic_actions(offering(), scenario, state)
        next_state = generated.actions[0].resulting_state

        with self.assertRaises(FutureActionError):
            generate_future_academic_actions(offering(), scenario, next_state)


if __name__ == "__main__":
    unittest.main()
