"""Exact timetable-quality facts for the Stage 4 rebuild.

This module extracts observable timetable structure from safely parsed schedules.  It
assigns no subjective utility, so the same exact facts can be evaluated by different
preference profiles without changing the feasible set or re-parsing source data.

The canonical-section API remains available, but the core extractor now consumes
``ParsedSchedule`` objects directly.  This lets later scenario layers evaluate hypothetical
future offerings without fabricating canonical observed ``Section`` objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from .sections import ParsedSchedule, Section


class TimetableQualityError(ValueError):
    """Timetable quality facts cannot be determined safely."""


@dataclass(frozen=True)
class DayQualityFacts:
    day: int
    first_fixed_period: int | None
    last_fixed_period: int | None
    fixed_periods: tuple[int, ...]
    presence_periods: tuple[int, ...]
    conflict_periods: tuple[int, ...]
    holes: tuple[int, ...]
    fixed_runs: tuple[int, ...]
    lunch_fully_blocked: bool
    dinner_fully_blocked: bool
    physically_present: bool
    fixed_commitment: bool


@dataclass(frozen=True)
class TimetableQualityFacts:
    days: tuple[DayQualityFacts, ...]
    presence_free_weekdays: frozenset[int]
    fixed_free_weekdays: frozenset[int]
    friday_event_window_free: bool
    weekend_connected_presence_free_run: int


def _periods(mask: int, day: int) -> tuple[int, ...]:
    word = (mask >> (day * 16)) & 0xFFFF
    return tuple(period for period in range(1, 16) if word & (1 << period))


def _holes(periods: tuple[int, ...]) -> tuple[int, ...]:
    if len(periods) < 2:
        return ()
    occupied = set(periods)
    out: list[int] = []
    run = 0
    for period in range(periods[0], periods[-1] + 1):
        if period in occupied:
            if run:
                out.append(run)
                run = 0
        else:
            run += 1
    return tuple(out)


def _runs(periods: tuple[int, ...]) -> tuple[int, ...]:
    if not periods:
        return ()
    out: list[int] = []
    run = 1
    for previous, current in zip(periods, periods[1:]):
        if current == previous + 1:
            run += 1
        else:
            out.append(run)
            run = 1
    out.append(run)
    return tuple(out)


def _weekend_connected_run(presence_free_weekdays: frozenset[int]) -> int:
    """Length of the maximal no-presence run connected to Sat/Sun."""

    attached: set[int] = set()
    for day in range(4, -1, -1):
        if day in presence_free_weekdays:
            attached.add(day)
        else:
            break
    for day in range(0, 5):
        if day in presence_free_weekdays:
            attached.add(day)
        else:
            break

    if not attached:
        return 2
    return 2 + len(attached)


def _extract_from_masks(
    conflict_mask: int,
    presence_mask: int,
    fixed_mask: int,
) -> TimetableQualityFacts:
    if presence_mask & ~fixed_mask:
        raise TimetableQualityError("presence mask is not a subset of fixed mask")
    if fixed_mask & ~conflict_mask:
        raise TimetableQualityError("fixed mask is not a subset of conflict mask")

    days: list[DayQualityFacts] = []
    presence_free: set[int] = set()
    fixed_free: set[int] = set()

    for day in range(5):
        fixed_periods = _periods(fixed_mask, day)
        presence_periods = _periods(presence_mask, day)
        conflict_periods = _periods(conflict_mask, day)

        if not presence_periods:
            presence_free.add(day)
        if not fixed_periods:
            fixed_free.add(day)

        days.append(
            DayQualityFacts(
                day=day,
                first_fixed_period=fixed_periods[0] if fixed_periods else None,
                last_fixed_period=fixed_periods[-1] if fixed_periods else None,
                fixed_periods=fixed_periods,
                presence_periods=presence_periods,
                conflict_periods=conflict_periods,
                holes=_holes(fixed_periods),
                fixed_runs=_runs(fixed_periods),
                lunch_fully_blocked=all(p in fixed_periods for p in (3, 4, 5)),
                dinner_fully_blocked=all(p in fixed_periods for p in (9, 10, 11)),
                physically_present=bool(presence_periods),
                fixed_commitment=bool(fixed_periods),
            )
        )

    friday_fixed = set(_periods(fixed_mask, 4))
    event_window = set(range(6, 12))

    return TimetableQualityFacts(
        days=tuple(days),
        presence_free_weekdays=frozenset(presence_free),
        fixed_free_weekdays=frozenset(fixed_free),
        friday_event_window_free=not bool(friday_fixed & event_window),
        weekend_connected_presence_free_run=_weekend_connected_run(
            frozenset(presence_free)
        ),
    )


def extract_timetable_quality_from_parsed_schedules(
    schedules: tuple[ParsedSchedule, ...],
) -> TimetableQualityFacts:
    """Extract exact timetable structure from already-validated parsed schedules.

    This pure scenario-friendly entry point carries no section identity and makes no claim
    that its schedules came from observed canonical catalogue rows.
    """

    conflict_mask = 0
    presence_mask = 0
    fixed_mask = 0
    for schedule in schedules:
        if not isinstance(schedule, ParsedSchedule):
            raise TimetableQualityError(
                "parsed-schedule extractor received a non-ParsedSchedule value"
            )
        conflict_mask |= schedule.conflict_mask
        presence_mask |= schedule.presence_mask
        fixed_mask |= schedule.fixed_mask
    return _extract_from_masks(conflict_mask, presence_mask, fixed_mask)


def extract_timetable_quality(sections: tuple[Section, ...]) -> TimetableQualityFacts:
    """Extract exact timetable structure from fully parsed canonical sections.

    ``NoListedSchedule`` and ``UnresolvedSchedule`` are intentionally rejected rather than
    treated as free time.  A scenario layer may handle them explicitly, but the exact-facts
    path must not fabricate schedule neutrality.
    """

    schedules: list[ParsedSchedule] = []
    for section in sections:
        if not isinstance(section.schedule, ParsedSchedule):
            raise TimetableQualityError(
                f"section {section.section_id} has non-parsed schedule: "
                f"{type(section.schedule).__name__}"
            )
        schedules.append(section.schedule)
    return extract_timetable_quality_from_parsed_schedules(tuple(schedules))
