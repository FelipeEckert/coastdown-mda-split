"""Characterization coverage for active Split tab orchestration."""

from contextlib import ExitStack
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
    def test_each_main_tab_executes_only_its_renderer(self):
        pages = (
            ("2_dados_veiculo", page_2_dados_veiculo),
            ("split_workflow", page_split_workflow),
            ("split_coefficient_calculation", page_split_coefficient_calculation),
            ("split_final_comparison", page_split_final_comparison),
            ("split_results", page_split_results),
        )
        for selected, (page_id, _) in enumerate(pages):
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
                    patch.object(app.st, "tabs", return_value=_containers(5, selected))
                )
                renderers = []
                for renderer_page, module in pages:
                    renderers.append(
                        stack.enter_context(
                            patch.object(
                                module,
                                "render",
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

    def test_each_nested_pair_tab_executes_only_its_renderer(self):
        for selected in range(3):
            with self.subTest(selected=selected), ExitStack() as stack:
                state = _SessionState(active_test_id="active", language="pt")
                stack.enter_context(
                    patch.object(
                        page_split_coefficient_calculation.st,
                        "session_state",
                        state,
                    )
                )
                stack.enter_context(
                    patch.object(page_split_coefficient_calculation.st, "header")
                )
                stack.enter_context(
                    patch.object(
                        page_split_coefficient_calculation.st,
                        "tabs",
                        return_value=_containers(3, selected),
                    )
                )
                renderers = (
                    stack.enter_context(
                        patch.object(
                            page_split_coefficient_calculation,
                            "_render_coefficient_calculation",
                        )
                    ),
                    stack.enter_context(
                        patch.object(
                            page_split_coefficient_calculation,
                            "_render_graphical_analysis",
                        )
                    ),
                    stack.enter_context(
                        patch.object(page_split_auto_selection, "render")
                    ),
                )

                page_split_coefficient_calculation.render(_translate)

                self.assertEqual(
                    [renderer.call_count for renderer in renderers],
                    [int(index == selected) for index in range(3)],
                )

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
        pages = (
            page_2_dados_veiculo,
            page_split_workflow,
            page_split_coefficient_calculation,
            page_split_final_comparison,
            page_split_results,
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
            renderers = [
                stack.enter_context(patch.object(module, "render")) for module in pages
            ]

            app.render_test_analysis(_translate)
            state[tab_key] = "page_split_workflow"
            app.render_test_analysis(_translate)
            app.render_test_analysis(_translate)

        self.assertEqual([renderer.call_count for renderer in renderers], [1, 2, 0, 0, 0])
        self.assertEqual(state.current_page, "split_workflow")

    def test_nested_tab_selection_persists_and_switches_on_rerun(self):
        state = _SessionState(active_test_id="active", language="pt")
        tab_key = "split_pair_analysis_tabs_active_pt"

        def selected_containers(labels, **_kwargs):
            return _containers(len(labels), labels.index(state[tab_key]))

        with ExitStack() as stack:
            streamlit = page_split_coefficient_calculation.st
            stack.enter_context(patch.object(streamlit, "session_state", state))
            stack.enter_context(patch.object(streamlit, "header"))
            stack.enter_context(patch.object(streamlit, "tabs", side_effect=selected_containers))
            calculate = stack.enter_context(
                patch.object(
                    page_split_coefficient_calculation,
                    "_render_coefficient_calculation",
                )
            )
            graph = stack.enter_context(
                patch.object(
                    page_split_coefficient_calculation,
                    "_render_graphical_analysis",
                )
            )
            automatic = stack.enter_context(
                patch.object(page_split_auto_selection, "render")
            )

            state[tab_key] = "split_graphical_analysis"
            page_split_coefficient_calculation.render(_translate)
            page_split_coefficient_calculation.render(_translate)
            state[tab_key] = "split_auto_tab"
            page_split_coefficient_calculation.render(_translate)

        calculate.assert_not_called()
        self.assertEqual(graph.call_count, 2)
        automatic.assert_called_once_with(_translate)

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
                patch.object(app.st, "tabs", return_value=_containers(5, 0))
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
        state[tab_key] = "page_split_pair_analysis"
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
                    "render",
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
