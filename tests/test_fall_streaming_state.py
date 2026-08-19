import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.fall_candidate_sets import (  # noqa: E402
    FallCandidateSet,
    FallLoadPolicy,
    enumerate_fall_candidate_sets,
)
from timetable_optimizer.fall_resumable_enumeration import (  # noqa: E402
    FallResumableEnumerationStatus,
    enumerate_fall_candidate_batch,
)
from timetable_optimizer.fall_search import FallSearchUnknown  # noqa: E402
from timetable_optimizer.fall_streaming_search import (  # noqa: E402
    FallCandidateEvaluation,
    FallCandidateEvaluationStatus,
    FallStreamingAccumulator,
)
from timetable_optimizer.fall_streaming_state import (  # noqa: E402
    FallStreamingStateError,
    FallStreamingStateStore,
    fall_streaming_search_signature,
)
from timetable_optimizer.fall_universe import (  # noqa: E402
    FallSearchScope,
    FallSectionUniverse,
)
from timetable_optimizer.sections import ParsedSchedule, Section  # noqa: E402

EVALUATION_SIGNATURE = "fixture-evaluation-v1"


def section(section_id, mask):
    schedule = ParsedSchedule(
        raw_time_text=f"mask-{mask}",
        raw_room_text="A",
        segments=(),
        conflict_mask=mask,
        presence_mask=mask,
        fixed_mask=mask,
    )
    return Section(
        section_id=section_id,
        course_code=f"C{section_id}",
        name=section_id,
        korean_name=section_id,
        campus="국제",
        credits=3.0,
        professor="Professor",
        language_code="",
        note="",
        grading="",
        cancelled=False,
        mode_text="",
        schedule=schedule,
        language_name="영어",
    )


def universe():
    sections = (section("A", 1), section("B", 2), section("C", 4))
    return FallSectionUniverse(
        universe_id="state-test",
        scope=FallSearchScope.full_catalog(),
        source_name="fixture",
        source_fingerprint="fixture-v1",
        included_sections=sections,
        hard_exclusions=(),
        scoped_out_section_ids=frozenset(),
        global_catalogue_unknowns=(),
        scope_unknowns=(),
        known_physical_section_ids=frozenset(item.section_id for item in sections),
    )


def policy():
    return FallLoadPolicy(
        ordinary_credit_cap=6.0,
        chapel_exempt_from_ordinary_cap=True,
        source_id="SPEC.md §3.3",
    )


def unresolved_evaluation(candidate: FallCandidateSet) -> FallCandidateEvaluation:
    fall_set_id = "test::" + "+".join(candidate.section_ids or ("empty",))
    unknown = FallSearchUnknown(
        code="fixture_unresolved",
        message="fixture unresolved alternative",
        fall_set_id=fall_set_id,
        section_ids=candidate.section_ids,
    )
    return FallCandidateEvaluation(
        fall_set_id=fall_set_id,
        section_ids=candidate.section_ids,
        status=FallCandidateEvaluationStatus.UNRESOLVED,
        known_infeasible=False,
        branch_results=(),
        utility_records=(),
        proven_unreachable_branch_ids=frozenset(),
        unresolved_alternatives=(unknown,),
        blocker_codes=frozenset(),
    )


def commit(store, *, signature, batch, accumulator, previous):
    return store.commit_batch(
        search_signature=signature,
        evaluation_signature=EVALUATION_SIGNATURE,
        checkpoint=batch.checkpoint,
        accumulator=accumulator,
        structural_status=batch.status,
        previous_committed_batches=previous,
    )


