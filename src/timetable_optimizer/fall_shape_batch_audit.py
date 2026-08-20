"""Bounded real-candidate exposure audit for provisional Fall shape sensitivity.

This module deliberately does **not** sample randomly and does not claim representativeness.
It consumes whichever exact candidate batch the caller supplies (for example the first N nodes
from the resumable bitset DFS) and answers only:

* which unresolved timetable-shape families actually activate in that batch;
* which exact state dimensions activate;
* how many distinct exact unresolved-shape signatures occur;
* how far the archival diagnostic scenarios move those unresolved contributions.

An enumeration prefix can establish *existence* of an activation but cannot establish its
population frequency or whether the eventual optimum depends on it.  The result therefore
carries an explicit ``representative=False`` flag and must never be used as a pruning proof.
The signature count is an engineering diagnostic only: a small count can justify retaining
symbolic alternatives, while a large count warns that another compact representation may be
needed.  It says nothing about which signature is preferable.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType
from typing import Iterable, Mapping

from .fall_candidate_sets import FallCandidateSet
from .fall_shape_diagnostics import assess_archival_shape_sensitivity
from .fall_unresolved_shape import (
    FallUnresolvedShapeSignature,
    unresolved_shape_signature,
)
from .timetable_quality import extract_timetable_quality
from .timetable_utility import timetable_preference_quantities


class FallShapeBatchAuditError(ValueError):
    """Candidate-batch diagnostic inputs are invalid."""


@dataclass(frozen=True)
class FallShapeBatchAudit:
    candidates_seen: int
    candidates_evaluated: int
    candidates_skipped_unresolved_schedule: int
    candidates_below_credit_floor: int
    minimum_known_ordinary_credits: float
    family_activation_counts: Mapping[str, int]
    state_activation_counts: Mapping[str, int]
    distinct_unresolved_shape_signatures: int
    most_common_unresolved_shape_signatures: tuple[
        tuple[FallUnresolvedShapeSignature, int], ...
    ]
    maximum_archival_spread: float
    maximum_spread_section_ids: tuple[str, ...]
    uncovered_archival_state_dimensions: tuple[str, ...]
    representative: bool = False
    proof_evidence: bool = False

    def __post_init__(self) -> None:
        if self.candidates_seen < 0 or self.candidates_evaluated < 0:
            raise FallShapeBatchAuditError("candidate counters cannot be negative")
        if not isfinite(self.minimum_known_ordinary_credits):
            raise FallShapeBatchAuditError("credit floor must be finite")
        if self.distinct_unresolved_shape_signatures < 0:
            raise FallShapeBatchAuditError("distinct signature count cannot be negative")
        if self.distinct_unresolved_shape_signatures > self.candidates_evaluated:
            raise FallShapeBatchAuditError(
                "distinct signature count cannot exceed evaluated candidates"
            )
        if len(self.most_common_unresolved_shape_signatures) > 10:
            raise FallShapeBatchAuditError("diagnostic retains at most ten common signatures")
        for _, count in self.most_common_unresolved_shape_signatures:
            if count <= 0:
                raise FallShapeBatchAuditError("common signature counts must be positive")
        if self.representative or self.proof_evidence:
            raise FallShapeBatchAuditError(
                "bounded DFS batch diagnostics cannot claim representativeness or proof status"
            )


def _family_for_dimension(dimension: str) -> str | None:
    if dimension == "friday_event_window_free":
        return "friday_event_value"
    if dimension.startswith("long_fixed_run_delta_"):
        return "long_fixed_run_shape"
    if dimension.startswith("weekend_attached_presence_free_extra_total_"):
        return "weekend_attached_run_shape"
    return None


def audit_candidate_shape_batch(
    candidates: Iterable[FallCandidateSet],
    *,
    minimum_known_ordinary_credits: float = 0.0,
) -> FallShapeBatchAudit:
    """Audit shape exposure in one caller-supplied exact candidate batch.

    ``minimum_known_ordinary_credits`` is a diagnostic filter only.  It does not change the
    optimizer's candidate family and must not be described as an admissibility constraint.
    """

    if not isfinite(minimum_known_ordinary_credits) or minimum_known_ordinary_credits < 0:
        raise FallShapeBatchAuditError(
            "minimum_known_ordinary_credits must be finite and nonnegative"
        )

    seen = 0
    evaluated = 0
    skipped_schedule = 0
    below_floor = 0
    family_counts: dict[str, int] = {
        "friday_event_value": 0,
        "long_fixed_run_shape": 0,
        "weekend_attached_run_shape": 0,
    }
    state_counts: dict[str, int] = {}
    signature_counts: Counter[FallUnresolvedShapeSignature] = Counter()
    max_spread = 0.0
    max_ids: tuple[str, ...] = ()
    uncovered: set[str] = set()

    for candidate in candidates:
        seen += 1
        if candidate.load.known_ordinary_credits < minimum_known_ordinary_credits:
            below_floor += 1
            continue
        if candidate.unresolved_schedule_section_ids:
            skipped_schedule += 1
            continue

        facts = extract_timetable_quality(candidate.sections)
        quantities = timetable_preference_quantities(facts)
        signature_counts[unresolved_shape_signature(facts)] += 1

        active_families: set[str] = set()
        for dimension, quantity in quantities.items():
            family = _family_for_dimension(dimension)
            if family is None or quantity <= 0:
                continue
            active_families.add(family)
            state_counts[dimension] = state_counts.get(dimension, 0) + 1
        for family in active_families:
            family_counts[family] += 1

        sensitivity = assess_archival_shape_sensitivity(quantities)
        uncovered.update(sensitivity.unresolved_shape_dimensions_not_covered)
        spread = sensitivity.spread or 0.0
        if spread > max_spread:
            max_spread = spread
            max_ids = candidate.section_ids
        evaluated += 1

    return FallShapeBatchAudit(
        candidates_seen=seen,
        candidates_evaluated=evaluated,
        candidates_skipped_unresolved_schedule=skipped_schedule,
        candidates_below_credit_floor=below_floor,
        minimum_known_ordinary_credits=minimum_known_ordinary_credits,
        family_activation_counts=MappingProxyType(dict(sorted(family_counts.items()))),
        state_activation_counts=MappingProxyType(dict(sorted(state_counts.items()))),
        distinct_unresolved_shape_signatures=len(signature_counts),
        most_common_unresolved_shape_signatures=tuple(signature_counts.most_common(10)),
        maximum_archival_spread=max_spread,
        maximum_spread_section_ids=max_ids,
        uncovered_archival_state_dimensions=tuple(sorted(uncovered)),
        representative=False,
        proof_evidence=False,
    )
