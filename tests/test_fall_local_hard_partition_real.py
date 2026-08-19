import json
import unittest
from pathlib import Path

from timetable_optimizer.catalog import load_catalog_files
from timetable_optimizer.fall_local_hard_partition import (
    partition_fall_universe_by_local_hard_evidence,
)
from timetable_optimizer.fall_registration_screening import (
    screen_fall_universe_for_freshman_registration,
)
from timetable_optimizer.fall_universe import build_fall_section_universe


ROOT = Path(__file__).resolve().parents[1]


class RealFallLocalHardPartitionTests(unittest.TestCase):
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
        with (ROOT / "fall2026_seats.json").open(encoding="utf-8") as handle:
            seat_rows = json.load(handle)
        cls.screening = screen_fall_universe_for_freshman_registration(
            cls.universe,
            cls.snapshot,
            seat_rows,
            source_id="fall2026_seats.json",
        )
        cls.partition = partition_fall_universe_by_local_hard_evidence(
            cls.screening.screened_universe,
            registration_assessments=cls.screening.registration_assessment_map,
        )

    def test_real_partition_preserves_every_screened_section(self):
        partition = self.partition
        accounted = (
            partition.resolved_core_section_ids
            | partition.unresolved_family_section_ids
            | partition.blocked_family_section_ids
        )
        self.assertEqual(
            accounted,
            self.screening.screened_universe.searchable_section_ids,
        )
        self.assertFalse(
            partition.resolved_core_section_ids
            & partition.unresolved_family_section_ids
        )
        self.assertFalse(
            partition.resolved_core_section_ids
            & partition.blocked_family_section_ids
        )

    def test_registration_unknown_families_remain_visible_not_dropped(self):
        self.assertTrue(
            self.screening.unresolved_section_ids
            <= self.partition.unresolved_family_section_ids
        )
        self.assertTrue(self.partition.global_optimum_blocked_by_local_unknowns)
        self.assertFalse(
            self.partition.resolved_core_universe.eligible_for_global_optimum_claim
        )

    def test_real_partition_audit_counts_are_visible(self):
        issue_counts = {}
        for family in self.partition.unresolved_families:
            for issue in family.issues:
                issue_counts[issue.code] = issue_counts.get(issue.code, 0) + 1
        print(
            "REAL_FALL_LOCAL_HARD_PARTITION",
            {
                "screened_searchable": len(
                    self.screening.screened_universe.included_sections
                ),
                "resolved_core_sections": len(
                    self.partition.resolved_core_universe.included_sections
                ),
                "unresolved_family_sections": len(
                    self.partition.unresolved_families
                ),
                "blocked_family_sections_after_screen": len(
                    self.partition.blocked_families
                ),
                "unresolved_issue_counts": dict(sorted(issue_counts.items())),
            },
        )


if __name__ == "__main__":
    unittest.main()
