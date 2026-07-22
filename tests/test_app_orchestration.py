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
        self.assertNotIn("using_split_method", created)
        self.assertNotIn("test_method", created)
        self.assertNotIn("using_split_method", self.state)
        self.assertNotIn("test_method", self.state)
        self.assertNotIn("mass_input_mode", created)
        self.assertNotIn("split_source_files", created)
        self.assertNotIn("data_info", created)
        self.assertIsNone(created["weather_data_split"])
        self.assertIsNone(created["excel_buffer"])
        self.assertEqual(created["split_ambient_version"], 0)
        self.assertIsNone(created["split_processed_at"])
        self.assertEqual(created["split_ambient_mode"], "fixed")
        self.assertEqual(created["split_fixed_temperature"], 25.0)
        self.assertEqual(created["split_fixed_pressure"], 101.3)
        self.assertEqual(self.state.split_fixed_temperature, 25.0)
        self.assertEqual(self.state.split_fixed_pressure, 101.3)
        error.assert_not_called()
        rerun.assert_called_once_with()

        app.save_active_test_state()
        self.assertNotIn("mass_input_mode", created)
        self.assertNotIn("split_source_files", created)
        self.assertNotIn("data_info", created)
        self.assertNotIn("using_split_method", created)
        self.assertNotIn("test_method", created)

    def test_legacy_method_flags_remain_stored_but_never_enter_active_state(self):
        snapshots = {
            "using-only": {"using_split_method": False},
            "method-only": {"test_method": "traditional"},
            "both": {
                "using_split_method": True,
                "test_method": "split",
            },
            "string": {
                "using_split_method": "false",
                "test_method": "unknown",
            },
            "number": {"using_split_method": 1, "test_method": 0},
            "list": {"using_split_method": [], "test_method": ["split"]},
            "none": {"using_split_method": None, "test_method": None},
        }

        for test_id, legacy_fields in snapshots.items():
            with self.subTest(snapshot=test_id):
                self.state.clear()
                app.init_session_state()
                self.state.tests = {
                    test_id: {
                        "name": test_id,
                        **copy.deepcopy(legacy_fields),
                    }
                }
                original = copy.deepcopy(self.state.tests[test_id])
                self.state.using_split_method = "leaked"
                self.state.test_method = ["leaked"]

                app.activate_test(test_id)
                after_first_load = copy.deepcopy(self.state.tests[test_id])
                app.load_test_state(test_id)
                self.assertEqual(self.state.tests[test_id], after_first_load)
                app.save_active_test_state()

                self.assertNotIn("using_split_method", self.state)
                self.assertNotIn("test_method", self.state)
                for key, value in original.items():
                    self.assertEqual(self.state.tests[test_id][key], value)

    def test_switching_isolates_legacy_method_page_state_without_persisting_it(self):
        from pages._legacy_method_state import (
            legacy_test_method,
            legacy_test_method_key,
        )

        self.state.tests = {
            "legacy": {
                "name": "Legacy Standard",
                "using_split_method": False,
                "test_method": "traditional",
            },
            "split": self._snapshot("Current Split"),
        }

        app.activate_test("legacy")
        self.state[legacy_test_method_key(self.state)] = "traditional"
        self.state.using_split_method = False
        self.state.test_method = "traditional"
        app.activate_test("split")
        app.save_active_test_state()

        self.assertEqual(legacy_test_method(self.state), "split")
        self.assertNotIn("using_split_method", self.state)
        self.assertNotIn("test_method", self.state)
        self.assertNotIn("using_split_method", self.state.tests["split"])
        self.assertNotIn("test_method", self.state.tests["split"])
        self.assertFalse(self.state.tests["legacy"]["using_split_method"])
        self.assertEqual(self.state.tests["legacy"]["test_method"], "traditional")

    def test_active_split_builders_do_not_write_stale_state(self):
        high_file = SimpleNamespace(name="high.csv")
        low_file = SimpleNamespace(name="low.csv")
        high_runs = {"high-run": {"direction": "+"}}
        low_runs = {"low-run": {"direction": "-"}}

        with (
            patch.object(
                app,
                "_load_uploaded_csv_file",
                side_effect=[
                    ([{"row": "high"}], high_runs, None),
                    ([{"row": "low"}], low_runs, None),
                ],
            ),
            patch.object(app, "_uploaded_file_sha256", side_effect=["high-hash", "low-hash"]),
        ):
            uploaded_state = app._build_split_coastdown_state(
                high_file,
                low_file,
                "separate",
                _translate,
            )

        loaded_state = app._build_split_state_from_loaded(
            "high.csv",
            "high-hash",
            [{"row": "high"}],
            high_runs,
            low_filename="low.csv",
            low_hash="low-hash",
            low_df=[{"row": "low"}],
            low_runs=low_runs,
        )

        for state in (uploaded_state, loaded_state):
            self.assertNotIn("split_source_files", state)
            self.assertEqual(
                [source["filename"] for source in state["split_input_sources"]],
                ["high.csv", "low.csv"],
            )
            self.assertNotIn("data_info", state)

        from pages import page_2_dados_veiculo as vehicle_page

        self.state.vehicle_info = {}
        vehicle_page._store_mass_data({
            "running_order_mass_kg": 1500.0,
            "rotational_equivalent_mass_kg": 45.0,
            "test_mass_kg": 1636.0,
            "effective_mass_kg": 1681.0,
        })

        self.assertNotIn("mass_input_mode", self.state)
        self.assertEqual(self.state.total_mass, 1636.0)
        self.assertEqual(self.state.vehicle_info["effective_mass"], 1681.0)

    def test_legacy_stale_keys_remain_stored_but_do_not_override_canonical_state(self):
        canonical_sources = [{"filename": "canonical.csv", "role": "high"}]
        self.state.tests = {
            "legacy": {
                "name": "Legacy",
                "mass_input_mode": "legacy-mode",
                "split_source_files": ["stale.csv"],
                "data_info": {"filename": "stale.csv"},
                "split_input_sources": canonical_sources,
                "split_processed_at": "2026-06-10T12:00:00+00:00",
            }
        }
        self.state.mass_input_mode = "leaked-mode"
        self.state.split_source_files = ["leaked.csv"]
        self.state.data_info = {"filename": "leaked.csv"}

        app.activate_test("legacy")

        self.assertNotIn("mass_input_mode", self.state)
        self.assertNotIn("split_source_files", self.state)
        self.assertNotIn("data_info", self.state)
        self.assertEqual(self.state.split_input_sources, canonical_sources)
        self.assertEqual(
            self.state.split_processed_at,
            "2026-06-10T12:00:00+00:00",
        )
        self.assertEqual(
            self.state.tests["legacy"]["mass_input_mode"],
            "legacy-mode",
        )
        self.assertEqual(
            self.state.tests["legacy"]["split_source_files"],
            ["stale.csv"],
        )
        self.assertEqual(
            self.state.tests["legacy"]["data_info"],
            {"filename": "stale.csv"},
        )

    def test_switching_and_round_trip_do_not_leak_or_reintroduce_stale_keys(self):
        self.state.tests = {
            "legacy": {
                "name": "Legacy",
                "mass_input_mode": "legacy-mode",
                "split_source_files": ["legacy.csv"],
                "data_info": {"filename": "legacy.csv"},
                "split_processed_at": "2026-06-10T12:00:00+00:00",
            },
            "canonical": self._snapshot(
                "Canonical",
                split_input_sources=[{"filename": "canonical.csv", "role": "high"}],
                split_processed_at="2026-06-10T13:00:00+00:00",
            ),
        }

        app.activate_test("legacy")
        app.activate_test("canonical")
        app.save_active_test_state()

        self.assertNotIn("mass_input_mode", self.state)
        self.assertNotIn("split_source_files", self.state)
        self.assertNotIn("data_info", self.state)
        self.assertNotIn("mass_input_mode", self.state.tests["canonical"])
        self.assertNotIn("split_source_files", self.state.tests["canonical"])
        self.assertNotIn("data_info", self.state.tests["canonical"])
        self.assertEqual(
            self.state.tests["canonical"]["split_input_sources"],
            [{"filename": "canonical.csv", "role": "high"}],
        )
        self.assertEqual(
            self.state.tests["legacy"]["split_source_files"],
            ["legacy.csv"],
        )
        self.assertEqual(
            self.state.tests["legacy"]["data_info"],
            {"filename": "legacy.csv"},
        )
        self.assertEqual(
            self.state.split_processed_at,
            "2026-06-10T13:00:00+00:00",
        )
        self.assertEqual(
            self.state.tests["canonical"]["split_processed_at"],
            "2026-06-10T13:00:00+00:00",
        )

    def test_retained_legacy_state_round_trips_without_switch_leakage(self):
        legacy_weather = [{"source": "canonical-legacy"}]
        canonical_weather = [{"source": "canonical-current"}]
        self.state.tests = {
            "legacy": self._snapshot(
                "Legacy",
                weather_data=legacy_weather,
                weather_data_split="malformed-weather",
                excel_buffer=["malformed-buffer"],
                split_ambient_version="malformed-version",
                split_processed_at={"malformed": True},
            ),
            "canonical": self._snapshot(
                "Canonical",
                weather_data=canonical_weather,
                weather_data_split=[{"source": "legacy-current"}],
                excel_buffer=b"legacy-export",
                split_ambient_version=7,
                split_processed_at="2026-06-10T14:00:00+00:00",
            ),
        }

        app.activate_test("legacy")
        self.assertEqual(self.state.weather_data, legacy_weather)
        self.assertEqual(self.state.weather_data_split, "malformed-weather")
        self.assertEqual(self.state.excel_buffer, ["malformed-buffer"])
        self.assertEqual(self.state.split_ambient_version, "malformed-version")
        self.assertEqual(self.state.split_processed_at, {"malformed": True})

        app.activate_test("canonical")
        app.save_active_test_state()

        self.assertEqual(self.state.weather_data, canonical_weather)
        self.assertEqual(
            self.state.weather_data_split,
            [{"source": "legacy-current"}],
        )
        self.assertEqual(self.state.excel_buffer, b"legacy-export")
        self.assertEqual(self.state.split_ambient_version, 7)
        self.assertEqual(
            self.state.split_processed_at,
            "2026-06-10T14:00:00+00:00",
        )
        self.assertEqual(
            self.state.tests["canonical"]["split_ambient_version"],
            7,
        )
        self.assertEqual(
            self.state.tests["legacy"]["split_processed_at"],
            {"malformed": True},
        )

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
    def test_legacy_flags_cannot_override_active_split_routing(self):
        app_test = AppTest.from_file(ROOT_DIR / "app.py", default_timeout=20)
        app_test.session_state["tests"] = {
            "legacy": {
                "name": "Legacy Standard",
                "using_split_method": False,
                "test_method": "traditional",
                "current_page": "1_abrir_teste",
            }
        }
        app_test.session_state["active_test_id"] = "legacy"

        app_test.run()

        self.assertEqual(len(app_test.exception), 0)
        self.assertEqual(app_test.session_state["current_page"], "2_dados_veiculo")
        self.assertNotIn("using_split_method", app_test.session_state)
        self.assertNotIn("test_method", app_test.session_state)

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


