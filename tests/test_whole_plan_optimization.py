import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.candidate_assessment import (  # noqa: E402
    CandidateAssessment,
    CandidateDegreeTransition,
    CandidateLoadFacts,
)
from timetable_optimizer.course_preferences import ProfessorRatingBook  # noqa: E402
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
from timetable_optimizer.fall_continuation import build_fall_continuation_bridge  # noqa: E402
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
from timetable_optimizer.future_utility import (  # noqa: E402
    TemporalUtilityAggregation,
    TemporalUtilityWeight,
)
from timetable_optimizer.preferences import (  # noqa: E402
    EstimateStatus,
    PreferenceProfile,
)
from timetable_optimizer.timetable_utility import (  # noqa: E402
    PartialUtilityAssessment,
    UtilityContribution,
)
from timetable_optimizer.whole_plan_optimization import (  # noqa: E402
    WholePlanOptimizationError,
    WholePlanOptimizationStatus,
    assess_fall_candidate_whole_plan,
)


def scenario(*, include_b=False):
    requirements = [SpecificCourseRequirement("req_a", "A", ("A",), 3.0)]
    if include_b:
        requirements.append(SpecificCourseRequirement("req_b", "B", ("B",), 3.0))
    return DegreeScenario(
        scenario_id="whole-plan-test-b" if include_b else "whole-plan-test-a",
        graduation_min_credits=6.0 if include_b else 3.0,
        major_mode=MajorMode.SINGLE,
        qrm_major_credit_target=0.0,
        requirements=tuple(requirements),
        qrm_korean_credit_cap=KoreanMajorCreditCap(4, 12.0),
        exclusive_major_assignment=True,
        second_major=SecondMajorSpec(SecondMajorStatus.NONE),
    )


def template(degree_scenario, start):
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
        "future",
        (
            FutureTermOpportunitySet(
                "2027S",
                OpportunitySetStatus.EXPLICIT_SCENARIO,
                source_id="scenario:2027S-empty",
            ),
        ),
    )
    return build_future_planning_problem(
        "template",
        degree_remainder(start, degree_scenario),
        FutureTimelineScenario("timeline", (term,)),
        opportunities,
    )


def transition(degree_scenario, start):
    effect = RecognitionEffect.course(
        completion_id="A-01",
        course_code="A",
        credits=3.0,
        satisfy=("req_a",),
    )
    end = apply_recognition(start, degree_scenario, effect)
    return CandidateDegreeTransition(
        scenario_id=degree_scenario.scenario_id,
        starting_state=start,
        resulting_state=end,
        selected_option_ids=("A-01:default",),
    )


def candidate(degree_transition, *, present_unknowns=()):
    timetable = PartialUtilityAssessment(
        contributions=(
            UtilityContribution(
                dimension_id="present_exact",
                quantity=1.0,
                status=EstimateStatus.EXACT,
                lower=5.0,
                upper=5.0,
                point=5.0,
            ),
        ),
        unresolved=(),
        active_relations=(),
        measured_lower=5.0,
        measured_upper=5.0,
        heuristic_point_delta=0.0,
    )
    return CandidateAssessment(
        section_ids=("A-01",),
        load=CandidateLoadFacts(3.0, 3.0, 0.0, ()),
        timetable_facts=None,
        timetable_utility=timetable,
        course_preferences=(),
        travel_facts=None,
        registration=(),
        recognition=(),
        degree_transition=degree_transition,
        hard_constraint_issues=(),
        present_preference_unknowns=frozenset(present_unknowns),
        future_unknowns=frozenset(),
    )


def policy(fall_weight=1.0, future_weight=1.0):
    return TemporalUtilityAggregation(
        source_id="user:whole-plan-policy",
        weights=(
            TemporalUtilityWeight("2026F", fall_weight),
            TemporalUtilityWeight("2027S", future_weight),
        ),
    )


class WholePlanOptimizationTests(unittest.TestCase):
    def run_plan(self, degree_scenario, fall_candidate, temporal_policy):
        start = fall_candidate.degree_transition.starting_state
        bridge = build_fall_continuation_bridge(
            "fall-a",
            fall_candidate,
            degree_scenario,
            template(degree_scenario, start),
        )
        return assess_fall_candidate_whole_plan(
            bridge,
            degree_scenario,
            PreferenceProfile("empty"),
            ProfessorRatingBook(()),
            temporal_policy,
        )

    def test_fall_and_future_use_one_explicit_temporal_objective(self):
        degree_scenario = scenario()
        start = DegreeState()
        result = self.run_plan(
            degree_scenario,
            candidate(transition(degree_scenario, start)),
            policy(fall_weight=2.0, future_weight=0.5),
        )

        self.assertEqual(result.status, WholePlanOptimizationStatus.OPTIMUM_PROVEN)
        self.assertIsNotNone(result.proven_best)
        self.assertEqual(result.proven_best.term_ids, ("2026F",))
        self.assertEqual(result.proven_best.complete_bounds, (10.0, 10.0))
        self.assertEqual(result.future_search.witnesses[0].steps, ())

    def test_positive_fall_weight_keeps_present_unknown_visible(self):
        degree_scenario = scenario()
        start = DegreeState()
        result = self.run_plan(
            degree_scenario,
            candidate(
                transition(degree_scenario, start),
                present_unknowns=("registration_obtainability::A-01",),
            ),
            policy(fall_weight=1.0, future_weight=0.0),
        )
        self.assertEqual(
            result.status, WholePlanOptimizationStatus.UTILITY_UNRESOLVED
        )
        self.assertIn(
            "2026F::registration_obtainability::A-01",
            result.candidates[0].unresolved_dimensions,
        )

    def test_zero_fall_weight_may_ignore_preference_unknown_but_not_degree_feasibility(self):
        degree_scenario = scenario()
        start = DegreeState()
        result = self.run_plan(
            degree_scenario,
            candidate(
                transition(degree_scenario, start),
                present_unknowns=("registration_obtainability::A-01",),
            ),
            policy(fall_weight=0.0, future_weight=1.0),
        )
        self.assertEqual(result.status, WholePlanOptimizationStatus.OPTIMUM_PROVEN)
        self.assertEqual(result.proven_best.complete_bounds, (0.0, 0.0))

    def test_future_unreachable_after_fall_is_not_rescued_by_high_present_utility(self):
        degree_scenario = scenario(include_b=True)
        start = DegreeState()
        result = self.run_plan(
            degree_scenario,
            candidate(transition(degree_scenario, start)),
            policy(fall_weight=100.0, future_weight=1.0),
        )
        self.assertEqual(
            result.status, WholePlanOptimizationStatus.PROVEN_UNREACHABLE
        )
        self.assertFalse(result.candidates)

    def test_master_policy_must_include_fall_and_full_future_timeline(self):
        degree_scenario = scenario()
        start = DegreeState()
        fall_candidate = candidate(transition(degree_scenario, start))
        bridge = build_fall_continuation_bridge(
            "fall-a",
            fall_candidate,
            degree_scenario,
            template(degree_scenario, start),
        )
        bad = TemporalUtilityAggregation(
            source_id="bad",
            weights=(TemporalUtilityWeight("2027S", 1.0),),
        )
        with self.assertRaises(WholePlanOptimizationError):
            assess_fall_candidate_whole_plan(
                bridge,
                degree_scenario,
                PreferenceProfile("empty"),
                ProfessorRatingBook(()),
                bad,
            )


if __name__ == "__main__":
    unittest.main()
