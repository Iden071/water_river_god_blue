"""Proof-safe freshman registration screening for the Stage 4E Fall universe.

Registration evidence can shrink the combinatorial Fall domain only when it proves a hard
institutional gate.  This module therefore reuses :func:`assess_freshman_registration` and
classifies each currently searchable section into exactly one of three states:

* **blocked** — an observed nonzero year-quota scheme assigns zero seats to freshmen;
  this may become an auditable hard exclusion before timetable enumeration;
* **resolved nonblocking** — either no year-specific scheme exists or the observed scheme
  assigns a positive freshman quota;
* **unresolved** — no usable quota observation establishes whether a year gate applies.

The last two categories say nothing about actual registration *obtainability*.  Positive
quota is not a success probability, and unresolved gate evidence is never converted into a
hard exclusion.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from .catalog import CatalogSnapshot
from .fall_universe import (
    FallHardExclusionEvidence,
    FallSectionUniverse,
    FallUniverseError,
    build_fall_section_universe,
)
from .registration import (
    RegistrationAssessment,
    RegistrationEvidenceError,
    YearQuotaGateStatus,
    assess_freshman_registration,
)


class FallRegistrationScreeningError(ValueError):
    """Fall registration-screening inputs are inconsistent."""


class FallRegistrationScreeningStatus(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"


@dataclass(frozen=True)
class FallRegistrationScreeningIssue:
    code: str
    message: str
    section_id: str
    source_id: str

    def __post_init__(self) -> None:
        if not self.code.strip() or not self.message.strip() or not self.section_id.strip():
            raise FallRegistrationScreeningError(
                "registration screening issue requires code, message, and section_id"
            )
        if not self.source_id.strip():
            raise FallRegistrationScreeningError(
                "registration screening issue requires source_id"
            )


@dataclass(frozen=True)
class FallRegistrationScreening:
    """Registration gate evidence and the safely reduced Fall section universe."""

    original_universe: FallSectionUniverse
    screened_universe: FallSectionUniverse
    assessments: tuple[RegistrationAssessment, ...]
    new_hard_exclusions: tuple[FallHardExclusionEvidence, ...]
    resolved_nonblocking_section_ids: frozenset[str]
    unresolved_section_ids: frozenset[str]
    issues: tuple[FallRegistrationScreeningIssue, ...]
    source_id: str

    @property
    def status(self) -> FallRegistrationScreeningStatus:
        return (
            FallRegistrationScreeningStatus.PARTIAL
            if self.unresolved_section_ids or self.issues
            else FallRegistrationScreeningStatus.COMPLETE
        )

    @property
    def registration_assessment_map(self) -> dict[str, RegistrationAssessment]:
        return {assessment.section_id: assessment for assessment in self.assessments}

    @property
    def safely_removed_section_ids(self) -> frozenset[str]:
        return frozenset(item.section_id for item in self.new_hard_exclusions)

    @property
    def exact_gate_coverage(self) -> bool:
        return self.status is FallRegistrationScreeningStatus.COMPLETE


def _validate_universe_snapshot(
    universe: FallSectionUniverse,
    snapshot: CatalogSnapshot,
) -> None:
    snapshot_ids = frozenset(record.section_id for record in snapshot.physical_sections)
    if snapshot_ids != universe.known_physical_section_ids:
        raise FallRegistrationScreeningError(
            "Fall registration screening snapshot identities do not match the supplied universe"
        )
    for section in universe.included_sections:
        record = snapshot.record_for(section.section_id)
        if record is None or not record.usable or record.section != section:
            raise FallRegistrationScreeningError(
                f"searchable section {section.section_id!r} does not match canonical snapshot"
            )


def screen_fall_universe_for_freshman_registration(
    universe: FallSectionUniverse,
    snapshot: CatalogSnapshot,
    seat_rows: Mapping[str, Mapping[str, Any]],
    *,
    source_id: str = "fall2026_seats.json",
) -> FallRegistrationScreening:
    """Apply only proven freshman year-gate exclusions to a Fall section universe.

    Invalid quota evidence is retained as an issue and leaves the section searchable; it is
    not interpreted as either permission or prohibition.  Missing rows produce the canonical
    ``NO_OBSERVATION`` assessment, which downstream CandidateAssessment treats as a hard
    feasibility unknown.
    """

    if not source_id.strip():
        raise FallRegistrationScreeningError("registration screening requires source_id")
    _validate_universe_snapshot(universe, snapshot)

    assessments: list[RegistrationAssessment] = []
    exclusions: list[FallHardExclusionEvidence] = []
    resolved_nonblocking: set[str] = set()
    unresolved: set[str] = set()
    issues: list[FallRegistrationScreeningIssue] = []

    for section in universe.included_sections:
        try:
            assessment = assess_freshman_registration(
                section.section_id,
                seat_rows,
                source_id=source_id,
            )
        except RegistrationEvidenceError as exc:
            unresolved.add(section.section_id)
            issues.append(
                FallRegistrationScreeningIssue(
                    code="invalid_year_quota_evidence",
                    message=f"{type(exc).__name__}: {exc}",
                    section_id=section.section_id,
                    source_id=f"{source_id}:{section.section_id}",
                )
            )
            continue

        assessments.append(assessment)
        if assessment.year_quota_status is YearQuotaGateStatus.FRESHMAN_BLOCKED_BY_SCHEME:
            exclusions.append(
                FallHardExclusionEvidence(
                    section_id=section.section_id,
                    code="freshman_year_quota_block",
                    reason=(
                        "observed nonzero year-quota scheme assigns zero seats to first-year students"
                    ),
                    source_id=assessment.quota_source_id or f"{source_id}:{section.section_id}",
                )
            )
        elif assessment.year_quota_status is YearQuotaGateStatus.NO_OBSERVATION:
            unresolved.add(section.section_id)
        elif assessment.year_quota_status in {
            YearQuotaGateStatus.NO_YEAR_SCHEME,
            YearQuotaGateStatus.FRESHMAN_ALLOWED_BY_SCHEME,
        }:
            resolved_nonblocking.add(section.section_id)
        else:  # pragma: no cover - enum exhaustiveness guard
            raise FallRegistrationScreeningError(
                f"unsupported year-quota status {assessment.year_quota_status!r}"
            )

    existing_exclusions = universe.hard_exclusions
    duplicate_ids = {
        item.section_id for item in existing_exclusions
    } & {item.section_id for item in exclusions}
    if duplicate_ids:
        raise FallRegistrationScreeningError(
            "registration screening attempted to exclude section already excluded: "
            + ", ".join(sorted(duplicate_ids))
        )

    try:
        screened = build_fall_section_universe(
            universe.universe_id + ":freshman-registration-screened",
            snapshot,
            scope=universe.scope,
            hard_exclusions=existing_exclusions + tuple(exclusions),
        )
    except FallUniverseError as exc:
        raise FallRegistrationScreeningError(
            f"could not rebuild Fall universe after registration screening: {exc}"
        ) from exc

    return FallRegistrationScreening(
        original_universe=universe,
        screened_universe=screened,
        assessments=tuple(assessments),
        new_hard_exclusions=tuple(exclusions),
        resolved_nonblocking_section_ids=frozenset(resolved_nonblocking),
        unresolved_section_ids=frozenset(unresolved),
        issues=tuple(issues),
        source_id=source_id,
    )
