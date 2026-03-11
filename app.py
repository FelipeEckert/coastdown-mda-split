# coding: utf-8
"""
Coastdown Analysis Application - Streamlit Version

Aplicação principal para análise de testes de coastdown conforme ABNT 10312.
Suporta internacionalização (Português/Inglês).
"""

import streamlit as st
import sys
import os

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from translations import get_translator, get_available_languages

# Configuração da página
st.set_page_config(
    page_title="Coastdown Analysis (ABNT 10312)",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para botões de navegação
st.markdown("""
<style>
    /* Botões de navegação verdes */
    div[data-testid="stButton"] button[kind="primary"] {
        background-color: #28a745 !important;
        border-color: #28a745 !important;
    }
    
    div[data-testid="stButton"] button[kind="primary"]:hover {
        background-color: #218838 !important;
        border-color: #1e7e34 !important;
    }
    
    /* Cabeçalhos das tabelas em cinza */
    thead tr th {
        background-color: #2d2d2d !important;
        color: #ffffff !important;
    }
    
    /* Esconde a coluna de índice das tabelas */
    .stDataFrame thead tr th:first-child,
    .stDataFrame tbody tr td:first-child {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# ===== INICIALIZAÇÃO DO SESSION STATE =====
def init_session_state():
    """Inicializa todas as variáveis do session_state."""
    defaults = {
        # Idioma
        "language": "pt",
        
        # Método de teste
        "test_method": "traditional",  # "traditional" ou "split"
        
        # Arquivos carregados
        "coastdown_csv_path": None,
        "meteo_csv_path": None,
        "split_alta_csv_path": None,
        "split_baixa_csv_path": None,
        "split_meteo_csv_path": None,
        
        # DataFrames
        "df_raw": None,
        "df_raw_alta": None,
        "df_raw_baixa": None,
        
        # Dados processados
        "all_run_data": {},
        "all_run_data_alta": {},
        "all_run_data_baixa": {},
        "weather_data": None,
        "weather_data_split": None,
        
        # Dados do veículo
        "vehicle_info": {},
        "total_mass": 0.0,
        "mass_input_mode": "total",  # "total" ou "components"
        
        # Coeficientes
        "individual_coeffs": {},
        "calculated_pairs": {},
        "split_coefficients": {},
        
        # Resultados
        "pares_finais_selecionados": [],
        "final_results": {},
        "algorithm_results": None,
        
        # Flags de controle
        "using_split_method": False,
        "data_loaded": False,
        "vehicle_data_complete": False,
        "pairs_calculated": False,
        
        # Velocidades de referência (Split)
        "ref_vel_alta": 80.0,
        "ref_vel_baixa": 40.0,
        
        # Informações adicionais
        "data_info": {},
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# Inicializa o session state
init_session_state()

# ===== SIDEBAR: SELETOR DE IDIOMA =====
with st.sidebar:
    st.markdown("### 🌐 Idioma / Language")
    
    languages = get_available_languages()
    lang_options = {f"{lang['flag']} {lang['name']}": lang['code'] for lang in languages}
    
    # Encontra o índice do idioma atual
    current_lang_display = None
    for display, code in lang_options.items():
        if code == st.session_state.language:
            current_lang_display = display
            break
    
    selected_lang_display = st.selectbox(
        "Selecione / Select",
        options=list(lang_options.keys()),
        index=list(lang_options.keys()).index(current_lang_display) if current_lang_display else 0,
        label_visibility="collapsed"
    )
    
    # Atualiza o idioma se mudou
    new_lang = lang_options[selected_lang_display]
    if new_lang != st.session_state.language:
        st.session_state.language = new_lang
        st.rerun()
    
    st.markdown("---")

# Obtém a função de tradução para o idioma atual
t = get_translator(st.session_state.language)

# ===== TÍTULO PRINCIPAL =====
st.title(t("app_title"))

# ===== NAVEGAÇÃO =====
st.sidebar.markdown(f"### 📋 {t('page_open_test').split('.')[0]}. Navegação")

# Páginas disponíveis
pages = [
    ("1_abrir_teste", t("page_open_test")),
    ("2_dados_veiculo", t("page_vehicle_data")),
    ("3_analise_pares", t("page_pair_analysis")),
    ("4_selecao_algoritmo", "🤖 Seleção por Algoritmo"),
    ("5_comparativo", t("page_final_comparison")),
    ("6_resultados", t("page_final_results")),
]

# Determina quais páginas estão habilitadas
page_enabled = {
    "1_abrir_teste": True,
    "2_dados_veiculo": st.session_state.data_loaded,
    "3_analise_pares": st.session_state.vehicle_data_complete,
    "4_selecao_algoritmo": st.session_state.vehicle_data_complete,
    "5_comparativo": st.session_state.pairs_calculated,
    "6_resultados": len(st.session_state.pares_finais_selecionados) > 0,
}

# Inicializa página atual se não existir
if "current_page" not in st.session_state:
    st.session_state.current_page = "1_abrir_teste"

# Cria botões de navegação na sidebar
for page_id, page_name in pages:
    enabled = page_enabled.get(page_id, False)
    
    if enabled:
        if st.sidebar.button(page_name, key=f"nav_{page_id}", use_container_width=True):
            st.session_state.current_page = page_id
            st.rerun()
    else:
        st.sidebar.button(page_name, key=f"nav_{page_id}", use_container_width=True, disabled=True)
    
    # Se for a página de Análise de Pares e estiver ativa, mostra sub-abas
    if page_id == "3_analise_pares" and enabled and st.session_state.current_page == "3_analise_pares":
        # Inicializa sub-aba se não existir
        if "pair_analysis_subtab" not in st.session_state:
            st.session_state.pair_analysis_subtab = "calculos"
        
        st.sidebar.markdown("**Sub-páginas:**")
        
        col1, col2, col3 = st.sidebar.columns(3)
        with col1:
            if st.button("🔢", key="sub_calculos", help="Cálculos", use_container_width=True):
                st.session_state.pair_analysis_subtab = "calculos"
                st.rerun()
        with col2:
            if st.button("📊", key="sub_graficos", help="Gráficos", use_container_width=True):
                st.session_state.pair_analysis_subtab = "graficos"
                st.rerun()
        with col3:
            if st.button("🎯", key="sub_simulacao", help="Simulação", use_container_width=True):
                st.session_state.pair_analysis_subtab = "simulacao"
                st.rerun()

st.sidebar.markdown("---")

# ===== STATUS DO PROGRESSO =====
with st.sidebar:
    st.markdown("### 📊 Status")
    
    if st.session_state.data_loaded:
        st.success(f"✅ {t('file_loaded_success')}")
        if st.session_state.all_run_data:
            st.info(f"🔢 {len(st.session_state.all_run_data)} {t('runs_detected')}")
    
    if st.session_state.vehicle_data_complete:
        st.success(f"✅ {t('vehicle_information')}")
        st.info(f"⚖️ {st.session_state.total_mass:.1f} kg")
    
    if st.session_state.calculated_pairs:
        st.success(f"✅ {len(st.session_state.calculated_pairs)} {t('calculated_pairs')}")
    
    if st.session_state.pares_finais_selecionados:
        st.success(f"✅ {len(st.session_state.pares_finais_selecionados)} {t('selected_pairs')}")

# ===== CONTEÚDO DA PÁGINA ATUAL =====
# O conteúdo será carregado das páginas individuais
current_page = st.session_state.current_page

if current_page == "1_abrir_teste":
    from pages import page_1_abrir_teste
    page_1_abrir_teste.render(t)
    
elif current_page == "2_dados_veiculo":
    from pages import page_2_dados_veiculo
    page_2_dados_veiculo.render(t)
    
elif current_page == "3_analise_pares":
    from pages import page_3_analise_pares
    page_3_analise_pares.render(t)
    
elif current_page == "4_selecao_algoritmo":
    from pages import page_4_selecao_algoritmo
    page_4_selecao_algoritmo.render(t)
    
elif current_page == "5_comparativo":
    from pages import page_5_comparativo
    page_5_comparativo.render(t)
    
elif current_page == "6_resultados":
    from pages import page_6_resultados
    page_6_resultados.render(t)
