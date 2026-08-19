import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.catalog import ingest_catalog  # noqa: E402
from timetable_optimizer.course_preferences import ProfessorRatingBook  # noqa: E402
from timetable_optimizer.degree import (  # noqa: E402
    DegreeScenario,
    DegreeState,
    KoreanMajorCreditCap,
    MajorMode,
    SecondMajorSpec,
    SecondMajorStatus,
    SpecificCourseRequirement,
)
from timetable_optimizer.degree_remainder import degree_remainder  # noqa: E402
from timetable_optimizer.fall_candidate_sets import fall2026_load_policy  # noqa: E402
from timetable_optimizer.fall_streaming_engine import (  # noqa: E402
    advance_fall_streaming_search,
)
from timetable_optimizer.fall_streaming_search import (  # noqa: E402
    FallCandidateEvaluationContext,
    FallStreamingSearchStatus,
)
from timetable_optimizer.fall_streaming_state import (  # noqa: E402
    FallStreamingStateError,
    FallStreamingStateStore,
)
from timetable_optimizer.fall_universe import build_fall_section_universe  # noqa: E402
from timetable_optimizer.future_opportunities import (  # noqa: E402
    FutureOpportunityScenario,
    FutureTermOpportunitySet,
    OpportunitySetStatus,
)
from timetable_optimizer.future_problem import build_future_planning_problem  # noqa: E402
from timetable_optimizer.future_scenarios import (  # noqa: E402
    CampusAccessKind,
    CampusAccessScenario,
    FutureCatalogueBasis,
    FutureCatalogueBasisKind,
    FutureTermScenario,
    FutureTimelineScenario,
    ResidenceState,
    TermActivity,
)
from timetable_optimizer.future_utility import (  # noqa: E402
    TemporalUtilityAggregation,
    TemporalUtilityWeight,
)
from timetable_optimizer.preferences import PreferenceProfile  # noqa: E402
from timetable_optimizer.registration import assess_freshman_registration  # noqa: E402


def row():
    return {
        "subjtnbCorsePrcts": "A-01",
        "subjtnb": "A",
        "subjtEngNm": "A",
        "subjtNm": "A",
        "campsDivNm": "국제",
        "cdt": 3,
        "cgprfNm": "Professor",
        "estblDeprtNm": "UIC",
        "hy": "1",
        "srclnLctreLangDivCd": "10",
        "srclnLctreLangDivNm": "영어",
        "subsrtDivNm": "",
        "atntnMattrDesc": "",
        "gradeEvlMthdDivNm": "절대평가",
        "lctreTimeNm": "화3",
        "lecrmNm": "A",
        "subjtClNm": "대면",
        "rmvlcYn": "0",
        "rmvlcYnNm": "",
    }


def scenario():
    return DegreeScenario(
        scenario_id="engine-a",
        graduation_min_credits=3.0,
        major_mode=MajorMode.SINGLE,
        qrm_major_credit_target=0.0,
        requirements=(
            SpecificCourseRequirement("req_a", "A", ("A",), 3.0),
        ),
        qrm_korean_credit_cap=KoreanMajorCreditCap(4, 12.0),
        exclusive_major_assignment=True,
        second_major=SecondMajorSpec(SecondMajorStatus.NONE),
    )


