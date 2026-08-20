import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.history import ingest_history, load_history_file  # noqa: E402
from timetable_optimizer.sections import (  # noqa: E402
    NoListedSchedule,
    ParsedSchedule,
    UnresolvedSchedule,
    section_from_raw,
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


class HistoricalIngestionUnitTests(unittest.TestCase):
    def test_terms_are_reconciled_independently(self):
        sid = "TEST1001-01-00"
        history = ingest_history(
            {
                "2024-1": [row(sid, cgprfNm="Professor A")],
                "2025-1": [row(sid, cgprfNm="Professor B")],
            }
        )
        self.assertEqual(history.term_labels, ("2024-1", "2025-1"))
        self.assertTrue(history.term("2024-1").record_for(sid).usable)
        self.assertTrue(history.term("2025-1").record_for(sid).usable)
        self.assertNotEqual(
            history.term("2024-1").record_for(sid).section.professor,
            history.term("2025-1").record_for(sid).section.professor,
        )

    def test_history_uses_schedule_statuses_instead_of_dropping_rows(self):
        history = ingest_history(
            {
                "2024-1": [
                    row("TEST1001-01-00"),
                    row("TEST1002-01-00", lctreTimeNm="", lecrmNm=""),
                    row(
                        "TEST1003-01-00",
                        lctreTimeNm="월3,4/수3",
                        lecrmNm="강의실A",
                    ),
                ]
            }
        )
        catalog = history.term("2024-1")
        self.assertEqual(len(catalog.observations), 3)
        self.assertEqual(len(catalog.physical_sections), 3)
        schedules = [record.section.schedule for record in catalog.physical_sections]
        self.assertTrue(any(isinstance(s, ParsedSchedule) for s in schedules))
        self.assertTrue(any(isinstance(s, NoListedSchedule) for s in schedules))
        self.assertTrue(any(isinstance(s, UnresolvedSchedule) for s in schedules))

        summary = history.summary()
        self.assertEqual(summary.parsed_schedule_count, 1)
        self.assertEqual(summary.no_listed_schedule_count, 1)
        self.assertEqual(summary.unresolved_schedule_count, 1)

    def test_every_observation_records_its_term_and_historical_source_kind(self):
        history = ingest_history({"2024-2": [row()]}, source_name="past_terms.json")
        observation = history.term("2024-2").observations[0]
        self.assertEqual(observation.source.term, "2024-2")
        self.assertEqual(observation.source.source_kind, "historical_portal_catalog")
        self.assertTrue(observation.source.source_fingerprint)

    def test_ingestion_is_deterministic(self):
        source = {"2024-1": [row()]}
        self.assertEqual(ingest_history(source), ingest_history(source))


class RealHistoricalCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = ROOT / "past_terms.json"
        with cls.path.open(encoding="utf-8") as fh:
            cls.raw_terms = json.load(fh)
        cls.history = load_history_file(cls.path)

    def test_every_term_is_present(self):
        self.assertEqual(self.history.term_labels, tuple(sorted(self.raw_terms)))

    def test_every_historical_source_row_is_preserved(self):
        raw_count = sum(len(rows) for rows in self.raw_terms.values())
        self.assertEqual(self.history.summary().observation_count, raw_count)

    def test_each_term_preserves_its_own_row_count_and_source_label(self):
        for term, rows in self.raw_terms.items():
            catalog = self.history.term(term)
            self.assertIsNotNone(catalog)
            self.assertEqual(len(catalog.observations), len(rows))
            self.assertTrue(
                all(observation.source.term == term for observation in catalog.observations)
            )

    def test_current_and_history_use_the_same_section_parser(self):
        for term in sorted(self.raw_terms):
            catalog = self.history.term(term)
            for index, raw in enumerate(self.raw_terms[term]):
                try:
                    expected = section_from_raw(raw)
                except Exception:
                    continue
                observation = catalog.observations[index]
                self.assertEqual(observation.section, expected)
                return
        self.fail("no parseable historical source row found")

    def test_all_parsed_historical_schedules_obey_three_mask_invariant(self):
        seen = 0
        for historical_term in self.history.terms:
            for section in historical_term.catalog.sections:
                if not isinstance(section.schedule, ParsedSchedule):
                    continue
                seen += 1
                self.assertEqual(
                    section.schedule.presence_mask & ~section.schedule.fixed_mask,
                    0,
                )
                self.assertEqual(
                    section.schedule.fixed_mask & ~section.schedule.conflict_mask,
                    0,
                )
        self.assertGreater(seen, 0)

    def test_source_campuses_are_not_filtered_before_parsing(self):
        raw_campuses = {
            str(raw.get("campsDivNm") or "")
            for rows in self.raw_terms.values()
            for raw in rows
            if str(raw.get("campsDivNm") or "")
        }
        observation_campuses = {
            str(observation.raw.get("campsDivNm") or "")
            for historical_term in self.history.terms
            for observation in historical_term.catalog.observations
            if str(observation.raw.get("campsDivNm") or "")
        }
        self.assertEqual(observation_campuses, raw_campuses)

    def test_file_fingerprint_is_stable_and_present(self):
        again = load_history_file(self.path)
        self.assertTrue(self.history.source_fingerprint)
        self.assertEqual(self.history.source_fingerprint, again.source_fingerprint)
        self.assertEqual(self.history, again)


if __name__ == "__main__":
    unittest.main()
