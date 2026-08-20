"""Proof-safe one-sided Fall 2026 timetable bounds from explicit user confirmation.

These bounds are intentionally weaker than final preference estimates.  They exist only to
support admissible optimistic branch bounds.

On 2026-08-20 the user confirmed that, holding every other consequence fixed, extending a
continuous fixed-time run beyond the already-confirmed four-period anchor cannot make the
run intrinsically better.  Any apparent benefit of a longer run (for example compressing
classes into fewer campus days or removing a gap) is represented by separate timetable
features and must not be credited to the run-length term itself.

Therefore, for every 5..15-period run state, the *additional* utility relative to the
four-period anchor has proof-safe upper bound 0.  The true delta may be negative and remains
unresolved for final ranking; this module does not pretend the old flat-marathon model was
correct.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from .fall_upper_bound_readiness import ProofUpperBound


_SOURCE_ID = "user:2026-08-20:long-fixed-run-monotonicity"


def fall2026_timetable_proof_upper_bounds() -> Mapping[str, ProofUpperBound]:
    """Return current user-confirmed one-sided timetable proof ceilings.

    Only dimensions with an actual one-sided confirmation belong here.  Friday-event value
    and additional weekend-attached-day value are intentionally absent and remain blockers.
    """

    values = {
        f"long_fixed_run_delta_{length}": ProofUpperBound(
            dimension_id=f"long_fixed_run_delta_{length}",
            upper=0.0,
            source_id=_SOURCE_ID,
            justification=(
                "User confirmed that, holding all separately modeled consequences fixed, "
                "a continuous fixed-time run longer than four periods cannot be intrinsically "
                "better merely because it is longer.  Hence the additional utility relative "
                "to the four-period anchor is <= 0.  No lower bound or point penalty is implied."
            ),
        )
        for length in range(5, 16)
    }
    return MappingProxyType(values)
