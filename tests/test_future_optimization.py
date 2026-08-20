import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.course_preferences import ProfessorRatingBook  # noqa: E402
from timetable_optimizer.degree import DegreeState  # noqa: E402
from timetable_optimizer.degree_remainder import DegreeRemainder  # noqa: E402
from timetable_optimizer.future_completion_search import (  # noqa: E402
    FutureCompletionSearchResult,
    FutureCompletionSearchStatus,
)
from timetable_optimizer.future_opportunities import (  # noqa: E402
    FutureOffering,
    FutureOfferingEvidence,
    FutureOfferingEvidenceKind,
    FutureOpportunityScenario,
    FutureTermOpportunitySet,
    OpportunitySetStatus,
)
from timetable_optimizer.future_optimization import (  # noqa: E402
    FutureOptimizationStatus,
    FutureUtilityCandidate,
    assess_future_completion_utility,
    build_safe_future_utility_frontiers,
)
from timetable_optimizer.future_problem import FuturePlanningProblem  # noqa: E402
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
from timetable_optimizer.future_utility import (  # noqa: E402
    FutureTermUtilityAssessment,
    FutureUtilityHistory,
    TemporalUtilityAggregation,
    TemporalUtilityWeight,
    aggregate_future_utility,
)
from timetable_optimizer.preferences import PreferenceProfile  # noqa: E402
from timetable_optimizer.sections import NoListedSchedule  # noqa: E402
from timetable_optimizer.timetable_utility import (  # noqa: E402
    PartialUtilityAssessment,
    UnresolvedUtilityDimension,
)


def complete_timetable():
    return PartialUtilityAssessment(
        contributions=(),
        unresolved=(),
        active_relations=(),
        measured_lower=0.0,
        measured_upper=0.0,
        heuristic_point_delta=0.0,
    )


def term_assessment(term_id, lower, upper, *, unresolved=()):
    return FutureTermUtilityAssessment(
        term_id=term_id,
        offering_ids=(),
        timetable_facts=None,
        timetable_utility=complete_timetable(),
        course_preferences=(),
        course_contributions=(),
        unresolved=tuple(unresolved),
        measured_lower=lower,
        measured_upper=upper,
        heuristic_point_delta=0.0,
        academic_utility_applicable=True,
    )


def candidate(candidate_id, term_values, *, unresolved=False):
    terms = []
    steps = []
    for index, (term_id, lower, upper) in enumerate(term_values):
        missing = ()
        if unresolved and index == len(term_values) - 1:
            missing = (
                UnresolvedUtilityDimension(
                    dimension_id=f"unknown::{candidate_id}",
                    quantity=1.0,
                    reason="test unresolved utility",
                ),
            )
        terms.append(term_assessment(term_id, lower, upper, unresolved=missing))
        steps.append(FutureTermWitness(term_id, (), (f"action:{candidate_id}:{index}",)))

    history = FutureUtilityHistory(tuple(terms))
    aggregation = TemporalUtilityAggregation(
        source_id="user:temporal-policy",
        weights=tuple(TemporalUtilityWeight(term.term_id, 1.0) for term in terms),
    )
    return FutureUtilityCandidate(
        candidate_id=candidate_id,
        witness=FutureReachabilityWitness(
            steps=tuple(steps),
            resulting_state=DegreeState(),
            remainder=DegreeRemainder("test", 0.0, ()),
        ),
        history=history,
        aggregation=aggregation,
        aggregate=aggregate_future_utility(history, aggregation),
    )


def scenario_term(term_id):
    return FutureTermScenario(
        term_id=term_id,
        activity=TermActivity.ACTIVE,
        ordinary_credit_cap=18.0,
        residence=ResidenceState.HOME,
        campus_access=CampusAccessScenario(CampusAccessKind.ANY),
        catalogue_basis=FutureCatalogueBasis(
            FutureCatalogueBasisKind.EXPLICIT_SCENARIO
        ),
    )


def scenario_offering(term_id):
    return FutureOffering(
        offering_id=f"{term_id}:A",
        term_id=term_id,
        course_code="A",
        credits=3.0,
        campus="국제",
        schedule=NoListedSchedule("", ""),
        professor="",
        evidence=FutureOfferingEvidence(
            FutureOfferingEvidenceKind.EXPLICIT_ASSUMPTION,
            source_id=f"scenario:{term_id}:A",
        ),
    )


def planning_problem():
    terms = (scenario_term("2027S"), scenario_term("2027F"))
    offerings = tuple(scenario_offering(term.term_id) for term in terms)
    return FuturePlanningProblem(
        problem_id="utility-status-test",
        degree_remainder=DegreeRemainder("test", 3.0, ()),
        timeline=FutureTimelineScenario("timeline", terms),
        opportunities=FutureOpportunityScenario(
            "opportunities",
            tuple(
                FutureTermOpportunitySet(
                    term_id=offering.term_id,
                    status=OpportunitySetStatus.EXPLICIT_SCENARIO,
                    offerings=(offering,),
                    source_id=f"scenario:{offering.term_id}",
                )
                for offering in offerings
            ),
        ),
        blockers=(),
    )


def witness(*term_ids):
    steps = tuple(
        FutureTermWitness(
            term_id,
            (f"{term_id}:A",),
            (f"action:{term_id}",),
        )
        for term_id in term_ids
    )
    return FutureReachabilityWitness(
        steps=steps,
        resulting_state=DegreeState(),
        remainder=DegreeRemainder("test", 0.0, ()),
    )


