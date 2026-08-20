import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.course_preferences import ProfessorRatingBook  # noqa: E402
from timetable_optimizer.degree import (  # noqa: E402
    qrm_single_major_2026,
    spring_2026_initial_state,
)
from timetable_optimizer.degree_remainder import degree_remainder  # noqa: E402
from timetable_optimizer.future_opportunities import (  # noqa: E402
    FutureOffering,
    FutureOfferingEvidence,
    FutureOfferingEvidenceKind,
    FutureOpportunityScenario,
    FutureTermOpportunitySet,
    OpportunitySetStatus,
)
from timetable_optimizer.future_problem import build_future_planning_problem  # noqa: E402
from timetable_optimizer.future_reachability import (  # noqa: E402
    FutureReachabilityWitness,
    FutureTermWitness,
)
from timetable_optimizer.future_scenarios import (  # noqa: E402
    CampusAccessKind,
    CampusAccessScenario,
    FutureCatalogueBasis,
    FutureCatalogueBasisKind,
    FutureTermScenario,
    FutureTimelineScenario,
    ResidenceState,
    TermActivity,
)
from timetable_optimizer.future_witness_utility import (  # noqa: E402
    FutureWitnessUtilityError,
    assess_future_witness_utility,
)
from timetable_optimizer.preferences import PreferenceProfile  # noqa: E402
from timetable_optimizer.sections import section_from_raw  # noqa: E402


def row(section_id="A-01", course_code="QRM1001"):
    return {
        "subjtnbCorsePrcts": section_id,
        "subjtnb": course_code,
        "subjtEngNm": course_code,
        "subjtNm": course_code,
        "campsDivNm": "국제",
        "cdt": 3,
        "cgprfNm": "Professor A",
        "srclnLctreLangDivCd": "10",
        "atntnMattrDesc": "",
        "gradeEvlMthdDivNm": "절대평가",
        "rmvlcYn": "0",
        "rmvlcYnNm": " ",
        "lctreTimeNm": "화3",
        "lecrmNm": "강의실A",
        "subjtClNm": "",
    }


def active_term():
    return FutureTermScenario(
        term_id="2027S",
        activity=TermActivity.ACTIVE,
        ordinary_credit_cap=18.0,
        residence=ResidenceState.HOME,
        campus_access=CampusAccessScenario(CampusAccessKind.ANY),
        catalogue_basis=FutureCatalogueBasis(
            FutureCatalogueBasisKind.EXPLICIT_SCENARIO
        ),
    )


def leave_term():
    return FutureTermScenario(
        term_id="military",
        activity=TermActivity.LEAVE,
        ordinary_credit_cap=0.0,
        residence=ResidenceState.OTHER,
        campus_access=CampusAccessScenario(CampusAccessKind.UNRESOLVED),
        catalogue_basis=FutureCatalogueBasis(FutureCatalogueBasisKind.UNRESOLVED),
    )


class FutureWitnessUtilityBridgeTests(unittest.TestCase):
    def setUp(self):
        scenario = qrm_single_major_2026()
        self.state = spring_2026_initial_state(scenario)
        self.remainder = degree_remainder(self.state, scenario)
        section = section_from_raw(row())
        self.offering = FutureOffering(
            offering_id="2027S:qrm1001",
            term_id="2027S",
            course_code="QRM1001",
            credits=3.0,
            campus="국제",
            schedule=section.schedule,
            professor="Professor A",
            evidence=FutureOfferingEvidence(
                FutureOfferingEvidenceKind.EXPLICIT_ASSUMPTION,
                source_id="scenario:2027S:qrm1001",
            ),
        )
        timeline = FutureTimelineScenario("timeline", (active_term(), leave_term()))
        opportunities = FutureOpportunityScenario(
            "opportunities",
            (
                FutureTermOpportunitySet(
                    "2027S",
                    OpportunitySetStatus.EXPLICIT_SCENARIO,
                    offerings=(self.offering,),
                    source_id="scenario:2027S",
                ),
                FutureTermOpportunitySet(
                    "military",
                    OpportunitySetStatus.EXPLICIT_SCENARIO,
                    source_id="scenario:military-empty",
                ),
            ),
        )
        self.problem = build_future_planning_problem(
            "problem", self.remainder, timeline, opportunities
        )

    def witness(self, *, first_offerings=("2027S:qrm1001",)):
        return FutureReachabilityWitness(
            steps=(
                FutureTermWitness("2027S", first_offerings, ("action",)),
                FutureTermWitness("military", (), ()),
            ),
            resulting_state=self.state,
            remainder=self.remainder,
        )

    def test_witness_maps_back_to_exact_scenario_offerings_by_term(self):
        result = assess_future_witness_utility(
            self.problem,
            self.witness(),
            PreferenceProfile("empty"),
            ProfessorRatingBook(()),
        )
        history = result.utility_history
        self.assertEqual(history.term_ids, ("2027S", "military"))
        self.assertEqual(history.terms[0].offering_ids, ("2027S:qrm1001",))
        self.assertTrue(history.terms[0].academic_utility_applicable)
        self.assertFalse(history.terms[1].academic_utility_applicable)

    def test_early_completion_witness_may_be_timeline_prefix(self):
        early = FutureReachabilityWitness(
            steps=(
                FutureTermWitness(
                    "2027S", ("2027S:qrm1001",), ("action",)
                ),
            ),
            resulting_state=self.state,
            remainder=self.remainder,
        )
        result = assess_future_witness_utility(
            self.problem,
            early,
            PreferenceProfile("empty"),
            ProfessorRatingBook(()),
        )
        self.assertEqual(result.utility_history.term_ids, ("2027S",))
        self.assertEqual(result.completion_term_id, "2027S")

    def test_witness_term_sequence_must_be_timeline_prefix(self):
        bad = FutureReachabilityWitness(
            steps=(FutureTermWitness("military", (), ()),),
            resulting_state=self.state,
            remainder=self.remainder,
        )
        with self.assertRaises(FutureWitnessUtilityError):
            assess_future_witness_utility(
                self.problem,
                bad,
                PreferenceProfile("empty"),
                ProfessorRatingBook(()),
            )

    def test_witness_cannot_reference_offering_outside_scenario(self):
        with self.assertRaises(FutureWitnessUtilityError):
            assess_future_witness_utility(
                self.problem,
                self.witness(first_offerings=("2027S:not-in-scenario",)),
                PreferenceProfile("empty"),
                ProfessorRatingBook(()),
            )


if __name__ == "__main__":
    unittest.main()
