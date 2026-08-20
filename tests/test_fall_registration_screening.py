import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.catalog import ingest_catalog  # noqa: E402
from timetable_optimizer.candidate_assessment import assess_candidate  # noqa: E402
from timetable_optimizer.course_preferences import ProfessorRatingBook  # noqa: E402
from timetable_optimizer.fall2026_preferences import fall2026_preference_profile  # noqa: E402
from timetable_optimizer.fall_registration_screening import (  # noqa: E402
    FallRegistrationScreeningStatus,
    screen_fall_universe_for_freshman_registration,
)
from timetable_optimizer.fall_universe import build_fall_section_universe  # noqa: E402


def row(section_id, *, time="화3"):
    return {
        "subjtnbCorsePrcts": section_id,
        "subjtnb": section_id.split("-")[0],
        "subjtEngNm": section_id,
        "subjtNm": section_id,
        "campsDivNm": "국제",
        "cdt": 3,
        "cgprfNm": "Professor",
        "estblDeprtNm": "UIC",
        "hy": "1",
        "srclnLctreLangDivCd": "10",
        "subsrtDivNm": "",
        "atntnMattrDesc": "",
        "gradeEvlMthdDivNm": "절대평가",
        "rmvlcYn": "0",
        "rmvlcYnNm": " ",
        "lctreTimeNm": time,
        "lecrmNm": "강의실A",
        "subjtClNm": "대면",
    }


def quota(y1, y2=0, y3=0, y4=0, y5=0, y6=0):
    return {
        "sy1PercpCnt": y1,
        "sy2PercpCnt": y2,
        "sy3PercpCnt": y3,
        "sy4PercpCnt": y4,
        "sy5PercpCnt": y5,
        "sy6PercpCnt": y6,
    }


def fixture():
    snapshot = ingest_catalog(
        [
            row("BLOCK-01"),
            row("NOSCHEME-01", time="수3"),
            row("ALLOW-01", time="목3"),
            row("MISSING-01", time="금3"),
            row("INVALID-01", time="월3"),
        ],
        source_name="fixture",
        term="2026F",
    )
    return snapshot, build_fall_section_universe("full", snapshot)


class FallRegistrationScreeningTests(unittest.TestCase):
    def test_only_exact_freshman_gate_block_is_removed(self):
        snapshot, universe = fixture()
        screening = screen_fall_universe_for_freshman_registration(
            universe,
            snapshot,
            {
                "BLOCK-01": quota(0, y2=20),
                "NOSCHEME-01": quota(0),
                "ALLOW-01": quota(10, y2=20),
                "INVALID-01": quota("not-a-number", y2=20),
            },
            source_id="test:seats",
        )

        self.assertEqual(screening.status, FallRegistrationScreeningStatus.PARTIAL)
        self.assertEqual(screening.safely_removed_section_ids, frozenset({"BLOCK-01"}))
        self.assertNotIn("BLOCK-01", screening.screened_universe.searchable_section_ids)
        self.assertTrue(
            {"NOSCHEME-01", "ALLOW-01", "MISSING-01", "INVALID-01"}
            <= screening.screened_universe.searchable_section_ids
        )
        self.assertEqual(
            screening.resolved_nonblocking_section_ids,
            frozenset({"NOSCHEME-01", "ALLOW-01"}),
        )
        self.assertEqual(
            screening.unresolved_section_ids,
            frozenset({"MISSING-01", "INVALID-01"}),
        )
        self.assertIn(
            "invalid_year_quota_evidence",
            {issue.code for issue in screening.issues},
        )

    def test_missing_row_assessment_remains_hard_unknown_downstream(self):
        snapshot, universe = fixture()
        screening = screen_fall_universe_for_freshman_registration(
            universe,
            snapshot,
            {},
            source_id="test:empty-seats",
        )
        section = snapshot.record_for("MISSING-01").section
        self.assertIsNotNone(section)

        assessment = assess_candidate(
            (section,),  # type: ignore[arg-type]
            fall2026_preference_profile(),
            ProfessorRatingBook(()),
            registration_assessments=screening.registration_assessment_map,
        )
        self.assertIn(
            "registration_year_gate_unresolved",
            {issue.code for issue in assessment.hard_constraint_unknowns},
        )

    def test_complete_gate_coverage_does_not_claim_obtainability(self):
        snapshot = ingest_catalog(
            [row("NOSCHEME-01"), row("ALLOW-01", time="수3")],
            source_name="fixture",
            term="2026F",
        )
        universe = build_fall_section_universe("full", snapshot)
        screening = screen_fall_universe_for_freshman_registration(
            universe,
            snapshot,
            {
                "NOSCHEME-01": quota(0),
                "ALLOW-01": quota(10, y2=20),
            },
            source_id="test:seats",
        )

        self.assertEqual(screening.status, FallRegistrationScreeningStatus.COMPLETE)
        self.assertTrue(screening.exact_gate_coverage)
        self.assertFalse(screening.new_hard_exclusions)
        for assessment in screening.assessments:
            self.assertEqual(assessment.obtainability.status.value, "unmeasured")

    def test_existing_cancellation_exclusion_survives_screen_rebuild(self):
        cancelled = row("CANCEL-01")
        cancelled["rmvlcYn"] = "1"
        cancelled["rmvlcYnNm"] = "폐강"
        snapshot = ingest_catalog(
            [cancelled, row("BLOCK-01", time="수3")],
            source_name="fixture",
            term="2026F",
        )
        universe = build_fall_section_universe("full", snapshot)
        screening = screen_fall_universe_for_freshman_registration(
            universe,
            snapshot,
            {"BLOCK-01": quota(0, y2=20)},
            source_id="test:seats",
        )

        exclusions = {
            item.section_id: item.code
            for item in screening.screened_universe.hard_exclusions
        }
        self.assertEqual(exclusions["CANCEL-01"], "canonical_cancelled")
        self.assertEqual(exclusions["BLOCK-01"], "freshman_year_quota_block")


if __name__ == "__main__":
    unittest.main()
