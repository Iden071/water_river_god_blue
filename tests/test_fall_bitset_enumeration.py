import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.fall_bitset_enumeration import (  # noqa: E402
    FallBitsetCheckpoint,
    FallBitsetEnumerationError,
    FallBitsetEnumerationStatus,
    enumerate_fall_candidate_bitset_batch,
)
from timetable_optimizer.fall_candidate_sets import (  # noqa: E402
    FallLoadPolicy,
    enumerate_fall_candidate_sets,
)
from timetable_optimizer.fall_universe import (  # noqa: E402
    FallSearchScope,
    FallSectionUniverse,
)
from timetable_optimizer.sections import (  # noqa: E402
    NoListedSchedule,
    ParsedSchedule,
    Section,
)


def section(section_id, *, mask=0, credits=3.0, course_code=None, parsed=True):
    schedule = (
        ParsedSchedule(
            raw_time_text=f"mask-{mask}",
            raw_room_text="A",
            segments=(),
            conflict_mask=mask,
            presence_mask=mask,
            fixed_mask=mask,
        )
        if parsed
        else NoListedSchedule(raw_time_text="", raw_room_text="")
    )
    return Section(
        section_id=section_id,
        course_code=course_code or f"C{section_id}",
        name=section_id,
        korean_name=section_id,
        campus="국제",
        credits=credits,
        professor="Professor",
        language_code="",
        note="",
        grading="",
        cancelled=False,
        mode_text="",
        schedule=schedule,
        language_name="영어",
    )


def universe(*sections):
    return FallSectionUniverse(
        universe_id="bitset-test",
        scope=FallSearchScope.full_catalog(),
        source_name="test-catalogue",
        source_fingerprint="test-fingerprint-v1",
        included_sections=tuple(sections),
        hard_exclusions=(),
        scoped_out_section_ids=frozenset(),
        global_catalogue_unknowns=(),
        scope_unknowns=(),
        known_physical_section_ids=frozenset(item.section_id for item in sections),
    )


def policy(cap=6.0):
    return FallLoadPolicy(
        ordinary_credit_cap=cap,
        chapel_exempt_from_ordinary_cap=True,
        source_id="SPEC.md §3.3",
    )


def ids(candidates):
    return {candidate.section_ids for candidate in candidates}


class BitsetFallEnumerationTests(unittest.TestCase):
    def test_complete_result_matches_reference_powerset(self):
        catalog = universe(
            section("A", mask=1),
            section("B", mask=1),
            section("C", mask=2),
            section("D", mask=4),
        )
        load = policy(6.0)
        reference = enumerate_fall_candidate_sets(
            catalog, load, max_subset_evaluations=1000
        )
        batch = enumerate_fall_candidate_bitset_batch(
            catalog,
            load,
            max_emitted_candidates=1000,
            max_expanded_extensions=1000,
        )
        self.assertEqual(batch.status, FallBitsetEnumerationStatus.COMPLETE)
        self.assertEqual(ids(batch.candidates), ids(reference.candidates))
        self.assertEqual(len(batch.candidates), len(ids(batch.candidates)))

    def test_pause_resume_json_round_trip_is_complete_without_duplicates(self):
        catalog = universe(
            section("A", mask=1),
            section("B", mask=2),
            section("C", mask=4),
            section("D", mask=8),
        )
        load = policy(9.0)
        reference = enumerate_fall_candidate_sets(
            catalog, load, max_subset_evaluations=1000
        )

        checkpoint = None
        emitted = []
        statuses = []
        while True:
            batch = enumerate_fall_candidate_bitset_batch(
                catalog,
                load,
                checkpoint=checkpoint,
                max_emitted_candidates=2,
                max_expanded_extensions=2,
            )
            statuses.append(batch.status)
            emitted.extend(candidate.section_ids for candidate in batch.candidates)
            if batch.complete:
                break
            self.assertTrue(batch.resumable)
            self.assertIsNotNone(batch.checkpoint)
            raw = json.loads(json.dumps(batch.checkpoint.to_dict()))
            checkpoint = FallBitsetCheckpoint.from_dict(raw)

        self.assertIn(FallBitsetEnumerationStatus.PAUSED, statuses)
        self.assertEqual(set(emitted), ids(reference.candidates))
        self.assertEqual(len(emitted), len(set(emitted)))

    def test_unknown_credit_and_nonparsed_schedule_are_retained(self):
        catalog = universe(
            section("A", mask=1, credits=3.0),
            section("U", credits=None, parsed=False),
        )
        batch = enumerate_fall_candidate_bitset_batch(
            catalog,
            policy(3.0),
            max_emitted_candidates=100,
            max_expanded_extensions=100,
        )
        by_ids = {candidate.section_ids: candidate for candidate in batch.candidates}
        both = by_ids[("A", "U")]
        self.assertIn("credit::U", both.enumeration_unknowns)
        self.assertIn("schedule::U", both.enumeration_unknowns)

    def test_conflict_and_credit_filtering_match_reference_family(self):
        catalog = universe(
            section("A", mask=1, credits=3.0),
            section("B", mask=1, credits=3.0),
            section("C", mask=2, credits=3.0),
        )
        load = policy(3.0)
        reference = enumerate_fall_candidate_sets(
            catalog, load, max_subset_evaluations=100
        )
        batch = enumerate_fall_candidate_bitset_batch(
            catalog,
            load,
            max_emitted_candidates=100,
            max_expanded_extensions=100,
        )
        self.assertEqual(ids(batch.candidates), ids(reference.candidates))
        self.assertNotIn(("A", "B"), ids(batch.candidates))
        self.assertNotIn(("A", "C"), ids(batch.candidates))

    def test_checkpoint_rejects_changed_policy_or_universe(self):
        catalog = universe(section("A", mask=1), section("B", mask=2))
        first = enumerate_fall_candidate_bitset_batch(
            catalog,
            policy(6.0),
            max_emitted_candidates=1,
            max_expanded_extensions=1,
        )
        self.assertIsNotNone(first.checkpoint)
        with self.assertRaises(FallBitsetEnumerationError):
            enumerate_fall_candidate_bitset_batch(
                catalog,
                policy(9.0),
                checkpoint=first.checkpoint,
            )
        changed = universe(
            section("A", mask=1),
            section("B", mask=2),
            section("C", mask=4),
        )
        with self.assertRaises(FallBitsetEnumerationError):
            enumerate_fall_candidate_bitset_batch(
                changed,
                policy(6.0),
                checkpoint=first.checkpoint,
            )

    def test_pause_never_claims_complete(self):
        catalog = universe(section("A", mask=1), section("B", mask=2))
        batch = enumerate_fall_candidate_bitset_batch(
            catalog,
            policy(),
            max_emitted_candidates=1,
            max_expanded_extensions=1,
        )
        self.assertEqual(batch.status, FallBitsetEnumerationStatus.PAUSED)
        self.assertFalse(batch.complete)
        self.assertTrue(batch.resumable)


if __name__ == "__main__":
    unittest.main()
