import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.catalog import ingest_catalog  # noqa: E402
from timetable_optimizer.degree import Completion, DegreeState, qrm_single_major_2026  # noqa: E402
from timetable_optimizer.fall_actions import (  # noqa: E402
    FallActionError,
    FallRecognitionEvidence,
    generate_fall_academic_actions,
    generate_fall_degree_transitions,
)


def row(section_id, course_code, *, time, department="Economics", language="한국어"):
    return {
        "subjtnbCorsePrcts": section_id,
        "subjtnb": course_code,
        "subjtEngNm": course_code,
        "subjtNm": course_code,
        "campsDivNm": "국제",
        "cdt": 3,
        "cgprfNm": "Professor",
        "srclnLctreLangDivCd": "10",
        "srclnLctreLangDivNm": language,
        "atntnMattrDesc": "",
        "gradeEvlMthdDivNm": "절대평가",
        "rmvlcYn": "0",
        "rmvlcYnNm": " ",
        "lctreTimeNm": time,
        "lecrmNm": "강의실A",
        "subjtClNm": "",
        "estblDeprtNm": department,
        "hy": "1",
        "subsrtDivNm": "",
    }


def snapshot(*rows):
    return ingest_catalog(rows, source_name="fall-test", term="2026F")


class FallAcademicActionTests(unittest.TestCase):
    def test_repeat_policy_unknown_does_not_invent_new_credit(self):
        catalog = snapshot(row("NEW-01", "ECO1103", time="화3"))
        section = catalog.sections[0]
        state = DegreeState(
            completions=(Completion("OLD-01", "ECO1103", 3.0),)
        )
        generated = generate_fall_academic_actions(
            section, catalog, qrm_single_major_2026(), state
        )
        self.assertFalse(generated.actions)
        self.assertEqual(generated.issues[0].code, "repeat_credit_unresolved")

    def test_explicit_no_additional_repeat_credit_is_identity_degree_action(self):
        catalog = snapshot(row("NEW-01", "ECO1103", time="화3"))
        section = catalog.sections[0]
        state = DegreeState(
            completions=(Completion("OLD-01", "ECO1103", 3.0),)
        )
        generated = generate_fall_academic_actions(
            section,
            catalog,
            qrm_single_major_2026(),
            state,
            evidence=FallRecognitionEvidence(
                source_id="registrar:repeat-policy",
                repeat_credit_allowed=False,
            ),
        )
        self.assertEqual(len(generated.actions), 1)
        self.assertIsNone(generated.actions[0].effect)
        self.assertEqual(generated.actions[0].resulting_state, state)

    def test_section_must_match_usable_canonical_snapshot(self):
        left = snapshot(row("A-01", "ECO1103", time="화3"))
        right = snapshot(row("A-01", "ECO1103", time="수3"))
        with self.assertRaises(FallActionError):
            generate_fall_academic_actions(
                right.sections[0], left, qrm_single_major_2026(), DegreeState()
            )


class FallDegreeTransitionBranchTests(unittest.TestCase):
    def test_korean_qrm_allowance_allocation_is_not_fixed_by_section_order(self):
        catalog = snapshot(
            row("A-01", "ECO1103", time="화3"),
            row("B-01", "ECO1104", time="수3"),
        )
        scenario = qrm_single_major_2026()
        # Three of the four allowed Korean QRM-major course slots are already consumed.
        start = DegreeState(
            qrm_korean_major_claims=(
                ("OLD-1", 3.0),
                ("OLD-2", 3.0),
                ("OLD-3", 3.0),
            )
        )
        generated = generate_fall_degree_transitions(
            catalog.sections,
            catalog,
            scenario,
            start,
        )

        self.assertTrue(generated.exact_enumeration_complete)
        self.assertTrue(generated.has_exact_branches)
        claimed_candidate_ids = {
            frozenset(
                completion_id
                for completion_id, _ in branch.transition.resulting_state.qrm_korean_major_claims
                if completion_id in {"A-01", "B-01"}
            )
            for branch in generated.branches
        }
        self.assertIn(frozenset({"A-01"}), claimed_candidate_ids)
        self.assertIn(frozenset({"B-01"}), claimed_candidate_ids)
        # Reserving the final slot from both current courses is also an explicit allocation.
        self.assertIn(frozenset(), claimed_candidate_ids)

    def test_unresolved_repeat_branch_makes_transition_enumeration_incomplete(self):
        catalog = snapshot(row("NEW-01", "ECO1103", time="화3"))
        start = DegreeState(
            completions=(Completion("OLD-01", "ECO1103", 3.0),)
        )
        generated = generate_fall_degree_transitions(
            catalog.sections,
            catalog,
            qrm_single_major_2026(),
            start,
        )
        self.assertFalse(generated.exact_enumeration_complete)
        self.assertFalse(generated.branches)
        self.assertIn(
            "repeat_credit_unresolved",
            {issue.code for issue in generated.unresolved_issues},
        )

    def test_manual_evidence_outside_candidate_is_rejected(self):
        catalog = snapshot(row("A-01", "ECO1103", time="화3"))
        with self.assertRaises(FallActionError):
            generate_fall_degree_transitions(
                catalog.sections,
                catalog,
                qrm_single_major_2026(),
                DegreeState(),
                evidence={
                    "NOT-IN-CANDIDATE": FallRecognitionEvidence(
                        source_id="manual:test",
                        korean_taught=True,
                    )
                },
            )


if __name__ == "__main__":
    unittest.main()
