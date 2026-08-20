import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.registration import (  # noqa: E402
    ObtainabilityStatus,
    RegistrationEvidenceError,
    YearQuotaGateStatus,
    assess_freshman_registration,
    historical_mileage_observation_from_row,
    mileage_evidence_for_course,
)


class FreshmanRegistrationEvidenceTests(unittest.TestCase):
    def test_all_zero_year_quotas_mean_no_scheme_not_impossible(self):
        rows = {
            "UIC1561-01-00": {
                "sy1PercpCnt": 0,
                "sy2PercpCnt": 0,
                "sy3PercpCnt": 0,
                "sy4PercpCnt": 0,
                "sy5PercpCnt": 0,
                "sy6PercpCnt": 0,
            }
        }
        assessment = assess_freshman_registration("UIC1561-01-00", rows)

        self.assertEqual(
            assessment.year_quota_status,
            YearQuotaGateStatus.NO_YEAR_SCHEME,
        )
        self.assertFalse(assessment.blocked_by_observed_year_gate)
        self.assertEqual(
            assessment.obtainability.status,
            ObtainabilityStatus.UNMEASURED,
        )
        self.assertIsNone(assessment.obtainability.point)

    def test_nonzero_scheme_with_zero_freshman_quota_is_exact_gate_block(self):
        rows = {
            "ECO2102-01-00": {
                "sy1PercpCnt": 0,
                "sy2PercpCnt": 35,
                "sy3PercpCnt": 15,
                "sy4PercpCnt": 9,
                "sy5PercpCnt": 0,
                "sy6PercpCnt": 0,
            }
        }
        assessment = assess_freshman_registration("ECO2102-01-00", rows)

        self.assertEqual(
            assessment.year_quota_status,
            YearQuotaGateStatus.FRESHMAN_BLOCKED_BY_SCHEME,
        )
        self.assertTrue(assessment.blocked_by_observed_year_gate)
        self.assertEqual(assessment.obtainability.status, ObtainabilityStatus.EXACT)
        self.assertEqual(assessment.obtainability.point, 0.0)

    def test_positive_freshman_quota_does_not_become_success_probability(self):
        rows = {
            "TEST1001-01-00": {
                "sy1PercpCnt": 20,
                "sy2PercpCnt": 10,
                "sy3PercpCnt": 0,
                "sy4PercpCnt": 0,
                "sy5PercpCnt": 0,
                "sy6PercpCnt": 0,
            }
        }
        assessment = assess_freshman_registration("TEST1001-01-00", rows)

        self.assertEqual(
            assessment.year_quota_status,
            YearQuotaGateStatus.FRESHMAN_ALLOWED_BY_SCHEME,
        )
        self.assertEqual(assessment.freshman_quota, 20)
        self.assertEqual(
            assessment.obtainability.status,
            ObtainabilityStatus.UNMEASURED,
        )
        self.assertFalse(assessment.obtainability_is_known)

    def test_missing_section_row_is_unknown_not_success(self):
        assessment = assess_freshman_registration("MISSING-01-00", {})

        self.assertEqual(
            assessment.year_quota_status,
            YearQuotaGateStatus.NO_OBSERVATION,
        )
        self.assertEqual(
            assessment.obtainability.status,
            ObtainabilityStatus.UNMEASURED,
        )
        self.assertIsNone(assessment.obtainability.point)

    def test_invalid_quota_is_rejected(self):
        rows = {
            "BAD-01-00": {
                "sy1PercpCnt": "not-a-number",
                "sy2PercpCnt": 1,
            }
        }
        with self.assertRaises(RegistrationEvidenceError):
            assess_freshman_registration("BAD-01-00", rows)


class MileageEvidenceTests(unittest.TestCase):
    def test_applicant_statistics_are_preserved_without_win_probability(self):
        row = {
            "subjtnb": "ECO1103",
            "subjtnbNo": "ECO1103-07-00",
            "syy": "2026",
            "smtDivCd": "20",
            "campsDivNm": "국제",
            "cnt": 4,
            "minMlg": 12,
            "avgMlg": 12,
            "maxMlg": 12,
            "usePosblMaxMlgVal": 12,
        }
        observation = historical_mileage_observation_from_row(
            row,
            source_id="mileage_history.json:0",
        )

        self.assertEqual(observation.course_code, "ECO1103")
        self.assertEqual(observation.section_id, "ECO1103-07-00")
        self.assertEqual(observation.applicant_count, 4)
        self.assertEqual(observation.min_bid, 12.0)
        self.assertEqual(observation.average_bid, 12.0)
        self.assertEqual(observation.max_bid, 12.0)
        self.assertEqual(observation.course_bid_ceiling, 12.0)
        self.assertFalse(hasattr(observation, "win_probability"))

    def test_course_filter_returns_only_requested_historical_signals(self):
        rows = [
            {"subjtnb": "A", "subjtnbNo": "A-01-00", "cnt": 1},
            {"subjtnb": "B", "subjtnbNo": "B-01-00", "cnt": 2},
            {"subjtnb": "A", "subjtnbNo": "A-02-00", "cnt": 3},
        ]
        observations = mileage_evidence_for_course("A", rows)
        self.assertEqual([item.section_id for item in observations], ["A-01-00", "A-02-00"])

    def test_inconsistent_applicant_summary_is_rejected(self):
        row = {
            "subjtnb": "BAD",
            "subjtnbNo": "BAD-01-00",
            "minMlg": 10,
            "avgMlg": 8,
            "maxMlg": 12,
        }
        with self.assertRaises(RegistrationEvidenceError):
            historical_mileage_observation_from_row(row, source_id="bad")


if __name__ == "__main__":
    unittest.main()
