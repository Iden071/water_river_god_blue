import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.catalog import SourceListingView  # noqa: E402
from timetable_optimizer.degree import qrm_single_major_2026, spring_2026_initial_state  # noqa: E402
from timetable_optimizer.recognition import (  # noqa: E402
    CourseRecognitionEvidence,
    QualificationStatus,
    recognize_section,
)
from timetable_optimizer.sections import NoListedSchedule, Section  # noqa: E402


def econ_section(*, language_name="", language_code="10"):
    return Section(
        section_id="ECO3130-01-00",
        course_code="ECO3130",
        name="International Finance",
        korean_name="",
        campus="신촌",
        credits=3.0,
        professor="",
        language_code=language_code,
        note="",
        grading="",
        cancelled=False,
        mode_text="",
        schedule=NoListedSchedule("", ""),
        language_name=language_name,
    )


class CanonicalLectureLanguageRecognitionTests(unittest.TestCase):
    def setUp(self):
        self.scenario = qrm_single_major_2026()
        self.state = spring_2026_initial_state(self.scenario)
        self.views = (SourceListingView("School of Economics", "3,4", "ME"),)

    def qrm_me(self, assessment):
        hits = [d for d in assessment.decisions if d.requirement_id == "qrm_me"]
        self.assertEqual(len(hits), 1)
        return hits[0]

    def test_explicit_korean_label_applies_qrm_korean_cap_accounting(self):
        out = recognize_section(
            econ_section(language_name="한국어"),
            self.scenario,
            self.state,
            source_views=self.views,
        )
        self.assertEqual(self.qrm_me(out).status, QualificationStatus.QUALIFIED)
        self.assertEqual(out.options[0].effect.qrm_korean_major_credits, 3.0)

    def test_explicit_english_label_establishes_non_korean(self):
        out = recognize_section(
            econ_section(language_name="영어"),
            self.scenario,
            self.state,
            source_views=self.views,
        )
        self.assertEqual(self.qrm_me(out).status, QualificationStatus.QUALIFIED)
        self.assertEqual(out.options[0].effect.qrm_korean_major_credits, 0.0)

    def test_numeric_code_alone_is_not_reverse_engineered(self):
        out = recognize_section(
            econ_section(language_name="", language_code="10"),
            self.scenario,
            self.state,
            source_views=self.views,
        )
        self.assertEqual(self.qrm_me(out).status, QualificationStatus.UNRESOLVED)
        self.assertTrue(any(issue.code == "qrm_korean_language_unresolved" for issue in out.issues))

    def test_manual_evidence_can_resolve_missing_source_label(self):
        out = recognize_section(
            econ_section(language_name=""),
            self.scenario,
            self.state,
            source_views=self.views,
            evidence=CourseRecognitionEvidence(korean_taught=True, source="verified manual evidence"),
        )
        self.assertEqual(self.qrm_me(out).status, QualificationStatus.QUALIFIED)
        self.assertEqual(out.options[0].effect.qrm_korean_major_credits, 3.0)

    def test_conflicting_source_and_manual_language_evidence_stays_unresolved(self):
        out = recognize_section(
            econ_section(language_name="한국어"),
            self.scenario,
            self.state,
            source_views=self.views,
            evidence=CourseRecognitionEvidence(korean_taught=False, source="conflicting manual evidence"),
        )
        self.assertEqual(self.qrm_me(out).status, QualificationStatus.UNRESOLVED)
        self.assertTrue(any(issue.code == "lecture_language_conflict" for issue in out.issues))

    def test_unrecognized_human_readable_label_stays_unresolved(self):
        out = recognize_section(
            econ_section(language_name="한국어/영어"),
            self.scenario,
            self.state,
            source_views=self.views,
        )
        self.assertEqual(self.qrm_me(out).status, QualificationStatus.UNRESOLVED)


if __name__ == "__main__":
    unittest.main()
