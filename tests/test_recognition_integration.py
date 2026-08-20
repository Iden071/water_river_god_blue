import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.catalog import ListingStatus, load_catalog_files  # noqa: E402
from timetable_optimizer.degree import qrm_single_major_2026, spring_2026_initial_state  # noqa: E402
from timetable_optimizer.recognition import QualificationStatus, recognize_section  # noqa: E402


class RealFallRecognitionIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = load_catalog_files(
            ROOT / "raw_2026F.json",
            program_listings_path=ROOT / "qrm_listings.json",
            listing_program="QRM",
            term="2026-2",
        )
        cls.scenario = qrm_single_major_2026()
        cls.state = spring_2026_initial_state(cls.scenario)

    def test_real_qrm_me_overlay_flows_from_catalogue_into_recognition(self):
        tested = []
        for listing in self.snapshot.listings:
            if (
                listing.program == "QRM"
                and listing.status is ListingStatus.OK
                and listing.listed_category == "ME"
            ):
                record = self.snapshot.record_for(listing.section_id)
                if record is None or not record.usable or record.section is None:
                    continue
                assessment = recognize_section(
                    record.section,
                    self.scenario,
                    self.state,
                    source_views=self.snapshot.source_views_for(listing.section_id),
                    program_listings=self.snapshot.listings_for(listing.section_id, program="QRM"),
                )
                decision = next(
                    d for d in assessment.decisions if d.requirement_id == "qrm_me"
                )
                tested.append((listing.section_id, decision.status))
                if decision.status is QualificationStatus.QUALIFIED:
                    self.assertTrue(
                        any(
                            ("qrm_me", record.section.credits) in option.effect.bucket_credit_claims
                            for option in assessment.options
                        )
                    )
                    return

        self.fail(
            "No real Fall QRM ME listing produced a directly qualified recognition path; "
            f"sample statuses={tested[:10]!r}"
        )


if __name__ == "__main__":
    unittest.main()
