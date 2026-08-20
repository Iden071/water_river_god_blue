"""Admissible Fall intrinsic utility upper bound for one exact bitset DFS frame.

This is the bridge between the proof-evidence audit and future branch-and-bound.  It does not
change the candidate family and it does not prune anything by itself.

The bound is deliberately relaxed:

* optional adverse timetable features may disappear in the relaxation;
* every activatable geometry dimension has an explicit safe quantity cap, so correctness does
  not depend on a label such as "penalty" or on the current sign of its utility estimate;
* positive free-day/trip features use monotonic information from the already-selected prefix
  when every selected schedule is parsed, otherwise the global weekly maximum is used;
* positive unresolved timetable shapes are usable only after explicit proof-safe upper bounds
  pass :func:`audit_fall_intrinsic_upper_bound_readiness`;
* course quality uses the user-confirmed global proof envelopes, never missing professor
  ratings or the old PROF_W multiplier;
* remaining courses are relaxed to a uniform-value credit knapsack that ignores conflicts
  among remaining sections.  Because conflicts are removed, not added, this can only increase
  the best possible descendant value and is therefore admissible;
* registration risk, degree continuation, and future utility are out of scope.  Their bounds
  must be combined later before a whole-plan branch can be pruned.

A frame from :mod:`fall_bitset_enumeration` contains exactly the still-unvisited descendants
of that DFS node.  The calculator therefore uses ``remaining_mask`` as supplied rather than
reconstructing an older/full sibling set.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Mapping

from .fall_bitset_enumeration import FallBitsetFrame
from .fall_candidate_sets import FallLoadPolicy
from .fall_upper_bound_readiness import (
    ProofUpperBound,
    audit_fall_intrinsic_upper_bound_readiness,
)
from .fall_universe import FallSectionUniverse
from .preferences import PreferenceProfile, PreferenceValue
from .recognition import CHAPEL_2026_CODES
from .sections import ParsedSchedule, Section
from .timetable_quality import extract_timetable_quality
from .timetable_utility import timetable_preference_dimension_contract


class FallIntrinsicBranchBoundError(ValueError):
    """Branch-bound inputs are inconsistent with the exact-search contract."""


class FallIntrinsicBranchBoundStatus(str, Enum):
    AVAILABLE = "available"
    INPUT_BLOCKED = "input_blocked"


@dataclass(frozen=True)
class FallIntrinsicBranchUpperBound:
    status: FallIntrinsicBranchBoundStatus
    total_upper_bound: float | None
    timetable_upper_bound: float | None
    selected_course_upper_bound: float | None
    relaxed_additional_course_upper_bound: float | None
    relaxed_additional_section_count: int
    missing_timetable_dimensions: tuple[str, ...]
    missing_course_bound_dimensions: tuple[str, ...]
    used_global_timetable_relaxation: bool
    registration_risk_layer_separate: bool = True

    @property
    def available(self) -> bool:
        return self.status is FallIntrinsicBranchBoundStatus.AVAILABLE


_REQUIRED_COURSE_DIMS = (
    "professor_rating_to_utility",
    "subject_interest",
    "workload",
    "difficulty",
)


def _ordered_sections(universe: FallSectionUniverse) -> tuple[Section, ...]:
    return tuple(sorted(universe.included_sections, key=lambda item: item.section_id))


def _course_upper_per_selected_section(
    bounds: Mapping[str, PreferenceValue],
) -> float:
    total = 0.0
    for dimension in _REQUIRED_COURSE_DIMS:
        value = bounds.get(dimension)
        if value is None or value.estimate.upper is None:
            raise FallIntrinsicBranchBoundError(
                f"missing proof-safe course upper endpoint for {dimension!r}"
            )
        total += value.estimate.upper
    if not isfinite(total):
        raise FallIntrinsicBranchBoundError("course upper bound must be finite")
    return total


def _ordinary_cost(section: Section, policy: FallLoadPolicy) -> float:
    if section.credits is None:
        # Unknown credit cannot be charged a positive amount in an optimistic relaxation.
        return 0.0
    credits = float(section.credits)
    if section.course_code in CHAPEL_2026_CODES and policy.chapel_exempt_from_ordinary_cap:
        return 0.0
    return credits


def _relaxed_max_additional_sections(
    sections: tuple[Section, ...],
    remaining_mask: int,
    remaining_ordinary_credits: float,
    per_section_upper: float,
    policy: FallLoadPolicy,
) -> tuple[int, float]:
    """Uniform-value 0/1 credit relaxation over the frame's unvisited descendants.

    Pairwise timetable conflicts between remaining sections are ignored.  Unknown-credit and
    Chapel-exempt sections have optimistic cost zero.  With one common course-quality upper
    value per selected section, sorting by ordinary credit cost exactly solves this relaxed
    count maximization.
    """

    if per_section_upper <= 0:
        return 0, 0.0

    costs: list[float] = []
    mask = remaining_mask
    while mask:
        low = mask & -mask
        index = low.bit_length() - 1
        if index >= len(sections):
            raise FallIntrinsicBranchBoundError(
                "frame remaining_mask references section outside supplied universe"
            )
        costs.append(_ordinary_cost(sections[index], policy))
        mask ^= low

    costs.sort()
    count = 0
    used = 0.0
    epsilon = 1e-12
    for cost in costs:
        if used + cost <= remaining_ordinary_credits + epsilon:
            used += cost
            count += 1
        else:
            break
    return count, count * per_section_upper


def _upper_map(bounds: tuple[ProofUpperBound, ...]) -> dict[str, float]:
    return {item.dimension_id: item.upper for item in bounds}


def _positive(upper: float) -> float:
    # Optional absence gives utility 0, so only positive upper endpoints can increase an
    # optimistic relaxation.  This is a mathematical max, not a semantic penalty assumption.
    return max(0.0, upper)


def _trip_upper_for_attached_at_most(
    attached_max: int,
    upper_by_dimension: Mapping[str, float],
) -> float:
    if attached_max <= 0:
        return 0.0
    first = _positive(upper_by_dimension["weekend_attached_presence_free_day"])
    best = first
    for count in range(2, min(5, attached_max) + 1):
        # Exactly one count-state can occur in a final timetable.  Take the best state rather
        # than summing mutually exclusive corrections.
        extra = upper_by_dimension[
            f"weekend_attached_presence_free_extra_total_{count}"
        ]
        best = max(best, first + extra, 0.0)
    return best


def _long_run_positive_relaxation(upper_by_dimension: Mapping[str, float]) -> float:
    """Loose global maximum for positive 5+ period run corrections.

    A 15-period weekday can contain at most two disjoint runs of length >=5 because distinct
    runs require at least one separating free period.  Therefore each exact run-length state
    can activate at most twice per day, ten times per Monday-Friday week.  Summing that cap for
    every length greatly over-relaxes mutually incompatible states, but remains admissible.
    This term collapses to zero as soon as each long-run correction has a nonpositive ceiling.
    """

    total = 0.0
    for length in range(5, 16):
        total += 10.0 * _positive(
            upper_by_dimension[f"long_fixed_run_delta_{length}"]
        )
    return total


def _other_geometry_positive_relaxation(
    upper_by_dimension: Mapping[str, float],
) -> float:
    """Cap all non-free-day, non-long-run activatable dimensions explicitly.

    These caps are intentionally loose and may sum mutually incompatible states.  They exist
    so admissibility never depends on the current sign of a preference value.

    * start-at-period-1 / start-at-period-2: at most five weekdays each;
    * lunch / dinner fully blocked: at most five weekdays each;
    * exact three-period runs: at most four per 15-period day -> 20/week;
    * four-period anchor: at most three disjoint >=4 runs per 15-period day -> 15/week;
    * dead-gap quadratic quantity: max 13^2 per day (periods 1 and 15 occupied) -> 845/week;
    * each exact late-finish period: at most five weekdays.
    """

    capacities: dict[str, float] = {
        "start_period_1_day": 5.0,
        "start_period_2_day": 5.0,
        "missing_lunch": 5.0,
        "missing_dinner": 5.0,
        "three_fixed_period_run": 20.0,
        "four_fixed_period_run": 15.0,
        "dead_gap_quadratic_unit": 845.0,
    }
    capacities.update({f"late_finish_period_{period}": 5.0 for period in range(9, 16)})
    return sum(
        capacity * _positive(upper_by_dimension[dimension])
        for dimension, capacity in capacities.items()
    )


def _validate_geometry_contract_accounted_for() -> None:
    explicit = {
        "rest_fixed_free_weekday",
        "weekend_attached_presence_free_day",
        "friday_event_window_free",
        "start_period_1_day",
        "start_period_2_day",
        "missing_lunch",
        "missing_dinner",
        "three_fixed_period_run",
        "four_fixed_period_run",
        "dead_gap_quadratic_unit",
        *(f"late_finish_period_{period}" for period in range(9, 16)),
        *(f"long_fixed_run_delta_{length}" for length in range(5, 16)),
        *(
            f"weekend_attached_presence_free_extra_total_{count}"
            for count in range(2, 6)
        ),
    }
    contract = timetable_preference_dimension_contract()
    missing = contract - explicit
    extra = explicit - contract
    if missing or extra:
        raise FallIntrinsicBranchBoundError(
            "branch timetable relaxation is out of sync with activation contract: "
            f"missing={sorted(missing)}, extra={sorted(extra)}"
        )


def _timetable_upper_bound(
    selected_sections: tuple[Section, ...],
    upper_by_dimension: Mapping[str, float],
) -> tuple[float, bool]:
    _validate_geometry_contract_accounted_for()

    parsed = all(isinstance(section.schedule, ParsedSchedule) for section in selected_sections)
    if parsed:
        facts = extract_timetable_quality(selected_sections)
        max_fixed_free_days = len(facts.fixed_free_weekdays)
        max_attached_days = max(0, facts.weekend_connected_presence_free_run - 2)
        friday_can_still_be_free = facts.friday_event_window_free
        used_global = False
    else:
        # Unknown selected schedule could still turn out to permit every positive weekly
        # feature.  Fall back to the global weekly maxima rather than guessing its geometry.
        max_fixed_free_days = 5
        max_attached_days = 5
        friday_can_still_be_free = True
        used_global = True

    rest_upper = max_fixed_free_days * _positive(
        upper_by_dimension["rest_fixed_free_weekday"]
    )
    trip_upper = _trip_upper_for_attached_at_most(
        max_attached_days,
        upper_by_dimension,
    )
    friday_upper = (
        _positive(upper_by_dimension["friday_event_window_free"])
        if friday_can_still_be_free
        else 0.0
    )
    long_run_upper = _long_run_positive_relaxation(upper_by_dimension)
    other_upper = _other_geometry_positive_relaxation(upper_by_dimension)

    return (
        rest_upper + trip_upper + friday_upper + long_run_upper + other_upper,
        used_global,
    )


def derive_fall_intrinsic_branch_upper_bound(
    universe: FallSectionUniverse,
    frame: FallBitsetFrame,
    load_policy: FallLoadPolicy,
    preference_profile: PreferenceProfile,
    *,
    global_course_utility_bounds: Mapping[str, PreferenceValue],
    explicit_timetable_upper_bounds: Mapping[str, ProofUpperBound] | None = None,
) -> FallIntrinsicBranchUpperBound:
    """Derive an admissible deterministic Fall utility upper bound for one DFS frame.

    If proof ceilings are still missing, return ``INPUT_BLOCKED`` with those dimensions rather
    than manufacturing a number.  A returned available bound is only for intrinsic Fall
    timetable/course utility; registration, degree, and future objective components must be
    bounded separately before any whole-plan prune.
    """

    readiness = audit_fall_intrinsic_upper_bound_readiness(
        preference_profile,
        global_course_utility_bounds=global_course_utility_bounds,
        explicit_timetable_upper_bounds=explicit_timetable_upper_bounds,
    )
    if not readiness.intrinsic_upper_bound_ready:
        return FallIntrinsicBranchUpperBound(
            status=FallIntrinsicBranchBoundStatus.INPUT_BLOCKED,
            total_upper_bound=None,
            timetable_upper_bound=None,
            selected_course_upper_bound=None,
            relaxed_additional_course_upper_bound=None,
            relaxed_additional_section_count=0,
            missing_timetable_dimensions=readiness.missing_timetable_dimensions,
            missing_course_bound_dimensions=readiness.missing_course_bound_dimensions,
            used_global_timetable_relaxation=False,
            registration_risk_layer_separate=True,
        )

    ordered = _ordered_sections(universe)
    if tuple(sorted(frame.selected_indices)) != frame.selected_indices:
        raise FallIntrinsicBranchBoundError("frame selected indices must be increasing")
    if frame.selected_indices and frame.selected_indices[-1] >= len(ordered):
        raise FallIntrinsicBranchBoundError(
            "frame selected index references section outside supplied universe"
        )
    if frame.remaining_mask >> len(ordered):
        raise FallIntrinsicBranchBoundError(
            "frame remaining_mask references section outside supplied universe"
        )

    selected_sections = tuple(ordered[index] for index in frame.selected_indices)
    per_section_upper = _course_upper_per_selected_section(
        global_course_utility_bounds
    )
    selected_course_upper = len(selected_sections) * per_section_upper

    remaining_credit = load_policy.ordinary_credit_cap - frame.known_ordinary_credits
    if remaining_credit < -1e-9:
        raise FallIntrinsicBranchBoundError(
            "frame already exceeds the supplied ordinary-credit cap"
        )
    remaining_credit = max(0.0, remaining_credit)
    additional_count, additional_upper = _relaxed_max_additional_sections(
        ordered,
        frame.remaining_mask,
        remaining_credit,
        per_section_upper,
        load_policy,
    )

    upper_by_dimension = _upper_map(readiness.timetable_upper_bounds)
    timetable_upper, used_global = _timetable_upper_bound(
        selected_sections,
        upper_by_dimension,
    )
    total = timetable_upper + selected_course_upper + additional_upper
    return FallIntrinsicBranchUpperBound(
        status=FallIntrinsicBranchBoundStatus.AVAILABLE,
        total_upper_bound=total,
        timetable_upper_bound=timetable_upper,
        selected_course_upper_bound=selected_course_upper,
        relaxed_additional_course_upper_bound=additional_upper,
        relaxed_additional_section_count=additional_count,
        missing_timetable_dimensions=(),
        missing_course_bound_dimensions=(),
        used_global_timetable_relaxation=used_global,
        registration_risk_layer_separate=True,
    )
