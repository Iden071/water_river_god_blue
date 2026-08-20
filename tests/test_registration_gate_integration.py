import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.candidate_assessment import assess_candidate  # noqa: E402
from timetable_optimizer.course_preferences import ProfessorRatingBook  # noqa: E402
from timetable_optimizer.fall2026_preferences import fall2026_preference_profile  # noqa: E402
from timetable_optimizer.registration import assess_freshman_registration  # noqa: E402
from timetable_optimizer.sections import section_from_raw  # noqa: E402


def section():
    return section_from_raw(
        {
            "subjtnbCorsePrcts": "A-01",
            "subjtnb": "A",
            "subjtEngNm": "A",
            "subjtNm": "A",
            "campsDivNm": "국제",
            "cdt": 3,
            "cgprfNm": "Professor",
            "srclnLctreLangDivCd": "10",
            "atntnMattrDesc": "",
            "gradeEvlMthdDivNm": "절대평가",
            "rmvlcYn": "0",
            "rmvlcYnNm": " ",
            "lctreTimeNm": "화3",
            "lecrmNm": "강의실A",
            "subjtClNm": "대면",
        }
    )


class RegistrationGateIntegrationTests(unittest.TestCase):
    def test_missing_quota_row_is_hard_unknown_not_resolved_permission(self):
        candidate_section = section()
        registration = assess_freshman_registration(candidate_section.section_id, {})
        assessment = assess_candidate(
            (candidate_section,),
            fall2026_preference_profile(),
            ProfessorRatingBook(()),
            registration_assessments={candidate_section.section_id: registration},
        )

        self.assertFalse(assessment.known_infeasible)
        self.assertIn(
            "registration_year_gate_unresolved",
            {issue.code for issue in assessment.hard_constraint_unknowns},
        )
        self.assertIn(
            "registration_obtainability::A-01",
            assessment.present_preference_unknowns,
        )


if __name__ == "__main__":
    unittest.main()
