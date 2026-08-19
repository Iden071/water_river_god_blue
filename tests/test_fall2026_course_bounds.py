import unittest

from timetable_optimizer.fall2026_course_bounds import (
    DIFFICULTY_BOUND,
    PROFESSOR_UTILITY_BOUND,
    SUBJECT_INTEREST_BOUND,
    WORKLOAD_BOUND,
    fall2026_course_utility_bounds,
)
from timetable_optimizer.preferences import EstimateStatus, PreferenceSourceKind


class Fall2026CourseUtilityBoundTests(unittest.TestCase):
    def setUp(self):
        self.bounds = fall2026_course_utility_bounds()

    def test_expected_four_course_dimensions_are_bounded(self):
        self.assertEqual(
            set(self.bounds),
            {
                PROFESSOR_UTILITY_BOUND,
                SUBJECT_INTEREST_BOUND,
                WORKLOAD_BOUND,
                DIFFICULTY_BOUND,
            },
        )
        self.assertTrue(
            all(
                value.estimate.status is EstimateStatus.BOUNDED
                for value in self.bounds.values()
            )
        )

    def test_one_sided_burden_bounds_use_neutral_zero_as_upper_limit(self):
        self.assertEqual(self.bounds[WORKLOAD_BOUND].estimate.bounds, (-15.0, 0.0))
        self.assertEqual(self.bounds[DIFFICULTY_BOUND].estimate.bounds, (-5.0, 0.0))

    def test_professor_and_interest_are_conservative_outer_envelopes(self):
        # The user supplied <=8 / <=3 true best-to-worst spans.  Because neutral=0
        # may lie anywhere inside those unknown ranges, [-8,+8] and [-3,+3] are
        # deliberately looser outer envelopes, not assertions of 16/6-point spans.
        self.assertEqual(
            self.bounds[PROFESSOR_UTILITY_BOUND].estimate.bounds,
            (-8.0, 8.0),
        )
        self.assertEqual(
            self.bounds[SUBJECT_INTEREST_BOUND].estimate.bounds,
            (-3.0, 3.0),
        )

    def test_every_numeric_bound_has_transparent_derived_provenance(self):
        for value in self.bounds.values():
            self.assertIsNotNone(value.provenance)
            assert value.provenance is not None
            self.assertIs(value.provenance.source_kind, PreferenceSourceKind.DERIVED)
            self.assertIn("2026-08-19", value.provenance.source_id)
            self.assertTrue(value.provenance.derivation)

    def test_mapping_is_read_only(self):
        with self.assertRaises(TypeError):
            self.bounds["new"] = self.bounds[WORKLOAD_BOUND]  # type: ignore[index]


if __name__ == "__main__":
    unittest.main()
