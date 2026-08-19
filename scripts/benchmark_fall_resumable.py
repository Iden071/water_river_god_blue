#!/usr/bin/env python3
"""Benchmark the exact Stage 4E Fall structural enumerator on the real catalogue.

This is intentionally NOT the final optimizer.  It discards emitted timetable candidates
and measures only the exact structural traversal (conflict + SPEC credit-cap pruning).
Its checkpoint exists so a long benchmark can be paused/resumed without restarting the DFS.

Example:
    python scripts/benchmark_fall_resumable.py --batches 20

Delete the checkpoint (or pass --reset) to restart from the root.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.catalog import load_catalog_files  # noqa: E402
from timetable_optimizer.fall_candidate_sets import fall2026_load_policy  # noqa: E402
from timetable_optimizer.fall_resumable_enumeration import (  # noqa: E402
    FallEnumerationCheckpoint,
    FallResumableEnumerationStatus,
    enumerate_fall_candidate_batch,
)
from timetable_optimizer.fall_universe import (  # noqa: E402
    FallUniverseStatus,
    build_fall_section_universe,
)


def _load_checkpoint(path: Path) -> FallEnumerationCheckpoint | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    return FallEnumerationCheckpoint.from_dict(raw)


def _atomic_save(path: Path, checkpoint: FallEnumerationCheckpoint) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(checkpoint.to_dict(), handle, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
        handle.flush()
    temporary.replace(path)


def _progress(batch, elapsed: float) -> dict[str, object]:
    checkpoint = batch.checkpoint
    if checkpoint is None:
        cumulative_emitted = len(batch.candidates)
        cumulative_checks = batch.batch_extension_checks
        stack_depth = 0
        root_next_index = None
        selected_depth = 0
    else:
        cumulative_emitted = checkpoint.emitted_candidates
        cumulative_checks = checkpoint.extension_checks
        stack_depth = len(checkpoint.frames)
        root_next_index = checkpoint.frames[0].next_index if checkpoint.frames else None
        selected_depth = max(
            (len(frame.selected_indices) for frame in checkpoint.frames),
            default=0,
        )

    return {
        "status": batch.status.value,
        "seconds": round(elapsed, 3),
        "batch_candidates": len(batch.candidates),
        "batch_extension_checks": batch.batch_extension_checks,
        "checks_per_second": (
            round(batch.batch_extension_checks / elapsed, 1) if elapsed > 0 else None
        ),
        "candidates_per_second": (
            round(len(batch.candidates) / elapsed, 1) if elapsed > 0 else None
        ),
        "batch_conflict_prunes": batch.batch_pruned_by_conflict,
        "batch_credit_prunes": batch.batch_pruned_by_credit_cap,
        "cumulative_candidates": cumulative_emitted,
        "cumulative_extension_checks": cumulative_checks,
        "checkpoint_stack_depth": stack_depth,
        "current_selected_depth": selected_depth,
        "root_next_index": root_next_index,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=ROOT / ".stage4" / "fall_resumable_benchmark.json",
        help="JSON checkpoint path (default: .stage4/fall_resumable_benchmark.json)",
    )
    parser.add_argument("--batches", type=int, default=10)
    parser.add_argument("--candidate-budget", type=int, default=100_000)
    parser.add_argument("--check-budget", type=int, default=5_000_000)
    parser.add_argument(
        "--reset",
        action="store_true",
        help="discard the existing benchmark checkpoint before starting",
    )
    args = parser.parse_args()

    if args.batches <= 0 or args.candidate_budget <= 0 or args.check_budget <= 0:
        parser.error("all numeric budgets must be positive")

    if args.reset and args.checkpoint.exists():
        args.checkpoint.unlink()

    snapshot = load_catalog_files(
        ROOT / "raw_2026F.json",
        program_listings_path=ROOT / "qrm_listings.json",
        listing_program="QRM",
        term="2026F",
    )
    universe = build_fall_section_universe("real-2026F-full-catalog", snapshot)
    if universe.status is not FallUniverseStatus.GLOBAL_COMPLETE:
        print(
            "Cannot benchmark exact full-catalogue traversal:",
            universe.status.value,
            file=sys.stderr,
        )
        return 2

    checkpoint = _load_checkpoint(args.checkpoint)
    print(
        "FALL_RESUMABLE_BENCHMARK",
        {
            "searchable_sections": len(universe.included_sections),
            "ordinary_credit_cap": fall2026_load_policy().ordinary_credit_cap,
            "checkpoint": str(args.checkpoint),
            "resuming": checkpoint is not None,
            "note": "benchmark only; emitted candidates are intentionally discarded",
        },
    )

    for batch_number in range(1, args.batches + 1):
        started = perf_counter()
        batch = enumerate_fall_candidate_batch(
            universe,
            fall2026_load_policy(),
            checkpoint=checkpoint,
            max_emitted_candidates=args.candidate_budget,
            max_extension_checks=args.check_budget,
        )
        elapsed = perf_counter() - started
        print(f"batch={batch_number}", _progress(batch, elapsed), flush=True)

        if batch.status is FallResumableEnumerationStatus.INPUT_BLOCKED:
            return 2
        if batch.status is FallResumableEnumerationStatus.COMPLETE:
            if args.checkpoint.exists():
                args.checkpoint.unlink()
            print("EXACT STRUCTURAL ENUMERATION COMPLETE")
            return 0

        assert batch.checkpoint is not None
        _atomic_save(args.checkpoint, batch.checkpoint)
        checkpoint = batch.checkpoint

    print(
        "PAUSED CLEANLY; rerun the same command to resume from",
        args.checkpoint,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
