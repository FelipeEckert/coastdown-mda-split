# coding: utf-8
"""
Página 3: Análise de Pares

Permite ao usuário selecionar pares de runs (ida/volta), aplicar correções
climáticas e calcular coeficientes F0/F2.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statistics import mean, stdev
import os
import sys

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.calculations import (
    calcular_energia,
    calcular_f0_f2_split,
    calculate_single_pair_corrected_data,
    calculate_single_pair_corrected_data2
)
from core.corrections import apply_climate_correction


def render(t):
    """Renderiza a página de análise de pares."""
    
    st.header(t("page_pair_analysis"))
    
    # Verifica se os dados do veículo foram preenchidos
    if not st.session_state.vehicle_data_complete:
        st.warning(t("error_no_mass"))
        return
    
    # Inicializa subtab se não existir
    if "pair_analysis_subtab" not in st.session_state:
        st.session_state.pair_analysis_subtab = "calculos"
    
    # Renderiza baseado na sub-aba selecionada
    current_subtab = st.session_state.pair_analysis_subtab
    
    if current_subtab == "calculos":
        # ===== CÁLCULOS E CORREÇÕES =====
        st.subheader("🔢 Cálculos e Correções")
        
        # ===== SELEÇÃO DE PARES =====
        st.markdown("### 🔗 Seleção de Pares")
        
        if st.session_state.using_split_method:
            render_split_pair_selection(t)
        else:
            render_traditional_pair_selection(t)
        
        st.markdown("---")
        
        # ===== PARES CALCULADOS =====
        if st.session_state.calculated_pairs:
            render_calculated_pairs_table(t)
            
            # Botão para prosseguir
            if st.button(f"➡️ Ir para Comparativo Final", 
                         type="primary", use_container_width=True, key="goto_comparativo"):
                st.session_state.pairs_calculated = True
                st.session_state.current_page = "5_comparativo"
                st.rerun()
    
    elif current_subtab == "graficos":
        # ===== GRÁFICOS DE DESACELERAÇÃO =====
        st.subheader("📊 Gráficos de Desaceleração")
        
        if st.session_state.all_run_data:
            render_deceleration_graphs(t)
        else:
            st.info("💡 Carregue os dados do teste para visualizar os gráficos de desaceleração")
            
            if st.button("🔢 Ir para Cálculos", type="primary"):
                st.session_state.pair_analysis_subtab = "calculos"
                st.rerun()
    
    elif current_subtab == "simulacao":
        # ===== SIMULAÇÃO =====
        st.subheader("🎯 Simulação de Desempenho")
        
        if st.session_state.get("current_pair_results"):
            render_simulation(t)
        else:
            st.info("💡 Calcule um par na sub-página 'Cálculos' para realizar simulações")
            
            if st.button("🔢 Ir para Cálculos", type="primary"):
                st.session_state.pair_analysis_subtab = "calculos"
                st.rerun()


def render_traditional_pair_selection(t):
    """Renderiza seleção de pares para método tradicional."""
    
    # Separa runs por direção (heading)
    runs_ida = []
    runs_volta = []
    
    for run_id, run_info in st.session_state.all_run_data.items():
        heading = run_info.get("heading", "")
        if heading in ["+", "N", "Norte", "North", "ida", "Ida", "IDA"]:
            runs_ida.append(run_id)
        elif heading in ["-", "S", "Sul", "South", "volta", "Volta", "VOLTA"]:
            runs_volta.append(run_id)
    
    # Se não conseguiu separar por heading, divide pela metade
    if not runs_ida or not runs_volta:
        all_runs = list(st.session_state.all_run_data.keys())
        mid = len(all_runs) // 2
        runs_ida = all_runs[:mid]
        runs_volta = all_runs[mid:]
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_ida = st.selectbox(
            t("select_outbound_run"),
            options=runs_ida,
            key="selected_ida"
        )
    
    with col2:
        selected_volta = st.selectbox(
            t("select_return_run"),
            options=runs_volta,
            key="selected_volta"
        )
    
    st.markdown("---")
    
    # ===== CONDIÇÕES AMBIENTAIS =====
    st.subheader(f"🌡️ Correção Climática")
    
    st.info("💡 **Importante:** A correção climática é aplicada INDIVIDUALMENTE em cada passada (ida e volta) usando as condições meteorológicas específicas de cada uma.")
    
    # Opções de fonte de dados meteorológicos
    correction_mode = st.radio(
        "Fonte dos Dados Meteorológicos:",
        ["Sem Correção", "Manual (por passada)", "Arquivo Meteorológico"],
        horizontal=True
    )
    
    temp_ida = temp_volta = press_ida = press_volta = None
    wind_ida = wind_volta = None
    
    if correction_mode == "Manual (por passada)":
        st.markdown("#### 📊 Dados por Passada")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🔼 Passada IDA (+)**")
            temp_ida = st.number_input(
                "Temperatura Ida (°C)",
                min_value=-20.0,
                max_value=50.0,
                value=25.0,
                step=0.5,
                format="%.1f",
                key="temp_ida"
            )
            press_ida = st.number_input(
                "Pressão Ida (kPa)",
                min_value=80.0,
                max_value=110.0,
                value=101.325,
                step=0.1,
                format="%.3f",
                key="press_ida"
            )
            wind_ida = st.number_input(
                "Vento Ida (m/s)",
                min_value=0.0,
                max_value=20.0,
                value=0.0,
                step=0.1,
                format="%.2f",
                key="wind_ida_manual"
            )
        
        with col2:
            st.markdown("**🔽 Passada VOLTA (-)**")
            temp_volta = st.number_input(
                "Temperatura Volta (°C)",
                min_value=-20.0,
                max_value=50.0,
                value=25.0,
                step=0.5,
                format="%.1f",
                key="temp_volta"
            )
            press_volta = st.number_input(
                "Pressão Volta (kPa)",
                min_value=80.0,
                max_value=110.0,
                value=101.325,
                step=0.1,
                format="%.3f",
                key="press_volta"
            )
            wind_volta = st.number_input(
                "Vento Volta (m/s)",
                min_value=0.0,
                max_value=20.0,
                value=0.0,
                step=0.1,
                format="%.2f",
                key="wind_volta_manual"
            )
    
    elif correction_mode == "Arquivo Meteorológico":
        if st.session_state.weather_data:
            st.success(f"✅ Arquivo meteorológico carregado com {len(st.session_state.weather_data)} registros")
            st.info("Os dados de T/P serão buscados automaticamente com base no timestamp de cada run")
        else:
            st.warning("⚠️ Nenhum arquivo meteorológico foi carregado. Volte para a Página 1 para carregar.")
            correction_mode = "Sem Correção"
    
    st.markdown("---")
    
    # ===== BOTÃO CALCULAR PAR =====
    if st.button(f"🔢 Calcular Par", type="primary", use_container_width=True):
        with st.spinner("Calculando par..."):
            try:
                # Obtém dados dos runs selecionados
                run_ida_info = st.session_state.all_run_data.get(selected_ida)
                run_volta_info = st.session_state.all_run_data.get(selected_volta)
                
                if not run_ida_info or not run_volta_info:
                    st.error("Erro: Runs selecionadas não encontradas!")
                    st.stop()
                
                # Obtém coeficientes individuais NÃO CORRIGIDOS
                coeffs_ida = st.session_state.individual_coeffs.get(selected_ida, {})
                coeffs_volta = st.session_state.individual_coeffs.get(selected_volta, {})
                
                f0_ida_raw = coeffs_ida.get("f0", 0)
                f2_ida_raw = coeffs_ida.get("f2", 0)
                f0_volta_raw = coeffs_volta.get("f0", 0)
                f2_volta_raw = coeffs_volta.get("f2", 0)
                
                # Calcula médias e CVs NÃO CORRIGIDOS
                from statistics import mean, stdev
                f0_mean = mean([f0_ida_raw, f0_volta_raw])
                f2_mean = mean([f2_ida_raw, f2_volta_raw])
                cv_f0 = (stdev([f0_ida_raw, f0_volta_raw]) / f0_mean) * 100 if f0_mean != 0 else 0
                cv_f2 = (stdev([f2_ida_raw, f2_volta_raw]) / f2_mean) * 100 if f2_mean != 0 else 0
                
                # Variáveis para valores corrigidos
                f0_ida_corr = f0_volta_corr = None
                f2_ida_corr = f2_volta_corr = None
                f0corr_mean = f2corr_mean = "N/A"
                cv_f0_corr = cv_f2_corr = "N/A"
                energy = "N/A"
                corrected = False
                
                temp_ida_used = temp_volta_used = "N/A"
                press_ida_used = press_volta_used = "N/A"
                wind_ida_ms = wind_volta_ms = wind_avg_ms = None
                
                # Aplica correção climática se necessário
                if correction_mode == "Manual (por passada)":
                    if temp_ida and press_ida and temp_volta and press_volta:
                        # Aplica correção POR PASSADA
                        f0_ida_corr, f2_ida_corr = apply_climate_correction(
                            f0_ida_raw, f2_ida_raw, temp_ida, press_ida
                        )
                        f0_volta_corr, f2_volta_corr = apply_climate_correction(
                            f0_volta_raw, f2_volta_raw, temp_volta, press_volta
                        )
                        
                        # Calcula médias e CVs CORRIGIDOS
                        f0corr_mean = mean([f0_ida_corr, f0_volta_corr])
                        f2corr_mean = mean([f2_ida_corr, f2_volta_corr])
                        cv_f0_corr = (stdev([f0_ida_corr, f0_volta_corr]) / f0corr_mean) * 100 if f0corr_mean != 0 else 0
                        cv_f2_corr = (stdev([f2_ida_corr, f2_volta_corr]) / f2corr_mean) * 100 if f2corr_mean != 0 else 0
                        
                        energy = calcular_energia(f0corr_mean, f2corr_mean)
                        corrected = True
                        
                        temp_ida_used = temp_ida
                        press_ida_used = press_ida
                        temp_volta_used = temp_volta
                        press_volta_used = press_volta
                        
                        # Vento manual
                        wind_ida_ms = wind_ida if wind_ida is not None and wind_ida > 0 else None
                        wind_volta_ms = wind_volta if wind_volta is not None and wind_volta > 0 else None
                        wind_vals = [w for w in [wind_ida_ms, wind_volta_ms] if w is not None]
                        wind_avg_ms = mean(wind_vals) if wind_vals else None
                        
                        # Aviso se vento > 3 m/s
                        if wind_avg_ms and wind_avg_ms > 3.0:
                            st.warning(f"⚠️ Vento médio ({wind_avg_ms:.2f} m/s) acima do recomendado pela norma (3.0 m/s)!")
                    else:
                        st.warning("⚠️ Preencha T/P para IDA e VOLTA para aplicar correção!")
                
                elif correction_mode == "Arquivo Meteorológico":
                    # Busca dados meteo mais próximos do timestamp de cada run
                    if st.session_state.weather_data:
                        from datetime import datetime
                        
                        # Pega timestamps das runs
                        ts_ida = run_ida_info.get("start_timestamp")
                        ts_volta = run_volta_info.get("start_timestamp")
                        
                        if ts_ida and ts_volta:
                            # Busca registro meteo mais próximo para cada run
                            def find_closest_weather(target_time, weather_data):
                                if not target_time or not weather_data:
                                    return None
                                closest = min(
                                    weather_data,
                                    key=lambda x: abs((x['timestamp'] - target_time).total_seconds())
                                )
                                return closest
                            
                            weather_ida = find_closest_weather(ts_ida, st.session_state.weather_data)
                            weather_volta = find_closest_weather(ts_volta, st.session_state.weather_data)
                            
                            if weather_ida and weather_volta:
                                temp_ida_used = weather_ida.get('temp_c')
                                press_ida_used = weather_ida.get('baro_kpa')
                                wind_ida_ms = weather_ida.get('wind_ms')
                                
                                temp_volta_used = weather_volta.get('temp_c')
                                press_volta_used = weather_volta.get('baro_kpa')
                                wind_volta_ms = weather_volta.get('wind_ms')
                                
                                # Aplica correção POR PASSADA
                                f0_ida_corr, f2_ida_corr = apply_climate_correction(
                                    f0_ida_raw, f2_ida_raw, temp_ida_used, press_ida_used
                                )
                                f0_volta_corr, f2_volta_corr = apply_climate_correction(
                                    f0_volta_raw, f2_volta_raw, temp_volta_used, press_volta_used
                                )
                                
                                # Calcula médias e CVs CORRIGIDOS
                                f0corr_mean = mean([f0_ida_corr, f0_volta_corr])
                                f2corr_mean = mean([f2_ida_corr, f2_volta_corr])
                                cv_f0_corr = (stdev([f0_ida_corr, f0_volta_corr]) / f0corr_mean) * 100 if f0corr_mean != 0 else 0
                                cv_f2_corr = (stdev([f2_ida_corr, f2_volta_corr]) / f2corr_mean) * 100 if f2corr_mean != 0 else 0
                                
                                energy = calcular_energia(f0corr_mean, f2corr_mean)
                                corrected = True
                                
                                # Calcula vento médio
                                wind_vals = [w for w in [wind_ida_ms, wind_volta_ms] if w is not None]
                                wind_avg_ms = mean(wind_vals) if wind_vals else None
                                
                                # Aviso se vento > 3 m/s
                                if wind_avg_ms and wind_avg_ms > 3.0:
                                    st.warning(f"⚠️ Vento médio ({wind_avg_ms:.2f} m/s) acima do recomendado pela norma (3.0 m/s)!")
                            else:
                                st.warning("⚠️ Não foi possível encontrar dados meteorológicos para as runs selecionadas!")
                        else:
                            st.warning("⚠️ Runs não possuem timestamp para buscar dados meteorológicos!")
                
                # Monta current_pair_results (estrutura COMPLETA como no PyQt5)
                st.session_state.current_pair_results = {
                    "run_ida": selected_ida,
                    "run_volta": selected_volta,
                    
                    # Médias NÃO corrigidas
                    "f0_mean": f0_mean,
                    "f2_mean": f2_mean,
                    
                    # Médias CORRIGIDAS
                    "f0corr_mean": f0corr_mean,
                    "f2corr_mean": f2corr_mean,
                    
                    # Condições médias
                    "temp": (temp_ida_used + temp_volta_used) / 2 if corrected and temp_ida_used != "N/A" else "N/A",
                    "press": (press_ida_used + press_volta_used) / 2 if corrected and press_ida_used != "N/A" else "N/A",
                    
                    # Condições por passada
                    "temp_ida_used": temp_ida_used,
                    "press_ida_used": press_ida_used,
                    "temp_volta_used": temp_volta_used,
                    "press_volta_used": press_volta_used,
                    
                    # Coeficientes por passada (corrigidos se houver correção, senão brutos)
                    "f0_ida": f0_ida_corr if corrected else f0_ida_raw,
                    "f2_ida": f2_ida_corr if corrected else f2_ida_raw,
                    "f0_volta": f0_volta_corr if corrected else f0_volta_raw,
                    "f2_volta": f2_volta_corr if corrected else f2_volta_raw,
                    
                    # Coeficientes BRUTOS por passada
                    "f0_ida_raw": f0_ida_raw,
                    "f2_ida_raw": f2_ida_raw,
                    "f0_volta_raw": f0_volta_raw,
                    "f2_volta_raw": f2_volta_raw,
                    
                    # Coeficientes CORRIGIDOS por passada
                    "f0_ida_corr": f0_ida_corr,
                    "f2_ida_corr": f2_ida_corr,
                    "f0_volta_corr": f0_volta_corr,
                    "f2_volta_corr": f2_volta_corr,
                    
                    # CVs
                    "cv_f0": cv_f0,
                    "cv_f2": cv_f2,
                    "cv_f0_corr": cv_f0_corr,
                    "cv_f2_corr": cv_f2_corr,
                    
                    # Energia
                    "energy": energy,
                    
                    # Flags
                    "corrected": corrected,
                    
                    # Vento
                    "wind_ida_ms": wind_ida_ms,
                    "wind_volta_ms": wind_volta_ms,
                    "wind_avg_ms": wind_avg_ms,
                }
                
                st.success(f"✅ Par {selected_ida}/{selected_volta} calculado com sucesso!")
                
                # Mostra resultados
                st.markdown("---")
                st.subheader(f"📊 Resultados do Par")
                
                # Tabela de coeficientes NÃO CORRIGIDOS - com HTML para melhor visualização
                st.markdown("#### Coeficientes NÃO Corrigidos")
                
                # Cria HTML customizado para merge de células dos CVs
                html_uncorr = f"""
                <style>
                    .results-table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin: 10px 0;
                    }}
                    .results-table th, .results-table td {{
                        border: 1px solid #444;
                        padding: 12px 8px;
                        text-align: center;
                    }}
                    .results-table th {{
                        background-color: #1f1f1f;
                        font-weight: bold;
                    }}
                    .results-table tr:nth-child(even) {{
                        background-color: #2a2a2a;
                    }}
                    .cv-cell {{
                        vertical-align: middle;
                        font-weight: bold;
                        background-color: #1a1a1a;
                    }}
                    .warning-cv {{
                        background-color: #ff6b6b;
                        color: #000;
                    }}
                </style>
                <table class="results-table">
                    <thead>
                        <tr>
                            <th>Run</th>
                            <th>f'0 (N)</th>
                            <th>f'2 (N/(m/s)²)</th>
                            <th>CV f'0 (%)</th>
                            <th>CV f'2 (%)</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>{selected_ida} ↑ [+]</td>
                            <td>{f0_ida_raw:.4f}</td>
                            <td>{f2_ida_raw:.6f}</td>
                            <td rowspan="3" class="cv-cell {'warning-cv' if cv_f0 > 10 else ''}">{cv_f0:.2f}</td>
                            <td rowspan="3" class="cv-cell {'warning-cv' if cv_f2 > 10 else ''}">{cv_f2:.2f}</td>
                        </tr>
                        <tr>
                            <td>{selected_volta} ↓ [-]</td>
                            <td>{f0_volta_raw:.4f}</td>
                            <td>{f2_volta_raw:.6f}</td>
                        </tr>
                        <tr>
                            <td><strong>Média</strong></td>
                            <td><strong>{f0_mean:.4f}</strong></td>
                            <td><strong>{f2_mean:.6f}</strong></td>
                        </tr>
                    </tbody>
                </table>
                """
                st.markdown(html_uncorr, unsafe_allow_html=True)
                
                # Tabela de coeficientes CORRIGIDOS (se houver)
                if corrected:
                    st.markdown("#### Coeficientes CORRIGIDOS")
                    
                    html_corr = f"""
                    <table class="results-table">
                        <thead>
                            <tr>
                                <th>Run</th>
                                <th>T (°C)</th>
                                <th>P (kPa)</th>
                                <th>f'0 Corr. (N)</th>
                                <th>f'2 Corr. (N/(km/h)²)</th>
                                <th>CV f'0 (%)</th>
                                <th>CV f'2 (%)</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>{selected_ida} ↑ [+]</td>
                                <td>{temp_ida_used:.1f}</td>
                                <td>{press_ida_used:.2f}</td>
                                <td>{f0_ida_corr:.4f}</td>
                                <td>{f2_ida_corr:.6f}</td>
                                <td rowspan="3" class="cv-cell {'warning-cv' if cv_f0_corr > 10 else ''}">{cv_f0_corr:.2f}</td>
                                <td rowspan="3" class="cv-cell {'warning-cv' if cv_f2_corr > 10 else ''}">{cv_f2_corr:.2f}</td>
                            </tr>
                            <tr>
                                <td>{selected_volta} ↓ [-]</td>
                                <td>{temp_volta_used:.1f}</td>
                                <td>{press_volta_used:.2f}</td>
                                <td>{f0_volta_corr:.4f}</td>
                                <td>{f2_volta_corr:.6f}</td>
                            </tr>
                            <tr>
                                <td><strong>Média</strong></td>
                                <td><strong>{(temp_ida_used + temp_volta_used)/2:.1f}</strong></td>
                                <td><strong>{(press_ida_used + press_volta_used)/2:.2f}</strong></td>
                                <td><strong>{f0corr_mean:.4f}</strong></td>
                                <td><strong>{f2corr_mean:.6f}</strong></td>
                            </tr>
                        </tbody>
                    </table>
                    """
                    st.markdown(html_corr, unsafe_allow_html=True)
                    
                    st.markdown("---")
                    st.metric("⚡ Energia", f"{energy:.2f} MJ/km")
                    
                    # Avisos de CV alto
                    if cv_f0_corr > 10.0:
                        st.warning(f"⚠️ CV de f'0 ({cv_f0_corr:.2f}%) está acima de 10%!")
                    if cv_f2_corr > 10.0:
                        st.warning(f"⚠️ CV de f'2 ({cv_f2_corr:.2f}%) está acima de 10%!")
                
                # Botão para adicionar ao comparativo - SEMPRE VISÍVEL após cálculo
                st.markdown("---")
                
            except Exception as e:
                st.error(f"Erro ao calcular par: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    # Botão "Adicionar ao Comparativo" - FORA do try/except e do spinner
    # Só aparece se current_pair_results existe
    if st.session_state.get("current_pair_results"):
        if st.button("➕ Adicionar ao Comparativo", type="primary", use_container_width=True, key="add_to_comp"):
            try:
                pair_data = st.session_state.current_pair_results
                selected_ida = pair_data["run_ida"]
                selected_volta = pair_data["run_volta"]
                pair_id = f"{selected_ida}/{selected_volta}"
                
                # Adiciona ao calculated_pairs
                st.session_state.calculated_pairs[pair_id] = {
                    **pair_data,
                    "pair_id": pair_id,
                    "run1": selected_ida,
                    "run2": selected_volta,
                    "f0_corr": pair_data["f0corr_mean"],
                    "f2_corr": pair_data["f2corr_mean"],
                    "selected": False,
                }
                
                st.session_state.pairs_calculated = True
                st.success(f"✅ Par {pair_id} adicionado ao comparativo!")
                
                # Limpa current_pair_results para permitir novo cálculo
                st.session_state.current_pair_results = None
                
                # Pequeno delay para usuário ver a mensagem
                import time
                time.sleep(1)
                st.rerun()
                
            except Exception as e:
                st.error(f"Erro ao adicionar par: {str(e)}")
                import traceback
                st.code(traceback.format_exc())


def render_split_pair_selection(t):
    """Renderiza seleção de pares para método split."""
    
    st.info("🔀 Método Split: Selecione runs de alta e baixa velocidade")
    
    # Runs de alta velocidade
    runs_alta = list(st.session_state.all_run_data_alta.keys()) if st.session_state.all_run_data_alta else []
    runs_baixa = list(st.session_state.all_run_data_baixa.keys()) if st.session_state.all_run_data_baixa else []
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Alta Velocidade**")
        selected_alta_ida = st.selectbox(
            f"{t('select_outbound_run')} (Alta)",
            options=runs_alta[:len(runs_alta)//2] if runs_alta else [],
            key="selected_alta_ida"
        )
        selected_alta_volta = st.selectbox(
            f"{t('select_return_run')} (Alta)",
            options=runs_alta[len(runs_alta)//2:] if runs_alta else [],
            key="selected_alta_volta"
        )
    
    with col2:
        st.markdown("**Baixa Velocidade**")
        selected_baixa_ida = st.selectbox(
            f"{t('select_outbound_run')} (Baixa)",
            options=runs_baixa[:len(runs_baixa)//2] if runs_baixa else [],
            key="selected_baixa_ida"
        )
        selected_baixa_volta = st.selectbox(
            f"{t('select_return_run')} (Baixa)",
            options=runs_baixa[len(runs_baixa)//2:] if runs_baixa else [],
            key="selected_baixa_volta"
        )
    
    st.markdown("---")
    
    # ===== CONDIÇÕES AMBIENTAIS =====
    st.subheader(f"🌡️ {t('environmental_conditions')}")
    
    apply_correction = st.checkbox(t("apply_climate_correction"), value=True, key="split_correction")
    
    if apply_correction:
        col1, col2 = st.columns(2)
        
        with col1:
            temperature = st.number_input(
                t("temperature"),
                min_value=-20.0,
                max_value=50.0,
                value=25.0,
                step=0.5,
                format="%.1f",
                key="split_temp"
            )
        
        with col2:
            pressure = st.number_input(
                t("pressure"),
                min_value=80.0,
                max_value=110.0,
                value=101.325,
                step=0.1,
                format="%.3f",
                key="split_pressure"
            )
    else:
        temperature = 25.0
        pressure = 101.325
    
    st.markdown("---")
    
    # ===== BOTÃO CALCULAR PAR SPLIT =====
    if st.button(f"🔢 {t('calculate_pair')} (Split)", type="primary", use_container_width=True):
        with st.spinner("Calculando par split..."):
            try:
                # Obtém dados dos runs selecionados
                times_alta_ida, vels_alta_ida, _ = st.session_state.all_run_data_alta.get(selected_alta_ida, ([], [], ""))
                times_alta_volta, vels_alta_volta, _ = st.session_state.all_run_data_alta.get(selected_alta_volta, ([], [], ""))
                times_baixa_ida, vels_baixa_ida, _ = st.session_state.all_run_data_baixa.get(selected_baixa_ida, ([], [], ""))
                times_baixa_volta, vels_baixa_volta, _ = st.session_state.all_run_data_baixa.get(selected_baixa_volta, ([], [], ""))
                
                # Calcula F0/F2 usando método split
                f0, f2 = calcular_f0_f2_split(
                    times_alta_ida, vels_alta_ida,
                    times_alta_volta, vels_alta_volta,
                    times_baixa_ida, vels_baixa_ida,
                    times_baixa_volta, vels_baixa_volta,
                    st.session_state.total_mass,
                    st.session_state.ref_vel_alta,
                    st.session_state.ref_vel_baixa
                )
                
                # Aplica correção climática se solicitado
                if apply_correction:
                    f0_corrigido, f2_corrigido = apply_climate_correction(
                        f0, f2, temperature, pressure
                    )
                else:
                    f0_corrigido = f0
                    f2_corrigido = f2
                
                # Calcula energia
                energia = calcular_energia(f0_corrigido, f2_corrigido, 
                                          st.session_state.total_mass)
                
                # Cria ID do par
                pair_id = f"split_{selected_alta_ida}_{selected_baixa_ida}"
                
                # Armazena o par calculado
                pair_data = {
                    "pair_id": pair_id,
                    "run_alta_ida": selected_alta_ida,
                    "run_alta_volta": selected_alta_volta,
                    "run_baixa_ida": selected_baixa_ida,
                    "run_baixa_volta": selected_baixa_volta,
                    "f0_par": f0,
                    "f2_par": f2,
                    "f0_corrigido": f0_corrigido,
                    "f2_corrigido": f2_corrigido,
                    "energia": energia,
                    "temperature": temperature,
                    "pressure": pressure,
                    "apply_correction": apply_correction,
                    "method": "split",
                    "selected": False
                }
                
                st.session_state.calculated_pairs[pair_id] = pair_data
                st.session_state.pairs_calculated = True
                
                st.success(f"✅ Par Split {pair_id} calculado com sucesso!")
                
                # Mostra resultados
                st.markdown("---")
                st.subheader(f"📈 {t('pair_results')}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(t("f0_coefficient"), f"{f0_corrigido:.4f} N")
                with col2:
                    st.metric(t("f2_coefficient"), f"{f2_corrigido:.6f} N/(km/h)²")
                with col3:
                    st.metric(t("energy"), f"{energia:.2f} J")
                
                st.rerun()
                
            except Exception as e:
                st.error(f"{t('error_calculation')}: {str(e)}")
                import traceback
                st.code(traceback.format_exc())


def render_calculated_pairs_table(t):
    """Renderiza cards com prévia dos pares calculados."""
    
    if not st.session_state.calculated_pairs:
        st.info("Nenhum par adicionado ao comparativo ainda")
        return
    
    st.markdown("### 📊 Pares Adicionados ao Comparativo")
    
    # Para cada par, cria um card compacto com prévia
    for pair_id, pair in st.session_state.calculated_pairs.items():
        # Extrai dados
        temp_ida = pair.get("temp_ida_used", "N/A")
        temp_volta = pair.get("temp_volta_used", "N/A")
        press_ida = pair.get("press_ida_used", "N/A")
        press_volta = pair.get("press_volta_used", "N/A")
        wind_ida = pair.get("wind_ida_ms")
        wind_volta = pair.get("wind_volta_ms")
        
        # Formata T/P
        temp_str = f"{temp_ida:.1f}/{temp_volta:.1f}" if isinstance(temp_ida, (int, float)) else f"{temp_ida}/{temp_volta}"
        press_str = f"{press_ida:.2f}/{press_volta:.2f}" if isinstance(press_ida, (int, float)) else f"{press_ida}/{press_volta}"
        
        # Formata Vento
        if wind_ida is not None and wind_volta is not None:
            wind_str = f"{wind_ida:.2f}/{wind_volta:.2f}"
        elif wind_ida is not None:
            wind_str = f"{wind_ida:.2f}/N/A"
        elif wind_volta is not None:
            wind_str = f"N/A/{wind_volta:.2f}"
        else:
            wind_str = "N/A"
        
        # Coeficientes
        f0_corr = pair.get("f0_corr", pair.get("f0corr_mean", 0))
        f2_corr = pair.get("f2_corr", pair.get("f2corr_mean", 0))
        cv_f0 = pair.get("cv_f0_corr", pair.get("cv_f0", 0))
        cv_f2 = pair.get("cv_f2_corr", pair.get("cv_f2", 0))
        energy = pair.get("energy", 0)
        
        # Card compacto
        with st.expander(f"**Par {pair_id}**", expanded=False):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown("**🌡️ Condições Ambientais**")
                st.write(f"Temp: {temp_str} °C")
                st.write(f"Press: {press_str} kPa")
                st.write(f"Vento: {wind_str} m/s")
            
            with col2:
                st.markdown("**📊 Coeficientes Corrigidos**")
                st.write(f"f'0: {f0_corr:.4f} N")
                st.write(f"f'2: {f2_corr:.6f}")
            
            with col3:
                st.markdown("**📈 Variações**")
                cv_f0_str = f"{cv_f0:.2f}%" if isinstance(cv_f0, (int, float)) else str(cv_f0)
                cv_f2_str = f"{cv_f2:.2f}%" if isinstance(cv_f2, (int, float)) else str(cv_f2)
                
                if isinstance(cv_f0, (int, float)) and cv_f0 > 10:
                    st.write(f"CV f'0: :red[{cv_f0_str}] ⚠️")
                else:
                    st.write(f"CV f'0: {cv_f0_str}")
                
                if isinstance(cv_f2, (int, float)) and cv_f2 > 10:
                    st.write(f"CV f'2: :red[{cv_f2_str}] ⚠️")
                else:
                    st.write(f"CV f'2: {cv_f2_str}")
            
            with col4:
                st.markdown("**⚡ Energia**")
                energy_str = f"{energy:.2f}" if isinstance(energy, (int, float)) else str(energy)
                # Aumenta a fonte do valor
                st.markdown(f"<h2 style='margin: 0; padding: 0;'>{energy_str}</h2>", unsafe_allow_html=True)
                st.markdown("<p style='margin: 0; color: #888;'>MJ/km</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.info("💡 Vá para **Comparativo Final** para selecionar e comparar os pares")


def render_deceleration_graphs(t):
    """Renderiza gráficos de desaceleração."""
    
    pair_data = st.session_state.get("current_pair_results", {})
    
    run_ida = pair_data.get("run_ida") if pair_data else None
    run_volta = pair_data.get("run_volta") if pair_data else None
    
    # Obtém dados das runs
    all_data = st.session_state.all_run_data
    if not all_data:
        st.warning("Dados das runs não disponíveis.")
        return
    
    # ===== SELEÇÃO DE RUNS PARA PLOTAR =====
    st.markdown("#### 🎯 Selecione as runs para visualizar")
    
    available_runs = sorted(all_data.keys())
    run_labels = [f"Run {r} ({all_data[r].get('heading', 'N/A')})" for r in available_runs]
    
    # Por padrão, seleciona as runs do par atual (se existir) ou as primeiras 4
    default_indices = []
    if run_ida is not None or run_volta is not None:
        for i, r in enumerate(available_runs):
            if r == run_ida or r == run_volta:
                default_indices.append(i)
    
    if not default_indices:
        default_indices = list(range(min(4, len(available_runs))))
    
    selected_labels = st.multiselect(
        "Runs para plotar:",
        options=run_labels,
        default=[run_labels[i] for i in default_indices],
        key="graph_runs_select"
    )
    
    # Extrai IDs das runs selecionadas
    import re
    selected_run_ids = []
    for label in selected_labels:
        match = re.search(r"Run (\d+)", label)
        if match:
            selected_run_ids.append(int(match.group(1)))
    
    if not selected_run_ids:
        st.info("Selecione pelo menos uma run para visualizar o gráfico.")
        return
    
    # ===== GRÁFICO 1: Velocidade x Tempo =====
    st.markdown("#### 📈 Velocidade x Tempo")
    
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    fig1.patch.set_facecolor('#0E1117')
    ax1.set_facecolor('#1a1a2e')
    
    colors = plt.cm.tab10.colors
    
    for idx, run_id in enumerate(selected_run_ids):
        if run_id in all_data:
            data = all_data[run_id]
            times = data["times"]
            velocities = data["velocities"]
            heading = data.get("heading", "N/A")
            color = colors[idx % len(colors)]
            
            # Destaca as runs do par atual
            linewidth = 2.5 if run_id in (run_ida, run_volta) else 1.5
            marker = 'o' if run_id in (run_ida, run_volta) else '.'
            markersize = 6 if run_id in (run_ida, run_volta) else 3
            
            label = f"Run {run_id} ({heading})"
            if run_id == run_ida:
                label += " ★ IDA"
            elif run_id == run_volta:
                label += " ★ VOLTA"
            
            ax1.plot(times, velocities, marker=marker, markersize=markersize,
                    linestyle='-', linewidth=linewidth, color=color, label=label)
    
    ax1.set_xlabel("Tempo (s)", fontsize=12, color='white')
    ax1.set_ylabel("Velocidade (km/h)", fontsize=12, color='white')
    ax1.set_title("Curvas de Desaceleração (Coastdown)", fontsize=14, fontweight='bold', color='white')
    ax1.grid(True, linestyle='--', alpha=0.3, color='gray')
    ax1.tick_params(colors='white')
    ax1.legend(fontsize=9, facecolor='#1a1a2e', edgecolor='gray', labelcolor='white')
    
    for spine in ax1.spines.values():
        spine.set_color('gray')
    
    fig1.tight_layout()
    st.pyplot(fig1)
    plt.close(fig1)
    
    # ===== GRÁFICO 2: Força de Arrasto x Velocidade =====
    if not pair_data:
        st.info("💡 Calcule um par na sub-página 'Cálculos' para visualizar os gráficos de Força de Arrasto e Desaceleração.")
        return
    
    st.markdown("#### 📉 Força de Arrasto (F) x Velocidade")
    
    # Usa coeficientes do par atual para plotar F = f0 + f2*V²
    f0_corr = pair_data.get("f0corr_mean", pair_data.get("f0_corr", pair_data.get("f0_mean", 0)))
    f2_corr = pair_data.get("f2corr_mean", pair_data.get("f2_corr", pair_data.get("f2_mean", 0)))
    
    if isinstance(f0_corr, (int, float)) and isinstance(f2_corr, (int, float)):
        v_range_kmh = np.linspace(0, 120, 200)
        v_range_ms = v_range_kmh / 3.6
        F_drag = f0_corr + f2_corr * (v_range_ms ** 2)
        
        fig2, ax2 = plt.subplots(figsize=(12, 5))
        fig2.patch.set_facecolor('#0E1117')
        ax2.set_facecolor('#1a1a2e')
        
        ax2.plot(v_range_kmh, F_drag, color='#00ff88', linewidth=2.5, label=f"F = {f0_corr:.4f} + {f2_corr:.6f} · V²")
        ax2.fill_between(v_range_kmh, 0, F_drag, alpha=0.15, color='#00ff88')
        
        ax2.set_xlabel("Velocidade (km/h)", fontsize=12, color='white')
        ax2.set_ylabel("Força de Arrasto (N)", fontsize=12, color='white')
        ax2.set_title("Força de Arrasto vs Velocidade", fontsize=14, fontweight='bold', color='white')
        ax2.grid(True, linestyle='--', alpha=0.3, color='gray')
        ax2.tick_params(colors='white')
        ax2.legend(fontsize=11, facecolor='#1a1a2e', edgecolor='gray', labelcolor='white')
        
        for spine in ax2.spines.values():
            spine.set_color('gray')
        
        fig2.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)
    else:
        st.info("Coeficientes corrigidos não disponíveis para plotar a curva de arrasto.")
    
    # ===== GRÁFICO 3: Desaceleração x Velocidade =====
    st.markdown("#### 📉 Desaceleração x Velocidade")
    
    total_mass = st.session_state.total_mass
    if isinstance(f0_corr, (int, float)) and isinstance(f2_corr, (int, float)) and total_mass > 0:
        v_range_kmh = np.linspace(5, 120, 200)
        v_range_ms = v_range_kmh / 3.6
        # a = F/m = (f0 + f2*V²) / m
        decel = (f0_corr + f2_corr * (v_range_ms ** 2)) / total_mass
        
        fig3, ax3 = plt.subplots(figsize=(12, 5))
        fig3.patch.set_facecolor('#0E1117')
        ax3.set_facecolor('#1a1a2e')
        
        ax3.plot(v_range_kmh, decel, color='#ff6b6b', linewidth=2.5, label=f"a = F(V) / {total_mass:.1f} kg")
        ax3.fill_between(v_range_kmh, 0, decel, alpha=0.15, color='#ff6b6b')
        
        ax3.set_xlabel("Velocidade (km/h)", fontsize=12, color='white')
        ax3.set_ylabel("Desaceleração (m/s²)", fontsize=12, color='white')
        ax3.set_title("Desaceleração vs Velocidade", fontsize=14, fontweight='bold', color='white')
        ax3.grid(True, linestyle='--', alpha=0.3, color='gray')
        ax3.tick_params(colors='white')
        ax3.legend(fontsize=11, facecolor='#1a1a2e', edgecolor='gray', labelcolor='white')
        
        for spine in ax3.spines.values():
            spine.set_color('gray')
        
        fig3.tight_layout()
        st.pyplot(fig3)
        plt.close(fig3)
    else:
        st.info("Massa do veículo ou coeficientes não disponíveis para plotar a desaceleração.")


def render_simulation(t):
    """Renderiza simulação de desempenho."""
    
    pair_data = st.session_state.current_pair_results
    
    if not pair_data:
        return
    
    st.info("🚧 Feature em desenvolvimento: Simulação de desempenho do veículo")
    
    st.write("**Simulações planejadas:**")
    st.write("- Cálculo de autonomia baseado nos coeficientes")
    st.write("- Previsão de consumo em diferentes velocidades")
    st.write("- Comparação de cenários (velocidade constante vs ciclo urbano)")
    
    # Placeholder - pode implementar depois com calma
    col1, col2 = st.columns(2)
    with col1:
        st.number_input("Velocidade de cruzeiro (km/h)", min_value=30.0, max_value=120.0, value=80.0)
    with col2:
        st.number_input("Distância simulada (km)", min_value=1.0, max_value=1000.0, value=100.0)
    
    if st.button("🎯 Simular", type="primary"):
        st.warning("Funcionalidade em desenvolvimento!")
