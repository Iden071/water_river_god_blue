import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.catalog import (  # noqa: E402
    IssueCode,
    RecordStatus,
    ingest_catalog,
    load_catalog_files,
)


def row(section_id="TEST1001-01-00", **overrides):
    base = {
        "subjtnbCorsePrcts": section_id,
        "subjtnb": section_id.split("-")[0],
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


class CatalogIngestionUnitTests(unittest.TestCase):
    def test_every_source_row_is_preserved(self):
        rows = [
            row("TEST1001-01-00"),
            row("TEST1002-01-00", lctreTimeNm="월3,4/수3", lecrmNm="강의실A"),
        ]
        snap = ingest_catalog(rows)
        self.assertEqual(len(snap.records), len(rows))
        self.assertEqual(len(snap.sections), 1)
        self.assertEqual(len(snap.unresolved), 1)
        self.assertEqual(snap.unresolved[0].issues[0].code, IssueCode.PARSE_ERROR)

    def test_duplicate_section_ids_are_not_resolved_by_overwrite(self):
        snap = ingest_catalog([row(), row(cgprfNm="Other Professor")])
        self.assertEqual(len(snap.records), 2)
        self.assertEqual(len(snap.sections), 0)
        self.assertTrue(all(r.status is RecordStatus.UNRESOLVED for r in snap.records))
        self.assertTrue(
            all(any(i.code is IssueCode.DUPLICATE_SECTION_ID for i in r.issues) for r in snap.records)
        )

    def test_qrm_category_is_metadata_not_generic_category_mutation(self):
        sid = "TEST1001-01-00"
        snap = ingest_catalog([row(sid, subsrtDivNm="MB")], qrm_listings={sid: {"cat": "ME"}})
        record = snap.record_for(sid)
        self.assertIsNotNone(record)
        self.assertTrue(record.usable)
        self.assertEqual(record.section.category, "MB")
        self.assertEqual(record.qrm_category, "ME")

    def test_orphan_qrm_listing_is_reported(self):
        snap = ingest_catalog([row()], qrm_listings={"OTHER1001-01-00": {"cat": "ME"}})
        self.assertEqual(len(snap.issues), 1)
        self.assertEqual(snap.issues[0].code, IssueCode.ORPHAN_QRM_LISTING)


class RealFallCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw_path = ROOT / "raw_2026F.json"
        cls.qrm_path = ROOT / "qrm_listings.json"
        with cls.raw_path.open(encoding="utf-8") as fh:
            cls.raw_rows = json.load(fh)
        cls.snapshot = load_catalog_files(cls.raw_path, qrm_listings_path=cls.qrm_path)

    def test_ingestion_is_lossless_at_row_boundary(self):
        self.assertEqual(len(self.snapshot.records), len(self.raw_rows))
        self.assertEqual(
            len(self.snapshot.sections) + len(self.snapshot.unresolved),
            len(self.raw_rows),
        )

    def test_both_campuses_survive_ingestion(self):
        campuses = {section.campus for section in self.snapshot.sections}
        self.assertIn("국제", campuses)
        self.assertIn("신촌", campuses)

    def test_known_blended_section_has_correct_three_mask_semantics(self):
        record = self.snapshot.record_for("YCA1102-10-00")
        self.assertIsNotNone(record)
        self.assertTrue(record.usable, record.issues)
        section = record.section
        self.assertEqual(section.conflict_mask.bit_count(), 3)
        self.assertEqual(section.presence_mask.bit_count(), 2)
        self.assertEqual(section.fixed_mask.bit_count(), 2)

    def test_no_time_rows_are_not_lost(self):
        raw_no_time = sum(1 for row_ in self.raw_rows if not str(row_.get("lctreTimeNm") or "").strip())
        ingested_no_time = sum(
            1
            for record in self.snapshot.records
            if record.section is not None and not record.section.time_text
        )
        self.assertEqual(ingested_no_time, raw_no_time)

    def test_explicit_cancellations_survive_as_data(self):
        raw_cancelled = sum(
            1
            for row_ in self.raw_rows
            if str(row_.get("rmvlcYnNm") or "").strip() == "폐강"
            or str(row_.get("rmvlcYn") or "").strip() == "1"
        )
        parsed_cancelled = sum(
            1
            for record in self.snapshot.records
            if record.section is not None and record.section.cancelled
        )
        self.assertEqual(parsed_cancelled, raw_cancelled)


if __name__ == "__main__":
    unittest.main()
