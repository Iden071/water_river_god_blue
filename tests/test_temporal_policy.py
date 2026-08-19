import unittest

from timetable_optimizer.future_utility import FutureUtilityError
from timetable_optimizer.temporal_policy import (
    TIME_NEUTRAL_SOURCE_ID,
    time_neutral_temporal_aggregation,
)


class TimeNeutralTemporalPolicyTests(unittest.TestCase):
    def test_every_academic_term_gets_equal_unit_weight(self):
        policy = time_neutral_temporal_aggregation(
            ("2026F", "2027S", "2027F", "2028S")
        )
        self.assertEqual(policy.source_id, TIME_NEUTRAL_SOURCE_ID)
        self.assertEqual(
            tuple((item.term_id, item.weight) for item in policy.weights),
            (
                ("2026F", 1.0),
                ("2027S", 1.0),
                ("2027F", 1.0),
                ("2028S", 1.0),
            ),
        )

    def test_policy_is_explicit_not_a_hidden_default(self):
        policy = time_neutral_temporal_aggregation(("2026F",))
        self.assertIn("time-neutral", policy.note)
        self.assertEqual(policy.weight_for("2026F"), 1.0)

    def test_duplicate_term_ids_are_rejected_by_temporal_contract(self):
        with self.assertRaises(FutureUtilityError):
            time_neutral_temporal_aggregation(("2026F", "2026F"))


if __name__ == "__main__":
    unittest.main()
