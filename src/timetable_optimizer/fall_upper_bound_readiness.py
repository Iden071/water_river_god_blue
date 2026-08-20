"""Proof-safe Fall intrinsic upper-bound readiness for branch-and-bound.

``fall_pruning_readiness`` asks a stronger question: is the Fall utility contribution fully
bounded well enough to participate in complete interval comparison?  Branch-and-bound needs
less.  To prove that a branch cannot beat an incumbent, only a defensible *upper* bound on
that branch's best possible utility is required.

This module keeps those two claims separate.  It audits only the deterministic/intrinsic
Fall academic objective:

* every timetable-geometry dimension the evaluator may activate needs a proof-safe upper;
* the four global course-quality dimensions need their already-elicited proof-safe envelopes;
* registration obtainability is deliberately **not** converted into a preference penalty here.

The last point is important.  The user explicitly classified registration obtainability as a
risk/contingency problem rather than a personal utility weight.  A later registration-strategy
layer must prove how risk changes the full objective before a deterministic timetable upper
bound can be advertised as a full registration-plan upper bound.  This module therefore says
``intrinsic_upper_bound_ready`` rather than ``whole_plan_upper_bound_ready``.

No one-sided bound is invented from a label such as "penalty" or from old RULES.md evidence.
If a currently unmeasured dimension has only an upper bound, it must be supplied explicitly as
``ProofUpperBound`` with provenance and a transparent justification.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Mapping

from .preferences import EstimateStatus, PreferenceProfile, PreferenceRuleError, PreferenceValue
from .timetable_utility import timetable_preference_dimension_contract


class FallUpperBoundError(ValueError):
    """An upper-bound readiness input violates the proof contract."""


class FallUpperBoundStatus(str, Enum):
    READY = "intrinsic_upper_bound_ready"
    BLOCKED = "intrinsic_upper_bound_blocked"


@dataclass(frozen=True)
class ProofUpperBound:
    """One-sided evidence that utility for a dimension can never exceed ``upper``."""

    dimension_id: str
    upper: float
    source_id: str
    justification: str

    def __post_init__(self) -> None:
        if not self.dimension_id.strip():
            raise FallUpperBoundError("proof upper bound requires a dimension_id")
        if not isfinite(self.upper):
            raise FallUpperBoundError("proof upper bound must be finite")
        if not self.source_id.strip() or not self.justification.strip():
            raise FallUpperBoundError(
                "proof upper bound requires provenance and transparent justification"
            )


@dataclass(frozen=True)
class FallUpperBoundReadiness:
    status: FallUpperBoundStatus
    timetable_upper_bounds: tuple[ProofUpperBound, ...]
    missing_timetable_dimensions: tuple[str, ...]
    missing_course_bound_dimensions: tuple[str, ...]
    registration_risk_layer_separate: bool = True

    @property
    def intrinsic_upper_bound_ready(self) -> bool:
        return self.status is FallUpperBoundStatus.READY

    @property
    def conceptual_timetable_blocker_families(self) -> tuple[str, ...]:
        families: set[str] = set()
        for dimension in self.missing_timetable_dimensions:
            if dimension == "three_fixed_period_run" or dimension.startswith(
                "long_fixed_run_delta_"
            ):
                families.add("fixed_run_shape")
            elif dimension.startswith("weekend_attached_presence_free_extra_total_"):
                families.add("weekend_attached_run_shape")
            elif dimension == "friday_event_window_free":
                families.add("friday_event_value")
            else:
                families.add(dimension)
        return tuple(sorted(families))


_REQUIRED_GLOBAL_COURSE_BOUND_DIMENSIONS = frozenset(
    {"professor_rating_to_utility", "subject_interest", "workload", "difficulty"}
)


def _profile_upper_bound(
    profile: PreferenceProfile,
    dimension_id: str,
) -> ProofUpperBound | None:
    try:
        value = profile.value(dimension_id)
    except PreferenceRuleError:
        return None

    estimate = value.estimate
    if estimate.status not in {EstimateStatus.EXACT, EstimateStatus.BOUNDED}:
        return None
    assert estimate.upper is not None
    provenance = value.provenance
    assert provenance is not None
    return ProofUpperBound(
        dimension_id=dimension_id,
        upper=estimate.upper,
        source_id=provenance.source_id,
        justification=(
            "Upper endpoint of an existing exact/bounded preference estimate; no "
            "one-sided value was inferred from a heuristic or unmeasured estimate."
        ),
    )


def _validate_explicit_upper_bounds(
    bounds: Mapping[str, ProofUpperBound],
) -> None:
    contract = timetable_preference_dimension_contract()
    unknown = set(bounds) - contract
    if unknown:
        raise FallUpperBoundError(
            "explicit timetable upper bounds target non-activatable dimensions: "
            + ", ".join(sorted(unknown))
        )
    mismatched = [key for key, bound in bounds.items() if key != bound.dimension_id]
    if mismatched:
        raise FallUpperBoundError(
            "explicit upper-bound mapping keys must match bound dimension ids: "
            + ", ".join(sorted(mismatched))
        )


def _course_bound_is_proof_numeric(value: PreferenceValue | None) -> bool:
    return value is not None and value.estimate.status in {
        EstimateStatus.EXACT,
        EstimateStatus.BOUNDED,
    }


def audit_fall_intrinsic_upper_bound_readiness(
    preference_profile: PreferenceProfile,
    *,
    global_course_utility_bounds: Mapping[str, PreferenceValue],
    explicit_timetable_upper_bounds: Mapping[str, ProofUpperBound] | None = None,
) -> FallUpperBoundReadiness:
    """Audit whether the intrinsic Fall utility has proof-safe one-sided maxima.

    Existing exact/bounded preference values automatically provide their upper endpoint.
    Unmeasured or heuristic timetable dimensions remain blockers unless an explicit
    one-sided ``ProofUpperBound`` is supplied.  The four course envelopes are checked
    separately because they apply per selected course rather than as timetable geometry.

    Registration is intentionally not part of this intrinsic audit.  The returned object
    always marks the registration-risk layer as separate so callers cannot accidentally
    reinterpret this status as whole-registration-plan readiness.
    """

    explicit = explicit_timetable_upper_bounds or {}
    _validate_explicit_upper_bounds(explicit)

    resolved: list[ProofUpperBound] = []
    missing: list[str] = []
    for dimension in sorted(timetable_preference_dimension_contract()):
        if dimension in explicit:
            resolved.append(explicit[dimension])
            continue
        bound = _profile_upper_bound(preference_profile, dimension)
        if bound is None:
            missing.append(dimension)
        else:
            resolved.append(bound)

    missing_course = tuple(
        sorted(
            dimension
            for dimension in _REQUIRED_GLOBAL_COURSE_BOUND_DIMENSIONS
            if not _course_bound_is_proof_numeric(
                global_course_utility_bounds.get(dimension)
            )
        )
    )

    status = (
        FallUpperBoundStatus.READY
        if not missing and not missing_course
        else FallUpperBoundStatus.BLOCKED
    )
    return FallUpperBoundReadiness(
        status=status,
        timetable_upper_bounds=tuple(resolved),
        missing_timetable_dimensions=tuple(missing),
        missing_course_bound_dimensions=missing_course,
        registration_risk_layer_separate=True,
    )
