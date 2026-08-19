"""Diagnostic-only sensitivity scenarios for unresolved Fall timetable shapes.

These scenarios answer a narrow engineering question: *if the old provisional shape choices
were moved across the range already recorded in RULES.md, how much could they move a given
timetable?*  They are intentionally **not** preference evidence and **not** proof bounds.

Nothing in this module returns :class:`PreferenceValue`, :class:`ProofUpperBound`, or any
object accepted by the branch-and-bound proof layer.  The archival constants remain below the
current authority boundary until the user manually reconfirms them or a separate proof-safe
ceiling is established.

Archival diagnostic family (R140-era evidence, provisional here):

* REST was bracketed 6..8;
* the first weekend-attached trip/home component was coupled as ``20 - REST`` -> 12..14;
* Friday-event bonus followed the older Monday/Friday 75% relation -> trip/3 -> 4..14/3;
* weekend trip shape used exponent 1.2..1.6, midpoint 1.4;
* the old marathon rule was flat for every run >=4 periods, so the diagnostic correction
  beyond the currently confirmed four-period -8 anchor is zero.

The endpoint scenarios preserve the old coupling rather than independently combining every
minimum and maximum.  They are sensitivity probes, not confidence intervals.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType
from typing import Mapping


class FallShapeDiagnosticError(ValueError):
    """A diagnostic scenario or activation map is malformed."""


@dataclass(frozen=True)
class ArchivedShapeScenario:
    """One coupled archival point scenario; never proof evidence."""

    scenario_id: str
    rest_value: float
    first_attached_trip_value: float
    weekend_run_exponent: float
    friday_event_value: float
    source_id: str
    note: str

    def __post_init__(self) -> None:
        if not self.scenario_id.strip() or not self.source_id.strip() or not self.note.strip():
            raise FallShapeDiagnosticError(
                "diagnostic scenario requires id, source provenance, and warning note"
            )
        for value in (
            self.rest_value,
            self.first_attached_trip_value,
            self.weekend_run_exponent,
            self.friday_event_value,
        ):
            if not isfinite(value):
                raise FallShapeDiagnosticError("diagnostic values must be finite")
        if self.first_attached_trip_value < 0 or self.weekend_run_exponent <= 0:
            raise FallShapeDiagnosticError(
                "archival trip value must be nonnegative and exponent positive"
            )

    def weekend_extra_total(self, attached_weekdays: int) -> float:
        """Old-formula total extra beyond the first attached weekday.

        The old trip formula was ``D * k**a`` for ``k`` attached weekdays.  The current
        Stage-4 representation already gives the first attached weekday its own value, so the
        state-specific unresolved correction is ``D * (k**a - 1)``.
        """

        if attached_weekdays < 2 or attached_weekdays > 5:
            raise FallShapeDiagnosticError(
                "attached_weekdays must be one of the current unresolved states 2..5"
            )
        return self.first_attached_trip_value * (
            attached_weekdays ** self.weekend_run_exponent - 1.0
        )

    def unresolved_shape_points(self) -> Mapping[str, float]:
        """Return provisional points for only the currently unresolved shape dimensions."""

        points: dict[str, float] = {
            "friday_event_window_free": self.friday_event_value,
        }
        # Legacy marathon rule treated all >=4-period runs as the same -8.  Since the
        # confirmed Stage-4 four-period anchor already contributes -8, the archival extra is 0.
        for length in range(5, 16):
            points[f"long_fixed_run_delta_{length}"] = 0.0
        for count in range(2, 6):
            points[
                f"weekend_attached_presence_free_extra_total_{count}"
            ] = self.weekend_extra_total(count)
        return MappingProxyType(points)


def archived_shape_sensitivity_scenarios() -> tuple[ArchivedShapeScenario, ...]:
    """Return low-trip, midpoint, and high-trip archival sensitivity points.

    The labels describe the old *trip-curve* direction.  Because REST and trip value were
    coupled inversely (trip = 20 - REST), these are not generic lower/middle/upper utility
    scenarios for an entire timetable.
    """

    common = (
        "Diagnostic only: reconstructed from archival RULES.md R140-era elicitation; "
        "not current user-confirmed proof evidence and never admissible as a pruning bound."
    )
    return (
        ArchivedShapeScenario(
            scenario_id="archival-low-trip-curve",
            rest_value=8.0,
            first_attached_trip_value=12.0,
            weekend_run_exponent=1.2,
            friday_event_value=4.0,
            source_id="provisional:R140:low-trip-endpoint",
            note=common,
        ),
        ArchivedShapeScenario(
            scenario_id="archival-midpoint",
            rest_value=7.0,
            first_attached_trip_value=13.0,
            weekend_run_exponent=1.4,
            friday_event_value=13.0 / 3.0,
            source_id="provisional:R140:midpoint",
            note=common,
        ),
        ArchivedShapeScenario(
            scenario_id="archival-high-trip-curve",
            rest_value=6.0,
            first_attached_trip_value=14.0,
            weekend_run_exponent=1.6,
            friday_event_value=14.0 / 3.0,
            source_id="provisional:R140:high-trip-endpoint",
            note=common,
        ),
    )


@dataclass(frozen=True)
class ShapeScenarioDelta:
    scenario_id: str
    active_shape_dimensions: tuple[str, ...]
    provisional_delta: float


@dataclass(frozen=True)
class ShapeSensitivityAssessment:
    """How much the archival shape scenarios move one timetable's unresolved contribution."""

    scenario_deltas: tuple[ShapeScenarioDelta, ...]
    unresolved_shape_dimensions_not_covered: tuple[str, ...]

    @property
    def spread(self) -> float | None:
        if not self.scenario_deltas:
            return None
        values = [item.provisional_delta for item in self.scenario_deltas]
        return max(values) - min(values)

    @property
    def scenario_points(self) -> Mapping[str, float]:
        return MappingProxyType(
            {item.scenario_id: item.provisional_delta for item in self.scenario_deltas}
        )


