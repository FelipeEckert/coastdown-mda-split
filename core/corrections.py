# coding: utf-8
"""
Funções de correção climática para análise de coastdown.

Este módulo contém todas as funções de correção climática
dos coeficientes F0 e F2.

IMPORTANTE: Não altere os nomes das funções ou variáveis para manter compatibilidade.
"""

import statistics
from .calculations import calcular_energia


def apply_climate_correction(
    f0_raw: float,
    f2_raw: float,
    temp_c: float,
    press_kpa: float
) -> tuple:
    """
    Aplica correção climática aos coeficientes F0 e F2.
    
    Args:
        f0_raw: Coeficiente F0 bruto
        f2_raw: Coeficiente F2 bruto
        temp_c: Temperatura em Celsius
        press_kpa: Pressão em kPa
        
    Returns:
        tuple: (f0_corrected, f2_corrected)
    """
    # Constantes de correção climática
    T0 = 293.15  # 20°C em Kelvin
    P0 = 101.325 # Pressão padrão em kPa
    Kt = 0.0086
    Kp = 0.0002503

    # Fatores de correção
    f0_corrected = f0_raw * (1 + Kt * ((temp_c + 273.15) - T0))
    f2_corrected = (((P0 * (temp_c + 273.15)) / (press_kpa * T0)) * (f2_raw - Kp * f0_raw) +
                            (Kp * f0_corrected)) / 12.96

    return f0_corrected, f2_corrected


def _calculate_single_pair_corrected_data(
    run_ida_id: int, 
    run_volta_id: int, 
    individual_coeffs: dict, 
    temp_ida_c: float,
    press_ida_kpa: float,
    temp_volta_c: float,
    press_volta_kpa: float,
    energy_calculator
) -> dict:
    """
    Calcula os coeficientes corrigidos e a energia para um par de runs,
    dada a temperatura e pressão.

    Args:
        run_ida_id: ID da run de ida.
        run_volta_id: ID da run de volta.
        individual_coeffs: Dicionário com os coeficientes individuais de todas as runs.
        temp_ida_c: Temperatura em Celsius para correção da ida.
        press_ida_kpa: Pressão em kPa para correção da ida.
        temp_volta_c: Temperatura em Celsius para correção da volta.
        press_volta_kpa: Pressão em kPa para correção da volta.

    Returns:
        Um dicionário contendo todos os coeficientes brutos, corrigidos, médias, CVs e energia.
    """
    # Obter f0 e f2 brutos para as runs de ida e volta
    f0_ida_raw = individual_coeffs.get(run_ida_id, {}).get("f0", 0.0)
    f2_ida_raw = individual_coeffs.get(run_ida_id, {}).get("f2", 0.0)
    f0_volta_raw = individual_coeffs.get(run_volta_id, {}).get("f0", 0.0)
    f2_volta_raw = individual_coeffs.get(run_volta_id, {}).get("f2", 0.0)

    # Constantes de correção climática (extraídas do seu código)
    T0 = 293.15  # 20°C em Kelvin
    P0 = 101.325 # Pressão padrão em kPa
    Kt = 0.0086
    Kp = 0.0002503

    # Fatores de correção para Run IDA
    f0_ida_corr = f0_ida_raw * (1 + Kt * ((temp_ida_c + 273.15) - T0))
    f2_ida_corr = (((P0 * (temp_ida_c + 273.15)) / (press_ida_kpa * T0)) * (f2_ida_raw - Kp * f0_ida_raw) +
                            (Kp * f0_ida_corr)) / 12.96

    # Fatores de correção para Run VOLTA
    f0_volta_corr = f0_volta_raw * (1 + Kt * ((temp_volta_c + 273.15) - T0))
    f2_volta_corr = (((P0 * (temp_volta_c + 273.15)) / (press_volta_kpa * T0)) * (f2_volta_raw - Kp * f0_volta_raw) +
                             (Kp * f0_volta_corr)) / 12.96

    # Médias dos coeficientes corrigidos
    f0_values_corrected = [f0_ida_corr, f0_volta_corr]
    f2_values_corrected = [f2_ida_corr, f2_volta_corr]

    mean_f0_corrected = statistics.mean(f0_values_corrected)
    mean_f2_corrected = statistics.mean(f2_values_corrected)

    # CVs dos coeficientes corrigidos
    cv_f0_corrected = (statistics.stdev(f0_values_corrected) / mean_f0_corrected) * 100 if len(f0_values_corrected) > 1 and mean_f0_corrected != 0 else 0.0
    cv_f2_corrected = (statistics.stdev(f2_values_corrected) / mean_f2_corrected) * 100 if len(f2_values_corrected) > 1 and mean_f2_corrected != 0 else 0.0

    # Energia
    mean_energy_corrected = energy_calculator(
        mean_f0_corrected,
        mean_f2_corrected,
    )

    return {
        'pair_id': f"{run_ida_id}/{run_volta_id}", # Adicionado para compatibilidade
        'run1': run_ida_id, # Adicionado para compatibilidade
        'run2': run_volta_id, # Adicionado para compatibilidade
        'f0_ida_raw': f0_ida_raw,
        'f2_ida_raw': f2_ida_raw,
        'f0_volta_raw': f0_volta_raw,
        'f2_volta_raw': f2_volta_raw,
        'f0_ida_corr': f0_ida_corr,
        'f2_ida_corr': f2_ida_corr,
        'f0_volta_corr': f0_volta_corr,
        'f2_volta_corr': f2_volta_corr,
        'mean_f0_corrected': mean_f0_corrected,
        'mean_f2_corrected': mean_f2_corrected,
        'cv_f0_corrected': cv_f0_corrected,
        'cv_f2_corrected': cv_f2_corrected,
        'energy': mean_energy_corrected,
        'mean_energy_corrected': mean_energy_corrected,
        #'temp': temp_c,
        #'press': press_kpa,
        "temp_ida_used": temp_ida_c,
        "temp_volta_used": temp_volta_c,
        "press_ida_used": press_ida_kpa,
        "press_volta_used": press_volta_kpa,
        "f0_mean": mean_f0_corrected, # Mantém como mean_f0_corrected
        "f2_mean": mean_f2_corrected, # Mantém como mean_f2_corrected
        "f0_corr": mean_f0_corrected,  # Mapeia para a chave antiga
        "f2_corr": mean_f2_corrected,  # Mapeia para a chave antiga
        "cv_f0": cv_f0_corrected,      # Mapeia para a chave antiga
        "cv_f2": cv_f2_corrected,      # Mapeia para a chave antiga
        'corrected': True             # Assume que sempre será corrigido nesta função
    }


