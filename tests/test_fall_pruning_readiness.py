import unittest

from timetable_optimizer.course_preferences import (
    ProfessorRatingBook,
    ProfessorRatingRecord,
)
from timetable_optimizer.fall2026_course_bounds import fall2026_course_utility_bounds
from timetable_optimizer.fall_pruning_readiness import (
    FallPruningBlockerKind,
    FallPruningReadinessError,
    FallPruningReadinessStatus,
    audit_fall_pruning_readiness,
)
from timetable_optimizer.fall_universe import FallSearchScope, FallSectionUniverse
from timetable_optimizer.preferences import (
    PreferenceEstimate,
    PreferenceProfile,
    PreferenceProvenance,
    PreferenceSourceKind,
    PreferenceValue,
)
from timetable_optimizer.registration import (
    ObtainabilityEstimate,
    ObtainabilityStatus,
    RegistrationAssessment,
    RegistrationRegime,
    YearQuotaGateStatus,
)
from timetable_optimizer.sections import ParsedSchedule, Section
from timetable_optimizer.timetable_utility import timetable_preference_dimension_contract


def section(section_id="A"):
    schedule = ParsedSchedule(
        raw_time_text="화3",
        raw_room_text="A",
        segments=(),
        conflict_mask=1,
        presence_mask=1,
        fixed_mask=1,
    )
    return Section(
        section_id=section_id,
        course_code="COURSE-A",
        name="Course A",
        korean_name="Course A",
        campus="국제",
        credits=3.0,
        professor="Professor",
        language_code="",
        note="",
        grading="",
        cancelled=False,
        mode_text="대면",
        schedule=schedule,
        language_name="영어",
    )


def universe(item):
    return FallSectionUniverse(
        universe_id="pruning-readiness",
        scope=FallSearchScope.explicit_subset(
            {item.section_id},
            source_id="test:core",
        ),
        source_name="fixture",
        source_fingerprint="fixture-v1",
        included_sections=(item,),
        hard_exclusions=(),
        scoped_out_section_ids=frozenset(),
        global_catalogue_unknowns=(),
        scope_unknowns=(),
        known_physical_section_ids=frozenset({item.section_id}),
    )


def provenance(source_id="user:test"):
    return PreferenceProvenance(
        PreferenceSourceKind.USER_INPUT,
        source_id,
    )


def exact_value(dimension, point):
    return PreferenceValue(
        dimension,
        PreferenceEstimate.exact(point),
        provenance(),
    )


def bounded_value(dimension, lower, upper):
    return PreferenceValue(
        dimension,
        PreferenceEstimate.bounded(lower, upper),
        provenance(),
    )


def complete_timetable_profile(*, overrides=(), extras=()):
    values = {
        dimension: exact_value(dimension, 0.0)
        for dimension in timetable_preference_dimension_contract()
    }
    for value in overrides:
        values[value.dimension_id] = value
    ordered = tuple(values[dimension] for dimension in sorted(values)) + tuple(extras)
    return PreferenceProfile("complete-timetable-fixture", values=ordered)


def resolved_registration(section_id="A"):
    return RegistrationAssessment(
        section_id=section_id,
        regime=RegistrationRegime.FRESHMAN_WAITLIST,
        year_quota_status=YearQuotaGateStatus.NO_YEAR_SCHEME,
        freshman_quota=None,
        obtainability=ObtainabilityEstimate(
            status=ObtainabilityStatus.BOUNDED,
            lower=0.2,
            upper=0.9,
            basis="test bounded evidence",
        ),
        quota_source_id="test:quota",
    )


