import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.degree import (  # noqa: E402
    RecognitionEffect,
    apply_recognition,
    qrm_single_major_2026,
    spring_2026_initial_state,
)
from timetable_optimizer.future_actions import FutureRecognitionEvidence  # noqa: E402
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
from timetable_optimizer.future_term_bundles import (  # noqa: E402
    FutureTermIssueStatus,
    generate_future_term_bundles,
)
from timetable_optimizer.sections import (  # noqa: E402
    DeliveryKind,
    NoListedSchedule,
    ParsedSchedule,
    ScheduleSegment,
    mask_from_blocks,
)


def term(*, cap=18.0, campus=CampusAccessKind.ANY, campuses=frozenset()):
    return FutureTermScenario(
        term_id="2027S",
        activity=TermActivity.ACTIVE,
        ordinary_credit_cap=cap,
        residence=ResidenceState.HOME,
        campus_access=CampusAccessScenario(campus, campuses),
        catalogue_basis=FutureCatalogueBasis(
            FutureCatalogueBasisKind.EXPLICIT_SCENARIO
        ),
    )


def parsed(day, periods):
    blocks = frozenset((day, period) for period in periods)
    mask = mask_from_blocks(blocks)
    return ParsedSchedule(
        raw_time_text="scenario",
        raw_room_text="scenario-room",
        segments=(
            ScheduleSegment(
                raw_time_text="scenario",
                raw_room_text="scenario-room",
                blocks=blocks,
                delivery_kind=DeliveryKind.IN_PERSON,
            ),
        ),
        conflict_mask=mask,
        presence_mask=mask,
        fixed_mask=mask,
    )


def offering(
    offering_id,
    course_code,
    *,
    credits=3.0,
    campus="국제",
    schedule=None,
):
    return FutureOffering(
        offering_id=offering_id,
        term_id="2027S",
        course_code=course_code,
        credits=credits,
        campus=campus,
        schedule=schedule if schedule is not None else parsed(0, (1,)),
        evidence=FutureOfferingEvidence(
            kind=FutureOfferingEvidenceKind.EXPLICIT_ASSUMPTION,
            source_id=f"scenario:{offering_id}",
        ),
    )