class LegacyPageMethodCompatibilityTests(unittest.TestCase):
    def test_legacy_method_resolution_accepts_only_historical_valid_values(self):
        from pages._legacy_method_state import legacy_test_method

        cases = (
            ({}, "split"),
            ({"using_split_method": False}, "traditional"),
            ({"test_method": "traditional"}, "traditional"),
            (
                {"using_split_method": True, "test_method": "split"},
                "split",
            ),
            (
                {"using_split_method": False, "test_method": "split"},
                "traditional",
            ),
            ({"using_split_method": "false", "test_method": "unknown"}, "split"),
            ({"using_split_method": 0, "test_method": 1}, "split"),
            ({"using_split_method": [], "test_method": ["traditional"]}, "split"),
            ({"using_split_method": None, "test_method": None}, "split"),
        )

        for snapshot, expected in cases:
            with self.subTest(snapshot=snapshot):
                state = _SessionState(
                    tests={"legacy": snapshot},
                    active_test_id="legacy",
                )
                self.assertEqual(legacy_test_method(state), expected)
                self.assertNotIn("using_split_method", state)
                self.assertNotIn("test_method", state)

    def test_direct_legacy_pages_resolve_method_without_active_flags(self):
        from pages import _page_1_obsoleto as open_page
        from pages import page_3_analise_pares as pair_page
        from pages import page_4_selecao_algoritmo as algorithm_page

        state = _SessionState(
            tests={
                "legacy": {
                    "using_split_method": [False],
                    "test_method": 1,
                }
            },
            active_test_id="legacy",
            data_loaded=False,
        )

        with (
            patch.object(open_page.st, "session_state", state),
            patch.object(open_page.st, "header"),
            patch.object(open_page.st, "subheader"),
            patch.object(
                open_page.st,
                "columns",
                return_value=(nullcontext(), nullcontext()),
            ),
            patch.object(open_page.st, "button", return_value=False),
            patch.object(open_page.st, "markdown"),
            patch.object(open_page, "render_split_upload") as render_split_upload,
        ):
            open_page.render(_translate)

        render_split_upload.assert_called_once_with(_translate)
        self.assertNotIn("using_split_method", state)
        self.assertNotIn("test_method", state)

        with (
            patch.object(pair_page.st, "session_state", state),
            patch.object(pair_page.st, "info") as info,
        ):
            pair_page.render_time_conformity_analysis(_translate)
        info.assert_called_once_with("time_conformity_split_not_supported")

        with patch.object(algorithm_page.st, "session_state", state):
            self.assertFalse(algorithm_page._has_algorithm_weather_sync_times(False))


if __name__ == "__main__":
    unittest.main()
