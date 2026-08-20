"""Exact structural signature for currently unresolved Fall timetable preferences.

This module does **not** assign utility and does **not** provide proof bounds.  It records the
finite timetable state on which the remaining unpriced geometry terms depend, so later search
layers can stratify or sensitivity-test alternatives instead of forcing stale scalar weights.

The signature deliberately contains only geometry that is still numerically incomplete:

* whether the Friday event window is free;
* how many weekdays are attached to the weekend-connected no-presence run;
* how many three-period fixed runs occur;
* the multiset of fixed run lengths above four periods.

One- and two-period runs are absent because the user explicitly confirmed they carry no
intrinsic run penalty.  Four periods is absent because its utility is already confirmed at
-8.  Known starts, meals, gaps, late finishes, and the first weekend-attached day likewise
remain in the ordinary measured utility path.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from .timetable_quality import TimetableQualityFacts


class FallUnresolvedShapeError(ValueError):
    """An unresolved-shape signature violates timetable geometry invariants."""


def is_fall_unresolved_shape_dimension(dimension_id: str) -> bool:
    """Whether ``dimension_id`` is one of the currently symbolic Fall shape terms."""

    return (
        dimension_id == "friday_event_window_free"
        or dimension_id == "three_fixed_period_run"
        or dimension_id.startswith("long_fixed_run_delta_")
        or dimension_id.startswith("weekend_attached_presence_free_extra_total_")
    )


@dataclass(frozen=True)
class FallUnresolvedShapeSignature:
    """Finite exact state for the current unmeasured timetable-shape dimensions."""

    friday_event_window_free: bool
    weekend_attached_presence_free_days: int
    three_fixed_period_run_count: int
    long_fixed_run_counts: tuple[tuple[int, int], ...]

    def __post_init__(self) -> None:
        if not 0 <= self.weekend_attached_presence_free_days <= 5:
            raise FallUnresolvedShapeError(
                "weekend-attached presence-free weekday count must be in 0..5"
            )
        if self.three_fixed_period_run_count < 0:
            raise FallUnresolvedShapeError("three-period run count cannot be negative")
        previous = 4
        for length, count in self.long_fixed_run_counts:
            if length <= previous or not 5 <= length <= 15:
                raise FallUnresolvedShapeError(
                    "long-run lengths must be unique, increasing, and in 5..15"
                )
            if count <= 0:
                raise FallUnresolvedShapeError("long-run counts must be positive")
            previous = length

    @property
    def active_dimension_quantities(self) -> Mapping[str, float]:
        """Return exactly the unresolved preference dimensions activated by this state."""

        quantities: dict[str, float] = {}
        if self.friday_event_window_free:
            quantities["friday_event_window_free"] = 1.0
        if self.weekend_attached_presence_free_days > 1:
            quantities[
                "weekend_attached_presence_free_extra_total_"
                f"{self.weekend_attached_presence_free_days}"
            ] = 1.0
        if self.three_fixed_period_run_count:
            quantities["three_fixed_period_run"] = float(
                self.three_fixed_period_run_count
            )
        for length, count in self.long_fixed_run_counts:
            quantities[f"long_fixed_run_delta_{length}"] = float(count)
        return MappingProxyType(quantities)


def unresolved_shape_signature(
    facts: TimetableQualityFacts,
) -> FallUnresolvedShapeSignature:
    """Extract the exact unresolved geometry state from timetable facts."""

    three_count = 0
    long_counts: dict[int, int] = {}
    for day in facts.days:
        for run_length in day.fixed_runs:
            if run_length == 3:
                three_count += 1
            elif run_length > 4:
                long_counts[run_length] = long_counts.get(run_length, 0) + 1

    attached_days = max(0, facts.weekend_connected_presence_free_run - 2)
    return FallUnresolvedShapeSignature(
        friday_event_window_free=facts.friday_event_window_free,
        weekend_attached_presence_free_days=attached_days,
        three_fixed_period_run_count=three_count,
        long_fixed_run_counts=tuple(sorted(long_counts.items())),
    )
