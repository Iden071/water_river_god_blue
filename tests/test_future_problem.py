import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.degree import (  # noqa: E402
    qrm_double_major_shell_2026,
    qrm_single_major_2026,
    spring_2026_initial_state,
)
from timetable_optimizer.degree_remainder import degree_remainder  # noqa: E402
from timetable_optimizer.future_opportunities import (  # noqa: E402
    FutureOpportunityScenario,
    FutureTermOpportunitySet,
    OpportunitySetStatus,
)
from timetable_optimizer.future_problem import (  # noqa: E402
    FutureProblemError,
    build_future_planning_problem,
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


def active_term(
    term_id="2027S",
    *,
    campus=CampusAccessKind.ANY,
    catalogue=FutureCatalogueBasisKind.EXPLICIT_SCENARIO,
):
    return FutureTermScenario(
        term_id=term_id,
        activity=TermActivity.ACTIVE,
        ordinary_credit_cap=18.0,
        residence=ResidenceState.HOME,
        campus_access=CampusAccessScenario(campus),
        catalogue_basis=FutureCatalogueBasis(catalogue),
    )


def explicit_empty(term_id="2027S"):
    return FutureTermOpportunitySet(
        term_id=term_id,
        status=OpportunitySetStatus.EXPLICIT_SCENARIO,
        source_id=f"scenario:{term_id}",
    )


class FuturePlanningProblemTests(unittest.TestCase):
    def single_remainder(self):
        scenario = qrm_single_major_2026()
        return degree_remainder(spring_2026_initial_state(scenario), scenario)

    def test_complete_explicit_inputs_are_ready_for_exact_search(self):
        problem = build_future_planning_problem(
            "exact",
            self.single_remainder(),
            FutureTimelineScenario("timeline", (active_term(),)),
            FutureOpportunityScenario("opps", (explicit_empty(),)),
        )
        self.assertTrue(problem.exact_search_ready)
        self.assertFalse(problem.blockers)

    def test_partial_historical_opportunities_block_exact_claim(self):
        timeline = FutureTimelineScenario(
            "timeline",
            (
                active_term(
                    catalogue=FutureCatalogueBasisKind.HISTORICAL_ANALOG
                ),
            ),
        )
        opportunities = FutureOpportunityScenario(
            "opps",
            (
                FutureTermOpportunitySet(
                    term_id="2027S",
                    status=OpportunitySetStatus.PARTIAL,
                ),
            ),
        )
        problem = build_future_planning_problem(
            "historical", self.single_remainder(), timeline, opportunities
        )
        self.assertFalse(problem.exact_search_ready)
        self.assertIn("opportunity_set_partial", problem.blocker_codes)

    def test_unresolved_campus_and_catalogue_are_visible_separate_blockers(self):
        timeline = FutureTimelineScenario(
            "timeline",
            (
                active_term(
                    campus=CampusAccessKind.UNRESOLVED,
                    catalogue=FutureCatalogueBasisKind.UNRESOLVED,
                ),
            ),
        )
        problem = build_future_planning_problem(
            "unknowns",
            self.single_remainder(),
            timeline,
            FutureOpportunityScenario("opps", (explicit_empty(),)),
        )
        self.assertIn("campus_access_unresolved", problem.blocker_codes)
        self.assertIn("catalogue_basis_unresolved", problem.blocker_codes)

    def test_unresolved_second_major_blocks_exact_future_claim(self):
        scenario = qrm_double_major_shell_2026()
        remainder = degree_remainder(
            spring_2026_initial_state(scenario), scenario
        )
        problem = build_future_planning_problem(
            "dm-unknown",
            remainder,
            FutureTimelineScenario("timeline", (active_term(),)),
            FutureOpportunityScenario("opps", (explicit_empty(),)),
        )
        self.assertTrue(problem.has_structural_degree_unknowns)
        self.assertIn("degree_structure_unresolved", problem.blocker_codes)

    def test_historical_analog_cannot_be_labeled_complete_by_itself(self):
        timeline = FutureTimelineScenario(
            "timeline",
            (
                active_term(
                    catalogue=FutureCatalogueBasisKind.HISTORICAL_ANALOG
                ),
            ),
        )
        problem = build_future_planning_problem(
            "bad-completeness",
            self.single_remainder(),
            timeline,
            FutureOpportunityScenario("opps", (explicit_empty(),)),
        )
        self.assertIn("historical_analog_claimed_complete", problem.blocker_codes)

    def test_leave_term_requires_explicit_empty_opportunity_set(self):
        leave = FutureTermScenario(
            term_id="military",
            activity=TermActivity.LEAVE,
            ordinary_credit_cap=0.0,
            residence=ResidenceState.OTHER,
            campus_access=CampusAccessScenario(CampusAccessKind.UNRESOLVED),
            catalogue_basis=FutureCatalogueBasis(
                FutureCatalogueBasisKind.UNRESOLVED
            ),
        )
        timeline = FutureTimelineScenario("timeline", (leave,))
        partial = FutureOpportunityScenario(
            "opps",
            (
                FutureTermOpportunitySet(
                    term_id="military",
                    status=OpportunitySetStatus.UNRESOLVED,
                ),
            ),
        )
        blocked = build_future_planning_problem(
            "leave-blocked", self.single_remainder(), timeline, partial
        )
        self.assertIn(
            "leave_opportunity_set_not_explicit", blocked.blocker_codes
        )

        exact = build_future_planning_problem(
            "leave-exact",
            self.single_remainder(),
            timeline,
            FutureOpportunityScenario("opps", (explicit_empty("military"),)),
        )
        self.assertTrue(exact.exact_search_ready)

    def test_mismatched_term_sets_are_rejected(self):
        with self.assertRaises(FutureProblemError):
            build_future_planning_problem(
                "mismatch",
                self.single_remainder(),
                FutureTimelineScenario("timeline", (active_term("2027S"),)),
                FutureOpportunityScenario("opps", (explicit_empty("2027F"),)),
            )


if __name__ == "__main__":
    unittest.main()
