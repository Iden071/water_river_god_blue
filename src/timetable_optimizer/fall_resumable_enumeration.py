"""Resumable exact structural enumeration for the Stage 4E Fall search.

The reference ``fall_candidate_sets`` implementation proves the right semantics but walks a
binary include/exclude tree.  With ~1,500 Fall sections, that representation spends almost
all of its effort traversing explicit exclusion paths.

This module enumerates the *same feasible subset family* using canonical extension DFS:

* the empty set is one node;
* a node containing indices ``i1 < ... < ik`` may extend only with an index ``j > ik``;
* an extension is skipped only when a parsed registration-conflict mask proves overlap or
  the known ordinary-credit total proves the explicit cap is exceeded;
* unknown credits and non-parsed schedules remain in the candidate and are never pruned.

Every feasible subset has exactly one increasing index sequence, so it is emitted exactly
once.  Search order changes performance, not semantics.

The complete DFS stack is serializable.  A stopped process therefore returns ``PAUSED`` with
a checkpoint rather than ``TRUNCATED``: resuming that checkpoint continues the same exact
search.  Only exhausting the stack yields ``COMPLETE``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from math import isfinite
from typing import Any, Mapping

from .fall_candidate_sets import (
    FallCandidateLoadFacts,
    FallCandidateSet,
    FallLoadPolicy,
)
from .fall_universe import FallSectionUniverse, FallUniverseStatus
from .recognition import CHAPEL_2026_CODES
from .sections import ParsedSchedule, Section


class FallResumableEnumerationError(ValueError):
    """A resumable Fall enumeration input/checkpoint is inconsistent."""


class FallResumableEnumerationStatus(str, Enum):
    COMPLETE = "complete"
    PAUSED = "paused"
    INPUT_BLOCKED = "input_blocked"


@dataclass(frozen=True)
class FallEnumerationFrame:
    """One DFS node plus its next unexplored canonical extension index."""

    selected_indices: tuple[int, ...]
    next_index: int
    conflict_mask: int
    known_total_credits: float
    known_ordinary_credits: float
    known_chapel_credits: float
    unknown_credit_section_ids: tuple[str, ...]
    unresolved_schedule_section_ids: tuple[str, ...]
    emitted: bool = False

    def __post_init__(self) -> None:
        if self.next_index < 0:
            raise FallResumableEnumerationError("frame next_index cannot be negative")
        if self.conflict_mask < 0:
            raise FallResumableEnumerationError("frame conflict mask cannot be negative")
        if tuple(sorted(self.selected_indices)) != self.selected_indices:
            raise FallResumableEnumerationError(
                "frame selected indices must be strictly increasing"
            )
        if len(self.selected_indices) != len(set(self.selected_indices)):
            raise FallResumableEnumerationError("frame repeats a selected index")
        for value in (
            self.known_total_credits,
            self.known_ordinary_credits,
            self.known_chapel_credits,
        ):
            if not isfinite(value) or value < 0:
                raise FallResumableEnumerationError(
                    "frame known credit totals must be finite and nonnegative"
                )


@dataclass(frozen=True)
class FallEnumerationCheckpoint:
    """Portable continuation state for one exact Fall structural search."""

    format_version: int
    search_signature: str
    frames: tuple[FallEnumerationFrame, ...]
    emitted_candidates: int = 0
    extension_checks: int = 0
    pruned_extensions_by_conflict: int = 0
    pruned_extensions_by_credit_cap: int = 0

    CURRENT_FORMAT_VERSION = 1

    def __post_init__(self) -> None:
        if self.format_version != self.CURRENT_FORMAT_VERSION:
            raise FallResumableEnumerationError(
                f"unsupported Fall checkpoint format version {self.format_version}"
            )
        if not self.search_signature.strip():
            raise FallResumableEnumerationError("checkpoint requires search signature")
        for value in (
            self.emitted_candidates,
            self.extension_checks,
            self.pruned_extensions_by_conflict,
            self.pruned_extensions_by_credit_cap,
        ):
            if value < 0:
                raise FallResumableEnumerationError(
                    "checkpoint counters cannot be negative"
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "format_version": self.format_version,
            "search_signature": self.search_signature,
            "frames": [asdict(frame) for frame in self.frames],
            "emitted_candidates": self.emitted_candidates,
            "extension_checks": self.extension_checks,
            "pruned_extensions_by_conflict": self.pruned_extensions_by_conflict,
            "pruned_extensions_by_credit_cap": self.pruned_extensions_by_credit_cap,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "FallEnumerationCheckpoint":
        try:
            frames = tuple(
                FallEnumerationFrame(
                    selected_indices=tuple(int(i) for i in item["selected_indices"]),
                    next_index=int(item["next_index"]),
                    conflict_mask=int(item["conflict_mask"]),
                    known_total_credits=float(item["known_total_credits"]),
                    known_ordinary_credits=float(item["known_ordinary_credits"]),
                    known_chapel_credits=float(item["known_chapel_credits"]),
                    unknown_credit_section_ids=tuple(item["unknown_credit_section_ids"]),
                    unresolved_schedule_section_ids=tuple(
                        item["unresolved_schedule_section_ids"]
                    ),
                    emitted=bool(item["emitted"]),
                )
                for item in raw["frames"]
            )
            return cls(
                format_version=int(raw["format_version"]),
                search_signature=str(raw["search_signature"]),
                frames=frames,
                emitted_candidates=int(raw.get("emitted_candidates", 0)),
                extension_checks=int(raw.get("extension_checks", 0)),
                pruned_extensions_by_conflict=int(
                    raw.get("pruned_extensions_by_conflict", 0)
                ),
                pruned_extensions_by_credit_cap=int(
                    raw.get("pruned_extensions_by_credit_cap", 0)
                ),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise FallResumableEnumerationError(
                f"malformed Fall enumeration checkpoint: {exc}"
            ) from exc


@dataclass(frozen=True)
class FallEnumerationBatch:
    """Candidates emitted during one bounded invocation of the exact DFS."""

    status: FallResumableEnumerationStatus
    candidates: tuple[FallCandidateSet, ...]
    checkpoint: FallEnumerationCheckpoint | None
    batch_extension_checks: int
    batch_pruned_by_conflict: int
    batch_pruned_by_credit_cap: int

    @property
    def complete(self) -> bool:
        return self.status is FallResumableEnumerationStatus.COMPLETE

    @property
    def resumable(self) -> bool:
        return self.status is FallResumableEnumerationStatus.PAUSED


def _ordered_sections(universe: FallSectionUniverse) -> tuple[Section, ...]:
    return tuple(sorted(universe.included_sections, key=lambda section: section.section_id))


def _search_signature(
    universe: FallSectionUniverse,
    load_policy: FallLoadPolicy,
    ordered: tuple[Section, ...],
) -> str:
    payload = {
        "contract": "stage4e-fall-canonical-extension-v1",
        "universe_id": universe.universe_id,
        "scope_kind": universe.scope.kind.value,
        "scope_source_id": universe.scope.source_id,
        "source_name": universe.source_name,
        "source_fingerprint": universe.source_fingerprint,
        "included_section_ids": [section.section_id for section in ordered],
        "load_policy": {
            "ordinary_credit_cap": load_policy.ordinary_credit_cap,
            "chapel_exempt_from_ordinary_cap": (
                load_policy.chapel_exempt_from_ordinary_cap
            ),
            "source_id": load_policy.source_id,
        },
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _credit_effect(
    section: Section,
    policy: FallLoadPolicy,
) -> tuple[float, float, float, bool]:
    if section.credits is None:
        return 0.0, 0.0, 0.0, True
    total = float(section.credits)
    if section.course_code in CHAPEL_2026_CODES:
        chapel = total
        ordinary = 0.0 if policy.chapel_exempt_from_ordinary_cap else total
    else:
        chapel = 0.0
        ordinary = total
    return total, ordinary, chapel, False


def _root_checkpoint(signature: str) -> FallEnumerationCheckpoint:
    return FallEnumerationCheckpoint(
        format_version=FallEnumerationCheckpoint.CURRENT_FORMAT_VERSION,
        search_signature=signature,
        frames=(
            FallEnumerationFrame(
                selected_indices=(),
                next_index=0,
                conflict_mask=0,
                known_total_credits=0.0,
                known_ordinary_credits=0.0,
                known_chapel_credits=0.0,
                unknown_credit_section_ids=(),
                unresolved_schedule_section_ids=(),
                emitted=False,
            ),
        ),
    )


def _validate_checkpoint(
    checkpoint: FallEnumerationCheckpoint,
    signature: str,
    section_count: int,
) -> None:
    if checkpoint.search_signature != signature:
        raise FallResumableEnumerationError(
            "Fall checkpoint belongs to a different universe/load-policy search"
        )
    for frame in checkpoint.frames:
        if frame.next_index > section_count:
            raise FallResumableEnumerationError(
                "checkpoint frame next_index exceeds current section universe"
            )
        if frame.selected_indices and frame.selected_indices[-1] >= section_count:
            raise FallResumableEnumerationError(
                "checkpoint frame references section outside current universe"
            )
        if frame.selected_indices and frame.next_index < frame.selected_indices[-1] + 1:
            raise FallResumableEnumerationError(
                "checkpoint frame next_index precedes its last selected section"
            )


def _candidate_from_frame(
    frame: FallEnumerationFrame,
    ordered: tuple[Section, ...],
) -> FallCandidateSet:
    sections = tuple(ordered[index] for index in frame.selected_indices)
    return FallCandidateSet(
        section_ids=tuple(section.section_id for section in sections),
        sections=sections,
        load=FallCandidateLoadFacts(
            known_total_credits=frame.known_total_credits,
            known_ordinary_credits=frame.known_ordinary_credits,
            known_chapel_credits=frame.known_chapel_credits,
            unknown_credit_section_ids=frame.unknown_credit_section_ids,
        ),
        unresolved_schedule_section_ids=frame.unresolved_schedule_section_ids,
    )


def enumerate_fall_candidate_batch(
    universe: FallSectionUniverse,
    load_policy: FallLoadPolicy,
    *,
    checkpoint: FallEnumerationCheckpoint | None = None,
    max_emitted_candidates: int = 10_000,
    max_extension_checks: int = 1_000_000,
) -> FallEnumerationBatch:
    """Continue exact structural enumeration for a bounded amount of work.

    ``PAUSED`` is not a proof failure and not a shortlist.  The returned checkpoint contains
    the complete unvisited DFS frontier.  Supplying it to the next call resumes without
    duplicate candidate emission or skipped branches.
    """

    if max_emitted_candidates <= 0:
        raise FallResumableEnumerationError("max_emitted_candidates must be positive")
    if max_extension_checks <= 0:
        raise FallResumableEnumerationError("max_extension_checks must be positive")

    ordered = _ordered_sections(universe)
    signature = _search_signature(universe, load_policy, ordered)

    if universe.status is FallUniverseStatus.INPUT_BLOCKED:
        if checkpoint is not None:
            _validate_checkpoint(checkpoint, signature, len(ordered))
        return FallEnumerationBatch(
            status=FallResumableEnumerationStatus.INPUT_BLOCKED,
            candidates=(),
            checkpoint=None,
            batch_extension_checks=0,
            batch_pruned_by_conflict=0,
            batch_pruned_by_credit_cap=0,
        )

    current = checkpoint or _root_checkpoint(signature)
    _validate_checkpoint(current, signature, len(ordered))

    stack = list(current.frames)
    emitted_total = current.emitted_candidates
    checks_total = current.extension_checks
    conflict_total = current.pruned_extensions_by_conflict
    credit_total = current.pruned_extensions_by_credit_cap

    candidates: list[FallCandidateSet] = []
    batch_checks = 0
    batch_conflict = 0
    batch_credit = 0

    while stack:
        if len(candidates) >= max_emitted_candidates:
            break

        frame = stack[-1]
        if not frame.emitted:
            candidates.append(_candidate_from_frame(frame, ordered))
            emitted_total += 1
            stack[-1] = FallEnumerationFrame(
                selected_indices=frame.selected_indices,
                next_index=frame.next_index,
                conflict_mask=frame.conflict_mask,
                known_total_credits=frame.known_total_credits,
                known_ordinary_credits=frame.known_ordinary_credits,
                known_chapel_credits=frame.known_chapel_credits,
                unknown_credit_section_ids=frame.unknown_credit_section_ids,
                unresolved_schedule_section_ids=frame.unresolved_schedule_section_ids,
                emitted=True,
            )
            continue

        if frame.next_index >= len(ordered):
            stack.pop()
            continue

        if batch_checks >= max_extension_checks:
            break

        index = frame.next_index
        section = ordered[index]
        # Advance the parent *before* exploring the extension.  If we pause inside the child,
        # resuming it eventually returns to a parent that already knows this index was tried.
        stack[-1] = FallEnumerationFrame(
            selected_indices=frame.selected_indices,
            next_index=index + 1,
            conflict_mask=frame.conflict_mask,
            known_total_credits=frame.known_total_credits,
            known_ordinary_credits=frame.known_ordinary_credits,
            known_chapel_credits=frame.known_chapel_credits,
            unknown_credit_section_ids=frame.unknown_credit_section_ids,
            unresolved_schedule_section_ids=frame.unresolved_schedule_section_ids,
            emitted=True,
        )

        batch_checks += 1
        checks_total += 1

        next_conflict_mask = frame.conflict_mask
        next_unresolved_schedules = frame.unresolved_schedule_section_ids
        if isinstance(section.schedule, ParsedSchedule):
            if frame.conflict_mask & section.schedule.conflict_mask:
                batch_conflict += 1
                conflict_total += 1
                continue
            next_conflict_mask |= section.schedule.conflict_mask
        else:
            next_unresolved_schedules = (
                frame.unresolved_schedule_section_ids + (section.section_id,)
            )

        add_total, add_ordinary, add_chapel, credit_unknown = _credit_effect(
            section, load_policy
        )
        next_ordinary = frame.known_ordinary_credits + add_ordinary
        if next_ordinary > load_policy.ordinary_credit_cap:
            batch_credit += 1
            credit_total += 1
            continue

        stack.append(
            FallEnumerationFrame(
                selected_indices=frame.selected_indices + (index,),
                next_index=index + 1,
                conflict_mask=next_conflict_mask,
                known_total_credits=frame.known_total_credits + add_total,
                known_ordinary_credits=next_ordinary,
                known_chapel_credits=frame.known_chapel_credits + add_chapel,
                unknown_credit_section_ids=(
                    frame.unknown_credit_section_ids
                    + ((section.section_id,) if credit_unknown else ())
                ),
                unresolved_schedule_section_ids=next_unresolved_schedules,
                emitted=False,
            )
        )

    if stack:
        next_checkpoint = FallEnumerationCheckpoint(
            format_version=FallEnumerationCheckpoint.CURRENT_FORMAT_VERSION,
            search_signature=signature,
            frames=tuple(stack),
            emitted_candidates=emitted_total,
            extension_checks=checks_total,
            pruned_extensions_by_conflict=conflict_total,
            pruned_extensions_by_credit_cap=credit_total,
        )
        status = FallResumableEnumerationStatus.PAUSED
    else:
        next_checkpoint = None
        status = FallResumableEnumerationStatus.COMPLETE

    return FallEnumerationBatch(
        status=status,
        candidates=tuple(candidates),
        checkpoint=next_checkpoint,
        batch_extension_checks=batch_checks,
        batch_pruned_by_conflict=batch_conflict,
        batch_pruned_by_credit_cap=batch_credit,
    )
