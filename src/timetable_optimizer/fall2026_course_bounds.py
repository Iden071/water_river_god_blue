"""Proof-safe Fall 2026 course-utility envelopes from explicit user input.

These are deliberately *bounds*, not point scores.  They exist so an exact search may
compute admissible optimistic/pessimistic utility envelopes without asking the user to rate
every course before pruning can begin.

The user supplied conservative best-to-worst impact spans and then confirmed a neutral-zero
convention on 2026-08-19:

* professor / teaching quality span <= 8;
* workload span <= 15, with very light workload approaching 0 and extra workload negative;
* intrinsic subject interest span <= 3, with neutral interest at 0;
* pure cognitive difficulty span <= 5, with very easy material approaching 0 and extra
  difficulty negative.

For workload and difficulty this gives one-sided utility envelopes [-15, 0] and [-5, 0].
For professor quality and subject interest, the user explicitly allows both positive and
negative effects around neutral 0.  A span ceiling alone does not identify where zero sits
inside the true range.  Therefore the proof-safe *outer* envelopes are [-8, +8] and
[-3, +3].  These outer envelopes are intentionally looser than the true <=8 / <=3 span;
they do not assert a 16- or 6-point true best-to-worst difference.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from .preferences import (
    PreferenceEstimate,
    PreferenceProvenance,
    PreferenceSourceKind,
    PreferenceValue,
)


PROFESSOR_UTILITY_BOUND = "professor_rating_to_utility"
SUBJECT_INTEREST_BOUND = "subject_interest"
WORKLOAD_BOUND = "workload"
DIFFICULTY_BOUND = "difficulty"


def _derived_bound(
    dimension_id: str,
    lower: float,
    upper: float,
    *,
    description: str,
    derivation: str,
) -> PreferenceValue:
    return PreferenceValue(
        dimension_id=dimension_id,
        estimate=PreferenceEstimate.bounded(lower, upper),
        provenance=PreferenceProvenance(
            source_kind=PreferenceSourceKind.DERIVED,
            source_id="user:2026-08-19:course-impact-bounds-neutral-zero",
            description=description,
            derivation=derivation,
        ),
        label=description,
    )


def fall2026_course_utility_bounds() -> Mapping[str, PreferenceValue]:
    """Return global per-course utility envelopes usable for proof-safe relaxation.

    The keys match the section-local blocker dimensions used by the Fall pruning-readiness
    audit.  Returning a read-only mapping helps keep these elicited bounds distinct from
    mutable course-specific ratings or later best estimates.
    """

    values = {
        PROFESSOR_UTILITY_BOUND: _derived_bound(
            "global_course_bound::professor_quality",
            -8.0,
            8.0,
            description="Professor / teaching quality utility outer envelope",
            derivation=(
                "User confirmed neutral professor quality = 0, good/bad professor effects "
                "may be positive/negative, and the true best-to-worst professor impact span "
                "is at most 8. If min <= 0 <= max and max-min <= 8, then min >= -8 and "
                "max <= +8; therefore [-8,+8] is a conservative outer envelope without "
                "assuming the true range is symmetric."
            ),
        ),
        SUBJECT_INTEREST_BOUND: _derived_bound(
            "global_course_bound::subject_interest",
            -3.0,
            3.0,
            description="Intrinsic subject-interest utility outer envelope",
            derivation=(
                "User confirmed neutral subject interest = 0, interesting/uninteresting "
                "subjects may contribute positively/negatively, and the true best-to-worst "
                "interest impact span is at most 3. Hence every possible value lies within "
                "[-3,+3], without assuming the true range is symmetric."
            ),
        ),
        WORKLOAD_BOUND: _derived_bound(
            "global_course_bound::workload",
            -15.0,
            0.0,
            description="Course workload utility envelope",
            derivation=(
                "User confirmed that a very light workload approaches neutral utility 0, "
                "additional workload is negative, and the conservative best-to-worst "
                "workload impact span is at most 15; therefore workload utility is bounded "
                "by [-15,0]."
            ),
        ),
        DIFFICULTY_BOUND: _derived_bound(
            "global_course_bound::difficulty",
            -5.0,
            0.0,
            description="Pure cognitive-difficulty utility envelope",
            derivation=(
                "User confirmed that cognitively easy material approaches neutral utility "
                "0, additional pure cognitive difficulty is negative, and the conservative "
                "best-to-worst difficulty impact span is at most 5; therefore pure "
                "difficulty utility is bounded by [-5,0]."
            ),
        ),
    }
    return MappingProxyType(values)
