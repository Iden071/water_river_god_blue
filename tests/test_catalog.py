import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.catalog import (  # noqa: E402
    IssueCode,
    ListingStatus,
    ObservationStatus,
    PhysicalStatus,
    ReconciliationKind,
    ingest_catalog,
    load_catalog_files,
)
from timetable_optimizer.sections import (  # noqa: E402
    NoListedSchedule,
    ParsedSchedule,
    UnresolvedSchedule,
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


class CatalogObservationTests(unittest.TestCase):
    def test_every_source_row_is_preserved_as_an_observation(self):
        rows = [
            row("TEST1001-01-00"),
            row("TEST1002-01-00", lctreTimeNm="월3,4/수3", lecrmNm="강의실A"),
        ]
        snapshot = ingest_catalog(rows)
        self.assertEqual(len(snapshot.observations), len(rows))
        self.assertTrue(all(o.status is ObservationStatus.PARSED for o in snapshot.observations))
        self.assertIsInstance(snapshot.observations[1].section.schedule, UnresolvedSchedule)

    def test_raw_observation_is_detached_from_later_input_mutation(self):
        raw = row()
        snapshot = ingest_catalog([raw])
        raw["cgprfNm"] = "Changed later"
        self.assertEqual(snapshot.observations[0].raw["cgprfNm"], "Professor")

    def test_missing_identity_preserves_observation_but_not_fake_physical_section(self):
        raw = row()
        raw["subjtnbCorsePrcts"] = ""
        snapshot = ingest_catalog([raw])
        self.assertEqual(len(snapshot.observations), 1)
        self.assertEqual(snapshot.observations[0].status, ObservationStatus.UNRESOLVED)
        self.assertEqual(len(snapshot.physical_sections), 0)


class ReconciliationTests(unittest.TestCase):
    def test_identical_duplicate_observations_are_coalesced_with_both_provenances(self):
        snapshot = ingest_catalog([row(), row()])
        self.assertEqual(len(snapshot.observations), 2)
        self.assertEqual(len(snapshot.physical_sections), 1)
        record = snapshot.record_for("TEST1001-01-00")
        self.assertEqual(record.status, PhysicalStatus.OK)
        self.assertEqual(record.reconciliation, ReconciliationKind.COALESCED_IDENTICAL)
        self.assertEqual(record.observation_indexes, (0, 1))
        self.assertEqual(len(snapshot.sections), 1)

    def test_contradictory_duplicate_observations_are_not_first_or_last_write_wins(self):
        snapshot = ingest_catalog([row(), row(cgprfNm="Other Professor")])
        record = snapshot.record_for("TEST1001-01-00")
        self.assertEqual(record.status, PhysicalStatus.UNRESOLVED)
        self.assertEqual(record.reconciliation, ReconciliationKind.CONFLICT)
        self.assertIsNone(record.section)
        self.assertTrue(any(i.code is IssueCode.DUPLICATE_SECTION_CONFLICT for i in record.issues))
        self.assertEqual(len(snapshot.sections), 0)


class ListingOverlayTests(unittest.TestCase):
    def test_program_category_is_separate_from_physical_catalogue_category(self):
        sid = "TEST1001-01-00"
        snapshot = ingest_catalog(
            [row(sid, subsrtDivNm="MB")],
            program_listings={sid: {"cat": "ME", "hy": "2", "camps": "신촌"}},
        )
        record = snapshot.record_for(sid)
        listing = snapshot.listings_for(sid, program="QRM")[0]
        self.assertTrue(record.usable)
        self.assertEqual(record.section.catalogue_category, "MB")
        self.assertEqual(listing.listed_category, "ME")
        self.assertEqual(listing.year_label, "2")
        self.assertEqual(listing.campus, "신촌")

    def test_invalid_program_listing_does_not_poison_valid_physical_section(self):
        sid = "TEST1001-01-00"
        snapshot = ingest_catalog([row(sid)], program_listings={sid: {"cat": ""}})
        record = snapshot.record_for(sid)
        listing = snapshot.listings_for(sid)[0]
        self.assertTrue(record.usable)
        self.assertEqual(listing.status, ListingStatus.UNRESOLVED)
        self.assertTrue(any(i.code is IssueCode.INVALID_LISTING for i in listing.issues))

    def test_orphan_listing_is_reported_without_creating_a_fake_physical_section(self):
        snapshot = ingest_catalog(
            [row()],
            program_listings={"OTHER1001-01-00": {"cat": "ME"}},
        )
        self.assertEqual(len(snapshot.physical_sections), 1)
        self.assertEqual(len(snapshot.issues), 1)
        self.assertEqual(snapshot.issues[0].code, IssueCode.ORPHAN_LISTING)


class ParserParityAndPurityTests(unittest.TestCase):
    def test_term_provenance_changes_but_parser_output_does_not(self):
        spring = ingest_catalog([row()], term="2025-1")
        fall = ingest_catalog([row()], term="2026-2")
        self.assertEqual(spring.sections[0], fall.sections[0])
        self.assertNotEqual(
            spring.observations[0].source.term,
            fall.observations[0].source.term,
        )

    def test_ingestion_is_deterministic_for_identical_inputs(self):
        rows = [row(), row("TEST1002-01-00", campsDivNm="신촌")]
        first = ingest_catalog(rows, source_name="fixture", term="2026-2")
        second = ingest_catalog(rows, source_name="fixture", term="2026-2")
        self.assertEqual(first, second)

    def test_importing_package_does_not_create_files_in_working_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["PYTHONPATH"] = str(ROOT / "src")
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            subprocess.run(
                [sys.executable, "-c", "import timetable_optimizer"],
                cwd=tmp,
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(list(Path(tmp).iterdir()), [])


class RealFallCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw_path = ROOT / "raw_2026F.json"
        cls.qrm_path = ROOT / "qrm_listings.json"
        with cls.raw_path.open(encoding="utf-8") as fh:
            cls.raw_rows = json.load(fh)
        cls.snapshot = load_catalog_files(
            cls.raw_path,
            program_listings_path=cls.qrm_path,
            listing_program="QRM",
            term="2026-2",
        )

    def test_ingestion_is_lossless_at_source_observation_boundary(self):
        self.assertEqual(len(self.snapshot.observations), len(self.raw_rows))

    def test_both_campuses_survive_same_ingestion_path(self):
        campuses = {section.campus for section in self.snapshot.sections}
        self.assertIn("국제", campuses)
        self.assertIn("신촌", campuses)

    def test_known_blended_section_has_correct_three_mask_semantics(self):
        record = self.snapshot.record_for("YCA1102-10-00")
        self.assertIsNotNone(record)
        self.assertTrue(record.usable, record.issues)
        section = record.section
        self.assertIsInstance(section.schedule, ParsedSchedule)
        self.assertEqual(section.conflict_mask.bit_count(), 3)
        self.assertEqual(section.presence_mask.bit_count(), 2)
        self.assertEqual(section.fixed_mask.bit_count(), 2)

    def test_no_time_rows_are_preserved_as_no_listed_schedule_not_zero_masks(self):
        raw_no_time = sum(
            1 for raw in self.raw_rows if not str(raw.get("lctreTimeNm") or "").strip()
        )
        ingested_no_time = sum(
            1
            for observation in self.snapshot.observations
            if observation.section is not None
            and isinstance(observation.section.schedule, NoListedSchedule)
        )
        self.assertEqual(ingested_no_time, raw_no_time)

    def test_explicit_cancellations_survive_as_source_facts(self):
        raw_cancelled = sum(
            1
            for raw in self.raw_rows
            if str(raw.get("rmvlcYnNm") or "").strip() == "폐강"
            or str(raw.get("rmvlcYn") or "").strip() == "1"
        )
        parsed_cancelled = sum(
            1
            for observation in self.snapshot.observations
            if observation.section is not None and observation.section.cancelled is True
        )
        self.assertEqual(parsed_cancelled, raw_cancelled)

    def test_source_file_fingerprint_is_recorded(self):
        self.assertEqual(len(self.snapshot.source_fingerprint), 64)
        self.assertTrue(all(o.source.source_fingerprint == self.snapshot.source_fingerprint for o in self.snapshot.observations))


if __name__ == "__main__":
    unittest.main()
