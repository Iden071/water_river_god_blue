import unittest

from timetable_optimizer.fall2026_course_bounds import fall2026_course_utility_bounds
from timetable_optimizer.fall2026_preferences import fall2026_preference_profile
from timetable_optimizer.fall_bitset_enumeration import FallBitsetFrame
from timetable_optimizer.fall_candidate_sets import FallLoadPolicy
from timetable_optimizer.fall_intrinsic_branch_bound import (
    FallIntrinsicBranchBoundStatus,
    derive_fall_intrinsic_branch_upper_bound,
)
from timetable_optimizer.fall_upper_bound_readiness import (
    ProofUpperBound,
    audit_fall_intrinsic_upper_bound_readiness,
)
from timetable_optimizer.fall_universe import FallSearchScope, FallSectionUniverse
from timetable_optimizer.preferences import (
    PreferenceEstimate,
    PreferenceProfile,
    PreferenceProvenance,
    PreferenceSourceKind,
    PreferenceValue,
)
from timetable_optimizer.sections import section_from_raw


def row(section_id, time, credits=3.0):
    return {
        "subjtnbCorsePrcts": section_id,
        "subjtnb": section_id.split("-")[0],
        "subjtEngNm": "TEST COURSE",
        "subjtNm": "테스트",
        "campsDivNm": "국제",
        "cdt": credits,
        "cgprfNm": "Professor",
        "srclnLctreLangDivCd": "10",
        "atntnMattrDesc": "",
        "gradeEvlMthdDivNm": "절대평가",
        "rmvlcYn": "0",
        "rmvlcYnNm": " ",
        "lctreTimeNm": time,
        "lecrmNm": "강의실A" if time else "",
        "subjtClNm": "대면",
    }


def make_universe(*sections):
    ordered = tuple(sorted(sections, key=lambda item: item.section_id))
    ids = frozenset(item.section_id for item in ordered)
    return FallSectionUniverse(
        universe_id="branch-bound-fixture",
        scope=FallSearchScope.explicit_subset(ids, source_id="test:bound-fixture"),
        source_name="fixture",
        source_fingerprint="fixture-v1",
        included_sections=ordered,
        hard_exclusions=(),
        scoped_out_section_ids=frozenset(),
        global_catalogue_unknowns=(),
        scope_unknowns=(),
        known_physical_section_ids=ids,
    )


def policy(cap=22.0):
    return FallLoadPolicy(
        ordinary_credit_cap=cap,
        chapel_exempt_from_ordinary_cap=True,
        source_id="test:load-policy",
    )


def frame(selected, remaining_mask, ordinary_credits):
    return FallBitsetFrame(
        selected_indices=selected,
        remaining_mask=remaining_mask,
        known_total_credits=ordinary_credits,
        known_ordinary_credits=ordinary_credits,
        known_chapel_credits=0.0,
        unknown_credit_section_ids=(),
        unresolved_schedule_section_ids=(),
    )


def zero_missing_shape_uppers(profile=None):
    profile = profile or fall2026_preference_profile()
    readiness = audit_fall_intrinsic_upper_bound_readiness(
        profile,
        global_course_utility_bounds=fall2026_course_utility_bounds(),
    )
    return {
        dimension: ProofUpperBound(
            dimension_id=dimension,
            upper=0.0,
            source_id="test:zero-shape-ceiling",
            justification="Test-only proof ceiling used to exercise bound arithmetic.",
        )
        for dimension in readiness.missing_timetable_dimensions
    }


def override_profile(dimension, estimate):
    base = fall2026_preference_profile()
    provenance = PreferenceProvenance(
        PreferenceSourceKind.USER_INPUT,
        "test:positive-geometry-upper",
    )
    replacement = PreferenceValue(
        dimension,
        estimate,
        provenance,
        "test override",
    )
    values = tuple(
        replacement if value.dimension_id == dimension else value
        for value in base.values
    )
    return PreferenceProfile("test-overridden-profile", values=values, relations=base.relations)


