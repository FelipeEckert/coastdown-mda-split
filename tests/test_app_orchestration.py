# coding: utf-8
"""Behavioral coverage for the active multi-test Streamlit orchestration."""

import copy
from contextlib import nullcontext
import logging
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


_previous_logging_disable = logging.root.manager.disable
logging.disable(logging.CRITICAL)
try:
    import app
finally:
    logging.disable(_previous_logging_disable)


ROOT_DIR = Path(__file__).resolve().parents[1]


class _SessionState(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc

    __setattr__ = dict.__setitem__


def _translate(key, **_kwargs):
    return key


class AppStateOrchestrationTests(unittest.TestCase):
    def setUp(self):
        self.state = _SessionState()
        self.session_patch = patch.object(app.st, "session_state", self.state)
        self.session_patch.start()
        self.addCleanup(self.session_patch.stop)
        app.init_session_state()

    def _snapshot(self, name, **changes):
        snapshot = copy.deepcopy(app.TEST_DEFAULTS)
        snapshot.update({"name": name, **changes})
        return snapshot

    def test_new_split_test_uses_canonical_fixed_defaults_and_becomes_active(self):
        coastdown_state = {
            "coastdown_csv_path": "combined.csv",
            "split_input_mode": "combined",
            "split_input_layout": "single_combined",
            "data_loaded": True,
        }

        with (
            patch.object(app, "_build_split_coastdown_state", return_value=coastdown_state),
            patch.object(app.st, "spinner", return_value=nullcontext()),
            patch.object(app.st, "rerun") as rerun,
            patch.object(app.st, "error") as error,
            patch.object(
                app.uuid,
                "uuid4",
                return_value=SimpleNamespace(hex="12345678abcdef"),
            ),
        ):
            app._process_new_test(
                "New Split",
                object(),
                None,
                "combined",
                None,
                25.0,
                101.3,
                _translate,
            )

        created = self.state.tests["test_12345678"]
        self.assertEqual(self.state.active_test_id, "test_12345678")
        self.assertEqual(created["test_method"], "split")
        self.assertEqual(created["split_ambient_mode"], "fixed")
        self.assertEqual(created["split_fixed_temperature"], 25.0)
        self.assertEqual(created["split_fixed_pressure"], 101.3)
        self.assertEqual(self.state.split_fixed_temperature, 25.0)
        self.assertEqual(self.state.split_fixed_pressure, 101.3)
        error.assert_not_called()
        rerun.assert_called_once_with()

    def test_reopens_legacy_snapshot_and_populates_canonical_fixed_keys(self):
        self.state.tests = {
            "legacy": {
                "name": "Legacy Split",
                "fixed_temperature": 17.5,
                "fixed_pressure": 99.4,
                "vehicle_info": {"model": "Legacy Vehicle"},
            }
        }

        app.activate_test("legacy")

        saved = self.state.tests["legacy"]
        self.assertEqual(self.state.active_test_id, "legacy")
        self.assertEqual(saved["split_fixed_temperature"], 17.5)
        self.assertEqual(saved["split_fixed_pressure"], 99.4)
        self.assertEqual(self.state.split_fixed_temperature, 17.5)
        self.assertEqual(self.state.split_fixed_pressure, 99.4)
        self.assertEqual(self.state.vehicle_model_input, "Legacy Vehicle")
        self.assertEqual(self.state.current_page, "2_dados_veiculo")

    def test_reopen_keeps_canonical_fixed_keys_over_legacy_values(self):
        self.state.tests = {
            "canonical": {
                "name": "Canonical Split",
                "fixed_temperature": 15.0,
                "fixed_pressure": 95.0,
                "split_fixed_temperature": 22.5,
                "split_fixed_pressure": 102.2,
            }
        }

        app.activate_test("canonical")

        self.assertEqual(self.state.split_fixed_temperature, 22.5)
        self.assertEqual(self.state.split_fixed_pressure, 102.2)
        self.assertEqual(
            self.state.tests["canonical"]["split_fixed_temperature"],
            22.5,
        )

    def test_switching_tests_saves_and_restores_state_without_leakage(self):
        self.state.tests = {
            "first": self._snapshot(
                "First",
                split_results=[{"id": "first-original"}],
                split_fixed_temperature=18.0,
            ),
            "second": self._snapshot(
                "Second",
                split_results=[{"id": "second-original"}],
                split_fixed_temperature=28.0,
            ),
        }

        app.activate_test("first")
        self.state.split_results.append({"id": "first-edited"})
        self.state.current_page = "split_workflow"
        self.assertEqual(len(self.state.tests["first"]["split_results"]), 1)

        app.activate_test("second")
        self.assertEqual(self.state.active_test_id, "second")
        self.assertEqual(self.state.split_results, [{"id": "second-original"}])
        self.assertEqual(self.state.split_fixed_temperature, 28.0)
        self.assertEqual(len(self.state.tests["first"]["split_results"]), 2)
        self.state.split_results.append({"id": "second-edited"})

        app.activate_test("first")
        self.assertEqual(self.state.current_page, "split_workflow")
        self.assertEqual(
            self.state.split_results,
            [{"id": "first-original"}, {"id": "first-edited"}],
        )
        self.assertEqual(
            self.state.tests["second"]["split_results"],
            [{"id": "second-original"}, {"id": "second-edited"}],
        )

    def test_editing_active_test_preserves_state_and_updates_name(self):
        self.state.tests = {
            "active": self._snapshot(
                "Before",
                split_results=[{"id": "kept"}],
            )
        }
        app.activate_test("active")
        self.state.edit_test_id = "active"
        self.state.edit_test_dialog_context = "active"
        self.state.edit_test_dialog_token = "token"

        with (
            patch.object(app.st, "spinner", return_value=nullcontext()),
            patch.object(app.st, "rerun") as rerun,
            patch.object(app.st, "error") as error,
        ):
            app._apply_test_edits(
                "active",
                "After",
                "separate",
                None,
                None,
                False,
                None,
                False,
                _translate,
            )

        self.assertEqual(self.state.tests["active"]["name"], "After")
        self.assertEqual(self.state.split_results, [{"id": "kept"}])
        self.assertEqual(self.state.active_test_id, "active")
        self.assertIsNone(self.state.edit_test_id)
        error.assert_not_called()
        rerun.assert_called_once_with()


class AppWorkflowAppTestTests(unittest.TestCase):
    def test_incomplete_active_snapshot_renders_and_routes_to_results(self):
        app_test = AppTest.from_file(ROOT_DIR / "app.py", default_timeout=20)
        app_test.session_state["tests"] = {
            "incomplete": {
                "name": "Incomplete Split",
                "fixed_temperature": 19.0,
            }
        }
        app_test.session_state["active_test_id"] = "incomplete"
        app_test.session_state["navigate_to_results"] = True

        app_test.run()

        self.assertEqual(len(app_test.exception), 0)
        self.assertEqual(app_test.session_state["active_test_id"], "incomplete")
        self.assertEqual(app_test.session_state["current_page"], "split_results")

        tab_key = "main_analysis_tabs_incomplete_pt"
        self.assertEqual(
            app_test.session_state[tab_key],
            app.get_translator("pt")("page_split_results"),
        )

        app_test.run()
        self.assertEqual(len(app_test.exception), 0)
        self.assertEqual(app_test.session_state["current_page"], "split_results")

        app_test.session_state[tab_key] = app.get_translator("pt")(
            "page_split_workflow"
        )
        app_test.run()
        self.assertEqual(len(app_test.exception), 0)
        self.assertEqual(app_test.session_state["current_page"], "split_workflow")

        app_test.session_state[tab_key] = app.get_translator("pt")(
            "page_split_pair_analysis"
        )
        app_test.run()
        nested_key = "split_pair_analysis_tabs_incomplete_pt"
        self.assertEqual(len(app_test.exception), 0)
        self.assertEqual(
            app_test.session_state[nested_key],
            app.get_translator("pt")("page_split_coefficient_calculation"),
        )

        app_test.session_state[nested_key] = app.get_translator("pt")(
            "split_graphical_analysis"
        )
        app_test.run()
        self.assertEqual(len(app_test.exception), 0)
        self.assertEqual(
            app_test.session_state[nested_key],
            app.get_translator("pt")("split_graphical_analysis"),
        )


if __name__ == "__main__":
    unittest.main()
