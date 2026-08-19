import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.catalog import load_catalog_files  # noqa: E402
from timetable_optimizer.fall_registration_screening import (  # noqa: E402
    screen_fall_universe_for_freshman_registration,
)
from timetable_optimizer.fall_universe import build_fall_section_universe  # noqa: E402
from timetable_optimizer.registration import YearQuotaGateStatus  # noqa: E402


class RealFallRegistrationScreeningAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = load_catalog_files(
            ROOT / "raw_2026F.json",
            program_listings_path=ROOT / "qrm_listings.json",
            listing_program="QRM",
            term="2026F",
        )
        cls.universe = build_fall_section_universe(
            "real-2026F-full-catalog",
            cls.snapshot,
        )
        with (ROOT / "fall2026_seats.json").open(encoding="utf-8") as fh:
            cls.seat_rows = json.load(fh)
        cls.screening = screen_fall_universe_for_freshman_registration(
            cls.universe,
            cls.snapshot,
            cls.seat_rows,
            source_id="fall2026_seats.json",
        )

    def test_every_safe_registration_exclusion_is_an_observed_block(self):
        assessments = self.screening.registration_assessment_map
        for exclusion in self.screening.new_hard_exclusions:
            assessment = assessments[exclusion.section_id]
            self.assertEqual(
                assessment.year_quota_status,
                YearQuotaGateStatus.FRESHMAN_BLOCKED_BY_SCHEME,
            )
            self.assertNotIn(
                exclusion.section_id,
                self.screening.screened_universe.searchable_section_ids,
            )

    def test_screening_never_drops_unresolved_gate_evidence(self):
        searchable = self.screening.screened_universe.searchable_section_ids
        self.assertTrue(self.screening.unresolved_section_ids <= searchable)
        self.assertEqual(
            len(searchable),
            len(self.universe.searchable_section_ids)
            - len(self.screening.new_hard_exclusions),
        )

    def test_real_screening_audit_counts_are_visible(self):
        statuses = {
            status: 0
            for status in YearQuotaGateStatus
        }
        for assessment in self.screening.assessments:
            statuses[assessment.year_quota_status] += 1

        print(
            "REAL_FALL_REGISTRATION_SCREENING",
            {
                "seat_rows": len(self.seat_rows),
                "original_searchable": len(self.universe.searchable_section_ids),
                "screened_searchable": len(self.screening.screened_universe.searchable_section_ids),
                "freshman_gate_exclusions": len(self.screening.new_hard_exclusions),
                "resolved_nonblocking": len(self.screening.resolved_nonblocking_section_ids),
                "unresolved_gate_sections": len(self.screening.unresolved_section_ids),
                "invalid_evidence_issues": len(self.screening.issues),
                "no_observation": statuses[YearQuotaGateStatus.NO_OBSERVATION],
                "no_year_scheme": statuses[YearQuotaGateStatus.NO_YEAR_SCHEME],
                "freshman_allowed": statuses[YearQuotaGateStatus.FRESHMAN_ALLOWED_BY_SCHEME],
                "freshman_blocked": statuses[YearQuotaGateStatus.FRESHMAN_BLOCKED_BY_SCHEME],
            },
        )


if __name__ == "__main__":
    unittest.main()
