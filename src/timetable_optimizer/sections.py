"""Pure canonical section and schedule primitives for the Stage 4 rebuild.

This module is deliberately limited to source-faithful structural facts.  It performs no
file I/O, makes no degree/eligibility/preference decisions, and never guesses a schedule
when the source data is ambiguous.

A schedule has three different meanings when it is successfully parsed:

    conflict_mask  registration/timetable overlap blocked by the university
    presence_mask  periods requiring physical campus presence
    fixed_mask     periods that pin the user's personal schedule to a clock time

For every :class:`ParsedSchedule`, ``presence ⊆ fixed ⊆ conflict``.

Crucially, a source row with no listed time is represented by
:class:`NoListedSchedule`, not by three zero masks.  A malformed or ambiguous schedule is
represented by :class:`UnresolvedSchedule`, not by a guessed schedule.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Mapping, TypeAlias


DAYS = {"월": 0, "화": 1, "수": 2, "목": 3, "금": 4, "토": 5, "일": 6}


class SectionParseError(ValueError):
    """Base error for section facts that cannot be interpreted safely."""


class SegmentAlignmentError(SectionParseError):
    """Raised internally when time and delivery segments cannot be aligned safely."""


class DeliveryKind(str, Enum):
    IN_PERSON = "inperson"
    LIVE_ONLINE = "live_online"
    VIDEO_BLOCK = "video_block"
    VIDEO_FREE = "video_free"


@dataclass(frozen=True)
class ScheduleSegment:
    """One aligned time/delivery segment, retaining the source text that produced it."""

    raw_time_text: str
    raw_room_text: str
    blocks: frozenset[tuple[int, int]]
    delivery_kind: DeliveryKind


@dataclass(frozen=True)
class ParsedSchedule:
    """A schedule whose timing and delivery semantics are sufficiently determined."""

    raw_time_text: str
    raw_room_text: str
    segments: tuple[ScheduleSegment, ...]
    conflict_mask: int
    presence_mask: int
    fixed_mask: int

    def __post_init__(self) -> None:
        if self.presence_mask & ~self.fixed_mask:
            raise SectionParseError("presence_mask is not a subset of fixed_mask")
        if self.fixed_mask & ~self.conflict_mask:
            raise SectionParseError("fixed_mask is not a subset of conflict_mask")


@dataclass(frozen=True)
class NoListedSchedule:
    """The source row contains no listed class time.

    This means only that no schedule is listed.  It must not be interpreted as proof that
    the section is asynchronous, freely overlappable, or schedule-neutral.
    """

    raw_time_text: str
    raw_room_text: str


@dataclass(frozen=True)
class UnresolvedSchedule:
    """The source contains schedule information that cannot be interpreted safely."""

    raw_time_text: str
    raw_room_text: str
    reason: str


Schedule: TypeAlias = ParsedSchedule | NoListedSchedule | UnresolvedSchedule


@dataclass(frozen=True)
class Section:
    """Canonical physical-section facts independent of downstream model decisions."""

    section_id: str
    course_code: str
    name: str
    korean_name: str
    campus: str
    credits: float | None
    professor: str
    department: str
    year_label: str
    language_code: str
    catalogue_category: str
    note: str
    grading: str
    cancelled: bool | None
    mode_text: str
    schedule: Schedule

    @property
    def schedule_is_parsed(self) -> bool:
        return isinstance(self.schedule, ParsedSchedule)

    @property
    def conflict_mask(self) -> int | None:
        return self.schedule.conflict_mask if isinstance(self.schedule, ParsedSchedule) else None

    @property
    def presence_mask(self) -> int | None:
        return self.schedule.presence_mask if isinstance(self.schedule, ParsedSchedule) else None

    @property
    def fixed_mask(self) -> int | None:
        return self.schedule.fixed_mask if isinstance(self.schedule, ParsedSchedule) else None

    @property
    def delivery_kinds(self) -> tuple[DeliveryKind, ...] | None:
        if not isinstance(self.schedule, ParsedSchedule):
            return None
        return tuple(segment.delivery_kind for segment in self.schedule.segments)

    @property
    def time_text(self) -> str:
        return self.schedule.raw_time_text

    @property
    def room_text(self) -> str:
        return self.schedule.raw_room_text



def segment_blocks(segment: str) -> frozenset[tuple[int, int]]:
    """Parse one portal time segment into ``(day, period)`` pairs.

    Parenthesized periods remain occupied.  A digit run closes on any non-digit, avoiding
    the historical ``목1(목2) -> 목12`` corruption.  Institutional range validation is done
    when masks are constructed.
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
    """Classify one non-empty room/delivery segment using verified portal semantics."""

    text = str(room_segment or "").strip()
    if not text:
        raise SegmentAlignmentError("scheduled time has no room/delivery metadata")
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



