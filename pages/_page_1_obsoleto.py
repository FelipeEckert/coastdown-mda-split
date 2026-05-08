# OBSOLETO - mantido para referência histórica
# Este arquivo não é mais utilizado pelo app.py (substituído pelo @st.dialog new_test_dialog).
# coding: utf-8
"""
[OBSOLETO] Página 1: Abrir Teste

Permite ao usuário selecionar o método de teste e carregar os arquivos CSV.
"""

import streamlit as st
import pandas as pd
import io
import os
import sys
import tempfile

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.loaders import carregar_dados_csv_robusto, read_weather_station_csv


def render(t):
    """Renderiza a página de abertura de teste."""

    st.header(t("page_open_test"))

    # ===== SELEÇÃO DO MÉTODO DE TESTE =====
    st.subheader(t("select_test_method"))

    col1, col2 = st.columns(2)

    with col1:
        traditional_selected = st.button(
            f"📊 {t('traditional_method')}",
            use_container_width=True,
            type="primary" if st.session_state.test_method == "traditional" else "secondary"
        )
        if traditional_selected:
            st.session_state.test_method = "traditional"
            st.session_state.using_split_method = False
            st.rerun()

    with col2:
        split_selected = st.button(
            f"📈 {t('split_method')}",
            use_container_width=True,
            type="primary" if st.session_state.test_method == "split" else "secondary"
        )
        if split_selected:
            st.session_state.test_method = "split"
            st.session_state.using_split_method = True
            st.rerun()

    st.markdown("---")

    # ===== UPLOAD DE ARQUIVOS =====
    if st.session_state.test_method == "traditional":
        render_traditional_upload(t)
    else:
        render_split_upload(t)

    st.markdown("---")

    # ===== BOTÃO PARA PROSSEGUIR =====
    if st.session_state.data_loaded:
        st.success(t("file_loaded_success"))

        # Mostra informações do arquivo carregado
        if st.session_state.all_run_data:
            st.info(f"🔢 {len(st.session_state.all_run_data)} {t('runs_detected')}")

            # Mostra tabela com os runs detectados
            with st.expander(f"📋 {t('runs_detected')}", expanded=False):
                runs_data = []
                for run_id, run_info in st.session_state.all_run_data.items():
                    times = run_info.get("times", [])
                    velocities = run_info.get("velocities", [])
                    heading = run_info.get("heading", "?")

                    runs_data.append({
                        t("run_id"): run_id,
                        t("heading"): heading,
                        "Pontos": len(times),
                        "V_inicial (km/h)": f"{velocities[0]:.1f}" if len(velocities) > 0 else "N/A",
                        "V_final (km/h)": f"{velocities[-1]:.1f}" if len(velocities) > 0 else "N/A",
                    })
                st.dataframe(pd.DataFrame(runs_data), use_container_width=True, hide_index=True)

        if st.button(f"➡️ {t('proceed_to_vehicle_data')}", type="primary", use_container_width=True):
            st.session_state.current_page = "2_dados_veiculo"
            st.rerun()


def render_traditional_upload(t):
    """Renderiza o upload para método tradicional."""

    st.subheader(f"📁 {t('traditional_method')}")

    # Upload do arquivo de coastdown
    uploaded_coastdown = st.file_uploader(
        t("upload_coastdown_csv"),
        type=["csv"],
        key="coastdown_file_traditional"
    )

    # Upload do arquivo meteorológico (opcional)
    uploaded_weather = st.file_uploader(
        t("upload_weather_csv"),
        type=["csv"],
        key="weather_file_traditional"
    )

    # Botão para carregar os dados
    if uploaded_coastdown is not None:
        if st.button(f"📥 {t('load_data')}", type="primary"):
            with st.spinner("Carregando dados..."):
                try:
                    # Cria arquivo temporário para o coastdown
                    with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as temp_file:
                        temp_file.write(uploaded_coastdown.getvalue())
                        temp_path = temp_file.name

                    # Carrega os dados usando a função existente
                    df_raw, all_run_data, test_date = carregar_dados_csv_robusto(temp_path)

                    # Remove o arquivo temporário após uso
                    try:
                        os.unlink(temp_path)
                    except:
                        pass

                    if df_raw is not None and all_run_data:
                        st.session_state.df_raw = df_raw
                        st.session_state.all_run_data = all_run_data
                        st.session_state.coastdown_csv_path = uploaded_coastdown.name
                        st.session_state.data_loaded = True
                        st.session_state.data_info = {
                            "filename": uploaded_coastdown.name,
                            "rows": len(df_raw),
                            "runs": len(all_run_data)
                        }

                        # Carrega dados meteorológicos se fornecidos
                        if uploaded_weather is not None:
                            with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as weather_temp_file:
                                weather_temp_file.write(uploaded_weather.getvalue())
                                weather_temp_path = weather_temp_file.name

                            weather_data = read_weather_station_csv(weather_temp_path)

                            # Remove o arquivo temporário após uso
                            try:
                                os.unlink(weather_temp_path)
                            except:
                                pass

                            if weather_data is not None:
                                st.session_state.weather_data = weather_data
                                st.session_state.meteo_csv_path = uploaded_weather.name

                        st.success(t("file_loaded_success"))
                        st.rerun()
                    else:
                        st.error(t("file_load_error"))

                except Exception as e:
                    st.error(f"{t('file_load_error')}: {str(e)}")


