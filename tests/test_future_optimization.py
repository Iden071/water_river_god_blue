import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.degree import DegreeState  # noqa: E402
from timetable_optimizer.degree_remainder import DegreeRemainder  # noqa: E402
from timetable_optimizer.future_optimization import (  # noqa: E402
    FutureUtilityCandidate,
    build_safe_future_utility_frontiers,
)
from timetable_optimizer.future_reachability import (  # noqa: E402
    FutureReachabilityWitness,
    FutureTermWitness,
)
from timetable_optimizer.future_utility import (  # noqa: E402
    FutureTermUtilityAssessment,
    FutureUtilityHistory,
    TemporalUtilityAggregation,
    TemporalUtilityWeight,
    aggregate_future_utility,
)
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


if __name__ == "__main__":
    unittest.main()
