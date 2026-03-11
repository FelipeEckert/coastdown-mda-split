# coding: utf-8
"""
Módulo core para análise de coastdown.

Contém funções de cálculo e correção climática.
"""

from .calculations import (
    calcular_energia,
    calcular_coeficientes_individuais,
    calcular_coeficientes_split,
    processar_tempos_split,
    calcular_f0_f2_split,
)

from .corrections import (
    apply_climate_correction,
    calculate_single_pair_corrected_data,
    calculate_single_pair_corrected_data2,
)

__all__ = [
    'calcular_energia',
    'calcular_coeficientes_individuais',
    'calcular_coeficientes_split',
    'processar_tempos_split',
    'calcular_f0_f2_split',
    'apply_climate_correction',
    'calculate_single_pair_corrected_data',
    'calculate_single_pair_corrected_data2',
]