class StreamingStatePersistenceTests(unittest.TestCase):
    def test_restart_resume_preserves_checkpoint_and_accumulator_together(self):
        catalog = universe()
        load = policy()
        signature = fall_streaming_search_signature(catalog, load)
        reference = enumerate_fall_candidate_sets(
            catalog,
            load,
            max_subset_evaluations=100,
        )

        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "state.sqlite3"
            store = FallStreamingStateStore(path)
            accumulator = FallStreamingAccumulator()

            first = enumerate_fall_candidate_batch(
                catalog,
                load,
                max_emitted_candidates=2,
                max_extension_checks=2,
            )
            self.assertEqual(first.status, FallResumableEnumerationStatus.PAUSED)
            for candidate in first.candidates:
                accumulator.add_evaluation(unresolved_evaluation(candidate))
            commit(store, signature=signature, batch=first, accumulator=accumulator, previous=0)

            reopened = FallStreamingStateStore(path).load(
                expected_search_signature=signature,
                expected_evaluation_signature=EVALUATION_SIGNATURE,
            )
            self.assertIsNotNone(reopened)
            assert reopened is not None
            self.assertEqual(reopened.committed_batches, 1)
            self.assertEqual(reopened.accumulator.processed_fall_sets, len(first.candidates))
            self.assertEqual(reopened.accumulator.unresolved_alternatives, len(first.candidates))

            checkpoint = reopened.checkpoint
            accumulator = reopened.accumulator
            committed = reopened.committed_batches
            while True:
                batch = enumerate_fall_candidate_batch(
                    catalog,
                    load,
                    checkpoint=checkpoint,
                    max_emitted_candidates=2,
                    max_extension_checks=2,
                )
                for candidate in batch.candidates:
                    accumulator.add_evaluation(unresolved_evaluation(candidate))
                state = commit(
                    store,
                    signature=signature,
                    batch=batch,
                    accumulator=accumulator,
                    previous=committed,
                )
                committed = state.committed_batches
                checkpoint = state.checkpoint
                if batch.status is FallResumableEnumerationStatus.COMPLETE:
                    break

            final = store.load(
                expected_search_signature=signature,
                expected_evaluation_signature=EVALUATION_SIGNATURE,
            )
            self.assertIsNotNone(final)
            assert final is not None
            self.assertTrue(final.complete)
            self.assertIsNone(final.checkpoint)
            self.assertEqual(final.accumulator.processed_fall_sets, len(reference.candidates))
            self.assertEqual(final.accumulator.unresolved_alternatives, len(reference.candidates))

    def test_search_or_evaluation_signature_mismatch_is_rejected(self):
        catalog = universe()
        load = policy()
        signature = fall_streaming_search_signature(catalog, load)
        with tempfile.TemporaryDirectory() as tempdir:
            store = FallStreamingStateStore(Path(tempdir) / "state.sqlite3")
            batch = enumerate_fall_candidate_batch(
                catalog,
                load,
                max_emitted_candidates=1,
                max_extension_checks=1,
            )
            commit(
                store,
                signature=signature,
                batch=batch,
                accumulator=FallStreamingAccumulator(),
                previous=0,
            )
            with self.assertRaises(FallStreamingStateError):
                store.load(
                    expected_search_signature="different-search",
                    expected_evaluation_signature=EVALUATION_SIGNATURE,
                )
            with self.assertRaises(FallStreamingStateError):
                store.load(
                    expected_search_signature=signature,
                    expected_evaluation_signature="different-evaluation-model",
                )

    def test_stale_writer_cannot_overwrite_newer_committed_batch(self):
        catalog = universe()
        load = policy()
        signature = fall_streaming_search_signature(catalog, load)
        with tempfile.TemporaryDirectory() as tempdir:
            store = FallStreamingStateStore(Path(tempdir) / "state.sqlite3")
            first = enumerate_fall_candidate_batch(
                catalog,
                load,
                max_emitted_candidates=1,
                max_extension_checks=1,
            )
            state1 = commit(
                store,
                signature=signature,
                batch=first,
                accumulator=FallStreamingAccumulator(),
                previous=0,
            )
            second = enumerate_fall_candidate_batch(
                catalog,
                load,
                checkpoint=state1.checkpoint,
                max_emitted_candidates=1,
                max_extension_checks=1,
            )
            commit(
                store,
                signature=signature,
                batch=second,
                accumulator=state1.accumulator,
                previous=1,
            )

            with self.assertRaises(FallStreamingStateError):
                store.commit_batch(
                    search_signature=signature,
                    evaluation_signature=EVALUATION_SIGNATURE,
                    checkpoint=state1.checkpoint,
                    accumulator=state1.accumulator,
                    structural_status=state1.structural_status,
                    previous_committed_batches=1,
                )

    def test_writer_cannot_change_evaluation_model_midstream(self):
        catalog = universe()
        load = policy()
        signature = fall_streaming_search_signature(catalog, load)
        with tempfile.TemporaryDirectory() as tempdir:
            store = FallStreamingStateStore(Path(tempdir) / "state.sqlite3")
            first = enumerate_fall_candidate_batch(
                catalog,
                load,
                max_emitted_candidates=1,
                max_extension_checks=1,
            )
            commit(
                store,
                signature=signature,
                batch=first,
                accumulator=FallStreamingAccumulator(),
                previous=0,
            )
            with self.assertRaises(FallStreamingStateError):
                store.commit_batch(
                    search_signature=signature,
                    evaluation_signature="changed-objective",
                    checkpoint=first.checkpoint,
                    accumulator=FallStreamingAccumulator(),
                    structural_status=first.status,
                    previous_committed_batches=1,
                )

    def test_reset_removes_saved_progress(self):
        catalog = universe()
        load = policy()
        signature = fall_streaming_search_signature(catalog, load)
        with tempfile.TemporaryDirectory() as tempdir:
            store = FallStreamingStateStore(Path(tempdir) / "state.sqlite3")
            batch = enumerate_fall_candidate_batch(
                catalog,
                load,
                max_emitted_candidates=1,
                max_extension_checks=1,
            )
            commit(
                store,
                signature=signature,
                batch=batch,
                accumulator=FallStreamingAccumulator(),
                previous=0,
            )
            store.reset()
            self.assertIsNone(
                store.load(
                    expected_search_signature=signature,
                    expected_evaluation_signature=EVALUATION_SIGNATURE,
                )
            )


if __name__ == "__main__":
    unittest.main()
