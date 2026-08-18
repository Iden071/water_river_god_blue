import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.candidate_assessment import (  # noqa: E402
    CandidateAssessmentError,
    CandidateDegreeTransition,
    assess_candidate,
)
from timetable_optimizer.course_preferences import (  # noqa: E402
    parse_professor_ratings_csv,
)
from timetable_optimizer.degree import (  # noqa: E402
    apply_recognition,
    qrm_single_major_2026,
    spring_2026_initial_state,
)
from timetable_optimizer.fall2026_preferences import (  # noqa: E402
    fall2026_preference_profile,
)
from timetable_optimizer.recognition import recognize_section  # noqa: E402
from timetable_optimizer.registration import (  # noqa: E402
    assess_freshman_registration,
)
from timetable_optimizer.sections import section_from_raw  # noqa: E402


def row(
    section_id,
    course_code,
    *,
    time,
    room="강의실A",
    campus="국제",
    credits=3,
    professor="Professor",
    cancelled="0",
):
    return {
        "subjtnbCorsePrcts": section_id,
        "subjtnb": course_code,
        "subjtEngNm": course_code,
        "subjtNm": course_code,
        "campsDivNm": campus,
        "cdt": credits,
        "cgprfNm": professor,
        "srclnLctreLangDivCd": "10",
        "atntnMattrDesc": "",
        "gradeEvlMthdDivNm": "절대평가",
        "rmvlcYn": cancelled,
        "rmvlcYnNm": "폐강" if cancelled == "1" else " ",
        "lctreTimeNm": time,
        "lecrmNm": room,
        "subjtClNm": "",
    }


def no_gate_registration(section_id):
    return assess_freshman_registration(
        section_id,
        {
            section_id: {
                "sy1PercpCnt": 0,
                "sy2PercpCnt": 0,
                "sy3PercpCnt": 0,
                "sy4PercpCnt": 0,
                "sy5PercpCnt": 0,
                "sy6PercpCnt": 0,
            }
        },
    )


