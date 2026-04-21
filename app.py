# coding: utf-8
"""
Coastdown MDA - Plataforma de Análise Multi-Teste

Aplicação principal para análise de testes de coastdown conforme ABNT 10312.
Suporta múltiplos testes simultâneos e internacionalização (Português/Inglês).

Arquitetura:
- Flat session state = estado do TESTE ATIVO
- tests[test_id] = snapshot salvo ao trocar de teste
- Páginas 2-6 acessam flat keys sem modificação (compatibilidade total)
"""

import copy
import os
import sys
import tempfile
import uuid

import streamlit as st

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from translations import get_translator, get_available_languages
from data.loaders import carregar_dados_csv_robusto, read_weather_station_csv

# ===== CONFIGURAÇÃO DA PÁGINA =====
st.set_page_config(
    page_title="Coastdown MDA",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== CSS CUSTOMIZADO =====
st.markdown("""
<style>
    /* ---- Botões primários verdes ---- */
    div[data-testid="stButton"] button[kind="primary"] {
        background-color: #28a745 !important;
        border-color: #28a745 !important;
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        background-color: #218838 !important;
        border-color: #1e7e34 !important;
    }

    /* ---- Cabeçalhos de tabelas em cinza escuro ---- */
    thead tr th {
        background-color: #2d2d2d !important;
        color: #ffffff !important;
    }

    /* ---- Esconde coluna de índice das tabelas ---- */
    .stDataFrame thead tr th:first-child,
    .stDataFrame tbody tr td:first-child {
        display: none;
    }

    /* ---- Cards de teste na sidebar ---- */
    .mda-test-card {
        border-radius: 8px;
        padding: 10px 14px 10px 14px;
        margin-bottom: 2px;
        transition: border-color 0.2s;
    }
    .mda-test-card.active {
        background-color: #1a2d4a;
        border: 2px solid #4a9eff;
    }
    .mda-test-card.complete {
        background-color: #181818;
        border: 1px solid #3d3d3d;
    }
    .mda-test-card.incomplete {
        background-color: #1e1a13;
        border: 1px solid #ff9800;
    }
    .mda-card-title {
        font-size: 0.88em;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .mda-badge-active {
        background-color: #4a9eff22;
        color: #4a9eff;
        font-size: 0.72em;
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 10px;
        border: 1px solid #4a9eff66;
        letter-spacing: 0.03em;
    }
    .mda-card-files {
        font-size: 0.78em;
        color: #a0a0a0;
        display: flex;
        gap: 14px;
        margin-top: 2px;
    }
    .mda-file-ok   { color: #4caf50; }
    .mda-file-warn { color: #ff9800; }
    .mda-file-err  { color: #f44336; }

    /* ---- Botões de navegação (página ativa destaque) ---- */
    .nav-active-label {
        background-color: #1a2d4a;
        border-left: 3px solid #4a9eff;
        color: #4a9eff;
        font-weight: 600;
        font-size: 0.82em;
        padding: 5px 10px;
        border-radius: 0 6px 6px 0;
        margin-bottom: 4px;
        display: block;
    }

    /* ---- Espaçamento geral ---- */
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 0.5rem;
        padding-bottom: 0.5rem;
    }
    .main .block-container {
        padding-top: 1rem !important;
    }

    /* ---- Abas de navegação: fonte maior ---- */
    .stTabs [data-baseweb="tab"] {
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
</style>
""", unsafe_allow_html=True)

# ===== CONSTANTES: CHAVES DO TESTE =====

# Chaves do session_state que pertencem ao estado de um teste individual.
# São salvas no dict do teste ao trocar de teste ativo e restauradas ao ativar.
TEST_STATE_KEYS = [
    # Arquivos
    "coastdown_csv_path", "meteo_csv_path",
    "split_alta_csv_path", "split_baixa_csv_path", "split_meteo_csv_path",
    # DataFrames
    "df_raw", "df_raw_alta", "df_raw_baixa",
    # Dados processados
    "all_run_data", "all_run_data_alta", "all_run_data_baixa",
    "weather_data", "weather_data_split",
    # Dados do veículo
    "vehicle_info", "total_mass", "mass_input_mode",
    # Coeficientes e pares
    "individual_coeffs", "calculated_pairs", "split_coefficients",
    # Resultados
    "pares_finais_selecionados", "final_results", "algorithm_results",
    # Flags de controle
    "using_split_method", "test_method",
    "data_loaded", "vehicle_data_complete", "pairs_calculated",
    # Velocidades de referência
    "ref_vel_alta", "ref_vel_baixa",
    # Informações
    "data_info",
    # Navegação interna do teste
    "current_page", "pair_analysis_subtab",
]

# Valores padrão para um teste novo/vazio
TEST_DEFAULTS = {
    "coastdown_csv_path": None,
    "meteo_csv_path": None,
    "split_alta_csv_path": None,
    "split_baixa_csv_path": None,
    "split_meteo_csv_path": None,
    "df_raw": None,
    "df_raw_alta": None,
    "df_raw_baixa": None,
    "all_run_data": {},
    "all_run_data_alta": {},
    "all_run_data_baixa": {},
    "weather_data": None,
    "weather_data_split": None,
    "vehicle_info": {},
    "total_mass": 0.0,
    "mass_input_mode": "total",
    "individual_coeffs": {},
    "calculated_pairs": {},
    "split_coefficients": {},
    "pares_finais_selecionados": [],
    "final_results": {},
    "algorithm_results": None,
    "using_split_method": False,
    "test_method": "traditional",
    "data_loaded": False,
    "vehicle_data_complete": False,
    "pairs_calculated": False,
    "ref_vel_alta": 80.0,
    "ref_vel_baixa": 40.0,
    "data_info": {},
    "current_page": "2_dados_veiculo",
    "pair_analysis_subtab": "calculos",
}


# ===== INICIALIZAÇÃO DO SESSION STATE =====

def init_session_state():
    """Inicializa todas as variáveis do session_state."""
    # Configuração global de idioma
    if "language" not in st.session_state:
        st.session_state.language = "pt"

    # Estrutura multi-teste
    if "tests" not in st.session_state:
        st.session_state.tests = {}
    if "active_test_id" not in st.session_state:
        st.session_state.active_test_id = None
    if "show_new_test_form" not in st.session_state:
        st.session_state.show_new_test_form = False
    if "delete_confirm_id" not in st.session_state:
        st.session_state.delete_confirm_id = None

    # Flat keys de compatibilidade com páginas 2-6
    for key, default in TEST_DEFAULTS.items():
        if key not in st.session_state:
            if isinstance(default, (dict, list)):
                st.session_state[key] = copy.deepcopy(default)
            else:
                st.session_state[key] = default


# ===== GERENCIAMENTO DE TESTES =====

def save_active_test_state():
    """Salva o estado atual das flat keys no dicionário do teste ativo."""
    test_id = st.session_state.active_test_id
    if not test_id or test_id not in st.session_state.tests:
        return
    for key in TEST_STATE_KEYS:
        val = st.session_state.get(key)
        if isinstance(val, (dict, list)):
            st.session_state.tests[test_id][key] = copy.deepcopy(val)
        else:
            st.session_state.tests[test_id][key] = val


def load_test_state(test_id):
    """Restaura o estado de um teste nas flat keys."""
    test_data = st.session_state.tests.get(test_id, {})
    for key in TEST_STATE_KEYS:
        if key in test_data:
            val = test_data[key]
            if isinstance(val, (dict, list)):
                st.session_state[key] = copy.deepcopy(val)
            else:
                st.session_state[key] = val
        else:
            default = TEST_DEFAULTS.get(key)
            if isinstance(default, (dict, list)):
                st.session_state[key] = copy.deepcopy(default)
            else:
                st.session_state[key] = default


def activate_test(test_id):
    """Salva estado do teste atual e ativa outro teste."""
    save_active_test_state()
    load_test_state(test_id)
    st.session_state.active_test_id = test_id


def delete_test(test_id):
    """Remove um teste e ajusta o teste ativo se necessário."""
    if test_id not in st.session_state.tests:
        st.session_state.delete_confirm_id = None
        return

    del st.session_state.tests[test_id]

    if st.session_state.active_test_id == test_id:
        remaining = list(st.session_state.tests.keys())
        if remaining:
            # Ativa o primeiro teste restante
            load_test_state(remaining[0])
            st.session_state.active_test_id = remaining[0]
        else:
            # Sem testes: reseta todas as flat keys
            for key, default in TEST_DEFAULTS.items():
                if isinstance(default, (dict, list)):
                    st.session_state[key] = copy.deepcopy(default)
                else:
                    st.session_state[key] = default
            st.session_state.active_test_id = None

    st.session_state.delete_confirm_id = None


# ===== RENDERIZAÇÃO DA SIDEBAR =====

def render_sidebar(t):
    """Renderiza a sidebar completa: idioma, testes e navegação."""

    # ---- Título ----
    st.markdown("## Coastdown MDA")

    # ---- Seletor de idioma ----
    languages = get_available_languages()
    lang_options = {f"{lang['flag']} {lang['name']}": lang['code'] for lang in languages}

    current_display = next(
        (disp for disp, code in lang_options.items() if code == st.session_state.language),
        list(lang_options.keys())[0]
    )

    selected_display = st.selectbox(
        "🌐 Idioma / Language",
        options=list(lang_options.keys()),
        index=list(lang_options.keys()).index(current_display),
        label_visibility="collapsed",
        key="lang_selector"
    )
    new_lang = lang_options[selected_display]
    if new_lang != st.session_state.language:
        st.session_state.language = new_lang
        st.rerun()

    st.markdown("---")

    # ---- Botão "+ Novo Teste" ----
    if st.button(f"+ {t('new_test')}", use_container_width=True, type="primary"):
        st.session_state.show_new_test_form = True
        st.rerun()

    st.markdown("---")

    # ---- Lista de testes ----
    if not st.session_state.tests:
        st.caption(t("no_tests_message"))
    else:
        for test_id, test in st.session_state.tests.items():
            render_test_card(test_id, test, t)

    # ---- Status do teste ativo ----
    if st.session_state.active_test_id:
        st.markdown("---")
        render_sidebar_status(t)


def render_test_card(test_id, test, t):
    """Renderiza o card visual de um teste na sidebar."""
    is_active = test_id == st.session_state.active_test_id
    name = test.get("name", test_id)

    # Status dos arquivos — usa flat state para teste ativo (live), dict para os outros
    if is_active:
        csv_ok = st.session_state.data_loaded
        meteo_ok = bool(st.session_state.weather_data or st.session_state.meteo_csv_path)
    else:
        csv_ok = test.get("data_loaded", False)
        meteo_ok = bool(test.get("weather_data") or test.get("meteo_csv_path"))

    # Classe CSS conforme estado
    if is_active:
        card_class = "active"
    elif csv_ok:
        card_class = "complete"
    else:
        card_class = "incomplete"

    # Badge "ATIVO" só aparece no card ativo
    badge_html = (
        f'<span class="mda-badge-active">● {t("active_test").upper()}</span>'
        if is_active else ""
    )

    # Ícones de status dos arquivos
    csv_cls = "mda-file-ok" if csv_ok else "mda-file-err"
    csv_sym = "✓" if csv_ok else "✗"
    meteo_cls = "mda-file-ok" if meteo_ok else "mda-file-warn"
    meteo_sym = "✓" if meteo_ok else "⚠"

    # Trunca nome longo para caber no card
    display_name = name if len(name) <= 20 else name[:18] + "…"

    # Layout: card (esquerda) | botão excluir (direita, mesma linha)
    col_card, col_del = st.columns([5, 1])

    with col_card:
        st.markdown(
            f'<div class="mda-test-card {card_class}">'
            f'<div class="mda-card-title"><span>{display_name}</span>{badge_html}</div>'
            f'<div class="mda-card-files">'
            f'<span>CSV: <span class="{csv_cls}">{csv_sym}</span></span>'
            f'<span>Meteo: <span class="{meteo_cls}">{meteo_sym}</span></span>'
            f'</div></div>',
            unsafe_allow_html=True
        )
        if not is_active:
            if st.button(
                t("switch_test"),
                key=f"sel_{test_id}",
                use_container_width=True
            ):
                activate_test(test_id)
                st.session_state.show_new_test_form = False
                st.rerun()

    with col_del:
        # Alinha verticalmente com o topo do card
        st.markdown("<div style='padding-top:6px'>", unsafe_allow_html=True)
        if st.button("✕", key=f"del_{test_id}", help=t("remove_test"), use_container_width=True):
            st.session_state.delete_confirm_id = test_id
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)

    # Confirmação de exclusão
    if st.session_state.delete_confirm_id == test_id:
        st.warning(t("confirm_delete_test"))
        c1, c2 = st.columns(2)
        with c1:
            if st.button(t("confirm"), key=f"conf_del_{test_id}", type="primary"):
                delete_test(test_id)
                st.rerun()
        with c2:
            if st.button(t("cancel"), key=f"canc_del_{test_id}"):
                st.session_state.delete_confirm_id = None
                st.rerun()


