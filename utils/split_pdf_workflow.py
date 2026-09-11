"""Per-test report metadata and the Results PDF dialog; no scientific calculations."""

from copy import deepcopy
from datetime import datetime

import streamlit as st

from reports.split_pdf_report import export_split_final_results_to_pdf


METADATA_FIELDS = (
    "test_date", "responsible_engineer", "operator", "driver", "location",
    "service_identifier", "report_identifier", "start_time", "end_time",
    "logger", "vbox", "weather_station", "comments",
)
EQUIPMENT_FIELDS = ("logger", "vbox", "weather_station")


def prefill_report_metadata(test, state):
    """Prefer saved report edits, then available active-test metadata."""
    metadata = deepcopy(test.get("test_metadata") or {})
    vehicle = state.get("vehicle_info") or test.get("vehicle_info") or {}
    equipment = metadata.get("equipment", test.get("equipment", {}))
    equipment = deepcopy(equipment) if isinstance(equipment, dict) else {"logger": equipment}
    if "meteo" in equipment and "weather_station" not in equipment:
        equipment["weather_station"] = equipment.pop("meteo")
    for key in METADATA_FIELDS:
        if key in EQUIPMENT_FIELDS:
            equipment.setdefault(key, test.get(key, vehicle.get(key, "")))
        else:
            metadata.setdefault(key, test.get(key, vehicle.get(key, "")))
    metadata["test_date"] = vehicle.get("test_date") or state.get("csv_test_date") or metadata["test_date"]
    metadata["equipment"] = equipment
    # Current configuration is canonical; never replace it with an old report edit.
    metadata["configuration"] = deepcopy(state.get("split_interval_config", test.get("split_interval_config")))
    metadata["method"] = test.get("method") or metadata.get("method") or "Split"
    return metadata


def pdf_metadata(metadata, t):
    """Format metadata labels/configuration only; preserve all stored values."""
    supplied = deepcopy(metadata)
    supplied["equipment"] = {
        {"logger": "Logger", "vbox": "VBOX", "weather_station": "Meteo"}.get(key, key): value
        for key, value in metadata["equipment"].items()
    }
    config = supplied.get("configuration")
    if isinstance(config, dict):
        missing = t("split_pdf_not_provided")
        sections = []
        for interval in ("high", "low"):
            values = config.get(interval) or {}
            sections.append(f"{interval.title()} {values.get('start', missing)}-{values.get('end', missing)} km/h "
                            f"(ref. {values.get('reference', missing)})")
        sections.append(f"{t('split_pdf_step')}: {config.get('step_kmh', missing)} km/h")
        supplied["configuration"] = "; ".join(sections)
    return supplied


def _input_text(value):
    return "" if value is None else str(value).strip()


def _report_dialog(test_id, summary, vehicle_data, analysis, t):
    if st.session_state.get("active_test_id") != test_id:
        st.info(t("split_pdf_test_changed"))
        return
    test = st.session_state.tests[test_id]
    metadata = prefill_report_metadata(test, st.session_state)
    st.caption(t("split_pdf_metadata_note"))
    columns = st.columns(2)
    for index, key in enumerate(METADATA_FIELDS):
        source = metadata["equipment"] if key in EQUIPMENT_FIELDS else metadata
        target = st if key == "comments" else columns[index % 2]
        widget = target.text_area if key == "comments" else target.text_input
        options = {"disabled": bool((st.session_state.get("vehicle_info") or {}).get("test_date")
                                    or st.session_state.get("csv_test_date"))} if key == "test_date" else {}
        source[key] = widget(
            t("split_pdf_" + key), value=_input_text(source.get(key)),
            key=f"split_pdf_{test_id}_{key}", **options,
        ).strip()
    # Store raw blanks, not localized placeholders; language switches remain correct.
    test["test_metadata"] = {key: deepcopy(value) for key, value in metadata.items()
                             if key != "configuration"}
    values = [metadata["equipment"].get(key) if key in EQUIPMENT_FIELDS else metadata.get(key)
              for key in METADATA_FIELDS]
    if any(not _input_text(value) for value in values):
        st.caption(t("split_pdf_missing_notice"))
    if st.button(t("split_pdf_generate"), type="primary", icon=":material/picture_as_pdf:", width="stretch"):
        language = st.session_state.get("language", "pt")
        supplied = pdf_metadata(metadata, t)
        try:
            with st.spinner(t("split_pdf_generate")):
                payload = export_split_final_results_to_pdf(
                    final_results=summary, vehicle_data=vehicle_data,
                    deviation_analysis=analysis,
                    graph_series=deepcopy(test.get("graph_series") or []),
                    test_name=test.get("name", ""), generated_at=datetime.now().astimezone(),
                    test_metadata=supplied, language=language,
                )
        except ValueError:
            st.error(t("split_pdf_layout_error"))
            return
        st.download_button(t("split_pdf_download"), payload,
                           file_name="relatorio_split.pdf", mime="application/pdf",
                           on_click="ignore", width="stretch")


def render_pdf_export(summary, vehicle_data, analysis, t):
    """Open the metadata dialog only after an explicit PDF request."""
    test_id = st.session_state.get("active_test_id")
    if test_id not in st.session_state.get("tests", {}):
        return
    if st.session_state.get("split_pdf_dialog_test") != test_id:
        st.session_state.pop("split_pdf_dialog_test", None)
    if st.button(t("split_pdf_open"), icon=":material/picture_as_pdf:", width="stretch"):
        st.session_state.split_pdf_dialog_test = test_id
    if st.session_state.get("split_pdf_dialog_test") == test_id:
        st.dialog(t("split_pdf_title"), width="medium",
                  on_dismiss=lambda: st.session_state.pop("split_pdf_dialog_test", None))(_report_dialog)(
            test_id, deepcopy(summary), deepcopy(vehicle_data), deepcopy(analysis), t,
        )
