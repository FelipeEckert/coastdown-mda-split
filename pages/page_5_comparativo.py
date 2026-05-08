# coding: utf-8
"""
Página 5: Comparativo Final

Permite ao usuário comparar múltiplos pares calculados e selecionar para análise final.
Pares adicionados pelo algoritmo são destacados com cores:
  - Verde claro (#D1FFBD): selecionado por Menor Energia
  - Azul claro (#ADD8E6): selecionado por Proximidade ao Target
"""

import streamlit as st
import pandas as pd
import numpy as np
from statistics import mean, stdev
import os
import sys

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.calculations import calcular_energia


def normalize_pair(pair: dict) -> dict:
    """
    Retorna cópia do par com chaves canônicas resolvidas.

    Pares de page_3 (manual) e page_4 (algoritmo) usam nomes de campos
    diferentes para os mesmos valores. Esta função unifica em chaves
    prefixadas com '_' para evitar colisão:

        _f0, _f2, _cv_f0, _cv_f2, _energy

    Retorna None nos campos ausentes ou não-numéricos (ex.: energy="N/A"
    quando correção climática não foi aplicada). Nunca retorna 0.0 como
    fallback silencioso — campos ausentes devem ser tratados explicitamente
    pelo código de exibição.
    """
    def _resolve(keys):
        for k in keys:
            v = pair.get(k)
            if v is not None and isinstance(v, (int, float)):
                return float(v)
        return None

    result = dict(pair)
    result["_f0"]     = _resolve(("f0_corr", "mean_f0_corrected", "f0corr_mean"))
    result["_f2"]     = _resolve(("f2_corr", "mean_f2_corrected", "f2corr_mean"))
    result["_cv_f0"]  = _resolve(("cv_f0_corr", "cv_f0_corrected", "cv_f0"))
    result["_cv_f2"]  = _resolve(("cv_f2_corr", "cv_f2_corrected", "cv_f2"))
    result["_energy"] = _resolve(("energy", "mean_energy_corrected"))
    return result


def _is_corrected(pair: dict) -> bool:
    """Retorna True se o par possui F0 e F2 corrigidos válidos."""
    n = normalize_pair(pair)
    return n["_f0"] is not None and n["_f2"] is not None


def _format_wind(pair):
    """Formata o vento do par para exibição."""
    wind_avg = pair.get("wind_avg_ms")
    wind_ida = pair.get("wind_ida_ms")
    wind_volta = pair.get("wind_volta_ms")
    
    # Tenta exibir ida/volta separados
    if wind_ida is not None or wind_volta is not None:
        try:
            w_i = f"{float(wind_ida):.2f}" if wind_ida is not None and not pd.isna(wind_ida) else "N/A"
        except (TypeError, ValueError):
            w_i = "N/A"
        try:
            w_v = f"{float(wind_volta):.2f}" if wind_volta is not None and not pd.isna(wind_volta) else "N/A"
        except (TypeError, ValueError):
            w_v = "N/A"
        return f"{w_i} / {w_v}"
    
    # Fallback: vento médio
    if wind_avg is not None:
        try:
            if not pd.isna(wind_avg):
                return f"{float(wind_avg):.2f}"
        except (TypeError, ValueError):
            pass
    
    return "N/A"


