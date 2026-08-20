"""Concrete second-major scenarios for the Stage 4 degree-state rebuild."""

from __future__ import annotations
from dataclasses import dataclass, replace
from .degree import AnyOfRequirement, CreditBucketRequirement, DegreeRuleError, DegreeScenario, SecondMajorSpec, SecondMajorStatus, SpecificCourseRequirement, qrm_double_major_shell_2026

PHYSICS_REQUIREMENT_SOURCE="Yonsei Physics undergraduate requirement notice (2024-02-05), current for 2024+; verified 2026-08-18"
PHYSICS_CURRICULUM_SOURCE="Yonsei Physics current undergraduate curriculum; verified 2026-08-18"
EEE_REQUIREMENT_SOURCE="Yonsei Electrical & Electronic Engineering current campus double-major graduation table, 2018+ row; verified 2026-08-18"
APPLIED_STATISTICS_SOURCE="Yonsei Applied Statistics graduation-requirement notice, 2026-07 revision; verified 2026-08-18"
MATHEMATICS_SOURCE="Yonsei Mathematics undergraduate major-credit table for 2022+ entrants; verified 2026-08-18"
INDUSTRIAL_ENGINEERING_SOURCE="Yonsei Industrial Engineering posted graduation-requirement workbook (2025-06-19 revision); verified 2026-08-18"
COMPUTING_SOURCE="Yonsei Software/School of Computing current undergraduate guidance; verified 2026-08-18"

APPLIED_STATISTICS_DOUBLE_MAJOR_CREDITS_2026=36.0
APPLIED_STATISTICS_QRM_TEMP_CROSS_RECOGNITION_2026={"QRM3004":"STA3125","QRM3005":"STA3126","QRM2004":"STA2105"}

PHYSICS_REQUIRED_2026=tuple(SpecificCourseRequirement(r,t,(c,),3.0,source=PHYSICS_REQUIREMENT_SOURCE) for r,t,c in (("second_physics_lab_a1","Physics Lab (A-1)","PHY2105"),("second_physics_quantum_1","Quantum Mechanics (1)","PHY3101"),("second_physics_quantum_2","Quantum Mechanics (2)","PHY3102"),("second_physics_em_1","Electromagnetism (1)","PHY3103"),("second_physics_em_2","Electromagnetism (2)","PHY3104"),("second_physics_statistical","Statistical Physics","PHY3106"),("second_physics_lab_b1","Physics Lab (B-1)","PHY3107"),("second_physics_mechanics_1","Mechanics (1)","PHY3110"),("second_physics_mechanics_2","Mechanics (2)","PHY3111")))
PHYSICS_ELECTIVE_2026=CreditBucketRequirement("second_physics_electives","Physics Major Electives",9.0,"physics_major_elective_2026",source=PHYSICS_REQUIREMENT_SOURCE)
PHYSICS_ELECTIVE_2026_CODES=frozenset({"PHY2103","PHY2104","PHY2106","PHY3105","PHY3108","PHY3109","PHY4101","PHY4102","PHY4107","PHY4109","PHY4113","PHY4115","PHY4116","PHY4117","PHY4205","PHY4206","PHY4207","PHY4208"})

EEE_REQUIRED_2026=tuple(SpecificCourseRequirement(r,t,(c,),3.0,source=EEE_REQUIREMENT_SOURCE) for r,t,c in (("second_eee_data_structures","Data Structures","EEE2020"),("second_eee_electromagnetics_1","Electromagnetics (1)","EEE2030"),("second_eee_basic_circuit_theory","Basic Circuit Theory","EEE2010"),("second_eee_digital_logic","Digital Logic Circuit","EEE2040"),("second_eee_signals_systems","Signals and Systems","EEE2060"),("second_eee_electronic_circuits_1","Electronic Circuits (1)","EEE2050"),("second_eee_basic_analog_lab","Basic Analog Experiment","EEE2111"),("second_eee_basic_digital_lab","Basic Digital Experiment","EEE3313"),("second_eee_capstone","Electrical and Electronic Engineering Capstone Design","EEE4610")))
EEE_EXPERIMENT_2026_CODES=("EEE4549","EEE4423","EEE4473","EEE4621","EEE4548","EEE4474","EEE4475","EEE4476")
EEE_EXPERIMENT_2026=AnyOfRequirement("second_eee_experiment","EEE designated experiment elective",EEE_EXPERIMENT_2026_CODES,3.0,source=EEE_REQUIREMENT_SOURCE)
EEE_ELECTIVE_2026_CODES=frozenset({"EEE2001","EEE2112","EEE3120","EEE3150","EEE3210","EEE3220","EEE3240","EEE3310","EEE3314","EEE3350","EEE3410","EEE3430","EEE3440","EEE3450","EEE3510","EEE3511","EEE3530","EEE3535","EEE3540","EEE3543","EEE3544","EEE3545","EEE3547","EEE3548","EEE4110","EEE4120","EEE4140","EEE4240","EEE4250","EEE4260","EEE4270","EEE4280","EEE4290","EEE4320","EEE4340","EEE4350","EEE4420","EEE4430","EEE4624"})
EEE_ELECTIVE_2026=CreditBucketRequirement("second_eee_electives","EEE Major Electives",6.0,"eee_major_elective_2018_plus",source=EEE_REQUIREMENT_SOURCE)

