import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.catalog import ingest_catalog  # noqa: E402
from timetable_optimizer.course_preferences import ProfessorRatingBook  # noqa: E402
from timetable_optimizer.degree import (  # noqa: E402
    CreditBucketRequirement,
    DegreeScenario,
    DegreeState,
    KoreanMajorCreditCap,
    MajorMode,
    SecondMajorSpec,
    SecondMajorStatus,
    SpecificCourseRequirement,
)
from timetable_optimizer.degree_remainder import degree_remainder  # noqa: E402
from timetable_optimizer.fall_candidate_sets import (  # noqa: E402
    enumerate_fall_candidate_sets,
    fall2026_load_policy,
)
from timetable_optimizer.fall_resumable_enumeration import (  # noqa: E402
    FallResumableEnumerationStatus,
    enumerate_fall_candidate_batch,
)
from timetable_optimizer.fall_search import (  # noqa: E402
    FallWholePlanSearchStatus,
    search_fall_whole_plans,
)
from timetable_optimizer.fall_streaming_search import (  # noqa: E402
    FallCandidateEvaluationContext,
    FallStreamingAccumulator,
    FallStreamingSearchStatus,
    consume_fall_enumeration_batch,
)
from timetable_optimizer.fall_universe import (  # noqa: E402
    FallSearchScope,
    build_fall_section_universe,
)
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


def row(section_id, course_code, *, time="화3", credits=3, cancellation_known=True):
    result = {
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
        "lctreTimeNm": time,
        "lecrmNm": "강의실A",
        "subjtClNm": "대면",
    }
    if cancellation_known:
        result["rmvlcYn"] = "0"
        result["rmvlcYnNm"] = " "
    return result


def course_a_scenario():
    return DegreeScenario(
        scenario_id="stream-fall-a",
        graduation_min_credits=3.0,
        major_mode=MajorMode.SINGLE,
        qrm_major_credit_target=0.0,
        requirements=(
            SpecificCourseRequirement(
                requirement_id="req_a",
                title="A",
                course_codes=("A",),
                credits=3.0,
            ),
        ),
        qrm_korean_credit_cap=KoreanMajorCreditCap(4, 12.0),
        exclusive_major_assignment=True,
        second_major=SecondMajorSpec(SecondMajorStatus.NONE),
    )


def scird_scenario():
    return DegreeScenario(
        scenario_id="stream-fall-scird",
        graduation_min_credits=3.0,
        major_mode=MajorMode.SINGLE,
        qrm_major_credit_target=0.0,
        requirements=(
            CreditBucketRequirement(
                requirement_id="cc_scird",
                title="Science Literacy / RDQM",
                target_credits=3.0,
                qualification_rule_id="uic_science_literacy_or_rdqm_2026",
            ),
        ),
        qrm_korean_credit_cap=KoreanMajorCreditCap(4, 12.0),
        exclusive_major_assignment=True,
        second_major=SecondMajorSpec(SecondMajorStatus.NONE),
    )


def future_template(scenario, start):
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
    opportunities = FutureOpportunityScenario(
        "future-empty",
        (
            FutureTermOpportunitySet(
                "2027S",
                OpportunitySetStatus.EXPLICIT_SCENARIO,
                source_id="scenario:2027S-known-empty",
            ),
        ),
    )
    return build_future_planning_problem(
        "stream-template",
        degree_remainder(start, scenario),
        FutureTimelineScenario("timeline", (term,)),
        opportunities,
    )


def temporal_policy():
    return TemporalUtilityAggregation(
        source_id="test:future-only-objective",
        weights=(
            TemporalUtilityWeight("2026F", 0.0),
            TemporalUtilityWeight("2027S", 1.0),
        ),
    )


def registration(section_id):
    return assess_freshman_registration(
        section_id,
        {
            section_id: {
                "sy1PercpCnt": 0,
                "sy2PercpCnt": 0,
                "sy3PercpCnt": 0,
                "sy4PercpCnt": 0,
                "sy5PercpCnt": 0,
                "sy6PercpCnt": 0,
            }
        },
    )


def setup_problem(rows, scenario, *, scope=None):
    snapshot = ingest_catalog(rows, source_name="fixture", term="2026F")
    universe = build_fall_section_universe(
        "stream-universe",
        snapshot,
        scope=scope,
    )
    start = DegreeState()
    registrations = {
        section.section_id: registration(section.section_id)
        for section in snapshot.sections
    }
    context = FallCandidateEvaluationContext(
        snapshot=snapshot,
        degree_scenario=scenario,
        starting_state=start,
        future_template=future_template(scenario, start),
        preference_profile=PreferenceProfile("empty"),
        professor_ratings=ProfessorRatingBook(()),
        temporal_aggregation=temporal_policy(),
        load_policy=fall2026_load_policy(),
        registration_assessments=registrations,
    )
    return snapshot, universe, context


def run_reference(snapshot, universe, context):
    candidates = enumerate_fall_candidate_sets(
        universe,
        context.load_policy,
        max_subset_evaluations=1000,
    )
    return search_fall_whole_plans(
        candidates,
        snapshot,
        context.degree_scenario,
        context.starting_state,
        context.future_template,
        context.preference_profile,
        context.professor_ratings,
        context.temporal_aggregation,
        registration_assessments=context.registration_assessments,
    )


