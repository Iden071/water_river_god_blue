"""Assemble Stage 4D future inputs and expose exact-search readiness.

This module does not optimize.  It protects the boundary immediately before optimization:
a solver must be able to tell whether its degree structure, timeline assumptions, campus
access, and opportunity sets are complete enough for an exact claim.

A partially observed historical analogue can still be useful for sensitivity analysis or a
heuristic scenario, but it must not silently become the universe over which an exact future
optimum is claimed.
"""

from __future__ import annotations

from dataclasses import dataclass

from .degree_remainder import DegreeRemainder
from .future_opportunities import (
    FutureOpportunityScenario,
    OpportunitySetStatus,
)
from .future_scenarios import (
    CampusAccessKind,
    FutureCatalogueBasisKind,
    FutureTimelineScenario,
    TermActivity,
)


class FutureProblemError(ValueError):
    """Future problem inputs are structurally inconsistent."""


@dataclass(frozen=True)
class FutureProblemBlocker:
    code: str
    message: str
    term_id: str | None = None

    def __post_init__(self) -> None:
        if not self.code.strip() or not self.message.strip():
            raise FutureProblemError("future problem blocker requires code and message")


@dataclass(frozen=True)
class FuturePlanningProblem:
    """Validated Stage 4D inputs before recognition/action generation and search."""

    problem_id: str
    degree_remainder: DegreeRemainder
    timeline: FutureTimelineScenario
    opportunities: FutureOpportunityScenario
    blockers: tuple[FutureProblemBlocker, ...]

    @property
    def exact_search_ready(self) -> bool:
        return not self.blockers

    @property
    def blocker_codes(self) -> frozenset[str]:
        return frozenset(blocker.code for blocker in self.blockers)

    @property
    def has_structural_degree_unknowns(self) -> bool:
        return any(
            blocker.code == "degree_structure_unresolved"
            for blocker in self.blockers
        )


def build_future_planning_problem(
    problem_id: str,
    degree_remainder: DegreeRemainder,
    timeline: FutureTimelineScenario,
    opportunities: FutureOpportunityScenario,
) -> FuturePlanningProblem:
    """Validate future inputs and enumerate why exact optimization is or is not justified."""

    if not problem_id.strip():
        raise FutureProblemError("future planning problem requires problem_id")

    timeline_ids = tuple(term.term_id for term in timeline.terms)
    opportunity_ids = tuple(term.term_id for term in opportunities.terms)
    missing_opportunity_terms = sorted(set(timeline_ids) - set(opportunity_ids))
    extra_opportunity_terms = sorted(set(opportunity_ids) - set(timeline_ids))
    if missing_opportunity_terms or extra_opportunity_terms:
        pieces: list[str] = []
        if missing_opportunity_terms:
            pieces.append("missing=" + ",".join(missing_opportunity_terms))
        if extra_opportunity_terms:
            pieces.append("extra=" + ",".join(extra_opportunity_terms))
        raise FutureProblemError(
            "timeline/opportunity term sets do not match: " + "; ".join(pieces)
        )

    blockers: list[FutureProblemBlocker] = []

    if degree_remainder.structural_unknowns:
        blockers.append(
            FutureProblemBlocker(
                code="degree_structure_unresolved",
                message=(
                    "degree remainder contains unresolved institutional structure: "
                    + ", ".join(sorted(degree_remainder.structural_unknowns))
                ),
            )
        )

    for term in timeline.terms:
        opportunity_set = opportunities.term(term.term_id)

        if term.activity is TermActivity.LEAVE:
            if opportunity_set.status is not OpportunitySetStatus.EXPLICIT_SCENARIO:
                blockers.append(
                    FutureProblemBlocker(
                        code="leave_opportunity_set_not_explicit",
                        term_id=term.term_id,
                        message=(
                            "leave term requires an explicit empty opportunity scenario before exact search"
                        ),
                    )
                )
            elif opportunity_set.offerings:
                blockers.append(
                    FutureProblemBlocker(
                        code="leave_term_has_academic_offerings",
                        term_id=term.term_id,
                        message=(
                            "leave term has zero academic credit capacity but its explicit opportunity set contains offerings"
                        ),
                    )
                )
            continue

        if term.campus_access.kind is CampusAccessKind.UNRESOLVED:
            blockers.append(
                FutureProblemBlocker(
                    code="campus_access_unresolved",
                    term_id=term.term_id,
                    message="active future term has unresolved campus access",
                )
            )

        if term.catalogue_basis.kind is FutureCatalogueBasisKind.UNRESOLVED:
            blockers.append(
                FutureProblemBlocker(
                    code="catalogue_basis_unresolved",
                    term_id=term.term_id,
                    message="active future term has unresolved catalogue basis",
                )
            )

        if opportunity_set.status is OpportunitySetStatus.UNRESOLVED:
            blockers.append(
                FutureProblemBlocker(
                    code="opportunity_set_unresolved",
                    term_id=term.term_id,
                    message="active future term has no resolved opportunity set",
                )
            )
        elif opportunity_set.status is OpportunitySetStatus.PARTIAL:
            blockers.append(
                FutureProblemBlocker(
                    code="opportunity_set_partial",
                    term_id=term.term_id,
                    message=(
                        "future opportunity set is partial; exact optimum over all possible offerings cannot be claimed"
                    ),
                )
            )

        if (
            term.catalogue_basis.kind is FutureCatalogueBasisKind.HISTORICAL_ANALOG
            and opportunity_set.status is OpportunitySetStatus.EXPLICIT_SCENARIO
        ):
            blockers.append(
                FutureProblemBlocker(
                    code="historical_analog_claimed_complete",
                    term_id=term.term_id,
                    message=(
                        "historical-analogue catalogue basis cannot by itself justify a complete future opportunity universe"
                    ),
                )
            )

    return FuturePlanningProblem(
        problem_id=problem_id,
        degree_remainder=degree_remainder,
        timeline=timeline,
        opportunities=opportunities,
        blockers=tuple(blockers),
    )
