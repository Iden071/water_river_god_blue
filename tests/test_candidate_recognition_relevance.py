import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.candidate_assessment import (  # noqa: E402
    CandidateDegreeTransition,
    assess_candidate,
)
from timetable_optimizer.course_preferences import parse_professor_ratings_csv  # noqa: E402
from timetable_optimizer.degree import (  # noqa: E402
    DegreeScenario,
    DegreeState,
    KoreanMajorCreditCap,
    MajorMode,
    SecondMajorSpec,
    SecondMajorStatus,
    SpecificCourseRequirement,
    apply_recognition,
)
from timetable_optimizer.fall2026_preferences import fall2026_preference_profile  # noqa: E402
from timetable_optimizer.recognition import recognize_section  # noqa: E402
from timetable_optimizer.registration import assess_freshman_registration  # noqa: E402
from timetable_optimizer.sections import section_from_raw  # noqa: E402


def row():
    return {
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


def scenario():
    return DegreeScenario(
        scenario_id="candidate-relevance-test",
        graduation_min_credits=3.0,
        major_mode=MajorMode.SINGLE,
        qrm_major_credit_target=0.0,
        requirements=(
            SpecificCourseRequirement(
                requirement_id="req_a",
                title="A",
                course_codes=("A",),
                credits=3.0,
            ),
        ),
        qrm_korean_credit_cap=KoreanMajorCreditCap(4, 12.0),
        exclusive_major_assignment=True,
        second_major=SecondMajorSpec(SecondMajorStatus.NONE),
    )


class CandidateRecognitionRelevanceTests(unittest.TestCase):
    def test_out_of_scenario_unresolved_decision_does_not_reopen_exact_transition(self):
        degree_scenario = scenario()
        start = DegreeState()
        section = section_from_raw(row())
        recognition = recognize_section(section, degree_scenario, start)

        scird = [
            decision
            for decision in recognition.decisions
            if decision.requirement_id == "cc_scird"
        ]
        self.assertEqual(len(scird), 1)
        self.assertEqual(scird[0].status.value, "unresolved")

        option = recognition.options[0]
        end = apply_recognition(start, degree_scenario, option.effect)
        transition = CandidateDegreeTransition(
            scenario_id=degree_scenario.scenario_id,
            starting_state=start,
            resulting_state=end,
            selected_option_ids=(option.option_id,),
        )
        registration = assess_freshman_registration(
            section.section_id,
            {
                section.section_id: {
                    "sy1PercpCnt": 0,
                    "sy2PercpCnt": 0,
                    "sy3PercpCnt": 0,
                    "sy4PercpCnt": 0,
                    "sy5PercpCnt": 0,
                    "sy6PercpCnt": 0,
                }
            },
        )
        assessment = assess_candidate(
            (section,),
            fall2026_preference_profile(),
            parse_professor_ratings_csv("name,rating\n"),
            registration_assessments={section.section_id: registration},
            recognition_assessments={section.section_id: recognition},
            degree_scenario=degree_scenario,
            degree_transition=transition,
        )

        self.assertNotIn(
            "recognition::A-01::cc_scird",
            assessment.future_unknowns,
        )
        self.assertFalse(assessment.future_unknowns)


if __name__ == "__main__":
    unittest.main()
