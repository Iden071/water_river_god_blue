import json
import unittest
from pathlib import Path

from timetable_optimizer.catalog import load_catalog_files
from timetable_optimizer.course_preferences import parse_professor_ratings_csv
from timetable_optimizer.fall2026_course_bounds import fall2026_course_utility_bounds
from timetable_optimizer.fall2026_preferences import fall2026_preference_profile
from timetable_optimizer.fall_local_hard_partition import (
    partition_fall_universe_by_local_hard_evidence,
)
from timetable_optimizer.fall_pruning_readiness import (
    FallPruningReadinessStatus,
    audit_fall_pruning_readiness,
)
from timetable_optimizer.fall_registration_screening import (
    screen_fall_universe_for_freshman_registration,
)
from timetable_optimizer.fall_universe import build_fall_section_universe


ROOT = Path(__file__).resolve().parents[1]


class RealFallPruningReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        snapshot = load_catalog_files(
            ROOT / "raw_2026F.json",
            program_listings_path=ROOT / "qrm_listings.json",
            listing_program="QRM",
            term="2026F",
        )
        universe = build_fall_section_universe(
            "real-2026F-full-catalog",
            snapshot,
        )
        with (ROOT / "fall2026_seats.json").open(encoding="utf-8") as handle:
            seat_rows = json.load(handle)
        screening = screen_fall_universe_for_freshman_registration(
            universe,
            snapshot,
            seat_rows,
            source_id="fall2026_seats.json",
        )
        cls.partition = partition_fall_universe_by_local_hard_evidence(
            screening.screened_universe,
            registration_assessments=screening.registration_assessment_map,
        )
        cls.registrations = screening.registration_assessment_map
        with (ROOT / "prof_ratings.csv").open(encoding="utf-8-sig") as handle:
            cls.professor_ratings = parse_professor_ratings_csv(
                handle.read(),
                source_id="prof_ratings.csv",
            )
        cls.readiness = audit_fall_pruning_readiness(
            cls.partition.resolved_core_universe,
            fall2026_preference_profile(),
            cls.professor_ratings,
            # User confirmed intrinsic semester utility is time-neutral on 2026-08-19.
            # Fall therefore has the same unit coefficient as any other academic term;
            # future uncertainty/recourse is modeled separately, not as temporal discount.
            fall_weight=1.0,
            registration_assessments=cls.registrations,
            global_course_utility_bounds=fall2026_course_utility_bounds(),
        )

    def test_real_temporal_objective_is_defined_but_present_bound_is_still_blocked(self):
        self.assertEqual(
            self.readiness.status,
            FallPruningReadinessStatus.PRESENT_BOUND_BLOCKED,
        )
        self.assertTrue(self.readiness.objective_defined)

    def test_user_course_envelopes_remove_intrinsic_course_blockers(self):
        by_dimension = {
            blocker.dimension: blocker
            for blocker in self.readiness.section_local_blockers
        }
        self.assertEqual(set(by_dimension), {"registration_obtainability"})
        self.assertEqual(
            by_dimension["registration_obtainability"].affected_section_count,
            len(self.partition.resolved_core_universe.included_sections),
        )

    def test_only_three_conceptual_timetable_shape_families_remain(self):
        dimensions = {
            item.dimension for item in self.readiness.timetable_profile_blockers
        }
        expected = {"friday_event_window_free", "three_fixed_period_run"}
        expected.update(f"long_fixed_run_delta_{length}" for length in range(5, 16))
        expected.update(
            f"weekend_attached_presence_free_extra_total_{count}"
            for count in range(2, 6)
        )
        self.assertEqual(dimensions, expected)
        # Raw state count is intentionally larger than conceptual blocker count: the model
        # preserves the three-period state plus nonlinear longer-run/weekend uncertainty
        # instead of pretending one scalar controls each family.
        self.assertEqual(len(dimensions), 17)

    def test_real_readiness_audit_counts_are_visible(self):
        section_counts = {
            blocker.dimension: blocker.affected_section_count
            for blocker in self.readiness.section_local_blockers
        }
        timetable = tuple(
            blocker.dimension for blocker in self.readiness.timetable_profile_blockers
        )
        conceptual = {
            "friday_event": [d for d in timetable if d == "friday_event_window_free"],
            "fixed_run_shape": [
                d
                for d in timetable
                if d == "three_fixed_period_run"
                or d.startswith("long_fixed_run_delta_")
            ],
            "weekend_attached_run_shape": [
                d
                for d in timetable
                if d.startswith("weekend_attached_presence_free_extra_total_")
            ],
        }
        print(
            "REAL_FALL_PRUNING_READINESS",
            {
                "status": self.readiness.status.value,
                "core_sections": self.readiness.core_section_count,
                "section_local_blocker_counts": section_counts,
                "timetable_profile_blocker_families": {
                    key: len(value) for key, value in conceptual.items()
                },
                "timetable_profile_blockers": timetable,
            },
        )


if __name__ == "__main__":
    unittest.main()
