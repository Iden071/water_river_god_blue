import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.catalog import PhysicalStatus, load_catalog_files  # noqa: E402
from timetable_optimizer.fall_candidate_sets import (  # noqa: E402
    FallCandidateSetEnumerationStatus,
    enumerate_fall_candidate_sets,
    fall2026_load_policy,
)
from timetable_optimizer.fall_universe import (  # noqa: E402
    FallUniverseStatus,
    build_fall_section_universe,
)


class RealFallUniverseAuditTests(unittest.TestCase):
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

    def test_every_known_physical_id_is_accounted_for(self):
        searchable = set(self.universe.searchable_section_ids)
        excluded = {item.section_id for item in self.universe.hard_exclusions}
        unresolved = {
            record.section_id
            for record in self.snapshot.physical_sections
            if record.status is PhysicalStatus.UNRESOLVED
        }

        self.assertFalse(searchable & excluded)
        self.assertFalse(searchable & unresolved)
        self.assertFalse(excluded & unresolved)
        self.assertEqual(
            searchable | excluded | unresolved,
            set(self.universe.known_physical_section_ids),
        )

    def test_real_full_catalog_smoke_never_turns_limit_into_optimum(self):
        generated = enumerate_fall_candidate_sets(
            self.universe,
            fall2026_load_policy(),
            max_subset_evaluations=1_000,
        )

        if self.universe.status is FallUniverseStatus.GLOBAL_COMPLETE:
            self.assertEqual(
                generated.status,
                FallCandidateSetEnumerationStatus.TRUNCATED,
            )
            self.assertEqual(generated.evaluated_subsets, 1_000)
            self.assertFalse(generated.global_search_space_complete)
        else:
            self.assertEqual(
                generated.status,
                FallCandidateSetEnumerationStatus.INPUT_BLOCKED,
            )
            self.assertEqual(generated.evaluated_subsets, 0)

        print(
            "REAL_FALL_UNIVERSE",
            {
                "status": self.universe.status.value,
                "source_observations": len(self.snapshot.observations),
                "physical_sections": len(self.snapshot.physical_sections),
                "searchable_sections": len(self.universe.included_sections),
                "hard_exclusions": len(self.universe.hard_exclusions),
                "global_unknowns": len(self.universe.global_catalogue_unknowns),
                "smoke_status": generated.status.value,
                "smoke_evaluated_subsets": generated.evaluated_subsets,
                "conflict_prunes": generated.pruned_include_branches_by_conflict,
                "credit_prunes": generated.pruned_include_branches_by_credit_cap,
            },
        )


if __name__ == "__main__":
    unittest.main()
