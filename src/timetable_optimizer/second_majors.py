"""Concrete second-major scenarios for the Stage 4 degree-state rebuild.

The old optimizer represented an undecided second major as anonymous generic ``DM`` courses.
Different majors carry different required courses, credit structures, sequencing, and
cross-recognition rules, so missing structure remains unresolved rather than being replaced
by generic filler.

``DegreeScenario.requirements`` is the evaluation set used by the current Stage 4B degree and
recognition code. ``SecondMajorSpec.requirements`` also preserves ownership. The builder
copies every evidence-backed second-major requirement into the scenario evaluation set so
nested requirements cannot exist invisibly.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from .degree import (
    AnyOfRequirement,
    CreditBucketRequirement,
    DegreeRuleError,
    DegreeScenario,
    SecondMajorSpec,
    SecondMajorStatus,
    SpecificCourseRequirement,
    qrm_double_major_shell_2026,
)

PHYSICS_REQUIREMENT_SOURCE = "Yonsei Physics undergraduate requirement notice (2024-02-05), current for 2024+; verified 2026-08-18"
PHYSICS_CURRICULUM_SOURCE = "Yonsei Physics current undergraduate curriculum; verified 2026-08-18"
EEE_REQUIREMENT_SOURCE = "Yonsei Electrical & Electronic Engineering current campus double-major graduation table, 2018+ row; verified 2026-08-18"
APPLIED_STATISTICS_SOURCE = "Yonsei Applied Statistics graduation-requirement notice, 2026-07 revision; verified 2026-08-18"
MATHEMATICS_SOURCE = "Yonsei Mathematics undergraduate major-credit table for 2022+ entrants; verified 2026-08-18"
INDUSTRIAL_ENGINEERING_SOURCE = "Yonsei Industrial Engineering posted graduation-requirement workbook (2025-06-19 revision); verified 2026-08-18"
COMPUTING_SOURCE = "Yonsei Software/School of Computing current undergraduate guidance; verified 2026-08-18"

# Publicly established Applied Statistics facts that do not depend on the unread workbook.
APPLIED_STATISTICS_DOUBLE_MAJOR_CREDITS_2026 = 36.0
APPLIED_STATISTICS_QRM_TEMP_CROSS_RECOGNITION_2026 = {
    "QRM3004": "STA3125",
    "QRM3005": "STA3126",
    "QRM2004": "STA2105",
}

PHYSICS_REQUIRED_2026 = (
    SpecificCourseRequirement("second_physics_lab_a1", "Physics Lab (A-1)", ("PHY2105",), 3.0, source=PHYSICS_REQUIREMENT_SOURCE),
    SpecificCourseRequirement("second_physics_quantum_1", "Quantum Mechanics (1)", ("PHY3101",), 3.0, source=PHYSICS_REQUIREMENT_SOURCE),
    SpecificCourseRequirement("second_physics_quantum_2", "Quantum Mechanics (2)", ("PHY3102",), 3.0, source=PHYSICS_REQUIREMENT_SOURCE),
    SpecificCourseRequirement("second_physics_em_1", "Electromagnetism (1)", ("PHY3103",), 3.0, source=PHYSICS_REQUIREMENT_SOURCE),
    SpecificCourseRequirement("second_physics_em_2", "Electromagnetism (2)", ("PHY3104",), 3.0, source=PHYSICS_REQUIREMENT_SOURCE),
    SpecificCourseRequirement("second_physics_statistical", "Statistical Physics", ("PHY3106",), 3.0, source=PHYSICS_REQUIREMENT_SOURCE),
    SpecificCourseRequirement("second_physics_lab_b1", "Physics Lab (B-1)", ("PHY3107",), 3.0, source=PHYSICS_REQUIREMENT_SOURCE),
    SpecificCourseRequirement("second_physics_mechanics_1", "Mechanics (1)", ("PHY3110",), 3.0, source=PHYSICS_REQUIREMENT_SOURCE),
    SpecificCourseRequirement("second_physics_mechanics_2", "Mechanics (2)", ("PHY3111",), 3.0, source=PHYSICS_REQUIREMENT_SOURCE),
)
PHYSICS_ELECTIVE_2026 = CreditBucketRequirement("second_physics_electives", "Physics Major Electives", 9.0, "physics_major_elective_2026", source=PHYSICS_REQUIREMENT_SOURCE)
PHYSICS_ELECTIVE_2026_CODES = frozenset({"PHY2103", "PHY2104", "PHY2106", "PHY3105", "PHY3108", "PHY3109", "PHY4101", "PHY4102", "PHY4107", "PHY4109", "PHY4113", "PHY4115", "PHY4116", "PHY4117", "PHY4205", "PHY4206", "PHY4207", "PHY4208"})

EEE_REQUIRED_2026 = (
    SpecificCourseRequirement("second_eee_data_structures", "Data Structures", ("EEE2020",), 3.0, source=EEE_REQUIREMENT_SOURCE),
    SpecificCourseRequirement("second_eee_electromagnetics_1", "Electromagnetics (1)", ("EEE2030",), 3.0, source=EEE_REQUIREMENT_SOURCE),
    SpecificCourseRequirement("second_eee_basic_circuit_theory", "Basic Circuit Theory", ("EEE2010",), 3.0, source=EEE_REQUIREMENT_SOURCE),
    SpecificCourseRequirement("second_eee_digital_logic", "Digital Logic Circuit", ("EEE2040",), 3.0, source=EEE_REQUIREMENT_SOURCE),
    SpecificCourseRequirement("second_eee_signals_systems", "Signals and Systems", ("EEE2060",), 3.0, source=EEE_REQUIREMENT_SOURCE),
    SpecificCourseRequirement("second_eee_electronic_circuits_1", "Electronic Circuits (1)", ("EEE2050",), 3.0, source=EEE_REQUIREMENT_SOURCE),
    SpecificCourseRequirement("second_eee_basic_analog_lab", "Basic Analog Experiment", ("EEE2111",), 3.0, source=EEE_REQUIREMENT_SOURCE),
    SpecificCourseRequirement("second_eee_basic_digital_lab", "Basic Digital Experiment", ("EEE3313",), 3.0, source=EEE_REQUIREMENT_SOURCE),
    SpecificCourseRequirement("second_eee_capstone", "Electrical and Electronic Engineering Capstone Design", ("EEE4610",), 3.0, source=EEE_REQUIREMENT_SOURCE),
)
EEE_EXPERIMENT_2026_CODES = ("EEE4549", "EEE4423", "EEE4473", "EEE4621", "EEE4548", "EEE4474", "EEE4475", "EEE4476")
EEE_EXPERIMENT_2026 = AnyOfRequirement("second_eee_experiment", "EEE designated experiment elective", EEE_EXPERIMENT_2026_CODES, 3.0, source=EEE_REQUIREMENT_SOURCE)
EEE_ELECTIVE_2026_CODES = frozenset({"EEE2001", "EEE2112", "EEE3120", "EEE3150", "EEE3210", "EEE3220", "EEE3240", "EEE3310", "EEE3314", "EEE3350", "EEE3410", "EEE3430", "EEE3440", "EEE3450", "EEE3510", "EEE3511", "EEE3530", "EEE3535", "EEE3540", "EEE3543", "EEE3544", "EEE3545", "EEE3547", "EEE3548", "EEE4110", "EEE4120", "EEE4140", "EEE4240", "EEE4250", "EEE4260", "EEE4270", "EEE4280", "EEE4290", "EEE4320", "EEE4340", "EEE4350", "EEE4420", "EEE4430", "EEE4624"})
EEE_ELECTIVE_2026 = CreditBucketRequirement("second_eee_electives", "EEE Major Electives", 6.0, "eee_major_elective_2018_plus", source=EEE_REQUIREMENT_SOURCE)


@dataclass(frozen=True)
class SecondMajorCandidate:
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
    "physics",
    SecondMajorSpec(SecondMajorStatus.RESOLVED, "Physics", PHYSICS_REQUIRED_2026 + (PHYSICS_ELECTIVE_2026,)),
    ("Current 2024+ Physics second-major rule: 27 required + 9 elective = 36 credits.", "Required course identities and current elective catalogue are published by the department."),
    ("Future offering frequency and timetable geometry remain future-catalogue uncertainty.", "Recommended prerequisite text is not encoded as a hard prerequisite without a binding rule."),
)
ELECTRICAL_ELECTRONIC_ENGINEERING = SecondMajorCandidate(
    "electrical-electronic-engineering",
    SecondMajorSpec(SecondMajorStatus.RESOLVED, "Electrical and Electronic Engineering", EEE_REQUIRED_2026 + (EEE_EXPERIMENT_2026, EEE_ELECTIVE_2026)),
    ("Current campus double-major table labels the active rule 2018+ and totals 36 credits.", "Structure: EEE2020 3 credits + eight fixed required courses 24 credits + one designated experiment 3 credits + published electives 6 credits.", "EEE2113 is explicitly marked as having no completion obligation in the current table."),
    ("The table recommends engineering-foundation study for practical course access but does not make that recommendation a double-major graduation requirement.", "Future offering frequency, prerequisites, and timetable geometry remain downstream evidence questions."),
)
APPLIED_STATISTICS = SecondMajorCandidate(
    "applied-statistics",
    SecondMajorSpec(SecondMajorStatus.UNRESOLVED, "Applied Statistics"),
    (
        "The July 2026 department notice establishes 36 major credits for an on-campus double major; Introduction to Statistics is separate unless the first major already requires it. QRM already requires STA1001, so this QRM-first-major scenario does not add a separate 3-credit STA1001 burden beyond the 36 major credits.",
        "The authoritative category structure is in the dedicated campus-double-major workbook sheet.",
        "The January 2026 temporary prior-taking rule maps QRM3004 -> STA3125, QRM3005 -> STA3126, and QRM2004 -> STA2105, only for qualifying previously taken offerings under that temporary rule.",
        "A course recognized as a QRM Major Elective cannot simultaneously be used as Applied Statistics second-major credit.",
        "Outside-department recognition for double-major students is limited to two courses and has additional exclusions/conditions.",
    ),
    ("The current category-by-category double-major spreadsheet could be identified but not parsed through the available web/connector interface, so exact Basic/Requisite/Elective minima are not encoded.", "Do not replace the missing category structure with a generic 36-credit bucket."),
)
MATHEMATICS = SecondMajorCandidate("mathematics", SecondMajorSpec(SecondMajorStatus.UNRESOLVED, "Mathematics"), ("The department's 2022+ major-credit table states that a second Mathematics major requires 36 major credits: 9 required + 27 elective.",), ("The published course-flow image cannot be reconciled safely with a literal 9-credit required set; exact required identities remain unresolved.",))
INDUSTRIAL_ENGINEERING = SecondMajorCandidate("industrial-engineering", SecondMajorSpec(SecondMajorStatus.UNRESOLVED, "Industrial Engineering"), ("The department publishes the entry-year-specific workbook 산업공학과_졸업요건표(2025.06.19).xlsx and explicitly instructs students to use the rule for their admission year.",), ("The official attachment could be identified but not parsed through the available web/connector interface, so its current second-major category/course structure is not encoded.", "Courses absent from the table may require department-office confirmation, so the general IE curriculum is not substituted for the workbook."))
COMPUTER_SCIENCE = SecondMajorCandidate("computer-science", SecondMajorSpec(SecondMajorStatus.UNRESOLVED, "Computer Science"), ("Current Software guidance states that a second Software major totals 36 required + elective major credits and excludes certain course categories from second-major credit.", "The current School of Computing separately publishes a newer CAS-coded curriculum for recent entrants."), ("The formal 2026 second-major identity/curriculum mapping between the older Software rules and newer School of Computing curriculum is not established well enough to encode one graph.", "Do not silently apply the 2021-23 SWE table to a 2026 candidate or treat every CAS course as second-major credit."))

SECOND_MAJOR_CANDIDATES_2026 = (MATHEMATICS, INDUSTRIAL_ENGINEERING, ELECTRICAL_ELECTRONIC_ENGINEERING, COMPUTER_SCIENCE, APPLIED_STATISTICS, PHYSICS)
SECOND_MAJOR_CANDIDATES_BY_ID = {candidate.candidate_id: candidate for candidate in SECOND_MAJOR_CANDIDATES_2026}


def qrm_double_major_candidate_2026(candidate_id: str) -> DegreeScenario:
    try:
        candidate = SECOND_MAJOR_CANDIDATES_BY_ID[candidate_id]
    except KeyError as exc:
        raise DegreeRuleError(f"unknown second-major candidate: {candidate_id!r}") from exc
    base = qrm_double_major_shell_2026()
    combined = base.requirements + candidate.spec.requirements
    ids = tuple(requirement.requirement_id for requirement in combined)
    if len(ids) != len(set(ids)):
        raise DegreeRuleError(f"duplicate requirement id while building second-major scenario {candidate_id!r}")
    return replace(base, scenario_id=f"qrm-double-{candidate.candidate_id}-2026", requirements=combined, second_major=candidate.spec)
