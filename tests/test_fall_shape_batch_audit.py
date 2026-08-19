import unittest

from timetable_optimizer.fall_candidate_sets import (
    FallCandidateLoadFacts,
    FallCandidateSet,
)
from timetable_optimizer.fall_shape_batch_audit import (
    FallShapeBatchAuditError,
    audit_candidate_shape_batch,
)
from timetable_optimizer.sections import ParsedSchedule, section_from_raw


def row(section_id, time):
    return {
        "subjtnbCorsePrcts": section_id,
        "subjtnb": section_id.split("-")[0],
        "subjtEngNm": "TEST COURSE",
        "subjtNm": "테스트",
        "campsDivNm": "국제",
        "cdt": 3,
        "cgprfNm": "Professor",
        "srclnLctreLangDivCd": "10",
        "atntnMattrDesc": "",
        "gradeEvlMthdDivNm": "절대평가",
        "rmvlcYn": "0",
        "rmvlcYnNm": " ",
        "lctreTimeNm": time,
        "lecrmNm": "강의실A" if time else "",
        "subjtClNm": "대면",
    }


def candidate(section_id, time, credits=3.0):
    item = section_from_raw(row(section_id, time))
    unresolved = () if isinstance(item.schedule, ParsedSchedule) else (item.section_id,)
    return FallCandidateSet(
        section_ids=(item.section_id,),
        sections=(item,),
        load=FallCandidateLoadFacts(
            known_total_credits=credits,
            known_ordinary_credits=credits,
            known_chapel_credits=0.0,
            unknown_credit_section_ids=(),
        ),
        unresolved_schedule_section_ids=unresolved,
    )


class FallShapeBatchAuditTests(unittest.TestCase):
    def test_exposure_families_are_counted_without_claiming_representativeness(self):
        items = (
            candidate("LONG1001-01-00", "화3,4,5,6,7"),
            candidate("MID1001-01-00", "수3"),
        )
        result = audit_candidate_shape_batch(items)
        self.assertEqual(result.candidates_seen, 2)
        self.assertEqual(result.candidates_evaluated, 2)
        self.assertFalse(result.representative)
        self.assertFalse(result.proof_evidence)
        self.assertGreater(result.family_activation_counts["long_fixed_run_shape"], 0)
        self.assertGreater(
            result.family_activation_counts["weekend_attached_run_shape"], 0
        )
        self.assertGreater(result.family_activation_counts["friday_event_value"], 0)
        self.assertIn("long_fixed_run_delta_5", result.state_activation_counts)
        self.assertGreater(result.maximum_archival_spread, 0.0)
        self.assertFalse(result.uncovered_archival_state_dimensions)

    def test_credit_floor_is_diagnostic_filter_not_candidate_mutation(self):
        low = candidate("LOW1001-01-00", "화3", credits=3.0)
        high = candidate("HIGH1001-01-00", "화4", credits=18.0)
        result = audit_candidate_shape_batch(
            (low, high), minimum_known_ordinary_credits=12.0
        )
        self.assertEqual(result.candidates_seen, 2)
        self.assertEqual(result.candidates_below_credit_floor, 1)
        self.assertEqual(result.candidates_evaluated, 1)
        self.assertEqual(result.minimum_known_ordinary_credits, 12.0)

    def test_nonparsed_schedule_is_visible_and_skipped(self):
        unresolved = candidate("UNK1001-01-00", "")
        result = audit_candidate_shape_batch((unresolved,))
        self.assertEqual(result.candidates_seen, 1)
        self.assertEqual(result.candidates_skipped_unresolved_schedule, 1)
        self.assertEqual(result.candidates_evaluated, 0)

    def test_invalid_credit_floor_is_rejected(self):
        with self.assertRaises(FallShapeBatchAuditError):
            audit_candidate_shape_batch((), minimum_known_ordinary_credits=-1.0)


if __name__ == "__main__":
    unittest.main()
