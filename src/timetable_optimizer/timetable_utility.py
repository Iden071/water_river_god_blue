"""Partial timetable-utility evaluation for the Stage 4 rebuild.

The evaluator consumes exact :mod:`timetable_quality` facts and a preference
profile.  It deliberately refuses to manufacture a single score when the
preference evidence does not justify one.

Three kinds of output stay separate:

* exact/bounded evidence contributes to a measured interval;
* heuristic evidence contributes only a labelled heuristic point;
* active unmeasured or undeclared dimensions are reported explicitly.

This is intentionally not the final whole-plan objective.  Course quality,
degree continuation value, registration risk, travel, and second-major
scenario aggregation remain separate later layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .preferences import (
    EstimateStatus,
    LinearPreferenceRelation,
    PreferenceProfile,
    PreferenceProvenance,
    PreferenceRuleError,
)
from .timetable_quality import TimetableQualityFacts


class TimetableUtilityError(ValueError):
    """Timetable utility cannot be evaluated under the supplied contract."""


@dataclass(frozen=True)
class UtilityContribution:
    """One activated preference dimension and its evidence-backed contribution."""

    dimension_id: str
    quantity: float
    status: EstimateStatus
    lower: float | None = None
    upper: float | None = None
    point: float | None = None
    provenance: PreferenceProvenance | None = None
    label: str = ""

    def __post_init__(self) -> None:
        if not self.dimension_id.strip():
            raise TimetableUtilityError("utility contribution requires a dimension_id")
        if not isfinite(self.quantity) or self.quantity <= 0:
            raise TimetableUtilityError("utility contribution quantity must be positive")


@dataclass(frozen=True)
class UnresolvedUtilityDimension:
    """An active timetable feature whose subjective value is not numerically usable."""

    dimension_id: str
    quantity: float
    reason: str
    label: str = ""


@dataclass(frozen=True)
class PartialUtilityAssessment:
    """A non-lossy utility result for one timetable.

    ``measured_lower`` and ``measured_upper`` cover only exact/bounded
    contributions.  They are *not* bounds on the whole timetable whenever
    heuristics or unresolved dimensions remain active.
    """

    contributions: tuple[UtilityContribution, ...]
    unresolved: tuple[UnresolvedUtilityDimension, ...]
    active_relations: tuple[LinearPreferenceRelation, ...]
    measured_lower: float
    measured_upper: float
    heuristic_point_delta: float

    @property
    def has_heuristics(self) -> bool:
        return any(
            contribution.status is EstimateStatus.HEURISTIC
            for contribution in self.contributions
        )

    @property
    def has_unresolved(self) -> bool:
        return bool(self.unresolved)

    @property
    def complete_bounds(self) -> tuple[float, float] | None:
        """Whole declared-timetable bounds, only when no information was dropped."""

        if self.has_heuristics or self.has_unresolved:
            return None
        return (self.measured_lower, self.measured_upper)

    @property
    def unresolved_dimensions(self) -> frozenset[str]:
        return frozenset(item.dimension_id for item in self.unresolved)


def _add(quantities: dict[str, float], dimension_id: str, amount: float = 1.0) -> None:
    if amount <= 0:
        return
    quantities[dimension_id] = quantities.get(dimension_id, 0.0) + amount


def timetable_preference_quantities(facts: TimetableQualityFacts) -> dict[str, float]:
    """Translate observable timetable facts into declared preference dimensions.

    The translation itself assigns no utility.  Where the historical evidence
    pins only one point on a shape (for example a four-period gap), only that
    point is activated numerically; other observed lengths activate a separate
    unresolved shape dimension instead of being interpolated silently.
    """

    quantities: dict[str, float] = {}

    for day in facts.days:
        if day.first_fixed_period == 1:
            _add(quantities, "start_period_1_day")
        elif day.first_fixed_period == 2:
            _add(quantities, "start_period_2_day")

        if day.last_fixed_period is not None and day.last_fixed_period >= 9:
            _add(quantities, f"late_finish_period_{day.last_fixed_period}")

        if day.lunch_fully_blocked:
            _add(quantities, "missing_lunch")
        if day.dinner_fully_blocked:
            _add(quantities, "missing_dinner")

        for run_length in day.fixed_runs:
            if run_length == 4:
                _add(quantities, "four_fixed_period_run")
            elif run_length > 4:
                _add(quantities, "long_fixed_run_shape")

        for hole_length in day.holes:
            if hole_length == 4:
                _add(quantities, "four_period_hole")
            elif hole_length > 0:
                _add(quantities, "dead_gap_shape")

    _add(
        quantities,
        "rest_fixed_free_weekday",
        float(len(facts.fixed_free_weekdays)),
    )

    attached_presence_free_days = max(
        0, facts.weekend_connected_presence_free_run - 2
    )
    if attached_presence_free_days:
        # The first attached day has a defensible interval.  Additional days
        # depend on the still-unresolved marginal-value shape.
        _add(quantities, "weekend_attached_presence_free_day")
        if attached_presence_free_days > 1:
            _add(
                quantities,
                "weekend_run_curvature",
                float(attached_presence_free_days - 1),
            )

    if facts.friday_event_window_free:
        _add(quantities, "friday_event_window_free")

    return quantities


def _contribution(profile: PreferenceProfile, dimension_id: str, quantity: float):
    try:
        value = profile.value(dimension_id)
    except PreferenceRuleError:
        return None, UnresolvedUtilityDimension(
            dimension_id=dimension_id,
            quantity=quantity,
            reason="active timetable dimension has no declared preference evidence",
        )

    estimate = value.estimate
    if estimate.status is EstimateStatus.UNMEASURED:
        return None, UnresolvedUtilityDimension(
            dimension_id=dimension_id,
            quantity=quantity,
            reason="preference dimension is explicitly unmeasured",
            label=value.label,
        )

    if estimate.status is EstimateStatus.EXACT:
        assert estimate.point is not None
        point = estimate.point * quantity
        return (
            UtilityContribution(
                dimension_id=dimension_id,
                quantity=quantity,
                status=estimate.status,
                lower=point,
                upper=point,
                point=point,
                provenance=value.provenance,
                label=value.label,
            ),
            None,
        )

    if estimate.status is EstimateStatus.BOUNDED:
        assert estimate.lower is not None and estimate.upper is not None
        return (
            UtilityContribution(
                dimension_id=dimension_id,
                quantity=quantity,
                status=estimate.status,
                lower=estimate.lower * quantity,
                upper=estimate.upper * quantity,
                provenance=value.provenance,
                label=value.label,
            ),
            None,
        )

    if estimate.status is EstimateStatus.HEURISTIC:
        assert estimate.point is not None
        return (
            UtilityContribution(
                dimension_id=dimension_id,
                quantity=quantity,
                status=estimate.status,
                lower=(estimate.lower * quantity if estimate.lower is not None else None),
                upper=(estimate.upper * quantity if estimate.upper is not None else None),
                point=estimate.point * quantity,
                provenance=value.provenance,
                label=value.label,
            ),
            None,
        )

    raise TimetableUtilityError(
        f"unsupported estimate status for {dimension_id!r}: {estimate.status!r}"
    )


def evaluate_timetable_utility(
    facts: TimetableQualityFacts,
    profile: PreferenceProfile,
) -> PartialUtilityAssessment:
    """Evaluate timetable geometry without collapsing uncertainty to a fake score."""

    quantities = timetable_preference_quantities(facts)
    contributions: list[UtilityContribution] = []
    unresolved: list[UnresolvedUtilityDimension] = []
    measured_lower = 0.0
    measured_upper = 0.0
    heuristic_point_delta = 0.0

    for dimension_id in sorted(quantities):
        quantity = quantities[dimension_id]
        contribution, missing = _contribution(profile, dimension_id, quantity)
        if missing is not None:
            unresolved.append(missing)
            continue
        assert contribution is not None
        contributions.append(contribution)

        if contribution.status in {EstimateStatus.EXACT, EstimateStatus.BOUNDED}:
            assert contribution.lower is not None and contribution.upper is not None
            measured_lower += contribution.lower
            measured_upper += contribution.upper
        elif contribution.status is EstimateStatus.HEURISTIC:
            assert contribution.point is not None
            heuristic_point_delta += contribution.point

    active_dimensions = set(quantities)
    active_relations = tuple(
        relation
        for relation in profile.relations
        if any(term.dimension_id in active_dimensions for term in relation.terms)
    )

    return PartialUtilityAssessment(
        contributions=tuple(contributions),
        unresolved=tuple(unresolved),
        active_relations=active_relations,
        measured_lower=measured_lower,
        measured_upper=measured_upper,
        heuristic_point_delta=heuristic_point_delta,
    )
