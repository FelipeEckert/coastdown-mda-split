# coding: utf-8
"""Session-state helpers for Split workflow invalidation."""

from copy import deepcopy
from datetime import datetime, timezone


LEGACY_SPLIT_FINAL_RESULTS_FLAG = "_split_final_results_legacy_only"


def build_split_fixed_conditions(temperature: float, pressure: float) -> dict:
    """Store fixed inputs under legacy and canonical Split keys."""
    return {
        "fixed_temperature": temperature,
        "fixed_pressure": pressure,
        "split_fixed_temperature": temperature,
        "split_fixed_pressure": pressure,
    }


def migrate_split_fixed_conditions(test_data: dict) -> None:
    """Populate missing canonical Split keys from legacy saved state in place."""
    for canonical_key, legacy_key in (
        ("split_fixed_temperature", "fixed_temperature"),
        ("split_fixed_pressure", "fixed_pressure"),
    ):
        if canonical_key not in test_data and legacy_key in test_data:
            test_data[canonical_key] = test_data[legacy_key]


def _legacy_split_final_count(legacy) -> int | None:
    """Return one valid count shared by every current legacy count field."""
    if not isinstance(legacy, dict):
        return None
    counts = []
    for key in ("num_results", "num_pairs"):
        if key not in legacy:
            continue
        value = legacy[key]
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            return None
        counts.append(value)
    return counts[0] if counts and len(set(counts)) == 1 else None


def migrate_legacy_split_final_results(test_data: dict) -> bool:
    """Restore canonical pairs only from a complete legacy selected-pair list."""
    if "split_comparison_pairs" in test_data:
        return False
    legacy = test_data.get("split_final_results")
    selected_pairs = legacy.get("selected_pairs") if isinstance(legacy, dict) else None
    count = _legacy_split_final_count(legacy)
    if (
        not isinstance(selected_pairs, list)
        or not selected_pairs
        or count is None
        or count != len(selected_pairs)
        or any(
            not isinstance(pair, dict) or pair.get("selected") is not True
            for pair in selected_pairs
        )
    ):
        return False
    pair_ids = [pair.get("id") for pair in selected_pairs]
    if (
        any(not isinstance(pair_id, str) or not pair_id.strip() for pair_id in pair_ids)
        or len({pair_id.strip() for pair_id in pair_ids}) != len(pair_ids)
    ):
        return False

    from core.split_comparison import is_split_pair_corrected

    if any(not is_split_pair_corrected(pair) for pair in selected_pairs):
        return False
    test_data["split_comparison_pairs"] = deepcopy(selected_pairs)
    return True


def clear_split_final_results_compatibility(test_data: dict) -> None:
    """Remove the read-only legacy summary after canonical state changes."""
    test_data.pop("split_final_results", None)
    test_data.pop(LEGACY_SPLIT_FINAL_RESULTS_FLAG, None)


def split_final_results_status(test_data: dict) -> dict:
    """Return current final-result availability from canonical or legacy state."""
    if test_data.get(LEGACY_SPLIT_FINAL_RESULTS_FLAG):
        legacy = test_data.get("split_final_results")
        count = _legacy_split_final_count(legacy)
        return {
            "source": "legacy",
            "available": count is not None,
            "selected_pair_count": count or 0,
        }

    from core.split_results import consolidate_split_final_results

    summary = consolidate_split_final_results(
        test_data.get("split_comparison_pairs") or []
    )
    count = summary["num_results"]
    return {
        "source": "split_comparison_pairs",
        "available": count > 0,
        "selected_pair_count": count,
    }


def ensure_split_comparison_pairs(test_data: dict) -> list[dict]:
    """Initialize comparison pairs only when the state key is absent."""
    if "split_comparison_pairs" not in test_data:
        # Navigation/rendering must never replace an existing comparison list.
        test_data["split_comparison_pairs"] = []
    return test_data["split_comparison_pairs"]


def invalidate_split_input_state(test_data: dict, reset_meteo_sync: bool = True) -> dict:
    """Clear Split-derived state after coastdown input files or mode change."""
    test_data["split_parsed_runs"] = {}
    test_data["split_results"] = []
    test_data["split_comparison_pairs"] = []
    test_data["split_last_calculated_result"] = None
    test_data["split_auto_selection_last_result"] = None
    test_data["split_auto_selection_pending"] = None
    test_data["split_auto_replace_request"] = None
    test_data["split_auto_replace_dialog_open"] = False
    clear_split_final_results_compatibility(test_data)
    test_data["excel_buffer"] = None
    test_data["split_input_version"] = int(test_data.get("split_input_version") or 0) + 1
    test_data["split_parse_dirty"] = True
    test_data["split_parse_feedback_current"] = False
    test_data["split_parse_validation_issues"] = []
    test_data["split_processed_at"] = None
    if reset_meteo_sync:
        test_data["sync_meteo_by_time_only"] = False
    return test_data


def initialize_split_parse_state(test_data: dict, processed_config: dict) -> dict:
    """Initialize draft/dirty state for new and legacy Split tests."""
    if test_data.get("split_interval_draft_config") is None:
        test_data["split_interval_draft_config"] = deepcopy(processed_config)
    if "split_parse_dirty" not in test_data:
        test_data["split_parse_dirty"] = not bool(test_data.get("split_parsed_runs"))
    if "split_parse_feedback_current" not in test_data:
        test_data["split_parse_feedback_current"] = (
            bool(test_data.get("split_parsed_runs"))
            and not test_data["split_parse_dirty"]
        )
    test_data.setdefault("split_parse_validation_issues", [])
    test_data.setdefault("split_processed_at", None)
    return test_data


