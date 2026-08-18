"""Source-faithful catalogue ingestion for the Stage 4 rebuild.

This module is the explicit I/O/reconciliation boundary above the pure parser in
:mod:`timetable_optimizer.sections`.

The important distinction is:

    source observation  !=  physical section  !=  program listing overlay

Every source row is preserved.  Multiple observations of the same physical section are
reconciled only when they are exactly compatible; contradictory duplicates remain explicit
and unresolved.  Program-specific listing metadata (currently QRM's own category view) is
kept separately and cannot make an otherwise valid physical section disappear.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .sections import Section, SectionParseError, section_from_raw


class ObservationStatus(str, Enum):
    PARSED = "parsed"
    UNRESOLVED = "unresolved"


class PhysicalStatus(str, Enum):
    OK = "ok"
    UNRESOLVED = "unresolved"


class ListingStatus(str, Enum):
    OK = "ok"
    UNRESOLVED = "unresolved"


class ReconciliationKind(str, Enum):
    SINGLE = "single"
    COALESCED_IDENTICAL = "coalesced_identical"
    CONFLICT = "conflict"


class IssueCode(str, Enum):
    PARSE_ERROR = "parse_error"
    DUPLICATE_SECTION_CONFLICT = "duplicate_section_conflict"
    INVALID_LISTING = "invalid_listing"
    ORPHAN_LISTING = "orphan_listing"


@dataclass(frozen=True)
class SourceRef:
    """Where one observation came from."""

    source_kind: str
    source_name: str
    term: str
    source_index: int
    source_fingerprint: str = ""


@dataclass(frozen=True)
class CatalogIssue:
    code: IssueCode
    message: str
    section_id: str = ""
    source_index: int | None = None


@dataclass(frozen=True)
class SectionObservation:
    """One raw catalogue row plus the canonical facts derivable from it."""

    source: SourceRef
    section_id: str
    course_code: str
    status: ObservationStatus
    section: Section | None
    raw: Mapping[str, Any]
    issues: tuple[CatalogIssue, ...] = ()


@dataclass(frozen=True)
class PhysicalSectionRecord:
    """One physical section reconciled from one or more source observations."""

    section_id: str
    status: PhysicalStatus
    section: Section | None
    observation_indexes: tuple[int, ...]
    reconciliation: ReconciliationKind
    issues: tuple[CatalogIssue, ...] = ()

    @property
    def usable(self) -> bool:
        return self.status is PhysicalStatus.OK and self.section is not None


@dataclass(frozen=True)
class ListingObservation:
    """Program/department-specific view of a section, separate from physical facts."""

    source: SourceRef
    program: str
    section_id: str
    status: ListingStatus
    listed_category: str | None
    year_label: str
    campus: str
    raw: Mapping[str, Any]
    issues: tuple[CatalogIssue, ...] = ()


@dataclass(frozen=True)
class CatalogSnapshot:
    observations: tuple[SectionObservation, ...]
    physical_sections: tuple[PhysicalSectionRecord, ...]
    listings: tuple[ListingObservation, ...] = ()
    issues: tuple[CatalogIssue, ...] = ()
    source_name: str = ""
    source_fingerprint: str = ""

    @property
    def sections(self) -> tuple[Section, ...]:
        return tuple(
            record.section
            for record in self.physical_sections
            if record.usable and record.section is not None
        )

    @property
    def unresolved_physical_sections(self) -> tuple[PhysicalSectionRecord, ...]:
        return tuple(
            record
            for record in self.physical_sections
            if record.status is PhysicalStatus.UNRESOLVED
        )

    def record_for(self, section_id: str) -> PhysicalSectionRecord | None:
        hits = [record for record in self.physical_sections if record.section_id == section_id]
        return hits[0] if len(hits) == 1 else None

    def listings_for(self, section_id: str, *, program: str | None = None) -> tuple[ListingObservation, ...]:
        return tuple(
            listing
            for listing in self.listings
            if listing.section_id == section_id
            and (program is None or listing.program == program)
        )



def _identifier(raw: Mapping[str, Any], key: str) -> str:
    return str(raw.get(key) or "").strip()



def _copy_raw(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Detach retained provenance from a caller's later mutation of its input mapping."""

    return dict(raw)



