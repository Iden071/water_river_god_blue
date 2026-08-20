"""Registration evidence primitives for Stage 4C.

Registration has two logically different questions:

1. Is an observed institutional gate known to block this student?
2. If not blocked, how obtainable is the section under the applicable registration regime?

The legacy model sometimes returned ``1.0`` for question 2 when it had only answered
question 1.  Stage 4 makes that state impossible: evidence that a year-quota gate does not
block a freshman never becomes a probability of successful registration.

This module also preserves historical mileage observations as *applicant-distribution
signals*.  It does not reinterpret min/avg/max applicant bids as winning cutoffs and does
not calibrate them into a probability without a separate validated model.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Any, Iterable, Mapping


class RegistrationEvidenceError(ValueError):
    """Registration evidence violates the Stage 4 evidence contract."""


class RegistrationRegime(str, Enum):
    """Registration mechanism relevant to the user."""

    FRESHMAN_WAITLIST = "freshman_waitlist"
    MILEAGE = "mileage"


class YearQuotaGateStatus(str, Enum):
    """What the observed per-year quota table establishes, and no more."""

    NO_OBSERVATION = "no_observation"
    NO_YEAR_SCHEME = "no_year_scheme"
    FRESHMAN_ALLOWED_BY_SCHEME = "freshman_allowed_by_scheme"
    FRESHMAN_BLOCKED_BY_SCHEME = "freshman_blocked_by_scheme"


class ObtainabilityStatus(str, Enum):
    """Epistemic status of a registration-success estimate."""

    EXACT = "exact"
    BOUNDED = "bounded"
    HEURISTIC = "heuristic"
    UNMEASURED = "unmeasured"


@dataclass(frozen=True)
class ObtainabilityEstimate:
    """Probability-like evidence, constrained to [0,1] and explicitly typed."""

    status: ObtainabilityStatus
    point: float | None = None
    lower: float | None = None
    upper: float | None = None
    basis: str = ""

    def __post_init__(self) -> None:
        for value in (self.point, self.lower, self.upper):
            if value is not None:
                if not isfinite(value) or not 0.0 <= value <= 1.0:
                    raise RegistrationEvidenceError(
                        "obtainability probabilities must be finite and in [0,1]"
                    )

        if self.status is ObtainabilityStatus.EXACT:
            if self.point is None or self.lower != self.point or self.upper != self.point:
                raise RegistrationEvidenceError(
                    "exact obtainability requires point == lower == upper"
                )
        elif self.status is ObtainabilityStatus.BOUNDED:
            if self.point is not None or self.lower is None or self.upper is None:
                raise RegistrationEvidenceError(
                    "bounded obtainability requires lower/upper and no point"
                )
            if self.lower > self.upper:
                raise RegistrationEvidenceError("obtainability lower bound exceeds upper")
        elif self.status is ObtainabilityStatus.HEURISTIC:
            if self.point is None:
                raise RegistrationEvidenceError(
                    "heuristic obtainability requires a point estimate"
                )
            if (self.lower is None) != (self.upper is None):
                raise RegistrationEvidenceError(
                    "heuristic bounds must be supplied together"
                )
            if self.lower is not None and not (self.lower <= self.point <= self.upper):
                raise RegistrationEvidenceError(
                    "heuristic point must lie inside supplied bounds"
                )
        elif self.status is ObtainabilityStatus.UNMEASURED:
            if self.point is not None or self.lower is not None or self.upper is not None:
                raise RegistrationEvidenceError(
                    "unmeasured obtainability cannot contain numeric probability"
                )
        else:
            raise RegistrationEvidenceError(
                f"unsupported obtainability status: {self.status!r}"
            )

    @classmethod
    def unmeasured(cls, basis: str = "") -> "ObtainabilityEstimate":
        return cls(ObtainabilityStatus.UNMEASURED, basis=basis)


@dataclass(frozen=True)
class FreshmanQuotaObservation:
    """One section's observed six-year quota vector."""

    section_id: str
    year_quotas: tuple[int, int, int, int, int, int]
    source_id: str

    def __post_init__(self) -> None:
        if not self.section_id.strip() or not self.source_id.strip():
            raise RegistrationEvidenceError(
                "freshman quota observation requires section_id and source_id"
            )
        if any((not isinstance(value, int)) or value < 0 for value in self.year_quotas):
            raise RegistrationEvidenceError(
                "year quotas must be six nonnegative integers"
            )

    @property
    def gate_status(self) -> YearQuotaGateStatus:
        # Verified repository rule: all-zero means no per-year scheme, not that
        # every year is forbidden.
        if not any(self.year_quotas):
            return YearQuotaGateStatus.NO_YEAR_SCHEME
        if self.year_quotas[0] == 0:
            return YearQuotaGateStatus.FRESHMAN_BLOCKED_BY_SCHEME
        return YearQuotaGateStatus.FRESHMAN_ALLOWED_BY_SCHEME


