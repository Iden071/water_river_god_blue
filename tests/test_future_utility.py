import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.course_preferences import (  # noqa: E402
    ProfessorRatingBook,
    ProfessorRatingRecord,
)
from timetable_optimizer.future_opportunities import (  # noqa: E402
    FutureOffering,
    FutureOfferingEvidence,
    FutureOfferingEvidenceKind,
)
from timetable_optimizer.future_scenarios import (  # noqa: E402
    CampusAccessKind,
    CampusAccessScenario,
    FutureCatalogueBasis,
    FutureCatalogueBasisKind,
    FutureTermScenario,
    ResidenceState,
    TermActivity,
)
from timetable_optimizer.future_utility import (  # noqa: E402
    FutureTermUtilityAssessment,
    FutureUtilityError,
    FutureUtilityHistory,
    TemporalUtilityAggregation,
    TemporalUtilityWeight,
    aggregate_future_utility,
    assess_future_term_utility,
)
from timetable_optimizer.preferences import (  # noqa: E402
    PreferenceEstimate,
    PreferenceProfile,
    PreferenceProvenance,
    PreferenceSourceKind,
    PreferenceValue,
)
from timetable_optimizer.sections import (  # noqa: E402
    NoListedSchedule,
    section_from_raw,
)
from timetable_optimizer.timetable_quality import (  # noqa: E402
    extract_timetable_quality,
    extract_timetable_quality_from_parsed_schedules,
)


def row(section_id, course_code, *, time="화3", room="강의실A", campus="국제"):
    return {
        "subjtnbCorsePrcts": section_id,
        "subjtnb": course_code,
        "subjtEngNm": course_code,
        "subjtNm": course_code,
        "campsDivNm": campus,
        "cdt": 3,
        "cgprfNm": "Professor A",
        "srclnLctreLangDivCd": "10",
        "atntnMattrDesc": "",
        "gradeEvlMthdDivNm": "절대평가",
        "rmvlcYn": "0",
        "rmvlcYnNm": " ",
        "lctreTimeNm": time,
        "lecrmNm": room,
        "subjtClNm": "",
    }


def term(term_id="2027S", *, activity=TermActivity.ACTIVE):
    return FutureTermScenario(
        term_id=term_id,
        activity=activity,
        ordinary_credit_cap=18.0 if activity is TermActivity.ACTIVE else 0.0,
        residence=ResidenceState.HOME,
        campus_access=CampusAccessScenario(CampusAccessKind.ANY),
        catalogue_basis=FutureCatalogueBasis(
            FutureCatalogueBasisKind.EXPLICIT_SCENARIO
        ),
    )


def future_from_section(section, *, term_id="2027S", offering_id=None):
    return FutureOffering(
        offering_id=offering_id or f"{term_id}:{section.course_code}",
        term_id=term_id,
        course_code=section.course_code,
        credits=section.credits,
        campus=section.campus,
        schedule=section.schedule,
        professor=section.professor,
        evidence=FutureOfferingEvidence(
            FutureOfferingEvidenceKind.EXPLICIT_ASSUMPTION,
            source_id=f"scenario:{term_id}:{section.course_code}",
        ),
    )


def provenance(source_id="user:test"):
    return PreferenceProvenance(
        PreferenceSourceKind.USER_INPUT,
        source_id,
    )


def exact_value(dimension_id, value):
    return PreferenceValue(
        dimension_id,
        PreferenceEstimate.exact(value),
        provenance=provenance(f"user:{dimension_id}"),
    )


def bounded_value(dimension_id, lower, upper):
    return PreferenceValue(
        dimension_id,
        PreferenceEstimate.bounded(lower, upper),
        provenance=provenance(f"user:{dimension_id}"),
    )


def heuristic_value(dimension_id, point):
    return PreferenceValue(
        dimension_id,
        PreferenceEstimate.heuristic(point),
        provenance=provenance(f"user:{dimension_id}"),
    )


class TimetableQualityScenarioParityTests(unittest.TestCase):
    def test_parsed_schedule_extractor_matches_canonical_section_wrapper(self):
        sections = (
            section_from_raw(row("A-01", "A", time="화1,2", room="강의실A")),
            section_from_raw(row("B-01", "B", time="금7", room="실시간온라인")),
        )
        direct = extract_timetable_quality_from_parsed_schedules(
            tuple(section.schedule for section in sections)  # type: ignore[misc]
        )
        self.assertEqual(direct, extract_timetable_quality(sections))


