# coding: utf-8
"""Split vehicle data and normative effective-mass calculation."""

import streamlit as st

from core.split_vehicle_mass import (
    compute_split_effective_mass,
    normalize_split_vehicle_mass_data,
)


def _current_mass_data():
    return normalize_split_vehicle_mass_data({
        "vehicle_info": st.session_state.get("vehicle_info") or {},
        "total_mass": st.session_state.get("total_mass"),
    })


def _store_mass_data(mass_data):
    vehicle_info = st.session_state.vehicle_info
    vehicle_info.update(mass_data)
    # Compatibility aliases for inherited state; total_mass is the test mass M.
    vehicle_info["curb_mass"] = mass_data["running_order_mass_kg"]
    vehicle_info["inertia_mass"] = mass_data["rotational_equivalent_mass_kg"]
    vehicle_info["effective_mass"] = mass_data["effective_mass_kg"]
    st.session_state.total_mass = mass_data["test_mass_kg"]
    st.session_state.mass_input_mode = "running_order_mass"


def _invalidate_mass_dependent_results(previous_effective_mass, effective_mass):
    if previous_effective_mass in (None, effective_mass):
        return
    for key, empty_value in (
        ("split_results", []),
        ("split_comparison_pairs", []),
        ("split_last_calculated_result", None),
        ("split_auto_selection_last_result", None),
        ("split_auto_selection_pending", None),
        ("split_final_results", {}),
        ("split_results_excel_cache", None),
        ("excel_buffer", None),
    ):
        st.session_state[key] = empty_value


def render(t):
    """Render explicit Split mass inputs and calculated M, me and Me."""
    st.header(t("page_vehicle_data"))
    if not st.session_state.data_loaded:
        st.warning(t("error_no_file"))
        return

    st.subheader(f"🚗 {t('vehicle_information')}")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input(t("vehicle_model"), key="vehicle_model_input")
        st.session_state.vehicle_info["model"] = st.session_state.vehicle_model_input
    with col2:
        st.date_input(t("test_date"), key="test_date_input")
        st.session_state.vehicle_info["test_date"] = st.session_state.test_date_input

    st.markdown("---")
    st.subheader(f"⚖️ {t('split_vehicle_mass_title')}")
    current = _current_mass_data()
    running_default = current["running_order_mass_kg"] or 1500.0
    rotational_default = current["rotational_equivalent_mass_kg"] or 0.0
    has_informed_rotational_mass = bool(
        st.session_state.vehicle_info.get("rotational_mass_available", False)
    )

    running_order_mass = st.number_input(
        t("split_running_order_mass"), min_value=0.0, max_value=50000.0,
        value=float(running_default), step=10.0, format="%.2f",
    )
    rotational_available = st.checkbox(
        t("split_rotational_mass_available"), value=has_informed_rotational_mass,
    )
    rotational_mass = None
    if rotational_available:
        rotational_mass = st.number_input(
            t("split_rotational_equivalent_mass"), min_value=0.0,
            max_value=5000.0, value=float(rotational_default or 1.0),
            step=1.0, format="%.2f",
        )
    else:
        st.caption(t("split_rotational_mass_estimate_note"))

    if running_order_mass <= 0:
        st.session_state.vehicle_data_complete = False
        st.warning(t("error_no_mass"))
        return

    mass_data = compute_split_effective_mass(
        running_order_mass_kg=running_order_mass,
        rotational_equivalent_mass_kg=rotational_mass,
    )
    previous_effective_mass = current["effective_mass_kg"]
    st.session_state.vehicle_info["rotational_mass_available"] = rotational_available
    _store_mass_data(mass_data)
    _invalidate_mass_dependent_results(
        previous_effective_mass, mass_data["effective_mass_kg"],
    )

    st.subheader(t("split_vehicle_mass_summary"))
    columns = st.columns(3)
    columns[0].metric(t("split_test_mass"), f"{mass_data['test_mass_kg']:.2f} kg")
    columns[1].metric(
        t("split_rotational_equivalent_mass"),
        f"{mass_data['rotational_equivalent_mass_kg']:.2f} kg",
    )
    columns[2].metric(
        t("split_effective_mass"), f"{mass_data['effective_mass_kg']:.2f} kg",
    )

    st.markdown("---")
    if st.button(t("split_confirm_vehicle_data"), type="primary"):
        st.session_state.vehicle_data_complete = True
        st.success(t("split_vehicle_data_ready"))
