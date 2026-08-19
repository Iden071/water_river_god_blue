"""Stateful future recognition/action generation for Stage 4D.

The future search must not decide degree recognition by an arbitrary iteration order over
courses.  Recognition can depend on the *current* :class:`DegreeState` (for example the
QRM Korean-taught Economics/Applied-Statistics cap), and one course can branch between
QRM and second-major assignment.

This module therefore turns one :class:`FutureOffering` into explicit state-transition
actions.  Every generated action contains the exact recognition option selected and the
resulting immutable degree state.  A later solver may choose among these actions; this layer
does not rank them, force an offering to be taken, or collapse unresolved recognition.

Future scenario evidence is converted into the existing canonical recognition authority
rather than creating a second degree-rule implementation.  The small internal course view
below is intentionally *not* a canonical physical ``Section``: hypothetical future offerings
are planning objects, not observations that should leak into the canonical catalogue.
"""

from __future__ import annotations

from dataclasses import dataclass

from .catalog import ListingObservation, ListingStatus, SourceListingView, SourceRef
from .degree import (
    DegreeRuleError,
    DegreeScenario,
    DegreeState,
    RecognitionEffect,
    apply_recognition,
)
from .future_opportunities import FutureOffering
from .recognition import (
    CourseRecognitionEvidence,
    QualificationStatus,
    RecognitionAssessment,
    recognize_section,
)


class FutureActionError(ValueError):
    """Future action generation received inconsistent scenario/state input."""


@dataclass(frozen=True)
class FutureRecognitionEvidence:
    """Scenario-local evidence needed by the canonical recognition authority.

    Course codes already establish many requirements.  These fields carry only additional
    scenario evidence that cannot safely be inferred from a code: listing department,
    an optional QRM program-listing category, and explicit language evidence.

    When any additional evidence is supplied, ``source_id`` is required so hypothetical
    assumptions remain auditable.
    """

    source_id: str = ""
    departments: tuple[str, ...] = ()
    qrm_listing_status: ListingStatus | None = None
    qrm_listed_category: str | None = None
    foreign_language_course: bool | None = None
    korean_taught: bool | None = None
    note: str = ""

    def __post_init__(self) -> None:
        has_payload = bool(
            self.departments
            or self.qrm_listing_status is not None
            or self.qrm_listed_category is not None
            or self.foreign_language_course is not None
            or self.korean_taught is not None
            or self.note.strip()
        )
        if has_payload and not self.source_id.strip():
            raise FutureActionError(
                "future recognition evidence requires source_id when evidence is supplied"
            )
        if self.qrm_listed_category is not None and self.qrm_listing_status is None:
            raise FutureActionError(
                "QRM listed category requires an explicit listing status"
            )
        if (
            self.qrm_listing_status is ListingStatus.UNRESOLVED
            and self.qrm_listed_category is not None
        ):
            raise FutureActionError(
                "unresolved QRM listing cannot simultaneously assert a category"
            )
        if any(not department.strip() for department in self.departments):
            raise FutureActionError("future recognition department labels must be nonblank")


@dataclass(frozen=True)
class FutureActionIssue:
    code: str
    message: str
    requirement_id: str = ""

    def __post_init__(self) -> None:
        if not self.code.strip() or not self.message.strip():
            raise FutureActionError("future action issue requires code and message")


@dataclass(frozen=True)
class FutureAcademicAction:
    """One explicit recognition branch for taking a future offering in the current state."""

    action_id: str
    term_id: str
    offering_id: str
    option_id: str
    reason: str
    effect: RecognitionEffect
    resulting_state: DegreeState

    def __post_init__(self) -> None:
        if not self.action_id.strip() or not self.offering_id.strip():
            raise FutureActionError("future academic action requires action/offering ids")
        if self.effect.completion.completion_id != self.offering_id:
            raise FutureActionError(
                "future recognition action must use scenario offering identity as completion identity"
            )


@dataclass(frozen=True)
class FutureActionGeneration:
    """Recognition result and executable branches for one offering at one degree state."""

    offering_id: str
    recognition: RecognitionAssessment
    actions: tuple[FutureAcademicAction, ...]
    unresolved_requirement_ids: frozenset[str]
    issues: tuple[FutureActionIssue, ...]

    @property
    def has_unresolved_recognition(self) -> bool:
        return bool(self.unresolved_requirement_ids)

    @property
    def has_actions(self) -> bool:
        return bool(self.actions)

    @property
    def exact_recognition_ready(self) -> bool:
        return self.has_actions and not self.has_unresolved_recognition


