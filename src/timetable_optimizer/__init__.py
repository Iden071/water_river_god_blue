"""Core timetable optimizer primitives introduced during Stage 4 repair."""

from .sections import (
    DAYS,
    DeliveryKind,
    Section,
    SectionParseError,
    SegmentAlignmentError,
    classify_room_segment,
    mask_from_blocks,
    section_from_raw,
    segment_blocks,
)

__all__ = [
    "DAYS",
    "DeliveryKind",
    "Section",
    "SectionParseError",
    "SegmentAlignmentError",
    "classify_room_segment",
    "mask_from_blocks",
    "section_from_raw",
    "segment_blocks",
]
