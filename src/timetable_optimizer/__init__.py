"""Core timetable optimizer primitives introduced during Stage 4 repair."""

from .catalog import (
    CatalogIssue,
    CatalogRecord,
    CatalogSnapshot,
    IssueCode,
    RecordStatus,
    ingest_catalog,
    load_catalog_files,
)
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
    "CatalogIssue",
    "CatalogRecord",
    "CatalogSnapshot",
    "DAYS",
    "DeliveryKind",
    "IssueCode",
    "RecordStatus",
    "Section",
    "SectionParseError",
    "SegmentAlignmentError",
    "classify_room_segment",
    "ingest_catalog",
    "load_catalog_files",
    "mask_from_blocks",
    "section_from_raw",
    "segment_blocks",
]
