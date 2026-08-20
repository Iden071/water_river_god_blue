import sys
import unittest
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.catalog import load_catalog_files  # noqa: E402
from timetable_optimizer.fall_bitset_enumeration import (  # noqa: E402
    FallBitsetEnumerationStatus,
    enumerate_fall_candidate_bitset_batch,
)
from timetable_optimizer.fall_candidate_sets import fall2026_load_policy  # noqa: E402
from timetable_optimizer.fall_universe import (  # noqa: E402
    FallUniverseStatus,
    build_fall_section_universe,
)
from timetable_optimizer.recognition import CHAPEL_2026_CODES  # noqa: E402


class RealFallBitsetSmokeTests(unittest.TestCase):
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

    def test_real_bitset_batch_is_exactly_resumable_and_reports_credit_shape(self):
        if self.universe.status is not FallUniverseStatus.GLOBAL_COMPLETE:
            batch = enumerate_fall_candidate_bitset_batch(
                self.universe,
                fall2026_load_policy(),
                max_emitted_candidates=10,
                max_expanded_extensions=10,
            )
            self.assertEqual(batch.status, FallBitsetEnumerationStatus.INPUT_BLOCKED)
            return

        unknown_credit = sum(
            section.credits is None for section in self.universe.included_sections
        )
        zero_known_ordinary = sum(
            section.credits is not None
            and (
                float(section.credits) == 0.0
                or section.course_code in CHAPEL_2026_CODES
            )
            for section in self.universe.included_sections
        )
        positive_known_ordinary = (
            len(self.universe.included_sections) - unknown_credit - zero_known_ordinary
        )

        started = perf_counter()
        batch = enumerate_fall_candidate_bitset_batch(
            self.universe,
            fall2026_load_policy(),
            max_emitted_candidates=100_000,
            max_expanded_extensions=100_000,
        )
        elapsed = perf_counter() - started

        self.assertIn(
            batch.status,
            {FallBitsetEnumerationStatus.PAUSED, FallBitsetEnumerationStatus.COMPLETE},
        )
        self.assertEqual(
            len({candidate.section_ids for candidate in batch.candidates}),
            len(batch.candidates),
        )
        if batch.status is FallBitsetEnumerationStatus.PAUSED:
            self.assertIsNotNone(batch.checkpoint)

        checkpoint = batch.checkpoint
        print(
            "REAL_FALL_BITSET",
            {
                "searchable_sections": len(self.universe.included_sections),
                "unknown_credit_sections": unknown_credit,
                "zero_known_ordinary_sections": zero_known_ordinary,
                "positive_known_ordinary_sections": positive_known_ordinary,
                "status": batch.status.value,
                "seconds": round(elapsed, 3),
                "emitted": len(batch.candidates),
                "expanded_extensions": batch.batch_expanded_extensions,
                "candidates_per_second": (
                    round(len(batch.candidates) / elapsed, 1) if elapsed > 0 else None
                ),
                "checkpoint_depth": (
                    len(checkpoint.frames) if checkpoint is not None else 0
                ),
                "max_selected_depth": (
                    max(
                        (len(frame.selected_indices) for frame in checkpoint.frames),
                        default=0,
                    )
                    if checkpoint is not None
                    else 0
                ),
                "root_remaining_count": (
                    checkpoint.frames[0].remaining_mask.bit_count()
                    if checkpoint is not None and checkpoint.frames
                    else 0
                ),
            },
        )


if __name__ == "__main__":
    unittest.main()
