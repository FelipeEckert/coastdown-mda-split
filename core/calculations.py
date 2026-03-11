# coding: utf-8
"""
Funções de cálculo para análise de coastdown.

Este módulo contém todas as funções de cálculo de coeficientes,
energia e processamento de dados.

IMPORTANTE: Não altere os nomes das funções ou variáveis para manter compatibilidade.
"""

import numpy as np
import pandas as pd
import statistics


def calcular_energia(f0, f2):
    """
    Calcula a energia combinada a partir dos coeficientes F0 e F2.
    
    Args:
        f0: Coeficiente F0
        f2: Coeficiente F2
        
    Returns:
        float: Energia combinada em MJ/km
    """
    # Constantes conforme planilha original 
    const_F0_city = 79.0100212980278
    const_F2_city = 101261.439856478
    const_F0_hwy = 73.4212978755833
    const_F2_hwy = 190140.972556837
    const_mph0 = 4.4497179
    const_mph2 = 1.7381710546875

    # Calcula energia em MJ/km
    energy_city = ((f0 / const_mph0) * const_F0_city + (f2 / const_mph2) * const_F2_city) / 1000
    energy_hwy = ((f0 / const_mph0) * const_F0_hwy + (f2 / const_mph2) * const_F2_hwy) / 1000
    energy_comb = (energy_city * 0.55) + (energy_hwy * 0.45)
    return energy_comb


def calcular_coeficientes_individuais(all_data, total_mass):
    """
    Calcula os coeficientes F0 e F2 para cada run individual.
    
    Args:
        all_data: Dicionário com dados de todas as runs (times, velocities, heading)
        total_mass: Massa total efetiva do veículo
        
    Returns:
        dict: Dicionário com coeficientes por run
    """
    results = {}
    # all_data agora contém (times, velocities, heading)
    for run, run_data in all_data.items():
        times = run_data["times"]
        velocities = run_data["velocities"]
        heading = run_data["heading"]

        A = 0
        B = 0
        C = 0
        D = 0
        E = 0
        if len(times) != len(velocities):
             print(f"Aviso: Run {run}: Discrepância entre número de tempos ({len(times)}) e velocidades ({len(velocities)}). Pulando run.")
             continue

        iv = len(velocities)
        num_intervals = iv - 1
        if num_intervals <= 0:
            print(f"Aviso: Run {run} tem dados insuficientes ({iv} pontos). Pulando...")
            continue

        valid_intervals = 0
        for i in range(num_intervals):
            Vi = velocities[i]
            Vip1 = velocities[i + 1]
            deltaT = times[i + 1] - times[i]

            if deltaT <= 1e-6:
                print(f"Aviso: Run {run}, Intervalo {i}: deltaT muito pequeno ou zero ({deltaT:.4g}). Pulando intervalo.")
                continue

            # Calcula aceleração e velocidade média no intervalo (em m/s)
            ai = (Vip1 - Vi) / (3.6 * deltaT)
            Vi_mean = (Vip1 + Vi) / (2 * 3.6)
            Vi_sq_mean = (Vi**2 + Vi * Vip1 + Vip1**2) / (3 * (3.6**2))

            if Vi_mean <= 1e-6: # Evita divisão por zero ou valores muito pequenos
                print(f"Aviso: Run {run}, Intervalo {i}: Velocidade média muito pequena ({Vi_mean:.4g}). Pulando intervalo.")
                continue

            # Acumula somas para regressão linear
            A += ai
            B += Vi_mean
            C += Vi_mean ** 2
            D += Vi_mean ** 4
            E += ai * Vi_mean ** 2
            valid_intervals += 1

        iv = len(velocities)
        numerator = (D * A) - (C * E)
        denominator = (iv - 1) * D - (C ** 2)
        numerator2 = ((iv - 1) * E) - (C * A)

        if valid_intervals < 5: # Requer um número mínimo de intervalos válidos
             print(f"Aviso: Run {run} tem poucos intervalos válidos ({valid_intervals}). Pulando cálculo de coeficientes.")
             continue

        # Calcula os coeficientes F0 e F2
        if abs(denominator) < 1e-9: # Evita divisão por zero
            print(f"Aviso: Run {run}: Denominador muito pequeno no cálculo dos coeficientes ({denominator:.4g}). Pulando run.")
            f0 = np.nan
            f2 = np.nan
        else:
            f0 = -(numerator / denominator) * total_mass
            f2 = -(numerator2 / denominator) * total_mass

        # Armazena resultados incluindo o heading
        results[run] = {"f0": f0, "f2": f2, "heading": heading}

    return results


