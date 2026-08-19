import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.catalog import ingest_catalog  # noqa: E402
from timetable_optimizer.fall_universe import (  # noqa: E402
    FallHardExclusionEvidence,
    FallSearchScope,
    FallUniverseError,
    FallUniverseStatus,
    build_fall_section_universe,
)


def row(section_id="A-01", course_code="A", **overrides):
    base = {
        "subjtnbCorsePrcts": section_id,
        "subjtnb": course_code,
        "subjtEngNm": course_code,
        "subjtNm": course_code,
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
        "lctreTimeNm": "화3",
        "lecrmNm": "강의실A",
        "subjtClNm": "대면",
    }
    base.update(overrides)
    return base


class FallSearchScopeTests(unittest.TestCase):
    def test_explicit_subset_requires_provenance(self):
        with self.assertRaises(FallUniverseError):
            FallSearchScope.explicit_subset({"A-01"}, source_id="")

    def test_full_catalog_cannot_smuggle_a_subset(self):
        with self.assertRaises(FallUniverseError):
            FallSearchScope(
                kind=FallSearchScope.full_catalog().kind,
                section_ids=frozenset({"A-01"}),
            )


class FallSectionUniverseTests(unittest.TestCase):
    def test_full_catalog_excludes_only_explicit_cancellation_by_default(self):
        snapshot = ingest_catalog(
            [
                row("A-01", "A"),
                row("B-01", "B", rmvlcYn="1", rmvlcYnNm="폐강"),
                # These were classes of legacy pre-search filters.  The new universe layer
                # does not infer a hard exclusion from either fact by itself.
                row("C-01", "C", atntnMattrDesc="Senior students only"),
                row("D-01", "D", cdt=0),
            ],
            source_name="fixture",
            term="2026F",
        )
        universe = build_fall_section_universe("full", snapshot)

        self.assertEqual(universe.status, FallUniverseStatus.GLOBAL_COMPLETE)
        self.assertTrue(universe.eligible_for_global_optimum_claim)
        self.assertEqual(
            universe.searchable_section_ids,
            frozenset({"A-01", "C-01", "D-01"}),
        )
        self.assertEqual(len(universe.hard_exclusions), 1)
        self.assertEqual(universe.hard_exclusions[0].section_id, "B-01")
        self.assertEqual(universe.hard_exclusions[0].code, "canonical_cancelled")

    def test_unknown_cancellation_is_not_treated_as_cancelled(self):
        raw = row("A-01", "A")
        raw.pop("rmvlcYn")
        raw.pop("rmvlcYnNm")
        snapshot = ingest_catalog([raw])
        universe = build_fall_section_universe("full", snapshot)

        self.assertIn("A-01", universe.searchable_section_ids)
        self.assertFalse(universe.hard_exclusions)

    def test_explicit_subset_is_exact_within_scope_but_never_global(self):
        snapshot = ingest_catalog([row("A-01", "A"), row("B-01", "B")])
        universe = build_fall_section_universe(
            "shortlist",
            snapshot,
            scope=FallSearchScope.explicit_subset(
                {"A-01"},
                source_id="user:diagnostic-shortlist",
            ),
        )

        self.assertEqual(universe.status, FallUniverseStatus.SCOPED_COMPLETE)
        self.assertTrue(universe.exact_scope_coverage)
        self.assertFalse(universe.global_catalogue_coverage)
        self.assertFalse(universe.eligible_for_global_optimum_claim)
        self.assertEqual(universe.searchable_section_ids, frozenset({"A-01"}))
        self.assertEqual(universe.scoped_out_section_ids, frozenset({"B-01"}))

    def test_unresolved_physical_section_blocks_full_catalog_claim(self):
        snapshot = ingest_catalog(
            [
                row("A-01", "A", cgprfNm="Professor A"),
                row("A-01", "A", cgprfNm="Professor B"),
            ]
        )
        universe = build_fall_section_universe("full", snapshot)

        self.assertEqual(universe.status, FallUniverseStatus.INPUT_BLOCKED)
        self.assertFalse(universe.global_catalogue_coverage)
        self.assertIn(
            "physical_section_unresolved",
            {unknown.code for unknown in universe.global_catalogue_unknowns},
        )

    def test_scoped_search_can_leave_unresolved_catalogue_material_outside_scope(self):
        snapshot = ingest_catalog(
            [
                row("A-01", "A"),
                row("B-01", "B", cgprfNm="Professor A"),
                row("B-01", "B", cgprfNm="Professor B"),
            ]
        )
        universe = build_fall_section_universe(
            "diagnostic",
            snapshot,
            scope=FallSearchScope.explicit_subset(
                {"A-01"},
                source_id="test:scope",
            ),
        )

        self.assertEqual(universe.status, FallUniverseStatus.SCOPED_COMPLETE)
        self.assertFalse(universe.scope_unknowns)
        self.assertTrue(universe.global_catalogue_unknowns)
        self.assertFalse(universe.eligible_for_global_optimum_claim)

    def test_requesting_unresolved_physical_section_blocks_that_scope(self):
        snapshot = ingest_catalog(
            [
                row("B-01", "B", cgprfNm="Professor A"),
                row("B-01", "B", cgprfNm="Professor B"),
            ]
        )
        universe = build_fall_section_universe(
            "bad-scope",
            snapshot,
            scope=FallSearchScope.explicit_subset(
                {"B-01"},
                source_id="test:scope",
            ),
        )

        self.assertEqual(universe.status, FallUniverseStatus.INPUT_BLOCKED)
        self.assertIn(
            "scope_physical_section_unresolved",
            {unknown.code for unknown in universe.scope_unknowns},
        )

    def test_missing_identity_source_row_blocks_global_catalogue_coverage(self):
        snapshot = ingest_catalog([row("", "A")])
        universe = build_fall_section_universe("full", snapshot)

        self.assertEqual(universe.status, FallUniverseStatus.INPUT_BLOCKED)
        self.assertIn(
            "source_observation_unidentified",
            {unknown.code for unknown in universe.global_catalogue_unknowns},
        )

    def test_missing_named_scope_section_is_unknown_not_silently_absent(self):
        snapshot = ingest_catalog([row("A-01", "A")])
        universe = build_fall_section_universe(
            "scope",
            snapshot,
            scope=FallSearchScope.explicit_subset(
                {"MISSING-01"},
                source_id="user:shortlist",
            ),
        )

        self.assertEqual(universe.status, FallUniverseStatus.INPUT_BLOCKED)
        self.assertIn(
            "scope_section_missing",
            {unknown.code for unknown in universe.scope_unknowns},
        )

    def test_external_hard_exclusion_requires_known_identity_and_provenance(self):
        with self.assertRaises(FallUniverseError):
            FallHardExclusionEvidence(
                section_id="A-01",
                code="eligibility",
                reason="documented gate",
                source_id="",
            )

        snapshot = ingest_catalog([row("A-01", "A")])
        with self.assertRaises(FallUniverseError):
            build_fall_section_universe(
                "full",
                snapshot,
                hard_exclusions=(
                    FallHardExclusionEvidence(
                        section_id="MISSING-01",
                        code="eligibility",
                        reason="documented gate",
                        source_id="registrar:test",
                    ),
                ),
            )

    def test_sourced_external_hard_exclusion_is_auditable(self):
        snapshot = ingest_catalog([row("A-01", "A"), row("B-01", "B")])
        exclusion = FallHardExclusionEvidence(
            section_id="B-01",
            code="documented_eligibility_gate",
            reason="official rule excludes this student from the section",
            source_id="registrar:eligibility:B-01",
        )
        universe = build_fall_section_universe(
            "full",
            snapshot,
            hard_exclusions=(exclusion,),
        )

        self.assertEqual(universe.status, FallUniverseStatus.GLOBAL_COMPLETE)
        self.assertEqual(universe.searchable_section_ids, frozenset({"A-01"}))
        self.assertEqual(universe.hard_exclusions, (exclusion,))


if __name__ == "__main__":
    unittest.main()
