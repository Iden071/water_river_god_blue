import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.catalog import ingest_catalog  # noqa: E402
from timetable_optimizer.fall_candidate_sets import (  # noqa: E402
    enumerate_fall_candidate_sets,
    fall2026_load_policy,
)
from timetable_optimizer.fall_universe import build_fall_section_universe  # noqa: E402
from timetable_optimizer.registration import assess_freshman_registration  # noqa: E402
from timetable_optimizer.verification import (  # noqa: E402
    audit_fall_input_verification,
    audit_fall_universe_verification,
)


class StreamingVerificationParityTests(unittest.TestCase):
    def test_reference_and_streaming_fall_audits_are_identical(self):
        row = {
            "subjtnbCorsePrcts": "A-01",
            "subjtnb": "A",
            "subjtEngNm": "A",
            "subjtNm": "A",
            "campsDivNm": "국제",
            "cdt": 3,
            "cgprfNm": "Professor",
            "estblDeprtNm": "UIC",
            "hy": "1",
            "srclnLctreLangDivNm": "영어",
            "subsrtDivNm": "",
            "atntnMattrDesc": "",
            "gradeEvlMthdDivNm": "절대평가",
            "lctreTimeNm": "화3",
            "lecrmNm": "A",
            "subjtClNm": "대면",
            "rmvlcYn": "0",
            "rmvlcYnNm": "",
        }
        snapshot = ingest_catalog((row,), source_name="fixture", term="2026F")
        universe = build_fall_section_universe("verify-stream", snapshot)
        load = fall2026_load_policy()
        enumeration = enumerate_fall_candidate_sets(
            universe,
            load,
            max_subset_evaluations=10,
        )
        registration = assess_freshman_registration("A-01", {})
        registrations = {"A-01": registration}

        reference = audit_fall_input_verification(
            enumeration,
            registration_assessments=registrations,
        )
        streaming = audit_fall_universe_verification(
            universe,
            load,
            registration_assessments=registrations,
        )
        self.assertEqual(reference, streaming)


if __name__ == "__main__":
    unittest.main()
