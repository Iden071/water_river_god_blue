"""Coverage-first exhaustive Fall + future search for Stage 4E.

This module connects the Stage 4E pieces built so far:

    Fall section universe
      -> exhaustive section-set enumeration
      -> present CandidateAssessment
      -> stateful Fall degree-transition branches
      -> rebased finite future problem
      -> one Fall + future objective
      -> proof-safe frontier across *all* Fall branches.

It is deliberately a reference implementation, not yet the scalable production search.
A truncated Fall subset enumeration is never evaluated as if it were a shortlist: the search
returns ``SEARCH_INCOMPLETE`` immediately.  Likewise, an unresolved Fall feasibility or
recognition branch is retained as an unresolved alternative that blocks an optimum proof.

Known-infeasible Fall sets and continuation branches proven unable to complete the degree may
be discarded safely.  Everything else must either reach the common whole-plan frontier or
remain visible as uncertainty.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from .candidate_assessment import (
    CandidateAssessment,
    CandidateConstraintIssue,
    ConstraintEvidenceStatus,
    assess_candidate,
)
from .catalog import CatalogSnapshot
from .course_preferences import ProfessorRatingBook
from .degree import DegreeScenario, DegreeState
from .degree_remainder import degree_remainder
from .fall_actions import (
    FallDegreeTransitionBranch,
    FallRecognitionEvidence,
    generate_fall_degree_transitions,
)
from .fall_candidate_sets import (
    FallCandidateSet,
    FallCandidateSetEnumeration,
    FallCandidateSetEnumerationStatus,
)
from .future_actions import FutureRecognitionEvidence
from .future_problem import FuturePlanningProblem
from .future_utility import TemporalUtilityAggregation
from .preferences import PreferenceProfile, PreferenceValue
from .registration import RegistrationAssessment
from .whole_plan_optimization import (
    WholePlanHorizonFrontier,
    WholePlanOptimizationAssessment,
    WholePlanOptimizationStatus,
    WholePlanUtilityCandidate,
    assess_fall_candidate_whole_plan,
    build_safe_whole_plan_frontiers,
)
from .fall_continuation import build_fall_continuation_bridge


class FallSearchError(ValueError):
    """End-to-end Fall search inputs violate the Stage 4E contract."""


class FallWholePlanSearchStatus(str, Enum):
    GLOBAL_OPTIMUM_PROVEN = "global_optimum_proven"
    SCOPED_OPTIMUM_PROVEN = "scoped_optimum_proven"
    PROVEN_NO_REACHABLE_PLAN = "proven_no_reachable_plan"
    BOUNDED_FRONTIER = "bounded_frontier"
    UTILITY_UNRESOLVED = "utility_unresolved"
    HORIZON_INCOMPARABLE = "horizon_incomparable"
    UNRESOLVED_ALTERNATIVES = "unresolved_alternatives"
    SEARCH_INCOMPLETE = "search_incomplete"
    INPUT_BLOCKED = "input_blocked"


@dataclass(frozen=True)
class FallSearchUnknown:
    code: str
    message: str
    fall_set_id: str = ""
    branch_id: str = ""
    section_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.code.strip() or not self.message.strip():
            raise FallSearchError("Fall search unknown requires code and message")


@dataclass(frozen=True)
class FallWholePlanBranchResult:
    """One exact Fall degree-recognition branch and its continuation assessment."""

    branch_id: str
    fall_set_id: str
    section_ids: tuple[str, ...]
    transition_option_ids: tuple[str, ...]
    candidate: CandidateAssessment
    whole_plan: WholePlanOptimizationAssessment


@dataclass(frozen=True)
class FallWholePlanSearchResult:
    status: FallWholePlanSearchStatus
    candidate_sets: FallCandidateSetEnumeration
    branch_results: tuple[FallWholePlanBranchResult, ...]
    utility_candidates: tuple[WholePlanUtilityCandidate, ...]
    frontiers: tuple[WholePlanHorizonFrontier, ...]
    known_infeasible_fall_set_ids: frozenset[str]
    proven_unreachable_branch_ids: frozenset[str]
    unresolved_alternatives: tuple[FallSearchUnknown, ...]
    blocker_codes: frozenset[str]

    @property
    def optimum_proven(self) -> bool:
        return self.status in {
            FallWholePlanSearchStatus.GLOBAL_OPTIMUM_PROVEN,
            FallWholePlanSearchStatus.SCOPED_OPTIMUM_PROVEN,
        }

    @property
    def global_optimum_proven(self) -> bool:
        return self.status is FallWholePlanSearchStatus.GLOBAL_OPTIMUM_PROVEN

    @property
    def scoped_optimum_proven(self) -> bool:
        return self.status is FallWholePlanSearchStatus.SCOPED_OPTIMUM_PROVEN

    @property
    def proven_best(self) -> WholePlanUtilityCandidate | None:
        if not self.optimum_proven or len(self.frontiers) != 1:
            return None
        return self.frontiers[0].unique_proven_best

    @property
    def proven_best_branch(self) -> FallWholePlanBranchResult | None:
        best = self.proven_best
        if best is None:
            return None
        hits = [
            branch
            for branch in self.branch_results
            if branch.whole_plan.bridge.candidate_id == best.fall_candidate_id
        ]
        return hits[0] if len(hits) == 1 else None


def _fall_set_id(index: int) -> str:
    return f"fall-set-{index:06d}"


def _credit_cap_unknown_issue(
    candidate_set: FallCandidateSet,
    enumeration: FallCandidateSetEnumeration,
) -> tuple[CandidateConstraintIssue, ...]:
    if not candidate_set.load.unknown_credit_section_ids:
        return ()
    return (
        CandidateConstraintIssue(
            code="ordinary_credit_cap_unresolved",
            status=ConstraintEvidenceStatus.UNRESOLVED,
            message=(
                "selected Fall section has unresolved credits, so compliance with the explicit ordinary-credit cap cannot be established"
            ),
            section_ids=candidate_set.load.unknown_credit_section_ids,
            source=enumeration.load_policy.source_id,
        ),
    )


def _recognition_map(
    branch: FallDegreeTransitionBranch,
) -> dict[str, object]:
    # Kept as a tiny helper so duplicate physical recognition identities become an explicit
    # integration failure rather than a last-write-wins dictionary accident.
    out: dict[str, object] = {}
    for assessment in branch.recognitions:
        if assessment.section_id in out:
            raise FallSearchError(
                f"duplicate recognition assessment for {assessment.section_id!r} in Fall branch"
            )
        out[assessment.section_id] = assessment
    return out


def _unknown(
    code: str,
    message: str,
    *,
    fall_set_id: str,
    branch_id: str = "",
    section_ids: tuple[str, ...] = (),
) -> FallSearchUnknown:
    return FallSearchUnknown(
        code=code,
        message=message,
        fall_set_id=fall_set_id,
        branch_id=branch_id,
        section_ids=section_ids,
    )


def _dedupe_unknowns(items: list[FallSearchUnknown]) -> tuple[FallSearchUnknown, ...]:
    out: list[FallSearchUnknown] = []
    seen: set[FallSearchUnknown] = set()
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return tuple(out)


def search_fall_whole_plans(
    candidate_sets: FallCandidateSetEnumeration,
    snapshot: CatalogSnapshot,
    degree_scenario: DegreeScenario,
    starting_state: DegreeState,
    future_template: FuturePlanningProblem,
    preference_profile: PreferenceProfile,
    professor_ratings: ProfessorRatingBook,
    temporal_aggregation: TemporalUtilityAggregation,
    *,
    registration_assessments: Mapping[str, RegistrationAssessment] | None = None,
    fall_recognition_evidence: Mapping[str, FallRecognitionEvidence] | None = None,
    future_recognition_evidence: Mapping[str, FutureRecognitionEvidence] | None = None,
    subject_interest: Mapping[str, PreferenceValue] | None = None,
    workload_utility: Mapping[str, PreferenceValue] | None = None,
    difficulty_utility: Mapping[str, PreferenceValue] | None = None,
    resolved_present_dimensions: Mapping[str, PreferenceValue] | None = None,
    max_future_selection_evaluations: int = 100_000,
) -> FallWholePlanSearchResult:
    """Evaluate every exact Fall set/recognition branch under the same whole-plan objective."""

    if max_future_selection_evaluations <= 0:
        raise FallSearchError("max_future_selection_evaluations must be positive")
    baseline = degree_remainder(starting_state, degree_scenario)
    if future_template.degree_remainder != baseline:
        raise FallSearchError(
            "future template remainder does not match the supplied Fall starting DegreeState"
        )

    if candidate_sets.status is FallCandidateSetEnumerationStatus.INPUT_BLOCKED:
        blockers = {
            f"fall_universe::{unknown.code}"
            for unknown in candidate_sets.universe.scope_unknowns
        }
        return FallWholePlanSearchResult(
            status=FallWholePlanSearchStatus.INPUT_BLOCKED,
            candidate_sets=candidate_sets,
            branch_results=(),
            utility_candidates=(),
            frontiers=(),
            known_infeasible_fall_set_ids=frozenset(),
            proven_unreachable_branch_ids=frozenset(),
            unresolved_alternatives=(),
            blocker_codes=frozenset(blockers),
        )

    # A truncated powerset is not a shortlist.  Do not spend continuation-search effort on
    # its prefix and, more importantly, do not expose a provisional winner as if it were a
    # candidate for proof.
    if not candidate_sets.enumeration_complete:
        return FallWholePlanSearchResult(
            status=FallWholePlanSearchStatus.SEARCH_INCOMPLETE,
            candidate_sets=candidate_sets,
            branch_results=(),
            utility_candidates=(),
            frontiers=(),
            known_infeasible_fall_set_ids=frozenset(),
            proven_unreachable_branch_ids=frozenset(),
            unresolved_alternatives=(),
            blocker_codes=frozenset({"fall_section_set_enumeration_incomplete"}),
        )

    registration_map = registration_assessments or {}
    fall_evidence = fall_recognition_evidence or {}
    resolutions = resolved_present_dimensions or {}

    branch_results: list[FallWholePlanBranchResult] = []
    utility_candidates: list[WholePlanUtilityCandidate] = []
    known_infeasible_sets: set[str] = set()
    proven_unreachable_branches: set[str] = set()
    unresolved: list[FallSearchUnknown] = []
    blockers: set[str] = set()
    continuation_search_incomplete = False

    for set_index, candidate_set in enumerate(candidate_sets.candidates):
        fall_set_id = _fall_set_id(set_index)
        static_extra = _credit_cap_unknown_issue(candidate_set, candidate_sets)

        preliminary = assess_candidate(
            candidate_set.sections,
            preference_profile,
            professor_ratings,
            subject_interest=subject_interest,
            workload_utility=workload_utility,
            difficulty_utility=difficulty_utility,
            registration_assessments=registration_map,
            degree_scenario=degree_scenario,
            external_constraint_issues=static_extra,
        )
        if preliminary.known_infeasible:
            known_infeasible_sets.add(fall_set_id)
            continue
        if preliminary.hard_constraint_unknowns:
            for issue in preliminary.hard_constraint_unknowns:
                unresolved.append(
                    _unknown(
                        f"fall_hard::{issue.code}",
                        issue.message,
                        fall_set_id=fall_set_id,
                        section_ids=issue.section_ids,
                    )
                )
            continue

        selected_ids = set(candidate_set.section_ids)
        transition_evidence = {
            section_id: evidence
            for section_id, evidence in fall_evidence.items()
            if section_id in selected_ids
        }
        transitions = generate_fall_degree_transitions(
            candidate_set.sections,
            snapshot,
            degree_scenario,
            starting_state,
            evidence=transition_evidence,
        )
        if transitions.unresolved_issues:
            for issue in transitions.unresolved_issues:
                unresolved.append(
                    _unknown(
                        f"fall_transition::{issue.code}",
                        issue.message,
                        fall_set_id=fall_set_id,
                        section_ids=(issue.section_id,),
                    )
                )
        if not transitions.branches:
            if not transitions.unresolved_issues:
                raise FallSearchError(
                    f"Fall set {fall_set_id} produced neither exact transition branches nor unresolved issues"
                )
            continue

        for branch_index, transition_branch in enumerate(transitions.branches):
            branch_id = f"{fall_set_id}::transition-{branch_index:03d}"
            raw_map = _recognition_map(transition_branch)
            recognition_map = {
                section_id: assessment  # type: ignore[assignment]
                for section_id, assessment in raw_map.items()
            }
            candidate = assess_candidate(
                candidate_set.sections,
                preference_profile,
                professor_ratings,
                subject_interest=subject_interest,
                workload_utility=workload_utility,
                difficulty_utility=difficulty_utility,
                registration_assessments=registration_map,
                recognition_assessments=recognition_map,  # type: ignore[arg-type]
                degree_scenario=degree_scenario,
                degree_transition=transition_branch.transition,
                external_constraint_issues=static_extra,
            )

            active_resolutions = {
                dimension_id: value
                for dimension_id, value in resolutions.items()
                if dimension_id in candidate.present_preference_unknowns
            }
            bridge = build_fall_continuation_bridge(
                branch_id,
                candidate,
                degree_scenario,
                future_template,
                resolved_present_dimensions=active_resolutions,
            )
            whole = assess_fall_candidate_whole_plan(
                bridge,
                degree_scenario,
                preference_profile,
                professor_ratings,
                temporal_aggregation,
                recognition_evidence=future_recognition_evidence,
                subject_interest=subject_interest,
                workload_utility=workload_utility,
                difficulty_utility=difficulty_utility,
                max_selection_evaluations=max_future_selection_evaluations,
            )
            branch_results.append(
                FallWholePlanBranchResult(
                    branch_id=branch_id,
                    fall_set_id=fall_set_id,
                    section_ids=candidate_set.section_ids,
                    transition_option_ids=transition_branch.transition.selected_option_ids,
                    candidate=candidate,
                    whole_plan=whole,
                )
            )

            if whole.status is WholePlanOptimizationStatus.PROVEN_UNREACHABLE:
                proven_unreachable_branches.add(branch_id)
                continue
            if whole.status is WholePlanOptimizationStatus.SEARCH_INCOMPLETE:
                continuation_search_incomplete = True
                blockers.add("future_completion_search_incomplete")
                blockers.update(whole.blocker_codes)
                utility_candidates.extend(whole.candidates)
                continue
            if whole.status is WholePlanOptimizationStatus.FUTURE_INPUT_BLOCKED:
                unresolved.append(
                    _unknown(
                        "future_input_blocked",
                        "future continuation inputs are insufficient for exact evaluation",
                        fall_set_id=fall_set_id,
                        branch_id=branch_id,
                        section_ids=candidate_set.section_ids,
                    )
                )
                blockers.update(whole.blocker_codes)
                continue
            if whole.status is WholePlanOptimizationStatus.FALL_BLOCKED:
                unresolved.append(
                    _unknown(
                        "fall_branch_blocked",
                        "selected Fall transition branch remains unresolved at the continuation boundary",
                        fall_set_id=fall_set_id,
                        branch_id=branch_id,
                        section_ids=candidate_set.section_ids,
                    )
                )
                blockers.update(whole.blocker_codes)
                continue

            # OPTIMUM_PROVEN / BOUNDED_FRONTIER / UTILITY_UNRESOLVED /
            # HORIZON_INCOMPARABLE are all exact continuation searches whose candidates
            # belong on the global Fall frontier.  Their local status must not rank Fall
            # branches before they meet each other.
            utility_candidates.extend(whole.candidates)

    unresolved_tuple = _dedupe_unknowns(unresolved)
    frontiers = (
        build_safe_whole_plan_frontiers(tuple(utility_candidates))
        if utility_candidates
        else ()
    )

    if continuation_search_incomplete:
        return FallWholePlanSearchResult(
            FallWholePlanSearchStatus.SEARCH_INCOMPLETE,
            candidate_sets,
            tuple(branch_results),
            tuple(utility_candidates),
            frontiers,
            frozenset(known_infeasible_sets),
            frozenset(proven_unreachable_branches),
            unresolved_tuple,
            frozenset(blockers),
        )

    if unresolved_tuple:
        blockers.update(item.code for item in unresolved_tuple)
        return FallWholePlanSearchResult(
            FallWholePlanSearchStatus.UNRESOLVED_ALTERNATIVES,
            candidate_sets,
            tuple(branch_results),
            tuple(utility_candidates),
            frontiers,
            frozenset(known_infeasible_sets),
            frozenset(proven_unreachable_branches),
            unresolved_tuple,
            frozenset(blockers),
        )

    if not utility_candidates:
        return FallWholePlanSearchResult(
            FallWholePlanSearchStatus.PROVEN_NO_REACHABLE_PLAN,
            candidate_sets,
            tuple(branch_results),
            (),
            (),
            frozenset(known_infeasible_sets),
            frozenset(proven_unreachable_branches),
            (),
            frozenset(blockers),
        )

    if len(frontiers) > 1:
        blockers.add("graduation_timing_utility_unresolved")
        return FallWholePlanSearchResult(
            FallWholePlanSearchStatus.HORIZON_INCOMPARABLE,
            candidate_sets,
            tuple(branch_results),
            tuple(utility_candidates),
            frontiers,
            frozenset(known_infeasible_sets),
            frozenset(proven_unreachable_branches),
            (),
            frozenset(blockers),
        )

    frontier = frontiers[0]
    if frontier.unresolved_candidates:
        blockers.add("whole_plan_utility_unresolved")
        return FallWholePlanSearchResult(
            FallWholePlanSearchStatus.UTILITY_UNRESOLVED,
            candidate_sets,
            tuple(branch_results),
            tuple(utility_candidates),
            frontiers,
            frozenset(known_infeasible_sets),
            frozenset(proven_unreachable_branches),
            (),
            frozenset(blockers),
        )

    if frontier.unique_proven_best is not None:
        status = (
            FallWholePlanSearchStatus.GLOBAL_OPTIMUM_PROVEN
            if candidate_sets.global_search_space_complete
            else FallWholePlanSearchStatus.SCOPED_OPTIMUM_PROVEN
        )
        return FallWholePlanSearchResult(
            status,
            candidate_sets,
            tuple(branch_results),
            tuple(utility_candidates),
            frontiers,
            frozenset(known_infeasible_sets),
            frozenset(proven_unreachable_branches),
            (),
            frozenset(blockers),
        )

    blockers.add("complete_whole_plan_bounds_overlap")
    return FallWholePlanSearchResult(
        FallWholePlanSearchStatus.BOUNDED_FRONTIER,
        candidate_sets,
        tuple(branch_results),
        tuple(utility_candidates),
        frontiers,
        frozenset(known_infeasible_sets),
        frozenset(proven_unreachable_branches),
        (),
        frozenset(blockers),
    )
