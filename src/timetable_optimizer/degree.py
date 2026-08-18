"""Canonical degree/recognition state for the Stage 4 rebuild.

This layer deliberately knows nothing about timetable geometry, travel, professor quality,
registration risk, or future catalogue prediction. It represents unique earned graduation
credits plus scenario-specific institutional requirements.

Qualification of arbitrary catalogue sections for broad buckets such as QRM ME, Language,
SciRD, or UIC Seminar lives in :mod:`timetable_optimizer.recognition`. This module defines
the requirement graph and protects state-transition invariants; it does not infer missing
recognition.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias


class DegreeRuleError(ValueError):
    """A proposed degree-state transition violates the frozen degree contract."""


class MajorMode(str, Enum):
    SINGLE = "single"
    DOUBLE = "double"


class SecondMajorStatus(str, Enum):
    NONE = "none"
    UNRESOLVED = "unresolved"
    RESOLVED = "resolved"


@dataclass(frozen=True)
class SpecificCourseRequirement:
    requirement_id: str
    title: str
    course_codes: tuple[str, ...]
    credits: float
    counts_toward_qrm_major: bool = False
    source: str = "2026 curriculum"


@dataclass(frozen=True)
class AnyOfRequirement:
    requirement_id: str
    title: str
    course_codes: tuple[str, ...]
    credits: float
    counts_toward_qrm_major: bool = False
    source: str = "2026 curriculum"


@dataclass(frozen=True)
class CategoryCountRequirement:
    requirement_id: str
    title: str
    categories: tuple[str, ...]
    required_count: int
    credits_per_category: float
    source: str = "2026 curriculum"


@dataclass(frozen=True)
class CreditBucketRequirement:
    requirement_id: str
    title: str
    target_credits: float
    qualification_rule_id: str
    counts_toward_qrm_major: bool = False
    waiver_allowed: bool = False
    source: str = "2026 curriculum"


@dataclass(frozen=True)
class ChapelRequirement:
    requirement_id: str
    title: str
    passes_required: int
    credits_per_pass: float
    # The ordinary graduation tables establish four Chapel passes but do not, in the
    # sources migrated in B.1, establish the separate offline-pass threshold. Preserve
    # that threshold as unresolved rather than inventing a number here.
    offline_passes_required: int | None = None
    source: str = "2026 curriculum"


Requirement: TypeAlias = (
    SpecificCourseRequirement
    | AnyOfRequirement
    | CategoryCountRequirement
    | CreditBucketRequirement
    | ChapelRequirement
)


@dataclass(frozen=True)
class KoreanMajorCreditCap:
    max_courses: int
    max_credits: float
    source: str = "2026 QRM curriculum"


@dataclass(frozen=True)
class SecondMajorSpec:
    status: SecondMajorStatus
    name: str | None = None
    requirements: tuple[Requirement, ...] = ()


@dataclass(frozen=True)
class DegreeScenario:
    scenario_id: str
    graduation_min_credits: float
    major_mode: MajorMode
    qrm_major_credit_target: float
    requirements: tuple[Requirement, ...]
    qrm_korean_credit_cap: KoreanMajorCreditCap
    exclusive_major_assignment: bool
    second_major: SecondMajorSpec

    def requirement(self, requirement_id: str) -> Requirement:
        hits = [req for req in self.requirements if req.requirement_id == requirement_id]
        if len(hits) != 1:
            raise DegreeRuleError(
                f"expected exactly one requirement {requirement_id!r}, found {len(hits)}"
            )
        return hits[0]


@dataclass(frozen=True)
class Completion:
    completion_id: str
    course_code: str | None
    credits: float
    label: str = ""


@dataclass(frozen=True)
class ChapelProgress:
    passes_completed: int = 0
    offline_passes_min: int = 0
    offline_passes_max: int = 0


@dataclass(frozen=True)
class RecognitionEffect:
    completion: Completion
    satisfy: tuple[str, ...] = ()
    category_claims: tuple[tuple[str, str], ...] = ()
    bucket_credit_claims: tuple[tuple[str, float], ...] = ()
    chapel_pass: bool = False
    chapel_offline: bool | None = None
    # Only credits from Korean-taught School of Economics / Applied Statistics courses
    # that are actually assigned to QRM major credit belong here. This is a recognition
    # cap, not a prohibition on taking the course or earning graduation credit.
    qrm_korean_major_credits: float = 0.0

    @classmethod
    def course(
        cls,
        *,
        completion_id: str,
        course_code: str,
        credits: float,
        satisfy: tuple[str, ...] = (),
        category_claims: tuple[tuple[str, str], ...] = (),
        bucket_credit_claims: tuple[tuple[str, float], ...] = (),
        qrm_korean_major_credits: float = 0.0,
        label: str = "",
    ) -> "RecognitionEffect":
        return cls(
            completion=Completion(completion_id, course_code, credits, label),
            satisfy=satisfy,
            category_claims=category_claims,
            bucket_credit_claims=bucket_credit_claims,
            qrm_korean_major_credits=qrm_korean_major_credits,
        )

    @classmethod
    def chapel(
        cls,
        *,
        completion_id: str,
        credits: float = 0.5,
        course_code: str | None = None,
        offline: bool | None = None,
        label: str = "Chapel",
    ) -> "RecognitionEffect":
        return cls(
            completion=Completion(completion_id, course_code, credits, label),
            chapel_pass=True,
            chapel_offline=offline,
        )


@dataclass(frozen=True)
class DegreeState:
    completions: tuple[Completion, ...] = ()
    explicitly_satisfied: frozenset[str] = frozenset()
    category_claims: frozenset[tuple[str, str]] = frozenset()
    bucket_credit_claims: tuple[tuple[str, float], ...] = ()
    chapel: ChapelProgress = ChapelProgress()
    qrm_korean_major_claims: tuple[tuple[str, float], ...] = ()

    @property
    def earned_credits(self) -> float:
        return sum(completion.credits for completion in self.completions)

    @property
    def completion_ids(self) -> frozenset[str]:
        return frozenset(completion.completion_id for completion in self.completions)

    @property
    def completed_course_codes(self) -> tuple[str, ...]:
        return tuple(
            completion.course_code
            for completion in self.completions
            if completion.course_code is not None
        )

    @property
    def qrm_korean_major_credits(self) -> float:
        return sum(credits for _, credits in self.qrm_korean_major_claims)

    @property
    def qrm_korean_major_courses(self) -> int:
        return len(self.qrm_korean_major_claims)

    def graduation_credit_deficit(self, scenario: DegreeScenario) -> float:
        return max(0.0, scenario.graduation_min_credits - self.earned_credits)

    def categories_for(self, requirement_id: str) -> frozenset[str]:
        return frozenset(
            category
            for req_id, category in self.category_claims
            if req_id == requirement_id
        )

    def bucket_credits_for(self, requirement_id: str) -> float:
        return sum(
            credits
            for req_id, credits in self.bucket_credit_claims
            if req_id == requirement_id
        )

    def is_requirement_satisfied(self, scenario: DegreeScenario, requirement_id: str) -> bool:
        if requirement_id in self.explicitly_satisfied:
            return True

        requirement = scenario.requirement(requirement_id)
        if isinstance(requirement, CategoryCountRequirement):
            return len(self.categories_for(requirement_id)) >= requirement.required_count
        if isinstance(requirement, CreditBucketRequirement):
            return self.bucket_credits_for(requirement_id) >= requirement.target_credits
        if isinstance(requirement, ChapelRequirement):
            if self.chapel.passes_completed < requirement.passes_required:
                return False
            if requirement.offline_passes_required is None:
                # Total passes are known, but the complete Chapel rule is not yet known.
                return False
            return self.chapel.offline_passes_min >= requirement.offline_passes_required
        return False

    def is_degree_complete(self, scenario: DegreeScenario) -> bool | None:
        if scenario.second_major.status is SecondMajorStatus.UNRESOLVED:
            return None
        if self.earned_credits < scenario.graduation_min_credits:
            return False
        return all(
            self.is_requirement_satisfied(scenario, requirement.requirement_id)
            for requirement in scenario.requirements
        )


def _validate_requirement_claim(scenario: DegreeScenario, requirement_id: str) -> Requirement:
    return scenario.requirement(requirement_id)


def _effect_claims_qrm_major(scenario: DegreeScenario, effect: RecognitionEffect) -> bool:
    for requirement_id in effect.satisfy:
        requirement = scenario.requirement(requirement_id)
        if getattr(requirement, "counts_toward_qrm_major", False):
            return True
    for requirement_id, _ in effect.bucket_credit_claims:
        requirement = scenario.requirement(requirement_id)
        if getattr(requirement, "counts_toward_qrm_major", False):
            return True
    return False


def apply_recognition(
    state: DegreeState,
    scenario: DegreeScenario,
    effect: RecognitionEffect,
) -> DegreeState:
    """Apply one already-validated recognition effect immutably.

    The recognition layer is responsible for producing evidence-backed effects from
    catalogue data. This function still protects the state from malformed effects: unique
    completion credit, requirement-type discipline, category/bucket identities, Korean QRM
    recognition caps, and bounded Chapel uncertainty.
    """

    completion = effect.completion
    if not completion.completion_id:
        raise DegreeRuleError("completion_id must be non-empty")
    if completion.completion_id in state.completion_ids:
        raise DegreeRuleError(f"completion already applied: {completion.completion_id}")
    if completion.credits < 0:
        raise DegreeRuleError("graduation credits cannot be negative")

    for requirement_id in effect.satisfy:
        requirement = _validate_requirement_claim(scenario, requirement_id)
        if not isinstance(requirement, (SpecificCourseRequirement, AnyOfRequirement)):
            raise DegreeRuleError(
                f"{requirement_id} cannot be satisfied by a boolean shortcut; "
                "use its structured recognition claim"
            )

    new_categories = set(state.category_claims)
    for requirement_id, category in effect.category_claims:
        requirement = _validate_requirement_claim(scenario, requirement_id)
        if not isinstance(requirement, CategoryCountRequirement):
            raise DegreeRuleError(f"{requirement_id} is not a category-count requirement")
        if category not in requirement.categories:
            raise DegreeRuleError(f"invalid category {category!r} for {requirement_id}")
        new_categories.add((requirement_id, category))

    new_bucket_claims = list(state.bucket_credit_claims)
    for requirement_id, credits in effect.bucket_credit_claims:
        requirement = _validate_requirement_claim(scenario, requirement_id)
        if not isinstance(requirement, CreditBucketRequirement):
            raise DegreeRuleError(f"{requirement_id} is not a credit-bucket requirement")
        if credits < 0:
            raise DegreeRuleError("bucket recognition credits cannot be negative")
        if credits > completion.credits:
            raise DegreeRuleError(
                f"bucket claim {credits} exceeds completion credits {completion.credits}"
            )
        new_bucket_claims.append((requirement_id, float(credits)))

    korean_claims = list(state.qrm_korean_major_claims)
    korean_credits = float(effect.qrm_korean_major_credits)
    if korean_credits < 0:
        raise DegreeRuleError("Korean QRM major recognition credits cannot be negative")
    if korean_credits > completion.credits:
        raise DegreeRuleError("Korean QRM major recognition exceeds completion credits")
    if korean_credits:
        if not _effect_claims_qrm_major(scenario, effect):
            raise DegreeRuleError(
                "Korean QRM cap usage requires an actual QRM-major recognition claim"
            )
        cap = scenario.qrm_korean_credit_cap
        if state.qrm_korean_major_courses + 1 > cap.max_courses:
            raise DegreeRuleError("QRM Korean-course major-credit course cap exceeded")
        if state.qrm_korean_major_credits + korean_credits > cap.max_credits:
            raise DegreeRuleError("QRM Korean-course major-credit credit cap exceeded")
        korean_claims.append((completion.completion_id, korean_credits))

    chapel = state.chapel
    if effect.chapel_pass:
        minimum = chapel.offline_passes_min
        maximum = chapel.offline_passes_max
        if effect.chapel_offline is True:
            minimum += 1
            maximum += 1
        elif effect.chapel_offline is None:
            maximum += 1
        chapel = ChapelProgress(
            passes_completed=chapel.passes_completed + 1,
            offline_passes_min=minimum,
            offline_passes_max=maximum,
        )

    return DegreeState(
        completions=state.completions + (completion,),
        explicitly_satisfied=state.explicitly_satisfied | frozenset(effect.satisfy),
        category_claims=frozenset(new_categories),
        bucket_credit_claims=tuple(new_bucket_claims),
        chapel=chapel,
        qrm_korean_major_claims=tuple(korean_claims),
    )


def _common_requirements() -> tuple[Requirement, ...]:
    return (
        ChapelRequirement("cc_chapel", "Chapel", passes_required=4, credits_per_pass=0.5),
        SpecificCourseRequirement(
            "cc_christianity",
            "Understanding Christianity",
            ("YCA1101", "YCA1102", "YCA1103"),
            3.0,
        ),
        SpecificCourseRequirement(
            "cc_fwis", "Freshman Writing Intensive Seminar", ("UIC1101",), 3.0
        ),
        CategoryCountRequirement(
            "cc_lhp",
            "CC Literature-History-Philosophy Series",
            ("literature", "history", "philosophy"),
            required_count=2,
            credits_per_category=3.0,
        ),
        CreditBucketRequirement(
            "cc_language",
            "Language",
            target_credits=3.0,
            qualification_rule_id="uic_language_2026",
            waiver_allowed=True,
        ),
        CreditBucketRequirement(
            "cc_scird",
            "Science Literacy or Research Design & Quantitative Methods",
            target_credits=3.0,
            qualification_rule_id="uic_science_literacy_or_rdqm_2026",
        ),
        SpecificCourseRequirement(
            "cc_critical_reasoning", "Critical Reasoning", ("UIC2101",), 3.0
        ),
        CreditBucketRequirement(
            "cc_uic_seminar",
            "UIC Seminars",
            target_credits=6.0,
            qualification_rule_id="uic_seminar_2026",
        ),
        SpecificCourseRequirement(
            "cc_western_civ", "Western Civilization", ("UIC1561",), 3.0
        ),
        SpecificCourseRequirement(
            "cc_eastern_civ", "Eastern Civilization", ("UIC1581",), 3.0
        ),
        SpecificCourseRequirement("cc_rc101", "Yonsei RC101", ("UCR1007",), 1.0),
    )


def _qrm_requirements(*, me_credits: float) -> tuple[Requirement, ...]:
    return (
        SpecificCourseRequirement(
            "qrm_intro_statistics",
            "Introduction to Statistics",
            ("STA1001",),
            3.0,
            counts_toward_qrm_major=False,
        ),
        SpecificCourseRequirement(
            "qrm_mr_intro",
            "Introduction to Quantitative Risk Management",
            ("QRM1001",),
            3.0,
            counts_toward_qrm_major=True,
        ),
        SpecificCourseRequirement(
            "qrm_mr_micro",
            "Microeconomics",
            ("ECO2102",),
            3.0,
            counts_toward_qrm_major=True,
        ),
        SpecificCourseRequirement(
            "qrm_mr_macro",
            "Macroeconomics",
            ("ECO2101",),
            3.0,
            counts_toward_qrm_major=True,
        ),
        SpecificCourseRequirement(
            "qrm_mr_math_econ",
            "Mathematics for Economics I",
            ("ECO1101",),
            3.0,
            counts_toward_qrm_major=True,
        ),
        AnyOfRequirement(
            "qrm_mr_mathstat_or_regression",
            "Mathematical Statistics or Regression Analysis",
            ("QRM3005", "QRM3004"),
            3.0,
            counts_toward_qrm_major=True,
        ),
        SpecificCourseRequirement(
            "qrm_mr_financial_engineering",
            "Principles of Financial Engineering",
            ("QRM3003",),
            3.0,
            counts_toward_qrm_major=True,
        ),
        CreditBucketRequirement(
            "qrm_me",
            "QRM Major Electives",
            target_credits=me_credits,
            qualification_rule_id="qrm_major_elective_2026",
            counts_toward_qrm_major=True,
        ),
    )


def qrm_single_major_2026() -> DegreeScenario:
    """2026 HASS/QRM first-major scenario with no second major."""

    return DegreeScenario(
        scenario_id="qrm-single-2026",
        graduation_min_credits=126.0,
        major_mode=MajorMode.SINGLE,
        qrm_major_credit_target=42.0,
        requirements=_common_requirements() + _qrm_requirements(me_credits=24.0),
        qrm_korean_credit_cap=KoreanMajorCreditCap(4, 12.0),
        exclusive_major_assignment=True,
        second_major=SecondMajorSpec(SecondMajorStatus.NONE),
    )


def qrm_double_major_shell_2026() -> DegreeScenario:
    """QRM first-major rules after choosing a double-major path, identity unresolved.

    This intentionally contains *no* anonymous second-major courses. Concrete second-major
    scenarios will extend this shell only after their actual institutional rules are built.
    """

    return DegreeScenario(
        scenario_id="qrm-double-shell-2026",
        graduation_min_credits=126.0,
        major_mode=MajorMode.DOUBLE,
        qrm_major_credit_target=36.0,
        requirements=_common_requirements() + _qrm_requirements(me_credits=18.0),
        qrm_korean_credit_cap=KoreanMajorCreditCap(4, 12.0),
        exclusive_major_assignment=True,
        second_major=SecondMajorSpec(SecondMajorStatus.UNRESOLVED),
    )


def spring_2026_initial_state(scenario: DegreeScenario) -> DegreeState:
    """Build the user's completed first-semester state from concrete known completions.

    Spring 2026 consisted of six ordinary 3-credit courses, RC101 (1 credit), and one
    0.5-credit Chapel pass, for 19.5 unique graduation credits. The Chapel section/code and
    offline/online status have not yet been established in the migrated evidence, so that
    completion intentionally keeps ``course_code=None`` and offline status unknown.
    """

    effects = (
        RecognitionEffect.course(
            completion_id="2026S-UIC1101",
            course_code="UIC1101",
            credits=3.0,
            satisfy=("cc_fwis",),
            label="Freshman Writing Intensive Seminar",
        ),
        RecognitionEffect.course(
            completion_id="2026S-YCA1101",
            course_code="YCA1101",
            credits=3.0,
            satisfy=("cc_christianity",),
            label="Christianity and World Culture",
        ),
        RecognitionEffect.course(
            completion_id="2026S-UIC1581",
            course_code="UIC1581",
            credits=3.0,
            satisfy=("cc_eastern_civ",),
            label="Eastern Civilization",
        ),
        RecognitionEffect.course(
            completion_id="2026S-UIC2101",
            course_code="UIC2101",
            credits=3.0,
            satisfy=("cc_critical_reasoning",),
            label="Critical Reasoning",
        ),
        RecognitionEffect.course(
            completion_id="2026S-UIC1901",
            course_code="UIC1901",
            credits=3.0,
            category_claims=(("cc_lhp", "philosophy"),),
            label="World Philosophy",
        ),
        RecognitionEffect.course(
            completion_id="2026S-STA1001",
            course_code="STA1001",
            credits=3.0,
            satisfy=("qrm_intro_statistics",),
            label="Introduction to Statistics",
        ),
        RecognitionEffect.course(
            completion_id="2026S-UCR1007",
            course_code="UCR1007",
            credits=1.0,
            satisfy=("cc_rc101",),
            label="Yonsei RC101",
        ),
        RecognitionEffect.chapel(
            completion_id="2026S-CHAPEL",
            credits=0.5,
            course_code=None,
            offline=None,
            label="Spring 2026 Chapel (section code/status not yet recorded)",
        ),
    )

    state = DegreeState()
    for effect in effects:
        state = apply_recognition(state, scenario, effect)
    return state
