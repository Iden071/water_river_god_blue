"""Concrete second-major scenarios for the Stage 4 degree-state rebuild.

The old optimizer represented an undecided second major as anonymous generic ``DM``
courses.  That is not a degree model: different majors carry different required courses,
credit structure, sequencing, and cross-recognition rules.

This module keeps candidate identity separate from evidence completeness.  A named candidate
may therefore remain ``UNRESOLVED`` until its current departmental rules are encoded.  Only
requirements supported by evidence are placed into the scenario; missing structure is never
replaced by generic filler.

``DegreeScenario.requirements`` is the evaluation set used by the current Stage 4B degree and
recognition code.  ``SecondMajorSpec.requirements`` also preserves ownership.  The builder
below deliberately copies each second-major requirement into the scenario evaluation set so
nested requirements cannot exist invisibly.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from .degree import (
    CreditBucketRequirement,
    DegreeRuleError,
    DegreeScenario,
    Requirement,
    SecondMajorSpec,
    SecondMajorStatus,
    SpecificCourseRequirement,
    qrm_double_major_shell_2026,
)


PHYSICS_REQUIREMENT_SOURCE = (
    "Yonsei Physics undergraduate requirement notice (2024-02-05), current for 2024+; "
    "verified 2026-08-18"
)
PHYSICS_CURRICULUM_SOURCE = (
    "Yonsei Physics current undergraduate curriculum; verified 2026-08-18"
)
APPLIED_STATISTICS_SOURCE = (
    "Yonsei Applied Statistics graduation-requirement notice, 2026-07 revision; "
    "verified 2026-08-18"
)


# Current Physics required-major courses published by the department.  The 2024+ rule for a
# student whose first major is elsewhere is 27 required-major credits + 9 elective-major
# credits = 36 Physics credits.
PHYSICS_REQUIRED_2026: tuple[SpecificCourseRequirement, ...] = (
    SpecificCourseRequirement(
        "second_physics_lab_a1",
        "Physics Lab (A-1)",
        ("PHY2105",),
        3.0,
        source=PHYSICS_REQUIREMENT_SOURCE,
    ),
    SpecificCourseRequirement(
        "second_physics_quantum_1",
        "Quantum Mechanics (1)",
        ("PHY3101",),
        3.0,
        source=PHYSICS_REQUIREMENT_SOURCE,
    ),
    SpecificCourseRequirement(
        "second_physics_quantum_2",
        "Quantum Mechanics (2)",
        ("PHY3102",),
        3.0,
        source=PHYSICS_REQUIREMENT_SOURCE,
    ),
    SpecificCourseRequirement(
        "second_physics_em_1",
        "Electromagnetism (1)",
        ("PHY3103",),
        3.0,
        source=PHYSICS_REQUIREMENT_SOURCE,
    ),
    SpecificCourseRequirement(
        "second_physics_em_2",
        "Electromagnetism (2)",
        ("PHY3104",),
        3.0,
        source=PHYSICS_REQUIREMENT_SOURCE,
    ),
    SpecificCourseRequirement(
        "second_physics_statistical",
        "Statistical Physics",
        ("PHY3106",),
        3.0,
        source=PHYSICS_REQUIREMENT_SOURCE,
    ),
    SpecificCourseRequirement(
        "second_physics_lab_b1",
        "Physics Lab (B-1)",
        ("PHY3107",),
        3.0,
        source=PHYSICS_REQUIREMENT_SOURCE,
    ),
    SpecificCourseRequirement(
        "second_physics_mechanics_1",
        "Mechanics (1)",
        ("PHY3110",),
        3.0,
        source=PHYSICS_REQUIREMENT_SOURCE,
    ),
    SpecificCourseRequirement(
        "second_physics_mechanics_2",
        "Mechanics (2)",
        ("PHY3111",),
        3.0,
        source=PHYSICS_REQUIREMENT_SOURCE,
    ),
)

PHYSICS_ELECTIVE_2026 = CreditBucketRequirement(
    "second_physics_electives",
    "Physics Major Electives",
    target_credits=9.0,
    qualification_rule_id="physics_major_elective_2026",
    source=PHYSICS_REQUIREMENT_SOURCE,
)

# Exact course identities currently published under Physics major electives.  These are
# evidence for the later recognition rule; recommended prerequisites on the department page
# are intentionally not promoted to hard prerequisites here.
PHYSICS_ELECTIVE_2026_CODES = frozenset(
    {
        "PHY2103",
        "PHY2104",
        "PHY2106",
        "PHY3105",
        "PHY3108",
        "PHY3109",
        "PHY4101",
        "PHY4102",
        "PHY4107",
        "PHY4109",
        "PHY4113",
        "PHY4115",
        "PHY4116",
        "PHY4117",
        "PHY4205",
        "PHY4206",
        "PHY4207",
        "PHY4208",
    }
)


@dataclass(frozen=True)
class SecondMajorCandidate:
    """One named second-major possibility plus the evidence state we can defend today."""

    candidate_id: str
    spec: SecondMajorSpec
    evidence_notes: tuple[str, ...] = ()
    unresolved_notes: tuple[str, ...] = ()

    @property
    def name(self) -> str:
        if self.spec.name is None:
            raise DegreeRuleError("a concrete second-major candidate must have a name")
        return self.spec.name


PHYSICS = SecondMajorCandidate(
    candidate_id="physics",
    spec=SecondMajorSpec(
        status=SecondMajorStatus.RESOLVED,
        name="Physics",
        requirements=PHYSICS_REQUIRED_2026 + (PHYSICS_ELECTIVE_2026,),
    ),
    evidence_notes=(
        "Current 2024+ Physics second-major rule: 27 required + 9 elective = 36 credits.",
        "Required course identities and current elective catalogue are published by the department.",
    ),
    unresolved_notes=(
        "Future offering frequency and timetable geometry remain future-catalogue uncertainty.",
        "Recommended prerequisite text is not encoded as a hard prerequisite without a binding rule.",
    ),
)

APPLIED_STATISTICS = SecondMajorCandidate(
    candidate_id="applied-statistics",
    spec=SecondMajorSpec(status=SecondMajorStatus.UNRESOLVED, name="Applied Statistics"),
    evidence_notes=(
        "Department notice establishes 36 major credits for an on-campus double major.",
        "The department maintains a dedicated double-major requirement sheet.",
        "QRM-to-Applied-Statistics cross-recognition has a time-limited prior-taking rule for named courses.",
    ),
    unresolved_notes=(
        "The current category-by-category double-major spreadsheet has not yet been ingested into the canonical model.",
        "Do not replace the missing category structure with a generic 36-credit bucket.",
    ),
)

MATHEMATICS = SecondMajorCandidate(
    candidate_id="mathematics",
    spec=SecondMajorSpec(status=SecondMajorStatus.UNRESOLVED, name="Mathematics"),
    unresolved_notes=(
        "Current cohort-specific Mathematics second-major requirement structure has not yet been encoded.",
    ),
)

INDUSTRIAL_ENGINEERING = SecondMajorCandidate(
    candidate_id="industrial-engineering",
    spec=SecondMajorSpec(status=SecondMajorStatus.UNRESOLVED, name="Industrial Engineering"),
    unresolved_notes=(
        "Current cohort-specific Industrial Engineering requirement spreadsheet has not yet been ingested.",
    ),
)

ELECTRICAL_ELECTRONIC_ENGINEERING = SecondMajorCandidate(
    candidate_id="electrical-electronic-engineering",
    spec=SecondMajorSpec(
        status=SecondMajorStatus.UNRESOLVED,
        name="Electrical and Electronic Engineering",
    ),
    unresolved_notes=(
        "Current detailed EEE second-major curriculum table has not yet been ingested.",
    ),
)

COMPUTER_SCIENCE = SecondMajorCandidate(
    candidate_id="computer-science",
    spec=SecondMajorSpec(status=SecondMajorStatus.UNRESOLVED, name="Computer Science"),
    unresolved_notes=(
        "Current cohort-specific Computer Science second-major requirement table has not yet been established completely.",
    ),
)


SECOND_MAJOR_CANDIDATES_2026: tuple[SecondMajorCandidate, ...] = (
    MATHEMATICS,
    INDUSTRIAL_ENGINEERING,
    ELECTRICAL_ELECTRONIC_ENGINEERING,
    COMPUTER_SCIENCE,
    APPLIED_STATISTICS,
    PHYSICS,
)

SECOND_MAJOR_CANDIDATES_BY_ID = {
    candidate.candidate_id: candidate for candidate in SECOND_MAJOR_CANDIDATES_2026
}


def qrm_double_major_candidate_2026(candidate_id: str) -> DegreeScenario:
    """Build one identity-specific QRM + second-major scenario.

    Unknown departmental structure remains unresolved.  For candidates with requirements
    already supported by evidence, those requirements are copied into the scenario's flat
    evaluation set as well as retained under ``SecondMajorSpec`` ownership.  This is a
    compatibility invariant for the current Stage 4B degree/recognition engine: no nested
    second-major requirement may be silently ignored.
    """

    try:
        candidate = SECOND_MAJOR_CANDIDATES_BY_ID[candidate_id]
    except KeyError as exc:
        raise DegreeRuleError(f"unknown second-major candidate: {candidate_id!r}") from exc

    base = qrm_double_major_shell_2026()
    combined = base.requirements + candidate.spec.requirements
    requirement_ids = tuple(requirement.requirement_id for requirement in combined)
    if len(requirement_ids) != len(set(requirement_ids)):
        raise DegreeRuleError(
            f"duplicate requirement id while building second-major scenario {candidate_id!r}"
        )

    return replace(
        base,
        scenario_id=f"qrm-double-{candidate.candidate_id}-2026",
        requirements=combined,
        second_major=candidate.spec,
    )
