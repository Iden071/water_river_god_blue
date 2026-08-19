import json
import time
import unittest
from pathlib import Path

from timetable_optimizer.catalog import load_catalog_files
from timetable_optimizer.fall_bitset_enumeration import (
    FallBitsetEnumerationStatus,
    enumerate_fall_candidate_bitset_batch,
)
from timetable_optimizer.fall_candidate_sets import fall2026_load_policy
from timetable_optimizer.fall_local_hard_partition import (
    partition_fall_universe_by_local_hard_evidence,
)
from timetable_optimizer.fall_registration_screening import (
    screen_fall_universe_for_freshman_registration,
)
from timetable_optimizer.fall_universe import build_fall_section_universe


ROOT = Path(__file__).resolve().parents[1]


class RealFallResolvedCoreBitsetSmokeTests(unittest.TestCase):
    def test_resolved_core_search_shape_is_visible(self):
        snapshot = load_catalog_files(
            ROOT / "raw_2026F.json",
            program_listings_path=ROOT / "qrm_listings.json",
            listing_program="QRM",
            term="2026F",
        )
        universe = build_fall_section_universe(
            "real-2026F-full-catalog",
            snapshot,
        )
        with (ROOT / "fall2026_seats.json").open(encoding="utf-8") as handle:
            seat_rows = json.load(handle)
        screening = screen_fall_universe_for_freshman_registration(
            universe,
            snapshot,
            seat_rows,
            source_id="fall2026_seats.json",
        )
        partition = partition_fall_universe_by_local_hard_evidence(
            screening.screened_universe,
            registration_assessments=screening.registration_assessment_map,
        )
        core = partition.resolved_core_universe

        started = time.perf_counter()
        batch = enumerate_fall_candidate_bitset_batch(
            core,
            fall2026_load_policy(),
            max_emitted_candidates=500_000,
            max_expanded_extensions=500_000,
        )
        elapsed = time.perf_counter() - started

        self.assertIn(
            batch.status,
            {
                FallBitsetEnumerationStatus.PAUSED,
                FallBitsetEnumerationStatus.COMPLETE,
            },
        )
        if batch.checkpoint is None:
            root_remaining = 0
            depth = 0
        else:
            root_remaining = batch.checkpoint.frames[0].remaining_mask.bit_count()
            depth = max(
                len(frame.selected_indices)
                for frame in batch.checkpoint.frames
            )
        print(
            "REAL_FALL_RESOLVED_CORE_BITSET",
            {
                "core_sections": len(core.included_sections),
                "status": batch.status.value,
                "seconds": round(elapsed, 3),
                "emitted": len(batch.candidates),
                "candidates_per_second": round(len(batch.candidates) / elapsed, 1),
                "root_remaining_count": root_remaining,
                "max_selected_depth": depth,
            },
        )


if __name__ == "__main__":
    unittest.main()
