"""Epistemically explicit future course opportunities for Stage 4D.

A future optimizer needs something it can allocate, but a historical section is not a
prediction that the same section will exist in a future term.  This module therefore wraps
candidate future offerings in an explicit scenario/evidence layer.

Two distinctions are protected:

* an UNRESOLVED opportunity set is not the same thing as a known empty set;
* a historically observed analogue is evidence for a possible scenario offering, not proof
  of future availability.

The objects here remain planning inputs.  They do not yet solve degree recognition or
allocate offerings across terms.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite

from .sections import Schedule


class FutureOpportunityError(ValueError):
    """Future opportunity evidence violates the Stage 4D contract."""


class OpportunitySetStatus(str, Enum):
    """How complete the represented opportunity set is claimed to be."""

    UNRESOLVED = "unresolved"
    PARTIAL = "partial"
    EXPLICIT_SCENARIO = "explicit_scenario"


class FutureOfferingEvidenceKind(str, Enum):
    """Why one scenario offering exists in the planning opportunity set."""

    HISTORICAL_ANALOG = "historical_analog"
    EXPLICIT_ASSUMPTION = "explicit_assumption"


@dataclass(frozen=True)
class FutureOfferingEvidence:
    kind: FutureOfferingEvidenceKind
    source_id: str
    source_term: str | None = None
    source_section_id: str | None = None
    note: str = ""

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise FutureOpportunityError("future offering evidence requires source_id")
        if self.kind is FutureOfferingEvidenceKind.HISTORICAL_ANALOG:
            if not (self.source_term and self.source_term.strip()):
                raise FutureOpportunityError(
                    "historical analogue requires a source term"
                )
            if not (self.source_section_id and self.source_section_id.strip()):
                raise FutureOpportunityError(
                    "historical analogue requires a source section id"
                )


@dataclass(frozen=True)
class FutureOffering:
    """One explicitly hypothesized opportunity in one future term scenario.

    ``offering_id`` is scenario-local identity; it must not reuse historical physical
    identity as though that section literally travels into the future.
    """

    offering_id: str
    term_id: str
    course_code: str
    credits: float | None
    campus: str
    schedule: Schedule
    evidence: FutureOfferingEvidence
    professor: str | None = None

    def __post_init__(self) -> None:
        if not self.offering_id.strip():
            raise FutureOpportunityError("future offering requires offering_id")
        if not self.term_id.strip():
            raise FutureOpportunityError("future offering requires term_id")
        if not self.course_code.strip():
            raise FutureOpportunityError("future offering requires course_code")
        if self.credits is not None and (
            not isfinite(self.credits) or self.credits < 0
        ):
            raise FutureOpportunityError(
                "future offering credits must be finite and nonnegative when known"
            )

    @property
    def is_historical_analogue(self) -> bool:
        return self.evidence.kind is FutureOfferingEvidenceKind.HISTORICAL_ANALOG


@dataclass(frozen=True)
class FutureTermOpportunitySet:
    """Opportunity evidence for one future term without false completeness."""

    term_id: str
    status: OpportunitySetStatus
    offerings: tuple[FutureOffering, ...] = ()
    source_id: str = ""
    note: str = ""

    def __post_init__(self) -> None:
        if not self.term_id.strip():
            raise FutureOpportunityError("future opportunity set requires term_id")
        if self.status is OpportunitySetStatus.UNRESOLVED and self.offerings:
            raise FutureOpportunityError(
                "unresolved opportunity set cannot carry offerings; use PARTIAL when some opportunities are known"
            )
        ids = [offering.offering_id for offering in self.offerings]
        if len(ids) != len(set(ids)):
            raise FutureOpportunityError(
                "future opportunity set contains duplicate offering ids"
            )
        wrong_terms = [
            offering.offering_id
            for offering in self.offerings
            if offering.term_id != self.term_id
        ]
        if wrong_terms:
            raise FutureOpportunityError(
                "future offering term does not match its opportunity set: "
                + ", ".join(wrong_terms)
            )
        if self.status is OpportunitySetStatus.EXPLICIT_SCENARIO and not self.source_id.strip():
            raise FutureOpportunityError(
                "explicit scenario opportunity set requires a source_id describing the assumption"
            )

    @property
    def completeness_known(self) -> bool:
        return self.status is OpportunitySetStatus.EXPLICIT_SCENARIO

    @property
    def known_empty(self) -> bool:
        return (
            self.status is OpportunitySetStatus.EXPLICIT_SCENARIO
            and not self.offerings
        )

    def offerings_for_course(self, course_code: str) -> tuple[FutureOffering, ...]:
        return tuple(
            offering
            for offering in self.offerings
            if offering.course_code == course_code
        )


@dataclass(frozen=True)
class FutureOpportunityScenario:
    """Finite term-indexed opportunity inputs corresponding to a future timeline."""

    scenario_id: str
    terms: tuple[FutureTermOpportunitySet, ...]

    def __post_init__(self) -> None:
        if not self.scenario_id.strip():
            raise FutureOpportunityError("future opportunity scenario requires scenario_id")
        term_ids = [term.term_id for term in self.terms]
        if len(term_ids) != len(set(term_ids)):
            raise FutureOpportunityError(
                "future opportunity scenario contains duplicate term ids"
            )

    def term(self, term_id: str) -> FutureTermOpportunitySet:
        hits = [term for term in self.terms if term.term_id == term_id]
        if len(hits) != 1:
            raise FutureOpportunityError(
                f"expected exactly one opportunity set for term {term_id!r}, found {len(hits)}"
            )
        return hits[0]

    @property
    def has_incomplete_opportunity_sets(self) -> bool:
        return any(not term.completeness_known for term in self.terms)
