import unittest

from timetable_optimizer.candidate_assessment import assess_candidate
from timetable_optimizer.course_preferences import ProfessorRatingBook
from timetable_optimizer.fall_local_hard_partition import (
    FallLocalHardIssueStatus,
    partition_fall_universe_by_local_hard_evidence,
)
from timetable_optimizer.fall_universe import FallSearchScope, FallSectionUniverse
from timetable_optimizer.preferences import PreferenceProfile
from timetable_optimizer.registration import assess_freshman_registration
from timetable_optimizer.sections import NoListedSchedule, ParsedSchedule, Section


def section(section_id, *, parsed=True, credits=3.0, cancelled=False):
    schedule = (
        ParsedSchedule(
            raw_time_text="fixture",
            raw_room_text="A",
            segments=(),
            conflict_mask=1 << (len(section_id) + 1),
            presence_mask=1 << (len(section_id) + 1),
            fixed_mask=1 << (len(section_id) + 1),
        )
        if parsed
        else NoListedSchedule(raw_time_text="", raw_room_text="")
    )
    return Section(
        section_id=section_id,
        course_code=f"C-{section_id}",
        name=section_id,
        korean_name=section_id,
        campus="국제",
        credits=credits,
        professor="Professor",
        language_code="",
        note="",
        grading="",
        cancelled=cancelled,
        mode_text="",
        schedule=schedule,
        language_name="영어",
    )


def universe(*sections):
    ids = frozenset(item.section_id for item in sections)
    return FallSectionUniverse(
        universe_id="partition-fixture",
        scope=FallSearchScope.full_catalog(),
        source_name="fixture",
        source_fingerprint="fixture-v1",
        included_sections=tuple(sections),
        hard_exclusions=(),
        scoped_out_section_ids=frozenset(),
        global_catalogue_unknowns=(),
        scope_unknowns=(),
        known_physical_section_ids=ids,
    )


def no_year_scheme(section_id):
    return assess_freshman_registration(
        section_id,
        {section_id: {f"sy{i}PercpCnt": 0 for i in range(1, 7)}},
        source_id="fixture-seats",
    )


def no_observation(section_id):
    return assess_freshman_registration(section_id, {}, source_id="fixture-seats")


def freshman_blocked(section_id):
    row = {f"sy{i}PercpCnt": 0 for i in range(1, 7)}
    row["sy2PercpCnt"] = 1
    return assess_freshman_registration(
        section_id,
        {section_id: row},
        source_id="fixture-seats",
    )


class FallLocalHardPartitionTests(unittest.TestCase):
    def test_every_searchable_section_is_accounted_for_exactly_once(self):
        resolved = section("R")
        gate_unknown = section("U")
        schedule_unknown = section("S", parsed=False)
        blocked = section("B")
        cancelled = section("C", cancelled=True)
        catalog = universe(resolved, gate_unknown, schedule_unknown, blocked, cancelled)
        registrations = {
            "R": no_year_scheme("R"),
            "U": no_observation("U"),
            "S": no_year_scheme("S"),
            "B": freshman_blocked("B"),
            "C": no_year_scheme("C"),
        }

        partition = partition_fall_universe_by_local_hard_evidence(
            catalog,
            registration_assessments=registrations,
        )

        self.assertEqual(partition.resolved_core_section_ids, {"R"})
        self.assertEqual(partition.unresolved_family_section_ids, {"U", "S"})
        self.assertEqual(partition.blocked_family_section_ids, {"B", "C"})
        self.assertTrue(partition.full_section_coverage)
        self.assertTrue(partition.global_optimum_blocked_by_local_unknowns)
        self.assertFalse(partition.resolved_core_universe.eligible_for_global_optimum_claim)

    def test_known_block_dominates_other_local_unknowns_for_family_class(self):
        item = section("X", parsed=False, cancelled=True)
        partition = partition_fall_universe_by_local_hard_evidence(
            universe(item),
            registration_assessments={"X": no_observation("X")},
        )
        self.assertEqual(partition.blocked_family_section_ids, {"X"})
        self.assertFalse(partition.unresolved_families)
        statuses = {issue.status for issue in partition.blocked_families[0].issues}
        self.assertIn(FallLocalHardIssueStatus.KNOWN_BLOCK, statuses)
        self.assertIn(FallLocalHardIssueStatus.UNRESOLVED, statuses)

    def test_registration_unknown_is_monotone_across_candidate_supersets(self):
        unknown = section("U")
        left = section("A")
        right = section("LONG")
        # Different fixture masks avoid accidental timetable conflict.
        catalog = universe(unknown, left, right)
        registrations = {
            "U": no_observation("U"),
            "A": no_year_scheme("A"),
            "LONG": no_year_scheme("LONG"),
        }
        partition = partition_fall_universe_by_local_hard_evidence(
            catalog,
            registration_assessments=registrations,
        )
        self.assertEqual(partition.unresolved_family_section_ids, {"U"})

        profile = PreferenceProfile("empty")
        ratings = ProfessorRatingBook(())
        for selected in ((unknown,), (unknown, left), (unknown, left, right)):
            assessed = assess_candidate(
                selected,
                profile,
                ratings,
                registration_assessments=registrations,
            )
            codes = {issue.code for issue in assessed.hard_constraint_unknowns}
            self.assertIn("registration_year_gate_unresolved", codes)

    def test_missing_registration_assessment_and_unknown_credit_are_local_unknowns(self):
        missing_gate = section("M")
        missing_credit = section("Q", credits=None)
        partition = partition_fall_universe_by_local_hard_evidence(
            universe(missing_gate, missing_credit),
            registration_assessments={"Q": no_year_scheme("Q")},
        )
        by_id = {
            family.section_id: {issue.code for issue in family.issues}
            for family in partition.unresolved_families
        }
        self.assertIn("registration_gate_unassessed", by_id["M"])
        self.assertIn("ordinary_credit_cap_unresolved", by_id["Q"])


if __name__ == "__main__":
    unittest.main()
