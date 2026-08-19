import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.degree import (  # noqa: E402
    qrm_single_major_2026,
    spring_2026_initial_state,
)
from timetable_optimizer.future_actions import (  # noqa: E402
    FutureRecognitionEvidence,
    generate_future_academic_actions,
)
from timetable_optimizer.future_opportunities import (  # noqa: E402
    FutureOffering,
    FutureOfferingEvidence,
    FutureOfferingEvidenceKind,
)
from timetable_optimizer.sections import NoListedSchedule  # noqa: E402


def repeated_sta1001():
    return FutureOffering(
        offering_id="2027S:repeat-sta1001",
        term_id="2027S",
        course_code="STA1001",
        credits=3.0,
        campus="신촌",
        schedule=NoListedSchedule("", ""),
        evidence=FutureOfferingEvidence(
            kind=FutureOfferingEvidenceKind.EXPLICIT_ASSUMPTION,
            source_id="scenario:repeat-sta1001",
        ),
    )


class FutureRepeatCreditTests(unittest.TestCase):
    def setUp(self):
        self.scenario = qrm_single_major_2026()
        self.state = spring_2026_initial_state(self.scenario)
        self.assertIn("STA1001", self.state.completed_course_codes)

    def test_repeat_without_credit_evidence_does_not_create_new_graduation_credit(self):
        generated = generate_future_academic_actions(
            repeated_sta1001(), self.scenario, self.state
        )
        self.assertFalse(generated.actions)
        self.assertTrue(
            any(issue.code == "repeat_credit_unresolved" for issue in generated.issues)
        )

    def test_explicit_no_additional_credit_stays_non_progressing(self):
        generated = generate_future_academic_actions(
            repeated_sta1001(),
            self.scenario,
            self.state,
            evidence=FutureRecognitionEvidence(
                source_id="scenario:retake-policy",
                repeat_credit_allowed=False,
            ),
        )
        self.assertFalse(generated.actions)
        self.assertTrue(
            any(
                issue.code == "repeat_course_no_additional_degree_credit"
                for issue in generated.issues
            )
        )

    def test_explicit_repeatable_additional_credit_can_create_transition(self):
        generated = generate_future_academic_actions(
            repeated_sta1001(),
            self.scenario,
            self.state,
            evidence=FutureRecognitionEvidence(
                source_id="scenario:repeatable-course-assumption",
                repeat_credit_allowed=True,
            ),
        )
        self.assertTrue(generated.actions)
        self.assertTrue(
            all(
                action.resulting_state.earned_credits
                == self.state.earned_credits + 3.0
                for action in generated.actions
            )
        )


if __name__ == "__main__":
    unittest.main()
