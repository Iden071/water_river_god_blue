"""Exact bitset-backed structural enumeration for the Stage 4E Fall search.

This backend enumerates the same feasible Fall section subsets as
:mod:`fall_resumable_enumeration`, but it does not scan every later section at every DFS node.
Instead each node carries a Python integer bitset containing only extensions that remain
compatible with the already-selected parsed schedule and the known ordinary-credit cap.

The optimization is representational only:

* canonical section order is unchanged;
* parsed schedule overlap is the only timetable prune;
* the explicit ordinary-credit cap is the only credit prune;
* unknown credits cost zero only for the purpose of *known-cap* pruning and remain marked
  unresolved in the emitted candidate, exactly as in the reference implementation;
* non-parsed schedules never create a conflict prune and remain marked unresolved;
* every feasible subset is emitted exactly once.

A serializable DFS checkpoint makes the search resumable.  Only an exhausted stack is
``COMPLETE``; a work budget produces ``PAUSED`` and never an optimum claim.
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


class FallBitsetEnumerationError(ValueError):
    """Bitset enumeration input or checkpoint is inconsistent."""


class FallBitsetEnumerationStatus(str, Enum):
    COMPLETE = "complete"
    PAUSED = "paused"
    INPUT_BLOCKED = "input_blocked"


@dataclass(frozen=True)
class FallBitsetFrame:
    """One DFS node and its still-unvisited structurally admissible child bitset."""

    selected_indices: tuple[int, ...]
    remaining_mask: int
    known_total_credits: float
    known_ordinary_credits: float
    known_chapel_credits: float
    unknown_credit_section_ids: tuple[str, ...]
    unresolved_schedule_section_ids: tuple[str, ...]
    emitted: bool = False

    def __post_init__(self) -> None:
        if self.remaining_mask < 0:
            raise FallBitsetEnumerationError("remaining_mask cannot be negative")
        if tuple(sorted(self.selected_indices)) != self.selected_indices:
            raise FallBitsetEnumerationError("selected indices must be increasing")
        if len(self.selected_indices) != len(set(self.selected_indices)):
            raise FallBitsetEnumerationError("frame repeats a selected index")
        for value in (
            self.known_total_credits,
            self.known_ordinary_credits,
            self.known_chapel_credits,
        ):
            if not isfinite(value) or value < 0:
                raise FallBitsetEnumerationError(
                    "known credit totals must be finite and nonnegative"
                )


@dataclass(frozen=True)
class FallBitsetCheckpoint:
    format_version: int
    search_signature: str
    frames: tuple[FallBitsetFrame, ...]
    emitted_candidates: int = 0
    expanded_extensions: int = 0

    CURRENT_FORMAT_VERSION = 1

    def __post_init__(self) -> None:
        if self.format_version != self.CURRENT_FORMAT_VERSION:
            raise FallBitsetEnumerationError(
                f"unsupported bitset checkpoint version {self.format_version}"
            )
        if not self.search_signature.strip():
            raise FallBitsetEnumerationError("checkpoint requires search_signature")
        if self.emitted_candidates < 0 or self.expanded_extensions < 0:
            raise FallBitsetEnumerationError("checkpoint counters cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        # Encode the potentially ~1500-bit masks as hex strings rather than giant JSON
        # decimal numbers.  This keeps checkpoints portable and exact.
        frames = []
        for frame in self.frames:
            raw = asdict(frame)
            raw["remaining_mask"] = hex(frame.remaining_mask)
            frames.append(raw)
        return {
            "format_version": self.format_version,
            "search_signature": self.search_signature,
            "frames": frames,
            "emitted_candidates": self.emitted_candidates,
            "expanded_extensions": self.expanded_extensions,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "FallBitsetCheckpoint":
        try:
            frames = tuple(
                FallBitsetFrame(
                    selected_indices=tuple(int(i) for i in item["selected_indices"]),
                    remaining_mask=int(str(item["remaining_mask"]), 16),
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
                expanded_extensions=int(raw.get("expanded_extensions", 0)),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise FallBitsetEnumerationError(
                f"malformed bitset checkpoint: {exc}"
            ) from exc


@dataclass(frozen=True)
class FallBitsetBatch:
    status: FallBitsetEnumerationStatus
    candidates: tuple[FallCandidateSet, ...]
    checkpoint: FallBitsetCheckpoint | None
    batch_expanded_extensions: int

    @property
    def complete(self) -> bool:
        return self.status is FallBitsetEnumerationStatus.COMPLETE

    @property
    def resumable(self) -> bool:
        return self.status is FallBitsetEnumerationStatus.PAUSED


@dataclass(frozen=True)
class _CompiledBitsetUniverse:
    ordered: tuple[Section, ...]
    conflict_masks: tuple[int, ...]
    ordinary_costs: tuple[float, ...]
    total_costs: tuple[float, ...]
    chapel_costs: tuple[float, ...]
    credit_unknown: tuple[bool, ...]
    unresolved_schedule: tuple[bool, ...]
    all_mask: int


def _ordered_sections(universe: FallSectionUniverse) -> tuple[Section, ...]:
    return tuple(sorted(universe.included_sections, key=lambda section: section.section_id))


def _search_signature(
    universe: FallSectionUniverse,
    load_policy: FallLoadPolicy,
    ordered: tuple[Section, ...],
) -> str:
    payload = {
        "contract": "stage4e-fall-bitset-extension-v1",
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


def _compile(
    ordered: tuple[Section, ...],
    policy: FallLoadPolicy,
) -> _CompiledBitsetUniverse:
    count = len(ordered)
    all_mask = (1 << count) - 1 if count else 0

    # For each timetable bit, record every section occupying it.  A section's conflict
    # bitset is then just the OR of the occupancy bitsets for its own schedule bits.
    occupancy: dict[int, int] = {}
    schedule_values: list[int | None] = []
    for index, section in enumerate(ordered):
        if isinstance(section.schedule, ParsedSchedule):
            mask = section.schedule.conflict_mask
            schedule_values.append(mask)
            bit_value = mask
            while bit_value:
                low = bit_value & -bit_value
                occupancy[low] = occupancy.get(low, 0) | (1 << index)
                bit_value ^= low
        else:
            schedule_values.append(None)

    conflict_masks: list[int] = []
    for mask in schedule_values:
        if mask is None:
            conflict_masks.append(0)
            continue
        conflicts = 0
        bit_value = mask
        while bit_value:
            low = bit_value & -bit_value
            conflicts |= occupancy.get(low, 0)
            bit_value ^= low
        conflict_masks.append(conflicts)

    ordinary_costs: list[float] = []
    total_costs: list[float] = []
    chapel_costs: list[float] = []
    credit_unknown: list[bool] = []
    unresolved_schedule: list[bool] = []
    for section in ordered:
        total, ordinary, chapel, unknown = _credit_effect(section, policy)
        total_costs.append(total)
        ordinary_costs.append(ordinary)
        chapel_costs.append(chapel)
        credit_unknown.append(unknown)
        unresolved_schedule.append(not isinstance(section.schedule, ParsedSchedule))

    return _CompiledBitsetUniverse(
        ordered=ordered,
        conflict_masks=tuple(conflict_masks),
        ordinary_costs=tuple(ordinary_costs),
        total_costs=tuple(total_costs),
        chapel_costs=tuple(chapel_costs),
        credit_unknown=tuple(credit_unknown),
        unresolved_schedule=tuple(unresolved_schedule),
        all_mask=all_mask,
    )


def _credit_allowed_mask(
    compiled: _CompiledBitsetUniverse,
    remaining_credit: float,
    cache: dict[float, int],
) -> int:
    # Credit totals in the source are stable decimal quantities; cache by the exact
    # subtraction result used by this search.  Unknown credits intentionally have known
    # ordinary cost zero and therefore remain admissible here.
    cached = cache.get(remaining_credit)
    if cached is not None:
        return cached
    mask = 0
    epsilon = 1e-12
    for index, cost in enumerate(compiled.ordinary_costs):
        if cost <= remaining_credit + epsilon:
            mask |= 1 << index
    cache[remaining_credit] = mask
    return mask


def _candidate_from_frame(
    frame: FallBitsetFrame,
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


def _validate_checkpoint(
    checkpoint: FallBitsetCheckpoint,
    signature: str,
    section_count: int,
) -> None:
    if checkpoint.search_signature != signature:
        raise FallBitsetEnumerationError(
            "bitset checkpoint belongs to a different universe/load-policy search"
        )
    all_mask = (1 << section_count) - 1 if section_count else 0
    for frame in checkpoint.frames:
        if frame.remaining_mask & ~all_mask:
            raise FallBitsetEnumerationError(
                "checkpoint remaining_mask references section outside universe"
            )
        if frame.selected_indices and frame.selected_indices[-1] >= section_count:
            raise FallBitsetEnumerationError(
                "checkpoint selected index references section outside universe"
            )
        if frame.selected_indices:
            lower_or_equal = (1 << (frame.selected_indices[-1] + 1)) - 1
            if frame.remaining_mask & lower_or_equal:
                raise FallBitsetEnumerationError(
                    "checkpoint child mask contains index not after last selected section"
                )


def enumerate_fall_candidate_bitset_batch(
    universe: FallSectionUniverse,
    load_policy: FallLoadPolicy,
    *,
    checkpoint: FallBitsetCheckpoint | None = None,
    max_emitted_candidates: int = 100_000,
    max_expanded_extensions: int = 1_000_000,
) -> FallBitsetBatch:
    """Continue the exact bitset DFS for a bounded amount of admissible work."""

    if max_emitted_candidates <= 0:
        raise FallBitsetEnumerationError("max_emitted_candidates must be positive")
    if max_expanded_extensions <= 0:
        raise FallBitsetEnumerationError("max_expanded_extensions must be positive")

    ordered = _ordered_sections(universe)
    signature = _search_signature(universe, load_policy, ordered)
    if universe.status is FallUniverseStatus.INPUT_BLOCKED:
        if checkpoint is not None:
            _validate_checkpoint(checkpoint, signature, len(ordered))
        return FallBitsetBatch(
            status=FallBitsetEnumerationStatus.INPUT_BLOCKED,
            candidates=(),
            checkpoint=None,
            batch_expanded_extensions=0,
        )

    compiled = _compile(ordered, load_policy)
    credit_mask_cache: dict[float, int] = {}

    if checkpoint is None:
        root_remaining = compiled.all_mask & _credit_allowed_mask(
            compiled,
            load_policy.ordinary_credit_cap,
            credit_mask_cache,
        )
        current = FallBitsetCheckpoint(
            format_version=FallBitsetCheckpoint.CURRENT_FORMAT_VERSION,
            search_signature=signature,
            frames=(
                FallBitsetFrame(
                    selected_indices=(),
                    remaining_mask=root_remaining,
                    known_total_credits=0.0,
                    known_ordinary_credits=0.0,
                    known_chapel_credits=0.0,
                    unknown_credit_section_ids=(),
                    unresolved_schedule_section_ids=(),
                    emitted=False,
                ),
            ),
        )
    else:
        _validate_checkpoint(checkpoint, signature, len(ordered))
        current = checkpoint

    stack = list(current.frames)
    emitted_total = current.emitted_candidates
    expanded_total = current.expanded_extensions
    candidates: list[FallCandidateSet] = []
    batch_expanded = 0

    while stack:
        if len(candidates) >= max_emitted_candidates:
            break

        frame = stack[-1]
        if not frame.emitted:
            candidates.append(_candidate_from_frame(frame, ordered))
            emitted_total += 1
            stack[-1] = FallBitsetFrame(
                selected_indices=frame.selected_indices,
                remaining_mask=frame.remaining_mask,
                known_total_credits=frame.known_total_credits,
                known_ordinary_credits=frame.known_ordinary_credits,
                known_chapel_credits=frame.known_chapel_credits,
                unknown_credit_section_ids=frame.unknown_credit_section_ids,
                unresolved_schedule_section_ids=frame.unresolved_schedule_section_ids,
                emitted=True,
            )
            continue

        if frame.remaining_mask == 0:
            stack.pop()
            continue
        if batch_expanded >= max_expanded_extensions:
            break

        low = frame.remaining_mask & -frame.remaining_mask
        index = low.bit_length() - 1
        parent_remaining = frame.remaining_mask ^ low

        # Advance the parent before descending, exactly like the reference resumable DFS.
        stack[-1] = FallBitsetFrame(
            selected_indices=frame.selected_indices,
            remaining_mask=parent_remaining,
            known_total_credits=frame.known_total_credits,
            known_ordinary_credits=frame.known_ordinary_credits,
            known_chapel_credits=frame.known_chapel_credits,
            unknown_credit_section_ids=frame.unknown_credit_section_ids,
            unresolved_schedule_section_ids=frame.unresolved_schedule_section_ids,
            emitted=True,
        )

        batch_expanded += 1
        expanded_total += 1

        next_ordinary = frame.known_ordinary_credits + compiled.ordinary_costs[index]
        remaining_credit = load_policy.ordinary_credit_cap - next_ordinary
        child_remaining = parent_remaining & ~compiled.conflict_masks[index]
        child_remaining &= _credit_allowed_mask(
            compiled,
            remaining_credit,
            credit_mask_cache,
        )

        section = ordered[index]
        stack.append(
            FallBitsetFrame(
                selected_indices=frame.selected_indices + (index,),
                remaining_mask=child_remaining,
                known_total_credits=(
                    frame.known_total_credits + compiled.total_costs[index]
                ),
                known_ordinary_credits=next_ordinary,
                known_chapel_credits=(
                    frame.known_chapel_credits + compiled.chapel_costs[index]
                ),
                unknown_credit_section_ids=(
                    frame.unknown_credit_section_ids
                    + ((section.section_id,) if compiled.credit_unknown[index] else ())
                ),
                unresolved_schedule_section_ids=(
                    frame.unresolved_schedule_section_ids
                    + ((section.section_id,) if compiled.unresolved_schedule[index] else ())
                ),
                emitted=False,
            )
        )

    if stack:
        next_checkpoint = FallBitsetCheckpoint(
            format_version=FallBitsetCheckpoint.CURRENT_FORMAT_VERSION,
            search_signature=signature,
            frames=tuple(stack),
            emitted_candidates=emitted_total,
            expanded_extensions=expanded_total,
        )
        status = FallBitsetEnumerationStatus.PAUSED
    else:
        next_checkpoint = None
        status = FallBitsetEnumerationStatus.COMPLETE

    return FallBitsetBatch(
        status=status,
        candidates=tuple(candidates),
        checkpoint=next_checkpoint,
        batch_expanded_extensions=batch_expanded,
    )
