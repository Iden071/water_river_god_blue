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
from timetable_optimizer.fall_shape_batch_audit import audit_candidate_shape_batch
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

        # Reuse a *small slice* of the exact candidates already generated above: no second
        # search benchmark and no permanent 500k-candidate utility-analysis tax on every CI
        # run.  A one-time 500k diagnostic was recorded separately in the Stage-4 diagnostic
        # checkpoint; this recurring smoke only guards the exposure-audit code path.
        #
        # The 12-credit floor is a diagnostic lens only, not a hard model constraint.  The
        # DFS prefix is explicitly non-representative, so counts below prove only that a shape
        # occurs in the exact family, not how common it is globally or whether it is optimal.
        diagnostic_prefix = batch.candidates[:50_000]
        sensitivity = audit_candidate_shape_batch(
            diagnostic_prefix,
            minimum_known_ordinary_credits=12.0,
        )
        self.assertFalse(sensitivity.representative)
        self.assertFalse(sensitivity.proof_evidence)
        self.assertGreater(sensitivity.candidates_evaluated, 0)
        self.assertFalse(sensitivity.uncovered_archival_state_dimensions)
        self.assertGreater(sensitivity.distinct_unresolved_shape_signatures, 0)

        common_signatures = []
        for signature, count in sensitivity.most_common_unresolved_shape_signatures:
            common_signatures.append(
                {
                    "count": count,
                    "friday_free": signature.friday_event_window_free,
                    "weekend_attached_days": signature.weekend_attached_presence_free_days,
                    "three_runs": signature.three_fixed_period_run_count,
                    "long_runs": signature.long_fixed_run_counts,
                }
            )

        print(
            "REAL_FALL_SHAPE_SENSITIVITY_PREFIX",
            {
                "warning": "exact DFS prefix; diagnostic only; not representative and not proof evidence",
                "candidate_prefix_seen": sensitivity.candidates_seen,
                "credit_floor_diagnostic_only": sensitivity.minimum_known_ordinary_credits,
                "evaluated_after_floor": sensitivity.candidates_evaluated,
                "below_floor": sensitivity.candidates_below_credit_floor,
                "skipped_unresolved_schedule": sensitivity.candidates_skipped_unresolved_schedule,
                "family_activation_counts": dict(sensitivity.family_activation_counts),
                "active_state_counts": dict(sensitivity.state_activation_counts),
                "distinct_unresolved_shape_signatures": sensitivity.distinct_unresolved_shape_signatures,
                "most_common_unresolved_shape_signatures": common_signatures,
                "maximum_archival_scenario_spread": round(
                    sensitivity.maximum_archival_spread, 3
                ),
                "max_spread_example_section_ids": sensitivity.maximum_spread_section_ids,
            },
        )


if __name__ == "__main__":
    unittest.main()