_SHAPE_PREFIXES = (
    "long_fixed_run_delta_",
    "weekend_attached_presence_free_extra_total_",
)
_SHAPE_EXACT_IDS = frozenset({"friday_event_window_free"})


def _is_shape_dimension(dimension_id: str) -> bool:
    return dimension_id in _SHAPE_EXACT_IDS or dimension_id.startswith(_SHAPE_PREFIXES)


def assess_archival_shape_sensitivity(
    preference_quantities: Mapping[str, float],
    scenarios: tuple[ArchivedShapeScenario, ...] | None = None,
) -> ShapeSensitivityAssessment:
    """Apply provisional shape points to an already-extracted timetable quantity map.

    Only shape dimensions are consumed.  Known exact/bounded timetable utility, course value,
    future value, registration, and degree consequences are deliberately absent; callers must
    not interpret the result as a timetable score or recommendation.
    """

    scenario_set = scenarios or archived_shape_sensitivity_scenarios()
    if len({scenario.scenario_id for scenario in scenario_set}) != len(scenario_set):
        raise FallShapeDiagnosticError("diagnostic scenario ids must be unique")

    active = tuple(
        sorted(
            dimension
            for dimension, quantity in preference_quantities.items()
            if _is_shape_dimension(dimension) and quantity > 0
        )
    )
    for dimension in active:
        quantity = preference_quantities[dimension]
        if not isfinite(quantity) or quantity <= 0:
            raise FallShapeDiagnosticError(
                "active diagnostic shape quantities must be finite and positive"
            )

    results: list[ShapeScenarioDelta] = []
    covered: set[str] = set()
    for scenario in scenario_set:
        points = scenario.unresolved_shape_points()
        delta = 0.0
        used: list[str] = []
        for dimension in active:
            point = points.get(dimension)
            if point is None:
                continue
            delta += preference_quantities[dimension] * point
            used.append(dimension)
            covered.add(dimension)
        results.append(
            ShapeScenarioDelta(
                scenario_id=scenario.scenario_id,
                active_shape_dimensions=tuple(used),
                provisional_delta=delta,
            )
        )

    return ShapeSensitivityAssessment(
        scenario_deltas=tuple(results),
        unresolved_shape_dimensions_not_covered=tuple(
            dimension for dimension in active if dimension not in covered
        ),
    )
