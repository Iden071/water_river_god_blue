"""Proof-safe one-sided Fall 2026 timetable bounds from explicit user confirmation.

These bounds are intentionally weaker than final preference estimates.  They exist only to
support admissible optimistic branch bounds.

On 2026-08-20 the user confirmed that one- and two-period continuous fixed-time runs carry no
intrinsic run penalty, while a three-period run may carry a very slight negative penalty but
its magnitude is not settled.  Therefore the three-period run utility has proof-safe upper
bound 0 without being assigned a fake point value.

The user also confirmed that, holding every other consequence fixed, extending a continuous
fixed-time run beyond the already-confirmed four-period anchor cannot make the run intrinsically
better.  Any apparent benefit of a longer run (for example compressing classes into fewer
campus days or removing a gap) is represented by separate timetable features and must not be
credited to the run-length term itself.  The latest clarification specifically re-confirmed
that moving from four to five consecutive periods is worse.

Therefore, for every 5..15-period run state, the *additional* utility relative to the
four-period anchor has proof-safe upper bound 0.  The true deltas may be negative and remain
unresolved for final ranking; this module does not pretend the old flat-marathon model was
correct.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from .fall_upper_bound_readiness import ProofUpperBound


_LONG_RUN_SOURCE_ID = "user:2026-08-20:long-fixed-run-monotonicity"
_THREE_RUN_SOURCE_ID = "user:2026-08-20:three-fixed-run-slight-burden"


def fall2026_timetable_proof_upper_bounds() -> Mapping[str, ProofUpperBound]:
    """Return current user-confirmed one-sided timetable proof ceilings.

    Only dimensions with an actual one-sided confirmation belong here.  Friday-event value
    and additional weekend-attached-day value are intentionally absent and remain blockers.
    """

    values = {
        "three_fixed_period_run": ProofUpperBound(
            dimension_id="three_fixed_period_run",
            upper=0.0,
            source_id=_THREE_RUN_SOURCE_ID,
            justification=(
                "User confirmed that one- and two-period runs are unpenalized and that a "
                "three-period continuous fixed-time run may have a very slight penalty. "
                "Its magnitude is unresolved, but its intrinsic utility contribution cannot "
                "be positive, so 0 is a proof-safe optimistic ceiling."
            ),
        ),
        **{
            f"long_fixed_run_delta_{length}": ProofUpperBound(
                dimension_id=f"long_fixed_run_delta_{length}",
                upper=0.0,
                source_id=_LONG_RUN_SOURCE_ID,
                justification=(
                    "User confirmed that, holding all separately modeled consequences fixed, "
                    "a continuous fixed-time run longer than four periods cannot be intrinsically "
                    "better merely because it is longer.  Hence the additional utility relative "
                    "to the four-period anchor is <= 0.  No lower bound or point penalty is implied."
                ),
            )
            for length in range(5, 16)
        },
    }
    return MappingProxyType(values)
