"""Unified, non-lossy candidate assessment for the Stage 4 rebuild.

Stage 4C has several evidence channels that must eventually meet without being
collapsed prematurely:

* exact timetable geometry and partial timetable utility;
* manually supplied course/professor evidence;
* physical campus-transition structure;
* registration gate/obtainability evidence;
* degree-recognition choices and (later) an explicitly selected degree transition.

This module is the integration boundary.  It deliberately does *not* choose among
recognition branches, invent travel feasibility, convert professor ratings to timetable
points, or treat missing registration odds as success.

A candidate therefore exposes separate hard-constraint violations, hard-constraint
unknowns, present-preference unknowns, and future/degree unknowns.  ``known_infeasible``
is meaningful even when the complete objective is not yet measurable.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Mapping

from .course_preferences import (
    ProfessorRatingBook,
    SectionCoursePreferenceEvidence,
    assess_section_course_preferences,
)
from .degree import DegreeScenario, DegreeState
from .preferences import PreferenceProfile, PreferenceValue
from .recognition import (
    CHAPEL_2026_CODES,
    QualificationStatus,
    RecognitionAssessment,
)
from .registration import ObtainabilityStatus, RegistrationAssessment
from .sections import ParsedSchedule, Section
from .timetable_quality import TimetableQualityFacts, extract_timetable_quality
from .timetable_utility import PartialUtilityAssessment, evaluate_timetable_utility
from .travel import TravelPathFacts, extract_travel_path_facts


class CandidateAssessmentError(ValueError):
    """Candidate assessment input violates the Stage 4 integration contract."""


class ConstraintEvidenceStatus(str, Enum):
    """Only unresolved and violated constraints need to be surfaced here."""

    UNRESOLVED = "unresolved"
    VIOLATED = "violated"


@dataclass(frozen=True)
class CandidateConstraintIssue:
    """One hard-constraint failure or unresolved hard-constraint question."""

    code: str
    status: ConstraintEvidenceStatus
    message: str
    section_ids: tuple[str, ...] = ()
    source: str = ""

    def __post_init__(self) -> None:
        if not self.code.strip() or not self.message.strip():
            raise CandidateAssessmentError(
                "candidate constraint issue requires nonblank code and message"
            )


@dataclass(frozen=True)
class CandidateLoadFacts:
    """Exact credit-load facts without turning a preferred load into a hard limit."""

    total_known_credits: float
    ordinary_known_credits: float
    chapel_known_credits: float
    unknown_credit_section_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        for value in (
            self.total_known_credits,
            self.ordinary_known_credits,
            self.chapel_known_credits,
        ):
            if not isfinite(value) or value < 0:
                raise CandidateAssessmentError(
                    "candidate credit totals must be finite and nonnegative"
                )


@dataclass(frozen=True)
class CandidateDegreeTransition:
    """An explicitly selected degree-state transition supplied by a later solver.

    Stage 4C never manufactures this object by choosing recognition options itself.  The
    option ids document the choices made by Stage 4D or another explicit caller.
    """

    scenario_id: str
    starting_state: DegreeState
    resulting_state: DegreeState
    selected_option_ids: tuple[str, ...]

    @property
    def credits_added(self) -> float:
        return self.resulting_state.earned_credits - self.starting_state.earned_credits

    def __post_init__(self) -> None:
        if not self.scenario_id.strip():
            raise CandidateAssessmentError("degree transition requires scenario_id")
        if self.credits_added < 0:
            raise CandidateAssessmentError("degree transition cannot remove earned credits")


@dataclass(frozen=True)
class CandidateAssessment:
    """One timetable candidate with all currently represented evidence channels."""

    section_ids: tuple[str, ...]
    load: CandidateLoadFacts
    timetable_facts: TimetableQualityFacts | None
    timetable_utility: PartialUtilityAssessment | None
    course_preferences: tuple[SectionCoursePreferenceEvidence, ...]
    travel_facts: TravelPathFacts | None
    registration: tuple[RegistrationAssessment, ...]
    recognition: tuple[RecognitionAssessment, ...]
    degree_transition: CandidateDegreeTransition | None
    hard_constraint_issues: tuple[CandidateConstraintIssue, ...]
    present_preference_unknowns: frozenset[str]
    future_unknowns: frozenset[str]

    @property
    def hard_constraint_violations(self) -> tuple[CandidateConstraintIssue, ...]:
        return tuple(
            issue
            for issue in self.hard_constraint_issues
            if issue.status is ConstraintEvidenceStatus.VIOLATED
        )

    @property
    def hard_constraint_unknowns(self) -> tuple[CandidateConstraintIssue, ...]:
        return tuple(
            issue
            for issue in self.hard_constraint_issues
            if issue.status is ConstraintEvidenceStatus.UNRESOLVED
        )

    @property
    def known_infeasible(self) -> bool:
        return bool(self.hard_constraint_violations)

    @property
    def hard_feasibility_resolved(self) -> bool:
        return not self.hard_constraint_violations and not self.hard_constraint_unknowns

    @property
    def timetable_bounds(self) -> tuple[float, float] | None:
        if self.timetable_utility is None:
            return None
        return self.timetable_utility.complete_bounds

    @property
    def present_assessment_complete(self) -> bool:
        return (
            not self.known_infeasible
            and self.timetable_utility is not None
            and self.timetable_bounds is not None
            and not self.present_preference_unknowns
            and not self.hard_constraint_unknowns
        )

    @property
    def future_assessment_complete(self) -> bool:
        return self.degree_transition is not None and not self.future_unknowns


def _load_facts(sections: tuple[Section, ...]) -> CandidateLoadFacts:
    total = ordinary = chapel = 0.0
    unknown: list[str] = []
    for section in sections:
        if section.credits is None:
            unknown.append(section.section_id)
            continue
        total += section.credits
        if section.course_code in CHAPEL_2026_CODES:
            chapel += section.credits
        else:
            ordinary += section.credits
    return CandidateLoadFacts(
        total_known_credits=total,
        ordinary_known_credits=ordinary,
        chapel_known_credits=chapel,
        unknown_credit_section_ids=tuple(sorted(unknown)),
    )


def _time_conflicts(
    sections: tuple[Section, ...],
) -> tuple[CandidateConstraintIssue, ...]:
    parsed = [
        section for section in sections if isinstance(section.schedule, ParsedSchedule)
    ]
    out: list[CandidateConstraintIssue] = []
    for index, left in enumerate(parsed):
        for right in parsed[index + 1 :]:
            overlap = left.schedule.conflict_mask & right.schedule.conflict_mask
            if overlap:
                out.append(
                    CandidateConstraintIssue(
                        code="registration_time_conflict",
                        status=ConstraintEvidenceStatus.VIOLATED,
                        message=(
                            "sections overlap under the canonical registration-conflict mask"
                        ),
                        section_ids=(left.section_id, right.section_id),
                        source="canonical conflict_mask",
                    )
                )
    return tuple(out)


def _recognition_unknowns(
    assessments: tuple[RecognitionAssessment, ...],
    degree_scenario: DegreeScenario | None,
) -> frozenset[str]:
    """Return only unresolved recognition decisions relevant to the supplied scenario.

    ``recognize_section`` deliberately records some broad decisions for auditability even
    when the requirement is absent from a small scenario.  Those decisions must not make an
    otherwise exact selected transition look unresolved.  Without a scenario we cannot
    establish relevance, so all unresolved decisions remain visible.
    """

    relevant_ids = (
        None
        if degree_scenario is None
        else {
            requirement.requirement_id
            for requirement in degree_scenario.requirements
        }
    )
    unresolved: set[str] = set()
    for assessment in assessments:
        for decision in assessment.decisions:
            if (
                decision.status is QualificationStatus.UNRESOLVED
                and (
                    relevant_ids is None
                    or decision.requirement_id in relevant_ids
                )
            ):
                unresolved.add(
                    f"recognition::{assessment.section_id}::{decision.requirement_id}"
                )
        if not assessment.options:
            unresolved.add(f"degree_transition::{assessment.section_id}")
    return frozenset(unresolved)


def assess_candidate(
    sections: tuple[Section, ...],
    preference_profile: PreferenceProfile,
    professor_ratings: ProfessorRatingBook,
    *,
    subject_interest: Mapping[str, PreferenceValue] | None = None,
    workload_utility: Mapping[str, PreferenceValue] | None = None,
    difficulty_utility: Mapping[str, PreferenceValue] | None = None,
    registration_assessments: Mapping[str, RegistrationAssessment] | None = None,
    recognition_assessments: Mapping[str, RecognitionAssessment] | None = None,
    degree_scenario: DegreeScenario | None = None,
    degree_transition: CandidateDegreeTransition | None = None,
    external_constraint_issues: tuple[CandidateConstraintIssue, ...] = (),
) -> CandidateAssessment:
    """Integrate Stage 4C evidence for one concrete section set.

    The function performs only integration-safe derivations.  It never chooses a degree
    recognition option, never estimates travel time, and never assigns missing registration
    odds or course preferences a neutral value.
    """

    section_ids = tuple(section.section_id for section in sections)
    if len(section_ids) != len(set(section_ids)):
        raise CandidateAssessmentError(
            "candidate cannot contain the same physical section twice"
        )

    if degree_transition is not None:
        if degree_scenario is None:
            raise CandidateAssessmentError(
                "degree_transition requires the corresponding degree_scenario"
            )
        if degree_transition.scenario_id != degree_scenario.scenario_id:
            raise CandidateAssessmentError(
                "degree transition scenario_id does not match degree_scenario"
            )

    issues: list[CandidateConstraintIssue] = list(external_constraint_issues)

    for section in sections:
        if section.cancelled is True:
            issues.append(
                CandidateConstraintIssue(
                    code="section_cancelled",
                    status=ConstraintEvidenceStatus.VIOLATED,
                    message="canonical catalogue evidence marks this section cancelled",
                    section_ids=(section.section_id,),
                    source="canonical cancelled flag",
                )
            )
        elif section.cancelled is None:
            issues.append(
                CandidateConstraintIssue(
                    code="cancellation_status_unresolved",
                    status=ConstraintEvidenceStatus.UNRESOLVED,
                    message="section cancellation status is not established",
                    section_ids=(section.section_id,),
                    source="canonical cancelled flag",
                )
            )

        if not isinstance(section.schedule, ParsedSchedule):
            issues.append(
                CandidateConstraintIssue(
                    code="schedule_unresolved",
                    status=ConstraintEvidenceStatus.UNRESOLVED,
                    message=(
                        "section schedule is not safely parsed, so conflicts and lived "
                        "timetable quality cannot be fully established"
                    ),
                    section_ids=(section.section_id,),
                    source=type(section.schedule).__name__,
                )
            )

    issues.extend(_time_conflicts(sections))

    all_parsed = all(isinstance(section.schedule, ParsedSchedule) for section in sections)
    timetable_facts: TimetableQualityFacts | None = None
    timetable_utility: PartialUtilityAssessment | None = None
    travel_facts: TravelPathFacts | None = None
    if all_parsed:
        timetable_facts = extract_timetable_quality(sections)
        timetable_utility = evaluate_timetable_utility(
            timetable_facts, preference_profile
        )
        travel_facts = extract_travel_path_facts(sections)

        for conflict in travel_facts.location_conflicts:
            issues.append(
                CandidateConstraintIssue(
                    code="simultaneous_multi_campus_presence",
                    status=ConstraintEvidenceStatus.VIOLATED,
                    message=(
                        "candidate requires physical presence at multiple campuses "
                        "simultaneously"
                    ),
                    section_ids=conflict.section_ids,
                    source="canonical physical-presence intervals",
                )
            )

        if travel_facts.transitions:
            involved = tuple(
                sorted(
                    {
                        section_id
                        for transition in travel_facts.transitions
                        for section_id in (
                            *transition.from_section_ids,
                            *transition.to_section_ids,
                        )
                    }
                )
            )
            issues.append(
                CandidateConstraintIssue(
                    code="travel_feasibility_unresolved",
                    status=ConstraintEvidenceStatus.UNRESOLVED,
                    message=(
                        "cross-campus transition exists but no explicit travel-time/residence "
                        "scenario has established physical feasibility"
                    ),
                    section_ids=involved,
                    source="Stage 4C travel path facts",
                )
            )

    course_preferences = tuple(
        assess_section_course_preferences(
            section,
            professor_ratings,
            subject_interest=subject_interest,
            workload_utility=workload_utility,
            difficulty_utility=difficulty_utility,
        )
        for section in sections
    )

    present_unknowns: set[str] = set()
    if timetable_utility is None:
        present_unknowns.add("timetable_utility")
    else:
        present_unknowns.update(
            f"timetable::{dimension}"
            for dimension in timetable_utility.unresolved_dimensions
        )
        if timetable_utility.has_heuristics:
            present_unknowns.add("timetable_heuristic_terms")

    for evidence in course_preferences:
        present_unknowns.update(
            f"course::{evidence.section_id}::{dimension}"
            for dimension in evidence.unresolved_dimensions
        )

    if travel_facts is not None and travel_facts.transitions:
        present_unknowns.add("mixed_campus_travel_disutility")

    registration_map = registration_assessments or {}
    registration: list[RegistrationAssessment] = []
    for section in sections:
        assessment = registration_map.get(section.section_id)
        if assessment is None:
            issues.append(
                CandidateConstraintIssue(
                    code="registration_gate_unassessed",
                    status=ConstraintEvidenceStatus.UNRESOLVED,
                    message="no section-specific registration gate assessment was supplied",
                    section_ids=(section.section_id,),
                    source="Stage 4C registration evidence",
                )
            )
            present_unknowns.add(
                f"registration_obtainability::{section.section_id}"
            )
            continue
        if assessment.section_id != section.section_id:
            raise CandidateAssessmentError(
                f"registration assessment key/section mismatch for {section.section_id}"
            )
        registration.append(assessment)
        if assessment.blocked_by_observed_year_gate:
            issues.append(
                CandidateConstraintIssue(
                    code="registration_year_gate_block",
                    status=ConstraintEvidenceStatus.VIOLATED,
                    message=(
                        "observed year-quota scheme blocks this section for a freshman"
                    ),
                    section_ids=(section.section_id,),
                    source=assessment.quota_source_id or "registration assessment",
                )
            )
        if assessment.obtainability.status is ObtainabilityStatus.UNMEASURED:
            present_unknowns.add(
                f"registration_obtainability::{section.section_id}"
            )
        elif assessment.obtainability.status is ObtainabilityStatus.HEURISTIC:
            present_unknowns.add(
                f"registration_obtainability_heuristic::{section.section_id}"
            )

    recognition_map = recognition_assessments or {}
    recognition: list[RecognitionAssessment] = []
    for section in sections:
        assessment = recognition_map.get(section.section_id)
        if assessment is None:
            continue
        if assessment.section_id != section.section_id:
            raise CandidateAssessmentError(
                f"recognition assessment key/section mismatch for {section.section_id}"
            )
        recognition.append(assessment)

    future_unknowns: set[str] = set(
        _recognition_unknowns(tuple(recognition), degree_scenario)
    )
    if degree_scenario is not None and len(recognition) < len(sections):
        missing = set(section_ids) - {
            assessment.section_id for assessment in recognition
        }
        future_unknowns.update(
            f"recognition_missing::{section_id}" for section_id in missing
        )
    if degree_scenario is not None and degree_transition is None:
        future_unknowns.add("degree_transition_not_selected")
    if degree_scenario is None:
        future_unknowns.add("degree_scenario_not_supplied")

    return CandidateAssessment(
        section_ids=section_ids,
        load=_load_facts(sections),
        timetable_facts=timetable_facts,
        timetable_utility=timetable_utility,
        course_preferences=course_preferences,
        travel_facts=travel_facts,
        registration=tuple(registration),
        recognition=tuple(recognition),
        degree_transition=degree_transition,
        hard_constraint_issues=tuple(issues),
        present_preference_unknowns=frozenset(present_unknowns),
        future_unknowns=frozenset(future_unknowns),
    )