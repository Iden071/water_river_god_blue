"""Proof-aware Fall section-set enumeration for Stage 4E.

This is deliberately a *set generator*, not a ranker.  It enumerates subsets of an explicit
:class:`~timetable_optimizer.fall_universe.FallSectionUniverse` while applying only static
hard facts that are already safe at this layer:

* an explicit ordinary-credit ceiling;
* canonical registration-conflict masks when schedules are parsed.

There is no six-course rule, no requirement-slot template, no MAX_DEFER, no OPEN pool, and
no 18-credit target promoted to feasibility.  Unknown credit or schedule information remains
inside emitted candidates as unresolved evidence.  A caller can then run the unified
CandidateAssessment, stateful Fall recognition branches, and the whole-plan objective.

A subset-evaluation limit is only a computational safety valve.  Hitting it returns
``TRUNCATED`` and can never support a global-optimum claim; it is not a top-N ranking step.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite

from .fall_universe import FallSectionUniverse, FallUniverseStatus
from .recognition import CHAPEL_2026_CODES
from .sections import ParsedSchedule, Section


class FallCandidateSetError(ValueError):
    """Fall section-set enumeration inputs are inconsistent."""


class FallCandidateSetEnumerationStatus(str, Enum):
    COMPLETE = "complete"
    TRUNCATED = "truncated"
    INPUT_BLOCKED = "input_blocked"


@dataclass(frozen=True)
class FallLoadPolicy:
    """Explicit hard credit-cap policy for the current Fall term.

    A preferred load (for example 18 credits) belongs in utility, not here.  This policy
    carries only the maximum ordinary credit load and whether Chapel is exempt from it.
    """

    ordinary_credit_cap: float
    chapel_exempt_from_ordinary_cap: bool
    source_id: str
    note: str = ""

    def __post_init__(self) -> None:
        if not isfinite(self.ordinary_credit_cap) or self.ordinary_credit_cap <= 0:
            raise FallCandidateSetError(
                "Fall ordinary credit cap must be finite and positive"
            )
        if not self.source_id.strip():
            raise FallCandidateSetError("Fall load policy requires source_id")


def fall2026_load_policy() -> FallLoadPolicy:
    """Current Stage 4 Fall load policy from the authoritative project specification."""

    return FallLoadPolicy(
        ordinary_credit_cap=22.0,
        chapel_exempt_from_ordinary_cap=True,
        source_id="SPEC.md §3.3",
        note=(
            "credit load, not raw course count, governs the Fall search; Chapel 0.5 credit "
            "does not count toward the ordinary maximum"
        ),
    )


@dataclass(frozen=True)
class FallCandidateLoadFacts:
    known_total_credits: float
    known_ordinary_credits: float
    known_chapel_credits: float
    unknown_credit_section_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        for value in (
            self.known_total_credits,
            self.known_ordinary_credits,
            self.known_chapel_credits,
        ):
            if not isfinite(value) or value < 0:
                raise FallCandidateSetError(
                    "Fall candidate known credit totals must be finite and nonnegative"
                )


@dataclass(frozen=True)
class FallCandidateSet:
    """One Fall physical-section subset not known to violate enumeration-level facts."""

    section_ids: tuple[str, ...]
    sections: tuple[Section, ...]
    load: FallCandidateLoadFacts
    unresolved_schedule_section_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.section_ids != tuple(section.section_id for section in self.sections):
            raise FallCandidateSetError(
                "Fall candidate section_ids must match section tuple order exactly"
            )
        if len(self.section_ids) != len(set(self.section_ids)):
            raise FallCandidateSetError("Fall candidate contains duplicate physical section")

    @property
    def enumeration_unknowns(self) -> frozenset[str]:
        unknowns = {
            f"credit::{section_id}"
            for section_id in self.load.unknown_credit_section_ids
        }
        unknowns.update(
            f"schedule::{section_id}"
            for section_id in self.unresolved_schedule_section_ids
        )
        return frozenset(unknowns)

    @property
    def enumeration_constraints_exact(self) -> bool:
        return not self.enumeration_unknowns


@dataclass(frozen=True)
class FallCandidateSetEnumeration:
    universe: FallSectionUniverse
    load_policy: FallLoadPolicy
    status: FallCandidateSetEnumerationStatus
    candidates: tuple[FallCandidateSet, ...]
    evaluated_subsets: int
    pruned_include_branches_by_conflict: int
    pruned_include_branches_by_credit_cap: int
    max_subset_evaluations: int

    @property
    def enumeration_complete(self) -> bool:
        return self.status is FallCandidateSetEnumerationStatus.COMPLETE

    @property
    def exact_scoped_search_space_complete(self) -> bool:
        return self.enumeration_complete and self.universe.exact_scope_coverage

    @property
    def global_search_space_complete(self) -> bool:
        return (
            self.enumeration_complete
            and self.universe.eligible_for_global_optimum_claim
        )


def _credit_effect(
    section: Section,
    policy: FallLoadPolicy,
) -> tuple[float, float, float, bool]:
    """Return total, ordinary, Chapel known-credit additions and whether credit is unknown."""

    if section.credits is None:
        return 0.0, 0.0, 0.0, True
    total = float(section.credits)
    if section.course_code in CHAPEL_2026_CODES:
        chapel = total
        ordinary = 0.0 if policy.chapel_exempt_from_ordinary_cap else total
    else:
        chapel = 0.0
        ordinary = total
    return total, ordinary, chapel, False


def enumerate_fall_candidate_sets(
    universe: FallSectionUniverse,
    load_policy: FallLoadPolicy,
    *,
    max_subset_evaluations: int = 100_000,
) -> FallCandidateSetEnumeration:
    """Enumerate every subset not *known* to violate the static Fall constraints.

    The iteration is an explicit depth-first powerset search rather than recursion so a
    full canonical catalogue cannot fail merely because it contains more sections than the
    Python recursion limit.  Parsed conflict masks and the known portion of ordinary credit
    load may prune branches.  Unknown credits/schedules cannot.
    """

    if max_subset_evaluations <= 0:
        raise FallCandidateSetError("max_subset_evaluations must be positive")
    if universe.status is FallUniverseStatus.INPUT_BLOCKED:
        return FallCandidateSetEnumeration(
            universe=universe,
            load_policy=load_policy,
            status=FallCandidateSetEnumerationStatus.INPUT_BLOCKED,
            candidates=(),
            evaluated_subsets=0,
            pruned_include_branches_by_conflict=0,
            pruned_include_branches_by_credit_cap=0,
            max_subset_evaluations=max_subset_evaluations,
        )

    ordered = tuple(sorted(universe.included_sections, key=lambda section: section.section_id))
    candidates: list[FallCandidateSet] = []
    evaluated = 0
    pruned_conflict = 0
    pruned_credit = 0

    # Stack tuple:
    # index, selected sections, accumulated parsed conflict mask,
    # known total/ordinary/chapel credits, unknown-credit ids, unresolved-schedule ids.
    stack: list[
        tuple[
            int,
            tuple[Section, ...],
            int,
            float,
            float,
            float,
            tuple[str, ...],
            tuple[str, ...],
        ]
    ] = [(0, (), 0, 0.0, 0.0, 0.0, (), ())]
    truncated = False

    while stack:
        (
            index,
            selected,
            conflict_mask,
            known_total,
            known_ordinary,
            known_chapel,
            unknown_credit_ids,
            unresolved_schedule_ids,
        ) = stack.pop()

        if index == len(ordered):
            if evaluated >= max_subset_evaluations:
                truncated = True
                break
            sections = selected
            candidates.append(
                FallCandidateSet(
                    section_ids=tuple(section.section_id for section in sections),
                    sections=sections,
                    load=FallCandidateLoadFacts(
                        known_total_credits=known_total,
                        known_ordinary_credits=known_ordinary,
                        known_chapel_credits=known_chapel,
                        unknown_credit_section_ids=unknown_credit_ids,
                    ),
                    unresolved_schedule_section_ids=unresolved_schedule_ids,
                )
            )
            evaluated += 1
            continue

        section = ordered[index]

        # Push INCLUDE first so EXCLUDE is explored first under LIFO.  That quickly obtains
        # small diagnostic candidates without assigning them any ranking significance.
        include_conflict = False
        next_conflict_mask = conflict_mask
        next_unresolved_schedules = unresolved_schedule_ids
        if isinstance(section.schedule, ParsedSchedule):
            if conflict_mask & section.schedule.conflict_mask:
                include_conflict = True
            else:
                next_conflict_mask |= section.schedule.conflict_mask
        else:
            next_unresolved_schedules = unresolved_schedule_ids + (section.section_id,)

        add_total, add_ordinary, add_chapel, credit_unknown = _credit_effect(
            section, load_policy
        )
        next_ordinary = known_ordinary + add_ordinary
        include_credit_violation = next_ordinary > load_policy.ordinary_credit_cap

        if include_conflict:
            pruned_conflict += 1
        elif include_credit_violation:
            pruned_credit += 1
        else:
            stack.append(
                (
                    index + 1,
                    selected + (section,),
                    next_conflict_mask,
                    known_total + add_total,
                    next_ordinary,
                    known_chapel + add_chapel,
                    unknown_credit_ids + ((section.section_id,) if credit_unknown else ()),
                    next_unresolved_schedules,
                )
            )

        # Excluding a section is always structurally available at this layer.  Whether
        # postponing it is desirable is a future-state question, not a Fall hard constraint.
        stack.append(
            (
                index + 1,
                selected,
                conflict_mask,
                known_total,
                known_ordinary,
                known_chapel,
                unknown_credit_ids,
                unresolved_schedule_ids,
            )
        )

    status = (
        FallCandidateSetEnumerationStatus.TRUNCATED
        if truncated or stack
        else FallCandidateSetEnumerationStatus.COMPLETE
    )
    return FallCandidateSetEnumeration(
        universe=universe,
        load_policy=load_policy,
        status=status,
        candidates=tuple(candidates),
        evaluated_subsets=evaluated,
        pruned_include_branches_by_conflict=pruned_conflict,
        pruned_include_branches_by_credit_cap=pruned_credit,
        max_subset_evaluations=max_subset_evaluations,
    )
