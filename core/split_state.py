# coding: utf-8
"""Session-state helpers for Split workflow invalidation."""


def invalidate_split_input_state(test_data: dict, reset_meteo_sync: bool = True) -> dict:
    """Clear Split-derived state after coastdown input files or mode change."""
    test_data["split_parsed_runs"] = {}
    test_data["split_results"] = []
    test_data["split_comparison_pairs"] = []
    test_data["split_last_calculated_result"] = None
    test_data["split_final_results"] = {}
    test_data["excel_buffer"] = None
    test_data["split_input_version"] = int(test_data.get("split_input_version") or 0) + 1
    if reset_meteo_sync:
        test_data["sync_meteo_by_time_only"] = False
    return test_data


def clear_split_final_state(test_data: dict) -> dict:
    """Clear final/export state after meteo or selection-dependent changes."""
    test_data["split_final_results"] = {}
    test_data["split_comparison_pairs"] = []
    test_data["split_last_calculated_result"] = None
    test_data["excel_buffer"] = None
    return test_data
