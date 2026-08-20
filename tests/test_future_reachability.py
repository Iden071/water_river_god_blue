import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.degree import (  # noqa: E402
    Completion,
    CreditBucketRequirement,
    DegreeScenario,
    DegreeState,
    KoreanMajorCreditCap,
    MajorMode,
    SecondMajorSpec,
    SecondMajorStatus,
    SpecificCourseRequirement,
)
from timetable_optimizer.degree_remainder import degree_remainder  # noqa: E402
from timetable_optimizer.future_actions import FutureRecognitionEvidence  # noqa: E402
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
    FutureReachabilityError,
    FutureReachabilityStatus,
    search_future_degree_reachability,
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
from timetable_optimizer.sections import (  # noqa: E402
    DeliveryKind,
    NoListedSchedule,
    ParsedSchedule,
    ScheduleSegment,
    mask_from_blocks,
)


def parsed(day, period):
    blocks = frozenset({(day, period)})
    mask = mask_from_blocks(blocks)
    return ParsedSchedule(
        raw_time_text="scenario",
        raw_room_text="scenario-room",
        segments=(
            ScheduleSegment(
                raw_time_text="scenario",
                raw_room_text="scenario-room",
                blocks=blocks,
                delivery_kind=DeliveryKind.IN_PERSON,
            ),
        ),
        conflict_mask=mask,
        presence_mask=mask,
        fixed_mask=mask,
    )


def offering(offering_id, term_id, course_code, *, schedule=None):
    return FutureOffering(
        offering_id=offering_id,
        term_id=term_id,
        course_code=course_code,
        credits=3.0,
        campus="국제",
        schedule=schedule if schedule is not None else parsed(0, 1),
        evidence=FutureOfferingEvidence(
            kind=FutureOfferingEvidenceKind.EXPLICIT_ASSUMPTION,
            source_id=f"scenario:{offering_id}",
        ),
    )


def tiny_science_scenario():
    return DegreeScenario(
        scenario_id="tiny-science",
        graduation_min_credits=3.0,
        major_mode=MajorMode.SINGLE,
        qrm_major_credit_target=0.0,
        requirements=(
            CreditBucketRequirement(
                requirement_id="cc_scird",
                title="Science",
                target_credits=3.0,
                qualification_rule_id="uic_science_literacy_or_rdqm_2026",
            ),
        ),
        qrm_korean_credit_cap=KoreanMajorCreditCap(4, 12.0),
        exclusive_major_assignment=True,
        second_major=SecondMajorSpec(SecondMajorStatus.NONE),
    )


def tiny_two_course_scenario():
    return DegreeScenario(
        scenario_id="tiny-two-course",
        graduation_min_credits=6.0,
        major_mode=MajorMode.SINGLE,
        qrm_major_credit_target=0.0,
        requirements=(
            SpecificCourseRequirement(
                "req_mat", "Math", ("MAT1001",), 3.0
            ),
            SpecificCourseRequirement(
                "req_phy", "Physics", ("PHY1001",), 3.0
            ),
        ),
        qrm_korean_credit_cap=KoreanMajorCreditCap(4, 12.0),
        exclusive_major_assignment=True,
        second_major=SecondMajorSpec(SecondMajorStatus.NONE),
    )


def future_term(term_id, *, cap=3.0, catalogue=FutureCatalogueBasisKind.EXPLICIT_SCENARIO):
    basis = (
        FutureCatalogueBasis(catalogue, source_terms=("2026S",))
        if catalogue is FutureCatalogueBasisKind.HISTORICAL_ANALOG
        else FutureCatalogueBasis(catalogue)
    )
    return FutureTermScenario(
        term_id=term_id,
        activity=TermActivity.ACTIVE,
        ordinary_credit_cap=cap,
        residence=ResidenceState.HOME,
        campus_access=CampusAccessScenario(CampusAccessKind.ANY),
        catalogue_basis=basis,
    )


