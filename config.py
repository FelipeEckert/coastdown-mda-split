# coding: utf-8
"""
Configurações globais do aplicativo Coastdown Analysis.

Este arquivo contém todas as constantes, fontes e configurações
utilizadas em todo o aplicativo.

IMPORTANTE: Não altere os nomes das variáveis para manter compatibilidade.
"""

from PyQt5.QtGui import QFont

###############################################################################
# FONTES - Mantendo nomes originais
###############################################################################

FONT_TITLE = QFont("Arial", 26, QFont.Bold)
FONT_LABEL = QFont("Arial", 18)
FONT_LABEL_BOLD = QFont("Arial", 18, QFont.Bold)
FONT_INPUT = QFont("Arial", 16)
FONT_BUTTON = QFont("Arial", 16)
FONT_BUTTON_BOLD = QFont("Arial", 20, QFont.Bold)
FONT_TABLE_HEADER = QFont("Arial", 14, QFont.Bold)
FONT_TABLE_CELL = QFont("Arial", 12)
FONT_SUBTAB = QFont("Arial", 14)
FONT_MONO = QFont("Consolas", 14)  # Fonte monoespaçada para resultados

###############################################################################
# TAMANHOS PADRÃO
###############################################################################

BUTTON_MIN_SIZE = (220, 45)
INPUT_MIN_HEIGHT = 36

###############################################################################
# MAPEAMENTO DE CÉLULAS DO TEMPLATE EXCEL
###############################################################################

celulas_template = {
    # Massas e data
    "massa_motorista": "C26",
    "massa_equipamento": "C27",
    "massa_veiculo": "C28",
    "massa_rotacional": "C29",
    "massa_efetiva": "C30",
    "data_teste": "C34",

    # Coeficientes sem correção (5 pares)
    "f0_ida_1": "F107", "f0_volta_1": "F108",
    "f2_ida_1": "H107", "f2_volta_1": "H108",
    "media_f0_1": "J107", "media_f2_1": "L107",

    "f0_ida_2": "F110", "f0_volta_2": "F111",
    "f2_ida_2": "H110", "f2_volta_2": "H111",
    "media_f0_2": "J110", "media_f2_2": "L110",

    "f0_ida_3": "F113", "f0_volta_3": "F114",
    "f2_ida_3": "H113", "f2_volta_3": "H114",
    "media_f0_3": "J113", "media_f2_3": "L113",

    "f0_ida_4": "F116", "f0_volta_4": "F117",
    "f2_ida_4": "H116", "f2_volta_4": "H117",
    "media_f0_4": "J116", "media_f2_4": "L116",

    "f0_ida_5": "F119", "f0_volta_5": "F120",
    "f2_ida_5": "H119", "f2_volta_5": "H120",
    "media_f0_5": "J119", "media_f2_5": "L119",

    # CVs
    "cv_f0": "H123",
    "cv_f2": "O123",

    # Coeficientes corrigidos (5 pares)
    "media_f0_corr_1": "F137", "media_f2_corr_1": "J137", "energia_1": "N137",
    "media_f0_corr_2": "F141", "media_f2_corr_2": "J141", "energia_2": "N141",
    "media_f0_corr_3": "F145", "media_f2_corr_3": "J145", "energia_3": "N145",
    "media_f0_corr_4": "F149", "media_f2_corr_4": "J149", "energia_4": "N149",
    "media_f0_corr_5": "F153", "media_f2_corr_5": "J153", "energia_5": "N153"
}
