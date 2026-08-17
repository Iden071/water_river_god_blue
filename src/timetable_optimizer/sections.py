"""Pure section/time primitives for the Stage 4 rebuild.

This module deliberately performs no file I/O and has no import-time side effects.
It is intended to replace the parsing/classification responsibilities currently spread
across build_canonical.py, pools_past.py, rank2.py, and fm_fix.py.

The three masks have different semantics:

    conflict_mask  registration/timetable overlap that the university blocks
    presence_mask  periods requiring physical campus presence
    fixed_mask     periods that pin the user's personal schedule to a clock time

Recorded video that cannot overlap another registered class therefore appears in
``conflict_mask`` but not ``fixed_mask``. Freely overlappable video appears in none.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Mapping


DAYS = {"월": 0, "화": 1, "수": 2, "목": 3, "금": 4, "토": 5, "일": 6}


class SectionParseError(ValueError):
    """Base error for section records whose schedule cannot be interpreted safely."""


class SegmentAlignmentError(SectionParseError):
    """Raised when non-empty time segments cannot be aligned with room/mode segments."""


class DeliveryKind(str, Enum):
    IN_PERSON = "inperson"
    LIVE_ONLINE = "live_online"
    VIDEO_BLOCK = "video_block"
    VIDEO_FREE = "video_free"


@dataclass(frozen=True)
class Section:
    """Canonical section record independent of search/scoring code."""

    section_id: str
    course_code: str
    name: str
    korean_name: str
    campus: str
    credits: float
    professor: str
    department: str
    year_label: str
    language_code: str
    category: str
    note: str
    grading: str
    time_text: str
    room_text: str
    mode_text: str
    conflict_mask: int
    presence_mask: int
    fixed_mask: int
    delivery_kinds: tuple[DeliveryKind, ...]

    @property
    def has_fixed_time(self) -> bool:
        return bool(self.fixed_mask)

    @property
    def has_campus_presence(self) -> bool:
        return bool(self.presence_mask)



def segment_blocks(segment: str) -> frozenset[tuple[int, int]]:
    """Parse one portal time segment into ``(day, period)`` pairs.

    Parenthesized periods are intentionally treated as occupied, matching the current
    verified portal semantics. Period 0 and negative/empty periods are ignored; callers
    may apply stricter institutional validation separately.
    """

    out: set[tuple[int, int]] = set()
    day: int | None = None
    number = ""

    for ch in f"{segment}#":
        if ch.isdigit():
            number += ch
            continue
        if number:
            period = int(number)
            if day is not None and period >= 1:
                out.add((day, period))
            number = ""
        if ch in DAYS:
            day = DAYS[ch]

    return frozenset(out)



def classify_room_segment(room_segment: str) -> DeliveryKind:
    """Classify the delivery behavior represented by one room/mode segment."""

    text = str(room_segment or "")
    if "중복수강불가" in text:
        return DeliveryKind.VIDEO_BLOCK
    if "동영상" in text:
        return DeliveryKind.VIDEO_FREE
    if "실시간" in text:
        return DeliveryKind.LIVE_ONLINE
    return DeliveryKind.IN_PERSON



def mask_from_blocks(blocks: Iterable[tuple[int, int]]) -> int:
    """Convert ``(day, period)`` pairs to the repository's compact bitmask format."""

    mask = 0
    for day, period in blocks:
        if not 0 <= day <= 6:
            raise SectionParseError(f"invalid day index: {day}")
        if not 1 <= period <= 15:
            raise SectionParseError(f"invalid period: {period}")
        mask |= 1 << (day * 16 + period)
    return mask



def _nonempty_time_segments(time_text: str) -> list[tuple[str, frozenset[tuple[int, int]]]]:
    out: list[tuple[str, frozenset[tuple[int, int]]]] = []
    for raw in str(time_text or "").split("/"):
        blocks = segment_blocks(raw)
        if blocks:
            out.append((raw, blocks))
    return out



def _aligned_segments(
    time_text: str, room_text: str
) -> list[tuple[frozenset[tuple[int, int]], DeliveryKind]]:
    """Return aligned time/delivery segments without guessing missing room metadata."""

    times = _nonempty_time_segments(time_text)
    if not times:
        return []

    rooms = str(room_text or "").split("/")
    if len(rooms) != len(times):
        raise SegmentAlignmentError(
            "time/room segment mismatch: "
            f"{len(times)} time segment(s) vs {len(rooms)} room segment(s); "
            f"time={time_text!r} room={room_text!r}"
        )

    return [(blocks, classify_room_segment(rooms[i])) for i, (_raw, blocks) in enumerate(times)]



def _masks(
    aligned: Iterable[tuple[frozenset[tuple[int, int]], DeliveryKind]]
) -> tuple[int, int, int, tuple[DeliveryKind, ...]]:
    conflict: set[tuple[int, int]] = set()
    presence: set[tuple[int, int]] = set()
    fixed: set[tuple[int, int]] = set()
    kinds: list[DeliveryKind] = []

    for blocks, kind in aligned:
        kinds.append(kind)
        if kind in {
            DeliveryKind.IN_PERSON,
            DeliveryKind.LIVE_ONLINE,
            DeliveryKind.VIDEO_BLOCK,
        }:
            conflict.update(blocks)
        if kind is DeliveryKind.IN_PERSON:
            presence.update(blocks)
        if kind in {DeliveryKind.IN_PERSON, DeliveryKind.LIVE_ONLINE}:
            fixed.update(blocks)

    return (
        mask_from_blocks(conflict),
        mask_from_blocks(presence),
        mask_from_blocks(fixed),
        tuple(kinds),
    )



def section_from_raw(raw: Mapping[str, Any]) -> Section:
    """Construct a canonical :class:`Section` from one portal row.

    Both campuses are accepted. A row with no scheduled time is preserved with zero masks.
    Ambiguous time/room alignment raises :class:`SegmentAlignmentError` instead of silently
    copying the final room segment or discarding the section. A higher ingestion layer can
    catch that exception and record an explicit unresolved-data status.
    """

    time_text = str(raw.get("lctreTimeNm") or "").strip()
    room_text = str(raw.get("lecrmNm") or "")
    aligned = _aligned_segments(time_text, room_text)
    conflict, presence, fixed, kinds = _masks(aligned)

    section_id = str(raw.get("subjtnbCorsePrcts") or "").strip()
    course_code = str(raw.get("subjtnb") or "").strip()
    if not section_id:
        raise SectionParseError("missing section id (subjtnbCorsePrcts)")
    if not course_code:
        raise SectionParseError(f"{section_id}: missing course code (subjtnb)")

    return Section(
        section_id=section_id,
        course_code=course_code,
        name=str(raw.get("subjtEngNm") or raw.get("subjtNm") or ""),
        korean_name=str(raw.get("subjtNm") or ""),
        campus=str(raw.get("campsDivNm") or ""),
        credits=float(raw.get("cdt") or 0),
        professor=str(raw.get("cgprfNm") or ""),
        department=str(raw.get("estblDeprtNm") or ""),
        year_label=str(raw.get("hy") or ""),
        language_code=str(raw.get("srclnLctreLangDivCd") or ""),
        category=str(raw.get("subsrtDivNm") or ""),
        note=str(raw.get("atntnMattrDesc") or ""),
        grading=str(raw.get("gradeEvlMthdDivNm") or ""),
        time_text=time_text,
        room_text=room_text,
        mode_text=str(raw.get("subjtClNm") or ""),
        conflict_mask=conflict,
        presence_mask=presence,
        fixed_mask=fixed,
        delivery_kinds=kinds,
    )
