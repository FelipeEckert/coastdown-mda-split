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
    for result in test_data.get("split_results") or []:
        if isinstance(result, dict):
            result.pop("weather_sync", None)
            result.pop("ambient_by_component", None)
            if result.get("ambient_mode") == "weather_sync":
                result["correction_available"] = False
                result["corrected_result_plus"] = None
                result["corrected_result_minus"] = None
                result["corrected_pair_mean"] = None
                result["temp_plus_used"] = None
                result["press_plus_used"] = None
                result["temp_minus_used"] = None
                result["press_minus_used"] = None
                for component in ("high_plus", "low_plus", "high_minus", "low_minus"):
                    result[f"temp_{component}"] = None
                    result[f"press_{component}"] = None
                    result[f"wind_{component}"] = None
                result["F0_plus"] = None
                result["F2_plus"] = None
                result["F0_minus"] = None
                result["F2_minus"] = None
                result["F0_mean"] = None
                result["F2_mean"] = None
                result["energy"] = None
                result["energy_unit"] = None
                result["energy_profile"] = None
                result["energy_origin"] = None
                result["energy_details"] = None
    test_data["split_final_results"] = {}
    test_data["split_comparison_pairs"] = []
    test_data["split_last_calculated_result"] = None
    test_data["excel_buffer"] = None
    return test_data


def invalidate_split_ambient_state(test_data: dict) -> dict:
    """Clear results whose correction depends on changed ambient conditions."""
    test_data["split_results"] = []
    test_data["split_comparison_pairs"] = []
    test_data["split_last_calculated_result"] = None
    test_data["split_final_results"] = {}
    test_data["excel_buffer"] = None
    test_data["split_ambient_version"] = (
        int(test_data.get("split_ambient_version") or 0) + 1
    )
    return test_data