def run_streaming(universe, context, *, candidate_budget=1, check_budget=3):
    accumulator = FallStreamingAccumulator()
    checkpoint = None
    paused_snapshots = []
    while True:
        batch = enumerate_fall_candidate_batch(
            universe,
            context.load_policy,
            checkpoint=checkpoint,
            max_emitted_candidates=candidate_budget,
            max_extension_checks=check_budget,
        )
        consume_fall_enumeration_batch(accumulator, batch, context)
        snapshot = accumulator.snapshot(
            structural_status=batch.status,
            universe=universe,
        )
        if batch.status is FallResumableEnumerationStatus.COMPLETE:
            return accumulator, snapshot, paused_snapshots
        self_status = snapshot.status
        if self_status is not FallStreamingSearchStatus.PAUSED:
            raise AssertionError(f"paused structural search overclaimed {self_status}")
        paused_snapshots.append(snapshot)
        checkpoint = batch.checkpoint
        assert checkpoint is not None


class StreamingReferenceParityTests(unittest.TestCase):
    def test_complete_global_optimum_matches_reference_winning_sections(self):
        snapshot, universe, context = setup_problem(
            [
                row("A-01", "A", time="화3"),
                row("B-01", "B", time="화3"),
            ],
            course_a_scenario(),
        )
        reference = run_reference(snapshot, universe, context)
        _accumulator, streamed, paused = run_streaming(universe, context)

        self.assertEqual(reference.status, FallWholePlanSearchStatus.GLOBAL_OPTIMUM_PROVEN)
        self.assertEqual(streamed.status, FallStreamingSearchStatus.GLOBAL_OPTIMUM_PROVEN)
        self.assertTrue(paused)
        self.assertTrue(all(not item.model_optimum_proven for item in paused))
        self.assertIsNotNone(streamed.proven_best)
        self.assertEqual(streamed.proven_best.section_ids, ("A-01",))
        self.assertEqual(
            streamed.proven_best.utility.complete_bounds,
            reference.proven_best.complete_bounds,
        )

    def test_explicit_subset_can_only_prove_scoped_optimum(self):
        scope = FallSearchScope.explicit_subset(
            {"A-01"},
            source_id="user:diagnostic-shortlist",
        )
        snapshot, universe, context = setup_problem(
            [row("A-01", "A"), row("OUT-01", "B", time="수3")],
            course_a_scenario(),
            scope=scope,
        )
        reference = run_reference(snapshot, universe, context)
        _accumulator, streamed, _paused = run_streaming(universe, context)
        self.assertEqual(reference.status, FallWholePlanSearchStatus.SCOPED_OPTIMUM_PROVEN)
        self.assertEqual(streamed.status, FallStreamingSearchStatus.SCOPED_OPTIMUM_PROVEN)
        self.assertFalse(streamed.status is FallStreamingSearchStatus.GLOBAL_OPTIMUM_PROVEN)

    def test_unresolved_hard_alternative_matches_reference_blocker_class(self):
        snapshot, universe, context = setup_problem(
            [
                row("A-01", "A", time="화3"),
                row("B-01", "A", time="화3", cancellation_known=False),
            ],
            course_a_scenario(),
        )
        reference = run_reference(snapshot, universe, context)
        _accumulator, streamed, _paused = run_streaming(universe, context)
        self.assertEqual(reference.status, FallWholePlanSearchStatus.UNRESOLVED_ALTERNATIVES)
        self.assertEqual(streamed.status, FallStreamingSearchStatus.UNRESOLVED_ALTERNATIVES)
        self.assertIn(
            "fall_hard::cancellation_status_unresolved",
            dict(streamed.unresolved_alternative_counts),
        )
        self.assertFalse(streamed.model_optimum_proven)

    def test_unresolved_recognition_alternative_matches_reference(self):
        snapshot, universe, context = setup_problem(
            [
                row("A-01", "UIC2151", time="화3"),
                row("B-01", "ZZZ1000", time="화3"),
            ],
            scird_scenario(),
        )
        reference = run_reference(snapshot, universe, context)
        _accumulator, streamed, _paused = run_streaming(universe, context)
        self.assertEqual(reference.status, FallWholePlanSearchStatus.UNRESOLVED_ALTERNATIVES)
        self.assertEqual(streamed.status, FallStreamingSearchStatus.UNRESOLVED_ALTERNATIVES)
        self.assertIn(
            "fall_transition::fall_recognition_unresolved",
            dict(streamed.unresolved_alternative_counts),
        )

    def test_proven_no_reachable_plan_matches_reference(self):
        snapshot, universe, context = setup_problem(
            [row("B-01", "B", time="화3")],
            course_a_scenario(),
        )
        reference = run_reference(snapshot, universe, context)
        _accumulator, streamed, _paused = run_streaming(universe, context)
        self.assertEqual(reference.status, FallWholePlanSearchStatus.PROVEN_NO_REACHABLE_PLAN)
        self.assertEqual(streamed.status, FallStreamingSearchStatus.PROVEN_NO_REACHABLE_PLAN)
        self.assertGreater(streamed.proven_unreachable_branches, 0)

    def test_unknown_credit_is_preserved_as_unresolved_not_pruned(self):
        snapshot, universe, context = setup_problem(
            [row("A-01", "A", credits=None)],
            course_a_scenario(),
        )
        reference = run_reference(snapshot, universe, context)
        _accumulator, streamed, _paused = run_streaming(universe, context)
        self.assertEqual(reference.status, FallWholePlanSearchStatus.UNRESOLVED_ALTERNATIVES)
        self.assertEqual(streamed.status, FallStreamingSearchStatus.UNRESOLVED_ALTERNATIVES)
        self.assertIn(
            "fall_hard::ordinary_credit_cap_unresolved",
            dict(streamed.unresolved_alternative_counts),
        )


if __name__ == "__main__":
    unittest.main()
