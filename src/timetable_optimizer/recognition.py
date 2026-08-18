"""Evidence-backed course recognition for the Stage 4 rebuild.

This module is the single authority that translates canonical catalogue facts plus explicit
recognition evidence into valid :class:`RecognitionEffect` objects for a degree scenario.
It does not schedule sections, score preferences, infer professor quality, or predict future
offerings.

The important epistemic distinction is retained explicitly:

    QUALIFIED      evidence establishes that this section may satisfy the requirement
    NOT_QUALIFIED  evidence establishes that it may not
    UNRESOLVED     available evidence is insufficient to decide safely

A section may still earn ordinary graduation credit even when one or more requirement
recognitions are unresolved or unavailable.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .catalog import ListingObservation, ListingStatus, SourceListingView
from .degree import (
    AnyOfRequirement,
    CategoryCountRequirement,
    ChapelRequirement,
    CreditBucketRequirement,
    DegreeScenario,
    DegreeState,
    RecognitionEffect,
    SpecificCourseRequirement,
)
from .sections import Section


class QualificationStatus(str, Enum):
    QUALIFIED = "qualified"
    NOT_QUALIFIED = "not_qualified"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class QualificationDecision:
    requirement_id: str
    status: QualificationStatus
    reason: str


@dataclass(frozen=True)
class RecognitionIssue:
    code: str
    message: str
    requirement_id: str = ""


@dataclass(frozen=True)
class RecognitionOption:
    option_id: str
    effect: RecognitionEffect
    reason: str


@dataclass(frozen=True)
class RecognitionAssessment:
    section_id: str
    decisions: tuple[QualificationDecision, ...]
    options: tuple[RecognitionOption, ...]
    issues: tuple[RecognitionIssue, ...] = ()


@dataclass(frozen=True)
class CourseRecognitionEvidence:
    """Explicit evidence not yet encoded as a canonical physical/listing fact.

    ``foreign_language_course`` is for the non-UIC language route.  ``korean_taught`` is
    needed for the QRM 4-course/12-credit Korean-course recognition cap.  Neither defaults
    to False: absence of evidence remains unknown.
    """

    foreign_language_course: bool | None = None
    korean_taught: bool | None = None
    source: str = ""


# 2026 Common Curriculum evidence -------------------------------------------------

UIC_LANGUAGE_CODES = frozenset(
    {
        "UIC1804",
        "UIC1805",
        "UIC1806",
        "UIC1808",
        "UIC1809",
        "UIC1810",
        "UIC2302",
        "UIC2306",
        "UIC2307",
        "UIC2310",
        "UIC2311",
        "UIC2312",
        "UIC3201",
        "UIC3202",
        "UIC3203",
        "UIC3204",
        "UIC3205",
        "UIC3206",
        "UIC3207",
    }
)

LANGUAGE_EXCLUDED_CODES = frozenset({"YCF1652"})

SCIRD_KNOWN_CODES = frozenset(
    {
        "UIC2151",
        "UIC1541",
        "UIC1918",
        "UIC1502",
        "UIC1920",
        "UIC1751",
        "MAT1001",
        "PHY1001",
        "CHE1001",
    }
)

LHP_LITERATURE_CODES = frozenset(
    {
        "UIC1200",
        "UIC1201",
        "UIC1251",
        "UIC1301",
        "UIC1351",
        "UIC1401",
        "UIC1451",
        "UIC1915",
    }
)
LHP_HISTORY_CODES = frozenset({"UIC1501", "UIC1551", "UIC1653"})
LHP_PHILOSOPHY_CODES = frozenset({"UIC1901"})

CHAPEL_2026_CODES = frozenset({"YCA1005", "YCA1006", "YCA1007", "YCA1008"})


# 2026 QRM curriculum: coded ME entries.  Curriculum rows whose code is shown as "-"
# cannot be recognized by title guessing here; a concrete QRM program-listing observation
# may establish those sections instead.
QRM_ME_2026_CODES = frozenset(
    {
        "ECO1103",
        "ECO1104",
        "QRM2001",
        "QRM2002",
        "QRM2004",
        "QRM2100",
        "QRM2101",
        "STA2102",
        "STA2104",
        "STA2105",
        "QRM3001",
        "QRM3002",
        "STP3007",
        "ECO3104",
        "ECO3127",
        "ECO3130",
        "ECO3134",
        "QRM4001",
        "QRM4807",
        "STA4103",
        "ECO4115",
        "ECO4862",
        "ECO4865",
    }
)


def _decision(
    requirement_id: str,
    status: QualificationStatus,
    reason: str,
) -> QualificationDecision:
    return QualificationDecision(requirement_id, status, reason)


def _qrm_department_status(source_views: tuple[SourceListingView, ...]) -> bool | None:
    """Return True/False/None for whether source views establish QRM department offering."""

    departments = [view.department.strip() for view in source_views if view.department.strip()]
    if not departments:
        return None
    qrm_tokens = (
        "quantitative risk management",
        "department of quantitative risk management",
        "qrm",
        "계량위험",
    )
    if any(any(token in dept.lower() for token in qrm_tokens) for dept in departments):
        return True
    return False


def _is_econ_or_applied_statistics(source_views: tuple[SourceListingView, ...]) -> bool:
    tokens = (
        "school of economics",
        "department of economics",
        "economics",
        "applied statistics",
        "경제학",
        "경제학부",
        "응용통계",
    )
    for view in source_views:
        department = view.department.strip().lower()
        if department and any(token in department for token in tokens):
            return True
    return False


def _lhp_category(course_code: str) -> str | None:
    if course_code in LHP_LITERATURE_CODES:
        return "literature"
    if course_code in LHP_HISTORY_CODES:
        return "history"
    if course_code in LHP_PHILOSOPHY_CODES:
        return "philosophy"
    return None


def _is_uic_seminar(course_code: str) -> bool:
    return (
        len(course_code) == 7
        and course_code.startswith("UIC")
        and course_code[3:].isdigit()
        and course_code[3:5] in {"35", "36"}
    )


def _qrm_me_status(
    section: Section,
    program_listings: tuple[ListingObservation, ...],
) -> QualificationDecision:
    if section.course_code in QRM_ME_2026_CODES:
        return _decision(
            "qrm_me",
            QualificationStatus.QUALIFIED,
            "course code is explicitly listed as QRM ME in the 2026 curriculum",
        )

    qrm_listings = [listing for listing in program_listings if listing.program.upper() == "QRM"]
    if any(
        listing.status is ListingStatus.OK and (listing.listed_category or "").upper() == "ME"
        for listing in qrm_listings
    ):
        return _decision(
            "qrm_me",
            QualificationStatus.QUALIFIED,
            "QRM program-listing evidence classifies this physical section as ME",
        )
    if any(listing.status is ListingStatus.UNRESOLVED for listing in qrm_listings):
        return _decision(
            "qrm_me",
            QualificationStatus.UNRESOLVED,
            "QRM program-listing evidence exists but is unresolved",
        )
    if qrm_listings:
        return _decision(
            "qrm_me",
            QualificationStatus.NOT_QUALIFIED,
            "QRM program-listing evidence does not classify this section as ME",
        )
    return _decision(
        "qrm_me",
        QualificationStatus.NOT_QUALIFIED,
        "course is neither a coded 2026 QRM ME nor backed by a QRM ME listing observation",
    )


def _language_status(
    section: Section,
    evidence: CourseRecognitionEvidence,
) -> QualificationDecision:
    code = section.course_code
    if code in UIC_LANGUAGE_CODES:
        return _decision(
            "cc_language",
            QualificationStatus.QUALIFIED,
            "course code is on the official 2026 UIC Language course list",
        )
    if code in LANGUAGE_EXCLUDED_CODES or code.startswith("YCC1"):
        return _decision(
            "cc_language",
            QualificationStatus.NOT_QUALIFIED,
            "course code is explicitly excluded from the language requirement",
        )
    if evidence.foreign_language_course is True:
        return _decision(
            "cc_language",
            QualificationStatus.QUALIFIED,
            f"explicit non-UIC foreign-language evidence{': ' + evidence.source if evidence.source else ''}",
        )
    if evidence.foreign_language_course is False:
        return _decision(
            "cc_language",
            QualificationStatus.NOT_QUALIFIED,
            f"explicit evidence says this is not a qualifying foreign-language course{': ' + evidence.source if evidence.source else ''}",
        )
    # The current project specifically contains YCF language candidates.  Prefix alone is
    # not enough to certify them, but it is enough to identify the unresolved evidence path.
    if code.startswith("YCF"):
        return _decision(
            "cc_language",
            QualificationStatus.UNRESOLVED,
            "possible non-UIC foreign-language route requires course-level evidence; prefix is not proof",
        )
    return _decision(
        "cc_language",
        QualificationStatus.NOT_QUALIFIED,
        "no evidence places this course on either documented language-recognition route",
    )


def _scird_status(section: Section) -> QualificationDecision:
    if section.course_code in SCIRD_KNOWN_CODES:
        return _decision(
            "cc_scird",
            QualificationStatus.QUALIFIED,
            "course code is on the official Science Literacy/RDQM qualifying list",
        )
    return _decision(
        "cc_scird",
        QualificationStatus.UNRESOLVED,
        "official list is explicitly open-ended ('other courses to be determined later')",
    )


def _specific_or_anyof_status(
    section: Section,
    requirement: SpecificCourseRequirement | AnyOfRequirement,
    source_views: tuple[SourceListingView, ...],
) -> QualificationDecision:
    if section.course_code not in requirement.course_codes:
        return _decision(
            requirement.requirement_id,
            QualificationStatus.NOT_QUALIFIED,
            "course code does not match this requirement",
        )

    if requirement.requirement_id == "qrm_mr_mathstat_or_regression":
        dept_status = _qrm_department_status(source_views)
        if dept_status is True:
            return _decision(
                requirement.requirement_id,
                QualificationStatus.QUALIFIED,
                "course code matches and source listing establishes QRM department offering",
            )
        if dept_status is False:
            return _decision(
                requirement.requirement_id,
                QualificationStatus.NOT_QUALIFIED,
                "2026 rule recognizes Mathematical Statistics/Regression only when offered by QRM",
            )
        return _decision(
            requirement.requirement_id,
            QualificationStatus.UNRESOLVED,
            "course code matches but offering-department evidence is missing",
        )

    return _decision(
        requirement.requirement_id,
        QualificationStatus.QUALIFIED,
        "course code exactly matches the degree requirement",
    )


def _subject_to_korean_qrm_cap(
    source_views: tuple[SourceListingView, ...],
    evidence: CourseRecognitionEvidence,
) -> bool | None:
    if not _is_econ_or_applied_statistics(source_views):
        return False
    if evidence.korean_taught is True:
        return True
    if evidence.korean_taught is False:
        return False
    return None


def _qrm_major_requirement_ids(scenario: DegreeScenario) -> frozenset[str]:
    return frozenset(
        requirement.requirement_id
        for requirement in scenario.requirements
        if getattr(requirement, "counts_toward_qrm_major", False)
    )


def recognize_section(
    section: Section,
    scenario: DegreeScenario,
    state: DegreeState,
    *,
    source_views: tuple[SourceListingView, ...] = (),
    program_listings: tuple[ListingObservation, ...] = (),
    evidence: CourseRecognitionEvidence = CourseRecognitionEvidence(),
) -> RecognitionAssessment:
    """Return evidence-backed degree-recognition choices for one canonical section."""

    decisions: list[QualificationDecision] = []
    issues: list[RecognitionIssue] = []

    # Requirements with exact course-code semantics.
    for requirement in scenario.requirements:
        if isinstance(requirement, (SpecificCourseRequirement, AnyOfRequirement)):
            decisions.append(
                _specific_or_anyof_status(section, requirement, source_views)
            )

    # L-H-P category recognition.
    if any(isinstance(req, CategoryCountRequirement) and req.requirement_id == "cc_lhp" for req in scenario.requirements):
        category = _lhp_category(section.course_code)
        if category is None:
            decisions.append(
                _decision(
                    "cc_lhp",
                    QualificationStatus.NOT_QUALIFIED,
                    "course code is not on the documented 2026 World Literature/History/Philosophy list",
                )
            )
        else:
            decisions.append(
                _decision(
                    "cc_lhp",
                    QualificationStatus.QUALIFIED,
                    f"course is documented in the {category} L-H-P category",
                )
            )

    # Broad credit-bucket rules.
    decisions.append(_language_status(section, evidence))
    decisions.append(_scird_status(section))
    decisions.append(
        _decision(
            "cc_uic_seminar",
            QualificationStatus.QUALIFIED if _is_uic_seminar(section.course_code) else QualificationStatus.NOT_QUALIFIED,
            "2026 curriculum defines UIC35xx/UIC36xx as UIC Seminars"
            if _is_uic_seminar(section.course_code)
            else "course code is outside the documented UIC35xx/UIC36xx seminar ranges",
        )
    )
    decisions.append(_qrm_me_status(section, program_listings))

    # Chapel is a nonstandard pass requirement, not an ordinary bucket.
    decisions.append(
        _decision(
            "cc_chapel",
            QualificationStatus.QUALIFIED if section.course_code in CHAPEL_2026_CODES else QualificationStatus.NOT_QUALIFIED,
            "course code is a 2026 Chapel code"
            if section.course_code in CHAPEL_2026_CODES
            else "course code is not a documented 2026 Chapel code",
        )
    )

    # Apply the Korean-taught Economics/Applied Statistics cap to QRM-major recognitions.
    qrm_ids = _qrm_major_requirement_ids(scenario)
    cap_subject = _subject_to_korean_qrm_cap(source_views, evidence)
    adjusted: list[QualificationDecision] = []
    korean_qrm_credits = 0.0
    for decision in decisions:
        if decision.requirement_id not in qrm_ids or decision.status is not QualificationStatus.QUALIFIED:
            adjusted.append(decision)
            continue

        if cap_subject is None:
            adjusted.append(
                _decision(
                    decision.requirement_id,
                    QualificationStatus.UNRESOLVED,
                    "Economics/Applied Statistics source is known, but Korean-vs-non-Korean lecture evidence is missing",
                )
            )
            issues.append(
                RecognitionIssue(
                    "qrm_korean_language_unresolved",
                    "QRM major recognition depends on whether this Economics/Applied Statistics section is taught in Korean",
                    decision.requirement_id,
                )
            )
            continue

        if cap_subject:
            credits = section.credits
            if credits is None:
                adjusted.append(decision)
                continue
            cap = scenario.qrm_korean_credit_cap
            if (
                state.qrm_korean_major_courses + 1 > cap.max_courses
                or state.qrm_korean_major_credits + credits > cap.max_credits
            ):
                adjusted.append(
                    _decision(
                        decision.requirement_id,
                        QualificationStatus.NOT_QUALIFIED,
                        "QRM Korean-course major-credit recognition cap is exhausted",
                    )
                )
                issues.append(
                    RecognitionIssue(
                        "qrm_korean_cap_exhausted",
                        "course may still be taken and earn graduation credit, but cannot receive additional QRM major-credit recognition under the 4-course/12-credit cap",
                        decision.requirement_id,
                    )
                )
                continue
            korean_qrm_credits = credits

        adjusted.append(decision)
    decisions = adjusted

    if section.credits is None:
        issues.append(
            RecognitionIssue(
                "missing_credits",
                "section credit value is unknown, so no degree-state transition is invented",
            )
        )
        return RecognitionAssessment(
            section_id=section.section_id,
            decisions=tuple(decisions),
            options=(),
            issues=tuple(issues),
        )

    qualified = {
        decision.requirement_id
        for decision in decisions
        if decision.status is QualificationStatus.QUALIFIED
    }

    if "cc_chapel" in qualified:
        option = RecognitionOption(
            option_id=f"{section.section_id}:chapel",
            effect=RecognitionEffect.chapel(
                completion_id=section.section_id,
                course_code=section.course_code,
                credits=section.credits,
                offline=None,
                label=section.name,
            ),
            reason="documented Chapel completion; offline/online status remains unresolved",
        )
        return RecognitionAssessment(
            section_id=section.section_id,
            decisions=tuple(decisions),
            options=(option,),
            issues=tuple(issues),
        )

    satisfy: list[str] = []
    category_claims: list[tuple[str, str]] = []
    bucket_claims: list[tuple[str, float]] = []

    for requirement in scenario.requirements:
        rid = requirement.requirement_id
        if rid not in qualified:
            continue
        if isinstance(requirement, (SpecificCourseRequirement, AnyOfRequirement)):
            satisfy.append(rid)
        elif isinstance(requirement, CategoryCountRequirement):
            if rid == "cc_lhp":
                category = _lhp_category(section.course_code)
                if category is not None:
                    category_claims.append((rid, category))
        elif isinstance(requirement, CreditBucketRequirement):
            bucket_claims.append((rid, section.credits))

    # A non-requirement elective still has a valid graduation-credit-only transition.
    effect = RecognitionEffect.course(
        completion_id=section.section_id,
        course_code=section.course_code,
        credits=section.credits,
        satisfy=tuple(satisfy),
        category_claims=tuple(category_claims),
        bucket_credit_claims=tuple(bucket_claims),
        qrm_korean_major_credits=korean_qrm_credits,
        label=section.name,
    )
    option = RecognitionOption(
        option_id=f"{section.section_id}:default",
        effect=effect,
        reason=(
            "apply all currently established compatible recognition claims"
            if satisfy or category_claims or bucket_claims
            else "graduation-credit-only recognition; no named requirement is established"
        ),
    )

    return RecognitionAssessment(
        section_id=section.section_id,
        decisions=tuple(decisions),
        options=(option,),
        issues=tuple(issues),
    )
