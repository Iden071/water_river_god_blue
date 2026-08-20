import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.future_scenarios import (  # noqa: E402
    CampusAccessKind,
    CampusAccessScenario,
    FutureCatalogueBasis,
    FutureCatalogueBasisKind,
    FutureScenarioError,
    FutureTermScenario,
    FutureTimelineScenario,
    ResidenceState,
    TermActivity,
)


class FutureScenarioTests(unittest.TestCase):
    def active_term(self, **overrides):
        kwargs = dict(
            term_id="2027S",
            activity=TermActivity.ACTIVE,
            ordinary_credit_cap=18.0,
            residence=ResidenceState.HOME,
            campus_access=CampusAccessScenario(CampusAccessKind.ANY),
            catalogue_basis=FutureCatalogueBasis(
                FutureCatalogueBasisKind.UNRESOLVED
            ),
        )
        kwargs.update(overrides)
        return FutureTermScenario(**kwargs)

    def test_credit_capacity_replaces_course_slot_count(self):
        term = self.active_term(ordinary_credit_cap=22.0)
        self.assertEqual(term.ordinary_credit_cap, 22.0)
        self.assertFalse(hasattr(term, "course_slots"))
        self.assertFalse(hasattr(term, "courses_per_term"))
        self.assertFalse(hasattr(term, "six_slots"))

    def test_any_campus_explicitly_permits_mixed_campus_planning(self):
        access = CampusAccessScenario(CampusAccessKind.ANY)
        self.assertTrue(access.allows("국제"))
        self.assertTrue(access.allows("신촌"))

    def test_restricted_and_unresolved_campus_access_are_distinct(self):
        restricted = CampusAccessScenario(
            CampusAccessKind.RESTRICTED, frozenset({"국제"})
        )
        unresolved = CampusAccessScenario(CampusAccessKind.UNRESOLVED)

        self.assertTrue(restricted.allows("국제"))
        self.assertFalse(restricted.allows("신촌"))
        self.assertIsNone(unresolved.allows("신촌"))

    def test_historical_analog_requires_named_source_terms(self):
        with self.assertRaises(FutureScenarioError):
            FutureCatalogueBasis(FutureCatalogueBasisKind.HISTORICAL_ANALOG)

        basis = FutureCatalogueBasis(
            FutureCatalogueBasisKind.HISTORICAL_ANALOG,
            source_terms=("2025S", "2026S"),
        )
        self.assertEqual(basis.source_terms, ("2025S", "2026S"))

    def test_unresolved_catalogue_is_not_an_empty_exact_catalogue(self):
        basis = FutureCatalogueBasis(FutureCatalogueBasisKind.UNRESOLVED)
        self.assertEqual(basis.kind, FutureCatalogueBasisKind.UNRESOLVED)
        self.assertFalse(hasattr(basis, "available_course_codes"))

    def test_leave_term_has_zero_credit_capacity(self):
        leave = FutureTermScenario(
            term_id="military-1",
            activity=TermActivity.LEAVE,
            ordinary_credit_cap=0.0,
            residence=ResidenceState.OTHER,
            campus_access=CampusAccessScenario(CampusAccessKind.UNRESOLVED),
            catalogue_basis=FutureCatalogueBasis(
                FutureCatalogueBasisKind.UNRESOLVED
            ),
        )
        self.assertFalse(leave.can_host_academic_credits)

        with self.assertRaises(FutureScenarioError):
            FutureTermScenario(
                term_id="bad-leave",
                activity=TermActivity.LEAVE,
                ordinary_credit_cap=3.0,
                residence=ResidenceState.OTHER,
                campus_access=CampusAccessScenario(CampusAccessKind.UNRESOLVED),
                catalogue_basis=FutureCatalogueBasis(
                    FutureCatalogueBasisKind.UNRESOLVED
                ),
            )

    def test_timeline_is_finite_ordered_and_does_not_force_capacity_use(self):
        first = self.active_term(term_id="2027S", ordinary_credit_cap=18.0)
        second = self.active_term(term_id="2027F", ordinary_credit_cap=22.0)
        timeline = FutureTimelineScenario(
            scenario_id="example",
            terms=(first, second),
        )

        self.assertEqual([term.term_id for term in timeline.terms], ["2027S", "2027F"])
        self.assertEqual(timeline.ordinary_credit_capacity, 40.0)
        self.assertTrue(timeline.has_unresolved_catalogue)
        self.assertFalse(hasattr(timeline, "minimum_courses_per_term"))

    def test_duplicate_term_ids_are_rejected(self):
        first = self.active_term(term_id="2027S")
        second = self.active_term(term_id="2027S")
        with self.assertRaises(FutureScenarioError):
            FutureTimelineScenario("duplicate", (first, second))


if __name__ == "__main__":
    unittest.main()