@dataclass(frozen=True)
class _FutureRecognitionCourseView:
    """Narrow duck-typed input consumed by ``recognize_section``.

    ``recognize_section`` uses section identity, course code, credits, display name and the
    explicit human-readable lecture-language label.  We intentionally provide only those
    semantics instead of fabricating a canonical observed Section.
    """

    section_id: str
    course_code: str
    credits: float | None
    name: str
    language_name: str = ""


def _recognition_inputs(
    offering: FutureOffering,
    evidence: FutureRecognitionEvidence,
) -> tuple[
    tuple[SourceListingView, ...],
    tuple[ListingObservation, ...],
    CourseRecognitionEvidence,
]:
    source_views = tuple(
        SourceListingView(
            department=department,
            year_label="future-scenario",
            catalogue_category="",
        )
        for department in evidence.departments
    )

    program_listings: tuple[ListingObservation, ...] = ()
    if evidence.qrm_listing_status is not None:
        source = SourceRef(
            source_kind="future_scenario",
            source_name=evidence.source_id or offering.evidence.source_id,
            term=offering.term_id,
            source_index=0,
        )
        program_listings = (
            ListingObservation(
                source=source,
                program="QRM",
                section_id=offering.offering_id,
                status=evidence.qrm_listing_status,
                listed_category=evidence.qrm_listed_category,
                year_label="future-scenario",
                campus=offering.campus,
                raw={
                    "scenario_offering_id": offering.offering_id,
                    "evidence_source_id": evidence.source_id,
                },
            ),
        )

    course_evidence = CourseRecognitionEvidence(
        foreign_language_course=evidence.foreign_language_course,
        korean_taught=evidence.korean_taught,
        source=evidence.source_id,
    )
    return source_views, program_listings, course_evidence


def generate_future_academic_actions(
    offering: FutureOffering,
    scenario: DegreeScenario,
    state: DegreeState,
    *,
    evidence: FutureRecognitionEvidence = FutureRecognitionEvidence(),
) -> FutureActionGeneration:
    """Generate recognition/state-transition branches for one future offering.

    Recognition is evaluated *at this state*.  Calling the function again after another
    action may therefore produce a different option set when a stateful cap or assignment
    rule has changed.  This is intentional and is the contract the finite future solver will
    branch over.
    """

    if offering.offering_id in state.completion_ids:
        raise FutureActionError(
            f"future offering {offering.offering_id!r} is already present in DegreeState"
        )

    source_views, program_listings, course_evidence = _recognition_inputs(
        offering, evidence
    )
    view = _FutureRecognitionCourseView(
        section_id=offering.offering_id,
        course_code=offering.course_code,
        credits=offering.credits,
        name=offering.course_code,
        language_name="",
    )

    # ``recognize_section`` is intentionally duck-typed at runtime.  The adapter above
    # carries exactly the attributes the recognition authority consumes; it is not inserted
    # into the canonical Section catalogue.
    recognition = recognize_section(  # type: ignore[arg-type]
        view,
        scenario,
        state,
        source_views=source_views,
        program_listings=program_listings,
        evidence=course_evidence,
    )

    unresolved = frozenset(
        decision.requirement_id
        for decision in recognition.decisions
        if decision.status is QualificationStatus.UNRESOLVED
    )
    issues: list[FutureActionIssue] = [
        FutureActionIssue(issue.code, issue.message, issue.requirement_id)
        for issue in recognition.issues
    ]

    actions: list[FutureAcademicAction] = []
    for option in recognition.options:
        try:
            resulting_state = apply_recognition(state, scenario, option.effect)
        except DegreeRuleError as exc:
            # A recognition option that cannot be applied to the very state against which
            # it was generated is an integration defect, not a branch to silently drop.
            raise FutureActionError(
                f"recognition option {option.option_id!r} cannot be applied: {exc}"
            ) from exc

        actions.append(
            FutureAcademicAction(
                action_id=f"{offering.term_id}:{option.option_id}",
                term_id=offering.term_id,
                offering_id=offering.offering_id,
                option_id=option.option_id,
                reason=option.reason,
                effect=option.effect,
                resulting_state=resulting_state,
            )
        )

    if not actions:
        issues.append(
            FutureActionIssue(
                code="no_applicable_recognition_action",
                message=(
                    "recognition authority produced no degree-state transition for this future offering"
                ),
            )
        )

    return FutureActionGeneration(
        offering_id=offering.offering_id,
        recognition=recognition,
        actions=tuple(actions),
        unresolved_requirement_ids=unresolved,
        issues=tuple(issues),
    )