def _parsed_schedule(time_text: str, room_text: str) -> ParsedSchedule:
    raw_time_segments = [segment for segment in time_text.split("/") if segment.strip()]
    raw_room_segments = room_text.split("/")

    if len(raw_room_segments) != len(raw_time_segments):
        raise SegmentAlignmentError(
            "time/room segment mismatch: "
            f"{len(raw_time_segments)} time segment(s) vs "
            f"{len(raw_room_segments)} room segment(s); "
            f"time={time_text!r} room={room_text!r}"
        )

    segments: list[ScheduleSegment] = []
    conflict: set[tuple[int, int]] = set()
    presence: set[tuple[int, int]] = set()
    fixed: set[tuple[int, int]] = set()

    for index, raw_time in enumerate(raw_time_segments):
        blocks = segment_blocks(raw_time)
        if not blocks:
            raise SectionParseError(
                "listed time segment has no parseable periods: "
                f"segment {index + 1}; time={time_text!r}"
            )
        raw_room = raw_room_segments[index].strip()
        kind = classify_room_segment(raw_room)
        segment = ScheduleSegment(
            raw_time_text=raw_time,
            raw_room_text=raw_room,
            blocks=blocks,
            delivery_kind=kind,
        )
        segments.append(segment)

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

    return ParsedSchedule(
        raw_time_text=time_text,
        raw_room_text=room_text,
        segments=tuple(segments),
        conflict_mask=mask_from_blocks(conflict),
        presence_mask=mask_from_blocks(presence),
        fixed_mask=mask_from_blocks(fixed),
    )



def parse_schedule(time_value: Any, room_value: Any) -> Schedule:
    """Parse schedule source fields without converting missing/ambiguous data to zero."""

    time_text = str(time_value or "").strip()
    room_text = str(room_value or "")
    if not time_text:
        return NoListedSchedule(raw_time_text=time_text, raw_room_text=room_text)
    try:
        return _parsed_schedule(time_text, room_text)
    except SectionParseError as exc:
        return UnresolvedSchedule(
            raw_time_text=time_text,
            raw_room_text=room_text,
            reason=f"{type(exc).__name__}: {exc}",
        )



def _credits(raw: Mapping[str, Any]) -> float | None:
    value = raw.get("cdt")
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise SectionParseError(f"invalid credit value: {value!r}") from exc



def _cancelled(raw: Mapping[str, Any]) -> bool | None:
    """Preserve explicit portal cancellation evidence without inventing a default."""

    flag_present = "rmvlcYn" in raw and raw.get("rmvlcYn") not in (None, "")
    name_present = "rmvlcYnNm" in raw and str(raw.get("rmvlcYnNm") or "").strip() != ""
    flag = str(raw.get("rmvlcYn") or "").strip()
    name = str(raw.get("rmvlcYnNm") or "").strip()

    if flag == "1" or name == "폐강":
        return True
    if flag_present and flag == "0":
        return False
    if name_present and name != "폐강":
        return False
    return None



def section_from_raw(raw: Mapping[str, Any]) -> Section:
    """Construct canonical physical-section facts from one portal observation.

    Missing identity or malformed numeric facts raise :class:`SectionParseError` because a
    physical section cannot be safely constructed.  Schedule ambiguity does *not* raise;
    it is retained inside :class:`UnresolvedSchedule` so the section's other known facts do
    not disappear.
    """

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
        credits=_credits(raw),
        professor=str(raw.get("cgprfNm") or ""),
        department=str(raw.get("estblDeprtNm") or ""),
        year_label=str(raw.get("hy") or ""),
        language_code=str(raw.get("srclnLctreLangDivCd") or ""),
        catalogue_category=str(raw.get("subsrtDivNm") or ""),
        note=str(raw.get("atntnMattrDesc") or ""),
        grading=str(raw.get("gradeEvlMthdDivNm") or ""),
        cancelled=_cancelled(raw),
        mode_text=str(raw.get("subjtClNm") or ""),
        schedule=parse_schedule(raw.get("lctreTimeNm"), raw.get("lecrmNm")),
    )
