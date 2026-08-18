"""Historical catalogue ingestion built on the same canonical parser as current data.

There is deliberately no historical schedule grammar in this module.  ``past_terms.json``
contains portal rows of the same structural kind as the current catalogue, so every term is
fed through :func:`timetable_optimizer.catalog.ingest_catalog` unchanged.

Terms are reconciled independently.  A section id repeated in 2024-1 and 2025-1 is therefore
two historical observations in two catalogues, not a duplicate-section conflict.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .catalog import CatalogSnapshot, ingest_catalog
from .sections import NoListedSchedule, ParsedSchedule, UnresolvedSchedule


@dataclass(frozen=True)
class HistoricalTerm:
    term: str
    catalog: CatalogSnapshot


@dataclass(frozen=True)
class HistorySummary:
    term_count: int
    observation_count: int
    physical_section_count: int
    unresolved_observation_count: int
    unresolved_physical_count: int
    parsed_schedule_count: int
    no_listed_schedule_count: int
    unresolved_schedule_count: int
    campuses: tuple[str, ...]
    delivery_counts: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class HistorySnapshot:
    terms: tuple[HistoricalTerm, ...]
    source_name: str = ""
    source_fingerprint: str = ""

    @property
    def term_labels(self) -> tuple[str, ...]:
        return tuple(item.term for item in self.terms)

    def term(self, label: str) -> CatalogSnapshot | None:
        hits = [item.catalog for item in self.terms if item.term == label]
        return hits[0] if len(hits) == 1 else None

    def summary(self) -> HistorySummary:
        observation_count = 0
        physical_section_count = 0
        unresolved_observation_count = 0
        unresolved_physical_count = 0
        parsed_schedule_count = 0
        no_listed_schedule_count = 0
        unresolved_schedule_count = 0
        campuses: set[str] = set()
        delivery = Counter()

        for historical_term in self.terms:
            catalog = historical_term.catalog
            observation_count += len(catalog.observations)
            physical_section_count += len(catalog.physical_sections)
            unresolved_observation_count += sum(
                1 for observation in catalog.observations if observation.section is None
            )
            unresolved_physical_count += len(catalog.unresolved_physical_sections)

            for section in catalog.sections:
                if section.campus:
                    campuses.add(section.campus)
                schedule = section.schedule
                if isinstance(schedule, ParsedSchedule):
                    parsed_schedule_count += 1
                    delivery.update(segment.delivery_kind.value for segment in schedule.segments)
                elif isinstance(schedule, NoListedSchedule):
                    no_listed_schedule_count += 1
                elif isinstance(schedule, UnresolvedSchedule):
                    unresolved_schedule_count += 1
                else:  # defensive: the Schedule union should be exhaustive
                    raise TypeError(f"unknown schedule type: {type(schedule)!r}")

        return HistorySummary(
            term_count=len(self.terms),
            observation_count=observation_count,
            physical_section_count=physical_section_count,
            unresolved_observation_count=unresolved_observation_count,
            unresolved_physical_count=unresolved_physical_count,
            parsed_schedule_count=parsed_schedule_count,
            no_listed_schedule_count=no_listed_schedule_count,
            unresolved_schedule_count=unresolved_schedule_count,
            campuses=tuple(sorted(campuses)),
            delivery_counts=tuple(sorted(delivery.items())),
        )


def _term_rows(value: Any, term: str) -> Sequence[Mapping[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"historical term {term!r} must contain a list of portal rows")
    if not all(isinstance(row, Mapping) for row in value):
        raise ValueError(f"historical term {term!r} contains a non-object row")
    return value


def _json_fingerprint(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ingest_history(
    term_rows: Mapping[str, Any],
    *,
    source_name: str = "",
    source_fingerprint: str = "",
) -> HistorySnapshot:
    """Ingest every historical term through the canonical catalogue parser.

    The outer mapping provides temporal separation only.  No schedule, presence, delivery,
    eligibility, or degree semantics are reconstructed here.
    """

    terms: list[HistoricalTerm] = []
    for raw_label in sorted(term_rows, key=str):
        term = str(raw_label)
        rows = _term_rows(term_rows[raw_label], term)
        term_fingerprint = _json_fingerprint(rows)
        term_source_name = f"{source_name}#{term}" if source_name else term
        catalog = ingest_catalog(
            rows,
            source_name=term_source_name,
            source_kind="historical_portal_catalog",
            term=term,
            source_fingerprint=term_fingerprint,
        )
        terms.append(HistoricalTerm(term=term, catalog=catalog))

    return HistorySnapshot(
        terms=tuple(terms),
        source_name=source_name,
        source_fingerprint=source_fingerprint,
    )


def load_history_file(path: str | Path) -> HistorySnapshot:
    """Explicit file-I/O boundary for the historical catalogue collection."""

    path = Path(path)
    with path.open(encoding="utf-8") as fh:
        obj = json.load(fh)
    if not isinstance(obj, Mapping):
        raise ValueError("historical catalogue JSON must be an object keyed by term")
    return ingest_history(
        obj,
        source_name=str(path),
        source_fingerprint=_file_sha256(path),
    )
