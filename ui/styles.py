from pathlib import Path
from string import Template

import streamlit as st


_FONT_SIZE_PRESETS = {
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
    },
}

_THEME_PATH = Path(__file__).with_name("theme.css")


def apply_global_styles(font_size_option):
    """Load and apply the global stylesheet with the selected font scale."""
    tokens = _FONT_SIZE_PRESETS.get(
        font_size_option,
        _FONT_SIZE_PRESETS["medium"],
    )
    stylesheet = Template(_THEME_PATH.read_text(encoding="utf-8")).substitute(tokens)
    st.markdown(f"<style>\n{stylesheet}\n</style>", unsafe_allow_html=True)
