"""Crash-safe persistence for a long Stage 4E streaming Fall search.

The structural DFS checkpoint and the compact whole-plan accumulator are one logical state.
Advancing only one of them would make a resumed run either skip evaluated candidates or
evaluate them twice.  This module stores both in one SQLite transaction.

Two signatures are required:

* ``search_signature`` binds the DFS to the exact Fall universe and load policy;
* ``evaluation_signature`` binds accumulated whole-plan results to every model/objective
  input that can change their meaning.

The accumulator payload uses Python pickle because it contains nested immutable Stage 4
objects and is intended only for a local, same-code search process.  Never open a database
from an untrusted source: pickle is not a safe interchange format.  The structural checkpoint
itself remains portable JSON.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import pickle
import sqlite3

from .fall_candidate_sets import FallLoadPolicy
from .fall_resumable_enumeration import (
    FallEnumerationCheckpoint,
    FallResumableEnumerationStatus,
    _ordered_sections,
    _search_signature,
)
from .fall_streaming_search import (
    FallCandidateEvaluationContext,
    FallStreamingAccumulator,
)
from .fall_universe import FallSectionUniverse
from .model_fingerprint import model_fingerprint
from .verification import VerificationSummary


class FallStreamingStateError(ValueError):
    """Persisted long-search state is corrupt or belongs to another exact search/model."""


STATE_FORMAT_VERSION = 2


@dataclass(frozen=True)
class PersistedFallStreamingState:
    search_signature: str
    evaluation_signature: str
    checkpoint: FallEnumerationCheckpoint | None
    accumulator: FallStreamingAccumulator
    structural_status: FallResumableEnumerationStatus
    committed_batches: int
    updated_at_utc: str

    @property
    def complete(self) -> bool:
        return self.structural_status is FallResumableEnumerationStatus.COMPLETE


def fall_streaming_search_signature(
    universe: FallSectionUniverse,
    load_policy: FallLoadPolicy,
) -> str:
    """Return the exact structural search signature used by resumable enumeration."""

    return _search_signature(universe, load_policy, _ordered_sections(universe))


def fall_streaming_evaluation_signature(
    context: FallCandidateEvaluationContext,
    *,
    verification: VerificationSummary | None = None,
) -> str:
    """Fingerprint every whole-plan input whose change invalidates an accumulated frontier."""

    return model_fingerprint(
        (context, verification),
        contract="stage4e-fall-streaming-evaluation-v1",
    )


class FallStreamingStateStore:
    """Single-row SQLite store for checkpoint + proof accumulator."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS stage4_fall_stream_state (
                    singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
                    format_version INTEGER NOT NULL,
                    search_signature TEXT NOT NULL,
                    evaluation_signature TEXT NOT NULL,
                    checkpoint_json TEXT,
                    accumulator_pickle BLOB NOT NULL,
                    structural_status TEXT NOT NULL,
                    committed_batches INTEGER NOT NULL,
                    updated_at_utc TEXT NOT NULL
                )
                """
            )

    def reset(self) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM stage4_fall_stream_state WHERE singleton_id = 1")

    def load(
        self,
        *,
        expected_search_signature: str,
        expected_evaluation_signature: str,
    ) -> PersistedFallStreamingState | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT format_version, search_signature, evaluation_signature,
                       checkpoint_json, accumulator_pickle, structural_status,
                       committed_batches, updated_at_utc
                  FROM stage4_fall_stream_state
                 WHERE singleton_id = 1
                """
            ).fetchone()
        if row is None:
            return None

        (
            format_version,
            search_signature,
            evaluation_signature,
            checkpoint_json,
            accumulator_blob,
            structural_status_raw,
            committed_batches,
            updated_at_utc,
        ) = row
        if int(format_version) != STATE_FORMAT_VERSION:
            raise FallStreamingStateError(
                f"unsupported streaming-state format version {format_version}; reset the state DB"
            )
        if search_signature != expected_search_signature:
            raise FallStreamingStateError(
                "persisted streaming state belongs to a different Fall universe/load policy"
            )
        if evaluation_signature != expected_evaluation_signature:
            raise FallStreamingStateError(
                "persisted streaming state belongs to a different degree/future/preference/evidence model"
            )

        checkpoint = None
        if checkpoint_json is not None:
            try:
                checkpoint = FallEnumerationCheckpoint.from_dict(
                    json.loads(checkpoint_json)
                )
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                raise FallStreamingStateError(
                    f"persisted structural checkpoint is malformed: {exc}"
                ) from exc
            if checkpoint.search_signature != search_signature:
                raise FallStreamingStateError(
                    "persisted structural checkpoint signature disagrees with state row"
                )

        try:
            accumulator = pickle.loads(accumulator_blob)
        except Exception as exc:  # pickle can surface several format/import errors
            raise FallStreamingStateError(
                f"persisted streaming accumulator cannot be restored: {exc}"
            ) from exc
        if not isinstance(accumulator, FallStreamingAccumulator):
            raise FallStreamingStateError(
                "persisted accumulator payload has unexpected type"
            )
        try:
            structural_status = FallResumableEnumerationStatus(structural_status_raw)
        except ValueError as exc:
            raise FallStreamingStateError(
                f"invalid persisted structural status {structural_status_raw!r}"
            ) from exc
        if structural_status is FallResumableEnumerationStatus.PAUSED and checkpoint is None:
            raise FallStreamingStateError("paused state is missing structural checkpoint")
        if structural_status is FallResumableEnumerationStatus.COMPLETE and checkpoint is not None:
            raise FallStreamingStateError("complete state must not retain a checkpoint")

        return PersistedFallStreamingState(
            search_signature=search_signature,
            evaluation_signature=evaluation_signature,
            checkpoint=checkpoint,
            accumulator=accumulator,
            structural_status=structural_status,
            committed_batches=int(committed_batches),
            updated_at_utc=str(updated_at_utc),
        )

    def commit_batch(
        self,
        *,
        search_signature: str,
        evaluation_signature: str,
        checkpoint: FallEnumerationCheckpoint | None,
        accumulator: FallStreamingAccumulator,
        structural_status: FallResumableEnumerationStatus,
        previous_committed_batches: int,
    ) -> PersistedFallStreamingState:
        """Atomically advance both structural and evaluation state by one consumed batch."""

        if not search_signature.strip() or not evaluation_signature.strip():
            raise FallStreamingStateError("search/evaluation signatures must be nonblank")
        if previous_committed_batches < 0:
            raise FallStreamingStateError("previous_committed_batches cannot be negative")
        if checkpoint is not None and checkpoint.search_signature != search_signature:
            raise FallStreamingStateError(
                "checkpoint signature does not match persistence search signature"
            )
        if structural_status is FallResumableEnumerationStatus.PAUSED and checkpoint is None:
            raise FallStreamingStateError("paused batch requires a checkpoint")
        if structural_status is FallResumableEnumerationStatus.COMPLETE and checkpoint is not None:
            raise FallStreamingStateError("complete batch must not retain a checkpoint")
        if structural_status is FallResumableEnumerationStatus.INPUT_BLOCKED:
            raise FallStreamingStateError(
                "input-blocked search should not commit an evaluated streaming batch"
            )

        checkpoint_json = (
            json.dumps(
                checkpoint.to_dict(),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            if checkpoint is not None
            else None
        )
        accumulator_blob = pickle.dumps(accumulator, protocol=pickle.HIGHEST_PROTOCOL)
        committed_batches = previous_committed_batches + 1
        updated_at = datetime.now(timezone.utc).isoformat()

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                """
                SELECT search_signature, evaluation_signature, committed_batches
                  FROM stage4_fall_stream_state
                 WHERE singleton_id = 1
                """
            ).fetchone()
            if existing is not None:
                existing_search, existing_evaluation, existing_batches = existing
                if existing_search != search_signature:
                    raise FallStreamingStateError(
                        "cannot overwrite persisted state from a different exact structural search"
                    )
                if existing_evaluation != evaluation_signature:
                    raise FallStreamingStateError(
                        "cannot overwrite persisted state from a different evaluation model"
                    )
                if int(existing_batches) != previous_committed_batches:
                    raise FallStreamingStateError(
                        "persisted state advanced since caller loaded it; refusing stale overwrite"
                    )
            elif previous_committed_batches != 0:
                raise FallStreamingStateError(
                    "caller claims prior committed batches but store is empty"
                )

            connection.execute(
                """
                INSERT INTO stage4_fall_stream_state (
                    singleton_id, format_version, search_signature, evaluation_signature,
                    checkpoint_json, accumulator_pickle, structural_status,
                    committed_batches, updated_at_utc
                ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(singleton_id) DO UPDATE SET
                    format_version = excluded.format_version,
                    search_signature = excluded.search_signature,
                    evaluation_signature = excluded.evaluation_signature,
                    checkpoint_json = excluded.checkpoint_json,
                    accumulator_pickle = excluded.accumulator_pickle,
                    structural_status = excluded.structural_status,
                    committed_batches = excluded.committed_batches,
                    updated_at_utc = excluded.updated_at_utc
                """,
                (
                    STATE_FORMAT_VERSION,
                    search_signature,
                    evaluation_signature,
                    checkpoint_json,
                    sqlite3.Binary(accumulator_blob),
                    structural_status.value,
                    committed_batches,
                    updated_at,
                ),
            )

        return PersistedFallStreamingState(
            search_signature=search_signature,
            evaluation_signature=evaluation_signature,
            checkpoint=checkpoint,
            accumulator=accumulator,
            structural_status=structural_status,
            committed_batches=committed_batches,
            updated_at_utc=updated_at,
        )
