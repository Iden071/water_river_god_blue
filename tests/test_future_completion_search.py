import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.degree import (  # noqa: E402
    DegreeScenario,
    DegreeState,
    KoreanMajorCreditCap,
    MajorMode,
    SecondMajorSpec,
    SecondMajorStatus,
    SpecificCourseRequirement,
)
from timetable_optimizer.degree_remainder import degree_remainder  # noqa: E402
from timetable_optimizer.future_completion_search import (  # noqa: E402
    FutureCompletionSearchStatus,
    enumerate_future_degree_completion_histories,
)
from timetable_optimizer.future_opportunities import (  # noqa: E402
    FutureOffering,
    FutureOfferingEvidence,
    FutureOfferingEvidenceKind,
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
from timetable_optimizer.sections import (  # noqa: E402
    DeliveryKind,
    NoListedSchedule,
    ParsedSchedule,
    ScheduleSegment,
    mask_from_blocks,
)


def parsed(day=0, period=1):
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


def scenario():
    return DegreeScenario(
        scenario_id="one-math",
        graduation_min_credits=3.0,
        major_mode=MajorMode.SINGLE,
        qrm_major_credit_target=0.0,
        requirements=(
            SpecificCourseRequirement(
                "req_math", "Math", ("MAT1001",), 3.0
            ),
        ),
        qrm_korean_credit_cap=KoreanMajorCreditCap(4, 12.0),
        exclusive_major_assignment=True,
        second_major=SecondMajorSpec(SecondMajorStatus.NONE),
    )


def term(term_id):
    return FutureTermScenario(
        term_id=term_id,
        activity=TermActivity.ACTIVE,
        ordinary_credit_cap=3.0,
        residence=ResidenceState.HOME,
        campus_access=CampusAccessScenario(CampusAccessKind.ANY),
        catalogue_basis=FutureCatalogueBasis(
            FutureCatalogueBasisKind.EXPLICIT_SCENARIO
        ),
    )


def offering(offering_id, term_id, *, schedule=None, code="MAT1001"):
    return FutureOffering(
        offering_id=offering_id,
        term_id=term_id,
        course_code=code,
        credits=3.0,
        campus="국제",
        schedule=schedule if schedule is not None else parsed(),
        evidence=FutureOfferingEvidence(
            FutureOfferingEvidenceKind.EXPLICIT_ASSUMPTION,
            source_id=f"scenario:{offering_id}",
        ),
    )


def opportunity_set(term_id, offerings=()):
    return FutureTermOpportunitySet(
        term_id=term_id,
        status=OpportunitySetStatus.EXPLICIT_SCENARIO,
        offerings=tuple(offerings),
        source_id=f"scenario:{term_id}",
    )


def problem(terms, sets):
    degree_scenario = scenario()
    state = DegreeState()
    return (
        degree_scenario,
        state,
        build_future_planning_problem(
            "completion-search-test",
            degree_remainder(state, degree_scenario),
            FutureTimelineScenario("timeline", tuple(terms)),
            FutureOpportunityScenario("opportunities", tuple(sets)),
        ),
    )


class FutureCompletionSearchTests(unittest.TestCase):
    def test_enumerates_early_and_late_completion_histories(self):
        early = offering("2027S:math", "2027S")
        late = offering("2027F:math", "2027F")
        degree_scenario, state, planning = problem(
            (term("2027S"), term("2027F")),
            (
                opportunity_set("2027S", (early,)),
                opportunity_set("2027F", (late,)),
            ),
        )

        result = enumerate_future_degree_completion_histories(
            planning, degree_scenario, state
        )

        self.assertEqual(result.status, FutureCompletionSearchStatus.COMPLETE)
        self.assertEqual(len(result.witnesses), 2)
        horizons = {tuple(step.term_id for step in witness.steps) for witness in result.witnesses}
        self.assertEqual(horizons, {("2027S",), ("2027S", "2027F")})
        selections = {
            tuple(step.offering_ids for step in witness.steps)
            for witness in result.witnesses
        }
        self.assertIn((("2027S:math",),), selections)
        self.assertIn(((), ("2027F:math",)), selections)

    def test_known_completion_is_retained_when_another_branch_is_unresolved(self):
        exact = offering("2027S:a-exact", "2027S")
        unknown = offering(
            "2027S:z-unknown",
            "2027S",
            schedule=NoListedSchedule("", ""),
        )
        degree_scenario, state, planning = problem(
            (term("2027S"),),
            (opportunity_set("2027S", (exact, unknown)),),
        )

        result = enumerate_future_degree_completion_histories(
            planning, degree_scenario, state
        )

        self.assertEqual(result.status, FutureCompletionSearchStatus.UNRESOLVED)
        self.assertTrue(result.any_completion_found)
        self.assertTrue(
            any(
                witness.steps[0].offering_ids == ("2027S:a-exact",)
                for witness in result.witnesses
            )
        )
        self.assertTrue(
            any(
                unknown.code == "offering_schedule_unresolved"
                for unknown in result.unknowns
            )
        )

    def test_node_limit_keeps_histories_found_before_truncation(self):
        first = offering("2027S:a-math", "2027S")
        second = offering("2027S:b-math", "2027S", schedule=parsed(1, 1))
        degree_scenario, state, planning = problem(
            (term("2027S"),),
            (opportunity_set("2027S", (first, second)),),
        )

        result = enumerate_future_degree_completion_histories(
            planning,
            degree_scenario,
            state,
            max_selection_evaluations=2,
        )

        self.assertEqual(result.status, FutureCompletionSearchStatus.NODE_LIMIT)
        self.assertEqual(len(result.witnesses), 1)
        self.assertEqual(
            result.witnesses[0].steps[0].offering_ids,
            ("2027S:a-math",),
        )
        self.assertFalse(result.enumeration_complete)

    def test_exact_empty_horizon_proves_unreachable(self):
        degree_scenario, state, planning = problem(
            (term("2027S"),),
            (opportunity_set("2027S"),),
        )

        result = enumerate_future_degree_completion_histories(
            planning, degree_scenario, state
        )

        self.assertEqual(
            result.status, FutureCompletionSearchStatus.PROVEN_UNREACHABLE
        )
        self.assertFalse(result.any_completion_found)
        self.assertTrue(result.enumeration_complete)


if __name__ == "__main__":
    unittest.main()
