# coding: utf-8
"""Focused regression tests for the Split workbook cache signature."""

from copy import deepcopy
from datetime import datetime, timezone
import unittest

import numpy as np

from data.split_exporters import build_split_export_signature


COMPONENTS = ("high_plus", "low_plus", "high_minus", "low_minus")


def _pair():
    pair = {
        "id": "pair-one",
        "selected": True,
        "selection_source": "manual",
        "F0_mean": 100.0,
        "F2_mean": 0.004,
        "cv_F0_percent": 1.2,
        "cv_F2_percent": 1.4,
        "energy": 0.5,
        "corrected_result_plus": {"F0": 99.0, "F2": 0.0039},
        "ambient_by_component": {},
    }
    for index, component in enumerate(COMPONENTS, start=1):
        pair[component] = {
            "filename": f"{component}.csv",
            "run_id": f"run-{index}",
            "delta_t_s": 10.0 + index,
            "subintervals": ["90-85", "85-80"],
            "source_columns": ["t_90_85", "t_85_80"],
        }
        pair[f"{component}_run"] = f"run-{index}"
        pair[f"{component}_delta_t_s"] = 10.0 + index
        pair["ambient_by_component"][component] = {
            "temperature_c": 25.0,
            "pressure_kpa": 101.3,
            "wind_speed_mps": 1.0,
            "sync_method": "nearest",
        }
    return pair


def _signature(pairs):
    return build_split_export_signature(
        final_results={
            "mean_f0": np.float64(100.0),
            "missing": np.float64("nan"),
        },
        selected_pairs=pairs,
        vehicle_data={
            "model": "Car",
            "generated": datetime(2026, 7, 20, tzinfo=timezone.utc),
        },
        deviation_analysis={"time_summary": {"groups": ("high", "low")}},
    )


class SplitExportCacheSignatureTests(unittest.TestCase):
    def test_identical_inputs_and_dictionary_key_order_reuse_signature(self):
        original = _pair()
        reordered = {
            key: deepcopy(value)
            for key, value in reversed(list(original.items()))
        }
        reordered["ambient_by_component"] = {
            key: dict(reversed(list(value.items())))
            for key, value in reversed(
                list(reordered["ambient_by_component"].items())
            )
        }

        self.assertEqual(_signature([original]), _signature([reordered]))

    def test_workbook_traceability_changes_invalidate_signature(self):
        cases = {
            "filename": lambda pair: pair["high_plus"].__setitem__(
                "filename", "replacement.csv"
            ),
            "run label": lambda pair: pair["high_plus"].__setitem__(
                "run_id", "replacement-run"
            ),
            "subinterval": lambda pair: pair["high_plus"][
                "subintervals"
            ].append("80-75"),
            "selection origin": lambda pair: pair.__setitem__(
                "selection_source", "algorithm"
            ),
            "corrected traceability": lambda pair: pair[
                "corrected_result_plus"
            ].__setitem__("F0", 101.0),
            "weather traceability": lambda pair: pair[
                "ambient_by_component"
            ]["high_plus"].__setitem__("sync_method", "interpolated"),
        }
        baseline = _signature([_pair()])

        for name, mutate in cases.items():
            with self.subTest(name=name):
                changed = _pair()
                mutate(changed)
                self.assertNotEqual(baseline, _signature([changed]))

    def test_unselected_internal_metadata_does_not_invalidate_signature(self):
        selected = _pair()
        unselected = _pair()
        unselected["id"] = "not-exported"
        unselected["selected"] = False
        baseline = _signature([selected, unselected])

        unselected["internal_ui_state"] = {"expanded": True}

        self.assertEqual(baseline, _signature([selected, unselected]))


if __name__ == "__main__":
    unittest.main()