def calcular_coeficientes_split(df_alta, df_baixa, ref_vel_alta, ref_vel_baixa, massa_efetiva):
    """
    Calcula coeficientes para o método Split.
    
    Args:
        df_alta: DataFrame com dados de alta velocidade
        df_baixa: DataFrame com dados de baixa velocidade
        ref_vel_alta: Velocidade de referência alta (km/h)
        ref_vel_baixa: Velocidade de referência baixa (km/h)
        massa_efetiva: Massa efetiva do veículo
        
    Returns:
        tuple: (df_alta, df_baixa) com colunas de delta_t adicionadas
    """
    # Esta função agora apenas extrai os DeltaTs por run e retorna os DataFrames com eles
    # A lógica de cálculo de F0 e F2 por run será feita na UI

    v_alta_ms = ref_vel_alta / 3.6
    v_baixa_ms = ref_vel_baixa / 3.6

    # Identifica colunas de DeltaT na alta velocidade
    colunas_delta_t_alta = [col for col in df_alta.columns if 'unnamed_col' in col and df_alta[col].dtype != 'object']
    if not colunas_delta_t_alta:
        raise ValueError("Nenhuma coluna de DeltaT encontrada no arquivo de alta velocidade.")

    # Para alta velocidade (90-70 km/h), precisamos das colunas de 90-85, 85-80, 80-75, 75-70
    # Como a ordem é da mais alta para a mais baixa, pegamos as colunas 1, 2, 3 e 4 (índices 1, 2, 3, 4)
    delta_t2_cols = colunas_delta_t_alta[1:5]
    #print(f"[DEBUG] calcular coeffff splitzada Colunas para DeltaT2 (90-70 km/h): {delta_t2_cols}")

    # Converte as colunas para numérico, forçando erros para NaN
    for col in delta_t2_cols:
        df_alta[col] = pd.to_numeric(df_alta[col], errors='coerce')

    df_alta['delta_t2_total'] = df_alta[delta_t2_cols].sum(axis=1, skipna=True)
    #print(f"[DEBUG] DeltaT2 total por run (alta): {df_alta['delta_t2_total'].tolist()}")

    # Identifica colunas de DeltaT na baixa velocidade
    colunas_delta_t_baixa = [col for col in df_baixa.columns if 'unnamed_col' in col and df_baixa[col].dtype != 'object']
    if not colunas_delta_t_baixa:
        raise ValueError("Nenhuma coluna de DeltaT encontrada no arquivo de baixa velocidade.")

    # Para baixa velocidade (45-35 km/h), precisamos das colunas de 45-40, 40-35
    # Pegamos as colunas 1 e 2 (índices 1, 2)
    delta_t1_cols = colunas_delta_t_baixa[1:3]
    #print(f"[DEBUG] Colunas para DeltaT1 (45-35 km/h): {delta_t1_cols}")

    # Converte as colunas para numérico, forçando erros para NaN
    for col in delta_t1_cols:
        df_baixa[col] = pd.to_numeric(df_baixa[col], errors='coerce')

    df_baixa['delta_t1_total'] = df_baixa[delta_t1_cols].sum(axis=1, skipna=True)
    #print(f"[DEBUG] DeltaT1 total por run (baixa): {df_baixa['delta_t1_total'].tolist()}")

    return df_alta, df_baixa


