import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.candidate_assessment import (  # noqa: E402
    CandidateAssessment,
    CandidateConstraintIssue,
    CandidateDegreeTransition,
    CandidateLoadFacts,
    ConstraintEvidenceStatus,
)
from timetable_optimizer.degree import (  # noqa: E402
    DegreeScenario,
    DegreeState,
    KoreanMajorCreditCap,
    MajorMode,
    RecognitionEffect,
    SecondMajorSpec,
    SecondMajorStatus,
    SpecificCourseRequirement,
    apply_recognition,
)
from timetable_optimizer.degree_remainder import degree_remainder  # noqa: E402
from timetable_optimizer.fall_continuation import (  # noqa: E402
    FallContinuationError,
    FallContinuationStatus,
    build_fall_continuation_bridge,
)
from timetable_optimizer.future_opportunities import (  # noqa: E402
    FutureOpportunityScenario,
    FutureTermOpportunitySet,
    OpportunitySetStatus,
)
from timetable_optimizer.future_problem import build_future_planning_problem  # noqa: E402
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
from timetable_optimizer.preferences import EstimateStatus  # noqa: E402
from timetable_optimizer.timetable_utility import (  # noqa: E402
    PartialUtilityAssessment,
    UtilityContribution,
)


def scenario():
    return DegreeScenario(
        scenario_id="fall-bridge-test",
        graduation_min_credits=6.0,
        major_mode=MajorMode.SINGLE,
        qrm_major_credit_target=0.0,
        requirements=(
            SpecificCourseRequirement("req_a", "A", ("A",), 3.0),
            SpecificCourseRequirement("req_b", "B", ("B",), 3.0),
        ),
        qrm_korean_credit_cap=KoreanMajorCreditCap(4, 12.0),
        exclusive_major_assignment=True,
        second_major=SecondMajorSpec(SecondMajorStatus.NONE),
    )


def future_template(degree_scenario, state):
    term = FutureTermScenario(
        term_id="2027S",
        activity=TermActivity.ACTIVE,
        ordinary_credit_cap=18.0,
        residence=ResidenceState.HOME,
        campus_access=CampusAccessScenario(CampusAccessKind.ANY),
        catalogue_basis=FutureCatalogueBasis(
            FutureCatalogueBasisKind.EXPLICIT_SCENARIO
        ),
    )
    opportunities = FutureOpportunityScenario(
        "future-opportunities",
        (
            FutureTermOpportunitySet(
                "2027S",
                OpportunitySetStatus.EXPLICIT_SCENARIO,
                source_id="scenario:2027S",
            ),
        ),
    )
    return build_future_planning_problem(
        "template",
        degree_remainder(state, degree_scenario),
        FutureTimelineScenario("timeline", (term,)),
        opportunities,
    )


def exact_timetable():
    return PartialUtilityAssessment(
        contributions=(
            UtilityContribution(
                dimension_id="present",
                quantity=1.0,
                status=EstimateStatus.EXACT,
                lower=2.0,
                upper=2.0,
                point=2.0,
            ),
        ),
        unresolved=(),
        active_relations=(),
        measured_lower=2.0,
        measured_upper=2.0,
        heuristic_point_delta=0.0,
    )


def candidate(transition=None, *, hard_issues=(), present_unknowns=(), future_unknowns=()):
    return CandidateAssessment(
        section_ids=("A-01",),
        load=CandidateLoadFacts(3.0, 3.0, 0.0, ()),
        timetable_facts=None,
        timetable_utility=exact_timetable(),
        course_preferences=(),
        travel_facts=None,
        registration=(),
        recognition=(),
        degree_transition=transition,
        hard_constraint_issues=tuple(hard_issues),
        present_preference_unknowns=frozenset(present_unknowns),
        future_unknowns=frozenset(future_unknowns),
    )


class FallContinuationBridgeTests(unittest.TestCase):
    def setUp(self):
        self.scenario = scenario()
        self.start = DegreeState()
        effect = RecognitionEffect.course(
            completion_id="A-01",
            course_code="A",
            credits=3.0,
            satisfy=("req_a",),
        )
        self.end = apply_recognition(self.start, self.scenario, effect)
        self.transition = CandidateDegreeTransition(
            scenario_id=self.scenario.scenario_id,
            starting_state=self.start,
            resulting_state=self.end,
            selected_option_ids=("A-01:default",),
        )
        self.template = future_template(self.scenario, self.start)

    def test_rebased_future_remainder_reflects_fall_degree_transition(self):
        bridge = build_fall_continuation_bridge(
            "fall-a",
            candidate(self.transition),
            self.scenario,
            self.template,
        )
        self.assertEqual(bridge.status, FallContinuationStatus.READY)
        self.assertTrue(bridge.future_search_ready)
        self.assertIsNotNone(bridge.future_problem)
        self.assertEqual(
            bridge.future_problem.degree_remainder.requirement_ids,
            ("req_b",),
        )
        self.assertEqual(
            bridge.future_problem.degree_remainder.graduation_credit_deficit,
            3.0,
        )

    def test_missing_degree_transition_blocks_exact_continuation(self):
        bridge = build_fall_continuation_bridge(
            "fall-a",
            candidate(
                None,
                future_unknowns=("degree_transition_not_selected",),
            ),
            self.scenario,
            self.template,
        )
        self.assertEqual(
            bridge.status, FallContinuationStatus.DEGREE_TRANSITION_UNRESOLVED
        )
        self.assertFalse(bridge.future_search_ready)
        self.assertIsNone(bridge.future_problem)

    def test_present_preference_unknown_does_not_corrupt_degree_rebase(self):
        bridge = build_fall_continuation_bridge(
            "fall-a",
            candidate(
                self.transition,
                present_unknowns=("registration_obtainability::A-01",),
            ),
            self.scenario,
            self.template,
        )
        self.assertEqual(bridge.status, FallContinuationStatus.READY)
        self.assertTrue(bridge.future_search_ready)
        self.assertFalse(bridge.whole_plan_utility_complete_before_future)

    def test_hard_feasibility_unknown_blocks_continuation_search(self):
        issue = CandidateConstraintIssue(
            code="travel_feasibility_unresolved",
            status=ConstraintEvidenceStatus.UNRESOLVED,
            message="travel time unknown",
        )
        bridge = build_fall_continuation_bridge(
            "fall-a",
            candidate(self.transition, hard_issues=(issue,)),
            self.scenario,
            self.template,
        )
        self.assertEqual(
            bridge.status, FallContinuationStatus.FALL_HARD_UNRESOLVED
        )
        self.assertFalse(bridge.future_search_ready)

    def test_future_template_must_match_transition_starting_state(self):
        other_start = DegreeState(
            completions=self.end.completions,
            satisfied_requirements=self.end.satisfied_requirements,
        )
        bad_template = future_template(self.scenario, other_start)
        with self.assertRaises(FallContinuationError):
            build_fall_continuation_bridge(
                "fall-a",
                candidate(self.transition),
                self.scenario,
                bad_template,
            )


if __name__ == "__main__":
    unittest.main()
