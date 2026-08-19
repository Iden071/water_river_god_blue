"""Explicit Fall 2026 candidate-universe contract for Stage 4E.

The legacy rankers mixed three different concepts:

* the canonical Fall catalogue observed from the portal;
* a hand-selected search scope / pool construction;
* the set over which an optimizer could legitimately claim a global optimum.

Those are not interchangeable.  This module keeps them separate.

A full-catalogue universe attempts to cover every physical section represented by the
canonical snapshot.  If a source observation or physical section is unresolved, that is a
global catalogue unknown rather than a section that may be silently dropped.  By contrast,
an explicitly sourced subset may still be exact *within that subset* when unresolved
catalogue material lies outside the chosen scope.  Such a result is necessarily scoped and
cannot be promoted to a global Fall optimum.

Known hard exclusions also require evidence.  The only exclusion inferred here directly
from canonical physical facts is an explicit cancellation flag.  Historical regex filters,
old requirement pools, completed-course lists, advisory year labels, inferred prerequisites,
and other legacy pool-building choices are deliberately not imported.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .catalog import CatalogSnapshot, ObservationStatus, PhysicalStatus
from .sections import Section


class FallUniverseError(ValueError):
    """Fall candidate-universe inputs violate the explicit-scope contract."""


class FallSearchScopeKind(str, Enum):
    FULL_CATALOG = "full_catalog"
    EXPLICIT_SUBSET = "explicit_subset"


class FallUniverseStatus(str, Enum):
    GLOBAL_COMPLETE = "global_complete"
    SCOPED_COMPLETE = "scoped_complete"
    INPUT_BLOCKED = "input_blocked"


@dataclass(frozen=True)
class FallSearchScope:
    """Which canonical Fall sections the caller intentionally asks the search to consider.

    ``FULL_CATALOG`` is the only scope kind eligible for a global-optimum claim.  An
    ``EXPLICIT_SUBSET`` is useful for diagnostics, user shortlists, and staged experiments,
    but its provenance is mandatory and the result remains scoped regardless of quality.
    """

    kind: FallSearchScopeKind
    section_ids: frozenset[str] = frozenset()
    source_id: str = ""
    note: str = ""

    def __post_init__(self) -> None:
        if any(not section_id.strip() for section_id in self.section_ids):
            raise FallUniverseError("Fall search-scope section ids must be nonblank")
        if self.kind is FallSearchScopeKind.FULL_CATALOG:
            if self.section_ids:
                raise FallUniverseError(
                    "full-catalog Fall scope cannot simultaneously name a section subset"
                )
        elif self.kind is FallSearchScopeKind.EXPLICIT_SUBSET:
            if not self.source_id.strip():
                raise FallUniverseError(
                    "explicit Fall section subset requires source_id / provenance"
                )
        else:  # pragma: no cover - Enum protects ordinary construction
            raise FallUniverseError(f"unsupported Fall scope kind: {self.kind!r}")

    @classmethod
    def full_catalog(cls, *, note: str = "") -> "FallSearchScope":
        return cls(FallSearchScopeKind.FULL_CATALOG, note=note)

    @classmethod
    def explicit_subset(
        cls,
        section_ids: frozenset[str] | set[str] | tuple[str, ...] | list[str],
        *,
        source_id: str,
        note: str = "",
    ) -> "FallSearchScope":
        return cls(
            FallSearchScopeKind.EXPLICIT_SUBSET,
            section_ids=frozenset(section_ids),
            source_id=source_id,
            note=note,
        )


@dataclass(frozen=True)
class FallHardExclusionEvidence:
    """Evidence that one physical section cannot belong to the admissible Fall set."""

    section_id: str
    code: str
    reason: str
    source_id: str

    def __post_init__(self) -> None:
        if not self.section_id.strip():
            raise FallUniverseError("hard exclusion requires section_id")
        if not self.code.strip() or not self.reason.strip() or not self.source_id.strip():
            raise FallUniverseError(
                "hard exclusion requires nonblank code, reason, and source_id"
            )


@dataclass(frozen=True)
class FallUniverseUnknown:
    """Catalogue/scope uncertainty that prevents exact section-universe coverage."""

    code: str
    message: str
    section_id: str = ""
    source_index: int | None = None

    def __post_init__(self) -> None:
        if not self.code.strip() or not self.message.strip():
            raise FallUniverseError("Fall universe unknown requires code and message")


@dataclass(frozen=True)
class FallSectionUniverse:
    """Searchable Fall sections plus explicit coverage/exclusion evidence."""

    universe_id: str
    scope: FallSearchScope
    source_name: str
    source_fingerprint: str
    included_sections: tuple[Section, ...]
    hard_exclusions: tuple[FallHardExclusionEvidence, ...]
    scoped_out_section_ids: frozenset[str]
    global_catalogue_unknowns: tuple[FallUniverseUnknown, ...]
    scope_unknowns: tuple[FallUniverseUnknown, ...]
    known_physical_section_ids: frozenset[str]

    def __post_init__(self) -> None:
        if not self.universe_id.strip():
            raise FallUniverseError("Fall section universe requires universe_id")
        included_ids = tuple(section.section_id for section in self.included_sections)
        if len(included_ids) != len(set(included_ids)):
            raise FallUniverseError("Fall section universe contains duplicate physical ids")
        exclusion_ids = tuple(item.section_id for item in self.hard_exclusions)
        if len(exclusion_ids) != len(set(exclusion_ids)):
            raise FallUniverseError("Fall section universe contains duplicate hard exclusions")
        if set(included_ids) & set(exclusion_ids):
            raise FallUniverseError(
                "one section cannot be both searchable and hard-excluded"
            )
        if set(included_ids) - self.known_physical_section_ids:
            raise FallUniverseError(
                "searchable section absent from known physical-section identities"
            )

    @property
    def searchable_section_ids(self) -> frozenset[str]:
        return frozenset(section.section_id for section in self.included_sections)

    @property
    def status(self) -> FallUniverseStatus:
        if self.scope_unknowns:
            return FallUniverseStatus.INPUT_BLOCKED
        if self.scope.kind is FallSearchScopeKind.FULL_CATALOG:
            if self.global_catalogue_unknowns:
                return FallUniverseStatus.INPUT_BLOCKED
            return FallUniverseStatus.GLOBAL_COMPLETE
        return FallUniverseStatus.SCOPED_COMPLETE

    @property
    def exact_scope_coverage(self) -> bool:
        return not self.scope_unknowns

    @property
    def global_catalogue_coverage(self) -> bool:
        return (
            self.scope.kind is FallSearchScopeKind.FULL_CATALOG
            and not self.global_catalogue_unknowns
            and not self.scope_unknowns
        )

    @property
    def eligible_for_global_optimum_claim(self) -> bool:
        """Whether this *section universe* may support a later global-optimum proof.

        This does not say the optimizer has enumerated all timetable subsets yet.  It only
        establishes that the Fall section domain itself is global rather than scoped or
        source-blocked.
        """

        return self.status is FallUniverseStatus.GLOBAL_COMPLETE


def _dedupe_unknowns(items: list[FallUniverseUnknown]) -> tuple[FallUniverseUnknown, ...]:
    out: list[FallUniverseUnknown] = []
    seen: set[FallUniverseUnknown] = set()
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return tuple(out)


def _canonical_cancel_exclusion(section: Section) -> FallHardExclusionEvidence | None:
    if section.cancelled is not True:
        return None
    return FallHardExclusionEvidence(
        section_id=section.section_id,
        code="canonical_cancelled",
        reason="canonical catalogue evidence explicitly marks this section cancelled",
        source_id="canonical:rmvlcYn/rmvlcYnNm",
    )


def build_fall_section_universe(
    universe_id: str,
    snapshot: CatalogSnapshot,
    *,
    scope: FallSearchScope | None = None,
    hard_exclusions: tuple[FallHardExclusionEvidence, ...] = (),
) -> FallSectionUniverse:
    """Build the explicit section domain for a later Fall timetable search.

    Unknown physical/source rows are never converted to absence.  External hard exclusions
    may safely remove a known section only when the caller provides provenance.  Explicit
    cancellation is additionally recognized from the canonical physical section itself.
    """

    scope = scope or FallSearchScope.full_catalog()
    physical_by_id = {record.section_id: record for record in snapshot.physical_sections}
    known_physical_ids = frozenset(physical_by_id)

    external_by_id: dict[str, FallHardExclusionEvidence] = {}
    for exclusion in hard_exclusions:
        if exclusion.section_id in external_by_id:
            raise FallUniverseError(
                f"duplicate external hard exclusion for {exclusion.section_id!r}"
            )
        if exclusion.section_id not in known_physical_ids:
            raise FallUniverseError(
                f"hard exclusion references unknown physical section {exclusion.section_id!r}"
            )
        external_by_id[exclusion.section_id] = exclusion

    global_unknowns: list[FallUniverseUnknown] = []
    for record in snapshot.physical_sections:
        if record.status is PhysicalStatus.UNRESOLVED and record.section_id not in external_by_id:
            global_unknowns.append(
                FallUniverseUnknown(
                    code="physical_section_unresolved",
                    message=(
                        "canonical source rows identify this physical section but do not establish one usable physical-section record"
                    ),
                    section_id=record.section_id,
                )
            )

    physical_observation_indexes = {
        index
        for record in snapshot.physical_sections
        for index in record.observation_indexes
    }
    for observation in snapshot.observations:
        if (
            observation.status is ObservationStatus.UNRESOLVED
            and observation.source.source_index not in physical_observation_indexes
        ):
            global_unknowns.append(
                FallUniverseUnknown(
                    code="source_observation_unidentified",
                    message=(
                        "catalogue source row is unresolved before a trustworthy physical-section identity can be searched"
                    ),
                    section_id=observation.section_id,
                    source_index=observation.source.source_index,
                )
            )

    if scope.kind is FallSearchScopeKind.FULL_CATALOG:
        requested_ids = set(known_physical_ids)
    else:
        requested_ids = set(scope.section_ids)

    scope_unknowns: list[FallUniverseUnknown] = []
    for section_id in sorted(requested_ids - set(known_physical_ids)):
        scope_unknowns.append(
            FallUniverseUnknown(
                code="scope_section_missing",
                message="explicit Fall search scope names a section absent from the canonical physical-section identities",
                section_id=section_id,
            )
        )

    included: list[Section] = []
    exclusions: dict[str, FallHardExclusionEvidence] = dict(external_by_id)

    for section_id in sorted(requested_ids & set(known_physical_ids)):
        record = physical_by_id[section_id]
        external = external_by_id.get(section_id)
        if external is not None:
            exclusions[section_id] = external
            continue
        if not record.usable or record.section is None:
            scope_unknowns.append(
                FallUniverseUnknown(
                    code="scope_physical_section_unresolved",
                    message="requested Fall section has no usable canonical physical-section record",
                    section_id=section_id,
                )
            )
            continue
        canonical_cancel = _canonical_cancel_exclusion(record.section)
        if canonical_cancel is not None:
            exclusions[section_id] = canonical_cancel
            continue
        included.append(record.section)

    scoped_out = frozenset(known_physical_ids - requested_ids)

    # Under full-catalog scope every global source/physical unknown is active.  An explicit
    # subset may remain exact within its own named ids while those global unknowns stay
    # visible as the reason it cannot become a global result.
    if scope.kind is FallSearchScopeKind.FULL_CATALOG:
        scope_unknowns.extend(global_unknowns)

    return FallSectionUniverse(
        universe_id=universe_id,
        scope=scope,
        source_name=snapshot.source_name,
        source_fingerprint=snapshot.source_fingerprint,
        included_sections=tuple(included),
        hard_exclusions=tuple(exclusions[section_id] for section_id in sorted(exclusions) if section_id in requested_ids),
        scoped_out_section_ids=scoped_out,
        global_catalogue_unknowns=_dedupe_unknowns(global_unknowns),
        scope_unknowns=_dedupe_unknowns(scope_unknowns),
        known_physical_section_ids=known_physical_ids,
    )
