"""Explicit temporal objective policies for the Stage 4 whole-plan model.

Temporal weighting is a preference claim, not a numerical convenience.  The user clarified
on 2026-08-19 that the earlier apparent preference for the current semester was actually an
information asymmetry: Fall 2026 is known concretely, future catalogues/circumstances are
uncertain, and future decisions can be re-optimized when more information arrives.

Holding those epistemic and state-transition effects aside, intrinsic academic-semester
utility is time-neutral: +10 in Fall and -10 in a later academic semester cancel.  This
module encodes that confirmed policy explicitly rather than reviving an implicit/default
"present bias" or pretending uncertainty itself is a utility discount.

Future uncertainty, recourse, GPA/admissions consequences, and other irreversible effects
must remain separate model components.
"""

from __future__ import annotations

from collections.abc import Iterable

from .future_utility import TemporalUtilityAggregation, TemporalUtilityWeight


TIME_NEUTRAL_SOURCE_ID = "user:2026-08-19:time-neutral-intrinsic-semester-utility"


def time_neutral_temporal_aggregation(
    term_ids: Iterable[str],
) -> TemporalUtilityAggregation:
    """Return the user's confirmed equal intrinsic weight for every supplied term.

    The returned policy is explicit and provenance-bearing.  It is not a library default:
    callers must deliberately request it for the scenario being evaluated.  Each term gets
    weight 1.0, so only differences in term utility/state consequences—not distance from the
    present—change its intrinsic contribution.
    """

    ids = tuple(term_ids)
    return TemporalUtilityAggregation(
        source_id=TIME_NEUTRAL_SOURCE_ID,
        weights=tuple(TemporalUtilityWeight(term_id, 1.0) for term_id in ids),
        note=(
            "User confirmed intrinsic semester utility is time-neutral. Future uncertainty "
            "and the ability to re-optimize later are epistemic/recourse effects, not a "
            "temporal preference discount; irreversible GPA/admissions/etc. effects belong "
            "in state consequences instead."
        ),
    )
