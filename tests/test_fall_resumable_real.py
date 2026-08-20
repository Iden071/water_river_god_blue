import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.catalog import load_catalog_files  # noqa: E402
from timetable_optimizer.fall_candidate_sets import fall2026_load_policy  # noqa: E402
from timetable_optimizer.fall_resumable_enumeration import (  # noqa: E402
    FallResumableEnumerationStatus,
    enumerate_fall_candidate_batch,
)
from timetable_optimizer.fall_universe import (  # noqa: E402
    FallUniverseStatus,
    build_fall_section_universe,
)


class RealFallResumableEnumerationSmokeTests(unittest.TestCase):
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

    def test_bounded_real_batch_is_exactly_resumable_not_fake_complete(self):
        max_candidates = 10_000
        max_checks = 1_000_000
        if self.universe.status is not FallUniverseStatus.GLOBAL_COMPLETE:
            batch = enumerate_fall_candidate_batch(
                self.universe,
                fall2026_load_policy(),
                max_emitted_candidates=max_candidates,
                max_extension_checks=max_checks,
            )
            self.assertEqual(
                batch.status,
                FallResumableEnumerationStatus.INPUT_BLOCKED,
            )
            return

        batch = enumerate_fall_candidate_batch(
            self.universe,
            fall2026_load_policy(),
            max_emitted_candidates=max_candidates,
            max_extension_checks=max_checks,
        )
        self.assertEqual(batch.status, FallResumableEnumerationStatus.PAUSED)
        self.assertIsNotNone(batch.checkpoint)
        self.assertGreater(len(batch.candidates), 0)
        self.assertLessEqual(len(batch.candidates), max_candidates)
        self.assertLessEqual(batch.batch_extension_checks, max_checks)
        # At least one explicit work budget must explain why this exact search paused.
        self.assertTrue(
            len(batch.candidates) == max_candidates
            or batch.batch_extension_checks == max_checks
        )
        candidate_ids = [candidate.section_ids for candidate in batch.candidates]
        self.assertEqual(len(candidate_ids), len(set(candidate_ids)))

        checkpoint = batch.checkpoint
        assert checkpoint is not None
        max_selected = max(
            (len(frame.selected_indices) for frame in checkpoint.frames),
            default=0,
        )
        print(
            "REAL_FALL_RESUMABLE",
            {
                "searchable_sections": len(self.universe.included_sections),
                "emitted": len(batch.candidates),
                "extension_checks": batch.batch_extension_checks,
                "conflict_prunes": batch.batch_pruned_by_conflict,
                "credit_prunes": batch.batch_pruned_by_credit_cap,
                "checkpoint_depth": len(checkpoint.frames),
                "max_selected_in_checkpoint": max_selected,
                "cumulative_emitted": checkpoint.emitted_candidates,
                "cumulative_checks": checkpoint.extension_checks,
            },
        )


if __name__ == "__main__":
    unittest.main()