def _reconcile(observations: Sequence[SectionObservation]) -> tuple[PhysicalSectionRecord, ...]:
    by_id: dict[str, list[SectionObservation]] = defaultdict(list)
    for observation in observations:
        if observation.section_id:
            by_id[observation.section_id].append(observation)

    physical: list[PhysicalSectionRecord] = []
    for section_id in sorted(by_id):
        group = by_id[section_id]
        indexes = tuple(observation.source.source_index for observation in group)

        if len(group) == 1:
            observation = group[0]
            if observation.status is ObservationStatus.PARSED and observation.section is not None:
                physical.append(
                    PhysicalSectionRecord(
                        section_id=section_id,
                        status=PhysicalStatus.OK,
                        section=observation.section,
                        observation_indexes=indexes,
                        reconciliation=ReconciliationKind.SINGLE,
                    )
                )
            else:
                physical.append(
                    PhysicalSectionRecord(
                        section_id=section_id,
                        status=PhysicalStatus.UNRESOLVED,
                        section=None,
                        observation_indexes=indexes,
                        reconciliation=ReconciliationKind.CONFLICT,
                        issues=observation.issues,
                    )
                )
            continue

        parsed_sections = [
            observation.section
            for observation in group
            if observation.status is ObservationStatus.PARSED and observation.section is not None
        ]
        all_parsed = len(parsed_sections) == len(group)
        identical = all_parsed and all(section == parsed_sections[0] for section in parsed_sections[1:])

        if identical:
            physical.append(
                PhysicalSectionRecord(
                    section_id=section_id,
                    status=PhysicalStatus.OK,
                    section=parsed_sections[0],
                    observation_indexes=indexes,
                    reconciliation=ReconciliationKind.COALESCED_IDENTICAL,
                )
            )
            continue

        issue = CatalogIssue(
            IssueCode.DUPLICATE_SECTION_CONFLICT,
            "multiple observations for this section are not exactly compatible",
            section_id=section_id,
        )
        physical.append(
            PhysicalSectionRecord(
                section_id=section_id,
                status=PhysicalStatus.UNRESOLVED,
                section=None,
                observation_indexes=indexes,
                reconciliation=ReconciliationKind.CONFLICT,
                issues=(issue,),
            )
        )

    return tuple(physical)



def _listing_observations(
    listings: Mapping[str, Any] | None,
    *,
    program: str,
    source_name: str,
    term: str,
    source_fingerprint: str,
) -> tuple[ListingObservation, ...]:
    if not listings:
        return ()

    out: list[ListingObservation] = []
    for index, section_id in enumerate(sorted(str(key) for key in listings)):
        row = listings[section_id]
        source = SourceRef(
            source_kind="program_listing",
            source_name=source_name,
            term=term,
            source_index=index,
            source_fingerprint=source_fingerprint,
        )
        issues: list[CatalogIssue] = []
        listed_category: str | None = None
        year_label = ""
        campus = ""

        if not isinstance(row, Mapping):
            issues.append(
                CatalogIssue(
                    IssueCode.INVALID_LISTING,
                    "listing metadata is not an object",
                    section_id=section_id,
                    source_index=index,
                )
            )
            raw: Mapping[str, Any] = {"value": row}
        else:
            raw = _copy_raw(row)
            value = str(row.get("cat") or "").strip()
            listed_category = value or None
            year_label = str(row.get("hy") or "")
            campus = str(row.get("camps") or "")
            if listed_category is None:
                issues.append(
                    CatalogIssue(
                        IssueCode.INVALID_LISTING,
                        "listing metadata has no category",
                        section_id=section_id,
                        source_index=index,
                    )
                )

        out.append(
            ListingObservation(
                source=source,
                program=program,
                section_id=section_id,
                status=ListingStatus.UNRESOLVED if issues else ListingStatus.OK,
                listed_category=listed_category,
                year_label=year_label,
                campus=campus,
                raw=raw,
                issues=tuple(issues),
            )
        )

    return tuple(out)