def master_aggregation():
    return TemporalUtilityAggregation(
        source_id="user:temporal-policy",
        weights=(
            TemporalUtilityWeight("2027S", 1.0),
            TemporalUtilityWeight("2027F", 1.0),
        ),
    )


class FutureUtilityFrontierTests(unittest.TestCase):
    def test_only_strict_complete_bound_dominance_removes_candidate(self):
        strong = candidate("strong", (("2027S", 5.0, 7.0),))
        weak = candidate("weak", (("2027S", 1.0, 4.0),))
        overlap = candidate("overlap", (("2027S", 6.0, 8.0),))

        (frontier,) = build_safe_future_utility_frontiers(
            (strong, weak, overlap)
        )

        self.assertEqual(
            frontier.strictly_dominated_candidate_ids, frozenset({"weak"})
        )
        self.assertEqual(
            {item.candidate_id for item in frontier.undominated_complete},
            {"strong", "overlap"},
        )
        self.assertIsNone(frontier.unique_proven_best)

    def test_unresolved_candidate_is_never_pruned_by_large_complete_score(self):
        strong = candidate("strong", (("2027S", 100.0, 100.0),))
        unknown = candidate(
            "unknown", (("2027S", -1000.0, -1000.0),), unresolved=True
        )

        (frontier,) = build_safe_future_utility_frontiers((strong, unknown))

        self.assertEqual(
            {item.candidate_id for item in frontier.unresolved_candidates},
            {"unknown"},
        )
        self.assertNotIn("unknown", frontier.strictly_dominated_candidate_ids)
        self.assertIsNone(frontier.unique_proven_best)

    def test_exact_ties_both_remain_on_frontier(self):
        left = candidate("left", (("2027S", 3.0, 3.0),))
        right = candidate("right", (("2027S", 3.0, 3.0),))

        (frontier,) = build_safe_future_utility_frontiers((left, right))

        self.assertFalse(frontier.strictly_dominated_candidate_ids)
        self.assertEqual(len(frontier.undominated_complete), 2)
        self.assertIsNone(frontier.unique_proven_best)

    def test_different_graduation_horizons_form_separate_frontiers(self):
        early = candidate("early", (("2027S", 0.0, 0.0),))
        late = candidate(
            "late",
            (("2027S", 100.0, 100.0), ("2027F", 100.0, 100.0)),
        )

        frontiers = build_safe_future_utility_frontiers((late, early))

        self.assertEqual(len(frontiers), 2)
        self.assertEqual(frontiers[0].term_ids, ("2027S",))
        self.assertEqual(frontiers[1].term_ids, ("2027S", "2027F"))
        self.assertFalse(frontiers[0].strictly_dominated_candidate_ids)
        self.assertFalse(frontiers[1].strictly_dominated_candidate_ids)

    def test_single_complete_candidate_is_proven_best_within_its_horizon(self):
        only = candidate("only", (("2027S", 1.0, 2.0),))
        (frontier,) = build_safe_future_utility_frontiers((only,))
        self.assertEqual(frontier.unique_proven_best.candidate_id, "only")


class FutureOptimizationStatusTests(unittest.TestCase):
    def setUp(self):
        self.problem = planning_problem()
        self.profile = PreferenceProfile("empty")
        self.professors = ProfessorRatingBook(())

    def search(self, status, witnesses):
        return FutureCompletionSearchResult(
            status=status,
            witnesses=tuple(witnesses),
            explored_selections=0,
            explored_bundles=0,
            frontier_sizes=(),
        )

    def test_different_completion_terms_block_global_optimum_claim(self):
        result = assess_future_completion_utility(
            self.search(
                FutureCompletionSearchStatus.COMPLETE,
                (witness("2027S"), witness("2027S", "2027F")),
            ),
            self.problem,
            self.profile,
            self.professors,
            master_aggregation(),
        )

        self.assertEqual(
            result.status, FutureOptimizationStatus.HORIZON_INCOMPARABLE
        )
        self.assertIn(
            "graduation_timing_utility_unresolved", result.blocker_codes
        )
        self.assertEqual(len(result.frontiers), 2)
        self.assertFalse(result.optimum_proven)

    def test_unresolved_future_utility_blocks_optimum_with_one_horizon(self):
        result = assess_future_completion_utility(
            self.search(
                FutureCompletionSearchStatus.COMPLETE,
                (witness("2027S"),),
            ),
            self.problem,
            self.profile,
            self.professors,
            master_aggregation(),
        )

        self.assertEqual(
            result.status, FutureOptimizationStatus.UTILITY_UNRESOLVED
        )
        self.assertIn("future_utility_unresolved", result.blocker_codes)
        self.assertFalse(result.optimum_proven)

    def test_incomplete_search_blocks_optimum_even_with_known_candidate(self):
        result = assess_future_completion_utility(
            self.search(
                FutureCompletionSearchStatus.NODE_LIMIT,
                (witness("2027S"),),
            ),
            self.problem,
            self.profile,
            self.professors,
            master_aggregation(),
        )

        self.assertEqual(result.status, FutureOptimizationStatus.SEARCH_INCOMPLETE)
        self.assertIn(
            "completion_history_search_incomplete", result.blocker_codes
        )
        self.assertFalse(result.optimum_proven)


if __name__ == "__main__":
    unittest.main()
