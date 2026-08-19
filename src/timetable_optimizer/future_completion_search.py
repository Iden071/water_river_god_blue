"""Exhaustive finite completion-history enumeration for Stage 4D.

``future_reachability`` answers the existential question "does at least one path graduate?"
and may safely deduplicate equal institutional states.  Utility optimization needs a stricter
carrier: two histories can reach the same ``DegreeState`` while having different timetable
and course utility.  This module therefore enumerates concrete degree-completion histories
without state-only deduplication and without any utility pruning.

The result is proof-aware.  Exact histories found so far are retained even if another branch
is unresolved, but the enumeration is called complete only when every potentially relevant
branch was exact and exhaustively searched.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from itertools import combinations
from typing import Mapping

from .degree import DegreeScenario, DegreeState
from .degree_remainder import degree_remainder
from .future_actions import FutureRecognitionEvidence
from .future_opportunities import FutureOffering
from .future_problem import FuturePlanningProblem
from .future_reachability import (
    FutureReachabilityWitness,
    FutureSearchUnknown,
    FutureTermWitness,
)
from .future_scenarios import TermActivity
from .future_term_bundles import (
    FutureTermBundle,
    FutureTermIssueStatus,
    generate_future_term_bundles,
)


class FutureCompletionSearchError(ValueError):
    """Completion-history enumeration inputs are inconsistent."""


class FutureCompletionSearchStatus(str, Enum):
    COMPLETE = "complete"
    PROVEN_UNREACHABLE = "proven_unreachable"
    INPUT_BLOCKED = "input_blocked"
    UNRESOLVED = "unresolved"
    NODE_LIMIT = "node_limit"


@dataclass(frozen=True)
class FutureCompletionSearchResult:
    status: FutureCompletionSearchStatus
    witnesses: tuple[FutureReachabilityWitness, ...]
    explored_selections: int
    explored_bundles: int
    frontier_sizes: tuple[tuple[str, int], ...]
    unknowns: tuple[FutureSearchUnknown, ...] = ()
    input_blocker_codes: frozenset[str] = frozenset()

    @property
    def enumeration_complete(self) -> bool:
        return self.status in {
            FutureCompletionSearchStatus.COMPLETE,
            FutureCompletionSearchStatus.PROVEN_UNREACHABLE,
        }

    @property
    def any_completion_found(self) -> bool:
        return bool(self.witnesses)


@dataclass(frozen=True)
class _OpenHistory:
    state: DegreeState
    steps: tuple[FutureTermWitness, ...]


def _powerset(offerings: tuple[FutureOffering, ...]):
    for size in range(len(offerings) + 1):
        yield from combinations(offerings, size)


def _bundle_unknowns(bundle: FutureTermBundle) -> tuple[FutureSearchUnknown, ...]:
    out: list[FutureSearchUnknown] = []
    for issue in bundle.hard_unknowns:
        out.append(
            FutureSearchUnknown(
                code=issue.code,
                message=issue.message,
                term_id=bundle.term_id,
                offering_ids=issue.offering_ids,
            )
        )
    for offering_id, requirement_id in sorted(bundle.unresolved_recognition):
        out.append(
            FutureSearchUnknown(
                code="future_recognition_unresolved",
                message=(
                    f"future offering {offering_id!r} has unresolved recognition for requirement {requirement_id!r}"
                ),
                term_id=bundle.term_id,
                offering_ids=(offering_id,),
            )
        )
    return tuple(out)


def _dead_end_is_unresolved(code: str) -> bool:
    # Explicit evidence that a repeat grants no additional degree credit is a known dead
    # branch. Missing credits, repeat policy, or recognition evidence are epistemic holes.
    return code != "repeat_course_no_additional_degree_credit"


def _dedupe_unknowns(
    unknowns: list[FutureSearchUnknown],
) -> tuple[FutureSearchUnknown, ...]:
    out: list[FutureSearchUnknown] = []
    seen: set[FutureSearchUnknown] = set()
    for unknown in unknowns:
        if unknown in seen:
            continue
        seen.add(unknown)
        out.append(unknown)
    return tuple(out)


def enumerate_future_degree_completion_histories(
    problem: FuturePlanningProblem,
    scenario: DegreeScenario,
    starting_state: DegreeState,
    *,
    recognition_evidence: Mapping[str, FutureRecognitionEvidence] | None = None,
    max_selection_evaluations: int = 100_000,
) -> FutureCompletionSearchResult:
    """Enumerate every exact degree-completion history inside one finite scenario.

    No utility-based pruning is performed.  A path stops when it first reaches degree
    completion; later timeline terms are outside that academic completion history rather than
    being fabricated as empty post-graduation semesters.
    """

    if max_selection_evaluations <= 0:
        raise FutureCompletionSearchError(
            "max_selection_evaluations must be positive"
        )
    if problem.degree_remainder.scenario_id != scenario.scenario_id:
        raise FutureCompletionSearchError(
            "future problem degree remainder does not belong to supplied degree scenario"
        )
    actual_remainder = degree_remainder(starting_state, scenario)
    if actual_remainder != problem.degree_remainder:
        raise FutureCompletionSearchError(
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
        raise FutureCompletionSearchError(
            "recognition evidence references offering(s) outside future problem: "
            + ", ".join(extra_evidence)
        )

    if not problem.exact_search_ready:
        return FutureCompletionSearchResult(
            status=FutureCompletionSearchStatus.INPUT_BLOCKED,
            witnesses=(),
            explored_selections=0,
            explored_bundles=0,
            frontier_sizes=(),
            input_blocker_codes=problem.blocker_codes,
        )

    initial_complete = starting_state.is_degree_complete(scenario)
    if initial_complete is True:
        return FutureCompletionSearchResult(
            status=FutureCompletionSearchStatus.COMPLETE,
            witnesses=(
                FutureReachabilityWitness(
                    steps=(),
                    resulting_state=starting_state,
                    remainder=actual_remainder,
                ),
            ),
            explored_selections=0,
            explored_bundles=0,
            frontier_sizes=(),
        )
    if initial_complete is None:
        raise FutureCompletionSearchError(
            "exact-search-ready problem cannot start from unresolved degree completion"
        )

    frontier: list[_OpenHistory] = [_OpenHistory(starting_state, ())]
    completed: list[FutureReachabilityWitness] = []
    unknowns: list[FutureSearchUnknown] = []
    frontier_sizes: list[tuple[str, int]] = []
    explored_selections = 0
    explored_bundles = 0

    for term in problem.timeline.terms:
        opportunity_set = problem.opportunities.term(term.term_id)

        if term.activity is TermActivity.LEAVE:
            frontier = [
                _OpenHistory(
                    history.state,
                    history.steps + (FutureTermWitness(term.term_id, (), ()),),
                )
                for history in frontier
            ]
            frontier_sizes.append((term.term_id, len(frontier)))
            continue

        offerings = tuple(
            sorted(opportunity_set.offerings, key=lambda offering: offering.offering_id)
        )
        next_frontier: list[_OpenHistory] = []

        for history in frontier:
            for subset in _powerset(offerings):
                if explored_selections >= max_selection_evaluations:
                    return FutureCompletionSearchResult(
                        status=FutureCompletionSearchStatus.NODE_LIMIT,
                        witnesses=tuple(completed),
                        explored_selections=explored_selections,
                        explored_bundles=explored_bundles,
                        frontier_sizes=tuple(frontier_sizes),
                        unknowns=_dedupe_unknowns(unknowns),
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
                    history.state,
                    recognition_evidence=subset_evidence,
                )

                if generated.known_infeasible:
                    continue

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
                    steps = history.steps + (step,)
                    complete = bundle.resulting_state.is_degree_complete(scenario)

                    if complete is True:
                        completed.append(
                            FutureReachabilityWitness(
                                steps=steps,
                                resulting_state=bundle.resulting_state,
                                remainder=degree_remainder(
                                    bundle.resulting_state, scenario
                                ),
                            )
                        )
                        continue
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
                        continue

                    next_frontier.append(
                        _OpenHistory(bundle.resulting_state, steps)
                    )

        frontier = next_frontier
        frontier_sizes.append((term.term_id, len(frontier)))
        if not frontier:
            # All still-open exact histories either completed or died.  Remaining timeline
            # terms cannot create new histories from nothing.
            break

    deduped_unknowns = _dedupe_unknowns(unknowns)
    if deduped_unknowns:
        return FutureCompletionSearchResult(
            status=FutureCompletionSearchStatus.UNRESOLVED,
            witnesses=tuple(completed),
            explored_selections=explored_selections,
            explored_bundles=explored_bundles,
            frontier_sizes=tuple(frontier_sizes),
            unknowns=deduped_unknowns,
        )

    if completed:
        return FutureCompletionSearchResult(
            status=FutureCompletionSearchStatus.COMPLETE,
            witnesses=tuple(completed),
            explored_selections=explored_selections,
            explored_bundles=explored_bundles,
            frontier_sizes=tuple(frontier_sizes),
        )

    return FutureCompletionSearchResult(
        status=FutureCompletionSearchStatus.PROVEN_UNREACHABLE,
        witnesses=(),
        explored_selections=explored_selections,
        explored_bundles=explored_bundles,
        frontier_sizes=tuple(frontier_sizes),
    )