@dataclass(frozen=True)
class SecondMajorCandidate:
    candidate_id:str; spec:SecondMajorSpec; evidence_notes:tuple[str,...]=(); unresolved_notes:tuple[str,...]=()
    @property
    def name(self)->str:
        if self.spec.name is None: raise DegreeRuleError("a concrete second-major candidate must have a name")
        return self.spec.name

PHYSICS=SecondMajorCandidate("physics",SecondMajorSpec(SecondMajorStatus.RESOLVED,"Physics",PHYSICS_REQUIRED_2026+(PHYSICS_ELECTIVE_2026,)),("Current 2024+ Physics second-major rule: 27 required + 9 elective = 36 credits.",),("Future offering frequency and timetable geometry remain downstream uncertainty.",))
ELECTRICAL_ELECTRONIC_ENGINEERING=SecondMajorCandidate("electrical-electronic-engineering",SecondMajorSpec(SecondMajorStatus.RESOLVED,"Electrical and Electronic Engineering",EEE_REQUIRED_2026+(EEE_EXPERIMENT_2026,EEE_ELECTIVE_2026)),("Current 2018+ campus double-major rule totals 36 credits: EEE2020 3 + eight fixed required 24 + one designated experiment 3 + electives 6.",),("Foundation recommendations are not promoted to hard requirements.",))
APPLIED_STATISTICS=SecondMajorCandidate("applied-statistics",SecondMajorSpec(SecondMajorStatus.UNRESOLVED,"Applied Statistics"),("Current notice: campus double major requires 36 major credits; QRM already requires STA1001, so no extra STA1001 burden is added beyond those 36 major credits.","Temporary prior-taking mappings: QRM3004->STA3125, QRM3005->STA3126, QRM2004->STA2105.","A QRM-major-elective recognition cannot simultaneously be used as Applied Statistics second-major credit."),("The category-by-category campus-double-major workbook is identified but not parseable through the current interface; exact category minima stay unresolved.","Do not replace missing structure with a generic 36-credit bucket."))
MATHEMATICS=SecondMajorCandidate("mathematics",SecondMajorSpec(SecondMajorStatus.UNRESOLVED,"Mathematics"),("Current aggregate: 36 major credits = 9 required + 27 elective.",),("Exact required-course identities remain unresolved because current published materials conflict when read literally.",))
INDUSTRIAL_ENGINEERING=SecondMajorCandidate("industrial-engineering",SecondMajorSpec(SecondMajorStatus.UNRESOLVED,"Industrial Engineering"),("Current department workbook 산업공학과_졸업요건표(2025.06.19).xlsx is explicitly entry-year-specific.",),("The official workbook is identified but not parseable through the current interface; no general-curriculum substitute is used.",))
COMPUTER_SCIENCE=SecondMajorCandidate("computer-science",SecondMajorSpec(SecondMajorStatus.UNRESOLVED,"Computer Science"),("Current public material spans older Software second-major rules and the newer School of Computing curriculum.",),("The formal 2026 mapping is not safe enough to encode one requirement graph.",))
SECOND_MAJOR_CANDIDATES_2026=(MATHEMATICS,INDUSTRIAL_ENGINEERING,ELECTRICAL_ELECTRONIC_ENGINEERING,COMPUTER_SCIENCE,APPLIED_STATISTICS,PHYSICS)
SECOND_MAJOR_CANDIDATES_BY_ID={c.candidate_id:c for c in SECOND_MAJOR_CANDIDATES_2026}

def qrm_double_major_candidate_2026(candidate_id:str)->DegreeScenario:
    try: candidate=SECOND_MAJOR_CANDIDATES_BY_ID[candidate_id]
    except KeyError as exc: raise DegreeRuleError(f"unknown second-major candidate: {candidate_id!r}") from exc
    base=qrm_double_major_shell_2026(); combined=base.requirements+candidate.spec.requirements; ids=tuple(r.requirement_id for r in combined)
    if len(ids)!=len(set(ids)): raise DegreeRuleError(f"duplicate requirement id while building second-major scenario {candidate_id!r}")
    return replace(base,scenario_id=f"qrm-double-{candidate.candidate_id}-2026",requirements=combined,second_major=candidate.spec)
