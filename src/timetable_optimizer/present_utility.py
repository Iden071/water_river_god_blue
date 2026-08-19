"""Non-lossy present-term utility for Stage 4E.

``CandidateAssessment`` is the Stage 4C evidence integration boundary.  Stage 4E needs one
additional projection: convert the preference evidence that is already numerical into the
same interval/heuristic/unresolved utility semantics used by the future optimizer, without
turning missing registration, travel, professor, workload, or difficulty evidence into zero.

This module deliberately does **not** decide hard feasibility or degree recognition.  Those
remain properties of the candidate/transition.  A whole-plan numerical bound is available
only when both preference evidence and hard feasibility are resolved.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .candidate_assessment import CandidateAssessment
from .preferences import EstimateStatus, PreferenceValue
from .timetable_utility import UtilityContribution


class PresentUtilityError(ValueError):
    """Present-term utility inputs violate the Stage 4E objective contract."""


@dataclass(frozen=True)
class PresentTermUtilityAssessment:
    """Current-semester utility evidence on the common Stage 4 utility scale."""

    term_id: str
    section_ids: tuple[str, ...]
    contributions: tuple[UtilityContribution, ...]
    measured_lower: float
    measured_upper: float
    heuristic_point_delta: float
    unresolved_dimensions: frozenset[str]
    known_infeasible: bool
    hard_feasibility_resolved: bool

    @property
    def has_heuristics(self) -> bool:
        return any(
            contribution.status is EstimateStatus.HEURISTIC
            for contribution in self.contributions
        )

    @property
    def has_unresolved(self) -> bool:
        return bool(self.unresolved_dimensions)

    @property
    def complete_bounds(self) -> tuple[float, float] | None:
        """Whole present-term bounds only when both utility and feasibility are resolved."""

        if (
            self.known_infeasible
            or not self.hard_feasibility_resolved
            or self.has_heuristics
            or self.has_unresolved
        ):
            return None
        return (self.measured_lower, self.measured_upper)


def _preference_contribution(
    value: PreferenceValue,
    *,
    dimension_id: str,
) -> UtilityContribution | None:
    estimate = value.estimate
    if estimate.status is EstimateStatus.UNMEASURED:
        return None
    if estimate.status is EstimateStatus.EXACT:
        assert estimate.point is not None
        return UtilityContribution(
            dimension_id=dimension_id,
            quantity=1.0,
            status=estimate.status,
            lower=estimate.point,
            upper=estimate.point,
            point=estimate.point,
            provenance=value.provenance,
            label=value.label,
        )
    if estimate.status is EstimateStatus.BOUNDED:
        assert estimate.lower is not None and estimate.upper is not None
        return UtilityContribution(
            dimension_id=dimension_id,
            quantity=1.0,
            status=estimate.status,
            lower=estimate.lower,
            upper=estimate.upper,
            provenance=value.provenance,
            label=value.label,
        )
    if estimate.status is EstimateStatus.HEURISTIC:
        assert estimate.point is not None
        return UtilityContribution(
            dimension_id=dimension_id,
            quantity=1.0,
            status=estimate.status,
            lower=estimate.lower,
            upper=estimate.upper,
            point=estimate.point,
            provenance=value.provenance,
            label=value.label,
        )
    raise PresentUtilityError(
        f"unsupported present preference estimate status: {estimate.status!r}"
    )


def assess_present_candidate_utility(
    candidate: CandidateAssessment,
    *,
    term_id: str = "2026F",
    resolved_dimensions: Mapping[str, PreferenceValue] | None = None,
) -> PresentTermUtilityAssessment:
    """Project one Stage 4C candidate into non-lossy current-term utility evidence.

    ``resolved_dimensions`` is an explicit evidence repair path.  A key may only replace a
    dimension already reported unresolved by ``CandidateAssessment``; callers cannot inject
    unrelated bonuses.  Timetable heuristic status cannot be erased by an override—the
    underlying timetable preference evidence itself must be upgraded.
    """

    if not term_id.strip():
        raise PresentUtilityError("present utility requires a nonblank term_id")

    contributions: list[UtilityContribution] = []
    unresolved = set(candidate.present_preference_unknowns)
    measured_lower = 0.0
    measured_upper = 0.0
    heuristic = 0.0

    if candidate.timetable_utility is None:
        unresolved.add("timetable_utility")
    else:
        contributions.extend(candidate.timetable_utility.contributions)
        measured_lower += candidate.timetable_utility.measured_lower
        measured_upper += candidate.timetable_utility.measured_upper
        heuristic += candidate.timetable_utility.heuristic_point_delta

    # Stage 4C stores course preference values without scoring them.  Stage 4E may carry
    # numerical values onto the common utility scale when the supplied PreferenceValue says
    # they are exact/bounded/heuristic.
    for evidence in candidate.course_preferences:
        for short_name, value in (
            ("subject_interest", evidence.subject_interest),
            ("workload", evidence.workload_utility),
            ("difficulty", evidence.difficulty_utility),
        ):
            dimension_id = f"course::{evidence.section_id}::{short_name}"
            contribution = _preference_contribution(
                value, dimension_id=dimension_id
            )
            if contribution is None:
                unresolved.add(dimension_id)
                continue
            contributions.append(contribution)
            unresolved.discard(dimension_id)
            if contribution.status in {EstimateStatus.EXACT, EstimateStatus.BOUNDED}:
                assert contribution.lower is not None and contribution.upper is not None
                measured_lower += contribution.lower
                measured_upper += contribution.upper
            else:
                assert contribution.point is not None
                heuristic += contribution.point

    resolutions = resolved_dimensions or {}
    for dimension_id, value in resolutions.items():
        if not dimension_id.strip():
            raise PresentUtilityError("resolved present dimension id must be nonblank")
        if dimension_id == "timetable_heuristic_terms":
            raise PresentUtilityError(
                "timetable heuristic status must be resolved in the preference profile, not hidden by an override"
            )
        if dimension_id not in unresolved:
            raise PresentUtilityError(
                f"present utility resolution {dimension_id!r} does not correspond to an unresolved candidate dimension"
            )
        contribution = _preference_contribution(value, dimension_id=dimension_id)
        if contribution is None:
            continue
        contributions.append(contribution)
        unresolved.remove(dimension_id)
        if contribution.status in {EstimateStatus.EXACT, EstimateStatus.BOUNDED}:
            assert contribution.lower is not None and contribution.upper is not None
            measured_lower += contribution.lower
            measured_upper += contribution.upper
        else:
            assert contribution.point is not None
            heuristic += contribution.point

    return PresentTermUtilityAssessment(
        term_id=term_id,
        section_ids=candidate.section_ids,
        contributions=tuple(contributions),
        measured_lower=measured_lower,
        measured_upper=measured_upper,
        heuristic_point_delta=heuristic,
        unresolved_dimensions=frozenset(unresolved),
        known_infeasible=candidate.known_infeasible,
        hard_feasibility_resolved=candidate.hard_feasibility_resolved,
    )
