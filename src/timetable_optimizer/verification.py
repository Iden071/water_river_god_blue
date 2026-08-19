"""Manual-verification authority for Stage 4 model evidence.

Search correctness and source verification are different questions.

A solver may prove that a plan is optimal *under the encoded model* while some institutional
facts inside that model still come from provisional research that the user has not manually
double-checked.  This module keeps those claims separate.

Governing rule (SPEC v0.5):

* facts promoted into SPEC are manually validated authority;
* a fact directly confirmed by the user may be marked USER_CONFIRMED while it is being
  promoted into SPEC;
* everything else defaults to PROVISIONAL, regardless of how confident an old comment,
  RULES entry, or research note sounds;
* genuinely unresolved evidence remains UNRESOLVED.

This layer does not change feasibility or utility semantics.  It tells callers whether an
otherwise exact result is also ready to be described as manually verified.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping

from .degree import DegreeScenario, SecondMajorStatus
from .fall_candidate_sets import FallCandidateSetEnumeration
from .registration import RegistrationAssessment, YearQuotaGateStatus


class VerificationError(ValueError):
    """Verification metadata violates the Stage 4 authority contract."""


class EvidenceAuthority(str, Enum):
    SPEC_CONFIRMED = "spec_confirmed"
    USER_CONFIRMED = "user_confirmed"
    PROVISIONAL = "provisional"
    UNRESOLVED = "unresolved"


class VerificationStatus(str, Enum):
    MANUALLY_VERIFIED = "manually_verified"
    PROVISIONAL = "provisional"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class EvidenceDependency:
    """One materially relevant model fact and its manual-verification authority."""

    dependency_id: str
    authority: EvidenceAuthority
    source_id: str
    description: str = ""

    def __post_init__(self) -> None:
        if not self.dependency_id.strip():
            raise VerificationError("verification dependency requires dependency_id")
        if not self.source_id.strip():
            raise VerificationError("verification dependency requires source_id")

    @property
    def manually_verified(self) -> bool:
        return self.authority in {
            EvidenceAuthority.SPEC_CONFIRMED,
            EvidenceAuthority.USER_CONFIRMED,
        }


@dataclass(frozen=True)
class VerificationSummary:
    """Deduplicated authority ledger for one model/result boundary."""

    dependencies: tuple[EvidenceDependency, ...]

    def __post_init__(self) -> None:
        ids = [dependency.dependency_id for dependency in self.dependencies]
        if len(ids) != len(set(ids)):
            raise VerificationError("verification summary contains duplicate dependency ids")

    @property
    def status(self) -> VerificationStatus:
        if any(
            dependency.authority is EvidenceAuthority.UNRESOLVED
            for dependency in self.dependencies
        ):
            return VerificationStatus.UNRESOLVED
        if any(
            dependency.authority is EvidenceAuthority.PROVISIONAL
            for dependency in self.dependencies
        ):
            return VerificationStatus.PROVISIONAL
        return VerificationStatus.MANUALLY_VERIFIED

    @property
    def manually_verified(self) -> bool:
        return self.status is VerificationStatus.MANUALLY_VERIFIED

    @property
    def provisional_dependencies(self) -> tuple[EvidenceDependency, ...]:
        return tuple(
            dependency
            for dependency in self.dependencies
            if dependency.authority is EvidenceAuthority.PROVISIONAL
        )

    @property
    def unresolved_dependencies(self) -> tuple[EvidenceDependency, ...]:
        return tuple(
            dependency
            for dependency in self.dependencies
            if dependency.authority is EvidenceAuthority.UNRESOLVED
        )

    @property
    def manual_verification_queue(self) -> tuple[EvidenceDependency, ...]:
        """Only dependencies that still need checking; SPEC/user-confirmed facts disappear."""

        return self.unresolved_dependencies + self.provisional_dependencies

    @classmethod
    def combine(cls, *summaries: "VerificationSummary") -> "VerificationSummary":
        by_id: dict[str, EvidenceDependency] = {}
        for summary in summaries:
            for dependency in summary.dependencies:
                previous = by_id.get(dependency.dependency_id)
                if previous is not None and previous != dependency:
                    raise VerificationError(
                        "conflicting verification metadata for dependency "
                        f"{dependency.dependency_id!r}"
                    )
                by_id[dependency.dependency_id] = dependency
        return cls(tuple(by_id[key] for key in sorted(by_id)))


def authority_from_source_id(source_id: str) -> EvidenceAuthority:
    """Apply the governing default: only explicit SPEC/user provenance is confirmed."""

    normalized = source_id.strip().casefold()
    if not normalized:
        raise VerificationError("source_id must be nonblank")
    if normalized.startswith("spec.md") or normalized.startswith("spec:"):
        return EvidenceAuthority.SPEC_CONFIRMED
    if normalized.startswith("user:") or normalized.startswith("user_confirmed:"):
        return EvidenceAuthority.USER_CONFIRMED
    return EvidenceAuthority.PROVISIONAL


def dependency_from_source(
    dependency_id: str,
    source_id: str,
    *,
    description: str = "",
    authority: EvidenceAuthority | None = None,
) -> EvidenceDependency:
    return EvidenceDependency(
        dependency_id=dependency_id,
        authority=authority or authority_from_source_id(source_id),
        source_id=source_id,
        description=description,
    )


def audit_degree_scenario_verification(scenario: DegreeScenario) -> VerificationSummary:
    """Report manual-verification dependencies of the encoded degree contract.

    DegreeScenario historically stored source strings rather than a separate authority tag.
    Under SPEC v0.5, those strings default to PROVISIONAL unless they explicitly cite SPEC.
    This is deliberately conservative: words such as "verified" in an old source string do
    not upgrade authority.
    """

    dependencies: list[EvidenceDependency] = [
        dependency_from_source(
            f"degree::{scenario.scenario_id}::graduation_min_credits",
            "encoded DegreeScenario.graduation_min_credits",
            description=f"minimum graduation credits = {scenario.graduation_min_credits:g}",
        ),
        dependency_from_source(
            f"degree::{scenario.scenario_id}::qrm_major_credit_target",
            "encoded DegreeScenario.qrm_major_credit_target",
            description=f"QRM major-credit target = {scenario.qrm_major_credit_target:g}",
        ),
        dependency_from_source(
            f"degree::{scenario.scenario_id}::qrm_korean_credit_cap",
            scenario.qrm_korean_credit_cap.source,
            description=(
                "QRM Korean-taught major-credit cap = "
                f"{scenario.qrm_korean_credit_cap.max_courses} courses / "
                f"{scenario.qrm_korean_credit_cap.max_credits:g} credits"
            ),
        ),
        dependency_from_source(
            f"degree::{scenario.scenario_id}::exclusive_major_assignment",
            "encoded DegreeScenario.exclusive_major_assignment",
            description=(
                "one completion cannot be assigned simultaneously to both majors"
                if scenario.exclusive_major_assignment
                else "cross-major assignment is non-exclusive"
            ),
        ),
    ]

    for requirement in scenario.requirements:
        dependencies.append(
            dependency_from_source(
                f"degree::{scenario.scenario_id}::requirement::{requirement.requirement_id}",
                requirement.source,
                description=requirement.title,
            )
        )

    if scenario.second_major.status is SecondMajorStatus.UNRESOLVED:
        dependencies.append(
            EvidenceDependency(
                dependency_id=f"degree::{scenario.scenario_id}::second_major_structure",
                authority=EvidenceAuthority.UNRESOLVED,
                source_id="DegreeScenario.second_major=UNRESOLVED",
                description="second-major requirement structure is not yet resolved",
            )
        )

    return VerificationSummary(tuple(dependencies))


def audit_fall_input_verification(
    candidate_sets: FallCandidateSetEnumeration,
    *,
    registration_assessments: Mapping[str, RegistrationAssessment] | None = None,
) -> VerificationSummary:
    """Report authority dependencies at the Fall-universe/search-input boundary."""

    universe = candidate_sets.universe
    dependencies: list[EvidenceDependency] = [
        dependency_from_source(
            "fall::ordinary_credit_cap",
            candidate_sets.load_policy.source_id,
            description=(
                f"ordinary Fall credit cap = {candidate_sets.load_policy.ordinary_credit_cap:g}; "
                f"Chapel exempt = {candidate_sets.load_policy.chapel_exempt_from_ordinary_cap}"
            ),
        ),
        dependency_from_source(
            "fall::catalogue_snapshot",
            universe.source_name or "canonical Fall catalogue snapshot",
            description=(
                "canonical Fall physical-section catalogue and parsed source observations"
            ),
        ),
    ]

    for exclusion in universe.hard_exclusions:
        dependencies.append(
            dependency_from_source(
                f"fall::hard_exclusion::{exclusion.section_id}",
                exclusion.source_id,
                description=f"{exclusion.code}: {exclusion.reason}",
            )
        )

    for section_id, assessment in sorted((registration_assessments or {}).items()):
        if assessment.year_quota_status is YearQuotaGateStatus.NO_OBSERVATION:
            dependencies.append(
                EvidenceDependency(
                    dependency_id=f"fall::registration_gate::{section_id}",
                    authority=EvidenceAuthority.UNRESOLVED,
                    source_id="registration:NO_OBSERVATION",
                    description="no observed year-quota evidence for this section",
                )
            )
            continue
        source_id = assessment.quota_source_id or "registration:missing_source_id"
        dependencies.append(
            dependency_from_source(
                f"fall::registration_gate::{section_id}",
                source_id,
                description=f"year-quota gate status = {assessment.year_quota_status.value}",
            )
        )

    return VerificationSummary(tuple(dependencies))


def can_claim_user_verified_optimum(
    *,
    model_optimum_proven: bool,
    verification: VerificationSummary,
) -> bool:
    """A proven model optimum becomes a user-verified optimum only with verified inputs."""

    return model_optimum_proven and verification.manually_verified


def compact_manual_verification_queue(
    dependencies: Iterable[EvidenceDependency],
) -> tuple[EvidenceDependency, ...]:
    """Stable helper for later finalist-driven verification queues."""

    unresolved = sorted(
        (
            dependency
            for dependency in dependencies
            if dependency.authority is EvidenceAuthority.UNRESOLVED
        ),
        key=lambda dependency: dependency.dependency_id,
    )
    provisional = sorted(
        (
            dependency
            for dependency in dependencies
            if dependency.authority is EvidenceAuthority.PROVISIONAL
        ),
        key=lambda dependency: dependency.dependency_id,
    )
    return tuple(unresolved + provisional)
