"""Attach future utility evidence to a concrete reachability witness.

The reachability solver and utility evaluator deliberately remain separate.  A reachability
witness proves an institutional path under the explicit future scenario; this module maps
that exact selected-offering history back onto the scenario's opportunity sets and evaluates
each academic term without changing the witness or its DegreeState transitions.

A reachability witness may end before the planning horizon when the degree is completed
early.  In that case the witness must be an exact *prefix* of the timeline.  Terms after
degree completion are not fabricated as empty academic timetables: doing so would turn
post-graduation non-participation into artificial free-day utility.  Comparison of histories
with different completion horizons therefore remains a later preference question unless
graduation timing is explicitly valued.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .course_preferences import ProfessorRatingBook
from .future_problem import FuturePlanningProblem
from .future_reachability import FutureReachabilityWitness
from .future_utility import (
    FutureUtilityHistory,
    assess_future_term_utility,
)
from .preferences import PreferenceProfile, PreferenceValue


class FutureWitnessUtilityError(ValueError):
    """Reachability witness and future scenario are inconsistent for utility evaluation."""


@dataclass(frozen=True)
class FutureWitnessUtilityAssessment:
    witness: FutureReachabilityWitness
    utility_history: FutureUtilityHistory

    @property
    def completion_term_id(self) -> str | None:
        return self.utility_history.term_ids[-1] if self.utility_history.term_ids else None


def assess_future_witness_utility(
    problem: FuturePlanningProblem,
    witness: FutureReachabilityWitness,
    preference_profile: PreferenceProfile,
    professor_ratings: ProfessorRatingBook,
    *,
    subject_interest: Mapping[str, PreferenceValue] | None = None,
    workload_utility: Mapping[str, PreferenceValue] | None = None,
    difficulty_utility: Mapping[str, PreferenceValue] | None = None,
) -> FutureWitnessUtilityAssessment:
    """Evaluate the selected offerings in one concrete finite reachability witness.

    ``witness.steps`` must match the planning timeline from its first term through the term
    in which the witness completes the degree.  It may be shorter than the full timeline,
    but it may not skip, reorder, or start after timeline terms.
    """

    timeline_ids = tuple(term.term_id for term in problem.timeline.terms)
    witness_ids = tuple(step.term_id for step in witness.steps)
    if len(witness_ids) > len(timeline_ids) or witness_ids != timeline_ids[: len(witness_ids)]:
        raise FutureWitnessUtilityError(
            "reachability witness term sequence must be an exact prefix of the future planning timeline"
        )

    term_assessments = []
    for term, step in zip(problem.timeline.terms, witness.steps):
        opportunity_set = problem.opportunities.term(term.term_id)
        by_id = {offering.offering_id: offering for offering in opportunity_set.offerings}
        if len(by_id) != len(opportunity_set.offerings):
            raise FutureWitnessUtilityError(
                f"future opportunity set {term.term_id!r} contains duplicate offering ids"
            )
        if len(step.offering_ids) != len(set(step.offering_ids)):
            raise FutureWitnessUtilityError(
                f"reachability witness term {term.term_id!r} repeats an offering id"
            )
        missing = sorted(set(step.offering_ids) - set(by_id))
        if missing:
            raise FutureWitnessUtilityError(
                "reachability witness references offering(s) outside the scenario: "
                + ", ".join(missing)
            )

        selected = tuple(by_id[offering_id] for offering_id in step.offering_ids)
        term_assessments.append(
            assess_future_term_utility(
                term,
                selected,
                preference_profile,
                professor_ratings,
                subject_interest=subject_interest,
                workload_utility=workload_utility,
                difficulty_utility=difficulty_utility,
            )
        )

    return FutureWitnessUtilityAssessment(
        witness=witness,
        utility_history=FutureUtilityHistory(tuple(term_assessments)),
    )
