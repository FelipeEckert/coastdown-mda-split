# coding: utf-8
"""Tests for final Split result consolidation."""

import unittest

from core.split_results import consolidate_split_final_results


class SplitResultsTest(unittest.TestCase):
    def test_requires_explicit_selected_true(self):
        summary = consolidate_split_final_results(
            [{"id": "implicit", "F0_mean": 100.0, "F2_mean": 0.004}]
        )
        self.assertEqual(summary["num_pairs"], 0)

    def _pair(self, pair_id, f0, f2, energy=None, selected=True):
        return {
            "id": pair_id,
            "selected": selected,
            "F0_mean": f0,
            "F2_mean": f2,
            "energy": energy,
            "warnings": [],
        }

    def test_consolidates_selected_corrected_coefficients_and_energy(self):
        summary = consolidate_split_final_results(
            [
                self._pair("pair-1", 100.0, 0.004, 0.20),
                self._pair("pair-2", 110.0, 0.006, 0.30),
            ]
        )

        self.assertEqual(summary["num_pairs"], 2)
        self.assertAlmostEqual(summary["mean_f0"], 105.0)
        self.assertAlmostEqual(summary["mean_f2"], 0.005)
        self.assertAlmostEqual(summary["mean_energy"], 0.25)
        self.assertAlmostEqual(summary["cv_f0"], 6.734350297014738)
        self.assertAlmostEqual(summary["cv_f2"], 28.284271247461902)
        self.assertAlmostEqual(summary["cv_energy"], 28.284271247461895)

    def test_ignores_unselected_pairs(self):
        summary = consolidate_split_final_results(
            [
                self._pair("selected", 100.0, 0.004, selected=True),
                self._pair("ignored", 900.0, 9.0, selected=False),
            ]
        )

        self.assertEqual(summary["num_pairs"], 1)
        self.assertEqual(summary["selected_pairs"][0]["id"], "selected")
        self.assertEqual(summary["mean_f0"], 100.0)

    def test_missing_energy_does_not_block_other_metrics(self):
        summary = consolidate_split_final_results(
            [
                self._pair("pair-1", 100.0, 0.004),
                self._pair("pair-2", 110.0, 0.006, 0.30),
            ]
        )

        self.assertEqual(summary["mean_energy"], 0.30)
        self.assertEqual(summary["energy_value_count"], 1)
        self.assertEqual(summary["missing_energy_count"], 1)
        self.assertIsNone(summary["cv_energy"])

    def test_empty_list_is_safe(self):
        summary = consolidate_split_final_results([])

        self.assertEqual(summary["num_pairs"], 0)
        self.assertIsNone(summary["mean_f0"])
        self.assertIsNone(summary["cv_f0"])
        self.assertEqual(summary["selected_pairs"], [])

    def test_single_pair_has_no_misleading_cv(self):
        summary = consolidate_split_final_results(
            [self._pair("pair-1", 100.0, 0.004, 0.20)]
        )

        self.assertIsNone(summary["cv_f0"])
        self.assertIsNone(summary["cv_f2"])
        self.assertIsNone(summary["cv_energy"])
        self.assertEqual(summary["conformity_status"], "not_evaluable")

    def test_preserves_warnings_and_ambient_traceability(self):
        ambient = {
            "high_plus": {
                "matched": True,
                "temperature_c": 24.0,
                "warnings": ["ambient warning"],
            }
        }
        pair = self._pair("pair-1", 100.0, 0.004)
        pair["warnings"] = ["weather warning"]
        pair["ambient_by_component"] = ambient

        summary = consolidate_split_final_results([pair])

        self.assertEqual(
            summary["warnings"],
            ["weather warning", "ambient warning"],
        )
        selected = summary["selected_pairs"][0]
        self.assertEqual(
            selected["warnings"],
            ["weather warning", "ambient warning"],
        )
        self.assertEqual(selected["ambient_by_component"], ambient)

    def test_missing_corrected_coefficients_are_reported_without_error(self):
        summary = consolidate_split_final_results(
            [self._pair("pair-1", None, None, 0.20)]
        )

        self.assertIsNone(summary["mean_f0"])
        self.assertEqual(summary["missing_f0_count"], 1)
        self.assertEqual(summary["missing_f2_count"], 1)
        self.assertEqual(summary["conformity_status"], "incomplete")


if __name__ == "__main__":
    unittest.main()