def make_problem(*, fall_weight=0.0):
    snapshot = ingest_catalog((row(),), source_name="fixture", term="2026F")
    universe = build_fall_section_universe("engine-universe", snapshot)
    degree_scenario = scenario()
    start = DegreeState()
    term = FutureTermScenario(
        term_id="2027S",
        activity=TermActivity.ACTIVE,
        ordinary_credit_cap=18.0,
        residence=ResidenceState.HOME,
        campus_access=CampusAccessScenario(CampusAccessKind.ANY),
        catalogue_basis=FutureCatalogueBasis(
            FutureCatalogueBasisKind.EXPLICIT_SCENARIO
        ),
    )
    future = build_future_planning_problem(
        "engine-future",
        degree_remainder(start, degree_scenario),
        FutureTimelineScenario("timeline", (term,)),
        FutureOpportunityScenario(
            "empty",
            (
                FutureTermOpportunitySet(
                    "2027S",
                    OpportunitySetStatus.EXPLICIT_SCENARIO,
                    source_id="scenario:known-empty",
                ),
            ),
        ),
    )
    registration = assess_freshman_registration(
        "A-01",
        {
            "A-01": {
                "sy1PercpCnt": 0,
                "sy2PercpCnt": 0,
                "sy3PercpCnt": 0,
                "sy4PercpCnt": 0,
                "sy5PercpCnt": 0,
                "sy6PercpCnt": 0,
            }
        },
    )
    context = FallCandidateEvaluationContext(
        snapshot=snapshot,
        degree_scenario=degree_scenario,
        starting_state=start,
        future_template=future,
        preference_profile=PreferenceProfile("empty"),
        professor_ratings=ProfessorRatingBook(()),
        temporal_aggregation=TemporalUtilityAggregation(
            source_id="test:policy",
            weights=(
                TemporalUtilityWeight("2026F", fall_weight),
                TemporalUtilityWeight("2027S", 1.0),
            ),
        ),
        load_policy=fall2026_load_policy(),
        registration_assessments={"A-01": registration},
    )
    return universe, context


class StreamingEngineTests(unittest.TestCase):
    def test_repeated_process_style_calls_reach_global_optimum(self):
        universe, context = make_problem()
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "search.sqlite3"
            statuses = []
            progress = None
            for _ in range(10):
                # Reconstruct store every iteration to mimic a fresh process invocation.
                progress = advance_fall_streaming_search(
                    universe,
                    context,
                    FallStreamingStateStore(path),
                    max_emitted_candidates=1,
                    max_extension_checks=1,
                )
                statuses.append(progress.snapshot.status)
                if progress.structural_complete:
                    break
            self.assertIsNotNone(progress)
            assert progress is not None
            self.assertIn(FallStreamingSearchStatus.PAUSED, statuses)
            self.assertEqual(
                progress.snapshot.status,
                FallStreamingSearchStatus.GLOBAL_OPTIMUM_PROVEN,
            )
            self.assertTrue(progress.snapshot.model_optimum_proven)
            self.assertIsNotNone(progress.snapshot.proven_best)
            self.assertEqual(progress.snapshot.proven_best.section_ids, ("A-01",))

            # Calling again after completion is read-only and returns the saved proof.
            again = advance_fall_streaming_search(
                universe,
                context,
                FallStreamingStateStore(path),
                max_emitted_candidates=1,
                max_extension_checks=1,
            )
            self.assertTrue(again.already_complete)
            self.assertIsNone(again.batch)
            self.assertEqual(
                again.snapshot.status,
                FallStreamingSearchStatus.GLOBAL_OPTIMUM_PROVEN,
            )

    def test_paused_batch_never_claims_current_incumbent_as_optimum(self):
        universe, context = make_problem()
        with tempfile.TemporaryDirectory() as tempdir:
            progress = advance_fall_streaming_search(
                universe,
                context,
                FallStreamingStateStore(Path(tempdir) / "search.sqlite3"),
                max_emitted_candidates=1,
                max_extension_checks=1,
            )
            self.assertEqual(progress.snapshot.status, FallStreamingSearchStatus.PAUSED)
            self.assertFalse(progress.snapshot.model_optimum_proven)

    def test_objective_change_refuses_to_resume_same_database(self):
        universe, original = make_problem(fall_weight=0.0)
        _universe2, changed = make_problem(fall_weight=1.0)
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "search.sqlite3"
            advance_fall_streaming_search(
                universe,
                original,
                FallStreamingStateStore(path),
                max_emitted_candidates=1,
                max_extension_checks=1,
            )
            with self.assertRaises(FallStreamingStateError):
                advance_fall_streaming_search(
                    universe,
                    changed,
                    FallStreamingStateStore(path),
                    max_emitted_candidates=1,
                    max_extension_checks=1,
                )


if __name__ == "__main__":
    unittest.main()
