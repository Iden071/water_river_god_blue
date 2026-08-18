import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.degree import (  # noqa: E402
    DegreeState,
    RecognitionEffect,
    apply_recognition,
    qrm_single_major_2026,
)


class CurrentChapelRuleTests(unittest.TestCase):
    def setUp(self):
        self.scenario = qrm_single_major_2026()

    def test_current_hard_rule_is_four_passes_with_no_offline_minimum(self):
        chapel = self.scenario.requirement("cc_chapel")
        self.assertEqual(chapel.passes_required, 4)
        self.assertEqual(chapel.credits_per_pass, 0.5)
        self.assertEqual(chapel.offline_passes_required, 0)

    def test_four_passes_satisfy_hard_rule_even_when_modality_is_unknown(self):
        state = DegreeState()
        for index in range(4):
            state = apply_recognition(
                state,
                self.scenario,
                RecognitionEffect.chapel(
                    completion_id=f"chapel-{index}",
                    offline=None,
                ),
            )

        # Modality uncertainty is still retained as provenance/utility information.
        self.assertEqual(state.chapel.passes_completed, 4)
        self.assertEqual(state.chapel.offline_passes_min, 0)
        self.assertEqual(state.chapel.offline_passes_max, 4)
        self.assertTrue(state.is_requirement_satisfied(self.scenario, "cc_chapel"))

    def test_face_to_face_pass_still_updates_modality_bounds(self):
        state = apply_recognition(
            DegreeState(),
            self.scenario,
            RecognitionEffect.chapel(
                completion_id="chapel-face-to-face",
                offline=True,
            ),
        )
        self.assertEqual(state.chapel.offline_passes_min, 1)
        self.assertEqual(state.chapel.offline_passes_max, 1)
        self.assertFalse(state.is_requirement_satisfied(self.scenario, "cc_chapel"))


if __name__ == "__main__":
    unittest.main()