class FallIntrinsicBranchUpperBoundTests(unittest.TestCase):
    def test_current_profile_is_blocked_until_shape_ceilings_exist(self):
        a = section_from_raw(row("A-01-00", "화3"))
        result = derive_fall_intrinsic_branch_upper_bound(
            make_universe(a),
            frame((0,), 0, 3.0),
            policy(),
            fall2026_preference_profile(),
            global_course_utility_bounds=fall2026_course_utility_bounds(),
        )
        self.assertEqual(result.status, FallIntrinsicBranchBoundStatus.INPUT_BLOCKED)
        self.assertIsNone(result.total_upper_bound)
        self.assertIn("friday_event_window_free", result.missing_timetable_dimensions)
        self.assertTrue(result.registration_risk_layer_separate)

    def test_parsed_prefix_tightens_free_day_upper_and_relaxed_course_count(self):
        a = section_from_raw(row("A-01-00", "화3"))
        b = section_from_raw(row("B-01-00", "수3"))
        universe = make_universe(a, b)
        # A is selected, B is the only unvisited descendant option.
        result = derive_fall_intrinsic_branch_upper_bound(
            universe,
            frame((0,), 1 << 1, 3.0),
            policy(),
            fall2026_preference_profile(),
            global_course_utility_bounds=fall2026_course_utility_bounds(),
            explicit_timetable_upper_bounds=zero_missing_shape_uppers(),
        )
        self.assertEqual(result.status, FallIntrinsicBranchBoundStatus.AVAILABLE)
        # Course upper per selected section = +8 professor +3 interest +0 workload +0 difficulty.
        self.assertEqual(result.selected_course_upper_bound, 11.0)
        self.assertEqual(result.relaxed_additional_section_count, 1)
        self.assertEqual(result.relaxed_additional_course_upper_bound, 11.0)
        # With only Tuesday occupied, four fixed-free weekdays remain; current proof uppers:
        # 4*8 rest +14 first attached trip, while test-only unresolved shape ceilings are 0.
        self.assertEqual(result.timetable_upper_bound, 46.0)
        self.assertEqual(result.total_upper_bound, 68.0)
        self.assertFalse(result.used_global_timetable_relaxation)

    def test_credit_relaxation_ignores_remaining_conflicts_but_respects_known_cap(self):
        a = section_from_raw(row("A-01-00", "화3"))
        b = section_from_raw(row("B-01-00", "수3"))
        c = section_from_raw(row("C-01-00", "목3"))
        universe = make_universe(a, b, c)
        result = derive_fall_intrinsic_branch_upper_bound(
            universe,
            frame((0,), (1 << 1) | (1 << 2), 3.0),
            policy(cap=6.0),
            fall2026_preference_profile(),
            global_course_utility_bounds=fall2026_course_utility_bounds(),
            explicit_timetable_upper_bounds=zero_missing_shape_uppers(),
        )
        self.assertEqual(result.relaxed_additional_section_count, 1)
        self.assertEqual(result.relaxed_additional_course_upper_bound, 11.0)

    def test_unparsed_selected_schedule_falls_back_to_looser_global_weekly_maximum(self):
        unresolved = section_from_raw(row("A-01-00", ""))
        result = derive_fall_intrinsic_branch_upper_bound(
            make_universe(unresolved),
            frame((0,), 0, 3.0),
            policy(),
            fall2026_preference_profile(),
            global_course_utility_bounds=fall2026_course_utility_bounds(),
            explicit_timetable_upper_bounds=zero_missing_shape_uppers(),
        )
        self.assertTrue(result.available)
        # Global fallback: five rest weekdays at +8, plus first attached trip at +14.
        self.assertEqual(result.timetable_upper_bound, 54.0)
        self.assertTrue(result.used_global_timetable_relaxation)

    def test_positive_upper_on_normally_adverse_dimension_is_not_silently_ignored(self):
        a = section_from_raw(row("A-01-00", "화3"))
        profile = override_profile(
            "start_period_1_day",
            PreferenceEstimate.bounded(-1.0, 2.0),
        )
        result = derive_fall_intrinsic_branch_upper_bound(
            make_universe(a),
            frame((0,), 0, 3.0),
            policy(),
            profile,
            global_course_utility_bounds=fall2026_course_utility_bounds(),
            explicit_timetable_upper_bounds=zero_missing_shape_uppers(profile),
        )
        # Generic relaxation explicitly allows five positive start-period-1 activations:
        # previous 46 timetable upper + 5*2.
        self.assertEqual(result.timetable_upper_bound, 56.0)
        self.assertEqual(result.total_upper_bound, 67.0)


if __name__ == "__main__":
    unittest.main()