class FutureTermUtilityTests(unittest.TestCase):
    def setUp(self):
        self.profile = PreferenceProfile("empty-profile")
        self.professors = ProfessorRatingBook(
            (
                ProfessorRatingRecord(
                    "Professor A", 0.5, "prof-sheet:Professor A"
                ),
            )
        )

    def test_nonparsed_future_schedule_is_unresolved_not_free(self):
        offering = FutureOffering(
            offering_id="2027S:UNKNOWN",
            term_id="2027S",
            course_code="UNKNOWN",
            credits=3.0,
            campus="국제",
            schedule=NoListedSchedule("", ""),
            professor="Professor A",
            evidence=FutureOfferingEvidence(
                FutureOfferingEvidenceKind.EXPLICIT_ASSUMPTION,
                source_id="scenario:unknown",
            ),
        )
        result = assess_future_term_utility(
            term(), (offering,), self.profile, self.professors
        )
        self.assertIsNone(result.timetable_utility)
        self.assertIn(
            "future_timetable_utility::2027S", result.unresolved_dimensions
        )
        self.assertIsNone(result.complete_bounds)

    def test_course_numeric_evidence_keeps_measured_and_heuristic_parts_separate(self):
        section = section_from_raw(row("A-01", "A", time="화3", room="강의실A"))
        offering = future_from_section(section)
        result = assess_future_term_utility(
            term(),
            (offering,),
            self.profile,
            self.professors,
            subject_interest={"A": exact_value("subject_interest::A", 3.0)},
            workload_utility={"A": bounded_value("workload_utility::A", -2.0, -1.0)},
            difficulty_utility={"A": heuristic_value("difficulty_utility::A", -4.0)},
        )

        # The empty timetable profile contributes no measured values; course evidence does.
        self.assertEqual(result.measured_lower, 1.0)
        self.assertEqual(result.measured_upper, 2.0)
        self.assertEqual(result.heuristic_point_delta, -4.0)
        self.assertIn(
            "professor_rating_to_utility::2027S:A", result.unresolved_dimensions
        )
        self.assertIsNone(result.complete_bounds)

    def test_known_professor_rating_is_not_silently_multiplied_by_legacy_weight(self):
        section = section_from_raw(row("A-01", "A"))
        result = assess_future_term_utility(
            term(), (future_from_section(section),), self.profile, self.professors
        )
        self.assertEqual(result.measured_lower, 0.0)
        self.assertEqual(result.measured_upper, 0.0)
        self.assertIn(
            "professor_rating_to_utility::2027S:A", result.unresolved_dimensions
        )

    def test_leave_term_is_not_scored_as_a_five_day_free_academic_timetable(self):
        result = assess_future_term_utility(
            term("military", activity=TermActivity.LEAVE),
            (),
            self.profile,
            self.professors,
        )
        self.assertFalse(result.academic_utility_applicable)
        self.assertEqual(result.complete_bounds, (0.0, 0.0))
        with self.assertRaises(FutureUtilityError):
            assess_future_term_utility(
                term("military", activity=TermActivity.LEAVE),
                (
                    FutureOffering(
                        offering_id="military:A",
                        term_id="military",
                        course_code="A",
                        credits=3.0,
                        campus="국제",
                        schedule=NoListedSchedule("", ""),
                        evidence=FutureOfferingEvidence(
                            FutureOfferingEvidenceKind.EXPLICIT_ASSUMPTION,
                            source_id="bad",
                        ),
                    ),
                ),
                self.profile,
                self.professors,
            )


class FutureTemporalAggregationTests(unittest.TestCase):
    def assessment(self, term_id, lower, upper, *, heuristic=0.0, unresolved=()):
        return FutureTermUtilityAssessment(
            term_id=term_id,
            offering_ids=(),
            timetable_facts=None,
            timetable_utility=None,
            course_preferences=(),
            course_contributions=(),
            unresolved=tuple(unresolved),
            measured_lower=lower,
            measured_upper=upper,
            heuristic_point_delta=heuristic,
            academic_utility_applicable=False,
        )

    def test_history_has_no_default_equal_weight_aggregation(self):
        history = FutureUtilityHistory(
            (self.assessment("2027S", 1, 2), self.assessment("2027F", 3, 4))
        )
        self.assertFalse(history.temporal_aggregation_resolved)
        self.assertFalse(hasattr(history, "complete_bounds"))

    def test_explicit_temporal_weights_aggregate_measured_intervals(self):
        history = FutureUtilityHistory(
            (self.assessment("2027S", 1, 2), self.assessment("2027F", 3, 4))
        )
        aggregation = TemporalUtilityAggregation(
            source_id="user:future-term-weights",
            weights=(
                TemporalUtilityWeight("2027S", 1.0),
                TemporalUtilityWeight("2027F", 0.5),
            ),
        )
        result = aggregate_future_utility(history, aggregation)
        self.assertEqual(result.measured_lower, 2.5)
        self.assertEqual(result.measured_upper, 4.0)
        self.assertEqual(result.complete_bounds, (2.5, 4.0))

    def test_temporal_weight_term_set_must_match_history(self):
        history = FutureUtilityHistory((self.assessment("2027S", 1, 2),))
        with self.assertRaises(FutureUtilityError):
            aggregate_future_utility(
                history,
                TemporalUtilityAggregation(
                    source_id="bad",
                    weights=(TemporalUtilityWeight("2027F", 1.0),),
                ),
            )


if __name__ == "__main__":
    unittest.main()