@dataclass(frozen=True)
class HistoricalMileageObservation:
    """Historical applicant-bid summary for one section offering.

    ``min_bid``, ``average_bid``, and ``max_bid`` describe observed applicants, not
    successful registrants.  ``applicant_count`` is retained separately from any seat-like
    field so a later model cannot silently reinterpret the statistics as a winning cutoff.
    """

    course_code: str
    section_id: str
    term: str
    campus: str
    applicant_count: int | None
    min_bid: float | None
    average_bid: float | None
    max_bid: float | None
    course_bid_ceiling: float | None
    source_id: str

    def __post_init__(self) -> None:
        if not self.course_code.strip() or not self.section_id.strip():
            raise RegistrationEvidenceError(
                "mileage observation requires course_code and section_id"
            )
        if not self.source_id.strip():
            raise RegistrationEvidenceError("mileage observation requires source_id")
        if self.applicant_count is not None and self.applicant_count < 0:
            raise RegistrationEvidenceError("applicant_count cannot be negative")
        for value in (
            self.min_bid,
            self.average_bid,
            self.max_bid,
            self.course_bid_ceiling,
        ):
            if value is not None and (not isfinite(value) or value < 0):
                raise RegistrationEvidenceError(
                    "mileage bid statistics must be finite and nonnegative"
                )
        numeric = [
            value for value in (self.min_bid, self.average_bid, self.max_bid)
            if value is not None
        ]
        if len(numeric) == 3 and not (
            self.min_bid <= self.average_bid <= self.max_bid  # type: ignore[operator]
        ):
            raise RegistrationEvidenceError(
                "mileage applicant statistics must satisfy min <= average <= max"
            )


@dataclass(frozen=True)
class RegistrationAssessment:
    """Registration evidence for a concrete section under one regime."""

    section_id: str
    regime: RegistrationRegime
    year_quota_status: YearQuotaGateStatus
    freshman_quota: int | None
    obtainability: ObtainabilityEstimate
    quota_source_id: str | None = None
    competition_observations: tuple[HistoricalMileageObservation, ...] = ()

    @property
    def blocked_by_observed_year_gate(self) -> bool:
        return self.year_quota_status is YearQuotaGateStatus.FRESHMAN_BLOCKED_BY_SCHEME

    @property
    def obtainability_is_known(self) -> bool:
        return self.obtainability.status is not ObtainabilityStatus.UNMEASURED


def _int_or_zero(value: Any) -> int:
    if value in (None, ""):
        return 0
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise RegistrationEvidenceError(
            f"invalid year-quota value: {value!r}"
        ) from exc
    if parsed < 0:
        raise RegistrationEvidenceError("year quota cannot be negative")
    return parsed


def freshman_quota_observation_from_row(
    section_id: str,
    row: Mapping[str, Any],
    *,
    source_id: str,
) -> FreshmanQuotaObservation:
    """Build a quota observation from a Fall seat-data row."""

    quotas = tuple(_int_or_zero(row.get(f"sy{i}PercpCnt")) for i in range(1, 7))
    return FreshmanQuotaObservation(
        section_id=section_id,
        year_quotas=quotas,  # type: ignore[arg-type]
        source_id=source_id,
    )


