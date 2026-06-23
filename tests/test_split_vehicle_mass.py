# coding: utf-8
"""Protection tests for the normative Split effective-mass chain."""

import inspect
import unittest

from core.split_vehicle_mass import (
    compute_split_effective_mass,
    normalize_split_vehicle_mass_data,
)


class SplitVehicleMassTests(unittest.TestCase):
    def test_running_order_mass_builds_m_me_and_effective_mass(self):
        result = compute_split_effective_mass(running_order_mass_kg=1500.0)

        self.assertEqual(result["test_mass_kg"], 1636.0)
        self.assertAlmostEqual(result["rotational_equivalent_mass_kg"], 49.08)
        self.assertAlmostEqual(result["effective_mass_kg"], 1685.08)
        self.assertTrue(result["rotational_mass_estimated"])

    def test_informed_rotational_mass_is_used_without_estimation(self):
        result = compute_split_effective_mass(
            running_order_mass_kg=1500.0,
            rotational_equivalent_mass_kg=55.0,
        )

        self.assertEqual(result["test_mass_kg"], 1636.0)
        self.assertEqual(result["rotational_equivalent_mass_kg"], 55.0)
        self.assertEqual(result["effective_mass_kg"], 1691.0)
        self.assertFalse(result["rotational_mass_estimated"])

    def test_direct_test_mass_does_not_add_136_twice(self):
        result = compute_split_effective_mass(test_mass_kg=1636.0)

        self.assertEqual(result["test_mass_kg"], 1636.0)
        self.assertAlmostEqual(result["effective_mass_kg"], 1685.08)

    def test_running_order_mass_takes_precedence_over_inconsistent_test_mass(self):
        result = compute_split_effective_mass(
            running_order_mass_kg=1500.0,
            test_mass_kg=1700.0,
        )

        self.assertEqual(result["test_mass_kg"], 1636.0)
        self.assertTrue(result["warnings"])

    def test_legacy_total_plus_effective_mass_is_normalized_as_m_plus_me(self):
        result = normalize_split_vehicle_mass_data({
            "total_mass": 1500.0,
            "vehicle_info": {"effective_mass": 1545.0, "inertia_mass": 45.0},
        })

        self.assertEqual(result["test_mass_kg"], 1500.0)
        self.assertEqual(result["rotational_equivalent_mass_kg"], 45.0)
        self.assertEqual(result["effective_mass_kg"], 1545.0)

    def test_legacy_effective_mass_direct_is_preserved(self):
        result = normalize_split_vehicle_mass_data({"effective_mass": 1545.0})

        self.assertEqual(result["effective_mass_kg"], 1545.0)
        self.assertIsNone(result["test_mass_kg"])
        self.assertTrue(result["warnings"])

    def test_module_does_not_import_streamlit(self):
        import core.split_vehicle_mass as module

        self.assertNotIn("streamlit", inspect.getsource(module).lower())


if __name__ == "__main__":
    unittest.main()