class FutureTermBundleTests(unittest.TestCase):
    def setUp(self):
        self.scenario = qrm_single_major_2026()
        self.state = spring_2026_initial_state(self.scenario)

    def test_explicit_parsed_single_course_can_form_exact_transition_bundle(self):
        generated = generate_future_term_bundles(
            term(),
            (
                offering(
                    "2027S:mat1001",
                    "MAT1001",
                    schedule=parsed(0, (3, 4, 5)),
                ),
            ),
            self.scenario,
            self.state,
        )

        self.assertEqual(len(generated.bundles), 1)
        bundle = generated.bundles[0]
        self.assertTrue(bundle.exact_transition_ready)
        self.assertEqual(bundle.load.known_ordinary_credits, 3.0)
        self.assertTrue(
            bundle.resulting_state.is_requirement_satisfied(
                self.scenario, "cc_scird"
            )
        )

    def test_credit_cap_violation_blocks_bundle_generation(self):
        generated = generate_future_term_bundles(
            term(cap=3.0),
            (
                offering("2027S:a", "MAT1001", schedule=parsed(0, (1,))),
                offering("2027S:b", "PHY1001", schedule=parsed(1, (1,))),
            ),
            self.scenario,
            self.state,
        )

        self.assertTrue(generated.known_infeasible)
        self.assertFalse(generated.bundles)
        self.assertTrue(
            any(
                issue.code == "ordinary_credit_cap_exceeded"
                and issue.status is FutureTermIssueStatus.VIOLATED
                for issue in generated.static_issues
            )
        )

    def test_chapel_credit_can_be_exempt_from_ordinary_capacity(self):
        generated = generate_future_term_bundles(
            term(cap=3.0),
            (
                offering("2027S:science", "MAT1001", schedule=parsed(0, (1,))),
                offering(
                    "2027S:chapel",
                    "YCA1005",
                    credits=0.5,
                    schedule=parsed(1, (1,)),
                ),
            ),
            self.scenario,
            self.state,
        )

        self.assertFalse(generated.known_infeasible)
        self.assertEqual(generated.load.known_total_credits, 3.5)
        self.assertEqual(generated.load.known_ordinary_credits, 3.0)
        self.assertEqual(generated.load.known_chapel_credits, 0.5)
        self.assertTrue(generated.bundles)

    def test_restricted_campus_violation_is_hard_failure(self):
        generated = generate_future_term_bundles(
            term(
                campus=CampusAccessKind.RESTRICTED,
                campuses=frozenset({"국제"}),
            ),
            (
                offering(
                    "2027S:sinchon",
                    "MAT1001",
                    campus="신촌",
                    schedule=parsed(0, (1,)),
                ),
            ),
            self.scenario,
            self.state,
        )

        self.assertFalse(generated.bundles)
        self.assertTrue(
            any(issue.code == "campus_access_violated" for issue in generated.static_issues)
        )

    def test_nonparsed_schedule_is_unknown_not_free(self):
        generated = generate_future_term_bundles(
            term(),
            (
                offering(
                    "2027S:unknown-time",
                    "MAT1001",
                    schedule=NoListedSchedule("", ""),
                ),
            ),
            self.scenario,
            self.state,
        )

        self.assertTrue(generated.bundles)
        self.assertTrue(
            any(issue.code == "offering_schedule_unresolved" for issue in generated.static_issues)
        )
        self.assertFalse(generated.bundles[0].exact_transition_ready)

    def test_known_timetable_conflict_blocks_selected_set(self):
        generated = generate_future_term_bundles(
            term(),
            (
                offering("2027S:a", "MAT1001", schedule=parsed(0, (2,))),
                offering("2027S:b", "PHY1001", schedule=parsed(0, (2,))),
            ),
            self.scenario,
            self.state,
        )

        self.assertFalse(generated.bundles)
        self.assertTrue(
            any(issue.code == "future_timetable_conflict" for issue in generated.static_issues)
        )

    def test_same_day_mixed_campus_is_possible_but_travel_feasibility_unresolved(self):
        generated = generate_future_term_bundles(
            term(),
            (
                offering(
                    "2027S:intl",
                    "MAT1001",
                    campus="국제",
                    schedule=parsed(0, (1,)),
                ),
                offering(
                    "2027S:sinchon",
                    "PHY1001",
                    campus="신촌",
                    schedule=parsed(0, (5,)),
                ),
            ),
            self.scenario,
            self.state,
        )

        self.assertTrue(generated.bundles)
        self.assertFalse(generated.known_infeasible)
        self.assertTrue(
            any(
                issue.code == "future_cross_campus_travel_unresolved"
                and issue.status is FutureTermIssueStatus.UNRESOLVED
                for issue in generated.static_issues
            )
        )
        self.assertTrue(all(not bundle.exact_transition_ready for bundle in generated.bundles))

    def test_korean_cap_allocation_is_not_decided_by_sorted_course_order(self):
        state = self.state
        for index in range(3):
            state = apply_recognition(
                state,
                self.scenario,
                RecognitionEffect.course(
                    completion_id=f"prior-korean-{index}",
                    course_code=f"TEST{index}",
                    credits=3.0,
                    bucket_credit_claims=(("qrm_me", 3.0),),
                    qrm_korean_major_credits=3.0,
                ),
            )
        self.assertEqual(state.qrm_korean_major_credits, 9.0)

        macro = offering(
            "2027S:a-macro",
            "ECO2101",
            campus="국제",
            schedule=parsed(0, (1,)),
        )
        micro = offering(
            "2027S:b-micro",
            "ECO2102",
            campus="국제",
            schedule=parsed(1, (1,)),
        )
        evidence = {
            macro.offering_id: FutureRecognitionEvidence(
                source_id="scenario:macro-korean",
                departments=("School of Economics",),
                korean_taught=True,
            ),
            micro.offering_id: FutureRecognitionEvidence(
                source_id="scenario:micro-korean",
                departments=("School of Economics",),
                korean_taught=True,
            ),
        }

        generated = generate_future_term_bundles(
            term(cap=6.0),
            (macro, micro),
            self.scenario,
            state,
            recognition_evidence=evidence,
        )

        self.assertTrue(generated.bundles)
        satisfaction_pairs = {
            (
                bundle.resulting_state.is_requirement_satisfied(
                    self.scenario, "qrm_mr_macro"
                ),
                bundle.resulting_state.is_requirement_satisfied(
                    self.scenario, "qrm_mr_micro"
                ),
            )
            for bundle in generated.bundles
        }
        self.assertIn((True, False), satisfaction_pairs)
        self.assertIn((False, True), satisfaction_pairs)
        self.assertNotIn((True, True), satisfaction_pairs)
        self.assertTrue(
            all(bundle.resulting_state.qrm_korean_major_credits <= 12.0 for bundle in generated.bundles)
        )

    def test_empty_selection_is_a_valid_identity_transition(self):
        generated = generate_future_term_bundles(
            term(), (), self.scenario, self.state
        )
        self.assertEqual(len(generated.bundles), 1)
        self.assertEqual(generated.bundles[0].resulting_state, self.state)
        self.assertTrue(generated.bundles[0].exact_transition_ready)


if __name__ == "__main__":
    unittest.main()
