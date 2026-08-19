import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.catalog import ingest_catalog  # noqa: E402
from timetable_optimizer.fall_candidate_sets import (  # noqa: E402
    FallCandidateSetEnumerationStatus,
    FallLoadPolicy,
    enumerate_fall_candidate_sets,
    fall2026_load_policy,
)
from timetable_optimizer.fall_universe import (  # noqa: E402
    FallSearchScope,
    build_fall_section_universe,
)


def row(
    section_id,
    course_code=None,
    *,
    time="화3",
    credits=3,
    room="강의실A",
    cancelled="0",
):
    course_code = course_code or section_id.split("-")[0]
    return {
        "subjtnbCorsePrcts": section_id,
        "subjtnb": course_code,
        "subjtEngNm": course_code,
        "subjtNm": course_code,
        "campsDivNm": "국제",
        "cdt": credits,
        "cgprfNm": "Professor",
        "estblDeprtNm": "UIC",
        "hy": "1",
        "srclnLctreLangDivCd": "10",
        "subsrtDivNm": "",
        "atntnMattrDesc": "",
        "gradeEvlMthdDivNm": "절대평가",
        "rmvlcYn": cancelled,
        "rmvlcYnNm": "폐강" if cancelled == "1" else " ",
        "lctreTimeNm": time,
        "lecrmNm": room,
        "subjtClNm": "대면",
    }


def universe(*rows, scope=None):
    snapshot = ingest_catalog(rows, source_name="fixture", term="2026F")
    return build_fall_section_universe("test-universe", snapshot, scope=scope)


