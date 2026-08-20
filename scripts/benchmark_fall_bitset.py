#!/usr/bin/env python3
"""Benchmark the exact bitset Stage 4E Fall structural enumerator.

This is still a structural benchmark, not the final optimizer.  Emitted candidates are
intentionally discarded.  The checkpoint is exact and resumable; only an exhausted stack
means structural enumeration is complete.

Example:
    py scripts/benchmark_fall_bitset.py --reset --batches 20
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
from timetable_optimizer.fall_bitset_enumeration import (  # noqa: E402
    FallBitsetCheckpoint,
    FallBitsetEnumerationStatus,
    enumerate_fall_candidate_bitset_batch,
)
from timetable_optimizer.fall_candidate_sets import fall2026_load_policy  # noqa: E402
from timetable_optimizer.fall_universe import (  # noqa: E402
    FallUniverseStatus,
    build_fall_section_universe,
)


def _load_checkpoint(path: Path) -> FallBitsetCheckpoint | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return FallBitsetCheckpoint.from_dict(json.load(handle))


def _atomic_save(path: Path, checkpoint: FallBitsetCheckpoint) -> None:
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
        cumulative_extensions = batch.batch_expanded_extensions
        stack_depth = 0
        selected_depth = 0
        root_remaining = 0
    else:
        cumulative_emitted = checkpoint.emitted_candidates
        cumulative_extensions = checkpoint.expanded_extensions
        stack_depth = len(checkpoint.frames)
        selected_depth = max(
            (len(frame.selected_indices) for frame in checkpoint.frames),
            default=0,
        )
        root_remaining = (
            checkpoint.frames[0].remaining_mask.bit_count()
            if checkpoint.frames
            else 0
        )
    return {
        "status": batch.status.value,
        "seconds": round(elapsed, 3),
        "batch_candidates": len(batch.candidates),
        "batch_expanded_extensions": batch.batch_expanded_extensions,
        "candidates_per_second": (
            round(len(batch.candidates) / elapsed, 1) if elapsed > 0 else None
        ),
        "extensions_per_second": (
            round(batch.batch_expanded_extensions / elapsed, 1) if elapsed > 0 else None
        ),
        "cumulative_candidates": cumulative_emitted,
        "cumulative_extensions": cumulative_extensions,
        "checkpoint_stack_depth": stack_depth,
        "current_selected_depth": selected_depth,
        "root_remaining_count": root_remaining,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=ROOT / ".stage4" / "fall_bitset_benchmark.json",
    )
    parser.add_argument("--batches", type=int, default=20)
    parser.add_argument("--candidate-budget", type=int, default=250_000)
    parser.add_argument("--extension-budget", type=int, default=250_000)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    if args.batches <= 0 or args.candidate_budget <= 0 or args.extension_budget <= 0:
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
        "FALL_BITSET_BENCHMARK",
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
        batch = enumerate_fall_candidate_bitset_batch(
            universe,
            fall2026_load_policy(),
            checkpoint=checkpoint,
            max_emitted_candidates=args.candidate_budget,
            max_expanded_extensions=args.extension_budget,
        )
        elapsed = perf_counter() - started
        print(f"batch={batch_number}", _progress(batch, elapsed), flush=True)

        if batch.status is FallBitsetEnumerationStatus.INPUT_BLOCKED:
            return 2
        if batch.status is FallBitsetEnumerationStatus.COMPLETE:
            if args.checkpoint.exists():
                args.checkpoint.unlink()
            print("EXACT BITSET STRUCTURAL ENUMERATION COMPLETE")
            return 0

        assert batch.checkpoint is not None
        _atomic_save(args.checkpoint, batch.checkpoint)
        checkpoint = batch.checkpoint

    print("PAUSED CLEANLY; rerun the same command to resume from", args.checkpoint)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
