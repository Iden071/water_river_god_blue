import sys
import unittest
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.catalog import ingest_catalog  # noqa: E402
from timetable_optimizer.course_preferences import (  # noqa: E402
    ProfessorRatingBook,
    ProfessorRatingRecord,
)
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
from timetable_optimizer.fall_streaming_search import (  # noqa: E402
    FallCandidateEvaluationContext,
)
from timetable_optimizer.fall_streaming_state import (  # noqa: E402
    fall_streaming_evaluation_signature,
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
from timetable_optimizer.model_fingerprint import model_fingerprint  # noqa: E402
from timetable_optimizer.preferences import PreferenceProfile  # noqa: E402


@dataclass(frozen=True)
class FingerprintFixture:
    name: str
    values: frozenset[int]
    mapping: dict[str, int]


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
        scenario_id="fingerprint-scenario",
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


def context(*, fall_weight=0.0, rating=None):
    catalog = ingest_catalog((row(),), source_name="fixture", term="2026F")
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
        "fingerprint-future",
        degree_remainder(start, degree_scenario),
        FutureTimelineScenario("timeline", (term,)),
        FutureOpportunityScenario(
            "opportunities",
            (
                FutureTermOpportunitySet(
                    "2027S",
                    OpportunitySetStatus.EXPLICIT_SCENARIO,
                    source_id="scenario:empty",
                ),
            ),
        ),
    )
    records = (
        (ProfessorRatingRecord("Professor", rating, "user:test"),)
        if rating is not None
        else ()
    )
    return FallCandidateEvaluationContext(
        snapshot=catalog,
        degree_scenario=degree_scenario,
        starting_state=start,
        future_template=future,
        preference_profile=PreferenceProfile("empty"),
        professor_ratings=ProfessorRatingBook(records),
        temporal_aggregation=TemporalUtilityAggregation(
            source_id="test:policy",
            weights=(
                TemporalUtilityWeight("2026F", fall_weight),
                TemporalUtilityWeight("2027S", 1.0),
            ),
        ),
        load_policy=fall2026_load_policy(),
    )


class ModelFingerprintTests(unittest.TestCase):
    def test_set_and_mapping_order_do_not_change_fingerprint(self):
        left = FingerprintFixture("x", frozenset({1, 2, 3}), {"a": 1, "b": 2})
        right = FingerprintFixture("x", frozenset({3, 2, 1}), {"b": 2, "a": 1})
        self.assertEqual(
            model_fingerprint(left, contract="test-v1"),
            model_fingerprint(right, contract="test-v1"),
        )

    def test_semantic_change_changes_fingerprint(self):
        left = FingerprintFixture("x", frozenset({1, 2}), {"a": 1})
        right = FingerprintFixture("x", frozenset({1, 2}), {"a": 2})
        self.assertNotEqual(
            model_fingerprint(left, contract="test-v1"),
            model_fingerprint(right, contract="test-v1"),
        )

    def test_contract_version_is_part_of_fingerprint(self):
        value = FingerprintFixture("x", frozenset({1}), {})
        self.assertNotEqual(
            model_fingerprint(value, contract="test-v1"),
            model_fingerprint(value, contract="test-v2"),
        )

    def test_real_streaming_context_is_fingerprintable_and_deterministic(self):
        left = context()
        right = context()
        self.assertEqual(
            fall_streaming_evaluation_signature(left),
            fall_streaming_evaluation_signature(right),
        )

    def test_objective_or_manual_preference_change_invalidates_evaluation_signature(self):
        baseline = fall_streaming_evaluation_signature(context())
        different_weight = fall_streaming_evaluation_signature(context(fall_weight=1.0))
        different_rating = fall_streaming_evaluation_signature(context(rating=0.5))
        self.assertNotEqual(baseline, different_weight)
        self.assertNotEqual(baseline, different_rating)


if __name__ == "__main__":
    unittest.main()