def render(t):
    """Renderiza a página de comparativo final."""
    
    st.header(t("page_final_comparison"))
    
    # Verifica se há pares calculados
    if not st.session_state.calculated_pairs:
        st.warning(t("error_no_pairs"))
        return
    
    # ===== AÇÕES EM LOTE (Selecionar/Desselecionar) =====
    st.subheader(t('auto_select_best'))
    
    # Inicializa flag de ação se não existir
    if "batch_action" not in st.session_state:
        st.session_state.batch_action = None
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Selecionar Todos", use_container_width=True, key="select_all"):
            st.session_state.batch_action = "select_all"
    
    with col2:
        if st.button("❎ Desselecionar Todos", use_container_width=True, key="deselect_all"):
            st.session_state.batch_action = "deselect_all"
    
    with col3:
        if st.button("🔄 Inverter Seleção", use_container_width=True, key="invert_selection"):
            st.session_state.batch_action = "invert"
    
    # Aplica ação em lote ANTES de renderizar checkboxes (apenas pares com correção)
    if st.session_state.batch_action == "select_all":
        for pair_id, pair in st.session_state.calculated_pairs.items():
            if _is_corrected(pair):
                st.session_state.calculated_pairs[pair_id]["selected"] = True
        st.session_state.batch_action = None
        st.rerun()
    elif st.session_state.batch_action == "deselect_all":
        for pair_id, pair in st.session_state.calculated_pairs.items():
            if _is_corrected(pair):
                st.session_state.calculated_pairs[pair_id]["selected"] = False
        st.session_state.batch_action = None
        st.rerun()
    elif st.session_state.batch_action == "invert":
        for pair_id, pair in st.session_state.calculated_pairs.items():
            if _is_corrected(pair):
                current = st.session_state.calculated_pairs[pair_id].get("selected", False)
                st.session_state.calculated_pairs[pair_id]["selected"] = not current
        st.session_state.batch_action = None
        st.rerun()
    
    st.markdown("---")
    
    # ===== LEGENDA DE CORES =====
    col_leg1, col_leg2, col_leg3 = st.columns([1, 1, 1])
    with col_leg1:
        st.markdown("**Legenda:**")
    with col_leg2:
        st.markdown("🟢 <span style='background-color: #D1FFBD; padding: 4px 12px; border-radius: 4px; color: black;'>Selecionado por Energia</span>", unsafe_allow_html=True)
    with col_leg3:
        st.markdown("🔵 <span style='background-color: #ADD8E6; padding: 4px 12px; border-radius: 4px; color: black;'>Selecionado por Target</span>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ===== TABELA DE PARES CALCULADOS =====
    st.subheader(f"📊 {t('calculated_pairs')}")
    render_pairs_selection_table(t)
    
    st.markdown("---")
    
    # ===== ESTATÍSTICAS DOS PARES SELECIONADOS =====
    selected_pairs = [p for p in st.session_state.calculated_pairs.values()
                      if p.get("selected", False) and _is_corrected(p)]
    
    if selected_pairs:
        st.subheader(f"📈 Estatísticas dos Pares Selecionados ({len(selected_pairs)} pares)")
        render_selection_statistics(t, selected_pairs)
        
        st.markdown("---")
        
        # ===== BOTÃO CALCULAR RESULTADOS FINAIS =====
        if st.button(f"🎯 {t('calculate_final_results')}", type="primary", use_container_width=True):
            calculate_and_store_final_results(t, selected_pairs)
    else:
        st.info("💡 Selecione pelo menos um par para ver as estatísticas e calcular os resultados finais.")


def render_pairs_selection_table(t):
    """Renderiza tabela de seleção de pares, separando corrigidos de não-corrigidos."""

    pairs = list(st.session_state.calculated_pairs.items())

    if not pairs:
        st.info("Nenhum par calculado ainda")
        return

    corrected   = [(pid, p) for pid, p in pairs if _is_corrected(p)]
    uncorrected = [(pid, p) for pid, p in pairs if not _is_corrected(p)]

    # Garante que pares sem correção nunca ficam marcados como selecionados
    for pid, _ in uncorrected:
        st.session_state.calculated_pairs[pid]["selected"] = False

    col_ratios = [0.5, 0.9, 0.9, 0.9, 1.0, 1.1, 1.1, 0.8, 0.8, 1.0, 0.5]

    def _fmt(val, fmt):
        return format(val, fmt) if val is not None else "N/A"

    def _render_header(labels, label_color="#ffffff"):
        cols = st.columns(col_ratios)
        for col, header in zip(cols, labels):
            col.markdown(
                f"<div style='text-align:center;font-size:0.85em;color:{label_color};'>"
                f"<strong>{header}</strong></div>",
                unsafe_allow_html=True
            )

    def _render_row(pair_id, pair, selectable=True):
        norm = normalize_pair(pair)

        if selectable:
            bg_color, text_color = "#1e1e1e", "white"
            if pair.get("selected_by_energy_algo", False):
                bg_color, text_color = "#D1FFBD", "black"
            elif pair.get("selected_by_target_algo", False):
                bg_color, text_color = "#ADD8E6", "black"
        else:
            bg_color, text_color = "rgba(255,152,0,0.10)", "#ffb74d"

        temp  = pair.get("temp",  pair.get("temp_ida_used",  "N/A"))
        press = pair.get("press", pair.get("press_ida_used", "N/A"))
        temp_str   = f"{temp:.1f}"  if isinstance(temp,  (int, float)) else "N/A"
        press_str  = f"{press:.2f}" if isinstance(press, (int, float)) else "N/A"
        wind_str   = _format_wind(pair)

        if selectable:
            f0_str = _fmt(norm["_f0"], ".4f")
            f2_str = _fmt(norm["_f2"], ".6f")
        else:
            # Seção de referência: exibe valores brutos (sem correção climática)
            def _raw(keys):
                for k in keys:
                    v = pair.get(k)
                    if v is not None and isinstance(v, (int, float)):
                        return float(v)
                return None
            f0_str = _fmt(_raw(("f0_mean", "f0_par", "f0corr_mean")), ".4f")
            f2_str = _fmt(_raw(("f2_mean", "f2_par", "f2corr_mean")), ".6f")

        cv_f0_str  = _fmt(norm["_cv_f0"],  ".2f")
        cv_f2_str  = _fmt(norm["_cv_f2"],  ".2f")
        energy_str = _fmt(norm["_energy"], ".4f")

        row_cols = st.columns(col_ratios)
        cell = (f"text-align:center;background-color:{bg_color};color:{text_color};"
                f"padding:8px;border-radius:4px;font-size:0.85em;")

        with row_cols[0]:
            if selectable:
                sel = st.checkbox("", value=pair.get("selected", False),
                                  key=f"sel_{pair_id}", label_visibility="collapsed")
                st.session_state.calculated_pairs[pair_id]["selected"] = sel
            else:
                st.markdown(f"<div style='{cell}'>⚠️</div>", unsafe_allow_html=True)
        with row_cols[1]:
            st.markdown(f"<div style='{cell}'><strong>{pair_id}</strong></div>", unsafe_allow_html=True)
        with row_cols[2]:
            st.markdown(f"<div style='{cell}'>{temp_str}</div>", unsafe_allow_html=True)
        with row_cols[3]:
            st.markdown(f"<div style='{cell}'>{press_str}</div>", unsafe_allow_html=True)
        with row_cols[4]:
            st.markdown(f"<div style='{cell}'>{wind_str}</div>", unsafe_allow_html=True)
        with row_cols[5]:
            st.markdown(f"<div style='{cell}'>{f0_str}</div>", unsafe_allow_html=True)
        with row_cols[6]:
            st.markdown(f"<div style='{cell}'>{f2_str}</div>", unsafe_allow_html=True)
        with row_cols[7]:
            cv_f0 = norm["_cv_f0"]
            cv_style = cell if (cv_f0 is None or cv_f0 <= 10) else (
                f"text-align:center;background-color:{bg_color};color:#ff6b6b;"
                f"padding:8px;border-radius:4px;font-weight:bold;font-size:0.85em;")
            st.markdown(f"<div style='{cv_style}'>{cv_f0_str}</div>", unsafe_allow_html=True)
        with row_cols[8]:
            cv_f2 = norm["_cv_f2"]
            cv_style = cell if (cv_f2 is None or cv_f2 <= 10) else (
                f"text-align:center;background-color:{bg_color};color:#ff6b6b;"
                f"padding:8px;border-radius:4px;font-weight:bold;font-size:0.85em;")
            st.markdown(f"<div style='{cv_style}'>{cv_f2_str}</div>", unsafe_allow_html=True)
        with row_cols[9]:
            st.markdown(f"<div style='{cell}'>{energy_str}</div>", unsafe_allow_html=True)
        with row_cols[10]:
            if st.button("❌", key=f"rem_{pair_id}", help=f"Remover par {pair_id}", use_container_width=True):
                del st.session_state.calculated_pairs[pair_id]
                st.rerun()
        st.markdown("<hr style='margin:2px 0;'>", unsafe_allow_html=True)

    # --- Seção 1: Pares com correção climática ---
    if corrected:
        _render_header(["Sel", "Par", "Temp (°C)", "Press (kPa)", "Vento (m/s)",
                        "F0 (N)", "F2 (N/km/h²)", "CV F0 (%)", "CV F2 (%)", "Energia", "❌"])
        st.markdown("---")
        for pair_id, pair in corrected:
            _render_row(pair_id, pair, selectable=True)
    else:
        st.info("Nenhum par com correção climática calculado ainda.")

    # --- Seção 2: Pares sem correção (referência) ---
    if uncorrected:
        st.markdown("---")
        st.markdown("**⚠️ Pares sem Correção Climática — apenas para referência**")
        st.caption("Estes pares não possuem coeficientes corrigidos e não podem ser incluídos no cálculo de resultados finais.")
        _render_header(["—", "Par", "Temp (°C)", "Press (kPa)", "Vento (m/s)",
                        "f'0 (N)", "f'2 (N/m/s²)", "CV F0 (%)", "CV F2 (%)", "Energia", "❌"],
                       label_color="#ffb74d")
        st.markdown("---")
        for pair_id, pair in uncorrected:
            _render_row(pair_id, pair, selectable=False)


def render_selection_statistics(t, selected_pairs):
    """Renderiza estatísticas dos pares selecionados."""
    norms = [normalize_pair(p) for p in selected_pairs]

    f0_values     = [n["_f0"]     for n in norms if n["_f0"]     is not None]
    f2_values     = [n["_f2"]     for n in norms if n["_f2"]     is not None]
    energy_values = [n["_energy"] for n in norms if n["_energy"] is not None]

    n_missing_f0 = len(selected_pairs) - len(f0_values)
    n_missing_energy = len(selected_pairs) - len(energy_values)

    if n_missing_f0:
        st.warning(f"⚠️ {n_missing_f0} par(es) sem F0/F2 válido — excluídos das estatísticas.")

    col1, col2, col3 = st.columns(3)

    with col1:
        if f0_values:
            mean_f0 = mean(f0_values)
            cv_f0 = (stdev(f0_values) / mean_f0 * 100) if len(f0_values) > 1 and mean_f0 != 0 else 0
            st.metric(t("mean_f0"), f"{mean_f0:.4f} N")
            st.metric(t("cv_f0"), f"{cv_f0:.2f}%")
        else:
            st.metric(t("mean_f0"), "N/A")
            st.metric(t("cv_f0"), "N/A")

    with col2:
        if f2_values:
            mean_f2 = mean(f2_values)
            cv_f2 = (stdev(f2_values) / mean_f2 * 100) if len(f2_values) > 1 and mean_f2 != 0 else 0
            st.metric(t("mean_f2"), f"{mean_f2:.6f}")
            st.metric(t("cv_f2"), f"{cv_f2:.2f}%")
        else:
            st.metric(t("mean_f2"), "N/A")
            st.metric(t("cv_f2"), "N/A")

    with col3:
        if energy_values:
            mean_energy = mean(energy_values)
            label = t("energy")
            if n_missing_energy:
                label += f" ({len(energy_values)}/{len(selected_pairs)} pares)"
            st.metric(label, f"{mean_energy:.4f} MJ/km")
        else:
            st.metric(t("energy"), "N/A")
        st.metric(t("selected_pairs"), f"{len(selected_pairs)}")


def calculate_and_store_final_results(t, selected_pairs):
    """Calcula e armazena os resultados finais."""
    norms = [normalize_pair(p) for p in selected_pairs]

    f0_values     = [n["_f0"]     for n in norms if n["_f0"]     is not None]
    f2_values     = [n["_f2"]     for n in norms if n["_f2"]     is not None]
    energy_values = [n["_energy"] for n in norms if n["_energy"] is not None]

    if not f0_values or not f2_values:
        st.error("❌ Nenhum par com F0/F2 válido. Verifique os dados dos pares selecionados.")
        return

    mean_f0 = mean(f0_values)
    mean_f2 = mean(f2_values)
    mean_energy = mean(energy_values) if energy_values else None

    cv_f0 = (stdev(f0_values) / mean_f0 * 100) if len(f0_values) > 1 and mean_f0 != 0 else 0.0
    cv_f2 = (stdev(f2_values) / mean_f2 * 100) if len(f2_values) > 1 and mean_f2 != 0 else 0.0

    st.session_state.final_results = {
        "mean_f0":    mean_f0,
        "mean_f2":    mean_f2,
        "mean_energy": mean_energy,
        "cv_f0":      cv_f0,
        "cv_f2":      cv_f2,
        "num_pairs":  len(selected_pairs),
        "total_mass": st.session_state.total_mass,
        "vehicle_info": st.session_state.vehicle_info,
    }

    st.session_state.pares_finais_selecionados = selected_pairs