def update_split_interval_draft(test_data: dict, new_config: dict) -> bool:
    """Store edited fields and mark the current parser output as stale."""
    previous_draft = test_data.get("split_interval_draft_config")
    changed = previous_draft != new_config
    test_data["split_interval_draft_config"] = deepcopy(new_config)
    config_differs = test_data.get("split_interval_config") != new_config
    if config_differs:
        test_data["split_parse_dirty"] = True
    elif test_data.get("split_parsed_runs"):
        test_data["split_parse_dirty"] = False
    if changed:
        test_data["split_parse_feedback_current"] = False
        test_data["split_parse_validation_issues"] = []
    return changed


def record_split_parse_failure(test_data: dict, issues: list[dict]) -> dict:
    """Keep stale parser data hidden and preserve validation feedback."""
    test_data["split_results"] = []
    test_data["split_comparison_pairs"] = []
    test_data["split_last_calculated_result"] = None
    test_data["split_auto_selection_last_result"] = None
    test_data["split_auto_selection_pending"] = None
    test_data["split_auto_replace_request"] = None
    test_data["split_auto_replace_dialog_open"] = False
    clear_split_final_results_compatibility(test_data)
    test_data["excel_buffer"] = None
    test_data["split_parse_dirty"] = True
    test_data["split_parse_feedback_current"] = True
    test_data["split_parse_validation_issues"] = deepcopy(issues)
    return test_data


def store_processed_split_intervals(
    test_data: dict,
    config: dict,
    parsed_runs: dict,
    processed_at: str | None = None,
) -> dict:
    """Commit one explicit parser run and invalidate older calculations."""
    invalidate_split_input_state(test_data, reset_meteo_sync=False)
    test_data["split_interval_config"] = deepcopy(config)
    test_data["split_interval_draft_config"] = deepcopy(config)
    test_data["split_parsed_runs"] = deepcopy(parsed_runs)
    test_data["split_processed_at"] = processed_at or datetime.now(
        timezone.utc
    ).isoformat()
    test_data["split_parse_dirty"] = False
    test_data["split_parse_feedback_current"] = True
    test_data["split_parse_validation_issues"] = []
    return test_data


def split_parse_is_current(test_data: dict) -> bool:
    """Return True only when parsed runs match the current interval draft."""
    if "split_parse_dirty" in test_data:
        return not bool(test_data.get("split_parse_dirty"))
    return bool(test_data.get("split_parsed_runs"))


def should_show_split_parse_details(test_data: dict) -> bool:
    """Return True only for feedback produced by the latest explicit attempt."""
    return bool(test_data.get("split_parse_feedback_current"))


def get_processed_split_review_state(test_data: dict) -> dict:
    """Return only committed parser inputs and outputs for the review UI."""
    return {
        "config": deepcopy(test_data.get("split_interval_config") or {}),
        "parsed_runs": deepcopy(test_data.get("split_parsed_runs") or {}),
        "processed_at": test_data.get("split_processed_at"),
    }


def update_split_interval_config(test_data: dict, new_config: dict) -> bool:
    """Save changed interval settings and invalidate every dependent result."""
    if test_data.get("split_interval_config") == new_config:
        return False

    test_data["split_interval_config"] = deepcopy(new_config)
    invalidate_split_input_state(test_data)
    return True


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
    clear_split_final_results_compatibility(test_data)
    test_data["split_comparison_pairs"] = []
    test_data["split_last_calculated_result"] = None
    test_data["split_auto_selection_last_result"] = None
    test_data["split_auto_selection_pending"] = None
    test_data["split_auto_replace_request"] = None
    test_data["split_auto_replace_dialog_open"] = False
    test_data["excel_buffer"] = None
    return test_data


def reset_split_final_outputs(test_data: dict) -> dict:
    """Clear Split final/export outputs after comparison selection changes."""
    clear_split_final_results_compatibility(test_data)
    test_data["excel_buffer"] = None
    test_data.pop("split_deviation_analysis_cache", None)
    test_data.pop("split_results_excel_cache", None)
    return test_data


def normalize_split_comparison_selection_state(test_data: dict) -> list[dict]:
    """Repair persisted comparison selection before rendering any main tab."""
    from core.split_comparison import force_uncorrected_split_pairs_unselected

    pairs = ensure_split_comparison_pairs(test_data)
    pairs, changed = force_uncorrected_split_pairs_unselected(pairs)
    if changed:
        test_data["split_comparison_pairs"] = pairs
        reset_split_final_outputs(test_data)
    return pairs


def clear_split_comparison_state(test_data: dict) -> dict:
    """Clear only final comparison pairs and their derived final outputs."""
    test_data["split_comparison_pairs"] = []
    reset_split_final_outputs(test_data)
    return test_data


def invalidate_split_ambient_state(test_data: dict) -> dict:
    """Clear results whose correction depends on changed ambient conditions."""
    test_data["split_results"] = []
    test_data["split_comparison_pairs"] = []
    test_data["split_last_calculated_result"] = None
    test_data["split_auto_selection_last_result"] = None
    test_data["split_auto_selection_pending"] = None
    test_data["split_auto_replace_request"] = None
    test_data["split_auto_replace_dialog_open"] = False
    clear_split_final_results_compatibility(test_data)
    test_data["excel_buffer"] = None
    try:
        ambient_version = int(test_data.get("split_ambient_version") or 0)
    except (TypeError, ValueError, OverflowError):
        ambient_version = 0
    test_data["split_ambient_version"] = ambient_version + 1
    return test_data
