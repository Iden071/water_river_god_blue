import unittest

from timetable_optimizer.fall2026_course_bounds import fall2026_course_utility_bounds
from timetable_optimizer.fall2026_preferences import fall2026_preference_profile
from timetable_optimizer.fall2026_timetable_bounds import (
    fall2026_timetable_proof_upper_bounds,
)
from timetable_optimizer.fall_upper_bound_readiness import (
    FallUpperBoundError,
    FallUpperBoundStatus,
    ProofUpperBound,
    audit_fall_intrinsic_upper_bound_readiness,
)
from timetable_optimizer.preferences import PreferenceProfile


class FallIntrinsicUpperBoundReadinessTests(unittest.TestCase):
    def test_current_real_profile_has_only_three_conceptual_timetable_blocker_families(self):
        result = audit_fall_intrinsic_upper_bound_readiness(
            fall2026_preference_profile(),
            global_course_utility_bounds=fall2026_course_utility_bounds(),
        )
        self.assertEqual(result.status, FallUpperBoundStatus.BLOCKED)
        self.assertTrue(result.registration_risk_layer_separate)
        self.assertEqual(
            set(result.conceptual_timetable_blocker_families),
            {
                "friday_event_value",
                "fixed_run_shape",
                "weekend_attached_run_shape",
            },
        )
        self.assertFalse(result.missing_course_bound_dimensions)

    def test_current_user_confirmed_one_sided_bounds_remove_run_blocker_family(self):
        result = audit_fall_intrinsic_upper_bound_readiness(
            fall2026_preference_profile(),
            global_course_utility_bounds=fall2026_course_utility_bounds(),
            explicit_timetable_upper_bounds=fall2026_timetable_proof_upper_bounds(),
        )
        self.assertEqual(result.status, FallUpperBoundStatus.BLOCKED)
        self.assertEqual(
            set(result.conceptual_timetable_blocker_families),
            {"friday_event_value", "weekend_attached_run_shape"},
        )
        self.assertNotIn("three_fixed_period_run", result.missing_timetable_dimensions)
        self.assertFalse(
            any(
                dimension.startswith("long_fixed_run_delta_")
                for dimension in result.missing_timetable_dimensions
            )
        )
        run_bounds = {
            bound.dimension_id: bound
            for bound in result.timetable_upper_bounds
            if bound.dimension_id == "three_fixed_period_run"
            or bound.dimension_id.startswith("long_fixed_run_delta_")
        }
        self.assertEqual(len(run_bounds), 12)
        self.assertTrue(all(bound.upper == 0.0 for bound in run_bounds.values()))

    def test_one_sided_upper_bounds_can_make_intrinsic_audit_ready_without_fake_points(self):
        profile = fall2026_preference_profile()
        first = audit_fall_intrinsic_upper_bound_readiness(
            profile,
            global_course_utility_bounds=fall2026_course_utility_bounds(),
        )
        explicit = {
            dimension: ProofUpperBound(
                dimension_id=dimension,
                upper=100.0,
                source_id="user:test-conservative-upper",
                justification="Test-only deliberately loose proof ceiling.",
            )
            for dimension in first.missing_timetable_dimensions
        }
        result = audit_fall_intrinsic_upper_bound_readiness(
            profile,
            global_course_utility_bounds=fall2026_course_utility_bounds(),
            explicit_timetable_upper_bounds=explicit,
        )
        self.assertEqual(result.status, FallUpperBoundStatus.READY)
        self.assertTrue(result.intrinsic_upper_bound_ready)
        self.assertFalse(result.missing_timetable_dimensions)
        # Registration remains a separate unsolved layer even when intrinsic pruning is ready.
        self.assertTrue(result.registration_risk_layer_separate)

    def test_missing_course_envelopes_are_separate_from_timetable_shape(self):
        result = audit_fall_intrinsic_upper_bound_readiness(
            fall2026_preference_profile(),
            global_course_utility_bounds={},
        )
        self.assertEqual(
            set(result.missing_course_bound_dimensions),
            {"professor_rating_to_utility", "subject_interest", "workload", "difficulty"},
        )

    def test_unmeasured_profile_is_not_silently_given_zero_upper_bound(self):
        result = audit_fall_intrinsic_upper_bound_readiness(
            PreferenceProfile("empty"),
            global_course_utility_bounds=fall2026_course_utility_bounds(),
        )
        self.assertTrue(result.missing_timetable_dimensions)
        self.assertIn("friday_event_window_free", result.missing_timetable_dimensions)
        self.assertIn("three_fixed_period_run", result.missing_timetable_dimensions)

    def test_explicit_upper_bound_requires_matching_activatable_dimension(self):
        bad = ProofUpperBound(
            "not_a_timetable_dimension",
            0.0,
            "test:bad",
            "Test invalid dimension.",
        )
        with self.assertRaises(FallUpperBoundError):
            audit_fall_intrinsic_upper_bound_readiness(
                fall2026_preference_profile(),
                global_course_utility_bounds=fall2026_course_utility_bounds(),
                explicit_timetable_upper_bounds={"not_a_timetable_dimension": bad},
            )


if __name__ == "__main__":
    unittest.main()