def calculate_single_pair_corrected_data(
    run_ida_id: int,
    run_volta_id: int,
    individual_coeffs: dict,
    temp_ida_c: float,
    press_ida_kpa: float,
    temp_volta_c: float,
    press_volta_kpa: float
) -> dict:
    """Calculate corrected pair data with this module's energy dependency."""
    return _calculate_single_pair_corrected_data(
        run_ida_id,
        run_volta_id,
        individual_coeffs,
        temp_ida_c,
        press_ida_kpa,
        temp_volta_c,
        press_volta_kpa,
        calcular_energia,
    )


def _calculate_single_pair_corrected_data2(
    f0_ida_raw: float,
    f2_ida_raw: float,
    f0_volta_raw: float,
    f2_volta_raw: float,
    temp_c: float,
    press_kpa: float,
    energy_calculator
) -> dict:
    """Calculate corrected pair data from raw coefficient values."""
    corrected = _calculate_single_pair_corrected_data(
        0,
        1,
        {
            0: {"f0": f0_ida_raw, "f2": f2_ida_raw},
            1: {"f0": f0_volta_raw, "f2": f2_volta_raw},
        },
        temp_c,
        press_kpa,
        temp_c,
        press_kpa,
        energy_calculator,
    )
    return {
        "f0_ida_raw": corrected["f0_ida_raw"],
        "f2_ida_raw": corrected["f2_ida_raw"],
        "f0_volta_raw": corrected["f0_volta_raw"],
        "f2_volta_raw": corrected["f2_volta_raw"],
        "f0_ida_corr": corrected["f0_ida_corr"],
        "f2_ida_corr": corrected["f2_ida_corr"],
        "f0_volta_corr": corrected["f0_volta_corr"],
        "f2_volta_corr": corrected["f2_volta_corr"],
        "mean_f0_corrected": corrected["mean_f0_corrected"],
        "mean_f2_corrected": corrected["mean_f2_corrected"],
        "cv_f0_corrected": corrected["cv_f0_corrected"],
        "cv_f2_corrected": corrected["cv_f2_corrected"],
        "energy": corrected["energy"],
        "temp": temp_c,
        "press": press_kpa,
    }


def calculate_single_pair_corrected_data2(
    f0_ida_raw: float,
    f2_ida_raw: float,
    f0_volta_raw: float,
    f2_volta_raw: float,
    temp_c: float,
    press_kpa: float
) -> dict:
    """Calculate corrected pair data from raw coefficient values."""
    return _calculate_single_pair_corrected_data2(
        f0_ida_raw,
        f2_ida_raw,
        f0_volta_raw,
        f2_volta_raw,
        temp_c,
        press_kpa,
        calcular_energia,
    )
