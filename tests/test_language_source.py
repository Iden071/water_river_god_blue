import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.catalog import load_catalog_files  # noqa: E402
from timetable_optimizer.sections import section_from_raw  # noqa: E402


class LectureLanguageSourceTests(unittest.TestCase):
    def test_human_readable_lecture_language_is_preserved_without_decoding_numeric_code(self):
        sec = section_from_raw(
            {
                "subjtnbCorsePrcts": "TEST1000-01-00",
                "subjtnb": "TEST1000",
                "cdt": "3",
                "srclnLctreLangDivCd": "10",
                "srclnLctreLangDivNm": "영어",
            }
        )
        self.assertEqual(sec.language_code, "10")
        self.assertEqual(sec.language_name, "영어")

    def test_missing_human_readable_language_remains_unknown_not_inferred_from_code(self):
        sec = section_from_raw(
            {
                "subjtnbCorsePrcts": "TEST1000-01-00",
                "subjtnb": "TEST1000",
                "cdt": "3",
                "srclnLctreLangDivCd": "10",
            }
        )
        self.assertEqual(sec.language_code, "10")
        self.assertEqual(sec.language_name, "")

    def test_real_fall_catalogue_preserves_any_explicit_language_label_verbatim(self):
        snapshot = load_catalog_files(ROOT / "raw_2026F.json", term="2026-2")
        observations = [
            observation
            for observation in snapshot.observations
            if str(observation.raw.get("srclnLctreLangDivNm") or "").strip()
            and observation.section is not None
        ]
        self.assertTrue(observations, "Fall catalogue has no explicit lecture-language labels")
        for observation in observations:
            expected = str(observation.raw.get("srclnLctreLangDivNm") or "").strip()
            self.assertEqual(observation.section.language_name, expected)


if __name__ == "__main__":
    unittest.main()
