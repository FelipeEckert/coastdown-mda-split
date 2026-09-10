"""Characterization coverage for active Split tab orchestration."""

from contextlib import ExitStack
from copy import deepcopy
import unittest
from unittest.mock import patch

import pandas as pd

import app
from pages import (
    page_2_dados_veiculo,
    page_split_auto_selection,
    page_split_coefficient_calculation,
    page_split_final_comparison,
    page_split_results,
    page_split_workflow,
)
from translations import get_translator


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
        def run(run_id, direction, delta_t, interval, interval_times):
            return {
                "run_id": run_id,
                "heading": direction,
                "filename": f"{interval}.csv",
                "start_kmh": 90.0 if interval == "high" else 45.0,
                "end_kmh": 70.0 if interval == "high" else 35.0,
                "reference_kmh": 80.0 if interval == "high" else 40.0,
                "delta_v_kmh": 20.0 if interval == "high" else 10.0,
                "delta_t_s": delta_t,
                "subintervals": (
                    ["90-85", "85-80"]
                    if interval == "high"
                    else ["45-40", "40-35"]
                ),
                "subinterval_times_s": interval_times,
            }

        parsed = {
            "high": [
                run(1, "+", 20.0, "high", [9.9, 10.1]),
                run(2, "+", 20.2, "high", [10.0, 10.2]),
                run(3, "-", 21.0, "high", [10.4, 10.6]),
                run(4, "-", 21.2, "high", [10.5, 10.7]),
            ],
            "low": [
                run(5, "+", 10.0, "low", [4.9, 5.1]),
                run(6, "+", 10.1, "low", [5.0, 5.1]),
                run(7, "-", 12.0, "low", [5.9, 6.1]),
                run(8, "-", 12.2, "low", [6.0, 6.2]),
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
            expander = stack.enter_context(
                patch.object(streamlit, "expander", return_value=_Container())
            )
            for method in ("subheader", "space"):
                stack.enter_context(patch.object(streamlit, method))
            markdown = stack.enter_context(patch.object(streamlit, "markdown"))
            caption = stack.enter_context(patch.object(streamlit, "caption"))
            dataframe = stack.enter_context(patch.object(streamlit, "dataframe"))
            stack.enter_context(patch.object(streamlit, "button", return_value=False))
            stack.enter_context(patch.object(streamlit, "info"))
            validator = stack.enter_context(
                patch.object(
                    page_split_coefficient_calculation,
                    "validate_split_selected_times",
                    wraps=page_split_coefficient_calculation.validate_split_selected_times,
                )
            )
            analyzer = stack.enter_context(
                patch.object(
                    page_split_coefficient_calculation,
                    "analyze_split_statistical_candidates",
                    wraps=page_split_coefficient_calculation.analyze_split_statistical_candidates,
                )
            )

            page_split_coefficient_calculation._render_statistical_analysis(
                _translate
            )

        validator.assert_called_once()
        analyzer.assert_not_called()
        self.assertEqual(dataframe.call_count, 6)
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

        high_frame = dataframe.call_args_list[2].args[0].data
        high_rows = high_frame.to_dict("records")
        self.assertEqual(
            list(high_frame.columns),
            ["run", "direction", "90-85", "85-80", "total_delta_t_s"],
        )
        self.assertEqual(len(high_rows), 4)
        self.assertEqual(high_rows[0]["run"], "1")
        self.assertEqual(high_rows[0]["direction"], "+")
        self.assertEqual(high_rows[0]["90-85"], 9.9)
        self.assertEqual(high_rows[-1]["total_delta_t_s"], 21.2)

        high_statistics = dataframe.call_args_list[3].args[0].to_dict("records")
        self.assertEqual(
            [row["interval"] for row in high_statistics],
            ["90-85", "85-80"],
        )
        self.assertAlmostEqual(high_statistics[0]["mean_s"], 10.2)
        self.assertAlmostEqual(
            high_statistics[0]["stdev_s"], 0.29439202887759464
        )
        self.assertAlmostEqual(
            high_statistics[0]["cv_pct"], 2.8861963615450455
        )

        low_frame = dataframe.call_args_list[4].args[0].data
        low_rows = low_frame.to_dict("records")
        self.assertEqual(
            list(low_frame.columns),
            ["run", "direction", "45-40", "40-35", "total_delta_t_s"],
        )
        self.assertEqual(len(low_rows), 4)
        self.assertEqual(low_rows[-1]["run"], "8")

        low_statistics = dataframe.call_args_list[5].args[0].to_dict("records")
        self.assertEqual(
            [row["interval"] for row in low_statistics],
            ["45-40", "40-35"],
        )
        self.assertEqual(
            sum(
                call.args[0] == "split_statistical_dispersion_caption"
                for call in caption.call_args_list
            ),
            2,
        )
        legend_titles = [
            call
            for call in markdown.call_args_list
            if call.args[0] == "**split_statistical_dispersion_title**"
        ]
        self.assertEqual(len(legend_titles), 2)
        self.assertTrue(
            all(
                call.kwargs["help"] == "split_statistical_dispersion_help"
                for call in legend_titles
            )
        )
        self.assertEqual(
            sum(
                call.args[0] == "split_statistical_dispersion_scale"
                for call in markdown.call_args_list
            ),
            2,
        )
        self.assertEqual(
            [call.args[0] for call in expander.call_args_list],
            ["split_graph_high_section_title", "split_graph_low_section_title"],
        )
        self.assertTrue(
            all(
                call.kwargs == {
                    "expanded": False,
                    "icon": ":material/table_rows:",
                }
                for call in expander.call_args_list
            )
        )
        self.assertEqual(state, original)

    def test_statistical_candidate_analysis_is_explicit_and_cached_per_parse(self):
        state = _SessionState(
            active_test_id="active",
            split_input_version=3,
            split_processed_at="2026-09-04T12:00:00+00:00",
        )
        parsed = {"high": [{"run_id": 1}], "low": []}
        analysis = {"candidate_groups": ()}
        streamlit = page_split_coefficient_calculation.st

        with ExitStack() as stack:
            stack.enter_context(patch.object(streamlit, "session_state", state))
            for method in ("subheader", "space", "caption"):
                stack.enter_context(patch.object(streamlit, method))
            button = stack.enter_context(
                patch.object(
                    streamlit,
                    "button",
                    side_effect=(False, True, False, False),
                )
            )
            spinner = stack.enter_context(
                patch.object(streamlit, "spinner", return_value=_Container())
            )
            info = stack.enter_context(patch.object(streamlit, "info"))
            success = stack.enter_context(patch.object(streamlit, "success"))
            analyzer = stack.enter_context(
                patch.object(
                    page_split_coefficient_calculation,
                    "analyze_split_statistical_candidates",
                    return_value=analysis,
                )
            )
            candidate_groups = stack.enter_context(
                patch.object(
                    page_split_coefficient_calculation,
                    "_render_statistical_candidate_groups",
                )
            )
            compatibility = stack.enter_context(
                patch.object(
                    page_split_coefficient_calculation,
                    "_render_statistical_direction_compatibility",
                )
            )

            for _ in range(3):
                page_split_coefficient_calculation._render_statistical_candidate_analysis(
                    parsed,
                    _translate,
                    {},
                )
            state["split_input_version"] += 1
            page_split_coefficient_calculation._render_statistical_candidate_analysis(
                parsed,
                _translate,
                {},
            )

        self.assertEqual(button.call_count, 4)
        self.assertEqual(info.call_count, 2)
        info.assert_called_with(
            "split_statistical_grouping_idle",
            icon=":material/info:",
        )
        spinner.assert_called_once_with(
            "split_statistical_grouping_running",
            show_time=True,
        )
        analyzer.assert_called_once_with(parsed)
        self.assertEqual(success.call_count, 2)
        self.assertEqual(candidate_groups.call_count, 2)
        self.assertEqual(compatibility.call_count, 2)
        self.assertIs(
            state["split_statistical_candidate_analysis_cache"]["analysis"],
            analysis,
        )

    def test_statistical_candidates_are_read_only_ranked_and_collapsible(self):
        def candidate(candidate_id, population, *, conforming, cohesion):
            return {
                "id": candidate_id,
                "population": population,
                "run_ids": (1, 2, 3, 4, 5),
                "runs": tuple(
                    {"source_index": index} for index in range(5)
                ),
                "size": 5,
                "mean_delta_t_s": 20.0,
                "sample_stdev_s": 0.2,
                "cv_pct": 1.0 if conforming else 3.0,
                "cv_conforming": conforming,
                "cv_limit_pct": 2.5,
                "cohesion_distance": cohesion,
            }

        def record(run_id, interval, direction):
            labels = (
                ["90-85", "85-80"]
                if interval == "high"
                else ["45-40", "40-35"]
            )
            times = [run_id / 10, run_id / 10 + 0.1]
            return {
                "run_id": run_id,
                "heading": direction,
                "subintervals": labels,
                "subinterval_times_s": times,
                "delta_t_s": sum(times),
            }

        parsed = {
            interval: [
                *(
                    record(run_id, interval, "+")
                    for run_id in range(start, start + 5)
                ),
                *(
                    record(run_id, interval, "-")
                    for run_id in range(start + 5, start + 10)
                ),
            ]
            for interval, start in (("high", 1), ("low", 11))
        }

        high_plus_secondary = candidate(
            "high_plus_1", "high_plus", conforming=False, cohesion=0.1
        )
        high_plus_primary = candidate(
            "high_plus_2", "high_plus", conforming=True, cohesion=0.8
        )
        populations = {
            "high_plus": {
                "candidate_groups": (
                    high_plus_secondary,
                    high_plus_primary,
                )
            },
            **{
                component: {
                    "candidate_groups": (
                        candidate(
                            f"{component}_1",
                            component,
                            conforming=True,
                            cohesion=0.4,
                        ),
                    )
                }
                for component in ("high_minus", "low_plus", "low_minus")
            },
        }

        def combination(interval, rank, *, opposite_conforming):
            plus_candidate_id = (
                "high_plus_2"
                if interval == "high" and rank == 1
                else f"{interval}_plus_1"
            )
            return {
                "rank": rank,
                "plus_candidate_id": plus_candidate_id,
                "plus_run_ids": (1, 2, 3, 4, 5),
                "plus_size": 5,
                "plus_mean_delta_t_s": 20.0,
                "plus_cv_pct": 1.0,
                "plus_cv_conforming": True,
                "minus_candidate_id": f"{interval}_minus_1",
                "minus_run_ids": (6, 7, 8, 9, 10),
                "minus_size": 5,
                "minus_mean_delta_t_s": 22.4,
                "minus_cv_pct": 1.2,
                "minus_cv_conforming": True,
                "both_directional_cvs_conforming": True,
                "opposite_difference_pct": 12.0 if not opposite_conforming else 8.0,
                "opposite_conforming": opposite_conforming,
                "opposite_limit_pct": 10.0,
                "usable_run_count": 10,
                "cohesion_distance": 0.8,
            }

        analysis = {
            "minimum_group_size": 5,
            "populations": populations,
            "opposite_direction_combinations": {
                "high": (
                    combination("high", 1, opposite_conforming=False),
                    combination("high", 2, opposite_conforming=False),
                ),
                "low": (combination("low", 1, opposite_conforming=True),),
            },
        }
        original = deepcopy(analysis)
        t = get_translator("en")
        streamlit = page_split_coefficient_calculation.st
        table_options = {
            "width": "stretch",
            "height": "content",
            "hide_index": True,
            "row_height": 32,
            "placeholder": "—",
        }

        with ExitStack() as stack:
            container = stack.enter_context(
                patch.object(streamlit, "container", return_value=_Container())
            )
            expander = stack.enter_context(
                patch.object(streamlit, "expander", return_value=_Container())
            )
            for method in ("subheader", "space"):
                stack.enter_context(patch.object(streamlit, method))
            stack.enter_context(patch.object(streamlit, "metric"))
            table = stack.enter_context(patch.object(streamlit, "table"))
            markdown = stack.enter_context(patch.object(streamlit, "markdown"))
            stack.enter_context(patch.object(streamlit, "caption"))
            badge = stack.enter_context(patch.object(streamlit, "badge"))
            dataframe = stack.enter_context(patch.object(streamlit, "dataframe"))
            warning = stack.enter_context(patch.object(streamlit, "warning"))
            controls = [
                stack.enter_context(patch.object(streamlit, method))
                for method in ("button", "checkbox", "selectbox")
            ]

            candidate_labels = page_split_coefficient_calculation._render_statistical_candidate_groups(
                analysis,
                parsed,
                t,
                table_options,
            )
            page_split_coefficient_calculation._render_statistical_direction_compatibility(
                analysis,
                candidate_labels,
                t,
                table_options,
            )

        rendered_markdown = [call.args[0] for call in markdown.call_args_list]
        self.assertIn(
            "**Top-ranked candidate — Candidate 1**",
            rendered_markdown,
        )
        self.assertIn("**Secondary candidates (1)**", rendered_markdown)
        population_expanders = expander.call_args_list[:4]
        self.assertEqual(
            [call.args[0] for call in population_expanders],
            ["High+", "High-", "Low+", "Low-"],
        )
        self.assertTrue(
            all(
                call.kwargs == {
                    "expanded": False,
                    "icon": ":material/groups:",
                    "type": "default",
                }
                for call in population_expanders
            )
        )
        self.assertNotIn(
            "Secondary candidates (1)",
            [call.args[0] for call in expander.call_args_list],
        )
        self.assertEqual(badge.call_count, 10)
        run_count_badges = [
            call
            for call in badge.call_args_list
            if call.args and call.args[0] == "5 runs"
        ]
        self.assertEqual(len(run_count_badges), 4)
        self.assertTrue(
            all(call.kwargs == {"color": "blue"} for call in run_count_badges)
        )
        directional_badges = [
            call
            for call in badge.call_args_list
            if call.args and call.args[0].startswith("Directional CV")
        ]
        self.assertEqual(len(directional_badges), 4)
        self.assertTrue(any(call.kwargs["color"] == "red" for call in badge.call_args_list))
        self.assertTrue(
            all(
                call.args[0].startswith("Directional CV")
                for call in directional_badges
            )
        )
        centered_text = [
            call for call in markdown.call_args_list
            if call.kwargs.get("text_alignment") == "center"
        ]
        self.assertEqual(len(centered_text), 24)
        self.assertEqual(
            [call.args[0] for call in centered_text[:6]],
            ["Mean Δt [s]", "**20.000 s**", "C.V. Δt [%]", "**1.00%**",
             "Cohesion distance", "**0.800**"],
        )
        self.assertTrue(centered_text[4].kwargs["help"].startswith(
            "Largest normalized distance"
        ))
        self.assertTrue(any(
            call.kwargs == {"width": "stretch", "gap": None}
            for call in container.call_args_list
        ))
        self.assertEqual(
            page_split_coefficient_calculation._normative_status_badge(
                None,
                _translate,
            ),
            {
                "label": "split_results_status_not_evaluable",
                "color": "gray",
                "icon": ":material/help:",
            },
        )
        self.assertEqual(
            page_split_coefficient_calculation._candidate_cv_status(
                high_plus_primary,
                t,
            )["label"],
            "Directional CV conforming (1.00% ≤ 2.5%)",
        )
        priority_matrices = [
            call.args[0]
            for call in dataframe.call_args_list
            if "total_delta_t_s" in call.args[0].columns
            and "direction" not in call.args[0].columns
        ]
        self.assertEqual(len(priority_matrices), 4)
        self.assertEqual(
            list(priority_matrices[0].columns),
            ["run", "90-85", "85-80", "total_delta_t_s"],
        )
        self.assertEqual(
            priority_matrices[0]["run"].tolist(),
            ["1", "2", "3", "4", "5"],
        )
        secondary_frame = table.call_args_list[0].args[0].data
        self.assertEqual(
            secondary_frame[t("split_statistical_candidate_id")].tolist(),
            ["Candidate 2"],
        )
        self.assertEqual(
            secondary_frame[t("split_statistical_cv_status")].iloc[0],
            "✕ Directional CV nonconforming (3.00% > 2.5%)",
        )
        self.assertEqual(
            table.call_args_list[0].kwargs,
            {"hide_index": True, "border": "horizontal"},
        )
        self.assertNotRegex(
            secondary_frame.to_string(), r"(high|low)_(plus|minus)_\d+"
        )
        secondary_combination_rows = next(
            call.args[0].to_dict("records")
            for call in dataframe.call_args_list
            if "rank" in call.args[0].columns
        )
        self.assertEqual(secondary_combination_rows[0]["rank"], 2)
        rendered_values = " ".join(
            [*rendered_markdown]
            + [
                str(value)
                for call in dataframe.call_args_list
                for value in call.args[0].astype(str).to_numpy().flat
            ]
        )
        self.assertNotIn("high_plus_", rendered_values)
        self.assertNotIn("high_minus_", rendered_values)
        self.assertNotIn("low_plus_", rendered_values)
        self.assertNotIn("low_minus_", rendered_values)
        warning.assert_called_once_with(
            "Both directional CVs conform, but opposite-direction compatibility "
            "exceeds the 10% limit.",
            icon=":material/warning:",
        )
        self.assertTrue(all(control.call_count == 0 for control in controls))
        self.assertEqual(analysis, original)

    def test_interval_matrix_heatmap_is_robust_and_population_local(self):
        frame = pd.DataFrame(
            {
                "run": [str(index) for index in range(1, 11)],
                "direction": ["+"] * 5 + ["-"] * 5,
                "90-85": [
                    10.0, 10.1, 10.2, 10.3, 10.6,
                    20.0, 20.1, 20.2, 20.3, 20.4,
                ],
                "85-80": [
                    5.0, 5.1, 5.2, 5.3, 5.8,
                    8.0, 8.1, 8.2, 8.3, 8.4,
                ],
                "total_delta_t_s": [15.0] * 10,
            }
        )
        styles = page_split_coefficient_calculation._interval_matrix_dispersion_styles(
            frame,
            ["90-85", "85-80"],
        )

        self.assertEqual(
            styles.at[4, "90-85"],
            page_split_coefficient_calculation.MODERATE_DISPERSION_STYLE,
        )
        self.assertEqual(
            styles.at[4, "85-80"],
            page_split_coefficient_calculation.STRONG_DISPERSION_STYLE,
        )
        self.assertTrue(
            (styles.loc[5:, ["90-85", "85-80"]] == "").all().all()
        )
        self.assertTrue(
            (
                styles[["run", "direction", "total_delta_t_s"]] == ""
            ).all().all()
        )

    def test_dispersion_legend_translations_disclose_metric_and_thresholds(self):
        for language, moderate, strong, formula, mad_definition in (
            (
                "pt",
                "2,5",
                "3,5",
                "score = 0,67449 × |valor − mediana| / MAD",
                "MAD é a mediana dos desvios absolutos",
            ),
            (
                "en",
                "2.5",
                "3.5",
                "score = 0.67449 × |value − median| / MAD",
                "MAD is the median absolute deviation",
            ),
        ):
            t = get_translator(language)
            title = t("split_statistical_dispersion_title")
            scale = t("split_statistical_dispersion_scale")
            help_text = t("split_statistical_dispersion_help")
            caption = t("split_statistical_dispersion_caption")

            self.assertIn("MAD", title)
            self.assertIn(f"score < {moderate}", scale)
            self.assertIn(f"{moderate} ≤ score < {strong}", scale)
            self.assertIn(f"score ≥ {strong}", scale)
            self.assertIn(formula, help_text)
            self.assertIn(mad_definition, help_text)
            self.assertIn(
                "direction" if language == "en" else "direção",
                caption,
            )
            self.assertIn("normativ", caption.lower())

    def test_statistical_candidate_translations_cover_read_only_statuses(self):
        keys = (
            "split_statistical_time_overview",
            "split_statistical_candidate_groups_title",
            "split_statistical_candidate_groups_caption",
            "split_statistical_run_grouping",
            "split_statistical_grouping_idle",
            "split_statistical_grouping_running",
            "split_statistical_grouping_completed",
            "split_statistical_no_candidate_groups",
            "split_statistical_primary_candidate",
            "split_statistical_candidate_number",
            "split_statistical_run_count",
            "split_statistical_cv_conforming",
            "split_statistical_cv_nonconforming",
            "split_statistical_cv_not_evaluable",
            "split_statistical_cv_status",
            "split_statistical_primary_run_details",
            "split_statistical_candidate_runs",
            "split_statistical_secondary_candidates",
            "split_statistical_candidate_id",
            "split_statistical_runs",
            "split_statistical_cohesion",
            "split_statistical_cohesion_help",
            "split_statistical_compatibility_title",
            "split_statistical_compatibility_caption",
            "split_statistical_no_compatibility",
            "split_statistical_secondary_combinations",
            "split_statistical_directional_pass_opposite_fail",
            "split_statistical_rank",
            "split_statistical_plus_candidate",
            "split_statistical_minus_candidate",
            "split_statistical_plus_runs",
            "split_statistical_minus_runs",
            "split_statistical_plus_status",
            "split_statistical_minus_status",
            "split_statistical_usable_runs",
        )
        for language in ("pt", "en"):
            t = get_translator(language)
            self.assertTrue(all(t(key) != key for key in keys))
            self.assertIn(
                "faixa e direção" if language == "pt" else "speed range and direction",
                t("split_statistical_time_overview"),
            )
            self.assertIn(
                "somente leitura" if language == "pt" else "Read-only",
                t("split_statistical_candidate_groups_caption"),
            )
            self.assertEqual(
                t("split_statistical_candidate_groups_title"),
                "Candidatos prioritários"
                if language == "pt"
                else "Priority candidates",
            )
            self.assertIn(
                "10%",
                t(
                    "split_statistical_directional_pass_opposite_fail",
                    limit=10.0,
                ),
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
