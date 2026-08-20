"""Proof-safe compression of section-local Fall hard evidence.

The full Fall catalogue may contain many sections whose *individual* hard feasibility is
already unresolved (for example, no freshman year-gate observation) or individually blocked.
Enumerating every timetable that contains such a section repeats the same proof fact across
an enormous number of supersets.

This module compresses only monotone, section-local hard evidence:

* if one section is individually blocked, every timetable containing it is blocked;
* if one section carries an individual hard unknown, every timetable containing it still
  carries that unknown;
* only sections with no such local hard issue enter the expensive combinatorial core.

This is NOT a hidden shortlist and does not make unresolved sections disappear.  Each removed
section is retained as an auditable family certificate covering all candidate supersets that
contain it.  Consequently, unresolved family certificates still block a global optimum claim
until their evidence is resolved.  Non-local facts (time conflicts, cross-campus transitions,
degree recognition interactions, objective utility) are deliberately left to later search.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from .fall_universe import FallSearchScope, FallSectionUniverse
from .registration import RegistrationAssessment, YearQuotaGateStatus
from .sections import ParsedSchedule, Section


class FallLocalHardPartitionError(ValueError):
    """Local-hard partition inputs violate the coverage contract."""


class FallLocalHardIssueStatus(str, Enum):
    KNOWN_BLOCK = "known_block"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class FallLocalHardIssue:
    section_id: str
    code: str
    status: FallLocalHardIssueStatus
    message: str
    source_id: str

    def __post_init__(self) -> None:
        if not self.section_id.strip() or not self.code.strip():
            raise FallLocalHardPartitionError(
                "local hard issue requires section_id and code"
            )
        if not self.message.strip() or not self.source_id.strip():
            raise FallLocalHardPartitionError(
                "local hard issue requires message and source_id"
            )


@dataclass(frozen=True)
class FallLocalHardFamilyCertificate:
    """One section-local proof certificate covering every candidate that selects it."""

    section_id: str
    issues: tuple[FallLocalHardIssue, ...]

    def __post_init__(self) -> None:
        if not self.section_id.strip() or not self.issues:
            raise FallLocalHardPartitionError(
                "family certificate requires section_id and at least one issue"
            )
        if any(issue.section_id != self.section_id for issue in self.issues):
            raise FallLocalHardPartitionError(
                "family certificate contains issue for another section"
            )

    @property
    def known_blocked(self) -> bool:
        return any(
            issue.status is FallLocalHardIssueStatus.KNOWN_BLOCK
            for issue in self.issues
        )

    @property
    def unresolved(self) -> bool:
        return not self.known_blocked and any(
            issue.status is FallLocalHardIssueStatus.UNRESOLVED
            for issue in self.issues
        )


@dataclass(frozen=True)
class FallLocalHardPartition:
    """Section-domain coverage split for a later exact combinatorial search."""

    original_universe: FallSectionUniverse
    resolved_core_universe: FallSectionUniverse
    blocked_families: tuple[FallLocalHardFamilyCertificate, ...]
    unresolved_families: tuple[FallLocalHardFamilyCertificate, ...]

    def __post_init__(self) -> None:
        original_ids = self.original_universe.searchable_section_ids
        core_ids = self.resolved_core_universe.searchable_section_ids
        blocked_ids = frozenset(item.section_id for item in self.blocked_families)
        unresolved_ids = frozenset(item.section_id for item in self.unresolved_families)

        if len(blocked_ids) != len(self.blocked_families):
            raise FallLocalHardPartitionError("duplicate blocked family section id")
        if len(unresolved_ids) != len(self.unresolved_families):
            raise FallLocalHardPartitionError("duplicate unresolved family section id")
        if core_ids & blocked_ids or core_ids & unresolved_ids or blocked_ids & unresolved_ids:
            raise FallLocalHardPartitionError(
                "local-hard partition classes must be pairwise disjoint"
            )
        if core_ids | blocked_ids | unresolved_ids != original_ids:
            raise FallLocalHardPartitionError(
                "local-hard partition must account for every searchable section exactly once"
            )
        if any(not item.known_blocked for item in self.blocked_families):
            raise FallLocalHardPartitionError(
                "blocked family lacks a known-block issue"
            )
        if any(not item.unresolved for item in self.unresolved_families):
            raise FallLocalHardPartitionError(
                "unresolved family must contain unresolved issues and no known block"
            )

    @property
    def full_section_coverage(self) -> bool:
        return True

    @property
    def unresolved_family_section_ids(self) -> frozenset[str]:
        return frozenset(item.section_id for item in self.unresolved_families)

    @property
    def blocked_family_section_ids(self) -> frozenset[str]:
        return frozenset(item.section_id for item in self.blocked_families)

    @property
    def resolved_core_section_ids(self) -> frozenset[str]:
        return self.resolved_core_universe.searchable_section_ids

    @property
    def global_optimum_blocked_by_local_unknowns(self) -> bool:
        return bool(self.unresolved_families)


def _local_issues(
    section: Section,
    registration_assessments: Mapping[str, RegistrationAssessment],
) -> tuple[FallLocalHardIssue, ...]:
    issues: list[FallLocalHardIssue] = []

    if section.cancelled is True:
        issues.append(
            FallLocalHardIssue(
                section.section_id,
                "section_cancelled",
                FallLocalHardIssueStatus.KNOWN_BLOCK,
                "canonical catalogue evidence marks this section cancelled",
                "canonical cancelled flag",
            )
        )
    elif section.cancelled is None:
        issues.append(
            FallLocalHardIssue(
                section.section_id,
                "cancellation_status_unresolved",
                FallLocalHardIssueStatus.UNRESOLVED,
                "section cancellation status is not established",
                "canonical cancelled flag",
            )
        )

    if section.credits is None:
        issues.append(
            FallLocalHardIssue(
                section.section_id,
                "ordinary_credit_cap_unresolved",
                FallLocalHardIssueStatus.UNRESOLVED,
                "section credits are unknown, so any selected timetable containing it has unresolved credit-cap compliance",
                "canonical section credits",
            )
        )

    if not isinstance(section.schedule, ParsedSchedule):
        issues.append(
            FallLocalHardIssue(
                section.section_id,
                "schedule_unresolved",
                FallLocalHardIssueStatus.UNRESOLVED,
                "section schedule is not safely parsed; every timetable containing it retains unresolved conflict feasibility",
                type(section.schedule).__name__,
            )
        )

    registration = registration_assessments.get(section.section_id)
    if registration is None:
        issues.append(
            FallLocalHardIssue(
                section.section_id,
                "registration_gate_unassessed",
                FallLocalHardIssueStatus.UNRESOLVED,
                "no section-specific freshman registration-gate assessment was supplied",
                "Stage 4 registration evidence",
            )
        )
    else:
        if registration.section_id != section.section_id:
            raise FallLocalHardPartitionError(
                f"registration assessment key/section mismatch for {section.section_id!r}"
            )
        if registration.year_quota_status is YearQuotaGateStatus.FRESHMAN_BLOCKED_BY_SCHEME:
            issues.append(
                FallLocalHardIssue(
                    section.section_id,
                    "registration_year_gate_block",
                    FallLocalHardIssueStatus.KNOWN_BLOCK,
                    "observed year-quota scheme blocks this section for a freshman",
                    registration.quota_source_id or "registration assessment",
                )
            )
        elif registration.year_quota_status is YearQuotaGateStatus.NO_OBSERVATION:
            issues.append(
                FallLocalHardIssue(
                    section.section_id,
                    "registration_year_gate_unresolved",
                    FallLocalHardIssueStatus.UNRESOLVED,
                    "no section-specific year-quota observation establishes whether a freshman gate applies",
                    registration.quota_source_id or "Stage 4 registration evidence",
                )
            )
        elif registration.year_quota_status not in {
            YearQuotaGateStatus.NO_YEAR_SCHEME,
            YearQuotaGateStatus.FRESHMAN_ALLOWED_BY_SCHEME,
        }:
            raise FallLocalHardPartitionError(
                f"unsupported year-quota status {registration.year_quota_status!r}"
            )

    return tuple(issues)


def partition_fall_universe_by_local_hard_evidence(
    universe: FallSectionUniverse,
    *,
    registration_assessments: Mapping[str, RegistrationAssessment] | None = None,
) -> FallLocalHardPartition:
    """Compress monotone section-local hard evidence without losing catalogue coverage.

    The returned ``resolved_core_universe`` is intentionally an explicit derived subset and
    therefore cannot, by itself, support a global-optimum claim.  A later wrapper must combine
    its exact search result with the blocked/unresolved family certificates and the original
    universe coverage.
    """

    registration_map = registration_assessments or {}
    resolved: list[Section] = []
    blocked: list[FallLocalHardFamilyCertificate] = []
    unresolved: list[FallLocalHardFamilyCertificate] = []

    for section in sorted(universe.included_sections, key=lambda item: item.section_id):
        issues = _local_issues(section, registration_map)
        if not issues:
            resolved.append(section)
            continue
        certificate = FallLocalHardFamilyCertificate(section.section_id, issues)
        if certificate.known_blocked:
            blocked.append(certificate)
        else:
            unresolved.append(certificate)

    resolved_ids = frozenset(section.section_id for section in resolved)
    core_scope = FallSearchScope.explicit_subset(
        resolved_ids,
        source_id="derived:fall-local-hard-partition-v1",
        note=(
            "Derived exact-search core after preserving section-local blocked/unresolved "
            "families as separate coverage certificates; not a user shortlist."
        ),
    )
    resolved_core = FallSectionUniverse(
        universe_id=universe.universe_id + ":local-hard-resolved-core",
        scope=core_scope,
        source_name=universe.source_name,
        source_fingerprint=universe.source_fingerprint,
        included_sections=tuple(resolved),
        hard_exclusions=(),
        scoped_out_section_ids=frozenset(
            universe.known_physical_section_ids - resolved_ids
        ),
        global_catalogue_unknowns=universe.global_catalogue_unknowns,
        scope_unknowns=(),
        known_physical_section_ids=universe.known_physical_section_ids,
    )

    return FallLocalHardPartition(
        original_universe=universe,
        resolved_core_universe=resolved_core,
        blocked_families=tuple(blocked),
        unresolved_families=tuple(unresolved),
    )
