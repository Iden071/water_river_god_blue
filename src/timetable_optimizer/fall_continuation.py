"""Bridge one concrete Fall 2026 candidate into the Stage 4D continuation problem.

Stage 4E must optimize the current semester and finite continuation on one objective.  The
first invariant is structural: a Fall candidate's **selected** degree transition determines
the DegreeState from which future obligations are recomputed.  Reusing a future problem
whose degree remainder was calculated before Fall would silently erase the value/cost of
current course choices.

This module therefore rebases the future problem after one candidate while preserving the
same explicit timeline and opportunity scenario.  It does not choose a recognition branch;
if the Fall degree transition is unresolved, exact continuation is blocked rather than
invented.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from .candidate_assessment import CandidateAssessment, CandidateDegreeTransition
from .degree import DegreeScenario
from .degree_remainder import degree_remainder
from .future_problem import FuturePlanningProblem, build_future_planning_problem
from .preferences import PreferenceValue
from .present_utility import PresentTermUtilityAssessment, assess_present_candidate_utility


class FallContinuationError(ValueError):
    """Fall/current-to-future integration inputs are inconsistent."""


class FallContinuationStatus(str, Enum):
    READY = "ready"
    FALL_INFEASIBLE = "fall_infeasible"
    FALL_HARD_UNRESOLVED = "fall_hard_unresolved"
    DEGREE_TRANSITION_UNRESOLVED = "degree_transition_unresolved"
    FUTURE_INPUT_BLOCKED = "future_input_blocked"


@dataclass(frozen=True)
class FallContinuationBridge:
    """One current candidate plus the future problem induced by its resulting degree state."""

    candidate_id: str
    candidate: CandidateAssessment
    present_utility: PresentTermUtilityAssessment
    degree_transition: CandidateDegreeTransition | None
    future_problem: FuturePlanningProblem | None
    status: FallContinuationStatus
    blocker_codes: frozenset[str]

    @property
    def future_search_ready(self) -> bool:
        return (
            self.status is FallContinuationStatus.READY
            and self.future_problem is not None
            and self.future_problem.exact_search_ready
            and self.degree_transition is not None
        )

    @property
    def whole_plan_utility_complete_before_future(self) -> bool:
        """Whether the current-semester part has complete whole-term numerical bounds."""

        return self.present_utility.complete_bounds is not None


def build_fall_continuation_bridge(
    candidate_id: str,
    candidate: CandidateAssessment,
    degree_scenario: DegreeScenario,
    future_template: FuturePlanningProblem,
    *,
    present_term_id: str = "2026F",
    resolved_present_dimensions: Mapping[str, PreferenceValue] | None = None,
) -> FallContinuationBridge:
    """Rebase one future planning template after a selected Fall degree transition.

    ``future_template`` supplies only the continuation timeline/opportunity assumptions.  Its
    degree remainder must correspond to the transition's starting state, which protects
    against accidentally mixing candidates from a different baseline.
    """

    if not candidate_id.strip():
        raise FallContinuationError("Fall continuation bridge requires candidate_id")
    if future_template.degree_remainder.scenario_id != degree_scenario.scenario_id:
        raise FallContinuationError(
            "future template degree scenario does not match supplied degree scenario"
        )

    present = assess_present_candidate_utility(
        candidate,
        term_id=present_term_id,
        resolved_dimensions=resolved_present_dimensions,
    )
    blockers: set[str] = set()

    if candidate.known_infeasible:
        blockers.update(
            f"fall_hard::{issue.code}" for issue in candidate.hard_constraint_violations
        )
        return FallContinuationBridge(
            candidate_id=candidate_id,
            candidate=candidate,
            present_utility=present,
            degree_transition=candidate.degree_transition,
            future_problem=None,
            status=FallContinuationStatus.FALL_INFEASIBLE,
            blocker_codes=frozenset(blockers),
        )

    if candidate.hard_constraint_unknowns:
        blockers.update(
            f"fall_hard::{issue.code}" for issue in candidate.hard_constraint_unknowns
        )

    transition = candidate.degree_transition
    if transition is None:
        blockers.add("fall_degree_transition_not_selected")
        blockers.update(f"fall_future::{item}" for item in candidate.future_unknowns)
        return FallContinuationBridge(
            candidate_id=candidate_id,
            candidate=candidate,
            present_utility=present,
            degree_transition=None,
            future_problem=None,
            status=(
                FallContinuationStatus.FALL_HARD_UNRESOLVED
                if candidate.hard_constraint_unknowns
                else FallContinuationStatus.DEGREE_TRANSITION_UNRESOLVED
            ),
            blocker_codes=frozenset(blockers),
        )

    if transition.scenario_id != degree_scenario.scenario_id:
        raise FallContinuationError(
            "Fall degree transition scenario does not match supplied degree scenario"
        )

    baseline_remainder = degree_remainder(transition.starting_state, degree_scenario)
    if baseline_remainder != future_template.degree_remainder:
        raise FallContinuationError(
            "future template remainder does not correspond to the Fall transition starting state"
        )

    if candidate.future_unknowns:
        blockers.update(f"fall_future::{item}" for item in candidate.future_unknowns)

    rebased = build_future_planning_problem(
        problem_id=f"{future_template.problem_id}::after::{candidate_id}",
        degree_remainder=degree_remainder(
            transition.resulting_state, degree_scenario
        ),
        timeline=future_template.timeline,
        opportunities=future_template.opportunities,
    )
    blockers.update(f"future::{code}" for code in rebased.blocker_codes)

    if candidate.hard_constraint_unknowns:
        status = FallContinuationStatus.FALL_HARD_UNRESOLVED
    elif candidate.future_unknowns:
        status = FallContinuationStatus.DEGREE_TRANSITION_UNRESOLVED
    elif not rebased.exact_search_ready:
        status = FallContinuationStatus.FUTURE_INPUT_BLOCKED
    else:
        status = FallContinuationStatus.READY

    return FallContinuationBridge(
        candidate_id=candidate_id,
        candidate=candidate,
        present_utility=present,
        degree_transition=transition,
        future_problem=rebased,
        status=status,
        blocker_codes=frozenset(blockers),
    )