class UnifiedCandidateAssessmentTests(unittest.TestCase):
    def setUp(self):
        self.profile = fall2026_preference_profile()
        self.professors = parse_professor_ratings_csv("name,rating\n")

    def test_missing_registration_evidence_is_unknown_not_impossible(self):
        section = section_from_raw(row("A-01", "A", time="화3"))
        assessment = assess_candidate(
            (section,), self.profile, self.professors
        )

        self.assertFalse(assessment.known_infeasible)
        self.assertIsNotNone(assessment.timetable_facts)
        codes = {issue.code for issue in assessment.hard_constraint_unknowns}
        self.assertIn("registration_gate_unassessed", codes)
        self.assertIn(
            "registration_obtainability::A-01",
            assessment.present_preference_unknowns,
        )

    def test_conflicting_sections_are_known_infeasible_even_with_incomplete_utility(self):
        a = section_from_raw(row("A-01", "A", time="화3,4"))
        b = section_from_raw(row("B-01", "B", time="화4,5"))
        registrations = {
            "A-01": no_gate_registration("A-01"),
            "B-01": no_gate_registration("B-01"),
        }
        assessment = assess_candidate(
            (a, b),
            self.profile,
            self.professors,
            registration_assessments=registrations,
        )

        self.assertTrue(assessment.known_infeasible)
        codes = {issue.code for issue in assessment.hard_constraint_violations}
        self.assertIn("registration_time_conflict", codes)
        self.assertFalse(assessment.present_assessment_complete)

    def test_nonparsed_schedule_prevents_fake_timetable_assessment(self):
        section = section_from_raw(row("U-01", "U", time="미정"))
        assessment = assess_candidate(
            (section,),
            self.profile,
            self.professors,
            registration_assessments={"U-01": no_gate_registration("U-01")},
        )

        self.assertIsNone(assessment.timetable_facts)
        self.assertIsNone(assessment.timetable_utility)
        codes = {issue.code for issue in assessment.hard_constraint_unknowns}
        self.assertIn("schedule_unresolved", codes)
        self.assertIn("timetable_utility", assessment.present_preference_unknowns)

    def test_cross_campus_transition_is_both_feasibility_and_utility_unknown(self):
        songdo = section_from_raw(
            row("A-01", "A", time="화3,4", campus="국제")
        )
        sinchon = section_from_raw(
            row("B-01", "B", time="화8,9", campus="신촌")
        )
        assessment = assess_candidate(
            (songdo, sinchon),
            self.profile,
            self.professors,
            registration_assessments={
                "A-01": no_gate_registration("A-01"),
                "B-01": no_gate_registration("B-01"),
            },
        )

        self.assertIsNotNone(assessment.travel_facts)
        self.assertEqual(len(assessment.travel_facts.transitions), 1)
        codes = {issue.code for issue in assessment.hard_constraint_unknowns}
        self.assertIn("travel_feasibility_unresolved", codes)
        self.assertIn(
            "mixed_campus_travel_disutility",
            assessment.present_preference_unknowns,
        )

    def test_observed_freshman_year_gate_is_hard_failure(self):
        section = section_from_raw(row("A-01", "A", time="화3"))
        blocked = assess_freshman_registration(
            "A-01",
            {
                "A-01": {
                    "sy1PercpCnt": 0,
                    "sy2PercpCnt": 10,
                    "sy3PercpCnt": 10,
                    "sy4PercpCnt": 0,
                    "sy5PercpCnt": 0,
                    "sy6PercpCnt": 0,
                }
            },
        )
        assessment = assess_candidate(
            (section,),
            self.profile,
            self.professors,
            registration_assessments={"A-01": blocked},
        )

        self.assertTrue(assessment.known_infeasible)
        self.assertIn(
            "registration_year_gate_block",
            {issue.code for issue in assessment.hard_constraint_violations},
        )

    def test_credit_load_separates_chapel_from_ordinary_credits(self):
        ordinary = section_from_raw(row("A-01", "A", time="화3", credits=3))
        chapel = section_from_raw(
            row("YCA1006-01-00", "YCA1006", time="수3", credits=0.5)
        )
        assessment = assess_candidate(
            (ordinary, chapel),
            self.profile,
            self.professors,
            registration_assessments={
                "A-01": no_gate_registration("A-01"),
                "YCA1006-01-00": no_gate_registration("YCA1006-01-00"),
            },
        )

        self.assertEqual(assessment.load.total_known_credits, 3.5)
        self.assertEqual(assessment.load.ordinary_known_credits, 3.0)
        self.assertEqual(assessment.load.chapel_known_credits, 0.5)

    def test_recognition_is_carried_without_auto_selecting_degree_transition(self):
        scenario = qrm_single_major_2026()
        start = spring_2026_initial_state(scenario)
        section = section_from_raw(
            row("QRM1001-01-00", "QRM1001", time="화3")
        )
        recognition = recognize_section(section, scenario, start)
        assessment = assess_candidate(
            (section,),
            self.profile,
            self.professors,
            registration_assessments={
                section.section_id: no_gate_registration(section.section_id)
            },
            recognition_assessments={section.section_id: recognition},
            degree_scenario=scenario,
        )

        self.assertIsNone(assessment.degree_transition)
        self.assertIn("degree_transition_not_selected", assessment.future_unknowns)
        self.assertEqual(len(assessment.recognition), 1)

    def test_explicit_degree_transition_is_accepted_but_not_invented(self):
        scenario = qrm_single_major_2026()
        start = spring_2026_initial_state(scenario)
        section = section_from_raw(
            row("QRM1001-01-00", "QRM1001", time="화3")
        )
        recognition = recognize_section(section, scenario, start)
        option = recognition.options[0]
        end = apply_recognition(start, scenario, option.effect)
        transition = CandidateDegreeTransition(
            scenario_id=scenario.scenario_id,
            starting_state=start,
            resulting_state=end,
            selected_option_ids=(option.option_id,),
        )

        assessment = assess_candidate(
            (section,),
            self.profile,
            self.professors,
            registration_assessments={
                section.section_id: no_gate_registration(section.section_id)
            },
            recognition_assessments={section.section_id: recognition},
            degree_scenario=scenario,
            degree_transition=transition,
        )

        self.assertEqual(assessment.degree_transition.credits_added, 3.0)
        self.assertNotIn("degree_transition_not_selected", assessment.future_unknowns)

    def test_degree_transition_scenario_mismatch_is_rejected(self):
        scenario = qrm_single_major_2026()
        start = spring_2026_initial_state(scenario)
        transition = CandidateDegreeTransition(
            scenario_id="wrong-scenario",
            starting_state=start,
            resulting_state=start,
            selected_option_ids=(),
        )
        section = section_from_raw(row("A-01", "A", time="화3"))

        with self.assertRaises(CandidateAssessmentError):
            assess_candidate(
                (section,),
                self.profile,
                self.professors,
                degree_scenario=scenario,
                degree_transition=transition,
            )


if __name__ == "__main__":
    unittest.main()
