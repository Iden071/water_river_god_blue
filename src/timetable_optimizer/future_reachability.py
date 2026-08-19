"""Finite degree-reachability search for Stage 4D.

This is the first actual future *search* in the Stage 4 rebuild, but it intentionally has no
utility objective yet.  Its job is narrower and auditable:

    under one explicit finite future scenario, can the evolving canonical DegreeState reach
    degree completion?

The result is three-valued.  A concrete witness proves reachability.  Exhausting every exact
branch proves unreachability.  If a potentially relevant branch is unresolved, or a search
limit is hit, the answer is UNKNOWN rather than a fabricated negative result.

The search enumerates term subsets and delegates all stateful recognition/cap/campus/time
semantics to ``generate_future_term_bundles``.  States are deduplicated after each term for
pure reachability: once two histories produce the same DegreeState, future institutional
possibilities are identical at this layer.  Later utility optimization must retain the
history-dependent utility information separately rather than reusing this deduplication
blindly.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from itertools import combinations
from typing import Mapping

from .degree import DegreeScenario, DegreeState
from .degree_remainder import DegreeRemainder, degree_remainder
from .future_actions import FutureRecognitionEvidence
from .future_opportunities import FutureOffering
from .future_problem import FuturePlanningProblem
from .future_scenarios import TermActivity
from .future_term_bundles import (
    FutureTermBundle,
    FutureTermIssueStatus,
    generate_future_term_bundles,
)


class FutureReachabilityError(ValueError):
    """Future reachability search inputs are inconsistent."""


class FutureReachabilityStatus(str, Enum):
    REACHABLE = "reachable"
    PROVEN_UNREACHABLE = "proven_unreachable"
    INPUT_BLOCKED = "input_blocked"
    UNRESOLVED = "unresolved"
    NODE_LIMIT = "node_limit"


@dataclass(frozen=True)
class FutureTermWitness:
    term_id: str
    offering_ids: tuple[str, ...]
    action_ids: tuple[str, ...]


@dataclass(frozen=True)
class FutureReachabilityWitness:
    steps: tuple[FutureTermWitness, ...]
    resulting_state: DegreeState
    remainder: DegreeRemainder


@dataclass(frozen=True)
class FutureSearchUnknown:
    code: str
    message: str
    term_id: str | None = None
    offering_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class FutureReachabilityResult:
    status: FutureReachabilityStatus
    witness: FutureReachabilityWitness | None
    explored_selections: int
    explored_bundles: int
    frontier_sizes: tuple[tuple[str, int], ...]
    unknowns: tuple[FutureSearchUnknown, ...] = ()
    input_blocker_codes: frozenset[str] = frozenset()

    @property
    def degree_reachable(self) -> bool | None:
        if self.status is FutureReachabilityStatus.REACHABLE:
            return True
        if self.status is FutureReachabilityStatus.PROVEN_UNREACHABLE:
            return False
        return None

    @property
    def proof_complete(self) -> bool:
        return self.status in {
            FutureReachabilityStatus.REACHABLE,
            FutureReachabilityStatus.PROVEN_UNREACHABLE,
        }


def _powerset(offerings: tuple[FutureOffering, ...]):
    for size in range(len(offerings) + 1):
        yield from combinations(offerings, size)


def _bundle_unknowns(bundle: FutureTermBundle) -> tuple[FutureSearchUnknown, ...]:
    unknowns: list[FutureSearchUnknown] = []
    for issue in bundle.hard_unknowns:
        unknowns.append(
            FutureSearchUnknown(
                code=issue.code,
                message=issue.message,
                term_id=bundle.term_id,
                offering_ids=issue.offering_ids,
            )
        )
    for offering_id, requirement_id in sorted(bundle.unresolved_recognition):
        unknowns.append(
            FutureSearchUnknown(
                code="future_recognition_unresolved",
                message=(
                    f"future offering {offering_id!r} has unresolved recognition for requirement {requirement_id!r}"
                ),
                term_id=bundle.term_id,
                offering_ids=(offering_id,),
            )
        )
    return tuple(unknowns)


def _dead_end_is_unresolved(code: str) -> bool:
    """Return whether a no-action reason prevents an exact negative proof."""

    # Explicit evidence that a repeat earns no additional degree credit is a known
    # non-progressing branch.  Other no-action cases (missing credits, unresolved repeat
    # policy, unresolved recognition) are epistemic holes and must block a negative proof.
    return code != "repeat_course_no_additional_degree_credit"


def search_future_degree_reachability(
    problem: FuturePlanningProblem,
    scenario: DegreeScenario,
    starting_state: DegreeState,
    *,
    recognition_evidence: Mapping[str, FutureRecognitionEvidence] | None = None,
    max_selection_evaluations: int = 100_000,
) -> FutureReachabilityResult:
    """Search the finite explicit future scenario for a degree-completion witness.

    ``max_selection_evaluations`` limits term-subset evaluations, not wall-clock time.  If
    the limit is reached before a witness or exhaustive negative proof, the result is
    ``NODE_LIMIT`` and ``degree_reachable`` is ``None``.
    """

    if max_selection_evaluations <= 0:
        raise FutureReachabilityError("max_selection_evaluations must be positive")
    if problem.degree_remainder.scenario_id != scenario.scenario_id:
        raise FutureReachabilityError(
            "future problem degree remainder does not belong to supplied degree scenario"
        )
    actual_remainder = degree_remainder(starting_state, scenario)
    if actual_remainder != problem.degree_remainder:
        raise FutureReachabilityError(
            "future problem degree remainder is stale or does not match starting DegreeState"
        )

    evidence_map = recognition_evidence or {}
    known_offering_ids = {
        offering.offering_id
        for term in problem.opportunities.terms
        for offering in term.offerings
    }
    extra_evidence = sorted(set(evidence_map) - known_offering_ids)
    if extra_evidence:
        raise FutureReachabilityError(
            "recognition evidence references offering(s) outside future problem: "
            + ", ".join(extra_evidence)
        )

    if not problem.exact_search_ready:
        return FutureReachabilityResult(
            status=FutureReachabilityStatus.INPUT_BLOCKED,
            witness=None,
            explored_selections=0,
            explored_bundles=0,
            frontier_sizes=(),
            input_blocker_codes=problem.blocker_codes,
        )

    initial_complete = starting_state.is_degree_complete(scenario)
    if initial_complete is True:
        return FutureReachabilityResult(
            status=FutureReachabilityStatus.REACHABLE,
            witness=FutureReachabilityWitness(
                steps=(),
                resulting_state=starting_state,
                remainder=actual_remainder,
            ),
            explored_selections=0,
            explored_bundles=0,
            frontier_sizes=(),
        )
    if initial_complete is None:
        raise FutureReachabilityError(
            "exact-search-ready problem cannot start from structurally unresolved degree completion"
        )

    # One representative witness per institutional state is sufficient for reachability.
    frontier: dict[DegreeState, tuple[FutureTermWitness, ...]] = {
        starting_state: ()
    }
    frontier_sizes: list[tuple[str, int]] = []
    unknowns: list[FutureSearchUnknown] = []
    explored_selections = 0
    explored_bundles = 0

    for term in problem.timeline.terms:
        opportunity_set = problem.opportunities.term(term.term_id)

        if term.activity is TermActivity.LEAVE:
            next_frontier: dict[DegreeState, tuple[FutureTermWitness, ...]] = {}
            for state, witness in frontier.items():
                step = FutureTermWitness(term.term_id, (), ())
                next_frontier.setdefault(state, witness + (step,))
            frontier = next_frontier
            frontier_sizes.append((term.term_id, len(frontier)))
            continue

        offerings = tuple(
            sorted(opportunity_set.offerings, key=lambda offering: offering.offering_id)
        )
        next_frontier: dict[DegreeState, tuple[FutureTermWitness, ...]] = {}

        for state, witness in frontier.items():
            for subset in _powerset(offerings):
                if explored_selections >= max_selection_evaluations:
                    return FutureReachabilityResult(
                        status=FutureReachabilityStatus.NODE_LIMIT,
                        witness=None,
                        explored_selections=explored_selections,
                        explored_bundles=explored_bundles,
                        frontier_sizes=tuple(frontier_sizes),
                        unknowns=tuple(unknowns),
                    )
                explored_selections += 1

                subset_ids = {offering.offering_id for offering in subset}
                subset_evidence = {
                    offering_id: evidence_map[offering_id]
                    for offering_id in subset_ids
                    if offering_id in evidence_map
                }
                generated = generate_future_term_bundles(
                    term,
                    tuple(subset),
                    scenario,
                    state,
                    recognition_evidence=subset_evidence,
                )

                if generated.known_infeasible:
                    continue

                if generated.static_issues:
                    for issue in generated.static_issues:
                        if issue.status is FutureTermIssueStatus.UNRESOLVED:
                            unknowns.append(
                                FutureSearchUnknown(
                                    code=issue.code,
                                    message=issue.message,
                                    term_id=term.term_id,
                                    offering_ids=issue.offering_ids,
                                )
                            )

                if not generated.bundles:
                    for issue in generated.dead_end_issues:
                        if _dead_end_is_unresolved(issue.code):
                            unknowns.append(
                                FutureSearchUnknown(
                                    code=issue.code,
                                    message=issue.message,
                                    term_id=term.term_id,
                                    offering_ids=tuple(sorted(subset_ids)),
                                )
                            )
                    continue

                for bundle in generated.bundles:
                    explored_bundles += 1
                    if not bundle.exact_transition_ready:
                        unknowns.extend(_bundle_unknowns(bundle))
                        continue

                    step = FutureTermWitness(
                        term_id=term.term_id,
                        offering_ids=bundle.offering_ids,
                        action_ids=tuple(action.action_id for action in bundle.actions),
                    )
                    next_witness = witness + (step,)
                    next_frontier.setdefault(bundle.resulting_state, next_witness)

                    complete = bundle.resulting_state.is_degree_complete(scenario)
                    if complete is True:
                        final_remainder = degree_remainder(
                            bundle.resulting_state, scenario
                        )
                        return FutureReachabilityResult(
                            status=FutureReachabilityStatus.REACHABLE,
                            witness=FutureReachabilityWitness(
                                steps=next_witness,
                                resulting_state=bundle.resulting_state,
                                remainder=final_remainder,
                            ),
                            explored_selections=explored_selections,
                            explored_bundles=explored_bundles,
                            frontier_sizes=tuple(
                                frontier_sizes
                                + [(term.term_id, len(next_frontier))]
                            ),
                            unknowns=tuple(unknowns),
                        )
                    if complete is None:
                        unknowns.append(
                            FutureSearchUnknown(
                                code="degree_completion_unresolved",
                                message=(
                                    "resulting degree state has unresolved completion semantics"
                                ),
                                term_id=term.term_id,
                                offering_ids=bundle.offering_ids,
                            )
                        )

        frontier = next_frontier
        frontier_sizes.append((term.term_id, len(frontier)))

    # Reaching the horizon without a complete state is a negative proof only when every
    # potentially relevant branch was exact and fully explored.
    if unknowns:
        # Preserve first occurrence order while removing exact duplicates.
        deduped: list[FutureSearchUnknown] = []
        seen: set[FutureSearchUnknown] = set()
        for unknown in unknowns:
            if unknown in seen:
                continue
            seen.add(unknown)
            deduped.append(unknown)
        return FutureReachabilityResult(
            status=FutureReachabilityStatus.UNRESOLVED,
            witness=None,
            explored_selections=explored_selections,
            explored_bundles=explored_bundles,
            frontier_sizes=tuple(frontier_sizes),
            unknowns=tuple(deduped),
        )

    return FutureReachabilityResult(
        status=FutureReachabilityStatus.PROVEN_UNREACHABLE,
        witness=None,
        explored_selections=explored_selections,
        explored_bundles=explored_bundles,
        frontier_sizes=tuple(frontier_sizes),
    )
