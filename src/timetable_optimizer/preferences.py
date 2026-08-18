"""Preference evidence primitives for the Stage 4 rebuild.

This module represents what is known about a subjective preference before any
whole-plan utility function consumes it. It deliberately does not choose a
master score, aggregate second-major scenarios, or convert missing information
into a numerical default.

Preference evidence is not required to arrive as a scalar. A user may know
that one state is worse than another, or that two state differences are equal,
without having supplied either state with an absolute number. Linear relations
preserve those statements directly instead of forcing an invented point value.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite


class PreferenceRuleError(ValueError):
    """A preference value violates the Stage 4 preference contract."""


class PreferenceSourceKind(str, Enum):
    """Allowed origins for subjective preference information."""

    USER_INPUT = "user_input"
    DERIVED = "derived"


class EstimateStatus(str, Enum):
    """Epistemic status of a preference estimate.

    ``TRUNCATED`` and ``IMPOSSIBLE`` from the broader SPEC belong to search and
    feasibility results rather than subjective preference inputs, so they are
    intentionally not represented here.
    """

    EXACT = "exact"
    BOUNDED = "bounded"
    HEURISTIC = "heuristic"
    UNMEASURED = "unmeasured"


class PreferenceRelationKind(str, Enum):
    """Comparison operator for a linear relation among preference dimensions."""

    EQUAL = "equal"
    LESS_THAN = "less_than"
    LESS_OR_EQUAL = "less_or_equal"
    GREATER_THAN = "greater_than"
    GREATER_OR_EQUAL = "greater_or_equal"


@dataclass(frozen=True)
class PreferenceProvenance:
    """Trace a subjective statement to user input or a transparent derivation."""

    source_kind: PreferenceSourceKind
    source_id: str
    description: str = ""
    derivation: str | None = None

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise PreferenceRuleError("preference provenance requires a nonblank source_id")

        if self.source_kind is PreferenceSourceKind.DERIVED:
            if self.derivation is None or not self.derivation.strip():
                raise PreferenceRuleError(
                    "derived preference provenance requires a transparent derivation"
                )
        elif self.derivation is not None and self.derivation.strip():
            raise PreferenceRuleError(
                "direct user input must not be mislabeled with a derivation"
            )


@dataclass(frozen=True)
class PreferenceEstimate:
    """A point, interval, heuristic estimate, or explicitly missing value."""

    status: EstimateStatus
    point: float | None = None
    lower: float | None = None
    upper: float | None = None

    def __post_init__(self) -> None:
        for value in (self.point, self.lower, self.upper):
            if value is not None and not isfinite(value):
                raise PreferenceRuleError("preference estimates must be finite")

        if self.status is EstimateStatus.EXACT:
            if self.point is None or self.lower != self.point or self.upper != self.point:
                raise PreferenceRuleError(
                    "exact preference estimates require point == lower == upper"
                )
            return

        if self.status is EstimateStatus.BOUNDED:
            if self.point is not None or self.lower is None or self.upper is None:
                raise PreferenceRuleError(
                    "bounded preference estimates require lower/upper and no point"
                )
            if self.lower > self.upper:
                raise PreferenceRuleError("preference lower bound exceeds upper bound")
            return

        if self.status is EstimateStatus.HEURISTIC:
            if self.point is None:
                raise PreferenceRuleError("heuristic preference estimates require a point")
            if (self.lower is None) != (self.upper is None):
                raise PreferenceRuleError(
                    "heuristic preference bounds must be supplied together"
                )
            if self.lower is not None and not (self.lower <= self.point <= self.upper):
                raise PreferenceRuleError(
                    "heuristic preference point must lie inside supplied bounds"
                )
            return

        if self.status is EstimateStatus.UNMEASURED:
            if self.point is not None or self.lower is not None or self.upper is not None:
                raise PreferenceRuleError(
                    "unmeasured preference estimates cannot carry numerical values"
                )
            return

        raise PreferenceRuleError(f"unsupported preference estimate status: {self.status!r}")

    @classmethod
    def exact(cls, value: float) -> "PreferenceEstimate":
        return cls(EstimateStatus.EXACT, point=value, lower=value, upper=value)

    @classmethod
    def bounded(cls, lower: float, upper: float) -> "PreferenceEstimate":
        return cls(EstimateStatus.BOUNDED, lower=lower, upper=upper)

    @classmethod
    def heuristic(
        cls,
        point: float,
        *,
        lower: float | None = None,
        upper: float | None = None,
    ) -> "PreferenceEstimate":
        return cls(EstimateStatus.HEURISTIC, point=point, lower=lower, upper=upper)

    @classmethod
    def unmeasured(cls) -> "PreferenceEstimate":
        return cls(EstimateStatus.UNMEASURED)

    @property
    def bounds(self) -> tuple[float, float] | None:
        if self.lower is None or self.upper is None:
            return None
        return (self.lower, self.upper)

    def require_exact(self) -> float:
        """Return the point only when exact; never coerce uncertainty to a scalar."""

        if self.status is not EstimateStatus.EXACT or self.point is None:
            raise PreferenceRuleError(
                f"preference estimate is {self.status.value}, not exact"
            )
        return self.point


@dataclass(frozen=True)
class PreferenceValue:
    """One named subjective preference together with evidence and uncertainty."""

    dimension_id: str
    estimate: PreferenceEstimate
    provenance: PreferenceProvenance | None = None
    label: str = ""

    def __post_init__(self) -> None:
        if not self.dimension_id.strip():
            raise PreferenceRuleError("preference value requires a nonblank dimension_id")

        if self.estimate.status is not EstimateStatus.UNMEASURED and self.provenance is None:
            raise PreferenceRuleError(
                "every numerical preference estimate requires explicit provenance"
            )


@dataclass(frozen=True)
class LinearPreferenceTerm:
    """One coefficient in a linear preference relation."""

    dimension_id: str
    coefficient: float = 1.0

    def __post_init__(self) -> None:
        if not self.dimension_id.strip():
            raise PreferenceRuleError(
                "linear preference term requires a nonblank dimension_id"
            )
        if not isfinite(self.coefficient) or self.coefficient == 0:
            raise PreferenceRuleError(
                "linear preference term coefficient must be finite and nonzero"
            )


@dataclass(frozen=True)
class LinearPreferenceRelation:
    """Preserve a comparison without manufacturing absolute weights.

    The relation is interpreted as::

        sum(term.coefficient * utility(term.dimension_id))  relation  rhs

    For example, if larger utility is better, "missing dinner is worse than
    missing lunch" can be stored as ``dinner - lunch < 0``. A later solver may
    combine such evidence with anchors or bounds, but this layer does not do so.
    """

    terms: tuple[LinearPreferenceTerm, ...]
    relation: PreferenceRelationKind
    rhs: float
    provenance: PreferenceProvenance
    label: str = ""

    def __post_init__(self) -> None:
        if not self.terms:
            raise PreferenceRuleError(
                "linear preference relation requires at least one term"
            )
        if not isfinite(self.rhs):
            raise PreferenceRuleError("linear preference relation rhs must be finite")

        dimension_ids = [term.dimension_id for term in self.terms]
        if len(dimension_ids) != len(set(dimension_ids)):
            raise PreferenceRuleError(
                "linear preference relation must combine duplicate dimensions explicitly"
            )


@dataclass(frozen=True)
class PreferenceProfile:
    """A validated bundle of scalar and relational preference evidence."""

    profile_id: str
    values: tuple[PreferenceValue, ...] = ()
    relations: tuple[LinearPreferenceRelation, ...] = ()

    def __post_init__(self) -> None:
        if not self.profile_id.strip():
            raise PreferenceRuleError("preference profile requires a nonblank profile_id")
        ids = [value.dimension_id for value in self.values]
        if len(ids) != len(set(ids)):
            raise PreferenceRuleError(
                "preference profile cannot contain duplicate scalar dimensions"
            )

    def value(self, dimension_id: str) -> PreferenceValue:
        hits = [value for value in self.values if value.dimension_id == dimension_id]
        if len(hits) != 1:
            raise PreferenceRuleError(
                f"expected exactly one preference value {dimension_id!r}, found {len(hits)}"
            )
        return hits[0]

    @property
    def unmeasured_dimensions(self) -> frozenset[str]:
        return frozenset(
            value.dimension_id
            for value in self.values
            if value.estimate.status is EstimateStatus.UNMEASURED
        )