def render_sidebar_status(t):
    """Renderiza status resumido do teste ativo na sidebar."""
    st.markdown(
        f"<p style='font-size:0.78em;font-weight:600;color:#a0a0a0;"
        f"letter-spacing:0.08em;margin-bottom:6px;margin-top:4px'>"
        f"{t('status').upper()}</p>",
        unsafe_allow_html=True
    )

    if st.session_state.data_loaded:
        runs = len(st.session_state.all_run_data)
        st.markdown(
            f"<div style='font-size:0.82em;color:#4caf50;margin-bottom:3px'>"
            f"✅ {t('file_loaded_success')}"
            + (f" <span style='color:#a0a0a0'>({runs} {t('runs_detected')})</span>" if runs else "")
            + "</div>",
            unsafe_allow_html=True
        )

    if st.session_state.vehicle_data_complete:
        mass_str = (
            f" <span style='color:#a0a0a0'>{st.session_state.total_mass:.0f} kg</span>"
            if st.session_state.total_mass else ""
        )
        st.markdown(
            f"<div style='font-size:0.82em;color:#4caf50;margin-bottom:3px'>"
            f"✅ {t('vehicle_information')}{mass_str}</div>",
            unsafe_allow_html=True
        )

    if st.session_state.calculated_pairs:
        n = len(st.session_state.calculated_pairs)
        st.markdown(
            f"<div style='font-size:0.82em;color:#4caf50;margin-bottom:3px'>"
            f"✅ {n} {t('calculated_pairs')}</div>",
            unsafe_allow_html=True
        )

    if st.session_state.pares_finais_selecionados:
        n = len(st.session_state.pares_finais_selecionados)
        st.markdown(
            f"<div style='font-size:0.82em;color:#4a9eff;margin-bottom:3px'>"
            f"{n} {t('selected_pairs')}</div>",
            unsafe_allow_html=True
        )


