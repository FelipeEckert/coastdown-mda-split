# coding: utf-8
"""
Módulo core para análise de coastdown.

Contém funções de cálculo e correção climática.
"""

from .calculations import (
    calcular_energia,
    calcular_coeficientes_individuais,
)

from .corrections import (
    apply_climate_correction,
    calculate_single_pair_corrected_data,
    calculate_single_pair_corrected_data2,
)

from .split_calculations import (
    DEFAULT_SPLIT_INTERVAL_CONFIG,
    calculate_split_coefficients,
    calculate_split_result,
    coefficient_summary,
    delta_v_kmh,
    kmh_to_ms,
    validate_split_inputs,
)

__all__ = [
    'calcular_energia',
    'calcular_coeficientes_individuais',
    'apply_climate_correction',
    'calculate_single_pair_corrected_data',
    'calculate_single_pair_corrected_data2',
    'DEFAULT_SPLIT_INTERVAL_CONFIG',
    'calculate_split_coefficients',
    'calculate_split_result',
    'coefficient_summary',
    'delta_v_kmh',
    'kmh_to_ms',
    'validate_split_inputs',
]
