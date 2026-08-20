import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.catalog import ingest_catalog  # noqa: E402
from timetable_optimizer.degree import (  # noqa: E402
    qrm_double_major_shell_2026,
    qrm_single_major_2026,
)
from timetable_optimizer.fall_candidate_sets import (  # noqa: E402
    enumerate_fall_candidate_sets,
    fall2026_load_policy,
)
from timetable_optimizer.fall_universe import (  # noqa: E402
    FallSearchScope,
    build_fall_section_universe,
)
from timetable_optimizer.registration import assess_freshman_registration  # noqa: E402
from timetable_optimizer.verification import (  # noqa: E402
    EvidenceAuthority,
    EvidenceDependency,
    VerificationStatus,
    VerificationSummary,
    audit_degree_scenario_verification,
    audit_fall_input_verification,
    authority_from_source_id,
    can_claim_user_verified_optimum,
    compact_manual_verification_queue,
)


def row(section_id="UIC1000-01-00", *, cancelled=False):
    return {
        "subjtnbCorsePrcts": section_id,
        "subjtnb": "UIC1000",
        "subjtEngNm": "Example",
        "subjtNm": "Example",
        "campsDivNm": "국제",
        "cdt": 3,
        "cgprfNm": "Professor",
        "srclnLctreLangDivNm": "영어",
        "atntnMattrDesc": "",
        "gradeEvlMthdDivNm": "절대평가",
        "rmvlcYn": "1" if cancelled else "0",
        "rmvlcYnNm": "폐강" if cancelled else "",
        "lctreTimeNm": "화3",
        "lecrmNm": "A",
        "subjtClNm": "",
        "estblDeprtNm": "UIC",
        "hy": "1",
        "subsrtDivNm": "",
    }


class VerificationPrimitiveTests(unittest.TestCase):
    def test_only_explicit_spec_or_user_sources_are_confirmed(self):
        self.assertIs(
            authority_from_source_id("SPEC.md §7.1"),
            EvidenceAuthority.SPEC_CONFIRMED,
        )
        self.assertIs(
            authority_from_source_id("user:2026-08-19 chapel clarification"),
            EvidenceAuthority.USER_CONFIRMED,
        )
        self.assertIs(
            authority_from_source_id("2026 curriculum, verified 2026-08-18"),
            EvidenceAuthority.PROVISIONAL,
        )
        self.assertIs(
            authority_from_source_id("RULES.md R134"),
            EvidenceAuthority.PROVISIONAL,
        )

    def test_unresolved_outranks_provisional_in_summary_status(self):
        summary = VerificationSummary(
            (
                EvidenceDependency("a", EvidenceAuthority.SPEC_CONFIRMED, "SPEC.md §1"),
                EvidenceDependency("b", EvidenceAuthority.PROVISIONAL, "research note"),
                EvidenceDependency("c", EvidenceAuthority.UNRESOLVED, "missing evidence"),
            )
        )
        self.assertIs(summary.status, VerificationStatus.UNRESOLVED)
        self.assertFalse(summary.manually_verified)
        self.assertEqual(
            [item.dependency_id for item in summary.manual_verification_queue],
            ["c", "b"],
        )

    def test_model_optimum_and_user_verified_optimum_are_distinct_claims(self):
        provisional = VerificationSummary(
            (EvidenceDependency("x", EvidenceAuthority.PROVISIONAL, "old research"),)
        )
        verified = VerificationSummary(
            (EvidenceDependency("x", EvidenceAuthority.SPEC_CONFIRMED, "SPEC.md §3"),)
        )
        self.assertFalse(
            can_claim_user_verified_optimum(
                model_optimum_proven=True,
                verification=provisional,
            )
        )
        self.assertTrue(
            can_claim_user_verified_optimum(
                model_optimum_proven=True,
                verification=verified,
            )
        )
        self.assertFalse(
            can_claim_user_verified_optimum(
                model_optimum_proven=False,
                verification=verified,
            )
        )

    def test_compact_queue_orders_unresolved_before_provisional(self):
        dependencies = (
            EvidenceDependency("p2", EvidenceAuthority.PROVISIONAL, "p2"),
            EvidenceDependency("u1", EvidenceAuthority.UNRESOLVED, "u1"),
            EvidenceDependency("s", EvidenceAuthority.SPEC_CONFIRMED, "SPEC.md"),
            EvidenceDependency("p1", EvidenceAuthority.PROVISIONAL, "p1"),
        )
        self.assertEqual(
            [item.dependency_id for item in compact_manual_verification_queue(dependencies)],
            ["u1", "p1", "p2"],
        )


