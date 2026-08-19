"""Term-level future action bundles for Stage 4D.

This layer sits between individual stateful recognition actions and the eventual finite
search.  Given an explicitly selected set of future offerings for one term, it:

* checks term activity, credit capacity, campus access, and known timetable conflicts;
* keeps non-parsed schedules and cross-campus travel feasibility explicit as unknowns;
* re-evaluates recognition against the evolving immutable ``DegreeState``;
* enumerates recognition branches without letting a fixed course order choose allocation
  of the finite Korean QRM-major-credit allowance.

It deliberately does *not* enumerate subsets of the term's opportunity universe and does not
rank bundles.  A later search layer will choose subsets, call this generator, and optimize
over the resulting states.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from .degree import DegreeScenario, DegreeState
from .future_actions import (
    FutureAcademicAction,
    FutureActionIssue,
    FutureRecognitionEvidence,
    generate_future_academic_actions,
)
from .future_opportunities import FutureOffering
from .future_scenarios import FutureTermScenario, TermActivity
from .recognition import CHAPEL_2026_CODES
from .sections import ParsedSchedule


class FutureTermBundleError(ValueError):
    """Future term bundle input is structurally inconsistent."""


class FutureTermIssueStatus(str, Enum):
    UNRESOLVED = "unresolved"
    VIOLATED = "violated"


@dataclass(frozen=True)
class FutureTermIssue:
    code: str
    status: FutureTermIssueStatus
    message: str
    offering_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.code.strip() or not self.message.strip():
            raise FutureTermBundleError("future term issue requires code and message")


@dataclass(frozen=True)
class FutureTermLoadFacts:
    known_total_credits: float
    known_ordinary_credits: float
    known_chapel_credits: float
    unknown_credit_offering_ids: tuple[str, ...]


@dataclass(frozen=True)
class FutureTermBundle:
    """One state-transition branch for one selected future-term offering set."""

    term_id: str
    offering_ids: tuple[str, ...]
    actions: tuple[FutureAcademicAction, ...]
    starting_state: DegreeState
    resulting_state: DegreeState
    load: FutureTermLoadFacts
    constraint_issues: tuple[FutureTermIssue, ...]
    recognition_issues: tuple[FutureActionIssue, ...]
    unresolved_recognition: frozenset[tuple[str, str]]

    @property
    def hard_violations(self) -> tuple[FutureTermIssue, ...]:
        return tuple(
            issue
            for issue in self.constraint_issues
            if issue.status is FutureTermIssueStatus.VIOLATED
        )

    @property
    def hard_unknowns(self) -> tuple[FutureTermIssue, ...]:
        return tuple(
            issue
            for issue in self.constraint_issues
            if issue.status is FutureTermIssueStatus.UNRESOLVED
        )

    @property
    def known_infeasible(self) -> bool:
        return bool(self.hard_violations)

    @property
    def exact_transition_ready(self) -> bool:
        return (
            not self.hard_violations
            and not self.hard_unknowns
            and not self.unresolved_recognition
        )


@dataclass(frozen=True)
class FutureTermBundleGeneration:
    term_id: str
    selected_offering_ids: tuple[str, ...]
    load: FutureTermLoadFacts
    static_issues: tuple[FutureTermIssue, ...]
    bundles: tuple[FutureTermBundle, ...]
    dead_end_issues: tuple[FutureActionIssue, ...] = ()

    @property
    def known_infeasible(self) -> bool:
        return any(
            issue.status is FutureTermIssueStatus.VIOLATED
            for issue in self.static_issues
        )

    @property
    def has_bundles(self) -> bool:
        return bool(self.bundles)


def _load_facts(
    term: FutureTermScenario,
    offerings: tuple[FutureOffering, ...],
) -> FutureTermLoadFacts:
    total = ordinary = chapel = 0.0
    unknown: list[str] = []
    for offering in offerings:
        if offering.credits is None:
            unknown.append(offering.offering_id)
            continue
        total += offering.credits
        if offering.course_code in CHAPEL_2026_CODES:
            chapel += offering.credits
            if not term.chapel_exempt_from_ordinary_cap:
                ordinary += offering.credits
        else:
            ordinary += offering.credits
    return FutureTermLoadFacts(
        known_total_credits=total,
        known_ordinary_credits=ordinary,
        known_chapel_credits=chapel,
        unknown_credit_offering_ids=tuple(sorted(unknown)),
    )


def _periods_from_mask(mask: int, day: int) -> frozenset[int]:
    bits = (mask >> (day * 16)) & 0xFFFF
    return frozenset(period for period in range(1, 16) if bits & (1 << period))


def _static_issues(
    term: FutureTermScenario,
    offerings: tuple[FutureOffering, ...],
    load: FutureTermLoadFacts,
) -> tuple[FutureTermIssue, ...]:
    issues: list[FutureTermIssue] = []
    offering_ids = tuple(offering.offering_id for offering in offerings)

    if term.activity is TermActivity.LEAVE and offerings:
        issues.append(
            FutureTermIssue(
                code="academic_offering_selected_in_leave_term",
                status=FutureTermIssueStatus.VIOLATED,
                message="leave term cannot contain selected academic offerings",
                offering_ids=offering_ids,
            )
        )

    if load.unknown_credit_offering_ids:
        issues.append(
            FutureTermIssue(
                code="selected_credit_load_unresolved",
                status=FutureTermIssueStatus.UNRESOLVED,
                message=(
                    "selected offering credit value is unresolved, so term credit-cap feasibility cannot be established"
                ),
                offering_ids=load.unknown_credit_offering_ids,
            )
        )
    elif load.known_ordinary_credits > term.ordinary_credit_cap:
        issues.append(
            FutureTermIssue(
                code="ordinary_credit_cap_exceeded",
                status=FutureTermIssueStatus.VIOLATED,
                message=(
                    f"selected ordinary credits {load.known_ordinary_credits:g} exceed term cap {term.ordinary_credit_cap:g}"
                ),
                offering_ids=offering_ids,
            )
        )

    for offering in offerings:
        campus = offering.campus.strip()
        if not campus:
            issues.append(
                FutureTermIssue(
                    code="offering_campus_unresolved",
                    status=FutureTermIssueStatus.UNRESOLVED,
                    message="selected future offering has no campus assumption",
                    offering_ids=(offering.offering_id,),
                )
            )
            continue
        allowed = term.campus_access.allows(campus)
        if allowed is False:
            issues.append(
                FutureTermIssue(
                    code="campus_access_violated",
                    status=FutureTermIssueStatus.VIOLATED,
                    message=f"term scenario does not permit campus {campus!r}",
                    offering_ids=(offering.offering_id,),
                )
            )
        elif allowed is None:
            issues.append(
                FutureTermIssue(
                    code="campus_access_unresolved",
                    status=FutureTermIssueStatus.UNRESOLVED,
                    message="term campus access is unresolved for selected offering",
                    offering_ids=(offering.offering_id,),
                )
            )

    parsed = [
        offering for offering in offerings if isinstance(offering.schedule, ParsedSchedule)
    ]
    for offering in offerings:
        if not isinstance(offering.schedule, ParsedSchedule):
            issues.append(
                FutureTermIssue(
                    code="offering_schedule_unresolved",
                    status=FutureTermIssueStatus.UNRESOLVED,
                    message=(
                        "selected future offering lacks a safely parsed schedule, so conflict and travel feasibility are incomplete"
                    ),
                    offering_ids=(offering.offering_id,),
                )
            )

    for index, left in enumerate(parsed):
        for right in parsed[index + 1 :]:
            if left.schedule.conflict_mask & right.schedule.conflict_mask:
                issues.append(
                    FutureTermIssue(
                        code="future_timetable_conflict",
                        status=FutureTermIssueStatus.VIOLATED,
                        message="selected future offerings overlap under conflict masks",
                        offering_ids=(left.offering_id, right.offering_id),
                    )
                )

    # Mixed-campus attendance is not forbidden.  If two physical campuses occur on the
    # same day, however, the current future scenario does not yet contain transfer-time
    # assumptions, so physical feasibility remains unresolved rather than guessed.
    for day in range(7):
        campuses: dict[str, set[str]] = {}
        for offering in parsed:
            periods = _periods_from_mask(offering.schedule.presence_mask, day)
            if not periods:
                continue
            campus = offering.campus.strip()
            if not campus:
                continue
            campuses.setdefault(campus, set()).add(offering.offering_id)
        if len(campuses) > 1:
            involved = tuple(
                sorted(
                    offering_id
                    for ids in campuses.values()
                    for offering_id in ids
                )
            )
            issues.append(
                FutureTermIssue(
                    code="future_cross_campus_travel_unresolved",
                    status=FutureTermIssueStatus.UNRESOLVED,
                    message=(
                        "selected offerings require physical presence on multiple campuses in one day, but no future transfer-time scenario is supplied"
                    ),
                    offering_ids=involved,
                )
            )

    return tuple(issues)


def generate_future_term_bundles(
    term: FutureTermScenario,
    offerings: tuple[FutureOffering, ...],
    scenario: DegreeScenario,
    starting_state: DegreeState,
    *,
    recognition_evidence: Mapping[str, FutureRecognitionEvidence] | None = None,
) -> FutureTermBundleGeneration:
    """Enumerate recognition-state branches for one selected future-term course set."""

    ids = tuple(offering.offering_id for offering in offerings)
    if len(ids) != len(set(ids)):
        raise FutureTermBundleError("selected future term offerings contain duplicate ids")
    wrong_terms = [
        offering.offering_id for offering in offerings if offering.term_id != term.term_id
    ]
    if wrong_terms:
        raise FutureTermBundleError(
            "selected offering belongs to a different term: " + ", ".join(wrong_terms)
        )

    evidence_map = recognition_evidence or {}
    unknown_evidence_ids = sorted(set(evidence_map) - set(ids))
    if unknown_evidence_ids:
        raise FutureTermBundleError(
            "recognition evidence supplied for unselected offering(s): "
            + ", ".join(unknown_evidence_ids)
        )

    ordered = tuple(sorted(offerings, key=lambda offering: offering.offering_id))
    load = _load_facts(term, ordered)
    static_issues = _static_issues(term, ordered, load)
    if any(
        issue.status is FutureTermIssueStatus.VIOLATED for issue in static_issues
    ):
        return FutureTermBundleGeneration(
            term_id=term.term_id,
            selected_offering_ids=tuple(offering.offering_id for offering in ordered),
            load=load,
            static_issues=static_issues,
            bundles=(),
        )

    bundles: list[FutureTermBundle] = []
    dead_end_issues: list[FutureActionIssue] = []

    def recurse(
        index: int,
        state: DegreeState,
        actions: tuple[FutureAcademicAction, ...],
        recognition_issues: tuple[FutureActionIssue, ...],
        unresolved: frozenset[tuple[str, str]],
    ) -> None:
        if index == len(ordered):
            bundles.append(
                FutureTermBundle(
                    term_id=term.term_id,
                    offering_ids=tuple(offering.offering_id for offering in ordered),
                    actions=actions,
                    starting_state=starting_state,
                    resulting_state=state,
                    load=load,
                    constraint_issues=static_issues,
                    recognition_issues=recognition_issues,
                    unresolved_recognition=unresolved,
                )
            )
            return

        offering = ordered[index]
        generated = generate_future_academic_actions(
            offering,
            scenario,
            state,
            evidence=evidence_map.get(
                offering.offering_id, FutureRecognitionEvidence()
            ),
        )
        if not generated.actions:
            dead_end_issues.extend(generated.issues)
            return

        next_unresolved = unresolved | frozenset(
            (offering.offering_id, requirement_id)
            for requirement_id in generated.unresolved_requirement_ids
        )
        next_issues = recognition_issues + generated.issues
        for action in generated.actions:
            recurse(
                index + 1,
                action.resulting_state,
                actions + (action,),
                next_issues,
                next_unresolved,
            )

    recurse(0, starting_state, (), (), frozenset())

    return FutureTermBundleGeneration(
        term_id=term.term_id,
        selected_offering_ids=tuple(offering.offering_id for offering in ordered),
        load=load,
        static_issues=static_issues,
        bundles=tuple(bundles),
        dead_end_issues=tuple(dead_end_issues),
    )
