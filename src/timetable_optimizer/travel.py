"""Structural campus-transition facts for Stage 4C.

The SPEC requires mixed-campus schedules to be evaluated as paths, not by attaching a
``SINCHON_BONUS`` to a timetable.  This module takes the first safe step: it extracts exact
physical campus-presence intervals and the campus-to-campus transitions implied by them.

It intentionally does *not* decide:

* how many minutes a 국제↔신촌 transfer takes on a given day;
* whether the user starts/ends the day at dorm, home, or elsewhere;
* the subjective utility cost of travel;
* whether a gap containing a live-online commitment is practically usable for transit.

Those require an explicit travel/residence scenario.  The facts here preserve enough
structure for that later model and expose physical location conflicts directly.
"""

from __future__ import annotations

from dataclasses import dataclass

from .sections import DeliveryKind, ParsedSchedule, Section


class TravelPathError(ValueError):
    """Campus-path facts cannot be determined safely from the supplied sections."""


@dataclass(frozen=True)
class CampusPresenceInterval:
    """One contiguous period range with physical presence at one known campus."""

    day: int
    start_period: int
    end_period: int
    campus: str
    section_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not 0 <= self.day <= 6:
            raise TravelPathError("campus interval day must be in 0..6")
        if self.start_period < 1 or self.end_period < self.start_period:
            raise TravelPathError("invalid campus presence interval")
        if not self.campus.strip():
            raise TravelPathError("physical campus presence requires a campus label")
        if not self.section_ids:
            raise TravelPathError("campus presence interval requires at least one section")


@dataclass(frozen=True)
class CampusLocationConflict:
    """A period that simultaneously requires physical presence at multiple campuses."""

    day: int
    period: int
    campuses: tuple[str, ...]
    section_ids: tuple[str, ...]


@dataclass(frozen=True)
class CampusTransition:
    """One required move between consecutive physical campus commitments."""

    day: int
    from_campus: str
    to_campus: str
    depart_after_period: int
    arrive_by_period: int
    free_periods_between: int
    fixed_periods_between: tuple[int, ...]
    from_section_ids: tuple[str, ...]
    to_section_ids: tuple[str, ...]

    @property
    def has_intervening_fixed_commitment(self) -> bool:
        return bool(self.fixed_periods_between)


@dataclass(frozen=True)
class CampusDayPath:
    """Physical campus path facts for one day."""

    day: int
    intervals: tuple[CampusPresenceInterval, ...]
    transitions: tuple[CampusTransition, ...]
    location_conflicts: tuple[CampusLocationConflict, ...]

    @property
    def campuses(self) -> tuple[str, ...]:
        out: list[str] = []
        for interval in self.intervals:
            if interval.campus not in out:
                out.append(interval.campus)
        return tuple(out)


@dataclass(frozen=True)
class TravelPathFacts:
    """Exact campus-presence structure, awaiting travel/residence assumptions."""

    days: tuple[CampusDayPath, ...]

    @property
    def cross_campus_transitions(self) -> tuple[CampusTransition, ...]:
        return tuple(
            transition
            for day in self.days
            for transition in day.transitions
            if transition.from_campus != transition.to_campus
        )

    @property
    def location_conflicts(self) -> tuple[CampusLocationConflict, ...]:
        return tuple(conflict for day in self.days for conflict in day.location_conflicts)

    @property
    def requires_travel_model(self) -> bool:
        return bool(self.cross_campus_transitions)


def _periods_from_mask(mask: int, day: int) -> set[int]:
    day_bits = (mask >> (day * 16)) & 0xFFFF
    return {period for period in range(1, 16) if day_bits & (1 << period)}


