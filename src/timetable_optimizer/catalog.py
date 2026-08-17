"""Explicit catalogue ingestion for the Stage 4 rebuild.

The parser in :mod:`timetable_optimizer.sections` is intentionally pure and raises when a
portal row cannot be interpreted safely. This module is the boundary that turns those
exceptions into explicit unresolved catalogue records instead of dropping or guessing them.

No optimiser should read ``raw_2026F.json`` directly once migration reaches this layer.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from enum import Enum
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .sections import Section, SectionParseError, section_from_raw


class RecordStatus(str, Enum):
    OK = "ok"
    UNRESOLVED = "unresolved"


class IssueCode(str, Enum):
    PARSE_ERROR = "parse_error"
    DUPLICATE_SECTION_ID = "duplicate_section_id"
    INVALID_QRM_LISTING = "invalid_qrm_listing"
    ORPHAN_QRM_LISTING = "orphan_qrm_listing"


@dataclass(frozen=True)
class CatalogIssue:
    code: IssueCode
    message: str
    section_id: str = ""
    source_index: int | None = None


@dataclass(frozen=True)
class CatalogRecord:
    """One source row, preserved even when it cannot become a usable ``Section`` yet."""

    source_index: int
    section_id: str
    course_code: str
    status: RecordStatus
    section: Section | None
    qrm_category: str | None = None
    issues: tuple[CatalogIssue, ...] = ()

    @property
    def usable(self) -> bool:
        return self.status is RecordStatus.OK and self.section is not None


@dataclass(frozen=True)
class CatalogSnapshot:
    records: tuple[CatalogRecord, ...]
    issues: tuple[CatalogIssue, ...] = ()
    source_name: str = ""

    @property
    def sections(self) -> tuple[Section, ...]:
        """Only unambiguous parsed sections; unresolved rows are never silently admitted."""

        return tuple(r.section for r in self.records if r.usable and r.section is not None)

    @property
    def unresolved(self) -> tuple[CatalogRecord, ...]:
        return tuple(r for r in self.records if r.status is RecordStatus.UNRESOLVED)

    def record_for(self, section_id: str) -> CatalogRecord | None:
        hits = [r for r in self.records if r.section_id == section_id]
        return hits[0] if len(hits) == 1 else None



def _identifier(raw: Mapping[str, Any], key: str) -> str:
    return str(raw.get(key) or "").strip()



def _qrm_category(
    section_id: str,
    qrm_listings: Mapping[str, Any] | None,
) -> tuple[str | None, tuple[CatalogIssue, ...]]:
    if not qrm_listings or section_id not in qrm_listings:
        return None, ()
    row = qrm_listings[section_id]
    if not isinstance(row, Mapping):
        return None, (
            CatalogIssue(
                IssueCode.INVALID_QRM_LISTING,
                "QRM listing metadata is not an object",
                section_id=section_id,
            ),
        )
    value = str(row.get("cat") or "").strip()
    if not value:
        return None, (
            CatalogIssue(
                IssueCode.INVALID_QRM_LISTING,
                "QRM listing metadata has no category",
                section_id=section_id,
            ),
        )
    return value, ()



def ingest_catalog(
    rows: Iterable[Mapping[str, Any]],
    *,
    qrm_listings: Mapping[str, Any] | None = None,
    source_name: str = "",
) -> CatalogSnapshot:
    """Convert portal rows into a lossless catalogue snapshot.

    Every input row produces exactly one :class:`CatalogRecord`. Rows that fail parsing are
    retained as ``UNRESOLVED`` records with the error text. Duplicate physical section IDs
    are also retained and marked unresolved rather than resolved by first/last-write wins.
    QRM's own category is attached as source metadata instead of mutating the section's
    generic catalogue category.
    """

    records: list[CatalogRecord] = []
    for index, raw in enumerate(rows):
        section_id = _identifier(raw, "subjtnbCorsePrcts")
        course_code = _identifier(raw, "subjtnb")
        qcat, qissues = _qrm_category(section_id, qrm_listings)
        try:
            section = section_from_raw(raw)
            status = RecordStatus.OK
            issues = list(qissues)
            if qissues:
                status = RecordStatus.UNRESOLVED
        except (SectionParseError, TypeError, ValueError) as exc:
            section = None
            status = RecordStatus.UNRESOLVED
            issues = list(qissues)
            issues.append(
                CatalogIssue(
                    IssueCode.PARSE_ERROR,
                    f"{type(exc).__name__}: {exc}",
                    section_id=section_id,
                    source_index=index,
                )
            )
        records.append(
            CatalogRecord(
                source_index=index,
                section_id=section_id,
                course_code=course_code,
                status=status,
                section=section,
                qrm_category=qcat,
                issues=tuple(issues),
            )
        )

    counts = Counter(r.section_id for r in records if r.section_id)
    duplicate_ids = {sid for sid, n in counts.items() if n > 1}
    if duplicate_ids:
        repaired: list[CatalogRecord] = []
        for record in records:
            if record.section_id not in duplicate_ids:
                repaired.append(record)
                continue
            issue = CatalogIssue(
                IssueCode.DUPLICATE_SECTION_ID,
                f"section id appears {counts[record.section_id]} times in the source",
                section_id=record.section_id,
                source_index=record.source_index,
            )
            repaired.append(
                replace(
                    record,
                    status=RecordStatus.UNRESOLVED,
                    issues=record.issues + (issue,),
                )
            )
        records = repaired

    dataset_issues: list[CatalogIssue] = []
    if qrm_listings:
        source_ids = {r.section_id for r in records if r.section_id}
        for sid in sorted(set(qrm_listings) - source_ids):
            dataset_issues.append(
                CatalogIssue(
                    IssueCode.ORPHAN_QRM_LISTING,
                    "QRM listing refers to a section absent from this catalogue source",
                    section_id=sid,
                )
            )

    return CatalogSnapshot(
        records=tuple(records),
        issues=tuple(dataset_issues),
        source_name=source_name,
    )



def _rows_from_json_object(obj: Any) -> Sequence[Mapping[str, Any]]:
    """Accept the two raw wrappers already observed in this repository, nothing broader."""

    if isinstance(obj, list):
        if not all(isinstance(row, Mapping) for row in obj):
            raise ValueError("catalogue JSON list contains a non-object row")
        return obj
    if isinstance(obj, Mapping) and len(obj) == 1:
        only = next(iter(obj.values()))
        if isinstance(only, list) and all(isinstance(row, Mapping) for row in only):
            return only
    raise ValueError("catalogue JSON must be a list of rows or a one-key wrapper around one")



def load_catalog_files(
    raw_path: str | Path,
    *,
    qrm_listings_path: str | Path | None = None,
) -> CatalogSnapshot:
    """Explicit file-I/O boundary used by scripts/tests, never at module import time."""

    raw_path = Path(raw_path)
    with raw_path.open(encoding="utf-8") as fh:
        rows = _rows_from_json_object(json.load(fh))

    qrm_listings: Mapping[str, Any] | None = None
    if qrm_listings_path is not None:
        qpath = Path(qrm_listings_path)
        with qpath.open(encoding="utf-8") as fh:
            qobj = json.load(fh)
        if not isinstance(qobj, Mapping):
            raise ValueError("QRM listings JSON must be an object keyed by section id")
        qrm_listings = qobj

    return ingest_catalog(rows, qrm_listings=qrm_listings, source_name=str(raw_path))