class FallPruningReadinessTests(unittest.TestCase):
    def test_missing_temporal_weight_is_separate_from_unbounded_dimensions(self):
        item = section()
        result = audit_fall_pruning_readiness(
            universe(item),
            PreferenceProfile("empty"),
            ProfessorRatingBook(()),
            fall_weight=None,
        )
        self.assertEqual(
            result.status,
            FallPruningReadinessStatus.OBJECTIVE_UNRESOLVED,
        )
        self.assertIn(
            "temporal_weight::2026F",
            {item.dimension for item in result.blocker_families},
        )
        # The objective-definition problem does not hide latent section-local or timetable
        # evidence problems; both remain visible for the repair queue.
        self.assertIn(
            "professor_rating_to_utility",
            {item.dimension for item in result.section_local_blockers},
        )
        self.assertIn(
            "long_fixed_run_shape",
            {item.dimension for item in result.timetable_profile_blockers},
        )

    def test_positive_fall_weight_with_default_missing_course_evidence_blocks_bound(self):
        item = section()
        result = audit_fall_pruning_readiness(
            universe(item),
            PreferenceProfile("empty"),
            ProfessorRatingBook(()),
            fall_weight=1.0,
        )
        self.assertEqual(
            result.status,
            FallPruningReadinessStatus.PRESENT_BOUND_BLOCKED,
        )
        dimensions = {item.dimension for item in result.section_local_blockers}
        self.assertTrue(
            {
                "professor_rating",
                "professor_rating_to_utility",
                "subject_interest",
                "workload",
                "difficulty",
                "registration_obtainability",
            }
            <= dimensions
        )

    def test_zero_fall_weight_does_not_require_present_utility_bounds(self):
        item = section()
        result = audit_fall_pruning_readiness(
            universe(item),
            PreferenceProfile("empty"),
            ProfessorRatingBook(()),
            fall_weight=0.0,
        )
        self.assertEqual(
            result.status,
            FallPruningReadinessStatus.FALL_WEIGHT_ZERO,
        )
        self.assertTrue(result.present_numeric_bound_available)
        # Diagnostics are still retained; zero weight does not pretend the evidence exists.
        self.assertTrue(result.section_local_blockers)
        self.assertTrue(result.timetable_profile_blockers)

    def test_exact_bounded_inputs_can_make_present_bound_ready(self):
        item = section()
        ratings = ProfessorRatingBook(
            (ProfessorRatingRecord("Professor", 0.5, "user:rating"),)
        )
        result = audit_fall_pruning_readiness(
            universe(item),
            complete_timetable_profile(),
            ratings,
            fall_weight=1.0,
            registration_assessments={"A": resolved_registration()},
            subject_interest={
                "COURSE-A": bounded_value("subject_interest::COURSE-A", -2.0, 4.0)
            },
            workload_utility={
                "COURSE-A": exact_value("workload_utility::COURSE-A", -1.0)
            },
            difficulty_utility={
                "COURSE-A": bounded_value("difficulty_utility::COURSE-A", -3.0, 0.0)
            },
            resolved_present_dimensions={
                "course::A::professor_rating_to_utility": bounded_value(
                    "course::A::professor_rating_to_utility", -2.0, 2.0
                ),
            },
        )
        self.assertEqual(
            result.status,
            FallPruningReadinessStatus.PRESENT_BOUND_READY,
        )
        self.assertFalse(result.blocker_families)

    def test_global_course_bounds_remove_intrinsic_course_blockers_without_faking_ratings(self):
        item = section()
        result = audit_fall_pruning_readiness(
            universe(item),
            PreferenceProfile("empty"),
            ProfessorRatingBook(()),
            fall_weight=1.0,
            global_course_utility_bounds=fall2026_course_utility_bounds(),
        )
        dimensions = {item.dimension for item in result.section_local_blockers}
        self.assertEqual(dimensions, {"registration_obtainability"})
        self.assertEqual(
            result.status,
            FallPruningReadinessStatus.PRESENT_BOUND_BLOCKED,
        )

    def test_global_course_bounds_plus_bounded_registration_can_make_present_bound_ready(self):
        item = section()
        result = audit_fall_pruning_readiness(
            universe(item),
            complete_timetable_profile(),
            ProfessorRatingBook(()),
            fall_weight=1.0,
            registration_assessments={"A": resolved_registration()},
            global_course_utility_bounds=fall2026_course_utility_bounds(),
        )
        self.assertEqual(
            result.status,
            FallPruningReadinessStatus.PRESENT_BOUND_READY,
        )
        self.assertFalse(result.blocker_families)

    def test_global_course_bound_typos_or_nonproof_values_are_rejected(self):
        item = section()
        with self.assertRaises(FallPruningReadinessError):
            audit_fall_pruning_readiness(
                universe(item),
                PreferenceProfile("empty"),
                ProfessorRatingBook(()),
                fall_weight=1.0,
                global_course_utility_bounds={
                    "typo": bounded_value("typo", -1.0, 1.0)
                },
            )

        heuristic = PreferenceValue(
            "global_course_bound::workload",
            PreferenceEstimate.heuristic(-2.0, lower=-15.0, upper=0.0),
            provenance(),
        )
        with self.assertRaises(FallPruningReadinessError):
            audit_fall_pruning_readiness(
                universe(item),
                PreferenceProfile("empty"),
                ProfessorRatingBook(()),
                fall_weight=1.0,
                global_course_utility_bounds={"workload": heuristic},
            )

    def test_heuristic_activatable_timetable_scalar_remains_proof_blocker(self):
        item = section()
        heuristic = PreferenceValue(
            "friday_event_window_free",
            PreferenceEstimate.heuristic(-2.0, lower=-3.0, upper=-1.0),
            provenance(),
        )
        result = audit_fall_pruning_readiness(
            universe(item),
            complete_timetable_profile(overrides=(heuristic,)),
            ProfessorRatingBook(()),
            fall_weight=1.0,
        )
        profile = [
            blocker
            for blocker in result.blocker_families
            if blocker.kind is FallPruningBlockerKind.TIMETABLE_PROFILE
        ]
        self.assertIn("friday_event_window_free", {item.dimension for item in profile})

    def test_unrelated_profile_placeholder_is_not_a_timetable_bound_blocker(self):
        item = section()
        placeholder = PreferenceValue(
            "chapel_timing_advantage",
            PreferenceEstimate.unmeasured(),
            label="separate state-consequence placeholder",
        )
        result = audit_fall_pruning_readiness(
            universe(item),
            complete_timetable_profile(extras=(placeholder,)),
            ProfessorRatingBook(()),
            fall_weight=1.0,
            registration_assessments={"A": resolved_registration()},
            global_course_utility_bounds=fall2026_course_utility_bounds(),
        )
        self.assertNotIn(
            "chapel_timing_advantage",
            {item.dimension for item in result.timetable_profile_blockers},
        )
        self.assertEqual(result.status, FallPruningReadinessStatus.PRESENT_BOUND_READY)

    def test_missing_activatable_dimension_is_caught_even_if_profile_omits_it(self):
        item = section()
        values = tuple(
            exact_value(dimension, 0.0)
            for dimension in sorted(timetable_preference_dimension_contract())
            if dimension != "long_fixed_run_shape"
        )
        result = audit_fall_pruning_readiness(
            universe(item),
            PreferenceProfile("missing-long-run", values=values),
            ProfessorRatingBook(()),
            fall_weight=1.0,
            registration_assessments={"A": resolved_registration()},
            global_course_utility_bounds=fall2026_course_utility_bounds(),
        )
        blockers = {item.dimension for item in result.timetable_profile_blockers}
        self.assertEqual(blockers, {"long_fixed_run_shape"})
        self.assertEqual(result.status, FallPruningReadinessStatus.PRESENT_BOUND_BLOCKED)


if __name__ == "__main__":
    unittest.main()