class Stage4VerificationAuditTests(unittest.TestCase):
    def test_degree_audit_does_not_upgrade_old_verified_wording(self):
        summary = audit_degree_scenario_verification(qrm_single_major_2026())
        self.assertIs(summary.status, VerificationStatus.PROVISIONAL)
        by_id = {item.dependency_id: item for item in summary.dependencies}

        chapel = by_id["degree::qrm-single-2026::requirement::cc_chapel"]
        self.assertIs(chapel.authority, EvidenceAuthority.SPEC_CONFIRMED)

        qrm_intro = by_id["degree::qrm-single-2026::requirement::qrm_mr_intro"]
        self.assertIs(qrm_intro.authority, EvidenceAuthority.PROVISIONAL)

    def test_unresolved_second_major_is_separate_from_provisional_sources(self):
        summary = audit_degree_scenario_verification(qrm_double_major_shell_2026())
        self.assertIs(summary.status, VerificationStatus.UNRESOLVED)
        self.assertIn(
            "degree::qrm-double-shell-2026::second_major_structure",
            {item.dependency_id for item in summary.unresolved_dependencies},
        )

    def test_fall_load_policy_is_spec_confirmed_but_catalogue_is_provisional(self):
        snapshot = ingest_catalog((row(),), source_name="fall-test", term="2026F")
        universe = build_fall_section_universe(
            "fall-test",
            snapshot,
            scope=FallSearchScope.full_catalog(),
        )
        enumeration = enumerate_fall_candidate_sets(
            universe,
            fall2026_load_policy(),
            max_subset_evaluations=10,
        )
        summary = audit_fall_input_verification(enumeration)
        by_id = {item.dependency_id: item for item in summary.dependencies}
        self.assertIs(
            by_id["fall::ordinary_credit_cap"].authority,
            EvidenceAuthority.SPEC_CONFIRMED,
        )
        self.assertIs(
            by_id["fall::catalogue_snapshot"].authority,
            EvidenceAuthority.PROVISIONAL,
        )
        self.assertIs(summary.status, VerificationStatus.PROVISIONAL)

    def test_missing_registration_observation_is_verification_unresolved(self):
        snapshot = ingest_catalog((row(),), source_name="fall-test", term="2026F")
        universe = build_fall_section_universe("fall-test", snapshot)
        enumeration = enumerate_fall_candidate_sets(
            universe,
            fall2026_load_policy(),
            max_subset_evaluations=10,
        )
        assessment = assess_freshman_registration("UIC1000-01-00", {})
        summary = audit_fall_input_verification(
            enumeration,
            registration_assessments={"UIC1000-01-00": assessment},
        )
        self.assertIs(summary.status, VerificationStatus.UNRESOLVED)
        self.assertIn(
            "fall::registration_gate::UIC1000-01-00",
            {item.dependency_id for item in summary.unresolved_dependencies},
        )

    def test_canonical_cancellation_is_not_silently_user_verified(self):
        snapshot = ingest_catalog((row(cancelled=True),), source_name="fall-test", term="2026F")
        universe = build_fall_section_universe("fall-test", snapshot)
        enumeration = enumerate_fall_candidate_sets(
            universe,
            fall2026_load_policy(),
            max_subset_evaluations=10,
        )
        summary = audit_fall_input_verification(enumeration)
        exclusions = [
            item
            for item in summary.dependencies
            if item.dependency_id.startswith("fall::hard_exclusion::")
        ]
        self.assertEqual(len(exclusions), 1)
        self.assertIs(exclusions[0].authority, EvidenceAuthority.PROVISIONAL)


if __name__ == "__main__":
    unittest.main()
