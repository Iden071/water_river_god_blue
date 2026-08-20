import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.sections import (  # noqa: E402
    DeliveryKind,
    NoListedSchedule,
    ParsedSchedule,
    Section,
    UnresolvedSchedule,
    section_from_raw,
    segment_blocks,
)


def row(**overrides):
    base = {
        "subjtnbCorsePrcts": "TEST1001-01-00",
        "subjtnb": "TEST1001",
        "subjtEngNm": "TEST COURSE",
        "subjtNm": "테스트",
        "campsDivNm": "국제",
        "cdt": 3,
        "cgprfNm": "Professor",
        "estblDeprtNm": "UIC",
        "hy": "1",
        "srclnLctreLangDivCd": "10",
        "subsrtDivNm": "CC",
        "atntnMattrDesc": "",
        "gradeEvlMthdDivNm": "절대평가",
        "rmvlcYn": "0",
        "rmvlcYnNm": " ",
        "lctreTimeNm": "월3,4",
        "lecrmNm": "강의실A",
        "subjtClNm": "대면",
    }
    base.update(overrides)
    return base


class SegmentParserTests(unittest.TestCase):
    def test_parenthesized_periods_are_preserved(self):
        self.assertEqual(
            segment_blocks("월3,4,수3(수4)"),
            frozenset({(0, 3), (0, 4), (2, 3), (2, 4)}),
        )

    def test_parser_does_not_join_digits_across_commas(self):
        blocks = segment_blocks("화1,2,목1(목2)")
        self.assertIn((3, 1), blocks)
        self.assertIn((3, 2), blocks)
        self.assertNotIn((3, 12), blocks)


class SectionScheduleTests(unittest.TestCase):
    def test_in_person_occupies_all_three_masks(self):
        sec = section_from_raw(row())
        self.assertIsInstance(sec.schedule, ParsedSchedule)
        self.assertTrue(sec.conflict_mask)
        self.assertEqual(sec.conflict_mask, sec.presence_mask)
        self.assertEqual(sec.conflict_mask, sec.fixed_mask)
        self.assertEqual(sec.delivery_kinds, (DeliveryKind.IN_PERSON,))

    def test_live_plus_recorded_block_has_distinct_fixed_mask(self):
        sec = section_from_raw(
            row(
                lctreTimeNm="월7,8/수7",
                lecrmNm="실시간온라인/동영상(중복수강불가)",
                subjtClNm="비대면(실시간+동영상)",
            )
        )
        self.assertEqual(
            sec.delivery_kinds,
            (DeliveryKind.LIVE_ONLINE, DeliveryKind.VIDEO_BLOCK),
        )
        self.assertEqual(sec.conflict_mask.bit_count(), 3)
        self.assertEqual(sec.presence_mask, 0)
        self.assertEqual(sec.fixed_mask.bit_count(), 2)

    def test_freely_overlappable_video_occupies_no_mask_but_is_still_parsed(self):
        sec = section_from_raw(
            row(lctreTimeNm="목4", lecrmNm="동영상콘텐츠", subjtClNm="비대면")
        )
        self.assertIsInstance(sec.schedule, ParsedSchedule)
        self.assertEqual(sec.delivery_kinds, (DeliveryKind.VIDEO_FREE,))
        self.assertEqual(sec.conflict_mask, 0)
        self.assertEqual(sec.presence_mask, 0)
        self.assertEqual(sec.fixed_mask, 0)

    def test_no_listed_time_is_not_a_zero_mask_schedule(self):
        sec = section_from_raw(row(lctreTimeNm="", lecrmNm=""))
        self.assertIsInstance(sec.schedule, NoListedSchedule)
        self.assertIsNone(sec.conflict_mask)
        self.assertIsNone(sec.presence_mask)
        self.assertIsNone(sec.fixed_mask)
        self.assertIsNone(sec.delivery_kinds)

    def test_segment_mismatch_becomes_unresolved_not_guessed(self):
        sec = section_from_raw(row(lctreTimeNm="월3,4/수3", lecrmNm="실시간온라인"))
        self.assertIsInstance(sec.schedule, UnresolvedSchedule)
        self.assertIsNone(sec.conflict_mask)
        self.assertIn("mismatch", sec.schedule.reason)

    def test_blank_delivery_metadata_becomes_unresolved_not_in_person(self):
        sec = section_from_raw(row(lctreTimeNm="월3,4", lecrmNm=""))
        self.assertIsInstance(sec.schedule, UnresolvedSchedule)
        self.assertIsNone(sec.presence_mask)

    def test_nonblank_but_unparseable_time_is_unresolved_not_no_listed_schedule(self):
        sec = section_from_raw(row(lctreTimeNm="미정", lecrmNm="강의실A"))
        self.assertIsInstance(sec.schedule, UnresolvedSchedule)

    def test_mask_subset_invariant_holds_for_all_delivery_kinds(self):
        examples = [
            row(lecrmNm="강의실A"),
            row(lecrmNm="실시간온라인"),
            row(lecrmNm="동영상(중복수강불가)"),
            row(lecrmNm="동영상콘텐츠"),
        ]
        for raw in examples:
            with self.subTest(room=raw["lecrmNm"]):
                sec = section_from_raw(raw)
                self.assertIsInstance(sec.schedule, ParsedSchedule)
                self.assertEqual(sec.presence_mask & ~sec.fixed_mask, 0)
                self.assertEqual(sec.fixed_mask & ~sec.conflict_mask, 0)

    def test_both_campuses_use_same_section_representation(self):
        international = section_from_raw(row(campsDivNm="국제"))
        sinchon = section_from_raw(row(campsDivNm="신촌"))
        self.assertIsInstance(international, Section)
        self.assertIsInstance(sinchon, Section)
        self.assertEqual(type(international.schedule), type(sinchon.schedule))


class SourceFactTests(unittest.TestCase):
    def test_explicit_cancellation_true_and_false_are_preserved(self):
        self.assertTrue(section_from_raw(row(rmvlcYn="1", rmvlcYnNm="폐강")).cancelled)
        self.assertFalse(section_from_raw(row(rmvlcYn="0", rmvlcYnNm=" ")).cancelled)

    def test_missing_cancellation_evidence_is_unknown(self):
        raw = row()
        raw.pop("rmvlcYn")
        raw.pop("rmvlcYnNm")
        self.assertIsNone(section_from_raw(raw).cancelled)

    def test_missing_credit_is_unknown_not_zero(self):
        self.assertIsNone(section_from_raw(row(cdt=None)).credits)

    def test_canonical_section_contains_no_downstream_model_decisions(self):
        forbidden = {
            "eligible",
            "fulfills_ME",
            "fulfills_MR",
            "professor_utility",
            "difficulty",
            "future_probability",
            "score",
            "should_take",
        }
        self.assertFalse(forbidden & set(Section.__dataclass_fields__))


if __name__ == "__main__":
    unittest.main()
