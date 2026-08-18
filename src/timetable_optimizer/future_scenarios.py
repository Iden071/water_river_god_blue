"""Explicit future timeline assumptions for Stage 4D.

Future semesters are planning scenarios, not predictions.  This module therefore represents
only assumptions the optimizer is allowed to consume explicitly: which terms exist in the
scenario, whether the user is active or away, ordinary credit capacity, residence state,
campus access, and the epistemic basis for any future catalogue opportunity set.

There is intentionally no ``courses_per_term`` or six-slot abstraction.  Capacity is stated
in credits.  Mixed-campus terms are representable.  An unresolved future catalogue is a
typed unknown rather than an empty catalogue or an assumption that every historical course
will recur.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite


class FutureScenarioError(ValueError):
    """A future planning scenario violates the Stage 4D scenario contract."""


class TermActivity(str, Enum):
    ACTIVE = "active"
    LEAVE = "leave"


class ResidenceState(str, Enum):
    INTERNATIONAL_DORM = "international_dorm"
    HOME = "home"
    OTHER = "other"
    UNRESOLVED = "unresolved"


class CampusAccessKind(str, Enum):
    UNRESOLVED = "unresolved"
    ANY = "any"
    RESTRICTED = "restricted"


@dataclass(frozen=True)
class CampusAccessScenario:
    """Which campuses are permitted by this planning scenario.

    ``ANY`` explicitly permits mixed-campus planning. ``RESTRICTED`` names the allowed
    campuses. ``UNRESOLVED`` means the scenario has not established campus access and must
    not be treated as either unrestricted or impossible.
    """

    kind: CampusAccessKind
    campuses: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        clean = frozenset(campus.strip() for campus in self.campuses if campus.strip())
        if clean != self.campuses:
            object.__setattr__(self, "campuses", clean)
        if self.kind is CampusAccessKind.RESTRICTED and not self.campuses:
            raise FutureScenarioError(
                "restricted campus access requires at least one campus"
            )
        if self.kind is not CampusAccessKind.RESTRICTED and self.campuses:
            raise FutureScenarioError(
                "only restricted campus access may carry an explicit campus set"
            )

    def allows(self, campus: str) -> bool | None:
        name = campus.strip()
        if not name:
            raise FutureScenarioError("campus lookup requires a nonblank campus")
        if self.kind is CampusAccessKind.UNRESOLVED:
            return None
        if self.kind is CampusAccessKind.ANY:
            return True
        return name in self.campuses


class FutureCatalogueBasisKind(str, Enum):
    UNRESOLVED = "unresolved"
    HISTORICAL_ANALOG = "historical_analog"
    EXPLICIT_SCENARIO = "explicit_scenario"


@dataclass(frozen=True)
class FutureCatalogueBasis:
    """Epistemic label for the opportunity set used in a future-term scenario."""

    kind: FutureCatalogueBasisKind
    source_terms: tuple[str, ...] = ()
    note: str = ""

    def __post_init__(self) -> None:
        if self.kind is FutureCatalogueBasisKind.HISTORICAL_ANALOG:
            if not self.source_terms:
                raise FutureScenarioError(
                    "historical catalogue analog requires source term(s)"
                )
        elif self.kind is FutureCatalogueBasisKind.UNRESOLVED:
            if self.source_terms:
                raise FutureScenarioError(
                    "unresolved catalogue basis cannot silently carry source terms"
                )


@dataclass(frozen=True)
class FutureTermScenario:
    """One explicit future planning term.

    The ordinary credit cap is a capacity constraint, not a target.  A valid plan may use
    fewer credits when the finite degree remainder requires fewer.
    """

    term_id: str
    activity: TermActivity
    ordinary_credit_cap: float
    residence: ResidenceState
    campus_access: CampusAccessScenario
    catalogue_basis: FutureCatalogueBasis
    chapel_exempt_from_ordinary_cap: bool = True
    note: str = ""

    def __post_init__(self) -> None:
        if not self.term_id.strip():
            raise FutureScenarioError("future term requires a nonblank term_id")
        if not isfinite(self.ordinary_credit_cap) or self.ordinary_credit_cap < 0:
            raise FutureScenarioError(
                "future ordinary credit cap must be finite and nonnegative"
            )
        if self.activity is TermActivity.LEAVE and self.ordinary_credit_cap != 0:
            raise FutureScenarioError(
                "leave term must have zero ordinary academic credit capacity"
            )

    @property
    def can_host_academic_credits(self) -> bool:
        return self.activity is TermActivity.ACTIVE and self.ordinary_credit_cap > 0


@dataclass(frozen=True)
class FutureTimelineScenario:
    """Finite ordered planning horizon supplied explicitly to the future optimizer."""

    scenario_id: str
    terms: tuple[FutureTermScenario, ...]
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.scenario_id.strip():
            raise FutureScenarioError("future timeline requires a scenario_id")
        if not self.terms:
            raise FutureScenarioError(
                "future timeline must contain at least one explicit term"
            )
        term_ids = [term.term_id for term in self.terms]
        if len(term_ids) != len(set(term_ids)):
            raise FutureScenarioError("future timeline contains duplicate term ids")

    @property
    def ordinary_credit_capacity(self) -> float:
        return sum(term.ordinary_credit_cap for term in self.terms)

    @property
    def active_terms(self) -> tuple[FutureTermScenario, ...]:
        return tuple(term for term in self.terms if term.activity is TermActivity.ACTIVE)

    @property
    def has_unresolved_catalogue(self) -> bool:
        return any(
            term.catalogue_basis.kind is FutureCatalogueBasisKind.UNRESOLVED
            for term in self.terms
            if term.activity is TermActivity.ACTIVE
        )

    @property
    def has_unresolved_campus_access(self) -> bool:
        return any(
            term.campus_access.kind is CampusAccessKind.UNRESOLVED
            for term in self.terms
            if term.activity is TermActivity.ACTIVE
        )
