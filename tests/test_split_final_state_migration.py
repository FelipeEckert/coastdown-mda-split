"""Behavioral coverage for legacy Split final-result state migration."""

import copy
from contextlib import nullcontext
import unittest
from unittest.mock import Mock, patch

import app
from core.split_state import (
    LEGACY_SPLIT_FINAL_RESULTS_FLAG,
    migrate_legacy_split_final_results,
    split_final_results_status,
)
from pages import (
    page_split_coefficient_calculation,
    page_split_final_comparison,
    page_split_results,
)


class _State(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc

    __setattr__ = dict.__setitem__


def _pair(pair_id="pair-1"):
    return {
        "id": pair_id,
        "selected": True,
        "F0_mean": 100.0,
        "F2_mean": 0.004,
        "high_plus": {
            "subintervals": ["90-85"],
            "subinterval_times_s": [4.23],
        },
    }


def _render_fixed_ambient(state, temperature=20.0, pressure=101.325):
    streamlit = Mock(session_state=state)
    streamlit.radio.return_value = "split_ambient_mode_fixed"
    streamlit.columns.return_value = [nullcontext(), nullcontext()]
    streamlit.number_input.side_effect = [temperature, pressure]
    with patch.object(page_split_coefficient_calculation, "st", streamlit):
        page_split_coefficient_calculation._render_ambient_conditions(
            {}, lambda key: key
        )
    return streamlit


class SplitFinalStateMigrationTests(unittest.TestCase):
    def test_new_state_uses_only_canonical_pairs(self):
        state = {"split_comparison_pairs": [_pair()]}

        status = split_final_results_status(state)

        self.assertEqual(status["source"], "split_comparison_pairs")
        self.assertTrue(status["available"])
        self.assertEqual(status["selected_pair_count"], 1)
        self.assertNotIn("split_final_results", state)

    def test_canonical_pairs_take_precedence_when_both_keys_exist(self):
        state = {
            "split_comparison_pairs": [_pair()],
            "split_final_results": {"num_results": 9},
        }

        status = split_final_results_status(state)

        self.assertEqual(status["source"], "split_comparison_pairs")
        self.assertEqual(status["selected_pair_count"], 1)

    def test_legacy_selected_pairs_are_migrated_without_losing_summary(self):
        legacy = {
            "num_results": 1,
            "num_pairs": 1,
            "selected_pairs": [_pair()],
        }
        state = {"split_final_results": copy.deepcopy(legacy)}

        migrated = migrate_legacy_split_final_results(state)

        self.assertTrue(migrated)
        self.assertEqual(state["split_comparison_pairs"], legacy["selected_pairs"])
        self.assertEqual(
            state["split_comparison_pairs"][0]["high_plus"][
                "subinterval_times_s"
            ],
            [4.23],
        )
        self.assertEqual(state["split_final_results"], legacy)

    def test_active_test_round_trip_preserves_subinterval_times(self):
        state = _State()
        with patch.object(app.st, "session_state", state):
            app.init_session_state()
            state.tests = {"saved": {}}
            state.active_test_id = "saved"
            state.split_comparison_pairs = [_pair()]

            app.save_active_test_state()
            state.split_comparison_pairs = []
            app.load_test_state("saved")

        self.assertEqual(
            state.split_comparison_pairs[0]["high_plus"][
                "subinterval_times_s"
            ],
            [4.23],
        )

    def test_unsafe_legacy_pair_sets_are_not_migrated(self):
        duplicate = _pair("duplicate")
        cases = {
            "missing id": [{"selected": True, "F0_mean": 100.0, "F2_mean": 0.004}],
            "duplicate ids": [duplicate, copy.deepcopy(duplicate)],
            "malformed record": [_pair(), "not-a-pair"],
            "missing corrected fields": [{"id": "pair-1", "selected": True}],
            "invalid corrected fields": [
                {"id": "pair-1", "selected": True, "F0_mean": "bad", "F2_mean": 0.004}
            ],
            "partially selected": [_pair(), {**_pair("pair-2"), "selected": False}],
        }
        for label, pairs in cases.items():
            with self.subTest(label=label):
                state = {
                    "split_final_results": {
                        "num_results": len(pairs),
                        "num_pairs": len(pairs),
                        "selected_pairs": pairs,
                    }
                }

                self.assertFalse(migrate_legacy_split_final_results(state))
                self.assertNotIn("split_comparison_pairs", state)

    def test_conflicting_legacy_counts_reject_migration(self):
        state = {
            "split_final_results": {
                "num_results": 1,
                "num_pairs": 2,
                "selected_pairs": [_pair()],
            }
        }

        self.assertFalse(migrate_legacy_split_final_results(state))
        self.assertNotIn("split_comparison_pairs", state)

        missing_count = {
            "split_final_results": {"selected_pairs": [_pair()]}
        }
        self.assertFalse(migrate_legacy_split_final_results(missing_count))
        self.assertNotIn("split_comparison_pairs", missing_count)

    def test_migration_is_idempotent_and_never_replaces_canonical_pairs(self):
        state = {
            "split_final_results": {
                "num_results": 1,
                "num_pairs": 1,
                "selected_pairs": [_pair("legacy")],
            }
        }

        self.assertTrue(migrate_legacy_split_final_results(state))
        canonical_pairs = state["split_comparison_pairs"]
        canonical_snapshot = copy.deepcopy(canonical_pairs)
        self.assertFalse(migrate_legacy_split_final_results(state))
        self.assertIs(state["split_comparison_pairs"], canonical_pairs)
        self.assertEqual(state["split_comparison_pairs"], canonical_snapshot)

        existing = [_pair("canonical")]
        both = {
            "split_comparison_pairs": existing,
            "split_final_results": state["split_final_results"],
        }
        self.assertFalse(migrate_legacy_split_final_results(both))
        self.assertIs(both["split_comparison_pairs"], existing)

    def test_aggregate_only_legacy_state_is_preserved_and_explicit(self):
        legacy = {"num_results": 2, "mean_f0": 123.4}
        state = {
            "split_final_results": copy.deepcopy(legacy),
            LEGACY_SPLIT_FINAL_RESULTS_FLAG: True,
        }

        self.assertFalse(migrate_legacy_split_final_results(state))
        status = split_final_results_status(state)

        self.assertNotIn("split_comparison_pairs", state)
        self.assertEqual(state["split_final_results"], legacy)
        self.assertEqual(status["source"], "legacy")
        self.assertTrue(status["available"])
        self.assertEqual(status["selected_pair_count"], 2)

    def test_incomplete_legacy_state_is_safe(self):
        for legacy in (
            {"warnings": ["legacy"]},
            {"num_results": "2"},
            {"num_results": 1, "num_pairs": 2},
        ):
            with self.subTest(legacy=legacy):
                state = {
                    "split_final_results": legacy,
                    LEGACY_SPLIT_FINAL_RESULTS_FLAG: True,
                }

                self.assertFalse(migrate_legacy_split_final_results(state))
                status = split_final_results_status(state)

                self.assertEqual(status["source"], "legacy")
                self.assertFalse(status["available"])
                self.assertEqual(status["selected_pair_count"], 0)

    def test_non_dictionary_legacy_summaries_are_safe_and_not_migrated(self):
        for legacy in (None, "legacy", ["legacy"], 3):
            with self.subTest(legacy=legacy):
                test_data = {"split_final_results": legacy}
                self.assertFalse(migrate_legacy_split_final_results(test_data))
                self.assertNotIn("split_comparison_pairs", test_data)
                status = split_final_results_status(
                    {
                        "split_final_results": legacy,
                        LEGACY_SPLIT_FINAL_RESULTS_FLAG: True,
                    }
                )
                self.assertFalse(status["available"])
                self.assertEqual(status["selected_pair_count"], 0)

                state = _State(
                    tests={"legacy": {"split_final_results": legacy}}
                )
                with patch.object(app.st, "session_state", state):
                    app.init_session_state()
                    app.load_test_state("legacy")
                self.assertFalse(
                    state.get(LEGACY_SPLIT_FINAL_RESULTS_FLAG, False)
                )

    def test_passive_ambient_render_preserves_aggregate_only_legacy_state(self):
        legacy = {"num_results": 2, "mean_f0": 123.4}
        state = _State(
            tests={"legacy": {"split_final_results": copy.deepcopy(legacy)}},
            active_test_id="legacy",
            split_ambient_mode="fixed",
            split_fixed_temperature=20.0,
            split_fixed_pressure=101.325,
            split_ambient_signature=("fixed", 20.0, 101.325),
            split_ambient_version=0,
            split_results=[],
            split_comparison_pairs=[],
            split_last_calculated_result=None,
            excel_buffer=None,
            split_final_results=copy.deepcopy(legacy),
            **{LEGACY_SPLIT_FINAL_RESULTS_FLAG: True},
        )

        streamlit = _render_fixed_ambient(state)

        self.assertEqual(state.tests["legacy"]["split_final_results"], legacy)
        self.assertNotIn("split_comparison_pairs", state.tests["legacy"])
        streamlit.info.assert_not_called()

    def test_switching_and_round_trip_do_not_leak_or_add_redundant_state(self):
        state = _State()
        with patch.object(app.st, "session_state", state):
            app.init_session_state()
            state.tests = {
                "canonical": {
                    **copy.deepcopy(app.TEST_DEFAULTS),
                    "name": "Canonical",
                    "split_comparison_pairs": [_pair("canonical")],
                },
                "legacy": {
                    "name": "Legacy",
                    "split_final_results": {"num_results": 2, "mean_f0": 123.4},
                },
            }

            app.activate_test("legacy")
            self.assertTrue(state[LEGACY_SPLIT_FINAL_RESULTS_FLAG])
            self.assertNotIn("split_comparison_pairs", state.tests["legacy"])

            app.activate_test("canonical")
            self.assertFalse(state[LEGACY_SPLIT_FINAL_RESULTS_FLAG])
            self.assertNotIn("split_final_results", state)
            self.assertNotIn("split_comparison_pairs", state.tests["legacy"])

            app.activate_test("legacy")
            self.assertTrue(state[LEGACY_SPLIT_FINAL_RESULTS_FLAG])
            self.assertEqual(state.split_final_results["num_results"], 2)

            state.split_ambient_signature = ("fixed", 20.0, 101.325)
            streamlit = _render_fixed_ambient(state, temperature=21.0)
            streamlit.info.assert_called_once_with(
                "split_ambient_change_invalidated"
            )
            self.assertNotIn("split_final_results", state)
            self.assertNotIn("split_final_results", state.tests["legacy"])
            self.assertEqual(state.tests["legacy"]["split_comparison_pairs"], [])

            app.activate_test("canonical")
            self.assertEqual(
                state.split_comparison_pairs[0]["id"], "canonical"
            )
            self.assertNotIn("split_final_results", state)

        self.assertNotIn("split_final_results", state.tests["legacy"])
        self.assertEqual(state.tests["legacy"]["split_comparison_pairs"], [])

    def test_sidebar_count_is_derived_from_canonical_pairs(self):
        state = _State(
            data_loaded=False,
            vehicle_data_complete=False,
            split_results=[],
            split_comparison_pairs=[_pair()],
        )
        with patch.object(app.st, "session_state", state), patch.object(
            app.st, "markdown"
        ) as markdown:
            app.render_sidebar_status(lambda key: key)

        rendered = "\n".join(call.args[0] for call in markdown.call_args_list)
        self.assertIn("1 split_final_summary", rendered)

    def test_results_explains_aggregate_only_legacy_state(self):
        streamlit = Mock()
        streamlit.session_state = _State(
            split_comparison_pairs=[],
            split_final_results={"num_results": 2},
            **{LEGACY_SPLIT_FINAL_RESULTS_FLAG: True},
        )

        with patch.object(page_split_results, "st", streamlit):
            page_split_results.render(
                lambda key, **kwargs: f"{key}:{kwargs.get('count', '')}"
            )

        streamlit.warning.assert_called_once_with(
            "split_results_legacy_summary_only:2"
        )

    def test_final_action_navigates_without_writing_redundant_summary(self):
        streamlit = Mock()
        streamlit.session_state = _State(split_comparison_pairs=[_pair()])
        streamlit.button.return_value = True

        with patch.object(page_split_final_comparison, "st", streamlit):
            page_split_final_comparison._render_final_results_action(
                lambda key: key
            )

        self.assertTrue(streamlit.session_state.navigate_to_results)
        self.assertNotIn("split_final_results", streamlit.session_state)
        streamlit.rerun.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
