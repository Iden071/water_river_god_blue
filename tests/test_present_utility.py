import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.candidate_assessment import (  # noqa: E402
    CandidateAssessment,
    CandidateConstraintIssue,
    CandidateLoadFacts,
    ConstraintEvidenceStatus,
)
from timetable_optimizer.course_preferences import (  # noqa: E402
    ProfessorRatingLookup,
    ProfessorRatingStatus,
    SectionCoursePreferenceEvidence,
)
from timetable_optimizer.preferences import (  # noqa: E402
    EstimateStatus,
    PreferenceEstimate,
    PreferenceProvenance,
    PreferenceSourceKind,
    PreferenceValue,
)
from timetable_optimizer.present_utility import (  # noqa: E402
    PresentUtilityError,
    assess_present_candidate_utility,
)
from timetable_optimizer.timetable_utility import (  # noqa: E402
    PartialUtilityAssessment,
    UnresolvedUtilityDimension,
    UtilityContribution,
)


def provenance(source_id):
    return PreferenceProvenance(PreferenceSourceKind.USER_INPUT, source_id)


def exact(dimension_id, value):
    return PreferenceValue(
        dimension_id,
        PreferenceEstimate.exact(value),
        provenance=provenance(f"user:{dimension_id}"),
    )


def bounded(dimension_id, lower, upper):
    return PreferenceValue(
        dimension_id,
        PreferenceEstimate.bounded(lower, upper),
        provenance=provenance(f"user:{dimension_id}"),
    )


def heuristic(dimension_id, point):
    return PreferenceValue(
        dimension_id,
        PreferenceEstimate.heuristic(point),
        provenance=provenance(f"user:{dimension_id}"),
    )


def candidate(*, course_preferences=(), unknowns=(), hard_issues=(), timetable=None):
    if timetable is None:
        timetable = PartialUtilityAssessment(
            contributions=(
                UtilityContribution(
                    dimension_id="timetable:test",
                    quantity=1.0,
                    status=EstimateStatus.EXACT,
                    lower=1.0,
                    upper=1.0,
                    point=1.0,
                    provenance=provenance("user:timetable:test"),
                ),
            ),
            unresolved=(),
            active_relations=(),
            measured_lower=1.0,
            measured_upper=1.0,
            heuristic_point_delta=0.0,
        )
    return CandidateAssessment(
        section_ids=("A-01",),
        load=CandidateLoadFacts(3.0, 3.0, 0.0, ()),
        timetable_facts=None,
        timetable_utility=timetable,
        course_preferences=tuple(course_preferences),
        travel_facts=None,
        registration=(),
        recognition=(),
        degree_transition=None,
        hard_constraint_issues=tuple(hard_issues),
        present_preference_unknowns=frozenset(unknowns),
        future_unknowns=frozenset(),
    )


