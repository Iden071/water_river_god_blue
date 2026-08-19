"""Non-lossy future-term utility evidence for Stage 4D.

Reachability proves whether an explicit future scenario can finish the degree.  Optimization
needs more: it must retain how each reachable history feels without reviving the old habit
of collapsing unknowns into a single score.

This module therefore evaluates one *selected* future academic term using the same evidence
semantics as Stage 4C:

* exact/bounded values contribute to a measured interval;
* heuristic values remain a separate point delta;
* unmeasured dimensions remain explicit;
* a known professor rating remains raw evidence until a rating-to-utility conversion is
  actually elicited;
* a non-parsed future schedule blocks exact timetable utility rather than becoming free time.

A history is deliberately **not** summed by default.  Equal weighting of future semesters is
itself a preference assumption.  ``FutureUtilityHistory`` preserves per-term assessments and
only produces a cross-term aggregate when an explicit ``TemporalUtilityAggregation`` is
supplied.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping

from .course_preferences import (
    ProfessorRatingBook,
    ProfessorRatingLookup,
)
from .future_opportunities import FutureOffering
from .future_scenarios import FutureTermScenario, TermActivity
from .preferences import EstimateStatus, PreferenceValue
from .sections import ParsedSchedule
from .timetable_quality import (
    TimetableQualityFacts,
    extract_timetable_quality_from_parsed_schedules,
)
from .timetable_utility import (
    PartialUtilityAssessment,
    UnresolvedUtilityDimension,
    UtilityContribution,
    evaluate_timetable_utility,
)
from .preferences import PreferenceProfile


class FutureUtilityError(ValueError):
    """Future utility evidence violates the Stage 4D utility contract."""


@dataclass(frozen=True)
class FutureOfferingPreferenceEvidence:
    """Course-level subjective evidence for one hypothetical future offering."""

    offering_id: str
    course_code: str
    professor: ProfessorRatingLookup
    subject_interest: PreferenceValue
    workload_utility: PreferenceValue
    difficulty_utility: PreferenceValue


@dataclass(frozen=True)
class FutureTermUtilityAssessment:
    """One selected future term without cross-term aggregation assumptions."""

    term_id: str
    offering_ids: tuple[str, ...]
    timetable_facts: TimetableQualityFacts | None
    timetable_utility: PartialUtilityAssessment | None
    course_preferences: tuple[FutureOfferingPreferenceEvidence, ...]
    course_contributions: tuple[UtilityContribution, ...]
    unresolved: tuple[UnresolvedUtilityDimension, ...]
    measured_lower: float
    measured_upper: float
    heuristic_point_delta: float
    academic_utility_applicable: bool = True

    @property
    def has_heuristics(self) -> bool:
        timetable_has = (
            self.timetable_utility is not None
            and self.timetable_utility.has_heuristics
        )
        course_has = any(
            contribution.status is EstimateStatus.HEURISTIC
            for contribution in self.course_contributions
        )
        return timetable_has or course_has

    @property
    def has_unresolved(self) -> bool:
        timetable_unresolved = (
            self.timetable_utility is not None
            and self.timetable_utility.has_unresolved
        )
        return timetable_unresolved or bool(self.unresolved)

    @property
    def complete_bounds(self) -> tuple[float, float] | None:
        """Whole academic-term bounds only when no represented utility was dropped."""

        if not self.academic_utility_applicable:
            return (0.0, 0.0)
        if self.has_heuristics or self.has_unresolved or self.timetable_utility is None:
            return None
        return (self.measured_lower, self.measured_upper)

    @property
    def unresolved_dimensions(self) -> frozenset[str]:
        out = {item.dimension_id for item in self.unresolved}
        if self.timetable_utility is not None:
            out.update(self.timetable_utility.unresolved_dimensions)
        return frozenset(out)


@dataclass(frozen=True)
class FutureUtilityHistory:
    """Ordered per-term utility evidence for one future history.

    ``aggregate_bounds`` intentionally requires an explicit temporal aggregation policy;
    merely constructing a history does not imply equal weighting across semesters.
    """

    terms: tuple[FutureTermUtilityAssessment, ...]

    def __post_init__(self) -> None:
        ids = [term.term_id for term in self.terms]
        if len(ids) != len(set(ids)):
            raise FutureUtilityError("future utility history contains duplicate term ids")

    @property
    def term_ids(self) -> tuple[str, ...]:
        return tuple(term.term_id for term in self.terms)

    @property
    def unresolved_dimensions(self) -> frozenset[str]:
        return frozenset(
            f"{term.term_id}::{dimension}"
            for term in self.terms
            for dimension in term.unresolved_dimensions
        )

    @property
    def temporal_aggregation_resolved(self) -> bool:
        # A history object itself deliberately carries no default cross-term weights.
        return False


@dataclass(frozen=True)
class TemporalUtilityWeight:
    """Explicit exact weight for one academic term in a fixed future scenario."""

    term_id: str
    weight: float

    def __post_init__(self) -> None:
        if not self.term_id.strip():
            raise FutureUtilityError("temporal utility weight requires term_id")
        if not isfinite(self.weight) or self.weight < 0:
            raise FutureUtilityError(
                "temporal utility weight must be finite and nonnegative"
            )


@dataclass(frozen=True)
class TemporalUtilityAggregation:
    """Explicit cross-term weighting assumption with provenance."""

    source_id: str
    weights: tuple[TemporalUtilityWeight, ...]
    note: str = ""

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise FutureUtilityError("temporal utility aggregation requires source_id")
        ids = [weight.term_id for weight in self.weights]
        if len(ids) != len(set(ids)):
            raise FutureUtilityError(
                "temporal utility aggregation contains duplicate term ids"
            )

    def weight_for(self, term_id: str) -> float:
        hits = [weight.weight for weight in self.weights if weight.term_id == term_id]
        if len(hits) != 1:
            raise FutureUtilityError(
                f"expected exactly one temporal weight for term {term_id!r}, found {len(hits)}"
            )
        return hits[0]


@dataclass(frozen=True)
class AggregatedFutureUtility:
    """Cross-term utility after an explicit temporal aggregation assumption."""

    source_id: str
    measured_lower: float
    measured_upper: float
    heuristic_point_delta: float
    unresolved_dimensions: frozenset[str]

    @property
    def complete_bounds(self) -> tuple[float, float] | None:
        if self.heuristic_point_delta != 0.0 or self.unresolved_dimensions:
            return None
        return (self.measured_lower, self.measured_upper)


def _unmeasured(dimension_id: str, label: str) -> PreferenceValue:
    from .preferences import PreferenceEstimate

    return PreferenceValue(
        dimension_id=dimension_id,
        estimate=PreferenceEstimate.unmeasured(),
        label=label,
    )


def _value_contribution(
    value: PreferenceValue,
    *,
    scoped_dimension_id: str,
) -> tuple[UtilityContribution | None, UnresolvedUtilityDimension | None]:
    estimate = value.estimate
    if estimate.status is EstimateStatus.UNMEASURED:
        return None, UnresolvedUtilityDimension(
            dimension_id=scoped_dimension_id,
            quantity=1.0,
            reason="future course preference dimension is explicitly unmeasured",
            label=value.label,
        )

    if estimate.status is EstimateStatus.EXACT:
        assert estimate.point is not None
        return (
            UtilityContribution(
                dimension_id=scoped_dimension_id,
                quantity=1.0,
                status=estimate.status,
                lower=estimate.point,
                upper=estimate.point,
                point=estimate.point,
                provenance=value.provenance,
                label=value.label,
            ),
            None,
        )

    if estimate.status is EstimateStatus.BOUNDED:
        assert estimate.lower is not None and estimate.upper is not None
        return (
            UtilityContribution(
                dimension_id=scoped_dimension_id,
                quantity=1.0,
                status=estimate.status,
                lower=estimate.lower,
                upper=estimate.upper,
                provenance=value.provenance,
                label=value.label,
            ),
            None,
        )

    if estimate.status is EstimateStatus.HEURISTIC:
        assert estimate.point is not None
        return (
            UtilityContribution(
                dimension_id=scoped_dimension_id,
                quantity=1.0,
                status=estimate.status,
                lower=estimate.lower,
                upper=estimate.upper,
                point=estimate.point,
                provenance=value.provenance,
                label=value.label,
            ),
            None,
        )

    raise FutureUtilityError(
        f"unsupported preference estimate status: {estimate.status!r}"
    )


def _same_day_multi_campus(offerings: tuple[FutureOffering, ...]) -> bool:
    parsed = [
        offering
        for offering in offerings
        if isinstance(offering.schedule, ParsedSchedule)
    ]
    if len(parsed) != len(offerings):
        return False
    for day in range(5):
        campuses = {
            offering.campus.strip()
            for offering in parsed
            if offering.campus.strip()
            and ((offering.schedule.presence_mask >> (day * 16)) & 0xFFFF)
        }
        if len(campuses) > 1:
            return True
    return False


def assess_future_term_utility(
    term: FutureTermScenario,
    offerings: tuple[FutureOffering, ...],
    preference_profile: PreferenceProfile,
    professor_ratings: ProfessorRatingBook,
    *,
    subject_interest: Mapping[str, PreferenceValue] | None = None,
    workload_utility: Mapping[str, PreferenceValue] | None = None,
    difficulty_utility: Mapping[str, PreferenceValue] | None = None,
) -> FutureTermUtilityAssessment:
    """Attach non-lossy utility evidence to one selected future term."""

    ids = tuple(offering.offering_id for offering in offerings)
    if len(ids) != len(set(ids)):
        raise FutureUtilityError("future utility term contains duplicate offering ids")
    wrong_terms = [
        offering.offering_id for offering in offerings if offering.term_id != term.term_id
    ]
    if wrong_terms:
        raise FutureUtilityError(
            "future utility offering belongs to a different term: " + ", ".join(wrong_terms)
        )

    if term.activity is TermActivity.LEAVE:
        if offerings:
            raise FutureUtilityError("leave-term utility cannot contain academic offerings")
        return FutureTermUtilityAssessment(
            term_id=term.term_id,
            offering_ids=(),
            timetable_facts=None,
            timetable_utility=None,
            course_preferences=(),
            course_contributions=(),
            unresolved=(),
            measured_lower=0.0,
            measured_upper=0.0,
            heuristic_point_delta=0.0,
            academic_utility_applicable=False,
        )

    subject_map = subject_interest or {}
    workload_map = workload_utility or {}
    difficulty_map = difficulty_utility or {}

    timetable_facts: TimetableQualityFacts | None = None
    timetable_utility_assessment: PartialUtilityAssessment | None = None
    unresolved: list[UnresolvedUtilityDimension] = []
    measured_lower = 0.0
    measured_upper = 0.0
    heuristic_point_delta = 0.0

    if all(isinstance(offering.schedule, ParsedSchedule) for offering in offerings):
        timetable_facts = extract_timetable_quality_from_parsed_schedules(
            tuple(offering.schedule for offering in offerings)  # type: ignore[misc]
        )
        timetable_utility_assessment = evaluate_timetable_utility(
            timetable_facts, preference_profile
        )
        measured_lower += timetable_utility_assessment.measured_lower
        measured_upper += timetable_utility_assessment.measured_upper
        heuristic_point_delta += timetable_utility_assessment.heuristic_point_delta
    else:
        missing_ids = ",".join(
            sorted(
                offering.offering_id
                for offering in offerings
                if not isinstance(offering.schedule, ParsedSchedule)
            )
        )
        unresolved.append(
            UnresolvedUtilityDimension(
                dimension_id=f"future_timetable_utility::{term.term_id}",
                quantity=1.0,
                reason=(
                    "future timetable utility requires parsed schedules; unresolved offerings="
                    + missing_ids
                ),
            )
        )

    course_preferences: list[FutureOfferingPreferenceEvidence] = []
    course_contributions: list[UtilityContribution] = []

    for offering in sorted(offerings, key=lambda item: item.offering_id):
        code = offering.course_code
        professor = professor_ratings.lookup(offering.professor or "")
        preference = FutureOfferingPreferenceEvidence(
            offering_id=offering.offering_id,
            course_code=code,
            professor=professor,
            subject_interest=subject_map.get(
                code,
                _unmeasured(
                    f"subject_interest::{code}", f"Subject interest for {code}"
                ),
            ),
            workload_utility=workload_map.get(
                code,
                _unmeasured(
                    f"workload_utility::{code}", f"Workload utility for {code}"
                ),
            ),
            difficulty_utility=difficulty_map.get(
                code,
                _unmeasured(
                    f"difficulty_utility::{code}", f"Difficulty utility for {code}"
                ),
            ),
        )
        course_preferences.append(preference)

        if not professor.is_rated:
            unresolved.append(
                UnresolvedUtilityDimension(
                    dimension_id=f"professor_rating::{offering.offering_id}",
                    quantity=1.0,
                    reason="future offering professor is not manually rated",
                )
            )
        # Even a known manual [-1,+1] professor rating still lacks an elicited conversion
        # to the common utility scale.  Keep that missing bridge explicit.
        unresolved.append(
            UnresolvedUtilityDimension(
                dimension_id=f"professor_rating_to_utility::{offering.offering_id}",
                quantity=1.0,
                reason="no elicited professor-rating-to-utility conversion exists",
            )
        )

        for name, value in (
            ("subject_interest", preference.subject_interest),
            ("workload", preference.workload_utility),
            ("difficulty", preference.difficulty_utility),
        ):
            contribution, missing = _value_contribution(
                value,
                scoped_dimension_id=f"{name}::{offering.offering_id}",
            )
            if missing is not None:
                unresolved.append(missing)
                continue
            assert contribution is not None
            course_contributions.append(contribution)
            if contribution.status in {EstimateStatus.EXACT, EstimateStatus.BOUNDED}:
                assert contribution.lower is not None and contribution.upper is not None
                measured_lower += contribution.lower
                measured_upper += contribution.upper
            elif contribution.status is EstimateStatus.HEURISTIC:
                assert contribution.point is not None
                heuristic_point_delta += contribution.point

    if _same_day_multi_campus(offerings):
        unresolved.append(
            UnresolvedUtilityDimension(
                dimension_id=f"mixed_campus_travel_disutility::{term.term_id}",
                quantity=1.0,
                reason=(
                    "same-day cross-campus attendance exists but future travel disutility has not been valued"
                ),
            )
        )

    return FutureTermUtilityAssessment(
        term_id=term.term_id,
        offering_ids=tuple(sorted(ids)),
        timetable_facts=timetable_facts,
        timetable_utility=timetable_utility_assessment,
        course_preferences=tuple(course_preferences),
        course_contributions=tuple(course_contributions),
        unresolved=tuple(unresolved),
        measured_lower=measured_lower,
        measured_upper=measured_upper,
        heuristic_point_delta=heuristic_point_delta,
    )


def aggregate_future_utility(
    history: FutureUtilityHistory,
    aggregation: TemporalUtilityAggregation,
) -> AggregatedFutureUtility:
    """Aggregate future-term utility only under explicit exact temporal weights."""

    weight_ids = {weight.term_id for weight in aggregation.weights}
    history_ids = set(history.term_ids)
    if weight_ids != history_ids:
        missing = sorted(history_ids - weight_ids)
        extra = sorted(weight_ids - history_ids)
        pieces: list[str] = []
        if missing:
            pieces.append("missing=" + ",".join(missing))
        if extra:
            pieces.append("extra=" + ",".join(extra))
        raise FutureUtilityError(
            "temporal aggregation term set does not match utility history: "
            + "; ".join(pieces)
        )

    lower = upper = heuristic = 0.0
    unresolved: set[str] = set()
    for term in history.terms:
        weight = aggregation.weight_for(term.term_id)
        if weight == 0:
            continue
        lower += term.measured_lower * weight
        upper += term.measured_upper * weight
        heuristic += term.heuristic_point_delta * weight
        unresolved.update(
            f"{term.term_id}::{dimension}"
            for dimension in term.unresolved_dimensions
        )
        if term.timetable_utility is None and term.academic_utility_applicable:
            unresolved.add(f"{term.term_id}::timetable_utility")
        if term.has_heuristics and heuristic == 0.0:
            # A zero-valued heuristic is still heuristic evidence, not exact evidence.
            unresolved.add(f"{term.term_id}::heuristic_status")

    return AggregatedFutureUtility(
        source_id=aggregation.source_id,
        measured_lower=lower,
        measured_upper=upper,
        heuristic_point_delta=heuristic,
        unresolved_dimensions=frozenset(unresolved),
    )
