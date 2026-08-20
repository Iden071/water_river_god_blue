"""Non-lossy present-term utility for Stage 4E.

``CandidateAssessment`` is the Stage 4C evidence integration boundary.  Stage 4E needs one
additional projection: convert the preference evidence that is already numerical into the
same interval/heuristic/unresolved utility semantics used by the future optimizer, without
turning missing registration, travel, professor, workload, or difficulty evidence into zero.

This module deliberately does **not** decide hard feasibility or degree recognition.  Those
remain properties of the candidate/transition.  A whole-plan numerical bound is available
only when both preference evidence and hard feasibility are resolved.

Unresolved timetable utility is kept in two forms on purpose: ``unresolved_dimensions`` keeps
the broad compatibility/status view used by the whole-plan machinery, while
``unresolved_timetable_terms`` preserves the exact active quantity for each unmeasured
schedule-geometry term.  The latter prevents a later symbolic/sensitivity layer from losing
information by collapsing, for example, five three-period runs and one three-period run to the
same bare dimension name.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .candidate_assessment import CandidateAssessment
from .preferences import EstimateStatus, PreferenceValue
from .timetable_utility import (
    UnresolvedUtilityDimension,
    UtilityContribution,
)


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
    unresolved_timetable_terms: tuple[UnresolvedUtilityDimension, ...]
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
    quantity: float = 1.0,
) -> UtilityContribution | None:
    """Convert one scalar preference value while preserving its active quantity."""

    estimate = value.estimate
    if estimate.status is EstimateStatus.UNMEASURED:
        return None
    if estimate.status is EstimateStatus.EXACT:
        assert estimate.point is not None
        point = estimate.point * quantity
        return UtilityContribution(
            dimension_id=dimension_id,
            quantity=quantity,
            status=estimate.status,
            lower=point,
            upper=point,
            point=point,
            provenance=value.provenance,
            label=value.label,
        )
    if estimate.status is EstimateStatus.BOUNDED:
        assert estimate.lower is not None and estimate.upper is not None
        return UtilityContribution(
            dimension_id=dimension_id,
            quantity=quantity,
            status=estimate.status,
            lower=estimate.lower * quantity,
            upper=estimate.upper * quantity,
            provenance=value.provenance,
            label=value.label,
        )
    if estimate.status is EstimateStatus.HEURISTIC:
        assert estimate.point is not None
        return UtilityContribution(
            dimension_id=dimension_id,
            quantity=quantity,
            status=estimate.status,
            lower=(estimate.lower * quantity if estimate.lower is not None else None),
            upper=(estimate.upper * quantity if estimate.upper is not None else None),
            point=estimate.point * quantity,
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

    For an unresolved timetable scalar, a later resolution is interpreted as the per-unit
    preference value for the already-observed quantity.  This matches the ordinary timetable
    evaluator and avoids the old information-loss bug where resolving a dimension always
    contributed exactly one unit regardless of how many times it was active.
    """

    if not term_id.strip():
        raise PresentUtilityError("present utility requires a nonblank term_id")

    contributions: list[UtilityContribution] = []
    unresolved = set(candidate.present_preference_unknowns)
    unresolved_timetable_terms: dict[str, UnresolvedUtilityDimension] = {}
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
        for item in candidate.timetable_utility.unresolved:
            present_id = f"timetable::{item.dimension_id}"
            unresolved_timetable_terms[present_id] = UnresolvedUtilityDimension(
                dimension_id=present_id,
                quantity=item.quantity,
                reason=item.reason,
                label=item.label,
            )

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

        timetable_term = unresolved_timetable_terms.get(dimension_id)
        quantity = timetable_term.quantity if timetable_term is not None else 1.0
        contribution = _preference_contribution(
            value,
            dimension_id=dimension_id,
            quantity=quantity,
        )
        if contribution is None:
            continue
        contributions.append(contribution)
        unresolved.remove(dimension_id)
        unresolved_timetable_terms.pop(dimension_id, None)
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
        unresolved_timetable_terms=tuple(
            unresolved_timetable_terms[key]
            for key in sorted(unresolved_timetable_terms)
        ),
        known_infeasible=candidate.known_infeasible,
        hard_feasibility_resolved=candidate.hard_feasibility_resolved,
    )