def ingest_catalog(
    rows: Iterable[Mapping[str, Any]],
    *,
    source_name: str = "",
    source_kind: str = "portal_catalog",
    term: str = "",
    source_fingerprint: str = "",
    program_listings: Mapping[str, Any] | None = None,
    listing_program: str = "QRM",
    listing_source_name: str = "",
    listing_source_fingerprint: str = "",
) -> CatalogSnapshot:
    """Convert source rows into preserved observations and reconciled physical sections."""

    observations: list[SectionObservation] = []
    for index, raw in enumerate(rows):
        source = SourceRef(
            source_kind=source_kind,
            source_name=source_name,
            term=term,
            source_index=index,
            source_fingerprint=source_fingerprint,
        )
        section_id = _identifier(raw, "subjtnbCorsePrcts")
        course_code = _identifier(raw, "subjtnb")
        issues: list[CatalogIssue] = []
        try:
            section = section_from_raw(raw)
            status = ObservationStatus.PARSED
        except (SectionParseError, TypeError, ValueError) as exc:
            section = None
            status = ObservationStatus.UNRESOLVED
            issues.append(
                CatalogIssue(
                    IssueCode.PARSE_ERROR,
                    f"{type(exc).__name__}: {exc}",
                    section_id=section_id,
                    source_index=index,
                )
            )

        observations.append(
            SectionObservation(
                source=source,
                section_id=section_id,
                course_code=course_code,
                status=status,
                section=section,
                raw=_copy_raw(raw),
                issues=tuple(issues),
            )
        )

    physical_sections = _reconcile(observations)
    listings = _listing_observations(
        program_listings,
        program=listing_program,
        source_name=listing_source_name,
        term=term,
        source_fingerprint=listing_source_fingerprint,
    )

    physical_ids = {record.section_id for record in physical_sections}
    dataset_issues: list[CatalogIssue] = []
    for listing in listings:
        if listing.section_id not in physical_ids:
            dataset_issues.append(
                CatalogIssue(
                    IssueCode.ORPHAN_LISTING,
                    f"{listing.program} listing refers to a section absent from this catalogue source",
                    section_id=listing.section_id,
                    source_index=listing.source.source_index,
                )
            )

    return CatalogSnapshot(
        observations=tuple(observations),
        physical_sections=physical_sections,
        listings=listings,
        issues=tuple(dataset_issues),
        source_name=source_name,
        source_fingerprint=source_fingerprint,
    )



def _rows_from_json_object(obj: Any) -> Sequence[Mapping[str, Any]]:
    """Accept the two catalogue wrappers already observed in this repository."""

    if isinstance(obj, list):
        if not all(isinstance(row, Mapping) for row in obj):
            raise ValueError("catalogue JSON list contains a non-object row")
        return obj
    if isinstance(obj, Mapping) and len(obj) == 1:
        only = next(iter(obj.values()))
        if isinstance(only, list) and all(isinstance(row, Mapping) for row in only):
            return only
    raise ValueError("catalogue JSON must be a list of rows or a one-key wrapper around one")



def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()



def load_catalog_files(
    raw_path: str | Path,
    *,
    program_listings_path: str | Path | None = None,
    listing_program: str = "QRM",
    term: str = "",
) -> CatalogSnapshot:
    """Explicit file-I/O boundary; importing the package never reads or writes these files."""

    raw_path = Path(raw_path)
    with raw_path.open(encoding="utf-8") as fh:
        rows = _rows_from_json_object(json.load(fh))

    program_listings: Mapping[str, Any] | None = None
    listing_name = ""
    listing_fingerprint = ""
    if program_listings_path is not None:
        listing_path = Path(program_listings_path)
        with listing_path.open(encoding="utf-8") as fh:
            obj = json.load(fh)
        if not isinstance(obj, Mapping):
            raise ValueError("program listings JSON must be an object keyed by section id")
        program_listings = obj
        listing_name = str(listing_path)
        listing_fingerprint = _sha256(listing_path)

    return ingest_catalog(
        rows,
        source_name=str(raw_path),
        source_kind="portal_catalog",
        term=term,
        source_fingerprint=_sha256(raw_path),
        program_listings=program_listings,
        listing_program=listing_program,
        listing_source_name=listing_name,
        listing_source_fingerprint=listing_fingerprint,
    )