def assess_freshman_registration(
    section_id: str,
    seat_rows: Mapping[str, Mapping[str, Any]],
    *,
    source_id: str = "fall2026_seats.json",
) -> RegistrationAssessment:
    """Assess Fall freshman registration without inventing a success probability.

    A missing row is *not* interpreted as either permission or prohibition.  An all-zero
    quota vector means no year-specific quota scheme.  A nonzero scheme with year-1 quota
    equal to zero is an observed year-gate block.  In every non-blocked case, obtainability
    remains UNMEASURED until a first-come/waitlist competition model is actually validated.
    """

    row = seat_rows.get(section_id)
    if row is None:
        return RegistrationAssessment(
            section_id=section_id,
            regime=RegistrationRegime.FRESHMAN_WAITLIST,
            year_quota_status=YearQuotaGateStatus.NO_OBSERVATION,
            freshman_quota=None,
            obtainability=ObtainabilityEstimate.unmeasured(
                "no section quota observation; absence is not evidence of success or failure"
            ),
        )

    observation = freshman_quota_observation_from_row(
        section_id,
        row,
        source_id=f"{source_id}:{section_id}",
    )
    status = observation.gate_status
    quota = observation.year_quotas[0] if status is not YearQuotaGateStatus.NO_YEAR_SCHEME else None

    if status is YearQuotaGateStatus.FRESHMAN_BLOCKED_BY_SCHEME:
        # This is exact evidence about the year gate, not a general-purpose probability
        # model.  The section is impossible for a freshman under this observed scheme.
        obtainability = ObtainabilityEstimate(
            status=ObtainabilityStatus.EXACT,
            point=0.0,
            lower=0.0,
            upper=0.0,
            basis="observed year-quota scheme assigns zero seats to first-year students",
        )
    else:
        obtainability = ObtainabilityEstimate.unmeasured(
            "year-quota evidence does not establish first-come/waitlist acquisition odds"
        )

    return RegistrationAssessment(
        section_id=section_id,
        regime=RegistrationRegime.FRESHMAN_WAITLIST,
        year_quota_status=status,
        freshman_quota=quota,
        obtainability=obtainability,
        quota_source_id=observation.source_id,
    )


def historical_mileage_observation_from_row(
    row: Mapping[str, Any],
    *,
    source_id: str,
) -> HistoricalMileageObservation:
    """Preserve one historical mileage row without deriving a win probability."""

    def optional_float(key: str) -> float | None:
        raw = row.get(key)
        if raw in (None, ""):
            return None
        try:
            return float(raw)
        except (TypeError, ValueError) as exc:
            raise RegistrationEvidenceError(
                f"invalid {key} value: {raw!r}"
            ) from exc

    raw_count = row.get("cnt")
    applicant_count = None if raw_count in (None, "") else int(raw_count)
    course_code = str(row.get("subjtnb") or "").strip()
    section_id = str(row.get("subjtnbNo") or "").strip()
    if not section_id:
        division = str(row.get("corseDvclsNo") or "").strip()
        practice = str(row.get("prctsCorseDvclsNo") or "").strip()
        if course_code and division:
            section_id = f"{course_code}-{division}-{practice or '00'}"

    year = str(row.get("syy") or "").strip()
    semester = str(row.get("smtDivCd") or "").strip()
    term = f"{year}:{semester}" if year or semester else "unknown"

    return HistoricalMileageObservation(
        course_code=course_code,
        section_id=section_id,
        term=term,
        campus=str(row.get("campsDivNm") or "").strip(),
        applicant_count=applicant_count,
        min_bid=optional_float("minMlg"),
        average_bid=optional_float("avgMlg"),
        max_bid=optional_float("maxMlg"),
        course_bid_ceiling=optional_float("usePosblMaxMlgVal"),
        source_id=source_id,
    )


def mileage_evidence_for_course(
    course_code: str,
    rows: Iterable[Mapping[str, Any]],
    *,
    source_id: str = "mileage_history.json",
) -> tuple[HistoricalMileageObservation, ...]:
    """Return typed historical applicant signals for one course, with no calibration."""

    out: list[HistoricalMileageObservation] = []
    for index, row in enumerate(rows):
        if str(row.get("subjtnb") or "").strip() != course_code:
            continue
        out.append(
            historical_mileage_observation_from_row(
                row,
                source_id=f"{source_id}:{index}",
            )
        )
    return tuple(out)
