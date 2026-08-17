import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.sections import (  # noqa: E402
    DeliveryKind,
    SegmentAlignmentError,
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


class SectionMaskTests(unittest.TestCase):
    def test_in_person_occupies_all_three_masks(self):
        sec = section_from_raw(row())
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
        # Both blocks prevent overlapping registration.
        self.assertEqual(sec.conflict_mask.bit_count(), 3)
        # Neither requires campus presence.
        self.assertEqual(sec.presence_mask, 0)
        # Only the live Monday block pins personal time.
        self.assertEqual(sec.fixed_mask.bit_count(), 2)

    def test_freely_overlappable_video_occupies_no_mask(self):
        sec = section_from_raw(
            row(lctreTimeNm="목4", lecrmNm="동영상콘텐츠", subjtClNm="비대면")
        )
        self.assertEqual(sec.delivery_kinds, (DeliveryKind.VIDEO_FREE,))
        self.assertEqual(sec.conflict_mask, 0)
        self.assertEqual(sec.presence_mask, 0)
        self.assertEqual(sec.fixed_mask, 0)

    def test_no_time_section_is_preserved(self):
        sec = section_from_raw(row(lctreTimeNm="", lecrmNm=""))
        self.assertEqual(sec.conflict_mask, 0)
        self.assertEqual(sec.presence_mask, 0)
        self.assertEqual(sec.fixed_mask, 0)
        self.assertEqual(sec.delivery_kinds, ())

    def test_both_campuses_are_accepted(self):
        sec = section_from_raw(row(campsDivNm="신촌"))
        self.assertEqual(sec.campus, "신촌")

    def test_segment_mismatch_is_not_guessed(self):
        with self.assertRaises(SegmentAlignmentError):
            section_from_raw(
                row(lctreTimeNm="월3,4/수3", lecrmNm="실시간온라인")
            )

    def test_blank_delivery_metadata_is_not_assumed_in_person(self):
        with self.assertRaises(SegmentAlignmentError):
            section_from_raw(row(lctreTimeNm="월3,4", lecrmNm=""))

    def test_cancellation_field_is_preserved(self):
        sec = section_from_raw(row(rmvlcYn="1", rmvlcYnNm="폐강"))
        self.assertTrue(sec.cancelled)


if __name__ == "__main__":
    unittest.main()
