import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.preferences import (  # noqa: E402
    EstimateStatus,
    LinearPreferenceRelation,
    LinearPreferenceTerm,
    PreferenceEstimate,
    PreferenceProfile,
    PreferenceProvenance,
    PreferenceRelationKind,
    PreferenceRuleError,
    PreferenceSourceKind,
    PreferenceValue,
)


class PreferenceProvenanceTests(unittest.TestCase):
    def test_user_supplied_exact_value_is_allowed(self):
        value = PreferenceValue(
            dimension_id="friday_free",
            estimate=PreferenceEstimate.exact(8.0),
            provenance=PreferenceProvenance(
                PreferenceSourceKind.USER_INPUT,
                source_id="user-comparison-001",
                description="User directly valued keeping Friday free.",
            ),
        )
        self.assertEqual(value.estimate.require_exact(), 8.0)

    def test_derived_value_requires_transparent_derivation(self):
        with self.assertRaises(PreferenceRuleError):
            PreferenceProvenance(
                PreferenceSourceKind.DERIVED,
                source_id="derived-001",
            )

        provenance = PreferenceProvenance(
            PreferenceSourceKind.DERIVED,
            source_id="derived-002",
            derivation="Difference between two user-rated timetable states.",
        )
        self.assertEqual(provenance.source_kind, PreferenceSourceKind.DERIVED)

    def test_numeric_value_without_provenance_is_rejected(self):
        with self.assertRaises(PreferenceRuleError):
            PreferenceValue(
                dimension_id="late_finish",
                estimate=PreferenceEstimate.exact(-3.0),
            )


class PreferenceEstimateTests(unittest.TestCase):
    def test_unmeasured_is_not_zero(self):
        value = PreferenceValue(
            dimension_id="unknown_workload",
            estimate=PreferenceEstimate.unmeasured(),
        )
        self.assertEqual(value.estimate.status, EstimateStatus.UNMEASURED)
        self.assertIsNone(value.estimate.point)
        self.assertIsNone(value.estimate.bounds)
        with self.assertRaises(PreferenceRuleError):
            value.estimate.require_exact()

    def test_bounded_interval_preserves_uncertainty(self):
        estimate = PreferenceEstimate.bounded(-6.0, -2.0)
        self.assertEqual(estimate.status, EstimateStatus.BOUNDED)
        self.assertEqual(estimate.bounds, (-6.0, -2.0))
        self.assertIsNone(estimate.point)
        with self.assertRaises(PreferenceRuleError):
            estimate.require_exact()

    def test_invalid_interval_is_rejected(self):
        with self.assertRaises(PreferenceRuleError):
            PreferenceEstimate.bounded(2.0, -2.0)

    def test_heuristic_status_cannot_be_silently_treated_as_exact(self):
        estimate = PreferenceEstimate.heuristic(4.0, lower=2.0, upper=6.0)
        self.assertEqual(estimate.status, EstimateStatus.HEURISTIC)
        self.assertEqual(estimate.point, 4.0)
        with self.assertRaises(PreferenceRuleError):
            estimate.require_exact()

    def test_nonfinite_numbers_are_rejected(self):
        for value in (math.inf, -math.inf, math.nan):
            with self.subTest(value=value):
                with self.assertRaises(PreferenceRuleError):
                    PreferenceEstimate.exact(value)

    def test_unmeasured_cannot_hide_numeric_payload(self):
        with self.assertRaises(PreferenceRuleError):
            PreferenceEstimate(EstimateStatus.UNMEASURED, point=0.0)


class PreferenceRelationTests(unittest.TestCase):
    def setUp(self):
        self.user_source = PreferenceProvenance(
            PreferenceSourceKind.USER_INPUT,
            source_id="comparison-001",
            description="User compared missing dinner against missing lunch.",
        )

    def test_qualitative_relation_does_not_require_absolute_weights(self):
        relation = LinearPreferenceRelation(
            terms=(
                LinearPreferenceTerm("missing_dinner", 1.0),
                LinearPreferenceTerm("missing_lunch", -1.0),
            ),
            relation=PreferenceRelationKind.LESS_THAN,
            rhs=0.0,
            provenance=self.user_source,
        )
        self.assertEqual(relation.relation, PreferenceRelationKind.LESS_THAN)
        self.assertEqual(len(relation.terms), 2)

    def test_linear_relation_can_store_ratio_or_difference_claim(self):
        relation = LinearPreferenceRelation(
            terms=(
                LinearPreferenceTerm("monday_trip", 1.0),
                LinearPreferenceTerm("friday_trip", -0.75),
            ),
            relation=PreferenceRelationKind.EQUAL,
            rhs=0.0,
            provenance=self.user_source,
        )
        self.assertEqual(relation.rhs, 0.0)

    def test_relation_rejects_empty_terms(self):
        with self.assertRaises(PreferenceRuleError):
            LinearPreferenceRelation(
                terms=(),
                relation=PreferenceRelationKind.EQUAL,
                rhs=0.0,
                provenance=self.user_source,
            )

    def test_relation_rejects_duplicate_dimensions(self):
        with self.assertRaises(PreferenceRuleError):
            LinearPreferenceRelation(
                terms=(
                    LinearPreferenceTerm("rest", 1.0),
                    LinearPreferenceTerm("rest", -1.0),
                ),
                relation=PreferenceRelationKind.EQUAL,
                rhs=0.0,
                provenance=self.user_source,
            )

    def test_relation_rejects_nonfinite_rhs_or_coefficient(self):
        with self.assertRaises(PreferenceRuleError):
            LinearPreferenceTerm("rest", math.inf)
        with self.assertRaises(PreferenceRuleError):
            LinearPreferenceRelation(
                terms=(LinearPreferenceTerm("rest"),),
                relation=PreferenceRelationKind.EQUAL,
                rhs=math.nan,
                provenance=self.user_source,
            )


class PreferenceProfileTests(unittest.TestCase):
    def test_profile_preserves_unmeasured_dimensions(self):
        profile = PreferenceProfile(
            profile_id="test",
            values=(
                PreferenceValue(
                    dimension_id="workload",
                    estimate=PreferenceEstimate.unmeasured(),
                ),
            ),
        )
        self.assertEqual(profile.unmeasured_dimensions, frozenset({"workload"}))
        self.assertEqual(profile.value("workload").estimate.status, EstimateStatus.UNMEASURED)

    def test_profile_rejects_duplicate_scalar_dimensions(self):
        with self.assertRaises(PreferenceRuleError):
            PreferenceProfile(
                profile_id="test",
                values=(
                    PreferenceValue("workload", PreferenceEstimate.unmeasured()),
                    PreferenceValue("workload", PreferenceEstimate.unmeasured()),
                ),
            )

    def test_profile_lookup_rejects_missing_dimension(self):
        profile = PreferenceProfile(profile_id="test")
        with self.assertRaises(PreferenceRuleError):
            profile.value("missing")


if __name__ == "__main__":
    unittest.main()