class PresentUtilityTests(unittest.TestCase):
    def course_evidence(self):
        return SectionCoursePreferenceEvidence(
            section_id="A-01",
            course_code="A",
            professor=ProfessorRatingLookup(
                professor="Professor A",
                status=ProfessorRatingStatus.RATED,
                rating=0.5,
                source_id="prof:A",
            ),
            subject_interest=exact("subject_interest::A", 3.0),
            workload_utility=bounded("workload_utility::A", -2.0, -1.0),
            difficulty_utility=heuristic("difficulty_utility::A", -4.0),
        )

    def test_numeric_course_evidence_joins_timetable_interval_without_absorbing_heuristic(self):
        assessment = assess_present_candidate_utility(
            candidate(
                course_preferences=(self.course_evidence(),),
                unknowns=("course::A-01::professor_rating_to_utility",),
            )
        )

        self.assertEqual(assessment.measured_lower, 2.0)
        self.assertEqual(assessment.measured_upper, 3.0)
        self.assertEqual(assessment.heuristic_point_delta, -4.0)
        self.assertIn(
            "course::A-01::professor_rating_to_utility",
            assessment.unresolved_dimensions,
        )
        self.assertIsNone(assessment.complete_bounds)

    def test_explicit_resolution_must_target_an_existing_unknown(self):
        base = candidate(unknowns=("registration_obtainability::A-01",))
        resolved = assess_present_candidate_utility(
            base,
            resolved_dimensions={
                "registration_obtainability::A-01": exact("registration", -2.0)
            },
        )
        self.assertEqual(resolved.complete_bounds, (-1.0, -1.0))

        with self.assertRaises(PresentUtilityError):
            assess_present_candidate_utility(
                base,
                resolved_dimensions={"made_up_bonus": exact("bonus", 100.0)},
            )

    def test_unresolved_timetable_quantity_is_preserved_not_collapsed_to_name(self):
        timetable = PartialUtilityAssessment(
            contributions=(),
            unresolved=(
                UnresolvedUtilityDimension(
                    dimension_id="three_fixed_period_run",
                    quantity=4.0,
                    reason="magnitude not elicited",
                    label="Three-period continuous run",
                ),
            ),
            active_relations=(),
            measured_lower=0.0,
            measured_upper=0.0,
            heuristic_point_delta=0.0,
        )
        assessment = assess_present_candidate_utility(
            candidate(
                timetable=timetable,
                unknowns=("timetable::three_fixed_period_run",),
            )
        )

        self.assertEqual(
            assessment.unresolved_dimensions,
            frozenset({"timetable::three_fixed_period_run"}),
        )
        self.assertEqual(len(assessment.unresolved_timetable_terms), 1)
        term = assessment.unresolved_timetable_terms[0]
        self.assertEqual(term.dimension_id, "timetable::three_fixed_period_run")
        self.assertEqual(term.quantity, 4.0)

    def test_resolving_timetable_scalar_multiplies_preserved_quantity(self):
        timetable = PartialUtilityAssessment(
            contributions=(),
            unresolved=(
                UnresolvedUtilityDimension(
                    dimension_id="three_fixed_period_run",
                    quantity=4.0,
                    reason="magnitude not elicited",
                ),
            ),
            active_relations=(),
            measured_lower=0.0,
            measured_upper=0.0,
            heuristic_point_delta=0.0,
        )
        base = candidate(
            timetable=timetable,
            unknowns=("timetable::three_fixed_period_run",),
        )
        resolved = assess_present_candidate_utility(
            base,
            resolved_dimensions={
                "timetable::three_fixed_period_run": exact(
                    "three_fixed_period_run", -0.5
                )
            },
        )

        self.assertEqual(resolved.complete_bounds, (-2.0, -2.0))
        self.assertFalse(resolved.unresolved_timetable_terms)
        contribution = next(
            item
            for item in resolved.contributions
            if item.dimension_id == "timetable::three_fixed_period_run"
        )
        self.assertEqual(contribution.quantity, 4.0)
        self.assertEqual(contribution.point, -2.0)

    def test_hard_feasibility_unknown_blocks_whole_term_bounds_even_when_utility_is_exact(self):
        issue = CandidateConstraintIssue(
            code="travel_feasibility_unresolved",
            status=ConstraintEvidenceStatus.UNRESOLVED,
            message="test unresolved travel",
        )
        assessment = assess_present_candidate_utility(
            candidate(hard_issues=(issue,))
        )
        self.assertFalse(assessment.hard_feasibility_resolved)
        self.assertIsNone(assessment.complete_bounds)

    def test_zero_point_heuristic_is_still_not_exact(self):
        timetable = PartialUtilityAssessment(
            contributions=(
                UtilityContribution(
                    dimension_id="shape",
                    quantity=1.0,
                    status=EstimateStatus.HEURISTIC,
                    point=0.0,
                    provenance=provenance("user:shape"),
                ),
            ),
            unresolved=(),
            active_relations=(),
            measured_lower=0.0,
            measured_upper=0.0,
            heuristic_point_delta=0.0,
        )
        assessment = assess_present_candidate_utility(
            candidate(
                timetable=timetable,
                unknowns=("timetable_heuristic_terms",),
            )
        )
        self.assertTrue(assessment.has_heuristics)
        self.assertIsNone(assessment.complete_bounds)


if __name__ == "__main__":
    unittest.main()