def render_split_upload(t):
    """Renderiza o upload para método split."""

    st.subheader(f"📁 {t('split_method')}")

    col1, col2 = st.columns(2)

    with col1:
        # Upload do arquivo de alta velocidade
        uploaded_alta = st.file_uploader(
            t("upload_high_speed_csv"),
            type=["csv"],
            key="alta_file_split"
        )

    with col2:
        # Upload do arquivo de baixa velocidade
        uploaded_baixa = st.file_uploader(
            t("upload_low_speed_csv"),
            type=["csv"],
            key="baixa_file_split"
        )

    # Upload do arquivo meteorológico (opcional)
    uploaded_weather = st.file_uploader(
        t("upload_weather_csv"),
        type=["csv"],
        key="weather_file_split"
    )

    # Velocidades de referência
    st.markdown("---")
    st.subheader("Velocidades de Referência")

    col1, col2 = st.columns(2)
    with col1:
        ref_alta = st.number_input(
            "Velocidade Alta (km/h)",
            min_value=50.0,
            max_value=150.0,
            value=st.session_state.ref_vel_alta,
            step=5.0
        )
        st.session_state.ref_vel_alta = ref_alta

    with col2:
        ref_baixa = st.number_input(
            "Velocidade Baixa (km/h)",
            min_value=20.0,
            max_value=80.0,
            value=st.session_state.ref_vel_baixa,
            step=5.0
        )
        st.session_state.ref_vel_baixa = ref_baixa

    # Botão para carregar os dados
    if uploaded_alta is not None and uploaded_baixa is not None:
        if st.button(f"📥 {t('load_data')}", type="primary"):
            with st.spinner("Carregando dados..."):
                try:
                    # Cria arquivos temporários
                    with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as alta_temp_file:
                        alta_temp_file.write(uploaded_alta.getvalue())
                        alta_temp_path = alta_temp_file.name

                    with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as baixa_temp_file:
                        baixa_temp_file.write(uploaded_baixa.getvalue())
                        baixa_temp_path = baixa_temp_file.name

                    # Carrega os dados
                    df_raw_alta, all_run_data_alta, test_date_alta = carregar_dados_csv_robusto(alta_temp_path)
                    df_raw_baixa, all_run_data_baixa, test_date_baixa = carregar_dados_csv_robusto(baixa_temp_path)

                    # Remove os arquivos temporários após uso
                    try:
                        os.unlink(alta_temp_path)
                        os.unlink(baixa_temp_path)
                    except:
                        pass

                    if df_raw_alta is not None and df_raw_baixa is not None:
                        st.session_state.df_raw_alta = df_raw_alta
                        st.session_state.df_raw_baixa = df_raw_baixa
                        st.session_state.all_run_data_alta = all_run_data_alta
                        st.session_state.all_run_data_baixa = all_run_data_baixa
                        st.session_state.split_alta_csv_path = uploaded_alta.name
                        st.session_state.split_baixa_csv_path = uploaded_baixa.name

                        # Combina os run_data para compatibilidade
                        st.session_state.all_run_data = {
                            **{f"alta_{k}": v for k, v in all_run_data_alta.items()},
                            **{f"baixa_{k}": v for k, v in all_run_data_baixa.items()}
                        }

                        st.session_state.data_loaded = True
                        st.session_state.data_info = {
                            "filename_alta": uploaded_alta.name,
                            "filename_baixa": uploaded_baixa.name,
                            "runs_alta": len(all_run_data_alta),
                            "runs_baixa": len(all_run_data_baixa)
                        }

                        # Carrega dados meteorológicos se fornecidos
                        if uploaded_weather is not None:
                            with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as weather_temp_file:
                                weather_temp_file.write(uploaded_weather.getvalue())
                                weather_temp_path = weather_temp_file.name

                            weather_data = read_weather_station_csv(weather_temp_path)

                            # Remove o arquivo temporário após uso
                            try:
                                os.unlink(weather_temp_path)
                            except:
                                pass

                            if weather_data is not None:
                                st.session_state.weather_data_split = weather_data
                                st.session_state.split_meteo_csv_path = uploaded_weather.name

                        st.success(t("file_loaded_success"))
                        st.rerun()
                    else:
                        st.error(t("file_load_error"))

                except Exception as e:
                    st.error(f"{t('file_load_error')}: {str(e)}")
