# coding: utf-8
"""Regression tests for fixed-condition state compatibility."""

import unittest

from core.split_state import (
    build_split_fixed_conditions,
    migrate_split_fixed_conditions,
)


class SplitFixedConditionsStateTests(unittest.TestCase):
    def test_new_test_uses_non_default_fixed_values_for_split_keys(self):
        state = build_split_fixed_conditions(18.7, 98.6)

        self.assertEqual(state["fixed_temperature"], 18.7)
        self.assertEqual(state["fixed_pressure"], 98.6)
        self.assertEqual(state["split_fixed_temperature"], 18.7)
        self.assertEqual(state["split_fixed_pressure"], 98.6)

    def test_load_migrates_fixed_conditions_with_canonical_precedence(self):
        cases = {
            "legacy only": (
                {"fixed_temperature": 17.5, "fixed_pressure": 99.4},
                (17.5, 99.4),
            ),
            "canonical only": (
                {"split_fixed_temperature": 21.2, "split_fixed_pressure": 100.8},
                (21.2, 100.8),
            ),
            "canonical takes precedence": (
                {
                    "fixed_temperature": 15.0,
                    "fixed_pressure": 95.0,
                    "split_fixed_temperature": 22.5,
                    "split_fixed_pressure": 102.2,
                },
                (22.5, 102.2),
            ),
        }

        for name, (state, expected) in cases.items():
            with self.subTest(name=name):
                migrate_split_fixed_conditions(state)
                self.assertEqual(
                    (state["split_fixed_temperature"], state["split_fixed_pressure"]),
                    expected,
                )


if __name__ == "__main__":
    unittest.main()
