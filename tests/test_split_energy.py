# coding: utf-8
"""Tests for the pure Split energy convention."""

import unittest
from unittest.mock import patch

from core.calculations import calcular_energia
from core.split_energy import (
    DEFAULT_SPLIT_ENERGY_PROFILE,
    ENERGY_UNIT,
    calculate_split_energy,
)
from translations import get_translator


class SplitEnergyTest(unittest.TestCase):
    def test_split_energy_matches_inherited_standard_arithmetic(self):
        result = calculate_split_energy(
            F0_mean=137.46875487093314,
            F2_mean=0.04963502126831579,
        )

        expected = calcular_energia(
            137.46875487093314,
            0.04963502126831579,
        )
        self.assertAlmostEqual(result["energy"], expected)
        self.assertEqual(result["energy_unit"], ENERGY_UNIT)
        self.assertEqual(result["energy_status"], "calculated")
        self.assertEqual(
            result["energy_profile"],
            DEFAULT_SPLIT_ENERGY_PROFILE,
        )
        self.assertEqual(
            result["energy_origin"],
            "core.calculations.calcular_energia",
        )

    def test_split_energy_requires_corrected_coefficients(self):
        with self.assertRaisesRegex(ValueError, "F0 and F2 must be numeric"):
            calculate_split_energy(None, None)

    def test_split_energy_delegates_corrected_means_to_standard_formula(self):
        with patch(
            "core.split_energy.calcular_energia",
            return_value=7.25,
        ) as inherited_energy:
            result = calculate_split_energy(140.0, 0.05)

        inherited_energy.assert_called_once_with(140.0, 0.05)
        self.assertEqual(result["energy"], 7.25)
        self.assertEqual(result["energy_unit"], "MJ/km")
        self.assertEqual(result["energy_status"], "calculated")

    def test_old_missing_neutral_function_message_is_removed(self):
        message = get_translator("pt")("split_energy_unavailable_contract")

        self.assertNotIn("falta uma função Split neutra", message)


if __name__ == "__main__":
    unittest.main()