# ===== ÁREA PRINCIPAL =====

def render_welcome(t):
    """Renderiza a tela de boas-vindas quando não há testes ativos."""
    st.title("Coastdown MDA")
    st.markdown("---")

    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown(f"## {t('no_tests_title')}")
        st.markdown(t("no_tests_description"))
        st.markdown("")
        st.markdown(f"""
**Para começar:**
1. Clique em **➕ {t('new_test')}** na barra lateral
2. Dê um nome ao teste
3. Carregue o arquivo CSV do coastdown
4. Opcionalmente carregue o arquivo meteorológico
5. Clique em **{t('create_test')}**
        """)
        st.markdown("")
        if st.button(f"➕ {t('new_test')}", type="primary", use_container_width=True):
            st.session_state.show_new_test_form = True
            st.rerun()


@st.dialog("➕ Novo Teste / New Test", width="large")
def new_test_dialog(t):
    """
    Modal de criação de novo teste usando @st.dialog (Streamlit >= 1.31).
    Integra o upload de arquivos diretamente (substitui page_1).
    """
    # Nome do teste
    test_name = st.text_input(
        t("test_name"),
        placeholder="Ex.: Teste A - Veículo X",
        key="new_test_name_input"
    )

    st.markdown("---")

    # Upload do arquivo CSV de coastdown
    st.subheader(f"📁 {t('upload_coastdown_csv')}")
    uploaded_csv = st.file_uploader(
        t("upload_coastdown_csv"),
        type=["csv"],
        key="new_test_csv_upload",
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Upload do arquivo meteorológico (opcional)
    st.subheader(f"📊 {t('upload_weather_csv')}")
    uploaded_meteo = st.file_uploader(
        t("upload_weather_csv"),
        type=["csv"],
        key="new_test_meteo_upload",
        label_visibility="collapsed"
    )

    # Condições fixas se não houver arquivo meteo
    fixed_temp = 25.0
    fixed_pressure = 101.3
    if not uploaded_meteo:
        with st.expander(f"⚙️ {t('fixed_conditions')}", expanded=False):
            st.caption(t("fixed_conditions_hint"))
            fc1, fc2 = st.columns(2)
            with fc1:
                fixed_temp = st.number_input(
                    t("temperature"), value=25.0, step=0.1,
                    key="new_test_temp"
                )
            with fc2:
                fixed_pressure = st.number_input(
                    t("pressure"), value=101.3, step=0.1,
                    key="new_test_pressure"
                )

    st.markdown("---")

    # Botões de ação
    c1, c2 = st.columns(2)
    with c1:
        if st.button(f"✖️ {t('cancel')}", use_container_width=True):
            st.session_state.show_new_test_form = False
            st.rerun()
    with c2:
        create_disabled = (not uploaded_csv) or (not test_name.strip())
        if st.button(
            f"✅ {t('create_test')}",
            type="primary",
            use_container_width=True,
            disabled=create_disabled
        ):
            _process_new_test(
                test_name.strip(),
                uploaded_csv,
                uploaded_meteo,
                fixed_temp,
                fixed_pressure,
                t
            )


def _process_new_test(name, uploaded_csv, uploaded_meteo, fixed_temp, fixed_pressure, t):
    """
    Processa os arquivos carregados e cria o novo teste no session_state.
    Salva o estado do teste ativo atual antes de criar o novo.
    """
    with st.spinner(t("loading_files")):
        try:
            # Processa arquivo CSV de coastdown
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tmp:
                tmp.write(uploaded_csv.getvalue())
                tmp_path = tmp.name

            df_raw, all_run_data, _test_date = carregar_dados_csv_robusto(tmp_path)

            try:
                os.unlink(tmp_path)
            except Exception:
                pass

            if df_raw is None or not all_run_data:
                st.error(t("file_load_error"))
                return

            # Processa arquivo meteorológico se fornecido
            weather_data = None
            meteo_name = None
            if uploaded_meteo is not None:
                with tempfile.NamedTemporaryFile(
                    mode='wb', suffix='.csv', delete=False
                ) as tmp_m:
                    tmp_m.write(uploaded_meteo.getvalue())
                    tmp_m_path = tmp_m.name

                weather_data = read_weather_station_csv(tmp_m_path)
                meteo_name = uploaded_meteo.name

                try:
                    os.unlink(tmp_m_path)
                except Exception:
                    pass

            # Salva estado do teste ativo atual (se houver)
            save_active_test_state()

            # Cria ID único para o novo teste
            test_id = f"test_{uuid.uuid4().hex[:8]}"

            # Monta dicionário do novo teste a partir dos defaults
            new_test_data = copy.deepcopy(TEST_DEFAULTS)
            new_test_data.update({
                # Metadados do teste
                "name": name,
                # Dados carregados
                "df_raw": df_raw,
                "all_run_data": all_run_data,
                "coastdown_csv_path": uploaded_csv.name,
                "data_loaded": True,
                "data_info": {
                    "filename": uploaded_csv.name,
                    "rows": len(df_raw),
                    "runs": len(all_run_data),
                },
                # Dados meteorológicos
                "weather_data": weather_data,
                "meteo_csv_path": meteo_name,
                # Começa pela página de dados do veículo
                "current_page": "2_dados_veiculo",
            })

            # Registra o teste no dicionário de testes
            st.session_state.tests[test_id] = new_test_data

            # Ativa o novo teste (carrega seus dados nas flat keys)
            load_test_state(test_id)
            st.session_state.active_test_id = test_id
            st.session_state.show_new_test_form = False

            st.rerun()

        except Exception as e:
            st.error(f"{t('file_load_error')}: {str(e)}")


def render_test_analysis(t):
    """Renderiza a análise do teste ativo com navegação por abas."""
    active_test = st.session_state.tests.get(st.session_state.active_test_id, {})
    test_name = active_test.get("name", "Teste")

    st.title(test_name)

    tab_labels = [
        t("page_vehicle_data"),
        t("page_pair_analysis"),
        t("page_algorithm_selection"),
        t("page_final_comparison"),
        t("page_final_results"),
    ]

    tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_labels)

    with tab1:
        from pages import page_2_dados_veiculo
        page_2_dados_veiculo.render(t)

    with tab2:
        from pages import page_3_analise_pares
        page_3_analise_pares.render(t)

    with tab3:
        from pages import page_4_selecao_algoritmo
        page_4_selecao_algoritmo.render(t)

    with tab4:
        from pages import page_5_comparativo
        page_5_comparativo.render(t)

    with tab5:
        from pages import page_6_resultados
        page_6_resultados.render(t)


# ===== PONTO DE ENTRADA =====

init_session_state()

# Obtém a função de tradução para o idioma atual
t = get_translator(st.session_state.language)

# Renderiza sidebar
with st.sidebar:
    render_sidebar(t)

# Abre o modal de novo teste quando solicitado (overlay sobre o conteúdo)
if st.session_state.show_new_test_form:
    new_test_dialog(t)

# Renderiza área principal conforme estado
if not st.session_state.active_test_id:
    render_welcome(t)
else:
    render_test_analysis(t)
