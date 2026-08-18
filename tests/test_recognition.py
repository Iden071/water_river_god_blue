import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.catalog import (  # noqa: E402
    ListingObservation,
    ListingStatus,
    SourceListingView,
    SourceRef,
)
from timetable_optimizer.degree import (  # noqa: E402
    DegreeRuleError,
    RecognitionEffect,
    apply_recognition,
    qrm_single_major_2026,
    spring_2026_initial_state,
)
from timetable_optimizer.recognition import (  # noqa: E402
    CourseRecognitionEvidence,
    QualificationStatus,
    recognize_section,
)
from timetable_optimizer.sections import NoListedSchedule, Section  # noqa: E402


def section(code, *, credits=3.0, section_id=None, name="", language_code=""):
    return Section(
        section_id=section_id or f"{code}-01-00",
        course_code=code,
        name=name or code,
        korean_name="",
        campus="신촌",
        credits=credits,
        professor="",
        language_code=language_code,
        note="",
        grading="",
        cancelled=False,
        mode_text="",
        schedule=NoListedSchedule("", ""),
    )


def qrm_listing(sec, category):
    return ListingObservation(
        source=SourceRef("qrm_listing", "qrm_listings.json", "2026-2", 0),
        program="QRM",
        section_id=sec.section_id,
        status=ListingStatus.OK,
        listed_category=category,
        year_label="",
        campus=sec.campus,
        raw={},
    )


class RecognitionAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.scenario = qrm_single_major_2026()
        self.state = spring_2026_initial_state(self.scenario)

    def decision(self, assessment, requirement_id):
        hits = [d for d in assessment.decisions if d.requirement_id == requirement_id]
        self.assertEqual(len(hits), 1)
        return hits[0]

    def test_exact_qrm_required_course_is_recognized(self):
        sec = section("QRM1001")
        out = recognize_section(sec, self.scenario, self.state)
        self.assertEqual(
            self.decision(out, "qrm_mr_intro").status,
            QualificationStatus.QUALIFIED,
        )
        self.assertTrue(any("qrm_mr_intro" in option.effect.satisfy for option in out.options))

    def test_mathstat_or_regression_requires_qrm_department_evidence(self):
        sec = section("QRM3004")
        wrong_dept = (SourceListingView("Department of Applied Statistics", "3", "MR"),)
        out = recognize_section(sec, self.scenario, self.state, source_views=wrong_dept)
        self.assertEqual(
            self.decision(out, "qrm_mr_mathstat_or_regression").status,
            QualificationStatus.NOT_QUALIFIED,
        )
        self.assertFalse(any("qrm_mr_mathstat_or_regression" in o.effect.satisfy for o in out.options))

        unknown = recognize_section(sec, self.scenario, self.state)
        self.assertEqual(
            self.decision(unknown, "qrm_mr_mathstat_or_regression").status,
            QualificationStatus.UNRESOLVED,
        )

        qrm_dept = (SourceListingView("Department of Quantitative Risk Management", "3", "MR"),)
        accepted = recognize_section(sec, self.scenario, self.state, source_views=qrm_dept)
        self.assertEqual(
            self.decision(accepted, "qrm_mr_mathstat_or_regression").status,
            QualificationStatus.QUALIFIED,
        )

    def test_qrm_program_me_listing_can_establish_major_elective(self):
        sec = section("SPECIAL9999")
        out = recognize_section(
            sec,
            self.scenario,
            self.state,
            program_listings=(qrm_listing(sec, "ME"),),
        )
        self.assertEqual(self.decision(out, "qrm_me").status, QualificationStatus.QUALIFIED)
        self.assertTrue(
            any(("qrm_me", 3.0) in option.effect.bucket_credit_claims for option in out.options)
        )

    def test_official_qrm_me_code_is_not_limited_to_current_candidate_pool(self):
        sec = section("ECO3130")
        out = recognize_section(sec, self.scenario, self.state)
        self.assertEqual(self.decision(out, "qrm_me").status, QualificationStatus.QUALIFIED)

    def test_uic_35xx_and_36xx_are_uic_seminars(self):
        for code in ("UIC3527", "UIC3649"):
            with self.subTest(code=code):
                out = recognize_section(section(code), self.scenario, self.state)
                self.assertEqual(
                    self.decision(out, "cc_uic_seminar").status,
                    QualificationStatus.QUALIFIED,
                )
                self.assertTrue(
                    any(("cc_uic_seminar", 3.0) in o.effect.bucket_credit_claims for o in out.options)
                )

    def test_lhp_categories_are_distinct_and_science_history_is_not_world_history(self):
        literature = recognize_section(section("UIC1251"), self.scenario, self.state)
        self.assertTrue(
            any(("cc_lhp", "literature") in o.effect.category_claims for o in literature.options)
        )

        history = recognize_section(section("UIC1551"), self.scenario, self.state)
        self.assertTrue(
            any(("cc_lhp", "history") in o.effect.category_claims for o in history.options)
        )

        philosophy = recognize_section(section("UIC1901"), self.scenario, self.state)
        self.assertTrue(
            any(("cc_lhp", "philosophy") in o.effect.category_claims for o in philosophy.options)
        )

        science_history = recognize_section(section("UIC1541"), self.scenario, self.state)
        self.assertFalse(
            any(("cc_lhp", "history") in o.effect.category_claims for o in science_history.options)
        )
        self.assertTrue(
            any(("cc_scird", 3.0) in o.effect.bucket_credit_claims for o in science_history.options)
        )

    def test_science_rule_is_open_ended_not_false_negative(self):
        known = recognize_section(section("UIC2151"), self.scenario, self.state)
        self.assertEqual(self.decision(known, "cc_scird").status, QualificationStatus.QUALIFIED)

        unknown = recognize_section(section("NEWSCI9999"), self.scenario, self.state)
        self.assertEqual(
            self.decision(unknown, "cc_scird").status,
            QualificationStatus.UNRESOLVED,
        )

    def test_uic_language_list_is_exact_and_non_uic_route_requires_evidence(self):
        uic = recognize_section(section("UIC1806"), self.scenario, self.state)
        self.assertEqual(self.decision(uic, "cc_language").status, QualificationStatus.QUALIFIED)

        excluded = recognize_section(
            section("YCF1652"),
            self.scenario,
            self.state,
            evidence=CourseRecognitionEvidence(foreign_language_course=True, source="test"),
        )
        self.assertEqual(
            self.decision(excluded, "cc_language").status,
            QualificationStatus.NOT_QUALIFIED,
        )

        unresolved = recognize_section(section("YCF1301"), self.scenario, self.state)
        self.assertEqual(
            self.decision(unresolved, "cc_language").status,
            QualificationStatus.UNRESOLVED,
        )

        verified = recognize_section(
            section("YCF1301"),
            self.scenario,
            self.state,
            evidence=CourseRecognitionEvidence(foreign_language_course=True, source="verified course evidence"),
        )
        self.assertEqual(
            self.decision(verified, "cc_language").status,
            QualificationStatus.QUALIFIED,
        )

    def test_missing_credits_produces_no_invented_recognition_effect(self):
        out = recognize_section(section("QRM1001", credits=None), self.scenario, self.state)
        self.assertEqual(out.options, ())
        self.assertTrue(any(issue.code == "missing_credits" for issue in out.issues))

    def test_korean_econ_stat_major_cap_blocks_qrm_assignment_not_course_credit(self):
        state = self.state
        for i in range(4):
            state = apply_recognition(
                state,
                self.scenario,
                RecognitionEffect.course(
                    completion_id=f"korean-me-{i}",
                    course_code=f"KME{i}",
                    credits=3.0,
                    bucket_credit_claims=(("qrm_me", 3.0),),
                    qrm_korean_major_credits=3.0,
                ),
            )

        sec = section("ECO3130")
        views = (SourceListingView("School of Economics", "3,4", "ME"),)
        out = recognize_section(
            sec,
            self.scenario,
            state,
            source_views=views,
            evidence=CourseRecognitionEvidence(korean_taught=True, source="verified language evidence"),
        )
        self.assertEqual(self.decision(out, "qrm_me").status, QualificationStatus.NOT_QUALIFIED)
        self.assertTrue(any(issue.code == "qrm_korean_cap_exhausted" for issue in out.issues))

    def test_state_transition_rejects_bucket_satisfaction_shortcut(self):
        with self.assertRaises(DegreeRuleError):
            apply_recognition(
                self.state,
                self.scenario,
                RecognitionEffect.course(
                    completion_id="bad-language-shortcut",
                    course_code="UIC1806",
                    credits=3.0,
                    satisfy=("cc_language",),
                ),
            )


if __name__ == "__main__":
    unittest.main()
