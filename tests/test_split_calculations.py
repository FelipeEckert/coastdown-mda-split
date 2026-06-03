# coding: utf-8
"""Tests for Split method coefficient calculations."""

import math
import unittest

from core.split_calculations import (
    calculate_split_coefficients,
    delta_v_kmh,
    kmh_to_ms,
)


class SplitCalculationsTest(unittest.TestCase):
    def test_delta_v_is_positive_amplitude(self):
        self.assertEqual(delta_v_kmh(90.0, 70.0), 20.0)
        self.assertEqual(delta_v_kmh(70.0, 90.0), 20.0)

    def test_rejects_non_positive_delta_t(self):
        with self.assertRaisesRegex(ValueError, "Delta t1"):
            calculate_split_coefficients(
                1500.0,
                0.0,
                8.0,
                45.0,
                35.0,
                40.0,
                90.0,
                70.0,
                80.0,
            )

    def test_rejects_invalid_effective_mass(self):
        with self.assertRaisesRegex(ValueError, "Me"):
            calculate_split_coefficients(
                0.0,
                5.0,
                8.0,
                45.0,
                35.0,
                40.0,
                90.0,
                70.0,
                80.0,
            )

    def test_rejects_v2_not_greater_than_v1(self):
        with self.assertRaisesRegex(ValueError, "V2"):
            calculate_split_coefficients(
                1500.0,
                5.0,
                8.0,
                45.0,
                35.0,
                80.0,
                90.0,
                70.0,
                40.0,
            )

    def test_calculates_with_configurable_intervals_without_sign_inversion(self):
        mass = 1600.0
        delta_t1 = 6.0
        delta_t2 = 9.0
        low_start, low_end, low_ref = 50.0, 30.0, 40.0
        high_start, high_end, high_ref = 100.0, 80.0, 90.0

        result = calculate_split_coefficients(
            mass,
            delta_t1,
            delta_t2,
            low_start,
            low_end,
            low_ref,
            high_start,
            high_end,
            high_ref,
        )

        v1 = kmh_to_ms(low_ref)
        v2 = kmh_to_ms(high_ref)
        delta_v1 = kmh_to_ms(abs(low_start - low_end))
        delta_v2 = kmh_to_ms(abs(high_start - high_end))
        denominator = v2**2 - v1**2
        a1 = delta_v1 / delta_t1
        a2 = delta_v2 / delta_t2
        expected_f0 = (mass / denominator) * (a1 * v2**2 - a2 * v1**2)
        expected_f2 = (mass / denominator) * (a2 - a1)

        self.assertTrue(math.isclose(result["f0_prime"], expected_f0, rel_tol=1e-12))
        self.assertTrue(math.isclose(result["f2_prime"], expected_f2, rel_tol=1e-12))

    def test_known_real_case_returns_positive_road_load_coefficients(self):
        result = calculate_split_coefficients(
            effective_mass=1545.0,
            delta_t1_s=19.58,
            delta_t2_s=18.72,
            low_start_kmh=45.0,
            low_end_kmh=35.0,
            low_reference_kmh=40.0,
            high_start_kmh=90.0,
            high_end_kmh=70.0,
            high_reference_kmh=80.0,
        )

        self.assertTrue(math.isclose(result["f0_prime"], 139.41119395239252, rel_tol=1e-12))
        self.assertTrue(math.isclose(result["f2_prime"], 0.6461779091694823, rel_tol=1e-12))


if __name__ == "__main__":
    unittest.main()
