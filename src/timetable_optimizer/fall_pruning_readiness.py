"""Audit whether Fall-side objective branch-and-bound has proof-safe numeric inputs.

The bitset benchmarks establish that exact candidate enumeration is still combinatorially
large even after section-local hard-uncertainty compression.  The next tempting step is
objective branch-and-bound, but a branch can be pruned only when its best possible utility
has a defensible upper bound.

This module deliberately does NOT invent such bounds.  It reports whether the present/Fall
side of the objective is ready for them and identifies the evidence families that still lack
proof-safe numeric bounds.

Two distinct issues remain separate:

* objective definition: the Fall-vs-future temporal weight itself may not yet be elicited;
* objective boundedness: once Fall has positive weight, course/timetable/registration
  dimensions may still be unmeasured or heuristic rather than exact/bounded.

``PRESENT_BOUND_READY`` means only that the Fall-side evidence inspected here would permit a
numeric relaxed bound.  It does not claim that the future continuation bound is available or
that branch-and-bound has been implemented.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Mapping

from .course_preferences import (
    ProfessorRatingBook,
    assess_section_course_preferences,
)
from .fall_universe import FallSectionUniverse
from .preferences import EstimateStatus, PreferenceProfile, PreferenceValue
from .registration import (
    ObtainabilityStatus,
    RegistrationAssessment,
)


class FallPruningReadinessError(ValueError):
    """Pruning-readiness inputs are inconsistent."""


class FallPruningReadinessStatus(str, Enum):
    OBJECTIVE_UNRESOLVED = "objective_unresolved"
    PRESENT_BOUND_BLOCKED = "present_bound_blocked"
    PRESENT_BOUND_READY = "present_bound_ready"
    FALL_WEIGHT_ZERO = "fall_weight_zero"


class FallPruningBlockerKind(str, Enum):
    OBJECTIVE = "objective"
    SECTION_LOCAL = "section_local"
    TIMETABLE_PROFILE = "timetable_profile"


@dataclass(frozen=True)
class FallPruningBlockerFamily:
    """A repeated reason that prevents a proof-safe Fall-side upper bound."""

    dimension: str
    kind: FallPruningBlockerKind
    affected_section_ids: tuple[str, ...] = ()
    reason: str = ""

    def __post_init__(self) -> None:
        if not self.dimension.strip() or not self.reason.strip():
            raise FallPruningReadinessError(
                "pruning blocker requires dimension and reason"
            )
        if len(self.affected_section_ids) != len(set(self.affected_section_ids)):
            raise FallPruningReadinessError(
                "pruning blocker repeats an affected section id"
            )

    @property
    def affected_section_count(self) -> int:
        return len(self.affected_section_ids)

    @property
    def sample_section_ids(self) -> tuple[str, ...]:
        return self.affected_section_ids[:5]


@dataclass(frozen=True)
class FallPruningReadiness:
    """Fall-side proof-bound readiness; future-bound readiness is intentionally separate."""

    status: FallPruningReadinessStatus
    term_id: str
    fall_weight: float | None
    core_section_count: int
    blocker_families: tuple[FallPruningBlockerFamily, ...]

    @property
    def present_numeric_bound_available(self) -> bool:
        return self.status in {
            FallPruningReadinessStatus.PRESENT_BOUND_READY,
            FallPruningReadinessStatus.FALL_WEIGHT_ZERO,
        }

    @property
    def objective_defined(self) -> bool:
        return self.status is not FallPruningReadinessStatus.OBJECTIVE_UNRESOLVED

    @property
    def section_local_blockers(self) -> tuple[FallPruningBlockerFamily, ...]:
        return tuple(
            item
            for item in self.blocker_families
            if item.kind is FallPruningBlockerKind.SECTION_LOCAL
        )

    @property
    def timetable_profile_blockers(self) -> tuple[FallPruningBlockerFamily, ...]:
        return tuple(
            item
            for item in self.blocker_families
            if item.kind is FallPruningBlockerKind.TIMETABLE_PROFILE
        )


def _proof_numeric(value: PreferenceValue) -> bool:
    """Existing Stage 4 proof semantics accept exact/bounded, never heuristic points."""

    return value.estimate.status in {EstimateStatus.EXACT, EstimateStatus.BOUNDED}


def _explicit_resolution_available(
    dimension_id: str,
    resolutions: Mapping[str, PreferenceValue],
) -> bool:
    value = resolutions.get(dimension_id)
    return value is not None and _proof_numeric(value)


def _add_section_blocker(
    by_dimension: dict[str, set[str]],
    dimension: str,
    section_id: str,
) -> None:
    by_dimension.setdefault(dimension, set()).add(section_id)


def audit_fall_pruning_readiness(
    universe: FallSectionUniverse,
    preference_profile: PreferenceProfile,
    professor_ratings: ProfessorRatingBook,
    *,
    fall_weight: float | None,
    term_id: str = "2026F",
    registration_assessments: Mapping[str, RegistrationAssessment] | None = None,
    subject_interest: Mapping[str, PreferenceValue] | None = None,
    workload_utility: Mapping[str, PreferenceValue] | None = None,
    difficulty_utility: Mapping[str, PreferenceValue] | None = None,
    resolved_present_dimensions: Mapping[str, PreferenceValue] | None = None,
) -> FallPruningReadiness:
    """Report missing proof-safe Fall utility bounds without manufacturing numbers.

    The audit is conservative.  It only labels the *present* relaxed bound ready when every
    represented scalar timetable preference is exact/bounded, there are no unresolved
    qualitative relations in the current evaluator, and each selectable section's local
    course/registration utility evidence is exact/bounded or explicitly resolved with a
    proof-safe value.

    If ``fall_weight`` is ``None``, the real temporal objective has not been elicited.  The
    function still reports the latent boundedness blockers so evidence collection can be
    targeted, but the top-level status remains ``OBJECTIVE_UNRESOLVED``.
    """

    if not term_id.strip():
        raise FallPruningReadinessError("term_id must be nonblank")
    if fall_weight is not None and (not isfinite(fall_weight) or fall_weight < 0):
        raise FallPruningReadinessError(
            "fall_weight must be a finite nonnegative number or None"
        )

    registration_map = registration_assessments or {}
    subject_map = subject_interest or {}
    workload_map = workload_utility or {}
    difficulty_map = difficulty_utility or {}
    resolutions = resolved_present_dimensions or {}

    section_blockers: dict[str, set[str]] = {}

    for section in sorted(universe.included_sections, key=lambda item: item.section_id):
        evidence = assess_section_course_preferences(
            section,
            professor_ratings,
            subject_interest=subject_map,
            workload_utility=workload_map,
            difficulty_utility=difficulty_map,
        )
        sid = section.section_id

        # These names deliberately match CandidateAssessment.present_preference_unknowns.
        for dimension in evidence.unresolved_dimensions:
            scoped = f"course::{sid}::{dimension}"
            if not _explicit_resolution_available(scoped, resolutions):
                _add_section_blocker(section_blockers, dimension, sid)

        # SectionCoursePreferenceEvidence marks UNMEASURED values above, but heuristic
        # subject/workload/difficulty values are also not proof-safe complete bounds.
        for dimension, value in (
            ("subject_interest_heuristic", evidence.subject_interest),
            ("workload_heuristic", evidence.workload_utility),
            ("difficulty_heuristic", evidence.difficulty_utility),
        ):
            if value.estimate.status is EstimateStatus.HEURISTIC:
                _add_section_blocker(section_blockers, dimension, sid)

        registration = registration_map.get(sid)
        if registration is None:
            scoped = f"registration_obtainability::{sid}"
            if not _explicit_resolution_available(scoped, resolutions):
                _add_section_blocker(
                    section_blockers,
                    "registration_obtainability",
                    sid,
                )
        elif registration.obtainability.status is ObtainabilityStatus.UNMEASURED:
            scoped = f"registration_obtainability::{sid}"
            if not _explicit_resolution_available(scoped, resolutions):
                _add_section_blocker(
                    section_blockers,
                    "registration_obtainability",
                    sid,
                )
        elif registration.obtainability.status is ObtainabilityStatus.HEURISTIC:
            scoped = f"registration_obtainability_heuristic::{sid}"
            if not _explicit_resolution_available(scoped, resolutions):
                _add_section_blocker(
                    section_blockers,
                    "registration_obtainability_heuristic",
                    sid,
                )

    blockers: list[FallPruningBlockerFamily] = []
    if fall_weight is None:
        blockers.append(
            FallPruningBlockerFamily(
                dimension="temporal_weight::2026F",
                kind=FallPruningBlockerKind.OBJECTIVE,
                reason=(
                    "the real Fall-vs-future temporal weight has not been elicited; Stage 4 has no default equal/current-semester weight"
                ),
            )
        )

    # A relaxed bound over arbitrary descendants needs a defensible scalar bound for every
    # represented timetable dimension that may become active.  Exact/bounded values qualify;
    # unmeasured and heuristic values do not under current proof semantics.
    for value in preference_profile.values:
        if not _proof_numeric(value):
            blockers.append(
                FallPruningBlockerFamily(
                    dimension=value.dimension_id,
                    kind=FallPruningBlockerKind.TIMETABLE_PROFILE,
                    reason=(
                        "timetable preference is "
                        f"{value.estimate.status.value}, not an exact/bounded value usable in a proof-safe objective bound"
                    ),
                )
            )

    if preference_profile.relations:
        blockers.append(
            FallPruningBlockerFamily(
                dimension="qualitative_timetable_relations",
                kind=FallPruningBlockerKind.TIMETABLE_PROFILE,
                reason=(
                    "qualitative preference relations are preserved but the current relaxed-bound engine does not solve them into absolute admissible utility bounds"
                ),
            )
        )

    reasons = {
        "professor_rating": "listed professor is not manually rated; raw professor evidence is incomplete",
        "professor_rating_to_utility": "even a known [-1,+1] professor rating has no elicited conversion to the common utility scale",
        "subject_interest": "subject-interest utility is unmeasured for this course",
        "workload": "workload utility is unmeasured for this course",
        "difficulty": "difficulty utility is unmeasured for this course",
        "subject_interest_heuristic": "subject-interest input is heuristic rather than proof-safe exact/bounded evidence",
        "workload_heuristic": "workload input is heuristic rather than proof-safe exact/bounded evidence",
        "difficulty_heuristic": "difficulty input is heuristic rather than proof-safe exact/bounded evidence",
        "registration_obtainability": "registration obtainability is unmeasured and has no proof-safe utility bound",
        "registration_obtainability_heuristic": "registration obtainability is heuristic rather than proof-safe exact/bounded evidence",
    }
    for dimension in sorted(section_blockers):
        ids = tuple(sorted(section_blockers[dimension]))
        blockers.append(
            FallPruningBlockerFamily(
                dimension=dimension,
                kind=FallPruningBlockerKind.SECTION_LOCAL,
                affected_section_ids=ids,
                reason=reasons.get(
                    dimension,
                    "section-local utility evidence lacks a proof-safe bound",
                ),
            )
        )

    if fall_weight is None:
        status = FallPruningReadinessStatus.OBJECTIVE_UNRESOLVED
    elif fall_weight == 0:
        # Fall utility is mathematically absent from this particular objective.  We report
        # latent blockers above for diagnostics, but they cannot affect a zero-weight term.
        status = FallPruningReadinessStatus.FALL_WEIGHT_ZERO
    elif any(
        blocker.kind is not FallPruningBlockerKind.OBJECTIVE
        for blocker in blockers
    ):
        status = FallPruningReadinessStatus.PRESENT_BOUND_BLOCKED
    else:
        status = FallPruningReadinessStatus.PRESENT_BOUND_READY

    return FallPruningReadiness(
        status=status,
        term_id=term_id,
        fall_weight=fall_weight,
        core_section_count=len(universe.included_sections),
        blocker_families=tuple(blockers),
    )
