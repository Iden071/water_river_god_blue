"""Stateful current-semester recognition branches for Stage 4E.

A Fall timetable is not just a set of present-semester utility facts.  Its selected courses
change the DegreeState that Stage 4D continues from.  Recognition can itself be stateful: in
particular the finite Korean-taught QRM-major-credit allowance must be allocated rather than
consumed by arbitrary section iteration order.

This module is the observed-section analogue of ``future_actions``.  It uses the canonical
CatalogSnapshot as recognition evidence, reevaluates each selected section against the
current immutable DegreeState, and exposes every exact recognition branch.  A QRM Korean
claim gets an explicit "take but reserve the allowance" branch, so fixed processing order
does not decide allocation.

Retakes are also explicit.  If repeat-credit policy is unknown, no new degree transition is
invented.  If evidence explicitly says the repeat earns no additional degree credit, taking
that section is represented as an identity degree-state action rather than being declared
physically impossible.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping

from .candidate_assessment import CandidateDegreeTransition
from .catalog import CatalogSnapshot
from .degree import (
    DegreeRuleError,
    DegreeScenario,
    DegreeState,
    RecognitionEffect,
    apply_recognition,
    requirement_major_owner,
)
from .recognition import (
    CourseRecognitionEvidence,
    QualificationStatus,
    RecognitionAssessment,
    recognize_section,
)
from .sections import Section


class FallActionError(ValueError):
    """Current-semester action generation received inconsistent canonical/state input."""


@dataclass(frozen=True)
class FallRecognitionEvidence:
    """Manual evidence not already contained in the canonical Fall catalogue."""

    source_id: str = ""
    foreign_language_course: bool | None = None
    korean_taught: bool | None = None
    repeat_credit_allowed: bool | None = None
    note: str = ""

    def __post_init__(self) -> None:
        has_payload = (
            self.foreign_language_course is not None
            or self.korean_taught is not None
            or self.repeat_credit_allowed is not None
            or bool(self.note.strip())
        )
        if has_payload and not self.source_id.strip():
            raise FallActionError(
                "Fall recognition evidence requires source_id when manual evidence is supplied"
            )


@dataclass(frozen=True)
class FallActionIssue:
    code: str
    message: str
    section_id: str
    requirement_id: str = ""

    def __post_init__(self) -> None:
        if not self.code.strip() or not self.message.strip() or not self.section_id.strip():
            raise FallActionError("Fall action issue requires code, message, and section_id")


@dataclass(frozen=True)
class FallAcademicAction:
    """One exact degree-state branch for taking one observed Fall section."""

    action_id: str
    section_id: str
    option_id: str
    reason: str
    effect: RecognitionEffect | None
    resulting_state: DegreeState

    def __post_init__(self) -> None:
        if not self.action_id.strip() or not self.section_id.strip() or not self.option_id.strip():
            raise FallActionError("Fall academic action requires action/section/option ids")
        if self.effect is not None and self.effect.completion.completion_id != self.section_id:
            raise FallActionError(
                "observed Fall recognition action must use physical section identity as completion identity"
            )


@dataclass(frozen=True)
class FallActionGeneration:
    section_id: str
    recognition: RecognitionAssessment
    actions: tuple[FallAcademicAction, ...]
    unresolved_requirement_ids: frozenset[str]
    issues: tuple[FallActionIssue, ...]

    @property
    def exact_recognition_ready(self) -> bool:
        return bool(self.actions) and not self.unresolved_requirement_ids


@dataclass(frozen=True)
class FallDegreeTransitionBranch:
    """One exact recognition allocation for the entire selected Fall section set."""

    transition: CandidateDegreeTransition
    recognitions: tuple[RecognitionAssessment, ...]


@dataclass(frozen=True)
class FallDegreeTransitionGeneration:
    branches: tuple[FallDegreeTransitionBranch, ...]
    unresolved_issues: tuple[FallActionIssue, ...]

    @property
    def exact_enumeration_complete(self) -> bool:
        return not self.unresolved_issues

    @property
    def has_exact_branches(self) -> bool:
        return bool(self.branches)


@dataclass(frozen=True)
class _OpenFallPath:
    state: DegreeState
    option_ids: tuple[str, ...]
    recognitions: tuple[RecognitionAssessment, ...]


def _without_qrm_major_claims(
    effect: RecognitionEffect,
    scenario: DegreeScenario,
) -> RecognitionEffect:
    def keep(requirement_id: str) -> bool:
        return requirement_major_owner(scenario, requirement_id) != "qrm"

    return RecognitionEffect(
        completion=effect.completion,
        satisfy=tuple(rid for rid in effect.satisfy if keep(rid)),
        category_claims=tuple(
            claim for claim in effect.category_claims if keep(claim[0])
        ),
        bucket_credit_claims=tuple(
            claim for claim in effect.bucket_credit_claims if keep(claim[0])
        ),
        chapel_pass=effect.chapel_pass,
        chapel_offline=effect.chapel_offline,
        qrm_korean_major_credits=0.0,
    )


def _apply_fall2026_freshman_chapel_modality(
    recognition: RecognitionAssessment,
) -> RecognitionAssessment:
    """Resolve current Fall Chapel modality from the governing freshman rule.

    The Stage 4E Fall layer is specifically Fall 2026, when the user is a freshman.
    The user manually confirmed that freshmen must take Chapel offline.  Therefore a
    recognized current-semester Chapel action is definitively offline; this rule is not
    projected onto later future semesters after freshman year.
    """

    options = []
    for option in recognition.options:
        if not option.effect.chapel_pass:
            options.append(option)
            continue
        options.append(
            replace(
                option,
                effect=replace(option.effect, chapel_offline=True),
                reason=(
                    option.reason
                    + "; Fall 2026 freshman Chapel is required to be offline under the governing specification"
                ),
            )
        )
    return replace(recognition, options=tuple(options))


def _validate_canonical_section(section: Section, snapshot: CatalogSnapshot) -> None:
    record = snapshot.record_for(section.section_id)
    if record is None or not record.usable or record.section is None:
        raise FallActionError(
            f"Fall section {section.section_id!r} is not a usable canonical physical section"
        )
    if record.section != section:
        raise FallActionError(
            f"Fall section {section.section_id!r} does not match the canonical snapshot record"
        )


def generate_fall_academic_actions(
    section: Section,
    snapshot: CatalogSnapshot,
    scenario: DegreeScenario,
    state: DegreeState,
    *,
    evidence: FallRecognitionEvidence = FallRecognitionEvidence(),
) -> FallActionGeneration:
    """Generate all exact degree-state actions for taking one canonical Fall section now."""

    _validate_canonical_section(section, snapshot)
    if section.section_id in state.completion_ids:
        raise FallActionError(
            f"Fall section {section.section_id!r} is already present in DegreeState"
        )

    if section.course_code in state.completed_course_codes:
        if evidence.repeat_credit_allowed is None:
            issue = FallActionIssue(
                code="repeat_credit_unresolved",
                message=(
                    "course code is already completed; additional-credit/replacement semantics are unresolved"
                ),
                section_id=section.section_id,
            )
            return FallActionGeneration(
                section_id=section.section_id,
                recognition=RecognitionAssessment(section.section_id, (), (), ()),
                actions=(),
                unresolved_requirement_ids=frozenset(),
                issues=(issue,),
            )
        if evidence.repeat_credit_allowed is False:
            action = FallAcademicAction(
                action_id=f"2026F:{section.section_id}:repeat-no-additional-credit",
                section_id=section.section_id,
                option_id=f"{section.section_id}:repeat-no-additional-credit",
                reason=(
                    "explicit repeat policy says taking this already-completed course creates no additional DegreeState credit"
                ),
                effect=None,
                resulting_state=state,
            )
            return FallActionGeneration(
                section_id=section.section_id,
                recognition=RecognitionAssessment(section.section_id, (), (), ()),
                actions=(action,),
                unresolved_requirement_ids=frozenset(),
                issues=(),
            )

    course_evidence = CourseRecognitionEvidence(
        foreign_language_course=evidence.foreign_language_course,
        korean_taught=evidence.korean_taught,
        source=evidence.source_id,
    )
    recognition = recognize_section(
        section,
        scenario,
        state,
        source_views=snapshot.source_views_for(section.section_id),
        program_listings=snapshot.listings_for(section.section_id),
        evidence=course_evidence,
    )
    recognition = _apply_fall2026_freshman_chapel_modality(recognition)
    scenario_requirement_ids = {
        requirement.requirement_id for requirement in scenario.requirements
    }
    unresolved = frozenset(
        decision.requirement_id
        for decision in recognition.decisions
        if (
            decision.status is QualificationStatus.UNRESOLVED
            and decision.requirement_id in scenario_requirement_ids
        )
    )
    issues = tuple(
        FallActionIssue(
            code=issue.code,
            message=issue.message,
            section_id=section.section_id,
            requirement_id=issue.requirement_id,
        )
        for issue in recognition.issues
    )

    branch_effects: list[tuple[str, str, RecognitionEffect]] = []
    for option in recognition.options:
        branch_effects.append((option.option_id, option.reason, option.effect))
        if option.effect.qrm_korean_major_credits > 0:
            branch_effects.append(
                (
                    f"{option.option_id}:decline-qrm-korean",
                    (
                        option.reason
                        + "; take the course but reserve the finite Korean QRM-major-credit allowance for another Fall completion"
                    ),
                    _without_qrm_major_claims(option.effect, scenario),
                )
            )

    actions: list[FallAcademicAction] = []
    for option_id, reason, effect in branch_effects:
        try:
            resulting_state = apply_recognition(state, scenario, effect)
        except DegreeRuleError as exc:
            raise FallActionError(
                f"Fall recognition option {option_id!r} cannot be applied: {exc}"
            ) from exc
        actions.append(
            FallAcademicAction(
                action_id=f"2026F:{option_id}",
                section_id=section.section_id,
                option_id=option_id,
                reason=reason,
                effect=effect,
                resulting_state=resulting_state,
            )
        )

    if not actions and not issues:
        issues = (
            FallActionIssue(
                code="no_applicable_recognition_action",
                message="recognition authority produced no degree-state transition for this Fall section",
                section_id=section.section_id,
            ),
        )

    return FallActionGeneration(
        section_id=section.section_id,
        recognition=recognition,
        actions=tuple(actions),
        unresolved_requirement_ids=unresolved,
        issues=issues,
    )


def _dedupe_issues(issues: list[FallActionIssue]) -> tuple[FallActionIssue, ...]:
    out: list[FallActionIssue] = []
    seen: set[FallActionIssue] = set()
    for issue in issues:
        if issue in seen:
            continue
        seen.add(issue)
        out.append(issue)
    return tuple(out)


def generate_fall_degree_transitions(
    sections: tuple[Section, ...],
    snapshot: CatalogSnapshot,
    scenario: DegreeScenario,
    starting_state: DegreeState,
    *,
    evidence: Mapping[str, FallRecognitionEvidence] | None = None,
) -> FallDegreeTransitionGeneration:
    """Enumerate exact degree-state transitions for one selected Fall timetable.

    Sections are processed in stable physical-section-id order.  This does not freeze scarce
    QRM Korean-credit allocation because every consuming action has an explicit decline
    branch; later sections are reevaluated against each resulting state.
    """

    ids = tuple(section.section_id for section in sections)
    if len(ids) != len(set(ids)):
        raise FallActionError("Fall transition generation received a duplicate section")
    evidence_map = evidence or {}
    extra = sorted(set(evidence_map) - set(ids))
    if extra:
        raise FallActionError(
            "Fall recognition evidence references section(s) outside candidate: "
            + ", ".join(extra)
        )

    ordered = tuple(sorted(sections, key=lambda section: section.section_id))
    frontier = [_OpenFallPath(starting_state, (), ())]
    unresolved: list[FallActionIssue] = []

    for section in ordered:
        next_frontier: list[_OpenFallPath] = []
        for path in frontier:
            generated = generate_fall_academic_actions(
                section,
                snapshot,
                scenario,
                path.state,
                evidence=evidence_map.get(section.section_id, FallRecognitionEvidence()),
            )
            if generated.unresolved_requirement_ids:
                for requirement_id in sorted(generated.unresolved_requirement_ids):
                    unresolved.append(
                        FallActionIssue(
                            code="fall_recognition_unresolved",
                            message=(
                                f"Fall recognition is unresolved for requirement {requirement_id!r} at the current degree state"
                            ),
                            section_id=section.section_id,
                            requirement_id=requirement_id,
                        )
                    )
                unresolved.extend(generated.issues)
                continue
            if not generated.actions:
                unresolved.extend(generated.issues)
                continue

            for action in generated.actions:
                next_frontier.append(
                    _OpenFallPath(
                        state=action.resulting_state,
                        option_ids=path.option_ids + (action.option_id,),
                        recognitions=path.recognitions + (generated.recognition,),
                    )
                )
        frontier = next_frontier
        if not frontier:
            break

    branches: list[FallDegreeTransitionBranch] = []
    seen: set[tuple[DegreeState, tuple[str, ...]]] = set()
    for path in frontier:
        key = (path.state, path.option_ids)
        if key in seen:
            continue
        seen.add(key)
        branches.append(
            FallDegreeTransitionBranch(
                transition=CandidateDegreeTransition(
                    scenario_id=scenario.scenario_id,
                    starting_state=starting_state,
                    resulting_state=path.state,
                    selected_option_ids=path.option_ids,
                ),
                recognitions=path.recognitions,
            )
        )

    return FallDegreeTransitionGeneration(
        branches=tuple(branches),
        unresolved_issues=_dedupe_issues(unresolved),
    )
