"""Finite degree-remainder facts for Stage 4D.

The old continuation model could make obligations disappear into anonymous ``DM``/``FREE``
fillers.  This module instead asks a narrower exact question:

    given a concrete DegreeScenario and DegreeState, what institutional obligations remain?

The answer preserves each requirement's real shape.  A specific course stays a specific
course, an any-of requirement stays a choice, a category requirement stays a category
count, a credit bucket stays a bucket, and Chapel stays a pass requirement.

``graduation_credit_deficit`` is reported separately from named requirement deficits.  They
must not be added naively because one future completion can satisfy a named requirement and
also reduce the graduation-credit deficit.  Residual graduation credits are therefore not
materialized as fake future courses here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from .degree import (
    AnyOfRequirement,
    CategoryCountRequirement,
    ChapelRequirement,
    CreditBucketRequirement,
    DegreeRuleError,
    DegreeScenario,
    DegreeState,
    SecondMajorStatus,
    SpecificCourseRequirement,
)


@dataclass(frozen=True)
class SpecificCourseRemainder:
    requirement_id: str
    title: str
    course_codes: tuple[str, ...]
    credits: float
    counts_toward_qrm_major: bool


@dataclass(frozen=True)
class AnyOfRemainder:
    requirement_id: str
    title: str
    course_codes: tuple[str, ...]
    credits: float
    counts_toward_qrm_major: bool


@dataclass(frozen=True)
class CategoryCountRemainder:
    requirement_id: str
    title: str
    remaining_count: int
    remaining_categories: tuple[str, ...]
    credits_per_category: float


@dataclass(frozen=True)
class CreditBucketRemainder:
    requirement_id: str
    title: str
    remaining_credits: float
    qualification_rule_id: str
    counts_toward_qrm_major: bool


@dataclass(frozen=True)
class ChapelRemainder:
    requirement_id: str
    title: str
    remaining_passes: int
    credits_per_pass: float
    offline_passes_required: int | None
    offline_passes_min: int
    offline_passes_max: int

    @property
    def modality_rule_resolved(self) -> bool:
        return self.offline_passes_required is not None


RequirementRemainder: TypeAlias = (
    SpecificCourseRemainder
    | AnyOfRemainder
    | CategoryCountRemainder
    | CreditBucketRemainder
    | ChapelRemainder
)


@dataclass(frozen=True)
class DegreeRemainder:
    """Exact finite obligation ledger for one degree state/scenario pair."""

    scenario_id: str
    graduation_credit_deficit: float
    requirements: tuple[RequirementRemainder, ...]
    structural_unknowns: frozenset[str] = frozenset()

    @property
    def requirement_ids(self) -> tuple[str, ...]:
        return tuple(requirement.requirement_id for requirement in self.requirements)

    @property
    def named_requirements_complete(self) -> bool:
        return not self.requirements

    @property
    def structurally_resolved(self) -> bool:
        return not self.structural_unknowns

    @property
    def degree_obligations_complete(self) -> bool:
        return (
            self.graduation_credit_deficit <= 0
            and self.named_requirements_complete
            and self.structurally_resolved
        )

    def requirement(self, requirement_id: str) -> RequirementRemainder:
        hits = [
            requirement
            for requirement in self.requirements
            if requirement.requirement_id == requirement_id
        ]
        if len(hits) != 1:
            raise DegreeRuleError(
                f"expected exactly one remaining requirement {requirement_id!r}, found {len(hits)}"
            )
        return hits[0]


def degree_remainder(
    state: DegreeState,
    scenario: DegreeScenario,
) -> DegreeRemainder:
    """Return the non-anonymous remainder of ``scenario`` after ``state``.

    This is a pure projection of the canonical degree state.  It does not predict future
    course offerings, choose substitutions, create elective filler, or infer missing
    second-major structure.
    """

    out: list[RequirementRemainder] = []
    unknowns: set[str] = set()

    if scenario.second_major.status is SecondMajorStatus.UNRESOLVED:
        name = scenario.second_major.name or "unspecified"
        unknowns.add(f"second_major_structure::{name}")

    for requirement in scenario.requirements:
        if isinstance(requirement, SpecificCourseRequirement):
            if state.is_requirement_satisfied(scenario, requirement.requirement_id):
                continue
            out.append(
                SpecificCourseRemainder(
                    requirement_id=requirement.requirement_id,
                    title=requirement.title,
                    course_codes=requirement.course_codes,
                    credits=requirement.credits,
                    counts_toward_qrm_major=requirement.counts_toward_qrm_major,
                )
            )
            continue

        if isinstance(requirement, AnyOfRequirement):
            if state.is_requirement_satisfied(scenario, requirement.requirement_id):
                continue
            out.append(
                AnyOfRemainder(
                    requirement_id=requirement.requirement_id,
                    title=requirement.title,
                    course_codes=requirement.course_codes,
                    credits=requirement.credits,
                    counts_toward_qrm_major=requirement.counts_toward_qrm_major,
                )
            )
            continue

        if isinstance(requirement, CategoryCountRequirement):
            claimed = state.categories_for(requirement.requirement_id)
            remaining_count = max(0, requirement.required_count - len(claimed))
            if remaining_count == 0:
                continue
            remaining_categories = tuple(
                category
                for category in requirement.categories
                if category not in claimed
            )
            if remaining_count > len(remaining_categories):
                raise DegreeRuleError(
                    f"category remainder for {requirement.requirement_id!r} is impossible under current state"
                )
            out.append(
                CategoryCountRemainder(
                    requirement_id=requirement.requirement_id,
                    title=requirement.title,
                    remaining_count=remaining_count,
                    remaining_categories=remaining_categories,
                    credits_per_category=requirement.credits_per_category,
                )
            )
            continue

        if isinstance(requirement, CreditBucketRequirement):
            claimed = state.bucket_credits_for(requirement.requirement_id)
            remaining = max(0.0, requirement.target_credits - claimed)
            if remaining <= 0:
                continue
            out.append(
                CreditBucketRemainder(
                    requirement_id=requirement.requirement_id,
                    title=requirement.title,
                    remaining_credits=remaining,
                    qualification_rule_id=requirement.qualification_rule_id,
                    counts_toward_qrm_major=requirement.counts_toward_qrm_major,
                )
            )
            continue

        if isinstance(requirement, ChapelRequirement):
            remaining_passes = max(
                0, requirement.passes_required - state.chapel.passes_completed
            )
            modality_unresolved = requirement.offline_passes_required is None
            if remaining_passes == 0 and not modality_unresolved:
                if state.is_requirement_satisfied(scenario, requirement.requirement_id):
                    continue
            if modality_unresolved:
                unknowns.add(
                    f"chapel_modality_rule::{requirement.requirement_id}"
                )
            if remaining_passes > 0 or modality_unresolved:
                out.append(
                    ChapelRemainder(
                        requirement_id=requirement.requirement_id,
                        title=requirement.title,
                        remaining_passes=remaining_passes,
                        credits_per_pass=requirement.credits_per_pass,
                        offline_passes_required=requirement.offline_passes_required,
                        offline_passes_min=state.chapel.offline_passes_min,
                        offline_passes_max=state.chapel.offline_passes_max,
                    )
                )
            continue

        raise DegreeRuleError(
            f"unsupported requirement type in degree remainder: {type(requirement).__name__}"
        )

    return DegreeRemainder(
        scenario_id=scenario.scenario_id,
        graduation_credit_deficit=state.graduation_credit_deficit(scenario),
        requirements=tuple(out),
        structural_unknowns=frozenset(unknowns),
    )