def extract_travel_path_facts(sections: tuple[Section, ...]) -> TravelPathFacts:
    """Extract physical campus transitions without inventing travel costs or times.

    Every supplied section must have a parsed schedule.  A no-listed-time or unresolved
    section can alter both physical presence and the available transfer window, so treating
    it as schedule-neutral would be unsafe.
    """

    for section in sections:
        if not isinstance(section.schedule, ParsedSchedule):
            raise TravelPathError(
                f"section {section.section_id!r} has non-parsed schedule; "
                "travel path would be underdetermined"
            )

    # (day, period) -> [(campus, section_id), ...] for physical commitments.
    physical: dict[tuple[int, int], list[tuple[str, str]]] = {}
    fixed_by_day: dict[int, set[int]] = {day: set() for day in range(7)}

    for section in sections:
        schedule = section.schedule
        assert isinstance(schedule, ParsedSchedule)
        for day in range(7):
            fixed_by_day[day].update(_periods_from_mask(schedule.fixed_mask, day))

        for segment in schedule.segments:
            if segment.delivery_kind is not DeliveryKind.IN_PERSON:
                continue
            campus = section.campus.strip()
            if not campus:
                raise TravelPathError(
                    f"in-person section {section.section_id!r} has no campus label"
                )
            for day, period in segment.blocks:
                physical.setdefault((day, period), []).append(
                    (campus, section.section_id)
                )

    day_paths: list[CampusDayPath] = []
    for day in range(7):
        conflicts: list[CampusLocationConflict] = []
        unique_location: dict[int, tuple[str, tuple[str, ...]]] = {}

        for period in range(1, 16):
            occupants = physical.get((day, period), [])
            if not occupants:
                continue
            campuses = tuple(sorted({campus for campus, _ in occupants}))
            section_ids = tuple(sorted({section_id for _, section_id in occupants}))
            if len(campuses) > 1:
                conflicts.append(
                    CampusLocationConflict(
                        day=day,
                        period=period,
                        campuses=campuses,
                        section_ids=section_ids,
                    )
                )
                # There is no single physical path through an impossible location state.
                continue
            unique_location[period] = (campuses[0], section_ids)

        intervals: list[CampusPresenceInterval] = []
        current_campus: str | None = None
        current_start: int | None = None
        current_end: int | None = None
        current_sections: set[str] = set()

        def close_interval() -> None:
            nonlocal current_campus, current_start, current_end, current_sections
            if current_campus is None:
                return
            assert current_start is not None and current_end is not None
            intervals.append(
                CampusPresenceInterval(
                    day=day,
                    start_period=current_start,
                    end_period=current_end,
                    campus=current_campus,
                    section_ids=tuple(sorted(current_sections)),
                )
            )
            current_campus = None
            current_start = None
            current_end = None
            current_sections = set()

        for period in sorted(unique_location):
            campus, section_ids = unique_location[period]
            if (
                current_campus is not None
                and campus == current_campus
                and current_end is not None
                and period == current_end + 1
            ):
                current_end = period
                current_sections.update(section_ids)
                continue

            close_interval()
            current_campus = campus
            current_start = period
            current_end = period
            current_sections = set(section_ids)

        close_interval()

        transitions: list[CampusTransition] = []
        for previous, following in zip(intervals, intervals[1:]):
            if previous.campus == following.campus:
                continue
            free_periods = max(0, following.start_period - previous.end_period - 1)
            fixed_between = tuple(
                period
                for period in range(previous.end_period + 1, following.start_period)
                if period in fixed_by_day[day]
            )
            transitions.append(
                CampusTransition(
                    day=day,
                    from_campus=previous.campus,
                    to_campus=following.campus,
                    depart_after_period=previous.end_period,
                    arrive_by_period=following.start_period,
                    free_periods_between=free_periods,
                    fixed_periods_between=fixed_between,
                    from_section_ids=previous.section_ids,
                    to_section_ids=following.section_ids,
                )
            )

        day_paths.append(
            CampusDayPath(
                day=day,
                intervals=tuple(intervals),
                transitions=tuple(transitions),
                location_conflicts=tuple(conflicts),
            )
        )

    return TravelPathFacts(tuple(day_paths))