def exact_problem(scenario, state, terms, opportunity_sets):
    return build_future_planning_problem(
        "reachability-test",
        degree_remainder(state, scenario),
        FutureTimelineScenario("timeline", tuple(terms)),
        FutureOpportunityScenario("opportunities", tuple(opportunity_sets)),
    )


def explicit_set(term_id, offerings=()):
    return FutureTermOpportunitySet(
        term_id=term_id,
        status=OpportunitySetStatus.EXPLICIT_SCENARIO,
        offerings=tuple(offerings),
        source_id=f"scenario:{term_id}",
    )


class FutureReachabilityTests(unittest.TestCase):
    def test_concrete_witness_proves_reachability(self):
        scenario = tiny_science_scenario()
        state = DegreeState()
        mat = offering("2027S:mat", "2027S", "MAT1001")
        problem = exact_problem(
            scenario,
            state,
            (future_term("2027S"),),
            (explicit_set("2027S", (mat,)),),
        )

        result = search_future_degree_reachability(problem, scenario, state)

        self.assertEqual(result.status, FutureReachabilityStatus.REACHABLE)
        self.assertIs(result.degree_reachable, True)
        self.assertIsNotNone(result.witness)
        self.assertTrue(result.witness.remainder.degree_obligations_complete)
        self.assertEqual(result.witness.steps[0].offering_ids, ("2027S:mat",))

    def test_exhausted_exact_empty_scenario_proves_unreachable(self):
        scenario = tiny_science_scenario()
        state = DegreeState()
        problem = exact_problem(
            scenario,
            state,
            (future_term("2027S"),),
            (explicit_set("2027S"),),
        )

        result = search_future_degree_reachability(problem, scenario, state)

        self.assertEqual(
            result.status, FutureReachabilityStatus.PROVEN_UNREACHABLE
        )
        self.assertIs(result.degree_reachable, False)
        self.assertTrue(result.proof_complete)

    def test_unresolved_schedule_blocks_negative_proof(self):
        scenario = tiny_science_scenario()
        state = DegreeState()
        mat = offering(
            "2027S:mat",
            "2027S",
            "MAT1001",
            schedule=NoListedSchedule("", ""),
        )
        problem = exact_problem(
            scenario,
            state,
            (future_term("2027S"),),
            (explicit_set("2027S", (mat,)),),
        )

        result = search_future_degree_reachability(problem, scenario, state)

        self.assertEqual(result.status, FutureReachabilityStatus.UNRESOLVED)
        self.assertIsNone(result.degree_reachable)
        self.assertTrue(
            any(unknown.code == "offering_schedule_unresolved" for unknown in result.unknowns)
        )

    def test_node_limit_returns_unknown_not_false(self):
        scenario = tiny_science_scenario()
        state = DegreeState()
        mat = offering("2027S:mat", "2027S", "MAT1001")
        problem = exact_problem(
            scenario,
            state,
            (future_term("2027S"),),
            (explicit_set("2027S", (mat,)),),
        )

        result = search_future_degree_reachability(
            problem,
            scenario,
            state,
            max_selection_evaluations=1,
        )

        self.assertEqual(result.status, FutureReachabilityStatus.NODE_LIMIT)
        self.assertIsNone(result.degree_reachable)

    def test_input_readiness_blocker_prevents_exact_search_claim(self):
        scenario = tiny_science_scenario()
        state = DegreeState()
        mat = offering("2027S:mat", "2027S", "MAT1001")
        problem = build_future_planning_problem(
            "partial",
            degree_remainder(state, scenario),
            FutureTimelineScenario(
                "timeline",
                (
                    future_term(
                        "2027S",
                        catalogue=FutureCatalogueBasisKind.HISTORICAL_ANALOG,
                    ),
                ),
            ),
            FutureOpportunityScenario(
                "opportunities",
                (
                    FutureTermOpportunitySet(
                        term_id="2027S",
                        status=OpportunitySetStatus.PARTIAL,
                        offerings=(mat,),
                    ),
                ),
            ),
        )
        self.assertFalse(problem.exact_search_ready)

        result = search_future_degree_reachability(problem, scenario, state)

        self.assertEqual(result.status, FutureReachabilityStatus.INPUT_BLOCKED)
        self.assertIsNone(result.degree_reachable)
        self.assertIn("opportunity_set_partial", result.input_blocker_codes)

    def test_remainder_state_mismatch_is_rejected(self):
        scenario = tiny_science_scenario()
        empty = DegreeState()
        problem = exact_problem(
            scenario,
            empty,
            (future_term("2027S"),),
            (explicit_set("2027S"),),
        )
        different = DegreeState(
            completions=(Completion("other", "OTHER1000", 1.0),)
        )

        with self.assertRaises(FutureReachabilityError):
            search_future_degree_reachability(problem, scenario, different)

    def test_two_term_witness_evolves_same_degree_state_across_terms(self):
        scenario = tiny_two_course_scenario()
        state = DegreeState()
        mat = offering("2027S:mat", "2027S", "MAT1001", schedule=parsed(0, 1))
        phy = offering("2027F:phy", "2027F", "PHY1001", schedule=parsed(1, 1))
        problem = exact_problem(
            scenario,
            state,
            (future_term("2027S"), future_term("2027F")),
            (
                explicit_set("2027S", (mat,)),
                explicit_set("2027F", (phy,)),
            ),
        )

        result = search_future_degree_reachability(problem, scenario, state)

        self.assertEqual(result.status, FutureReachabilityStatus.REACHABLE)
        self.assertEqual(len(result.witness.steps), 2)
        self.assertEqual(result.witness.steps[0].offering_ids, ("2027S:mat",))
        self.assertEqual(result.witness.steps[1].offering_ids, ("2027F:phy",))

    def test_credit_cap_can_prove_one_term_scenario_unreachable(self):
        scenario = tiny_two_course_scenario()
        state = DegreeState()
        mat = offering("2027S:mat", "2027S", "MAT1001", schedule=parsed(0, 1))
        phy = offering("2027S:phy", "2027S", "PHY1001", schedule=parsed(1, 1))
        problem = exact_problem(
            scenario,
            state,
            (future_term("2027S", cap=3.0),),
            (explicit_set("2027S", (mat, phy)),),
        )

        result = search_future_degree_reachability(problem, scenario, state)

        self.assertEqual(
            result.status, FutureReachabilityStatus.PROVEN_UNREACHABLE
        )
        self.assertIs(result.degree_reachable, False)

    def test_unresolved_retake_policy_blocks_negative_proof_but_explicit_no_credit_does_not(self):
        scenario = tiny_science_scenario()
        # The course was completed previously but not assigned to the Science bucket.
        state = DegreeState(
            completions=(Completion("past-mat", "MAT1001", 3.0),)
        )
        repeat = offering("2027S:repeat-mat", "2027S", "MAT1001")
        problem = exact_problem(
            scenario,
            state,
            (future_term("2027S"),),
            (explicit_set("2027S", (repeat,)),),
        )

        unresolved = search_future_degree_reachability(problem, scenario, state)
        self.assertEqual(unresolved.status, FutureReachabilityStatus.UNRESOLVED)
        self.assertTrue(
            any(unknown.code == "repeat_credit_unresolved" for unknown in unresolved.unknowns)
        )

        resolved = search_future_degree_reachability(
            problem,
            scenario,
            state,
            recognition_evidence={
                repeat.offering_id: FutureRecognitionEvidence(
                    source_id="scenario:retake-policy",
                    repeat_credit_allowed=False,
                )
            },
        )
        self.assertEqual(
            resolved.status, FutureReachabilityStatus.PROVEN_UNREACHABLE
        )


if __name__ == "__main__":
    unittest.main()
