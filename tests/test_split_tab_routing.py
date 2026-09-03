"""Characterization coverage for active Split tab orchestration."""

from contextlib import ExitStack
from copy import deepcopy
import unittest
from unittest.mock import patch

import app
from pages import (
    page_2_dados_veiculo,
    page_split_auto_selection,
    page_split_coefficient_calculation,
    page_split_final_comparison,
    page_split_results,
    page_split_workflow,
)


class _SessionState(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc

    __setattr__ = dict.__setitem__


class _Container:
    def __init__(self, *, open=False):
        self.open = open

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def _containers(count, selected):
    return tuple(_Container(open=index == selected) for index in range(count))


def _translate(key, **_kwargs):
    return key


class SplitTabRoutingTests(unittest.TestCase):
    def test_combined_input_source_summary_uses_canonical_files(self):
        state = _SessionState(
            split_input_mode="combined",
            split_input_sources=[
                {"role": "full_or_combined", "filename": "combined.csv"},
            ],
        )
        streamlit = page_split_workflow.st

        with ExitStack() as stack:
            stack.enter_context(patch.object(streamlit, "session_state", state))
            stack.enter_context(
                patch.object(streamlit, "container", return_value=_Container())
            )
            stack.enter_context(patch.object(streamlit, "subheader"))
            stack.enter_context(patch.object(streamlit, "markdown"))
            badge = stack.enter_context(patch.object(streamlit, "badge"))

            page_split_workflow._render_input_sources(_translate)

        self.assertEqual(
            [call.args[0] for call in badge.call_args_list],
            ["split_input_mode_combined", "combined.csv", "no_meteo_file"],
        )

    def test_workflow_blocks_parsing_when_loaded_intervals_do_not_match(self):
        config = {
            "step_kmh": 10.0,
            "high": {"start": 100.0, "reference": 90.0, "end": 80.0},
            "low": {"start": 60.0, "reference": 50.0, "end": 40.0},
        }
        sources = [{"filename": "combined.csv", "role": "full_or_combined"}]
        issue = {
            "code": "source_interval_mismatch",
            "message": "Split intervals differ from the loaded file. High: 2 expected, 4 found.",
        }
        state = _SessionState(
            active_test_id="active",
            language="en",
            data_loaded=True,
            vehicle_data_complete=True,
            split_input_sources=sources,
            split_interval_config=config,
            split_parsed_runs={},
            split_parse_dirty=True,
            split_parse_feedback_current=False,
            split_parse_validation_issues=[],
        )
        streamlit = page_split_workflow.st

        with ExitStack() as stack:
            stack.enter_context(patch.object(streamlit, "session_state", state))
            stack.enter_context(
                patch.object(streamlit, "container", return_value=_Container())
            )
            stack.enter_context(
                patch.object(streamlit, "spinner", return_value=_Container())
            )
            for method in ("header", "info", "space"):
                stack.enter_context(patch.object(streamlit, method))
            warning = stack.enter_context(patch.object(streamlit, "warning"))
            stack.enter_context(
                patch.object(page_split_workflow, "_render_input_sources")
            )
            stack.enter_context(
                patch.object(streamlit, "button", side_effect=(True, False))
            )
            stack.enter_context(
                patch.object(
                    page_split_workflow,
                    "_render_interval_config",
                    return_value=config,
                )
            )
            validator = stack.enter_context(
                patch.object(
                    page_split_workflow,
                    "validate_split_source_consistency",
                    return_value=[issue],
                )
            )
            parser = stack.enter_context(
                patch.object(page_split_workflow, "parse_split_sources")
            )

            page_split_workflow.render(_translate)

        validator.assert_called_once_with(sources, config)
        parser.assert_not_called()
        self.assertEqual(state["split_parse_validation_issues"], [issue])
        warning.assert_any_call(issue["message"], icon=":material/warning:")

    def test_each_main_tab_executes_only_its_renderer(self):
        pages = (
            ("2_dados_veiculo", page_2_dados_veiculo, "render"),
            ("split_workflow", page_split_workflow, "render"),
            (
                "split_coefficient_calculation",
                page_split_coefficient_calculation,
                "render_manual",
            ),
            ("split_auto_selection", page_split_auto_selection, "render"),
            ("split_pair_analysis", page_split_coefficient_calculation, "render"),
            ("split_final_comparison", page_split_final_comparison, "render"),
            ("split_results", page_split_results, "render"),
        )
        for selected, (page_id, _, _) in enumerate(pages):
            with self.subTest(page=page_id), ExitStack() as stack:
                state = _SessionState(
                    tests={"active": {"name": "Active"}},
                    active_test_id="active",
                    language="pt",
                    current_page=page_id,
                    split_comparison_pairs=[],
                )
                stack.enter_context(patch.object(app.st, "session_state", state))
                stack.enter_context(patch.object(app.st, "title"))
                stack.enter_context(
                    patch.object(app.st, "tabs", return_value=_containers(7, selected))
                )
                renderers = []
                for renderer_page, module, renderer_name in pages:
                    renderers.append(
                        stack.enter_context(
                            patch.object(
                                module,
                                renderer_name,
                                side_effect=lambda _t, name=renderer_page: state.__setitem__(
                                    f"rendered_{name}", True
                                ),
                            )
                        )
                    )

                app.render_test_analysis(_translate)

                self.assertEqual(
                    [renderer.call_count for renderer in renderers],
                    [int(index == selected) for index in range(len(pages))],
                )
                self.assertEqual(
                    {key for key in state if key.startswith("rendered_")},
                    {f"rendered_{page_id}"},
                )

    def test_main_navigation_uses_the_requested_portuguese_order(self):
        state = _SessionState(
            tests={"active": {"name": "Active"}},
            active_test_id="active",
            language="pt",
            current_page="2_dados_veiculo",
            split_comparison_pairs=[],
        )
        translator = app.get_translator("pt")

        with ExitStack() as stack:
            stack.enter_context(patch.object(app.st, "session_state", state))
            stack.enter_context(patch.object(app.st, "title"))
            tabs = stack.enter_context(
                patch.object(app.st, "tabs", return_value=_containers(7, 0))
            )
            stack.enter_context(patch.object(page_2_dados_veiculo, "render"))

            app.render_test_analysis(translator)

        self.assertEqual(
            tabs.call_args.args[0],
            [
                "Dados do Veículo",
                "Setup Intervalos",
                "Seleção Manual",
                "Seleção Automática",
                "Análise de Pares",
                "Comparativo Final",
                "Resultados",
            ],
        )

    def test_manual_main_route_reuses_the_existing_calculation_renderer(self):
        with patch.object(
            page_split_coefficient_calculation.st, "header"
        ), patch.object(
            page_split_coefficient_calculation,
            "_render_coefficient_calculation",
        ) as calculation:
            page_split_coefficient_calculation.render_manual(_translate)

        calculation.assert_called_once_with(_translate)

    def test_pair_analysis_subtabs_render_only_the_open_surface(self):
        tab_key = "split_pair_analysis_tabs_active_pt"
        streamlit = page_split_coefficient_calculation.st
        labels = ["split_graphical_analysis", "split_statistical_analysis"]

        for selected in range(2):
            with self.subTest(selected=selected), ExitStack() as stack:
                state = _SessionState(
                    active_test_id="active",
                    language="pt",
                    **{tab_key: labels[selected]},
                )
                stack.enter_context(patch.object(streamlit, "session_state", state))
                stack.enter_context(patch.object(streamlit, "header"))
                tabs = stack.enter_context(
                    patch.object(
                        streamlit,
                        "tabs",
                        return_value=_containers(2, selected),
                    )
                )
                graph = stack.enter_context(
                    patch.object(
                        page_split_coefficient_calculation,
                        "_render_graphical_analysis",
                    )
                )
                statistics = stack.enter_context(
                    patch.object(
                        page_split_coefficient_calculation,
                        "_render_statistical_analysis",
                    )
                )

                page_split_coefficient_calculation.render(_translate)

                tabs.assert_called_once_with(
                    labels,
                    default=labels[selected],
                    key=tab_key,
                    on_change="rerun",
                )
                renderers = (graph, statistics)
                renderers[selected].assert_called_once_with(_translate)
                renderers[1 - selected].assert_not_called()

    def test_statistical_run_overview_reuses_normative_logic_without_mutation(self):
        def run(run_id, direction, delta_t, interval):
            return {
                "run_id": run_id,
                "heading": direction,
                "filename": f"{interval}.csv",
                "start_kmh": 90.0 if interval == "high" else 45.0,
                "end_kmh": 70.0 if interval == "high" else 35.0,
                "reference_kmh": 80.0 if interval == "high" else 40.0,
                "delta_v_kmh": 20.0 if interval == "high" else 10.0,
                "delta_t_s": delta_t,
                "subintervals": ["90-85", "85-80"],
                "subinterval_times_s": [4.9, 5.1],
            }

        parsed = {
            "high": [
                run(1, "+", 20.0, "high"),
                run(2, "+", 20.2, "high"),
                run(3, "-", 21.0, "high"),
                run(4, "-", 21.2, "high"),
            ],
            "low": [
                run(5, "+", 10.0, "low"),
                run(6, "+", 10.1, "low"),
                run(7, "-", 12.0, "low"),
                run(8, "-", 12.2, "low"),
            ],
        }
        state = _SessionState(
            data_loaded=True,
            split_parse_dirty=False,
            split_parsed_runs=parsed,
        )
        original = deepcopy(state)
        streamlit = page_split_coefficient_calculation.st

        with ExitStack() as stack:
            stack.enter_context(patch.object(streamlit, "session_state", state))
            stack.enter_context(
                patch.object(streamlit, "container", return_value=_Container())
            )
            for method in ("subheader", "caption", "markdown", "space"):
                stack.enter_context(patch.object(streamlit, method))
            dataframe = stack.enter_context(patch.object(streamlit, "dataframe"))
            validator = stack.enter_context(
                patch.object(
                    page_split_coefficient_calculation,
                    "validate_split_selected_times",
                    wraps=page_split_coefficient_calculation.validate_split_selected_times,
                )
            )

            page_split_coefficient_calculation._render_statistical_analysis(
                _translate
            )

        validator.assert_called_once()
        self.assertEqual(dataframe.call_count, 3)
        group_rows = dataframe.call_args_list[0].args[0].to_dict("records")
        self.assertEqual(
            [row["group"] for row in group_rows],
            ["High+", "High-", "Low+", "Low-"],
        )
        self.assertEqual([row["count"] for row in group_rows], [2, 2, 2, 2])
        self.assertAlmostEqual(group_rows[0]["mean_s"], 20.1)
        self.assertAlmostEqual(group_rows[0]["stdev_s"], 0.141421356237309)
        self.assertTrue(group_rows[0]["status"].startswith("✓ "))

        opposite_rows = dataframe.call_args_list[1].args[0].to_dict("records")
        self.assertEqual(
            [row["comparison"] for row in opposite_rows],
            ["High+ × High-", "Low+ × Low-"],
        )
        self.assertTrue(opposite_rows[0]["status"].startswith("✓ "))
        self.assertTrue(opposite_rows[1]["status"].startswith("✕ "))
        self.assertEqual(opposite_rows[1]["limit_pct"], 10.0)

        run_rows = dataframe.call_args_list[2].args[0].to_dict("records")
        self.assertEqual(len(run_rows), 8)
        self.assertEqual(run_rows[0]["group"], "High+")
        self.assertEqual(run_rows[0]["delta_t_s"], 20.0)
        self.assertEqual(run_rows[-1]["group"], "Low-")
        self.assertEqual(state, original)

    def test_each_parser_review_tab_renders_only_its_table(self):
        config = {
            "step_kmh": 5.0,
            "high": {"start": 90.0, "reference": 80.0, "end": 70.0},
            "low": {"start": 45.0, "reference": 40.0, "end": 35.0},
        }
        parsed = {
            "high": [{"start_kmh": 90.0, "end_kmh": 70.0}],
            "low": [{"start_kmh": 45.0, "end_kmh": 35.0}],
            "warnings": [],
        }
        for selected in range(2):
            with self.subTest(selected=selected), ExitStack() as stack:
                state = _SessionState(
                    active_test_id="active",
                    language="pt",
                    data_loaded=True,
                    vehicle_data_complete=True,
                    split_parse_dirty=False,
                    split_parse_validation_issues=[],
                )
                streamlit = page_split_workflow.st
                stack.enter_context(patch.object(streamlit, "session_state", state))
                for method in ("header", "info", "warning", "markdown", "subheader", "caption"):
                    stack.enter_context(patch.object(streamlit, method))
                dataframe = stack.enter_context(patch.object(streamlit, "dataframe"))
                stack.enter_context(
                    patch.object(streamlit, "columns", return_value=(_Container(), _Container()))
                )
                stack.enter_context(patch.object(streamlit, "button", return_value=False))
                stack.enter_context(
                    patch.object(streamlit, "tabs", return_value=_containers(2, selected))
                )
                stack.enter_context(
                    patch.object(
                        page_split_workflow,
                        "_render_interval_config",
                        return_value=config,
                    )
                )
                stack.enter_context(
                    patch.object(
                        page_split_workflow,
                        "get_processed_split_review_state",
                        return_value={"config": config, "parsed_runs": parsed},
                    )
                )
                stack.enter_context(
                    patch.object(
                        page_split_workflow,
                        "should_show_split_parse_details",
                        return_value=True,
                    )
                )

                page_split_workflow.render(_translate)

                self.assertEqual(dataframe.call_count, 1)
                rendered_records = dataframe.call_args.args[0].to_dict("records")
                expected_interval = "90-70" if selected == 0 else "45-35"
                self.assertEqual(rendered_records[0]["Interval"], expected_interval)

    def test_main_tab_selection_persists_and_switches_on_rerun(self):
        renderers = (
            (page_2_dados_veiculo, "render"),
            (page_split_workflow, "render"),
            (page_split_coefficient_calculation, "render_manual"),
            (page_split_auto_selection, "render"),
            (page_split_coefficient_calculation, "render"),
            (page_split_final_comparison, "render"),
            (page_split_results, "render"),
        )
        state = _SessionState(
            tests={"active": {"name": "Active"}},
            active_test_id="active",
            language="pt",
            current_page="2_dados_veiculo",
            split_comparison_pairs=[],
        )
        tab_key = "main_analysis_tabs_active_pt"

        def selected_containers(labels, **_kwargs):
            return _containers(len(labels), labels.index(state[tab_key]))

        with ExitStack() as stack:
            stack.enter_context(patch.object(app.st, "session_state", state))
            stack.enter_context(patch.object(app.st, "title"))
            stack.enter_context(patch.object(app.st, "tabs", side_effect=selected_containers))
            renderer_mocks = [
                stack.enter_context(patch.object(module, name))
                for module, name in renderers
            ]

            app.render_test_analysis(_translate)
            state[tab_key] = "page_split_workflow"
            app.render_test_analysis(_translate)
            app.render_test_analysis(_translate)

        self.assertEqual(
            [renderer.call_count for renderer in renderer_mocks],
            [1, 2, 0, 0, 0, 0, 0],
        )
        self.assertEqual(state.current_page, "split_workflow")

    def test_shared_comparison_repair_runs_without_rendering_final_tab(self):
        state = _SessionState(
            tests={"active": {"name": "Active"}},
            active_test_id="active",
            language="pt",
            current_page="2_dados_veiculo",
            split_comparison_pairs=[{"id": "legacy", "selected": True}],
            split_final_results={"stale": True},
            excel_buffer=b"stale",
            split_deviation_analysis_cache={"stale": True},
            split_results_excel_cache={"stale": True},
        )
        with ExitStack() as stack:
            stack.enter_context(patch.object(app.st, "session_state", state))
            stack.enter_context(patch.object(app.st, "title"))
            stack.enter_context(
                patch.object(app.st, "tabs", return_value=_containers(7, 0))
            )
            vehicle_render = stack.enter_context(
                patch.object(page_2_dados_veiculo, "render")
            )
            final_render = stack.enter_context(
                patch.object(page_split_final_comparison, "render")
            )

            app.render_test_analysis(_translate)

        vehicle_render.assert_called_once_with(_translate)
        final_render.assert_not_called()
        self.assertFalse(state.split_comparison_pairs[0]["selected"])
        self.assertNotIn("split_final_results", state)
        self.assertIsNone(state.excel_buffer)
        self.assertNotIn("split_deviation_analysis_cache", state)
        self.assertNotIn("split_results_excel_cache", state)

    def test_new_uncorrected_pair_is_repaired_before_results_can_observe_it(self):
        state = _SessionState(
            tests={"active": {"name": "Active"}},
            active_test_id="active",
            language="pt",
            current_page="split_coefficient_calculation",
            split_comparison_pairs=[],
        )
        tab_key = "main_analysis_tabs_active_pt"
        state[tab_key] = "page_split_coefficient_calculation"
        results_observations = []

        def selected_containers(labels, **_kwargs):
            return _containers(len(labels), labels.index(state[tab_key]))

        def insert_uncorrected_pair(_t):
            state.split_comparison_pairs.append(
                {"id": "new-uncorrected", "selected": True}
            )

        def observe_results(_t):
            results_observations.extend(
                pair["selected"] for pair in state.split_comparison_pairs
            )

        with ExitStack() as stack:
            stack.enter_context(patch.object(app.st, "session_state", state))
            stack.enter_context(patch.object(app.st, "title"))
            stack.enter_context(
                patch.object(app.st, "tabs", side_effect=selected_containers)
            )
            coefficient_render = stack.enter_context(
                patch.object(
                    page_split_coefficient_calculation,
                    "render_manual",
                    side_effect=insert_uncorrected_pair,
                )
            )
            final_render = stack.enter_context(
                patch.object(page_split_final_comparison, "render")
            )
            results_render = stack.enter_context(
                patch.object(
                    page_split_results,
                    "render",
                    side_effect=observe_results,
                )
            )

            app.render_test_analysis(_translate)

            coefficient_render.assert_called_once_with(_translate)
            final_render.assert_not_called()
            results_render.assert_not_called()
            self.assertFalse(state.split_comparison_pairs[0]["selected"])

            state[tab_key] = "page_split_results"
            app.render_test_analysis(_translate)

        self.assertEqual(results_observations, [False])
        final_render.assert_not_called()


if __name__ == "__main__":
    unittest.main()