def processar_tempos_split(df_alta, df_baixa):
    """
    Processa os tempos para o método Split.
    
    Args:
        df_alta: DataFrame com dados de alta velocidade
        df_baixa: DataFrame com dados de baixa velocidade
        
    Returns:
        tuple: (df_alta, df_baixa) com colunas de delta_t adicionadas
    """
    # Esta função agora apenas extrai os DeltaTs por run e retorna os DataFrames com eles

    # Identifica colunas de DeltaT na alta velocidade
    colunas_delta_t_alta = [col for col in df_alta.columns if 'unnamed_col' in col and df_alta[col].dtype != 'object']
    if not colunas_delta_t_alta:
        raise ValueError("Nenhuma coluna de DeltaT encontrada no arquivo de alta velocidade.")

    # Para alta velocidade (90-70 km/h), precisamos das colunas de 90-85, 85-80, 80-75, 75-70
    # Como a ordem é da mais alta para a mais baixa, pegamos as colunas 1, 2, 3 e 4 (índices 1, 2, 3, 4)
    delta_t2_cols = colunas_delta_t_alta[1:5]
    #print(f"[DEBUG] Colunas para DeltaT2 (90-70 km/h): {delta_t2_cols}")

    # Converte as colunas para numérico, forçando erros para NaN
    for col in delta_t2_cols:
        df_alta[col] = pd.to_numeric(df_alta[col], errors='coerce')

    df_alta['delta_t2_total'] = df_alta[delta_t2_cols].sum(axis=1, skipna=True)
    #print(f"[DEBUG]processar tempossssssss DeltaT2 total por run (alta): {df_alta['delta_t2_total'].tolist()}")

    # Identifica colunas de DeltaT na baixa velocidade
    colunas_delta_t_baixa = [col for col in df_baixa.columns if 'unnamed_col' in col and df_baixa[col].dtype != 'object']
    if not colunas_delta_t_baixa:
        raise ValueError("Nenhuma coluna de DeltaT encontrada no arquivo de baixa velocidade.")

    # Para baixa velocidade (45-35 km/h), precisamos das colunas de 45-40, 40-35
    # Pegamos as colunas 1 e 2 (índices 1, 2)
    delta_t1_cols = colunas_delta_t_baixa[1:3]
    #print(f"[DEBUG] Colunas para DeltaT1 (45-35 km/h): {delta_t1_cols}")

    # Converte as colunas para numérico, forçando erros para NaN
    for col in delta_t1_cols:
        df_baixa[col] = pd.to_numeric(df_baixa[col], errors='coerce')

    df_baixa['delta_t1_total'] = df_baixa[delta_t1_cols].sum(axis=1, skipna=True)
    #print(f"[DEBUG] DeltaT1 total por run (baixa): {df_baixa['delta_t1_total'].tolist()}")

    return df_alta, df_baixa


def calcular_f0_f2_split(delta_t1_medio, delta_t2_medio, ref_vel_alta, ref_vel_baixa, massa_efetiva):
    """
    Calcula F0 e F2 para o método Split.
    
    Args:
        delta_t1_medio: Delta T médio para baixa velocidade
        delta_t2_medio: Delta T médio para alta velocidade
        ref_vel_alta: Velocidade de referência alta (km/h)
        ref_vel_baixa: Velocidade de referência baixa (km/h)
        massa_efetiva: Massa efetiva do veículo
        
    Returns:
        tuple: (f0, f2)
    """
    v_alta_ms = ref_vel_alta / 3.6
    v_baixa_ms = ref_vel_baixa / 3.6

    delta_v2 = 20 / 3.6 # em m/s (90-70 km/h)
    delta_v1 = 10 / 3.6 # em m/s (45-35 km/h)

    if pd.isna(delta_t1_medio) or pd.isna(delta_t2_medio) or delta_t1_medio <= 0 or delta_t2_medio <= 0:
        return np.nan, np.nan

    # Fórmulas
    f0 = (massa_efetiva / (v_alta_ms**2 - v_baixa_ms**2)) * ((delta_v2 / delta_t2_medio) * v_baixa_ms**2 - (delta_v1 / delta_t1_medio) * v_alta_ms**2)

    f2 = (massa_efetiva / (v_alta_ms**2 - v_baixa_ms**2)) * ((delta_v1 / delta_t1_medio) - (delta_v2 / delta_t2_medio))

    return -f0, -f2


