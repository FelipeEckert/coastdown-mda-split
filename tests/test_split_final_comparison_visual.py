# coding: utf-8
"""Tests for pure visual-state helpers used by Split final comparison."""

import unittest

from core.split_state import ensure_split_comparison_pairs
from pages.page_split_final_comparison import get_pair_origin_visual_state


def _corrected_pair(**values):
    pair = {"F0_mean": 100.0, "F2_mean": 0.004}
    pair.update(values)
    return pair


class SplitFinalComparisonVisualTest(unittest.TestCase):
    def test_detects_algorithm_origins(self):
        self.assertEqual(
            get_pair_origin_visual_state(_corrected_pair(algorithm_source="energy")),
            "energy",
        )
        self.assertEqual(
            get_pair_origin_visual_state(_corrected_pair(algorithm_source="target")),
            "target",
        )
        self.assertEqual(
            get_pair_origin_visual_state(
                _corrected_pair(algorithm_sources=["energy", "target"])
            ),
            "energy_and_target",
        )

    def test_detects_manual_and_uncorrected(self):
        self.assertEqual(
            get_pair_origin_visual_state(_corrected_pair(selection_source="manual")),
            "manual",
        )
        self.assertEqual(
            get_pair_origin_visual_state({"selection_source": "manual"}),
            "uncorrected",
        )

    def test_ensure_comparison_pairs_preserves_existing_list(self):
        pairs = [{"id": "pair-1"}]
        state = {"split_comparison_pairs": pairs}

        result = ensure_split_comparison_pairs(state)

        self.assertIs(result, pairs)
        self.assertIs(state["split_comparison_pairs"], pairs)

    def test_ensure_comparison_pairs_initializes_only_missing_key(self):
        state = {}

        result = ensure_split_comparison_pairs(state)

        self.assertEqual(result, [])
        self.assertIs(result, state["split_comparison_pairs"])


if __name__ == "__main__":
    unittest.main()
