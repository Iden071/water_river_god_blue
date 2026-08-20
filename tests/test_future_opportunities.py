import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.future_opportunities import (  # noqa: E402
    FutureOffering,
    FutureOfferingEvidence,
    FutureOfferingEvidenceKind,
    FutureOpportunityError,
    FutureOpportunityScenario,
    FutureTermOpportunitySet,
    OpportunitySetStatus,
)
from timetable_optimizer.sections import parse_schedule  # noqa: E402


class FutureOpportunityTests(unittest.TestCase):
    def historical_offering(self, offering_id="2027S::QRM1001::analog"):
        return FutureOffering(
            offering_id=offering_id,
            term_id="2027S",
            course_code="QRM1001",
            credits=3.0,
            campus="국제",
            schedule=parse_schedule("목4,5,6", "강의실A"),
            evidence=FutureOfferingEvidence(
                kind=FutureOfferingEvidenceKind.HISTORICAL_ANALOG,
                source_id="history:2026S:QRM1001-01-00",
                source_term="2026S",
                source_section_id="QRM1001-01-00",
            ),
        )

    def test_historical_section_is_wrapped_as_scenario_offering_not_reused_identity(self):
        offering = self.historical_offering()
        self.assertTrue(offering.is_historical_analogue)
        self.assertEqual(offering.evidence.source_section_id, "QRM1001-01-00")
        self.assertNotEqual(offering.offering_id, offering.evidence.source_section_id)

    def test_historical_analogue_requires_source_term_and_section(self):
        with self.assertRaises(FutureOpportunityError):
            FutureOfferingEvidence(
                kind=FutureOfferingEvidenceKind.HISTORICAL_ANALOG,
                source_id="bad",
            )

    def test_unresolved_set_is_not_known_empty(self):
        opportunity_set = FutureTermOpportunitySet(
            term_id="2027S",
            status=OpportunitySetStatus.UNRESOLVED,
        )
        self.assertFalse(opportunity_set.known_empty)
        self.assertFalse(opportunity_set.completeness_known)

    def test_unresolved_set_cannot_hide_known_offerings(self):
        with self.assertRaises(FutureOpportunityError):
            FutureTermOpportunitySet(
                term_id="2027S",
                status=OpportunitySetStatus.UNRESOLVED,
                offerings=(self.historical_offering(),),
            )

    def test_partial_set_can_hold_historical_analogues_without_claiming_completeness(self):
        opportunity_set = FutureTermOpportunitySet(
            term_id="2027S",
            status=OpportunitySetStatus.PARTIAL,
            offerings=(self.historical_offering(),),
            source_id="historical sample",
        )
        self.assertFalse(opportunity_set.completeness_known)
        self.assertEqual(len(opportunity_set.offerings_for_course("QRM1001")), 1)

    def test_explicit_scenario_can_be_known_empty_but_requires_assumption_source(self):
        with self.assertRaises(FutureOpportunityError):
            FutureTermOpportunitySet(
                term_id="leave-like-term",
                status=OpportunitySetStatus.EXPLICIT_SCENARIO,
            )

        opportunity_set = FutureTermOpportunitySet(
            term_id="leave-like-term",
            status=OpportunitySetStatus.EXPLICIT_SCENARIO,
            source_id="scenario:no-courses-this-term",
        )
        self.assertTrue(opportunity_set.completeness_known)
        self.assertTrue(opportunity_set.known_empty)

    def test_term_mismatch_and_duplicate_offering_ids_are_rejected(self):
        offering = self.historical_offering()
        with self.assertRaises(FutureOpportunityError):
            FutureTermOpportunitySet(
                term_id="2027F",
                status=OpportunitySetStatus.PARTIAL,
                offerings=(offering,),
            )

        duplicate = self.historical_offering()
        with self.assertRaises(FutureOpportunityError):
            FutureTermOpportunitySet(
                term_id="2027S",
                status=OpportunitySetStatus.PARTIAL,
                offerings=(offering, duplicate),
            )

    def test_scenario_exposes_incomplete_terms_without_turning_them_empty(self):
        scenario = FutureOpportunityScenario(
            scenario_id="future-opportunities",
            terms=(
                FutureTermOpportunitySet(
                    term_id="2027S",
                    status=OpportunitySetStatus.PARTIAL,
                    offerings=(self.historical_offering(),),
                ),
                FutureTermOpportunitySet(
                    term_id="2027F",
                    status=OpportunitySetStatus.UNRESOLVED,
                ),
            ),
        )
        self.assertTrue(scenario.has_incomplete_opportunity_sets)
        self.assertFalse(scenario.term("2027F").known_empty)


if __name__ == "__main__":
    unittest.main()
