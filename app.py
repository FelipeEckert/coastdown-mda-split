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
import hashlib
import os
import sys
import tempfile
import uuid

import streamlit as st

# Adiciona o diretório raiz ao path para imports
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
APP_LOGO_SVG_PATH = os.path.join(ASSETS_DIR, "app_logo.svg")
APP_LOGO_PNG_PATH = os.path.join(ASSETS_DIR, "app_logo.png")
HYUNDAI_LOGO_SVG_PATH = os.path.join(ASSETS_DIR, "hyundai_logo.svg")
HYUNDAI_LOGO_PNG_PATH = os.path.join(ASSETS_DIR, "hyundai_logo.png")

sys.path.insert(0, BASE_DIR)

from translations import get_translator, get_available_languages
from data.loaders import carregar_dados_csv_robusto
from data.weather_loader import read_weather_file
from core.split_state import clear_split_final_state, invalidate_split_input_state

# ===== CONFIGURAÇÃO DA PÁGINA =====
st.set_page_config(
    page_title="Coastdown MDA Split",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

FONT_SIZE_PRESETS = {
    "small": {
        "base": "14px",
        "small": "12px",
        "label": "14px",
        "control": "14px",
        "button": "14px",
        "title": "22px",
        "subtitle": "18px",
        "section": "16px",
        "tab": "14px",
        "metric_value": "22px",
        "metric_label": "13px",
        "table": "13px",
        "sidebar_title": "14px",
        "sidebar_meta": "12px",
    },
    "medium": {
        "base": "16px",
        "small": "14px",
        "label": "16px",
        "control": "16px",
        "button": "16px",
        "title": "26px",
        "subtitle": "20px",
        "section": "18px",
        "tab": "16px",
        "metric_value": "26px",
        "metric_label": "15px",
        "table": "15px",
        "sidebar_title": "16px",
        "sidebar_meta": "14px",
    },
    "large": {
        "base": "18px",
        "small": "16px",
        "label": "18px",
        "control": "18px",
        "button": "18px",
        "title": "30px",
        "subtitle": "24px",
        "section": "21px",
        "tab": "18px",
        "metric_value": "30px",
        "metric_label": "17px",
        "table": "17px",
        "sidebar_title": "18px",
        "sidebar_meta": "16px",
    },
}


def apply_font_size_css(font_size_option):
    """Aplica CSS global centralizado para tamanhos de fonte da aplicação."""
    tokens = FONT_SIZE_PRESETS.get(font_size_option, FONT_SIZE_PRESETS["medium"])

    st.markdown(
        f"""
<style>
    :root {{
        --mda-font-base: {tokens["base"]};
        --mda-font-small: {tokens["small"]};
        --mda-font-label: {tokens["label"]};
        --mda-font-control: {tokens["control"]};
        --mda-font-button: {tokens["button"]};
        --mda-font-title: {tokens["title"]};
        --mda-font-subtitle: {tokens["subtitle"]};
        --mda-font-section: {tokens["section"]};
        --mda-font-tab: {tokens["tab"]};
        --mda-font-metric-value: {tokens["metric_value"]};
        --mda-font-metric-label: {tokens["metric_label"]};
        --mda-font-table: {tokens["table"]};
        --mda-font-sidebar-title: {tokens["sidebar_title"]};
        --mda-font-sidebar-meta: {tokens["sidebar_meta"]};
    }}

    html, body, [class*="css"] {{
        font-size: var(--mda-font-base);
    }}

    body, p, li, div, span, label {{
        font-size: inherit;
    }}

    h1 {{
        font-size: var(--mda-font-title) !important;
    }}

    h2 {{
        font-size: var(--mda-font-subtitle) !important;
    }}

    h3 {{
        font-size: var(--mda-font-section) !important;
    }}

    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stCaptionContainer"] p,
    .stCaption,
    .stMarkdown,
    .stText,
    .stAlert,
    .stAlert *,
    .stRadio,
    .stRadio *,
    .stCheckbox,
    .stCheckbox *,
    .stFileUploader,
    .stFileUploader *,
    .stExpander,
    .stExpander * {{
        font-size: var(--mda-font-base) !important;
    }}

    [data-testid="stCaptionContainer"] p,
    .stCaption {{
        font-size: var(--mda-font-small) !important;
    }}

    [data-testid="stMetricValue"] {{
        font-size: var(--mda-font-metric-value) !important;
    }}

    [data-testid="stMetricLabel"],
    [data-testid="stMetricDelta"] {{
        font-size: var(--mda-font-metric-label) !important;
    }}

    div[data-testid="stButton"] button,
    div[data-testid="stDownloadButton"] button {{
        font-size: var(--mda-font-button) !important;
    }}

    .stTextInput label,
    .stNumberInput label,
    .stSelectbox label,
    .stDateInput label,
    .stMultiSelect label,
    .stTextArea label,
    .stRadio label,
    .stCheckbox label,
    .stFileUploader label {{
        font-size: var(--mda-font-label) !important;
    }}

    input,
    textarea,
    [data-baseweb="input"] input,
    [data-baseweb="input"] textarea,
    [data-baseweb="base-input"] input,
    [data-baseweb="select"] > div,
    [data-baseweb="select"] span,
    [data-baseweb="select"] input,
    [data-baseweb="tag"],
    .stSelectbox div,
    .stMultiSelect div,
    .stDateInput input {{
        font-size: var(--mda-font-control) !important;
    }}

    .stTabs [data-baseweb="tab"] {{
        font-size: var(--mda-font-tab) !important;
        font-weight: 500 !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }}

    .stTabs [data-baseweb="tab-list"] {{
        gap: 2px;
    }}

    .stDataFrame,
    .stDataFrame *,
    [data-testid="stTable"],
    [data-testid="stTable"] *,
    table,
    thead tr th,
    tbody tr td {{
        font-size: var(--mda-font-table) !important;
    }}

    /* ---- Botões primários verdes ---- */
    div[data-testid="stButton"] button[kind="primary"] {{
        background-color: #28a745 !important;
        border-color: #28a745 !important;
    }}

    div[data-testid="stButton"] button[kind="primary"]:hover {{
        background-color: #218838 !important;
        border-color: #1e7e34 !important;
    }}

    /* ---- Cabeçalhos de tabelas em cinza escuro ---- */
    thead tr th {{
        background-color: #2d2d2d !important;
        color: #ffffff !important;
    }}

    /* ---- Esconde coluna de índice das tabelas ---- */
    .stDataFrame thead tr th:first-child,
    .stDataFrame tbody tr td:first-child {{
        display: none;
    }}

    .mda-sidebar-status-label {{
        font-size: var(--mda-font-small);
        font-weight: 600;
        color: #a0a0a0;
        letter-spacing: 0.08em;
        margin-bottom: 6px;
        margin-top: 4px;
    }}

    .mda-sidebar-status-item {{
        font-size: var(--mda-font-sidebar-meta);
        margin-bottom: 3px;
    }}

    .mda-pair-energy-value {{
        margin: 0;
        padding: 0;
        font-size: var(--mda-font-subtitle);
        line-height: 1.1;
    }}

    .mda-pair-energy-unit {{
        margin: 0;
        color: #888;
        font-size: var(--mda-font-small);
    }}

    /* ---- Espaçamento geral ---- */
    section[data-testid="stSidebar"] > div:first-child {{
        padding-top: 0.5rem;
        padding-bottom: 0.5rem;
    }}

    section[data-testid="stSidebar"] [class*="st-key-sidebar_brand_app_logo"],
    section[data-testid="stSidebar"] [class*="st-key-sidebar_brand_hyundai_logo"] {{
        margin-bottom: -0.35rem;
    }}

    .main .block-container {{
        padding-top: 1rem !important;
    }}

    /* ---- Cards de teste da sidebar: refinamento visual nativo ---- */
    section[data-testid="stSidebar"] [class*="st-key-test_card_active_"] {{
        background-color: #162b4d;
        border: 1px solid #4a9eff;
        border-radius: 10px;
        padding: 0.45rem 0.6rem;
        margin-bottom: 0.35rem;
    }}

    section[data-testid="stSidebar"] [class*="st-key-test_card_inactive_"] {{
        background-color: #1e1e1e;
        border: 1px solid #3d3d3d;
        border-radius: 10px;
        padding: 0.45rem 0.6rem;
        margin-bottom: 0.35rem;
    }}

    section[data-testid="stSidebar"] [class*="st-key-delete_btn_"] [data-testid="stButton"] {{
        width: auto;
    }}

    section[data-testid="stSidebar"] [class*="st-key-delete_btn_"] > div {{
        display: flex;
        justify-content: flex-end;
        align-items: flex-start;
    }}

    section[data-testid="stSidebar"] [class*="st-key-delete_btn_"] [data-testid="stButton"] button {{
        width: auto !important;
        min-width: 1.9rem !important;
        height: 1.9rem !important;
        padding: 0.08rem 0.42rem !important;
        line-height: 1 !important;
        margin-top: 0 !important;
        background-color: #8a2121 !important;
        border-color: #8a2121 !important;
        color: #ffffff !important;
    }}

    section[data-testid="stSidebar"] [class*="st-key-delete_btn_"] [data-testid="stButton"] button:hover {{
        background-color: #751b1b !important;
        border-color: #751b1b !important;
        color: #ffffff !important;
    }}

    section[data-testid="stSidebar"] [class*="st-key-sel_"] [data-testid="stButton"] button {{
        background-color: #46874e !important;
        border-color: #46874e !important;
        color: #ffffff !important;
    }}

    section[data-testid="stSidebar"] [class*="st-key-sel_"] [data-testid="stButton"] button:hover {{
        background-color: #3d7544 !important;
        border-color: #3d7544 !important;
        color: #ffffff !important;
    }}

    section[data-testid="stSidebar"] [class*="st-key-edit_btn_"] {{
        display: flex;
        justify-content: flex-end;
        align-items: center;
    }}

    section[data-testid="stSidebar"] [class*="st-key-edit_btn_"] > div {{
        width: 100%;
        display: flex;
        justify-content: flex-end;
        align-items: center;
    }}

    section[data-testid="stSidebar"] [class*="st-key-edit_btn_"] [data-testid="stButton"] {{
        width: auto;
        margin-left: auto;
    }}

    section[data-testid="stSidebar"] [class*="st-key-edit_btn_"] [data-testid="stButton"] button {{
        width: auto !important;
        min-width: 0 !important;
        height: 1.8rem !important;
        min-height: 1.8rem !important;
        padding: 0.04rem 0.38rem !important;
        line-height: 1 !important;
        font-size: var(--mda-font-small) !important;
        margin-top: 0.3rem !important;
        white-space: nowrap !important;
    }}

</style>
        """,
        unsafe_allow_html=True,
    )


def get_first_existing_asset(asset_paths):
    """Retorna o primeiro asset existente na ordem de prioridade informada."""
    for asset_path in asset_paths:
        if os.path.exists(asset_path):
            return asset_path
    return None


def render_optional_logo(asset_paths, width, key):
    """Renderiza um logo local opcional sem quebrar se o arquivo faltar."""
    asset_path = get_first_existing_asset(asset_paths)
    if asset_path:
        with st.container(key=key):
            st.image(asset_path, width=width)


def render_optional_app_logo():
    """Renderiza o logo do app no topo da sidebar, se o asset existir."""
    render_optional_logo(
        (APP_LOGO_SVG_PATH, APP_LOGO_PNG_PATH),
        width=64,
        key="sidebar_brand_app_logo",
    )


def render_optional_hyundai_brand():
    """Renderiza a marca Hyundai no topo da sidebar sem quebrar se o arquivo faltar."""
    render_optional_logo(
        (HYUNDAI_LOGO_SVG_PATH, HYUNDAI_LOGO_PNG_PATH),
        width=160,
        key="sidebar_brand_hyundai_logo",
    )

# ===== CONSTANTES: CHAVES DO TESTE =====

# Chaves do session_state que pertencem ao estado de um teste individual.
# São salvas no dict do teste ao trocar de teste ativo e restauradas ao ativar.
TEST_STATE_KEYS = [
    # Arquivos
    "coastdown_csv_path", "meteo_csv_path",
    "split_alta_csv_path", "split_baixa_csv_path", "split_meteo_csv_path",
    "split_source_files", "split_input_sources", "split_input_mode", "split_input_layout", "split_input_version",
    # DataFrames
    "df_raw", "df_raw_alta", "df_raw_baixa",
    # Dados processados
    "all_run_data", "all_run_data_alta", "all_run_data_baixa",
    "weather_data", "weather_data_split",
    "csv_test_date",
    # Dados do veículo
    "vehicle_info", "total_mass", "mass_input_mode",
    "vehicle_model_input", "test_date_input",
    # Coeficientes e pares
    "split_interval_config", "split_interval_draft_config",
    "split_parse_dirty", "split_parse_feedback_current",
    "split_parse_validation_issues", "split_processed_at",
    "split_parsed_runs", "split_results",
    "split_comparison_pairs", "split_last_calculated_result",
    # Resultados
    "split_final_results",
    # Flags de controle
    "using_split_method", "test_method",
    "data_loaded", "vehicle_data_complete",
    # Velocidades de referência
    # Informações
    "data_info",
    # Navegação interna do teste
    "current_page",
    # Alertas
    "date_mismatch_warning",
    "sync_meteo_by_time_only",
    "fixed_temperature", "fixed_pressure",
    "split_ambient_mode", "split_fixed_temperature", "split_fixed_pressure",
    "split_ambient_signature", "split_ambient_version",
    # Estado auxiliar do teste
    "excel_buffer",
]

# Valores padrão para um teste novo/vazio
TEST_DEFAULTS = {
    "coastdown_csv_path": None,
    "meteo_csv_path": None,
    "split_alta_csv_path": None,
    "split_baixa_csv_path": None,
    "split_meteo_csv_path": None,
    "split_source_files": [],
    "split_input_sources": [],
    "split_input_mode": "separate",
    "split_input_layout": "separate",
    "split_input_version": 0,
    "df_raw": None,
    "df_raw_alta": None,
    "df_raw_baixa": None,
    "all_run_data": {},
    "all_run_data_alta": {},
    "all_run_data_baixa": {},
    "weather_data": None,
    "weather_data_split": None,
    "csv_test_date": None,
    "vehicle_info": {},
    "total_mass": 0.0,
    "mass_input_mode": "total",
    "vehicle_model_input": "",
    "test_date_input": None,
    "split_interval_config": {
        "step_kmh": 5.0,
        "high": {"start": 90.0, "end": 70.0, "reference": 80.0},
        "low": {"start": 45.0, "end": 35.0, "reference": 40.0},
    },
    "split_interval_draft_config": {
        "step_kmh": 5.0,
        "high": {"start": 90.0, "end": 70.0, "reference": 80.0},
        "low": {"start": 45.0, "end": 35.0, "reference": 40.0},
    },
    "split_parse_dirty": True,
    "split_parse_feedback_current": False,
    "split_parse_validation_issues": [],
    "split_processed_at": None,
    "split_parsed_runs": {},
    "split_results": [],
    "split_comparison_pairs": [],
    "split_last_calculated_result": None,
    "split_final_results": {},
    "using_split_method": False,
    "test_method": "traditional",
    "data_loaded": False,
    "vehicle_data_complete": False,
    "data_info": {},
    "current_page": "2_dados_veiculo",
    "date_mismatch_warning": None,
    "sync_meteo_by_time_only": False,
    "fixed_temperature": 25.0,
    "fixed_pressure": 101.3,
    "split_ambient_mode": "fixed",
    "split_fixed_temperature": 20.0,
    "split_fixed_pressure": 101.325,
    "split_ambient_signature": None,
    "split_ambient_version": 0,
    "excel_buffer": None,
}


# ===== INICIALIZAÇÃO DO SESSION STATE =====

def init_session_state():
    """Inicializa todas as variáveis do session_state."""
    # Configuração global de idioma
    if "language" not in st.session_state:
        st.session_state.language = "pt"

    # Preferência de tamanho de fonte
    if "font_size" not in st.session_state:
        st.session_state.font_size = "medium"

    # Estrutura multi-teste
    if "tests" not in st.session_state:
        st.session_state.tests = {}
    if "active_test_id" not in st.session_state:
        st.session_state.active_test_id = None
    if "delete_confirm_id" not in st.session_state:
        st.session_state.delete_confirm_id = None
    if "edit_test_id" not in st.session_state:
        st.session_state.edit_test_id = None
    if "edit_test_dialog_context" not in st.session_state:
        st.session_state.edit_test_dialog_context = None
    if "edit_test_dialog_token" not in st.session_state:
        st.session_state.edit_test_dialog_token = None
    for key in (
        "split_high_uploader_key_version",
        "split_low_uploader_key_version",
        "split_weather_uploader_key_version",
    ):
        if key not in st.session_state:
            st.session_state[key] = 0

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

    # Compatibilidade com testes salvos antes das widget keys por teste.
    if "vehicle_model_input" not in test_data:
        st.session_state.vehicle_model_input = st.session_state.vehicle_info.get("model", "")
    if "test_date_input" not in test_data:
        st.session_state.test_date_input = st.session_state.vehicle_info.get("test_date", None)


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


def _close_edit_test_dialog():
    """Fecha o modal de edição e limpa seu estado auxiliar."""
    st.session_state.edit_test_id = None
    st.session_state.edit_test_dialog_context = None
    st.session_state.edit_test_dialog_token = None


def _prepare_edit_test_dialog_state(test_id):
    """Gera token novo quando um teste é aberto no modal de edição."""
    if st.session_state.get("edit_test_dialog_context") != test_id:
        st.session_state.edit_test_dialog_context = test_id
        st.session_state.edit_test_dialog_token = uuid.uuid4().hex[:8]

    return st.session_state.get("edit_test_dialog_token") or uuid.uuid4().hex[:8]


def _build_date_mismatch_warning(csv_date, weather_data, t):
    """Retorna alerta de data incompatível entre CSV e meteo, se necessário."""
    if not weather_data or csv_date is None:
        return None

    meteo_dates = sorted({
        item["timestamp"].date()
        for item in weather_data
        if item.get("timestamp") is not None
    })
    if not meteo_dates or csv_date in meteo_dates:
        return None

    meteo_date_text = ", ".join(date.strftime("%d/%m/%Y") for date in meteo_dates[:3])
    if len(meteo_dates) > 3:
        meteo_date_text += "..."

    return t(
        "date_mismatch_warning",
        data_csv=csv_date.strftime("%d/%m/%Y"),
        data_meteo=meteo_date_text
    )


def _sync_meteo_mode_changed(test_id, sync_enabled):
    """Salva modo de sincronizacao meteo e invalida resultados dependentes."""
    test_data = st.session_state.tests.get(test_id)
    if test_data is None:
        return

    previous = bool(test_data.get("sync_meteo_by_time_only", False))
    if previous == sync_enabled:
        return

    test_data["sync_meteo_by_time_only"] = sync_enabled
    _clear_test_data_for_meteo_change(test_data)

    for key in (
        "split_final_results",
        "excel_buffer",
    ):
        value = test_data.get(key, TEST_DEFAULTS.get(key))
        st.session_state[key] = copy.deepcopy(value) if isinstance(value, (dict, list)) else value


def _load_uploaded_csv_file(uploaded_csv, t, using_split_method=False, is_alta=True):
    """Valida e carrega um CSV de coastdown em estruturas temporárias."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as tmp:
        tmp.write(uploaded_csv.getvalue())
        tmp_path = tmp.name

    try:
        df_raw, all_run_data, csv_date = carregar_dados_csv_robusto(
            tmp_path,
            using_split_method=using_split_method,
            is_alta=is_alta,
        )
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    if df_raw is None or not all_run_data:
        raise ValueError(t("invalid_csv_file"))

    return df_raw, all_run_data, csv_date


def _load_uploaded_meteo_file(uploaded_meteo, t):
    """Validate and load a neutral CSV/XLSX weather file."""
    suffix = os.path.splitext(uploaded_meteo.name)[1].lower() or ".csv"
    with tempfile.NamedTemporaryFile(mode="wb", suffix=suffix, delete=False) as tmp:
        tmp.write(uploaded_meteo.getvalue())
        tmp_path = tmp.name

    try:
        weather_data = read_weather_file(tmp_path)
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    if not weather_data:
        raise ValueError(t("invalid_meteo_file"))

    return weather_data


def _uploaded_file_sha256(uploaded_file):
    """Return a content hash for uploaded files used in Split traceability."""
    if uploaded_file is None:
        return None
    return hashlib.sha256(uploaded_file.getvalue()).hexdigest()


def _normalize_split_input_mode(value, test_data=None):
    """Return canonical Split input mode: separate or combined."""
    if value in {"combined", "single_combined", "full_or_combined"}:
        return "combined"
    if value == "separate":
        return "separate"
    if test_data and (test_data.get("split_baixa_csv_path") or _find_split_source(test_data, "low")):
        return "separate"
    if test_data and test_data.get("coastdown_csv_path") and not test_data.get("split_alta_csv_path"):
        return "combined"
    return "separate"


def _legacy_split_input_layout(input_mode):
    """Map canonical input mode to the previous layout value for compatibility."""
    return "single_combined" if input_mode == "combined" else "separate"


def _build_split_coastdown_state(high_or_combined_csv, low_csv, input_mode, t):
    """Load Split coastdown files and return state fields for the active test."""
    input_mode = _normalize_split_input_mode(input_mode)
    is_combined = input_mode == "combined"
    df_raw, high_or_combined_runs, csv_date = _load_uploaded_csv_file(
        high_or_combined_csv,
        t,
        using_split_method=True,
        is_alta=True,
    )

    split_input_sources = []
    split_source_files = [high_or_combined_csv.name]
    combined_run_data = {
        f"main:{run_id}": data
        for run_id, data in high_or_combined_runs.items()
    }
    df_raw_alta = None
    df_raw_baixa = None
    all_run_data_alta = {}
    all_run_data_baixa = {}

    if is_combined:
        split_input_sources.append(
            {
                "filename": high_or_combined_csv.name,
                "content_sha256": _uploaded_file_sha256(high_or_combined_csv),
                "role": "full_or_combined",
                "all_run_data": high_or_combined_runs,
            }
        )
    else:
        df_raw_alta = df_raw
        all_run_data_alta = high_or_combined_runs
        split_input_sources.append(
            {
                "filename": high_or_combined_csv.name,
                "content_sha256": _uploaded_file_sha256(high_or_combined_csv),
                "role": "high",
                "all_run_data": all_run_data_alta,
            }
        )

        if low_csv is not None:
            df_raw_baixa, all_run_data_baixa, _ = _load_uploaded_csv_file(
                low_csv,
                t,
                using_split_method=True,
                is_alta=False,
            )
            split_input_sources.append(
                {
                    "filename": low_csv.name,
                    "content_sha256": _uploaded_file_sha256(low_csv),
                    "role": "low",
                    "all_run_data": all_run_data_baixa,
                }
            )
            split_source_files.append(low_csv.name)
            combined_run_data.update(
                {f"low:{run_id}": data for run_id, data in all_run_data_baixa.items()}
            )

    return {
        "df_raw": df_raw,
        "df_raw_alta": df_raw_alta,
        "df_raw_baixa": df_raw_baixa,
        "all_run_data": combined_run_data,
        "all_run_data_alta": all_run_data_alta,
        "all_run_data_baixa": all_run_data_baixa,
        "split_input_sources": split_input_sources,
        "split_source_files": split_source_files,
        "coastdown_csv_path": high_or_combined_csv.name,
        "split_alta_csv_path": high_or_combined_csv.name if not is_combined else None,
        "split_baixa_csv_path": low_csv.name if low_csv is not None else None,
        "split_input_mode": input_mode,
        "split_input_layout": _legacy_split_input_layout(input_mode),
        "data_loaded": True,
        "data_info": {
            "filename": high_or_combined_csv.name,
            "split_files": ", ".join(split_source_files),
            "rows": len(df_raw),
            "runs": len(combined_run_data),
        },
        "csv_test_date": csv_date,
    }


def _find_split_source(test_data, role):
    """Return the stored Split source for a given role."""
    for source in test_data.get("split_input_sources", []) or []:
        if source.get("role") == role:
            return source
    return None


def _build_split_state_from_loaded(
    high_filename,
    high_hash,
    high_df,
    high_runs,
    low_filename=None,
    low_hash=None,
    low_df=None,
    low_runs=None,
    csv_date=None,
):
    """Build separate high/low Split state from already-loaded run data."""
    low_runs = low_runs or {}
    split_input_sources = [
        {
            "filename": high_filename,
            "content_sha256": high_hash,
            "role": "high",
            "all_run_data": high_runs,
        }
    ]
    split_source_files = [high_filename]
    combined_run_data = {f"main:{run_id}": data for run_id, data in high_runs.items()}

    if low_filename and low_runs:
        split_input_sources.append(
            {
                "filename": low_filename,
                "content_sha256": low_hash,
                "role": "low",
                "all_run_data": low_runs,
            }
        )
        split_source_files.append(low_filename)
        combined_run_data.update({f"low:{run_id}": data for run_id, data in low_runs.items()})

    return {
        "df_raw": high_df,
        "df_raw_alta": high_df,
        "df_raw_baixa": low_df if low_filename else None,
        "all_run_data": combined_run_data,
        "all_run_data_alta": high_runs,
        "all_run_data_baixa": low_runs if low_filename else {},
        "split_input_sources": split_input_sources,
        "split_source_files": split_source_files,
        "coastdown_csv_path": high_filename,
        "split_alta_csv_path": high_filename,
        "split_baixa_csv_path": low_filename,
        "split_input_mode": "separate",
        "split_input_layout": "separate",
        "data_loaded": True,
        "data_info": {
            "filename": high_filename,
            "split_files": ", ".join(split_source_files),
            "rows": len(high_df),
            "runs": len(combined_run_data),
        },
        "csv_test_date": csv_date,
    }


def _clear_test_data_for_csv_change(test_data):
    """Limpa estruturas derivadas que dependem diretamente do CSV."""
    invalidate_split_input_state(test_data)


def _clear_test_data_for_meteo_change(test_data):
    """Limpa estruturas derivadas que dependem de correções climáticas e pares."""
    clear_split_final_state(test_data)


def _apply_test_edits(
    test_id,
    new_name,
    selected_input_mode,
    uploaded_high_csv,
    uploaded_low_csv,
    remove_low,
    uploaded_meteo,
    remove_meteo,
    t,
):
    """Aplica edição segura do teste somente após validar novos arquivos."""
    with st.spinner(t("loading_files")):
        try:
            save_active_test_state()

            original_test = st.session_state.tests.get(test_id)
            if original_test is None:
                st.error(t("file_load_error"))
                return

            updated_test = copy.deepcopy(original_test)
            updated_test["name"] = new_name

            current_input_mode = _normalize_split_input_mode(
                updated_test.get("split_input_mode") or updated_test.get("split_input_layout"),
                updated_test,
            )
            selected_input_mode = _normalize_split_input_mode(selected_input_mode, updated_test)
            mode_changed = selected_input_mode != current_input_mode

            csv_changed = any((uploaded_high_csv is not None, uploaded_low_csv is not None, remove_low, mode_changed))
            meteo_removed = bool(remove_meteo and original_test.get("meteo_csv_path"))
            meteo_changed = uploaded_meteo is not None or meteo_removed

            if csv_changed:
                if selected_input_mode == "combined":
                    if uploaded_low_csv is not None or remove_low:
                        raise ValueError(t("split_combined_low_edit_not_available"))
                    if uploaded_high_csv is None and mode_changed:
                        raise ValueError(t("split_replace_combined_required"))
                    if uploaded_high_csv is not None:
                        updated_test.update(
                            _build_split_coastdown_state(uploaded_high_csv, None, "combined", t)
                        )
                    else:
                        updated_test["split_input_mode"] = "combined"
                        updated_test["split_input_layout"] = _legacy_split_input_layout("combined")
                else:
                    if mode_changed and uploaded_high_csv is None:
                        raise ValueError(t("split_high_file_required"))
                    high_source = _find_split_source(updated_test, "high")
                    if uploaded_high_csv is not None:
                        high_df, high_runs, csv_date = _load_uploaded_csv_file(
                            uploaded_high_csv,
                            t,
                            using_split_method=True,
                            is_alta=True,
                        )
                        high_filename = uploaded_high_csv.name
                        high_hash = _uploaded_file_sha256(uploaded_high_csv)
                    else:
                        high_df = updated_test.get("df_raw_alta") or updated_test.get("df_raw")
                        high_runs = updated_test.get("all_run_data_alta") or (
                            high_source.get("all_run_data") if high_source else {}
                        )
                        high_filename = updated_test.get("split_alta_csv_path") or updated_test.get("coastdown_csv_path")
                        high_hash = high_source.get("content_sha256") if high_source else None
                        csv_date = updated_test.get("csv_test_date")

                    if not high_filename or high_df is None or not high_runs:
                        raise ValueError(t("split_high_file_required"))

                    low_source = _find_split_source(updated_test, "low")
                    if remove_low:
                        low_filename = None
                        low_hash = None
                        low_df = None
                        low_runs = {}
                    elif uploaded_low_csv is not None:
                        low_df, low_runs, _ = _load_uploaded_csv_file(
                            uploaded_low_csv,
                            t,
                            using_split_method=True,
                            is_alta=False,
                        )
                        low_filename = uploaded_low_csv.name
                        low_hash = _uploaded_file_sha256(uploaded_low_csv)
                    elif mode_changed:
                        low_filename = None
                        low_hash = None
                        low_df = None
                        low_runs = {}
                    else:
                        low_filename = updated_test.get("split_baixa_csv_path")
                        low_hash = low_source.get("content_sha256") if low_source else None
                        low_df = updated_test.get("df_raw_baixa")
                        low_runs = updated_test.get("all_run_data_baixa") or (
                            low_source.get("all_run_data") if low_source else {}
                        )

                    updated_test.update(
                        _build_split_state_from_loaded(
                            high_filename,
                            high_hash,
                            high_df,
                            high_runs,
                            low_filename=low_filename,
                            low_hash=low_hash,
                            low_df=low_df,
                            low_runs=low_runs,
                            csv_date=csv_date,
                        )
                    )

                _clear_test_data_for_csv_change(updated_test)
                if uploaded_high_csv is not None or mode_changed:
                    st.session_state.split_high_uploader_key_version += 1
                if uploaded_low_csv is not None or remove_low or mode_changed:
                    st.session_state.split_low_uploader_key_version += 1

            if uploaded_meteo is not None:
                updated_test["weather_data"] = _load_uploaded_meteo_file(uploaded_meteo, t)
                updated_test["meteo_csv_path"] = uploaded_meteo.name
                updated_test["split_meteo_csv_path"] = uploaded_meteo.name
                st.session_state.split_weather_uploader_key_version += 1
            elif meteo_removed:
                updated_test["weather_data"] = None
                updated_test["meteo_csv_path"] = None
                updated_test["split_meteo_csv_path"] = None
                updated_test["weather_data_split"] = None
                st.session_state.split_weather_uploader_key_version += 1

            if meteo_changed:
                _clear_test_data_for_meteo_change(updated_test)
                updated_test["sync_meteo_by_time_only"] = False
            elif csv_changed:
                updated_test["sync_meteo_by_time_only"] = False

            updated_test["date_mismatch_warning"] = _build_date_mismatch_warning(
                updated_test.get("csv_test_date"),
                updated_test.get("weather_data"),
                t
            )
            if not updated_test["date_mismatch_warning"]:
                updated_test["sync_meteo_by_time_only"] = False

            st.session_state.tests[test_id] = updated_test

            if st.session_state.active_test_id == test_id:
                load_test_state(test_id)

            _close_edit_test_dialog()
            st.rerun()

        except Exception as e:
            st.error(f"{t('file_load_error')}: {str(e)}")


def confirm_delete_dialog(t):
    """Exibe modal de confirmação para remover um teste."""
    test_id = st.session_state.get("delete_confirm_id")
    if not test_id:
        st.rerun()

    if test_id not in st.session_state.tests:
        st.session_state.delete_confirm_id = None
        st.rerun()

    @st.dialog(t("confirm_remove_title"), width="small")
    def _confirm_delete_dialog():
        st.write(t("confirm_delete_test"))

        c1, c2 = st.columns(2)
        with c1:
            if st.button(
                t("confirm"),
                key="confirm_delete_modal_confirm",
                type="primary",
                use_container_width=True,
            ):
                delete_test(test_id)
                st.rerun()
        with c2:
            if st.button(
                t("cancel"),
                key="confirm_delete_modal_cancel",
                use_container_width=True,
            ):
                st.session_state.delete_confirm_id = None
                st.rerun()

    _confirm_delete_dialog()


def edit_test_dialog(t):
    """Exibe modal para editar nome e arquivos de um teste existente."""
    save_active_test_state()

    test_id = st.session_state.get("edit_test_id")
    if not test_id:
        st.rerun()

    test_data = st.session_state.tests.get(test_id)
    if test_data is None:
        _close_edit_test_dialog()
        st.rerun()

    dialog_token = _prepare_edit_test_dialog_state(test_id)
    current_name = test_data.get("name", test_id)
    current_input_mode = _normalize_split_input_mode(
        test_data.get("split_input_mode") or test_data.get("split_input_layout"),
        test_data,
    )
    current_high = test_data.get("split_alta_csv_path")
    current_combined = test_data.get("coastdown_csv_path")
    current_low = test_data.get("split_baixa_csv_path")
    current_meteo = test_data.get("meteo_csv_path") or t("no_meteo_file")
    high_key_version = st.session_state.get("split_high_uploader_key_version", 0)
    low_key_version = st.session_state.get("split_low_uploader_key_version", 0)
    weather_key_version = st.session_state.get("split_weather_uploader_key_version", 0)
    has_current_meteo = bool(test_data.get("meteo_csv_path"))

    @st.dialog(t("edit_test_title"), width="large", on_dismiss=_close_edit_test_dialog)
    def _edit_test_dialog():
        st.write(f"**{t('test_name')}:** {current_name}")
        st.write(f"**{t('split_input_mode')}:** {t(f'split_input_mode_{current_input_mode}')}")
        if current_input_mode == "combined":
            st.write(f"**{t('split_current_combined_file')}:** {current_combined or 'N/A'}")
        else:
            st.write(f"**{t('split_current_high_file')}:** {current_high or 'N/A'}")
            st.write(f"**{t('split_current_low_file')}:** {current_low or t('split_no_low_file')}")
        st.write(f"**{t('split_current_weather_file')}:** {current_meteo}")

        st.markdown("---")

        updated_name = st.text_input(
            t("test_name"),
            value=current_name,
            key=f"edit_test_name_{dialog_token}"
        )

        st.markdown("---")

        mode_label_to_value = {
            t("split_input_mode_separate"): "separate",
            t("split_input_mode_combined"): "combined",
        }
        mode_labels = list(mode_label_to_value.keys())
        current_mode_label = next(
            label for label, value in mode_label_to_value.items()
            if value == current_input_mode
        )
        selected_mode_label = st.radio(
            t("split_input_mode"),
            options=mode_labels,
            index=mode_labels.index(current_mode_label),
            horizontal=True,
            key=f"edit_split_input_mode_{dialog_token}",
        )
        selected_input_mode = mode_label_to_value[selected_mode_label]
        mode_changed = selected_input_mode != current_input_mode

        if mode_changed:
            st.warning(t("warning_change_split_input_mode"))

        st.markdown("---")

        high_label = (
            t("split_replace_combined_csv")
            if selected_input_mode == "combined"
            else t("split_replace_high_csv")
        )
        uploaded_high_csv = st.file_uploader(
            high_label,
            type=["csv"],
            key=f"edit_split_high_{dialog_token}_{high_key_version}"
        )

        uploaded_low_csv = None
        remove_low = False
        if selected_input_mode == "separate":
            uploaded_low_csv = st.file_uploader(
                t("split_replace_low_csv") if current_low else t("split_add_low_csv"),
                type=["csv"],
                key=f"edit_split_low_{dialog_token}_{low_key_version}",
            )
            if current_low:
                remove_low = st.checkbox(
                    t("split_remove_low_file"),
                    key=f"edit_split_remove_low_{dialog_token}_{low_key_version}",
                    disabled=uploaded_low_csv is not None,
                )

        meteo_label = t("replace_meteo") if has_current_meteo else t("add_meteo")
        uploaded_meteo = st.file_uploader(
            meteo_label,
            type=["csv", "xlsx"],
            key=f"edit_test_meteo_{dialog_token}_{weather_key_version}"
        )

        remove_meteo = False
        if has_current_meteo:
            remove_meteo = st.checkbox(
                t("remove_meteo"),
                key=f"edit_test_remove_meteo_{dialog_token}",
                disabled=uploaded_meteo is not None
            )

        csv_changed = uploaded_high_csv is not None or uploaded_low_csv is not None or remove_low or mode_changed
        meteo_changed = uploaded_meteo is not None or remove_meteo
        name_changed = updated_name.strip() != current_name
        mode_change_missing_file = mode_changed and uploaded_high_csv is None

        if csv_changed:
            st.warning(t("warning_replace_csv"))
        if mode_change_missing_file:
            st.info(t("split_input_mode_change_requires_file"))

        if meteo_changed:
            st.warning(t("warning_replace_meteo"))

        confirm_csv = True
        confirm_meteo = True

        if csv_changed:
            confirm_csv = st.checkbox(
                t("confirm_replace_csv_understand"),
                key=f"edit_test_confirm_csv_{dialog_token}"
            )

        if meteo_changed:
            confirm_meteo = st.checkbox(
                t("confirm_replace_meteo_understand"),
                key=f"edit_test_confirm_meteo_{dialog_token}"
            )

        has_changes = name_changed or csv_changed or meteo_changed
        valid_name = bool(updated_name.strip())
        save_disabled = (
            (not has_changes)
            or (not valid_name)
            or (not confirm_csv)
            or (not confirm_meteo)
            or mode_change_missing_file
        )

        if not has_changes:
            st.info(t("no_changes_detected"))

        st.markdown("---")

        c1, c2 = st.columns(2)
        with c1:
            if st.button(
                t("cancel"),
                key=f"edit_test_cancel_{dialog_token}",
                use_container_width=True
            ):
                _close_edit_test_dialog()
                st.rerun()
        with c2:
            if st.button(
                t("save_changes"),
                key=f"edit_test_save_{dialog_token}",
                type="primary",
                use_container_width=True,
                disabled=save_disabled
            ):
                _apply_test_edits(
                    test_id,
                    updated_name.strip(),
                    selected_input_mode,
                    uploaded_high_csv,
                    uploaded_low_csv,
                    remove_low,
                    uploaded_meteo,
                    remove_meteo,
                    t
                )

    _edit_test_dialog()


# ===== RENDERIZAÇÃO DA SIDEBAR =====

def render_sidebar(t):
    """Renderiza a sidebar completa: idioma, testes e navegação."""

    render_optional_app_logo()
    render_optional_hyundai_brand()

    # ---- Título ----
    st.markdown("## Coastdown MDA Split")

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
        _close_edit_test_dialog()
        st.session_state.language = new_lang
        st.rerun()

    # ---- Seletor de tamanho de fonte ----
    font_values = ["small", "medium", "large"]
    font_labels = [t("font_small"), t("font_medium"), t("font_large")]
    current_font = st.session_state.get("font_size", "medium")
    current_font_idx = font_values.index(current_font) if current_font in font_values else 1

    selected_font_label = st.selectbox(
        t("font_size"),
        options=font_labels,
        index=current_font_idx,
        key="font_size_selector"
    )
    new_font = font_values[font_labels.index(selected_font_label)]
    if new_font != current_font:
        _close_edit_test_dialog()
        st.session_state.font_size = new_font
        st.rerun()

    st.markdown("---")

    # ---- Botão "+ Novo Teste" ----
    if st.button(f"+ {t('new_test')}", use_container_width=True, type="primary"):
        new_test_dialog(t)

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

    csv_sym = "✓" if csv_ok else "✗"
    meteo_sym = "✓" if meteo_ok else "⚠"
    status_text = f"CSV: {csv_sym}   Meteo: {meteo_sym}"
    card_key = (
        f"test_card_active_{test_id}"
        if is_active
        else f"test_card_inactive_{test_id}"
    )

    with st.container(border=True, key=card_key):
        col_info, col_delete = st.columns([0.82, 0.18], vertical_alignment="top")

        with col_info:
            st.markdown(f"**{name}**")

            if is_active:
                st.caption(f"● {t('active_test').upper()}")
            else:
                if st.button(t("switch_test"), key=f"sel_{test_id}"):
                    activate_test(test_id)
                    st.rerun()
            st.caption(status_text)

        with col_delete:
            with st.container(key=f"delete_btn_{test_id}"):
                if st.button("✕", key=f"del_{test_id}", help=t("remove_test")):
                    st.session_state.delete_confirm_id = test_id
                    st.rerun()
            with st.container(key=f"edit_btn_{test_id}"):
                if st.button("🛠", key=f"edit_{test_id}", help=t("edit_test_title")):
                    st.session_state.edit_test_id = test_id
                    st.rerun()

    st.markdown("")

def render_sidebar_status(t):
    """Renderiza status resumido do teste ativo na sidebar."""
    st.markdown(
        f"<p class='mda-sidebar-status-label'>{t('status').upper()}</p>",
        unsafe_allow_html=True
    )

    if st.session_state.data_loaded:
        runs = len(st.session_state.all_run_data)
        st.markdown(
            f"<div class='mda-sidebar-status-item' style='color:#4caf50'>"
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
            f"<div class='mda-sidebar-status-item' style='color:#4caf50'>"
            f"✅ {t('vehicle_information')}{mass_str}</div>",
            unsafe_allow_html=True
        )

    if st.session_state.split_results:
        n = len(st.session_state.split_results)
        st.markdown(
            f"<div class='mda-sidebar-status-item' style='color:#4caf50'>"
            f"✅ {n} {t('split_saved_results')}</div>",
            unsafe_allow_html=True
        )

    if st.session_state.split_final_results:
        n = st.session_state.split_final_results.get("num_results", 0)
        st.markdown(
            f"<div class='mda-sidebar-status-item' style='color:#4a9eff'>"
            f"{n} {t('split_final_summary')}</div>",
            unsafe_allow_html=True
        )


# ===== ÁREA PRINCIPAL =====

def render_welcome(t):
    """Renderiza a tela de boas-vindas quando não há testes ativos."""
    st.title("Coastdown MDA Split")
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
            new_test_dialog(t)


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

    # Upload dos arquivos CSV do Split
    st.subheader(t("split_upload_sources"))
    mode_label_to_value = {
        t("split_input_mode_separate"): "separate",
        t("split_input_mode_combined"): "combined",
    }
    selected_mode_label = st.radio(
        t("split_input_mode"),
        options=list(mode_label_to_value.keys()),
        horizontal=True,
        key="new_test_split_input_mode",
    )
    split_input_mode = mode_label_to_value[selected_mode_label]

    uploaded_csv = st.file_uploader(
        t("split_upload_combined_csv") if split_input_mode == "combined" else t("split_upload_high_csv"),
        type=["csv"],
        key="new_test_csv_upload",
    )
    uploaded_low_csv = None
    if split_input_mode == "separate":
        uploaded_low_csv = st.file_uploader(
            t("split_upload_low_csv"),
            type=["csv"],
            key="new_test_low_csv_upload",
        )

    st.markdown("---")

    # Upload do arquivo meteorológico (opcional)
    st.subheader(f"📊 {t('upload_weather_csv')}")
    uploaded_meteo = st.file_uploader(
        t("upload_weather_csv"),
        type=["csv", "xlsx"],
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
                uploaded_low_csv,
                split_input_mode,
                uploaded_meteo,
                fixed_temp,
                fixed_pressure,
                t
            )


def _process_new_test(name, uploaded_csv, uploaded_low_csv, split_input_mode, uploaded_meteo, fixed_temp, fixed_pressure, t):
    """
    Processa os arquivos carregados e cria o novo teste no session_state.
    Salva o estado do teste ativo atual antes de criar o novo.
    """
    with st.spinner(t("loading_files")):
        try:
            coastdown_state = _build_split_coastdown_state(
                uploaded_csv,
                uploaded_low_csv if split_input_mode == "separate" else None,
                split_input_mode,
                t,
            )

            # Processa arquivo meteorológico se fornecido
            weather_data = None
            meteo_name = None
            date_mismatch_warning = None
            if uploaded_meteo is not None:
                weather_data = _load_uploaded_meteo_file(uploaded_meteo, t)
                meteo_name = uploaded_meteo.name
                date_mismatch_warning = _build_date_mismatch_warning(
                    coastdown_state.get("csv_test_date"),
                    weather_data,
                    t,
                )

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
                **coastdown_state,
                # Dados meteorológicos
                "weather_data": weather_data,
                "meteo_csv_path": meteo_name,
                "split_meteo_csv_path": meteo_name,
                "fixed_temperature": fixed_temp,
                "fixed_pressure": fixed_pressure,
                "using_split_method": True,
                "test_method": "split",
                # Alerta de data incompatível (None se datas coincidem)
                "date_mismatch_warning": date_mismatch_warning,
                # Começa pela página de dados do veículo
                "current_page": "2_dados_veiculo",
            })

            # Registra o teste no dicionário de testes
            st.session_state.tests[test_id] = new_test_data

            # Ativa o novo teste (carrega seus dados nas flat keys)
            load_test_state(test_id)
            st.session_state.active_test_id = test_id

            st.rerun()

        except Exception as e:
            st.error(f"{t('file_load_error')}: {str(e)}")


def render_test_analysis(t):
    """Renderiza a análise do teste ativo com navegação por abas."""
    active_test = st.session_state.tests.get(st.session_state.active_test_id, {})
    test_name = active_test.get("name", "Teste")

    st.title(test_name)

    # Mostra alerta de data incompatível se existir
    warning_msg = st.session_state.get("date_mismatch_warning")
    if warning_msg:
        st.warning(warning_msg)
        st.caption(t("sync_meteo_time_only_help"))
        sync_enabled = st.checkbox(
            t("sync_meteo_time_only_label"),
            key="sync_meteo_by_time_only"
        )
        _sync_meteo_mode_changed(st.session_state.active_test_id, sync_enabled)
        if sync_enabled:
            st.info(t("sync_meteo_time_only_active"))

    tab_pages = [
        ("2_dados_veiculo", t("page_vehicle_data")),
        ("split_workflow", t("page_split_workflow")),
        ("split_coefficient_calculation", t("page_split_pair_analysis")),
        ("split_final_comparison", t("page_split_final_comparison")),
        ("split_results", t("page_split_results")),
    ]
    tab_labels = [label for _, label in tab_pages]
    page_to_label = dict(tab_pages)
    label_to_page = {label: page_id for page_id, label in tab_pages}

    tab_key = f"main_analysis_tabs_{st.session_state.active_test_id}_{st.session_state.language}"
    if st.session_state.pop("navigate_to_results", False):
        st.session_state.current_page = "split_results"
        st.session_state[tab_key] = page_to_label["split_results"]

    current_page = st.session_state.get("current_page", "2_dados_veiculo")
    default_label = page_to_label.get(current_page, tab_labels[0])
    if st.session_state.get(tab_key) not in label_to_page:
        st.session_state[tab_key] = default_label

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        tab_labels,
        default=st.session_state[tab_key],
        key=tab_key,
        on_change="rerun",
    )

    selected_page = label_to_page.get(st.session_state.get(tab_key))
    if selected_page:
        st.session_state.current_page = selected_page

    with tab1:
        from pages import page_2_dados_veiculo
        page_2_dados_veiculo.render(t)

    with tab2:
        from pages import page_split_workflow
        page_split_workflow.render(t)

    with tab3:
        from pages import page_split_coefficient_calculation
        page_split_coefficient_calculation.render(t)

    with tab4:
        from pages import page_split_final_comparison
        page_split_final_comparison.render(t)

    with tab5:
        from pages import page_split_results
        page_split_results.render(t)


# ===== PONTO DE ENTRADA =====

init_session_state()

apply_font_size_css(st.session_state.get("font_size", "medium"))

# Obtém a função de tradução para o idioma atual
t = get_translator(st.session_state.language)

# Renderiza sidebar
with st.sidebar:
    render_sidebar(t)

if st.session_state.get("delete_confirm_id"):
    confirm_delete_dialog(t)

if st.session_state.get("edit_test_id"):
    edit_test_dialog(t)

# Renderiza área principal conforme estado
if not st.session_state.active_test_id:
    render_welcome(t)
else:
    render_test_analysis(t)
