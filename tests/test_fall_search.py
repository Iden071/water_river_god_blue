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
from timetable_optimizer.fall_search import (  # noqa: E402
    FallWholePlanSearchStatus,
    search_fall_whole_plans,
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


def row(
    section_id,
    course_code,
    *,
    time="화3",
    credits=3,
    cancellation_known=True,
):
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
        scenario_id="fall-search-a",
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
        scenario_id="fall-search-scird",
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


def future_template(degree_scenario, start):
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
        "fall-search-template",
        degree_remainder(start, degree_scenario),
        FutureTimelineScenario("timeline", (term,)),
        opportunities,
    )


def temporal_policy():
    # Search tests isolate degree/coverage correctness.  Current-semester subjective utility
    # is intentionally ignored by this explicit policy while future feasibility still matters.
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


def run_search(rows, degree_scenario, *, scope=None, max_fall=1000):
    snapshot = ingest_catalog(rows, source_name="fixture", term="2026F")
    universe = build_fall_section_universe(
        "fall-search-universe",
        snapshot,
        scope=scope,
    )
    candidates = enumerate_fall_candidate_sets(
        universe,
        fall2026_load_policy(),
        max_subset_evaluations=max_fall,
    )
    start = DegreeState()
    registrations = {
        section.section_id: registration(section.section_id)
        for section in snapshot.sections
    }
    result = search_fall_whole_plans(
        candidates,
        snapshot,
        degree_scenario,
        start,
        future_template(degree_scenario, start),
        PreferenceProfile("empty"),
        ProfessorRatingBook(()),
        temporal_policy(),
        registration_assessments=registrations,
    )
    return snapshot, candidates, result


class FallWholePlanSearchTests(unittest.TestCase):
    def test_complete_full_catalog_can_prove_global_optimum(self):
        _snapshot, candidates, result = run_search(
            [
                row("A-01", "A", time="화3"),
                # Same time keeps A+B out of the feasible powerset, so only A can satisfy A.
                row("B-01", "B", time="화3"),
            ],
            course_a_scenario(),
        )

        self.assertTrue(candidates.global_search_space_complete)
        self.assertEqual(
            result.status,
            FallWholePlanSearchStatus.GLOBAL_OPTIMUM_PROVEN,
        )
        self.assertTrue(result.global_optimum_proven)
        self.assertIsNotNone(result.proven_best)
        self.assertIsNotNone(result.proven_best_branch)
        self.assertEqual(result.proven_best.complete_bounds, (0.0, 0.0))
        self.assertEqual(result.proven_best_branch.section_ids, ("A-01",))
        self.assertTrue(result.proven_unreachable_branch_ids)

    def test_complete_explicit_subset_can_only_prove_scoped_optimum(self):
        rows = [
            row("A-01", "A", time="화3"),
            row("OUTSIDE-01", "B", time="수3"),
        ]
        scope = FallSearchScope.explicit_subset(
            {"A-01"},
            source_id="user:diagnostic-shortlist",
        )
        _snapshot, candidates, result = run_search(
            rows,
            course_a_scenario(),
            scope=scope,
        )

        self.assertTrue(candidates.exact_scoped_search_space_complete)
        self.assertFalse(candidates.global_search_space_complete)
        self.assertEqual(
            result.status,
            FallWholePlanSearchStatus.SCOPED_OPTIMUM_PROVEN,
        )
        self.assertTrue(result.scoped_optimum_proven)
        self.assertFalse(result.global_optimum_proven)
        self.assertEqual(result.proven_best_branch.section_ids, ("A-01",))

    def test_truncated_fall_powerset_is_not_evaluated_as_a_shortlist(self):
        rows = [
            row("A-01", "A", time="월3"),
            row("B-01", "B", time="화3"),
            row("C-01", "C", time="수3"),
            row("D-01", "D", time="목3"),
        ]
        _snapshot, candidates, result = run_search(
            rows,
            course_a_scenario(),
            max_fall=5,
        )

        self.assertFalse(candidates.enumeration_complete)
        self.assertEqual(
            result.status,
            FallWholePlanSearchStatus.SEARCH_INCOMPLETE,
        )
        self.assertFalse(result.branch_results)
        self.assertFalse(result.utility_candidates)
        self.assertIsNone(result.proven_best)

    def test_unresolved_hard_fall_alternative_blocks_global_proof(self):
        _snapshot, _candidates, result = run_search(
            [
                row("A-01", "A", time="화3"),
                row(
                    "B-01",
                    "A",
                    time="화3",
                    cancellation_known=False,
                ),
            ],
            course_a_scenario(),
        )

        self.assertEqual(
            result.status,
            FallWholePlanSearchStatus.UNRESOLVED_ALTERNATIVES,
        )
        self.assertFalse(result.global_optimum_proven)
        self.assertIn(
            "fall_hard::cancellation_status_unresolved",
            {unknown.code for unknown in result.unresolved_alternatives},
        )
        # The exact A branch still survives for diagnostics; it just cannot become a proof.
        self.assertTrue(result.utility_candidates)

    def test_unresolved_relevant_recognition_branch_blocks_global_proof(self):
        _snapshot, _candidates, result = run_search(
            [
                row("A-01", "UIC2151", time="화3"),
                row("B-01", "ZZZ1000", time="화3"),
            ],
            scird_scenario(),
        )

        self.assertEqual(
            result.status,
            FallWholePlanSearchStatus.UNRESOLVED_ALTERNATIVES,
        )
        self.assertIn(
            "fall_transition::fall_recognition_unresolved",
            {unknown.code for unknown in result.unresolved_alternatives},
        )
        self.assertFalse(result.global_optimum_proven)

    def test_all_exact_fall_branches_can_prove_no_reachable_plan(self):
        _snapshot, candidates, result = run_search(
            [row("B-01", "B", time="화3")],
            course_a_scenario(),
        )

        self.assertTrue(candidates.global_search_space_complete)
        self.assertEqual(
            result.status,
            FallWholePlanSearchStatus.PROVEN_NO_REACHABLE_PLAN,
        )
        self.assertFalse(result.utility_candidates)
        self.assertFalse(result.unresolved_alternatives)
        self.assertTrue(result.proven_unreachable_branch_ids)

    def test_unknown_credit_survives_powerset_but_blocks_exact_fall_feasibility(self):
        _snapshot, candidates, result = run_search(
            [row("A-01", "A", time="화3", credits=None)],
            course_a_scenario(),
        )

        selected = next(
            candidate
            for candidate in candidates.candidates
            if candidate.section_ids == ("A-01",)
        )
        self.assertIn("credit::A-01", selected.enumeration_unknowns)
        self.assertEqual(
            result.status,
            FallWholePlanSearchStatus.UNRESOLVED_ALTERNATIVES,
        )
        self.assertIn(
            "fall_hard::ordinary_credit_cap_unresolved",
            {unknown.code for unknown in result.unresolved_alternatives},
        )
        self.assertFalse(result.global_optimum_proven)


if __name__ == "__main__":
    unittest.main()
