# coding: utf-8
"""
Página 2: Dados do Veículo

Permite ao usuário inserir informações do veículo e calcular a massa efetiva.
"""

import streamlit as st

# Adiciona o diretório raiz ao path



def render(t):
    """Renderiza a página de dados do veículo."""
    
    st.header(t("page_vehicle_data"))
    
    # Verifica se os dados foram carregados
    if not st.session_state.data_loaded:
        st.warning(t("error_no_file"))
        return
    
    # ===== INFORMAÇÕES DO VEÍCULO =====
    st.subheader(f"🚗 {t('vehicle_information')}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input(
            t("vehicle_model"),
            key="vehicle_model_input"
        )
        st.session_state.vehicle_info["model"] = st.session_state.vehicle_model_input
    
    with col2:
        st.date_input(
            t("test_date"),
            key="test_date_input"
        )
        st.session_state.vehicle_info["test_date"] = st.session_state.test_date_input
    
    st.markdown("---")
    
    # ===== MODO DE ENTRADA DE MASSA =====
    st.subheader(f"⚖️ {t('mass_input_mode')}")
    
    mass_mode = st.radio(
        t("mass_input_mode"),
        options=[t("total_mass_direct"), t("component_masses")],
        horizontal=True,
        label_visibility="collapsed"
    )
    st.caption(t("mass_norm_note"))
    
    # Determina o modo baseado na seleção
    if mass_mode == t("total_mass_direct"):
        st.session_state.mass_input_mode = "total"
        render_total_mass_input(t)
    else:
        st.session_state.mass_input_mode = "components"
        render_component_masses_input(t)
    
    st.markdown("---")
    
    # ===== RESUMO DA MASSA =====
    if st.session_state.total_mass > 0:
        st.subheader("📊 Resumo")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(t("total_mass"), f"{st.session_state.total_mass:.1f} kg")
        
        with col2:
            inertia_mass = st.session_state.vehicle_info.get("inertia_mass", 0.0)
            st.metric(t("inertia_mass"), f"{inertia_mass:.1f} kg")
        
        with col3:
            effective_mass = st.session_state.total_mass + inertia_mass
            st.session_state.vehicle_info["effective_mass"] = effective_mass
            st.metric(t("effective_mass"), f"{effective_mass:.1f} kg")
    
    st.markdown("---")
    
    # ===== ACAO SPLIT =====
    if st.button(t("split_confirm_vehicle_data"), type="primary"):
        if st.session_state.total_mass > 0:
            st.session_state.vehicle_data_complete = True
            st.success(t("split_vehicle_data_ready"))
        else:
            st.warning(t("error_no_mass"))


def render_total_mass_input(t):
    """Renderiza entrada de massa total direta."""
    
    col1, col2 = st.columns(2)
    
    with col1:
        total_mass = st.number_input(
            t("total_mass"),
            min_value=0.0,
            max_value=50000.0,
            value=st.session_state.total_mass if st.session_state.total_mass > 0 else 1500.0,
            step=10.0,
            format="%.1f"
        )
        st.session_state.total_mass = total_mass
    
    with col2:
        # Calcula automaticamente 3% da massa total (conforme ABNT 10312)
        inertia_percentage = st.number_input(
            "Percentual de Inércia (%)",
            min_value=0.0,
            max_value=10.0,
            value=3.0,
            step=0.1,
            format="%.1f",
            help="Percentual de massa de inércia rotacional (padrão ABNT: 3%)"
        )
        
        # Calcula a massa de inércia
        inertia_mass = total_mass * (inertia_percentage / 100.0)
        st.session_state.vehicle_info["inertia_mass"] = inertia_mass
        st.session_state.vehicle_info["inertia_percentage"] = inertia_percentage
        
        # Mostra o valor calculado
        st.info(f"Massa de Inércia: **{inertia_mass:.1f} kg**")


def render_component_masses_input(t):
    """Renderiza entrada de massas por componente."""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        curb_mass = st.number_input(
            t("curb_mass"),
            min_value=0.0,
            max_value=50000.0,
            value=st.session_state.vehicle_info.get("curb_mass", 1200.0),
            step=10.0,
            format="%.1f"
        )
        st.session_state.vehicle_info["curb_mass"] = curb_mass
    
    with col2:
        driver_mass = st.number_input(
            t("driver_mass"),
            min_value=0.0,
            max_value=500.0,
            value=st.session_state.vehicle_info.get("driver_mass", 75.0),
            step=1.0,
            format="%.1f"
        )
        st.session_state.vehicle_info["driver_mass"] = driver_mass
    
    with col3:
        equipment_mass = st.number_input(
            t("equipment_mass"),
            min_value=0.0,
            max_value=1000.0,
            value=st.session_state.vehicle_info.get("equipment_mass", 50.0),
            step=1.0,
            format="%.1f"
        )
        st.session_state.vehicle_info["equipment_mass"] = equipment_mass
    
    # Calcula massa total
    total_mass = curb_mass + driver_mass + equipment_mass
    st.session_state.total_mass = total_mass
    
    # Percentual de inércia (conforme ABNT 10312)
    inertia_percentage = st.number_input(
        "Percentual de Inércia (%)",
        min_value=0.0,
        max_value=10.0,
        value=st.session_state.vehicle_info.get("inertia_percentage", 3.0),
        step=0.1,
        format="%.1f",
        help="Percentual de massa de inércia rotacional (padrão ABNT: 3%)"
    )
    st.session_state.vehicle_info["inertia_percentage"] = inertia_percentage
    
    # Calcula a massa de inércia automaticamente
    inertia_mass = total_mass * (inertia_percentage / 100.0)
    st.session_state.vehicle_info["inertia_mass"] = inertia_mass
    
    # Mostra os totais calculados
    st.info(f"**{t('total_mass')}:** {total_mass:.1f} kg")
    st.info(f"**Massa de Inércia:** {inertia_mass:.1f} kg ({inertia_percentage}%)")
