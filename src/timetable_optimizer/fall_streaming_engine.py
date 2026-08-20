"""One-batch coordinator for a crash-safe long Stage 4E exact search.

A caller repeatedly invokes :func:`advance_fall_streaming_search`.  Each invocation:

1. fingerprints the structural universe and the full evaluation model;
2. loads the matching checkpoint + compact proof accumulator, or starts fresh;
3. enumerates a bounded exact Fall candidate batch;
4. evaluates every emitted candidate under the one Fall+future objective;
5. atomically commits the new DFS checkpoint and accumulator;
6. returns a proof-aware snapshot.

The function is intentionally batch-oriented.  A CLI/process may stop between calls without
losing committed progress, and a PAUSED snapshot never becomes an optimum claim.
"""

from __future__ import annotations

from dataclasses import dataclass

from .fall_resumable_enumeration import (
    FallEnumerationBatch,
    FallResumableEnumerationStatus,
    enumerate_fall_candidate_batch,
)
from .fall_streaming_search import (
    FallCandidateEvaluationContext,
    FallStreamingAccumulator,
    FallStreamingSearchSnapshot,
    consume_fall_enumeration_batch,
)
from .fall_streaming_state import (
    FallStreamingStateStore,
    PersistedFallStreamingState,
    fall_streaming_evaluation_signature,
    fall_streaming_search_signature,
)
from .fall_universe import FallSectionUniverse
from .verification import VerificationSummary


class FallStreamingEngineError(ValueError):
    """Long-search coordinator received inconsistent inputs."""


@dataclass(frozen=True)
class FallStreamingBatchProgress:
    batch: FallEnumerationBatch | None
    snapshot: FallStreamingSearchSnapshot
    committed_state: PersistedFallStreamingState | None
    already_complete: bool

    @property
    def structural_complete(self) -> bool:
        return self.snapshot.structural_status is FallResumableEnumerationStatus.COMPLETE


def advance_fall_streaming_search(
    universe: FallSectionUniverse,
    context: FallCandidateEvaluationContext,
    store: FallStreamingStateStore,
    *,
    verification: VerificationSummary | None = None,
    max_emitted_candidates: int = 1_000,
    max_extension_checks: int = 1_000_000,
    unresolved_example_limit: int = 5,
) -> FallStreamingBatchProgress:
    """Advance one durable batch of the exact streaming Fall+future search."""

    if max_emitted_candidates <= 0 or max_extension_checks <= 0:
        raise FallStreamingEngineError("streaming batch budgets must be positive")
    if unresolved_example_limit < 0:
        raise FallStreamingEngineError("unresolved_example_limit cannot be negative")

    search_signature = fall_streaming_search_signature(universe, context.load_policy)
    evaluation_signature = fall_streaming_evaluation_signature(
        context,
        verification=verification,
    )
    persisted = store.load(
        expected_search_signature=search_signature,
        expected_evaluation_signature=evaluation_signature,
    )

    if persisted is None:
        accumulator = FallStreamingAccumulator(
            unresolved_example_limit=unresolved_example_limit,
            verification=verification,
        )
        checkpoint = None
        committed_batches = 0
    else:
        accumulator = persisted.accumulator
        checkpoint = persisted.checkpoint
        committed_batches = persisted.committed_batches
        if persisted.structural_status is FallResumableEnumerationStatus.COMPLETE:
            snapshot = accumulator.snapshot(
                structural_status=FallResumableEnumerationStatus.COMPLETE,
                universe=universe,
            )
            return FallStreamingBatchProgress(
                batch=None,
                snapshot=snapshot,
                committed_state=persisted,
                already_complete=True,
            )

    batch = enumerate_fall_candidate_batch(
        universe,
        context.load_policy,
        checkpoint=checkpoint,
        max_emitted_candidates=max_emitted_candidates,
        max_extension_checks=max_extension_checks,
    )
    if batch.status is FallResumableEnumerationStatus.INPUT_BLOCKED:
        snapshot = accumulator.snapshot(
            structural_status=batch.status,
            universe=universe,
        )
        return FallStreamingBatchProgress(
            batch=batch,
            snapshot=snapshot,
            committed_state=None,
            already_complete=False,
        )

    consume_fall_enumeration_batch(accumulator, batch, context)
    committed = store.commit_batch(
        search_signature=search_signature,
        evaluation_signature=evaluation_signature,
        checkpoint=batch.checkpoint,
        accumulator=accumulator,
        structural_status=batch.status,
        previous_committed_batches=committed_batches,
    )
    snapshot = accumulator.snapshot(
        structural_status=batch.status,
        universe=universe,
    )
    return FallStreamingBatchProgress(
        batch=batch,
        snapshot=snapshot,
        committed_state=committed,
        already_complete=False,
    )