def calculate_single_pair_corrected_data(
    run_ida_id: int, 
    run_volta_id: int, 
    individual_coeffs: dict, 
    temp_ida_c: float,
    press_ida_kpa: float,
    temp_volta_c: float,
    press_volta_kpa: float
) -> dict:
    """
    Calcula os coeficientes corrigidos e a energia para um par de runs,
    dada a temperatura e pressão.

    Args:
        run_ida_id: ID da run de ida.
        run_volta_id: ID da run de volta.
        individual_coeffs: Dicionário com os coeficientes individuais de todas as runs.
        temp_ida_c: Temperatura em Celsius para correção (ida).
        press_ida_kpa: Pressão em kPa para correção (ida).
        temp_volta_c: Temperatura em Celsius para correção (volta).
        press_volta_kpa: Pressão em kPa para correção (volta).

    Returns:
        Um dicionário contendo todos os coeficientes brutos e corrigidos.
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
    mean_energy_corrected = calcular_energia(mean_f0_corrected, mean_f2_corrected)

    return {
        'pair_id': f"{run_ida_id}/{run_volta_id}",
        'run1': run_ida_id,
        'run2': run_volta_id,
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
        "temp_ida_used": temp_ida_c,
        "temp_volta_used": temp_volta_c,
        "press_ida_used": press_ida_kpa,
        "press_volta_used": press_volta_kpa,
        "f0_mean": mean_f0_corrected,
        "f2_mean": mean_f2_corrected,
        "f0_corr": mean_f0_corrected,
        "f2_corr": mean_f2_corrected,
        "cv_f0": cv_f0_corrected,
        "cv_f2": cv_f2_corrected,
        'corrected': True
    }


def calculate_single_pair_corrected_data2(
    f0_ida_raw: float, 
    f2_ida_raw: float, 
    f0_volta_raw: float, 
    f2_volta_raw: float, 
    temp_c: float, 
    press_kpa: float
) -> dict:
    """
    Calcula os coeficientes corrigidos para um par usando valores brutos diretamente.
    
    Args:
        f0_ida_raw: F0 bruto da ida
        f2_ida_raw: F2 bruto da ida
        f0_volta_raw: F0 bruto da volta
        f2_volta_raw: F2 bruto da volta
        temp_c: Temperatura em Celsius
        press_kpa: Pressão em kPa
        
    Returns:
        dict: Dicionário com coeficientes corrigidos
    """
    # Constantes de correção climática
    T0 = 293.15  # 20°C em Kelvin
    P0 = 101.325 # Pressão padrão em kPa
    Kt = 0.0086
    Kp = 0.0002503

    # Fatores de correção para Run IDA
    f0_ida_corr = f0_ida_raw * (1 + Kt * ((temp_c + 273.15) - T0))
    f2_ida_corr = (((P0 * (temp_c + 273.15)) / (press_kpa * T0)) * (f2_ida_raw - Kp * f0_ida_raw) +
                            (Kp * f0_ida_corr)) / 12.96

    # Fatores de correção para Run VOLTA
    f0_volta_corr = f0_volta_raw * (1 + Kt * ((temp_c + 273.15) - T0))
    f2_volta_corr = (((P0 * (temp_c + 273.15)) / (press_kpa * T0)) * (f2_volta_raw - Kp * f0_volta_raw) +
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
    mean_energy_corrected = calcular_energia(mean_f0_corrected, mean_f2_corrected)

    return {
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
        'temp': temp_c,
        'press': press_kpa,
    }