class FallCandidateSetEnumerationTests(unittest.TestCase):
    def test_no_six_course_cap_is_reintroduced(self):
        rows = tuple(
            row(f"C{i}-01", f"C{i}", time=f"{'월화수목금토일'[i]}3", credits=1)
            for i in range(7)
        )
        generated = enumerate_fall_candidate_sets(
            universe(*rows),
            fall2026_load_policy(),
            max_subset_evaluations=200,
        )

        self.assertEqual(generated.status, FallCandidateSetEnumerationStatus.COMPLETE)
        self.assertEqual(generated.evaluated_subsets, 128)
        self.assertTrue(
            any(len(candidate.section_ids) == 7 for candidate in generated.candidates)
        )

    def test_known_ordinary_credit_cap_prunes_only_proven_violation(self):
        generated = enumerate_fall_candidate_sets(
            universe(
                row("A-01", "A", time="화3", credits=12),
                row("B-01", "B", time="수3", credits=11),
            ),
            fall2026_load_policy(),
        )

        ids = {candidate.section_ids for candidate in generated.candidates}
        self.assertEqual(
            ids,
            {(), ("A-01",), ("B-01",)},
        )
        self.assertGreater(generated.pruned_include_branches_by_credit_cap, 0)
        self.assertTrue(generated.global_search_space_complete)

    def test_chapel_is_exempt_from_ordinary_cap_under_current_policy(self):
        generated = enumerate_fall_candidate_sets(
            universe(
                row("A-01", "A", time="화3", credits=22),
                row("YCA1006-01-00", "YCA1006", time="수3", credits=0.5),
            ),
            fall2026_load_policy(),
        )

        pair = next(
            candidate
            for candidate in generated.candidates
            if candidate.section_ids == ("A-01", "YCA1006-01-00")
        )
        self.assertEqual(pair.load.known_total_credits, 22.5)
        self.assertEqual(pair.load.known_ordinary_credits, 22.0)
        self.assertEqual(pair.load.known_chapel_credits, 0.5)

    def test_policy_can_explicitly_make_chapel_count_toward_cap(self):
        policy = FallLoadPolicy(
            ordinary_credit_cap=22.0,
            chapel_exempt_from_ordinary_cap=False,
            source_id="test:alternate-policy",
        )
        generated = enumerate_fall_candidate_sets(
            universe(
                row("A-01", "A", time="화3", credits=22),
                row("YCA1006-01-00", "YCA1006", time="수3", credits=0.5),
            ),
            policy,
        )
        self.assertNotIn(
            ("A-01", "YCA1006-01-00"),
            {candidate.section_ids for candidate in generated.candidates},
        )

    def test_parsed_registration_conflict_can_prune_include_branch(self):
        generated = enumerate_fall_candidate_sets(
            universe(
                row("A-01", "A", time="화3,4"),
                row("B-01", "B", time="화4,5"),
            ),
            fall2026_load_policy(),
        )

        self.assertNotIn(
            ("A-01", "B-01"),
            {candidate.section_ids for candidate in generated.candidates},
        )
        self.assertGreater(generated.pruned_include_branches_by_conflict, 0)

    def test_unknown_credit_is_retained_as_unresolved_not_pruned(self):
        generated = enumerate_fall_candidate_sets(
            universe(
                row("A-01", "A", time="화3", credits=22),
                row("B-01", "B", time="수3", credits=None),
            ),
            fall2026_load_policy(),
        )
        pair = next(
            candidate
            for candidate in generated.candidates
            if candidate.section_ids == ("A-01", "B-01")
        )

        self.assertIn("B-01", pair.load.unknown_credit_section_ids)
        self.assertIn("credit::B-01", pair.enumeration_unknowns)
        self.assertFalse(pair.enumeration_constraints_exact)

    def test_nonparsed_schedule_is_retained_as_unresolved_not_free(self):
        generated = enumerate_fall_candidate_sets(
            universe(
                row("A-01", "A", time="화3"),
                row("B-01", "B", time="미정"),
            ),
            fall2026_load_policy(),
        )
        pair = next(
            candidate
            for candidate in generated.candidates
            if candidate.section_ids == ("A-01", "B-01")
        )

        self.assertEqual(pair.unresolved_schedule_section_ids, ("B-01",))
        self.assertIn("schedule::B-01", pair.enumeration_unknowns)

    def test_explicit_subset_can_be_exhaustive_without_becoming_global(self):
        snapshot = ingest_catalog(
            [row("A-01", "A", time="화3"), row("B-01", "B", time="수3")]
        )
        scoped = build_fall_section_universe(
            "scope",
            snapshot,
            scope=FallSearchScope.explicit_subset(
                {"A-01"},
                source_id="user:diagnostic",
            ),
        )
        generated = enumerate_fall_candidate_sets(scoped, fall2026_load_policy())

        self.assertEqual(generated.status, FallCandidateSetEnumerationStatus.COMPLETE)
        self.assertTrue(generated.exact_scoped_search_space_complete)
        self.assertFalse(generated.global_search_space_complete)
        self.assertEqual(generated.evaluated_subsets, 2)

    def test_blocked_universe_is_not_partially_enumerated(self):
        blocked = universe(
            row("A-01", "A", cgprfNm="Professor A"),
            row("A-01", "A", cgprfNm="Professor B"),
        )
        generated = enumerate_fall_candidate_sets(
            blocked,
            fall2026_load_policy(),
        )

        self.assertEqual(
            generated.status,
            FallCandidateSetEnumerationStatus.INPUT_BLOCKED,
        )
        self.assertFalse(generated.candidates)
        self.assertEqual(generated.evaluated_subsets, 0)
        self.assertFalse(generated.global_search_space_complete)

    def test_subset_limit_is_truncation_not_top_n(self):
        generated = enumerate_fall_candidate_sets(
            universe(
                row("A-01", "A", time="월3"),
                row("B-01", "B", time="화3"),
                row("C-01", "C", time="수3"),
                row("D-01", "D", time="목3"),
            ),
            fall2026_load_policy(),
            max_subset_evaluations=5,
        )

        self.assertEqual(generated.status, FallCandidateSetEnumerationStatus.TRUNCATED)
        self.assertEqual(generated.evaluated_subsets, 5)
        self.assertEqual(len(generated.candidates), 5)
        self.assertFalse(generated.enumeration_complete)
        self.assertFalse(generated.global_search_space_complete)


if __name__ == "__main__":
    unittest.main()
