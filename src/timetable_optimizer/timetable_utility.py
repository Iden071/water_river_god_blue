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


_LATE_FINISH_PERIODS = tuple(range(9, 16))
_LONG_FIXED_RUN_LENGTHS = tuple(range(5, 16))
_WEEKEND_ATTACHED_DAY_COUNTS = tuple(range(2, 6))
_TIMETABLE_PREFERENCE_DIMENSION_CONTRACT = frozenset(
    {
        "start_period_1_day",
        "start_period_2_day",
        "missing_lunch",
        "missing_dinner",
        "three_fixed_period_run",
        "four_fixed_period_run",
        "dead_gap_quadratic_unit",
        "rest_fixed_free_weekday",
        "weekend_attached_presence_free_day",
        "friday_event_window_free",
        *(f"late_finish_period_{period}" for period in _LATE_FINISH_PERIODS),
        *(f"long_fixed_run_delta_{length}" for length in _LONG_FIXED_RUN_LENGTHS),
        *(
            f"weekend_attached_presence_free_extra_total_{count}"
            for count in _WEEKEND_ATTACHED_DAY_COUNTS
        ),
    }
)


def timetable_preference_dimension_contract() -> frozenset[str]:
    """Return every subjective dimension this timetable evaluator may activate.

    This is a proof contract, not a list of every preference-like concept in the
    repository.  Course burden, Chapel timing, registration risk, travel disutility,
    and similar layers are intentionally absent because this evaluator never emits
    them.  Conversely, dimensions produced dynamically by schedule geometry are
    included even when the current preference profile forgot to declare them.

    Run length is represented without inheriting the legacy threshold as a preference
    fact.  One- and two-period runs have no run-length term because the user explicitly
    confirmed no intrinsic penalty for them.  A three-period run activates its own
    unresolved state.  A four-period run uses the confirmed -8 anchor.  A run of 5+
    fixed periods receives that anchor plus an unresolved correction for its exact
    length.  Likewise, the first weekend-attached no-campus weekday retains its known
    value, while a state with 2..5 attached weekdays receives one unresolved extra-total
    correction for that exact state.  This is an exact reparameterization: no linearity
    or curvature is assumed merely to make the optimizer easier to write.

    A branch-bound readiness audit must use this contract rather than iterating over
    every value stored in a broad preference profile; otherwise it can both invent
    false blockers and miss real activatable ones.
    """

    return _TIMETABLE_PREFERENCE_DIMENSION_CONTRACT


def timetable_preference_quantities(facts: TimetableQualityFacts) -> dict[str, float]:
    """Translate observable timetable facts into declared preference dimensions.

    The translation itself assigns no utility.  Confirmed preference shapes are
    represented by a quantity that lets the profile provide one evidence-backed
    coefficient.  In particular, dead gaps use the confirmed quadratic curve
    ``-10 * (length/4)^2`` by accumulating ``length^2`` units.
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
            if run_length == 3:
                # User confirmed a very slight intrinsic burden may exist here, but did
                # not settle its magnitude.  Preserve it explicitly rather than silently
                # inheriting the old model's zero-below-four marathon threshold.
                _add(quantities, "three_fixed_period_run")
            elif run_length >= 4:
                # Preserve the confirmed four-period anchor inside every longer state,
                # then leave the exact additional effect of length 5+ unresolved.  This
                # does not assume a linear or fully known longer-run curve.
                _add(quantities, "four_fixed_period_run")
                if run_length > 4:
                    _add(quantities, f"long_fixed_run_delta_{run_length}")

        for hole_length in day.holes:
            if hole_length > 0:
                _add(
                    quantities,
                    "dead_gap_quadratic_unit",
                    float(hole_length * hole_length),
                )

    _add(
        quantities,
        "rest_fixed_free_weekday",
        float(len(facts.fixed_free_weekdays)),
    )

    attached_presence_free_days = max(
        0, facts.weekend_connected_presence_free_run - 2
    )
    if attached_presence_free_days:
        # The first attached weekday has a defensible interval.  If more weekdays attach,
        # retain that known component and represent the *total extra value beyond the first*
        # for the exact state.  One scalar "curvature" times N would silently assume linear
        # marginal value and cannot represent the older nonlinear evidence faithfully.
        _add(quantities, "weekend_attached_presence_free_day")
        if attached_presence_free_days > 1:
            _add(
                quantities,
                f"weekend_attached_presence_free_extra_total_{attached_presence_free_days}",
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
