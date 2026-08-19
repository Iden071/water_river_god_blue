import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.course_preferences import ProfessorRatingBook  # noqa: E402
from timetable_optimizer.degree_remainder import DegreeRemainder  # noqa: E402
from timetable_optimizer.future_bounds import (  # noqa: E402
    FutureBoundStatus,
    FuturePruningStatus,
    compare_continuation_bound_to_incumbent,
    derive_future_continuation_utility_bound,
    derive_relaxed_term_utility_envelope,
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
from timetable_optimizer.future_utility import (  # noqa: E402
    FutureTermUtilityAssessment,
    FutureUtilityHistory,
    TemporalUtilityAggregation,
    TemporalUtilityWeight,
    assess_future_term_utility,
)
from timetable_optimizer.preferences import (  # noqa: E402
    PreferenceEstimate,
    PreferenceProfile,
    PreferenceProvenance,
    PreferenceSourceKind,
    PreferenceValue,
)
from timetable_optimizer.sections import NoListedSchedule  # noqa: E402
from timetable_optimizer.timetable_utility import (  # noqa: E402
    PartialUtilityAssessment,
    UnresolvedUtilityDimension,
)


def provenance(name):
    return PreferenceProvenance(PreferenceSourceKind.USER_INPUT, f"test:{name}")


def exact_value(dimension_id, value):
    return PreferenceValue(
        dimension_id,
        PreferenceEstimate.exact(value),
        provenance=provenance(dimension_id),
    )


def complete_free_profile():
    # An empty active timetable activates exactly these four dimensions.  Their values
    # produce utility 5*1 + 1*2 + 4*0 + 1*3 = 10.
    return PreferenceProfile(
        "complete-free-profile",
        values=(
            exact_value("rest_fixed_free_weekday", 1.0),
            exact_value("weekend_attached_presence_free_day", 2.0),
            exact_value("weekend_run_curvature", 0.0),
            exact_value("friday_event_window_free", 3.0),
        ),
    )


def active_term(term_id):
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


def explicit_set(term_id, offerings=()):
    return FutureTermOpportunitySet(
        term_id=term_id,
        status=OpportunitySetStatus.EXPLICIT_SCENARIO,
        offerings=tuple(offerings),
        source_id=f"scenario:{term_id}",
    )


def unresolved_offering(term_id, suffix="A"):
    return FutureOffering(
        offering_id=f"{term_id}:{suffix}",
        term_id=term_id,
        course_code=f"COURSE{suffix}",
        credits=3.0,
        campus="국제",
        schedule=NoListedSchedule("", ""),
        professor=None,
        evidence=FutureOfferingEvidence(
            FutureOfferingEvidenceKind.EXPLICIT_ASSUMPTION,
            source_id=f"scenario:{term_id}:{suffix}",
        ),
    )


def problem(terms, opportunity_sets):
    return build_future_planning_problem(
        "bounds-test",
        DegreeRemainder("test", 3.0, ()),
        FutureTimelineScenario("timeline", tuple(terms)),
        FutureOpportunityScenario("opportunities", tuple(opportunity_sets)),
    )


def temporal(*weights):
    return TemporalUtilityAggregation(
        source_id="user:temporal-policy",
        weights=tuple(TemporalUtilityWeight(term_id, weight) for term_id, weight in weights),
    )


def complete_partial_utility():
    return PartialUtilityAssessment(
        contributions=(),
        unresolved=(),
        active_relations=(),
        measured_lower=0.0,
        measured_upper=0.0,
        heuristic_point_delta=0.0,
    )


def synthetic_term(term_id, value, *, unresolved=False):
    missing = ()
    if unresolved:
        missing = (
            UnresolvedUtilityDimension(
                dimension_id=f"unknown::{term_id}",
                quantity=1.0,
                reason="test unresolved utility",
            ),
        )
    return FutureTermUtilityAssessment(
        term_id=term_id,
        offering_ids=(),
        timetable_facts=None,
        timetable_utility=complete_partial_utility(),
        course_preferences=(),
        course_contributions=(),
        unresolved=missing,
        measured_lower=value,
        measured_upper=value,
        heuristic_point_delta=0.0,
        academic_utility_applicable=True,
    )


class FutureTermEnvelopeTests(unittest.TestCase):
    def setUp(self):
        self.profile = complete_free_profile()
        self.professors = ProfessorRatingBook(())

    def test_empty_explicit_active_term_has_exact_relaxed_envelope(self):
        term = active_term("2027S")
        result = derive_relaxed_term_utility_envelope(
            term,
            explicit_set("2027S"),
            self.profile,
            self.professors,
        )
        self.assertEqual(result.status, FutureBoundStatus.AVAILABLE)
        self.assertEqual(result.envelope.lower_bound, 10.0)
        self.assertEqual(result.envelope.upper_bound, 10.0)
        self.assertEqual(result.evaluated_subsets, 1)
        self.assertEqual(result.total_subsets, 1)

    def test_incomplete_opportunity_universe_has_no_bound(self):
        term = active_term("2027S")
        partial = FutureTermOpportunitySet(
            "2027S", OpportunitySetStatus.PARTIAL, offerings=()
        )
        result = derive_relaxed_term_utility_envelope(
            term, partial, self.profile, self.professors
        )
        self.assertEqual(result.status, FutureBoundStatus.INPUT_BLOCKED)
        self.assertIsNone(result.envelope)

    def test_any_unresolved_selection_blocks_whole_term_envelope(self):
        term = active_term("2027S")
        result = derive_relaxed_term_utility_envelope(
            term,
            explicit_set("2027S", (unresolved_offering("2027S"),)),
            self.profile,
            self.professors,
        )
        self.assertEqual(result.status, FutureBoundStatus.UTILITY_UNRESOLVED)
        self.assertIsNone(result.envelope)
        self.assertIn("term_utility_incomplete", result.blocker_codes)
        self.assertEqual(result.evaluated_subsets, 2)

    def test_subset_limit_never_returns_partial_max_as_a_bound(self):
        term = active_term("2027S")
        result = derive_relaxed_term_utility_envelope(
            term,
            explicit_set(
                "2027S",
                (
                    unresolved_offering("2027S", "A"),
                    unresolved_offering("2027S", "B"),
                ),
            ),
            self.profile,
            self.professors,
            max_subset_evaluations=3,
        )
        self.assertEqual(result.status, FutureBoundStatus.EVALUATION_LIMIT)
        self.assertIsNone(result.envelope)
        self.assertEqual(result.total_subsets, 4)
        self.assertEqual(result.evaluated_subsets, 0)


class FutureContinuationBoundTests(unittest.TestCase):
    def setUp(self):
        self.profile = complete_free_profile()
        self.professors = ProfessorRatingBook(())

    def test_prefix_plus_remaining_term_uses_same_temporal_objective(self):
        first = active_term("2027S")
        second = active_term("2027F")
        planning = problem(
            (first, second),
            (explicit_set("2027S"), explicit_set("2027F")),
        )
        first_assessment = assess_future_term_utility(
            first, (), self.profile, self.professors
        )
        prefix = FutureUtilityHistory((first_assessment,))

        bound = derive_future_continuation_utility_bound(
            planning,
            prefix,
            ("2027S", "2027F"),
            temporal(("2027S", 1.0), ("2027F", 0.5)),
            self.profile,
            self.professors,
        )

        self.assertTrue(bound.available)
        self.assertEqual((bound.lower_bound, bound.upper_bound), (15.0, 15.0))
        self.assertEqual(len(bound.term_envelopes), 1)
        self.assertEqual(bound.term_envelopes[0].term_id, "2027F")

    def test_zero_weight_unresolved_term_does_not_block_objective_bound(self):
        first = active_term("2027S")
        ignored = active_term("2027F")
        planning = problem(
            (first, ignored),
            (
                explicit_set("2027S"),
                explicit_set("2027F", (unresolved_offering("2027F"),)),
            ),
        )
        bound = derive_future_continuation_utility_bound(
            planning,
            FutureUtilityHistory(()),
            ("2027S", "2027F"),
            temporal(("2027S", 1.0), ("2027F", 0.0)),
            self.profile,
            self.professors,
        )
        self.assertTrue(bound.available)
        self.assertEqual((bound.lower_bound, bound.upper_bound), (10.0, 10.0))
        self.assertEqual(tuple(item.term_id for item in bound.term_envelopes), ("2027S",))

    def test_unresolved_prefix_blocks_bound(self):
        term = active_term("2027S")
        planning = problem((term,), (explicit_set("2027S"),))
        prefix = FutureUtilityHistory((synthetic_term("2027S", 10.0, unresolved=True),))
        bound = derive_future_continuation_utility_bound(
            planning,
            prefix,
            ("2027S",),
            temporal(("2027S", 1.0)),
            self.profile,
            self.professors,
        )
        self.assertEqual(bound.status, FutureBoundStatus.UTILITY_UNRESOLVED)
        self.assertIsNone(bound.upper_bound)
        self.assertIn("prefix_utility_incomplete", bound.blocker_codes)

    def test_strict_incumbent_lower_bound_can_prune_relaxed_upper_bound(self):
        term = active_term("2027S")
        planning = problem((term,), (explicit_set("2027S"),))
        policy = temporal(("2027S", 1.0))
        bound = derive_future_continuation_utility_bound(
            planning,
            FutureUtilityHistory(()),
            ("2027S",),
            policy,
            self.profile,
            self.professors,
        )
        incumbent = FutureUtilityHistory((synthetic_term("2027S", 11.0),))
        decision = compare_continuation_bound_to_incumbent(bound, incumbent, policy)
        self.assertEqual(decision.status, FuturePruningStatus.PRUNE_PROVEN)
        self.assertTrue(decision.prune)

    def test_equal_incumbent_and_upper_bound_does_not_prune(self):
        term = active_term("2027S")
        planning = problem((term,), (explicit_set("2027S"),))
        policy = temporal(("2027S", 1.0))
        bound = derive_future_continuation_utility_bound(
            planning,
            FutureUtilityHistory(()),
            ("2027S",),
            policy,
            self.profile,
            self.professors,
        )
        incumbent = FutureUtilityHistory((synthetic_term("2027S", 10.0),))
        decision = compare_continuation_bound_to_incumbent(bound, incumbent, policy)
        self.assertEqual(decision.status, FuturePruningStatus.KEEP_NOT_DOMINATED)
        self.assertFalse(decision.prune)


if __name__ == "__main__":
    unittest.main()
