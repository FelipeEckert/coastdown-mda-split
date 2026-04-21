# coding: utf-8
"""
Página 4: Seleção por Algoritmo

Permite selecionar automaticamente os melhores pares usando algoritmos:
- Menor Energia
- Proximidade ao Target

O algoritmo gera TODOS os pares candidatos a partir das runs brutas,
aplica correção climática individual por passada, e seleciona os k melhores.
"""

import streamlit as st
import pandas as pd
import numpy as np
import math
import re
import statistics
import itertools
from math import comb
from statistics import mean, stdev
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.calculations import (
    calcular_energia,
    calcular_f0_f2_split,
    calculate_single_pair_corrected_data,
    calculate_single_pair_corrected_data2
)
from core.corrections import apply_climate_correction


# ===== FUNÇÕES AUXILIARES (idênticas ao PyQt5 original) =====

def _cv_percent(vals):
    """Calcula o coeficiente de variação em porcentagem."""
    if not vals or len(vals) <= 1:
        return 0.0
    m = float(np.mean(vals))
    if abs(m) < 1e-12:
        return 0.0
    sd = float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0
    return (sd / m) * 100.0


def _subset_metrics(subset):
    """Retorna (energia_total, cv_f0, cv_f2, mean_f0, mean_f2)."""
    f0 = [p["mean_f0_corrected"] for p in subset]
    f2 = [p["mean_f2_corrected"] for p in subset]
    e = sum(p["mean_energy_corrected"] for p in subset)
    cv0 = _cv_percent(f0)
    cv2 = _cv_percent(f2)
    m0 = float(np.mean(f0)) if f0 else 0.0
    m2 = float(np.mean(f2)) if f2 else 0.0
    return e, cv0, cv2, m0, m2


def _extract_run_ids(pair_or_id) -> set:
    """
    Extrai IDs de passadas a partir de:
      - um dict com 'pair_id', ou
      - uma string de pair_id.
    Suporta formatos:
      - Standard: '12/17'
      - Split: '12/34+56/78'
    Retorna um set de inteiros.
    """
    if isinstance(pair_or_id, dict):
        s = str(pair_or_id.get("pair_id", ""))
    else:
        s = str(pair_or_id)

    ids = re.findall(r"\d+", s)
    out = set()
    for x in ids:
        try:
            out.add(int(x))
        except ValueError:
            pass
    return out


def _mean_or_none(vals):
    """Calcula média ignorando None e NaN."""
    nums = []
    for w in vals:
        try:
            if w is not None and not pd.isna(w):
                nums.append(float(w))
        except Exception:
            pass
    return float(sum(nums) / len(nums)) if nums else None


def _topk_by_energy(pairs, k):
    """Seleciona os k pares de menor energia usando heap (O(n log k))."""
    import heapq
    heap = []  # max-heap via (-energia, idx, pair)
    for i, p in enumerate(pairs):
        e = float(p["mean_energy_corrected"])
        if len(heap) < k:
            heapq.heappush(heap, (-e, i, p))
        else:
            if e < -heap[0][0]:
                heapq.heapreplace(heap, (-e, i, p))
    sel = [t[2] for t in heap]
    sel.sort(key=lambda x: x["mean_energy_corrected"])
    return sel


def _repair_by_swaps(selected, pool, cv_max, max_iters=300):
    """
    Tenta corrigir violações de CV trocando elementos do conjunto selecionado
    por itens do pool, priorizando grande redução de CV e baixo aumento de energia.
    """
    sel = selected[:]
    remaining = pool[:]
    energy, cv0, cv2, _, _ = _subset_metrics(sel)
    if cv0 <= cv_max and cv2 <= cv_max:
        return sel

    it = 0
    while it < max_iters:
        it += 1
        best = None  # (improv_cv, delta_energy, i, j, (new_e, new_cv0, new_cv2))
        base_cv_sum = cv0 + cv2

        for i, pi in enumerate(sel):
            base_without = sel[:i] + sel[i + 1:]
            for j, pj in enumerate(remaining):
                trial = base_without + [pj]
                e2, c0, c2, _, _ = _subset_metrics(trial)
                cv_sum = c0 + c2
                improv = base_cv_sum - cv_sum
                delta_e = e2 - energy
                if improv > 0:
                    if (best is None or
                            improv > best[0] or
                            (abs(improv - best[0]) < 1e-12 and delta_e < best[1])):
                        best = (improv, delta_e, i, j, (e2, c0, c2))

        if not best:
            break

        # aplica o melhor swap encontrado
        _, _, i, j, met = best
        pj = remaining[j]
        pi = sel[i]
        sel[i] = pj
        remaining[j] = pi
        energy, cv0, cv2 = met

        if cv0 <= cv_max and cv2 <= cv_max:
            return sel

    return sel if (cv0 <= cv_max and cv2 <= cv_max) else None


def select_by_target_advanced(valid_single_pairs, target_f0, target_f2, k,
                              normalize=True, multi_start=3, swap_limit=50):
    """
    Seleciona k pares cuja MÉDIA (f0,f2) fica mais próxima do target.
    Heurística: greedy incremental + 1-swap local search.
    (Idêntico ao select_best_pairs_by_target do PyQt5 original)
    """
    n = len(valid_single_pairs)
    if n < k:
        return None

    # Monta matriz de vetores (f0,f2) corrigidos
    try:
        v = np.array([[p["mean_f0_corrected"], p["mean_f2_corrected"]]
                       for p in valid_single_pairs], dtype=np.float64)
    except Exception:
        v = np.array([[p.get("f0_corr") or p.get("mean_f0_corrected"),
                        p.get("f2_corr") or p.get("mean_f2_corrected")]
                       for p in valid_single_pairs], dtype=np.float64)

    target = np.array([float(target_f0), float(target_f2)], dtype=np.float64)

    # Normalização (evita que f0 domine f2, ou vice-versa)
    if normalize:
        scale = np.std(v, axis=0)
        scale[scale == 0] = 1.0
        v_n = v / scale
        target_n = target / scale
    else:
        v_n = v
        target_n = target

    def score(idx_list):
        m = v_n[idx_list].mean(axis=0)
        d = m - target_n
        return float(d[0] * d[0] + d[1] * d[1])

    # Se o problema for pequeno, resolve exato
    try:
        if n <= 30 and comb(n, k) <= 200_000:
            best = None
            best_s = float("inf")
            for comb_idx in itertools.combinations(range(n), k):
                s = score(comb_idx)
                if s < best_s:
                    best_s = s
                    best = comb_idx
            return [valid_single_pairs[i] for i in best]
    except Exception:
        pass

    # Heurística: greedy + 1-swap
    d_ind = ((v_n - target_n) ** 2).sum(axis=1)
    seed_idxs = np.argsort(d_ind)[:max(1, multi_start)]

    best_idx = None
    best_s = float("inf")

    for seed in seed_idxs:
        selected = [int(seed)]
        # Greedy: adiciona 1 por vez
        while len(selected) < k:
            sel_arr = np.array(selected, dtype=int)
            mask = np.ones(n, dtype=bool)
            mask[sel_arr] = False
            cand_idx = np.where(mask)[0]

            current_sum = v_n[sel_arr].sum(axis=0)
            Lp1 = len(selected) + 1

            means = (current_sum + v_n[cand_idx]) / Lp1
            d = means - target_n
            s = (d * d).sum(axis=1)
            j_best = cand_idx[int(np.argmin(s))]
            selected.append(int(j_best))

        # 1-swap local search
        improved = True
        while improved:
            improved = False
            sel_arr = np.array(selected, dtype=int)
            current_s = score(sel_arr)
            current_sum = v_n[sel_arr].sum(axis=0)

            mask = np.ones(n, dtype=bool)
            mask[sel_arr] = False
            out_idx_all = np.where(mask)[0]

            J = min(swap_limit, out_idx_all.size)
            if J == 0:
                break
            out_idx = out_idx_all[np.argsort(d_ind[out_idx_all])[:J]]

            for pos_in, idx_in in enumerate(sel_arr):
                sum_wo = current_sum - v_n[idx_in]
                L = k
                means = (sum_wo + v_n[out_idx]) / L
                d = means - target_n
                s = (d * d).sum(axis=1)
                j = int(np.argmin(s))
                if s[j] + 1e-12 < current_s:
                    selected[pos_in] = int(out_idx[j])
                    improved = True
                    current_s = float(s[j])
                    current_sum = sum_wo + v_n[out_idx[j]]

        final_s = score(np.array(selected))
        if final_s < best_s:
            best_s = final_s
            best_idx = list(selected)

    if best_idx is None:
        return None
    return [valid_single_pairs[i] for i in best_idx]


# ===== GERAÇÃO DE PARES CANDIDATOS =====

def generate_all_candidate_pairs_traditional(weather_data, temp_fixed, press_fixed, cv_max, progress_callback=None):
    """
    Gera TODOS os pares candidatos para o método tradicional.
    Aplica correção climática INDIVIDUAL por passada (conforme norma ABNT 10312).
    
    Idêntico ao fluxo do select_best_pairs() do PyQt5 original.
    """
    all_run_data = st.session_state.all_run_data
    individual_coeffs = st.session_state.individual_coeffs

    # Separa runs por heading
    all_runs_ids = sorted([r_id for r_id in all_run_data.keys()], key=lambda x: int(x) if str(x).isdigit() else 0)
    ida_runs = [r_id for r_id in all_runs_ids if all_run_data[r_id].get("heading") == "+"]
    volta_runs = [r_id for r_id in all_runs_ids if all_run_data[r_id].get("heading") == "-"]

    if not ida_runs or not volta_runs:
        return []

    valid_single_pairs = []
    total = len(ida_runs) * len(volta_runs)
    count = 0

    for run_ida_id in ida_runs:
        for run_volta_id in volta_runs:
            count += 1
            if progress_callback:
                progress_callback(count / total)

            temp1 = None
            temp2 = None
            press1 = None
            press2 = None
            wind1 = None
            wind2 = None
            wind_avg = None

            current_temp = temp_fixed
            current_press = press_fixed
            temp_ida_used = None
            temp_volta_used = None
            press_ida_used = None
            press_volta_used = None

            if current_temp is None and weather_data:
                try:
                    ts1 = all_run_data[run_ida_id].get("start_timestamp")
                    ts2 = all_run_data[run_volta_id].get("start_timestamp")

                    if not ts1 or not ts2:
                        continue

                    closest1 = min(weather_data, key=lambda x: abs(x["timestamp"] - ts1))
                    closest2 = min(weather_data, key=lambda x: abs(x["timestamp"] - ts2))

                    temp1 = closest1.get("temp_c")
                    press1 = closest1.get("baro_kpa")
                    temp2 = closest2.get("temp_c")
                    press2 = closest2.get("baro_kpa")

                    # Vento por passada + média do par
                    wind1 = closest1.get("wind_ms")
                    wind2 = closest2.get("wind_ms")

                    wind_vals = []
                    for w in (wind1, wind2):
                        try:
                            if w is not None and not pd.isna(w):
                                wind_vals.append(float(w))
                        except Exception:
                            pass
                    wind_avg = float(sum(wind_vals) / len(wind_vals)) if wind_vals else None

                    if temp1 is None or press1 is None or temp2 is None or press2 is None:
                        continue

                    temp_ida_used = temp1
                    press_ida_used = press1
                    temp_volta_used = temp2
                    press_volta_used = press2

                    current_temp = (temp1 + temp2) / 2
                    current_press = (press1 + press2) / 2

                except Exception as e:
                    continue

            if current_temp is None or current_press is None:
                continue

            # Se NÃO estamos usando arquivo meteorológico,
            # assume que a mesma T/P manual vale para ida e volta
            if not weather_data:
                temp1 = current_temp
                temp2 = current_temp
                press1 = current_press
                press2 = current_press
                temp_ida_used = temp1
                temp_volta_used = temp2
                press_ida_used = press1
                press_volta_used = press2

            # Calcular dados corrigidos para o par
            try:
                pair_data = calculate_single_pair_corrected_data(
                    run_ida_id,
                    run_volta_id,
                    individual_coeffs,
                    temp_ida_used,
                    press_ida_used,
                    temp_volta_used,
                    press_volta_used
                )

                # Anexa vento ao pair_data
                pair_data["wind_ida_ms"] = wind1
                pair_data["wind_volta_ms"] = wind2
                pair_data["wind_avg_ms"] = wind_avg

                # Guardar condições usadas por passada e média
                pair_data["temp_ida_used"] = temp_ida_used
                pair_data["temp_volta_used"] = temp_volta_used
                pair_data["press_ida_used"] = press_ida_used
                pair_data["press_volta_used"] = press_volta_used
                pair_data["temp"] = current_temp
                pair_data["press"] = current_press

                # Buscar coeficientes não corrigidos dos individual_coeffs
                f0_ida_raw = individual_coeffs.get(run_ida_id, {}).get("f0")
                f2_ida_raw = individual_coeffs.get(run_ida_id, {}).get("f2")
                f0_volta_raw = individual_coeffs.get(run_volta_id, {}).get("f0")
                f2_volta_raw = individual_coeffs.get(run_volta_id, {}).get("f2")

                if all([f0_ida_raw, f2_ida_raw, f0_volta_raw, f2_volta_raw]):
                    mean_f0_raw = (f0_ida_raw + f0_volta_raw) / 2
                    mean_f2_raw = (f2_ida_raw + f2_volta_raw) / 2
                    pair_data["f0_mean"] = mean_f0_raw
                    pair_data["f2_mean"] = mean_f2_raw
                else:
                    pair_data["f0_mean"] = pair_data.get("mean_f0_corrected")
                    pair_data["f2_mean"] = pair_data.get("mean_f2_corrected")

                # Flags de seleção
                pair_data["selected_by_energy_algo"] = False
                pair_data["selected_by_target_algo"] = False
                pair_data["selected"] = False

                # Validar CVs individuais
                if pair_data["cv_f0_corrected"] <= cv_max and pair_data["cv_f2_corrected"] <= cv_max:
                    pair_data["pair_id"] = f"{run_ida_id}/{run_volta_id}"
                    valid_single_pairs.append(pair_data)

            except Exception as e:
                continue

    return valid_single_pairs


def generate_all_candidate_pairs_split(weather_data, temp_fixed, press_fixed, cv_max, progress_callback=None):
    """
    Gera TODOS os pares candidatos para o método Split.
    Aplica correção climática INDIVIDUAL por passada (conforme norma ABNT 10312).
    
    Idêntico ao fluxo do select_best_pairs() do PyQt5 original para Split.
    """
    all_run_data_alta = st.session_state.all_run_data_alta
    all_run_data_baixa = st.session_state.all_run_data_baixa
    total_mass = st.session_state.total_mass
    ref_vel_alta = st.session_state.ref_vel_alta
    ref_vel_baixa = st.session_state.ref_vel_baixa
    df_raw_alta = st.session_state.df_raw_alta
    df_raw_baixa = st.session_state.df_raw_baixa

    # Separa runs por heading
    alta_runs = sorted([r_id for r_id in all_run_data_alta.keys()], key=lambda x: int(x) if str(x).isdigit() else 0)
    baixa_runs = sorted([r_id for r_id in all_run_data_baixa.keys()], key=lambda x: int(x) if str(x).isdigit() else 0)

    if not alta_runs or not baixa_runs:
        return []

    alta_ida_runs = [r_id for r_id in alta_runs if all_run_data_alta[r_id].get("heading") == "+"]
    alta_volta_runs = [r_id for r_id in alta_runs if all_run_data_alta[r_id].get("heading") == "-"]
    baixa_ida_runs = [r_id for r_id in baixa_runs if all_run_data_baixa[r_id].get("heading") == "+"]
    baixa_volta_runs = [r_id for r_id in baixa_runs if all_run_data_baixa[r_id].get("heading") == "-"]

    if not alta_ida_runs or not alta_volta_runs or not baixa_ida_runs or not baixa_volta_runs:
        return []

    valid_pairs_split = []
    total_combinations = len(alta_ida_runs) * len(baixa_ida_runs) * len(alta_volta_runs) * len(baixa_volta_runs)
    combination_count = 0

    for id_alta_ida in alta_ida_runs:
        for id_baixa_ida in baixa_ida_runs:
            for id_alta_volta in alta_volta_runs:
                for id_baixa_volta in baixa_volta_runs:
                    combination_count += 1
                    if progress_callback:
                        progress_callback(combination_count / total_combinations)

                    wind_alta_ida = wind_baixa_ida = wind_alta_volta = wind_baixa_volta = None
                    wind_avg = None

                    # Calcular F0/F2 para o par de IDA
                    try:
                        delta_t2_ida = df_raw_alta.loc[df_raw_alta["run"] == id_alta_ida, "delta_t2_total"].iloc[0]
                        delta_t1_ida = df_raw_baixa.loc[df_raw_baixa["run"] == id_baixa_ida, "delta_t1_total"].iloc[0]
                    except (IndexError, KeyError):
                        continue

                    f0_ida_raw, f2_ida_raw = calcular_f0_f2_split(
                        delta_t1_ida, delta_t2_ida,
                        ref_vel_alta, ref_vel_baixa, total_mass
                    )

                    # Calcular F0/F2 para o par de VOLTA
                    try:
                        delta_t2_volta = df_raw_alta.loc[df_raw_alta["run"] == id_alta_volta, "delta_t2_total"].iloc[0]
                        delta_t1_volta = df_raw_baixa.loc[df_raw_baixa["run"] == id_baixa_volta, "delta_t1_total"].iloc[0]
                    except (IndexError, KeyError):
                        continue

                    f0_volta_raw, f2_volta_raw = calcular_f0_f2_split(
                        delta_t1_volta, delta_t2_volta,
                        ref_vel_alta, ref_vel_baixa, total_mass
                    )

                    # Pré-filtragem por CV dos coeficientes brutos
                    f0_values_raw = [f0_ida_raw, f0_volta_raw]
                    f2_values_raw = [f2_ida_raw, f2_volta_raw]

                    mean_f0_raw = statistics.mean(f0_values_raw)
                    mean_f2_raw = statistics.mean(f2_values_raw)

                    cv_f0_raw = (statistics.stdev(f0_values_raw) / mean_f0_raw) * 100 if mean_f0_raw != 0 else 0.0
                    cv_f2_raw = (statistics.stdev(f2_values_raw) / mean_f2_raw) * 100 if mean_f2_raw != 0 else 0.0

                    if cv_f0_raw > cv_max or cv_f2_raw > cv_max:
                        continue

                    # Obter temperatura e pressão
                    current_temp = temp_fixed
                    current_press = press_fixed

                    if current_temp is None and weather_data:
                        try:
                            ts_alta_ida = all_run_data_alta[id_alta_ida].get("start_timestamp")
                            ts_baixa_ida = all_run_data_baixa[id_baixa_ida].get("start_timestamp")
                            ts_alta_volta = all_run_data_alta[id_alta_volta].get("start_timestamp")
                            ts_baixa_volta = all_run_data_baixa[id_baixa_volta].get("start_timestamp")

                            if not all([ts_alta_ida, ts_baixa_ida, ts_alta_volta, ts_baixa_volta]):
                                continue

                            closest_alta_ida = min(weather_data, key=lambda x: abs(x["timestamp"] - ts_alta_ida))
                            closest_baixa_ida = min(weather_data, key=lambda x: abs(x["timestamp"] - ts_baixa_ida))
                            closest_alta_volta = min(weather_data, key=lambda x: abs(x["timestamp"] - ts_alta_volta))
                            closest_baixa_volta = min(weather_data, key=lambda x: abs(x["timestamp"] - ts_baixa_volta))

                            # Vento
                            wind_alta_ida = closest_alta_ida.get("wind_ms")
                            wind_baixa_ida = closest_baixa_ida.get("wind_ms")
                            wind_alta_volta = closest_alta_volta.get("wind_ms")
                            wind_baixa_volta = closest_baixa_volta.get("wind_ms")

                            wind_ida_avg = _mean_or_none([wind_alta_ida, wind_baixa_ida])
                            wind_volta_avg = _mean_or_none([wind_alta_volta, wind_baixa_volta])
                            wind_pair_avg = _mean_or_none([wind_ida_avg, wind_volta_avg])

                            # Temperatura e pressão
                            temps = [closest_alta_ida.get("temp_c"), closest_baixa_ida.get("temp_c"),
                                     closest_alta_volta.get("temp_c"), closest_baixa_volta.get("temp_c")]
                            presses = [closest_alta_ida.get("baro_kpa"), closest_baixa_ida.get("baro_kpa"),
                                       closest_alta_volta.get("baro_kpa"), closest_baixa_volta.get("baro_kpa")]

                            if None in temps or None in presses:
                                continue

                            current_temp = sum(temps) / len(temps)
                            current_press = sum(presses) / len(presses)

                        except Exception:
                            continue
                    else:
                        wind_ida_avg = None
                        wind_volta_avg = None
                        wind_pair_avg = None

                    if current_temp is None or current_press is None:
                        continue

                    # Aplicar correção climática
                    try:
                        corrected_data = calculate_single_pair_corrected_data2(
                            f0_ida_raw, f2_ida_raw,
                            f0_volta_raw, f2_volta_raw,
                            current_temp, current_press
                        )

                        combination = {
                            "pair_id": f"{id_alta_ida}/{id_baixa_ida}+{id_alta_volta}/{id_baixa_volta}",
                            "mean_f0_corrected": corrected_data["mean_f0_corrected"],
                            "mean_f2_corrected": corrected_data["mean_f2_corrected"],
                            "mean_energy_corrected": corrected_data["energy"],
                            "cv_f0_corrected": corrected_data["cv_f0_corrected"],
                            "cv_f2_corrected": corrected_data["cv_f2_corrected"],
                            "temp": current_temp,
                            "press": current_press,
                            "selected_by_energy_algo": False,
                            "selected_by_target_algo": False,
                            "selected": False,
                            "wind_ida_ms": wind_ida_avg,
                            "wind_volta_ms": wind_volta_avg,
                            "wind_avg_ms": wind_pair_avg,
                            # Chaves de compatibilidade
                            "f0_corr": corrected_data["mean_f0_corrected"],
                            "f2_corr": corrected_data["mean_f2_corrected"],
                            "cv_f0": corrected_data["cv_f0_corrected"],
                            "cv_f2": corrected_data["cv_f2_corrected"],
                            "energy": corrected_data["energy"],
                            "sub_pairs": [
                                {
                                    "pair_id": f"{id_alta_ida}/{id_baixa_ida}",
                                    "mean_f0_corrected": corrected_data["mean_f0_corrected"],
                                    "mean_f2_corrected": corrected_data["mean_f2_corrected"],
                                    "heading": "+"
                                },
                                {
                                    "pair_id": f"{id_alta_volta}/{id_baixa_volta}",
                                    "mean_f0_corrected": corrected_data["mean_f0_corrected"],
                                    "mean_f2_corrected": corrected_data["mean_f2_corrected"],
                                    "heading": "-"
                                }
                            ]
                        }

                        valid_pairs_split.append(combination)

                    except Exception:
                        continue

    return valid_pairs_split


# ===== RENDERIZAÇÃO DA PÁGINA =====

def render(t):
    """Renderiza a página de seleção por algoritmo."""

    st.header("🤖 Seleção Automática de Pares")

    # Verifica pré-requisitos
    if not st.session_state.data_loaded:
        st.warning("⚠️ Nenhum dado carregado. Vá para **Abrir Teste** primeiro.")
        return

    if not st.session_state.vehicle_data_complete:
        st.warning("⚠️ Dados do veículo incompletos. Vá para **Dados do Veículo** primeiro.")
        return

    if not st.session_state.individual_coeffs and not st.session_state.using_split_method:
        st.warning("⚠️ Coeficientes individuais não calculados. Vá para **Análise de Pares** primeiro.")
        return

    st.info("""
    💡 **Como funciona:**
    
    Esta ferramenta analisa **todas as combinações possíveis** de pares (ida × volta) e seleciona 
    automaticamente os melhores baseado em critérios científicos.
    
    A correção climática é aplicada **individualmente por passada** conforme a norma ABNT 10312.
    
    **Dois modos disponíveis:**
    - 🟢 **Menor Energia:** Seleciona pares que minimizam o consumo energético
    - 🔵 **Proximidade ao Target:** Seleciona pares mais próximos de valores F0/F2 desejados
    """)

    st.markdown("---")

    # ===== CONFIGURAÇÕES DO ALGORITMO =====
    st.subheader("⚙️ Configurações")

    col1, col2, col3 = st.columns(3)

    with col1:
        algorithm_mode = st.selectbox(
            "Algoritmo:",
            ["Menor Energia", "Proximidade ao Target"],
            help="Escolha o critério de seleção automática",
            key="algo_mode"
        )

    with col2:
        num_pairs = st.number_input(
            "Número de pares (k):",
            min_value=2,
            max_value=20,
            value=5,
            help="Quantos pares selecionar na combinação final",
            key="algo_k"
        )

    with col3:
        default_cv = 2.5 if st.session_state.using_split_method else 10.0
        cv_max = st.number_input(
            "CV máximo (%):",
            min_value=0.1,
            max_value=60.0,
            value=default_cv,
            step=0.1,
            help="Valores típicos: Standard=10%, Split=2.5%",
            key="algo_cv_max"
        )

    # Campos de Target (se necessário)
    target_f0 = None
    target_f2 = None
    if algorithm_mode == "Proximidade ao Target":
        st.markdown("### 🎯 Valores Target")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            target_f0 = st.number_input(
                "Target F0 (N):",
                min_value=0.0,
                max_value=1000.0,
                value=110.0,
                step=0.1,
                format="%.2f",
                key="algo_target_f0"
            )
        with col_t2:
            target_f2 = st.number_input(
                "Target F2 (N/(km/h)²):",
                min_value=0.0,
                max_value=1.0,
                value=0.043,
                step=0.001,
                format="%.6f",
                key="algo_target_f2"
            )

    st.markdown("---")

    # ===== DADOS METEOROLÓGICOS =====
    st.subheader("🌡️ Dados Meteorológicos")

    weather_data = None
    if st.session_state.using_split_method:
        weather_data = st.session_state.get("weather_data_split")
    else:
        weather_data = st.session_state.get("weather_data")

    temp_fixed = None
    press_fixed = None

    if weather_data:
        st.success(f"✅ Dados meteorológicos carregados ({len(weather_data)} registros). Serão usados automaticamente por passada.")
    else:
        st.warning("⚠️ Não há dados meteorológicos carregados.")
        use_fixed = st.checkbox("Usar temperatura e pressão fixas", value=True, key="algo_use_fixed")

        if use_fixed:
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                temp_fixed = st.number_input(
                    "Temperatura (°C):",
                    min_value=-50.0,
                    max_value=60.0,
                    value=25.0,
                    step=0.1,
                    key="algo_temp_fixed"
                )
            with col_m2:
                press_fixed = st.number_input(
                    "Pressão (kPa):",
                    min_value=80.0,
                    max_value=110.0,
                    value=101.325,
                    step=0.01,
                    key="algo_press_fixed"
                )
        else:
            st.error("❌ Sem dados meteorológicos e sem valores fixos. Não é possível executar o algoritmo.")
            return

    st.markdown("---")

    # ===== OPÇÃO DE EVITAR PASSADAS REPETIDAS =====
    avoid_repeated = st.checkbox(
        "Evitar passadas repetidas nos pares selecionados (recomendado pela norma)",
        value=True,
        key="algo_avoid_repeated"
    )

    st.markdown("---")

    # ===== BOTÃO EXECUTAR =====
    if st.button("🚀 Executar Seleção Automática", type="primary", use_container_width=True, key="algo_execute"):
        run_algorithm(
            algorithm_mode, num_pairs, cv_max,
            weather_data, temp_fixed, press_fixed,
            target_f0, target_f2, avoid_repeated
        )

    # ===== RESULTADOS =====
    if "algorithm_results" in st.session_state and st.session_state.algorithm_results:
        display_algorithm_results(t, st.session_state.algorithm_results)


def run_algorithm(algorithm_mode, k, cv_max, weather_data, temp_fixed, press_fixed,
                  target_f0, target_f2, avoid_repeated):
    """Executa o algoritmo de seleção automática."""

    with st.spinner("🔄 Gerando todos os pares candidatos... Isso pode levar alguns minutos."):
        progress_bar = st.progress(0, text="Analisando combinações...")

        def update_progress(pct):
            progress_bar.progress(pct, text=f"Analisando combinações... {pct * 100:.0f}%")

        # Gera TODOS os pares candidatos
        if st.session_state.using_split_method:
            valid_pairs = generate_all_candidate_pairs_split(
                weather_data, temp_fixed, press_fixed, cv_max, update_progress
            )
        else:
            valid_pairs = generate_all_candidate_pairs_traditional(
                weather_data, temp_fixed, press_fixed, cv_max, update_progress
            )

        progress_bar.empty()

    if not valid_pairs:
        st.error("❌ Nenhuma combinação válida encontrada com os critérios definidos!")
        return

    if len(valid_pairs) < k:
        st.error(f"❌ Apenas {len(valid_pairs)} pares válidos encontrados. São necessários pelo menos {k}.")
        return

    st.info(f"✅ {len(valid_pairs)} pares candidatos válidos encontrados.")

    # ===== EXECUTA O ALGORITMO DE SELEÇÃO =====
    with st.spinner("🔄 Executando algoritmo de seleção..."):
        best_combination = []
        best_score = float("inf")

        if algorithm_mode == "Menor Energia":
            # Ordena todos os pares candidatos por energia crescente
            sorted_pairs = sorted(valid_pairs, key=lambda p: p["mean_energy_corrected"])

            selected = []
            used_runs = set()

            for p in sorted_pairs:
                if avoid_repeated:
                    run_ids = _extract_run_ids(p)
                    if not used_runs.isdisjoint(run_ids):
                        continue
                    selected.append(p)
                    used_runs |= run_ids
                else:
                    selected.append(p)

                if len(selected) == k:
                    break

            # Se não conseguiu k pares únicos
            if avoid_repeated and len(selected) < k:
                st.warning(f"⚠️ Apenas {len(selected)} pares sem repetição. Completando com pares repetidos.")
                for p in sorted_pairs:
                    if p in selected:
                        continue
                    selected.append(p)
                    if len(selected) == k:
                        break

            best_combination = selected
            best_score = sum(p["mean_energy_corrected"] for p in best_combination) if best_combination else float("inf")

        elif algorithm_mode == "Proximidade ao Target":
            if target_f0 is None or target_f2 is None:
                st.error("❌ Valores de Target F0 e F2 são necessários!")
                return

            # Usa seleção gulosa com respeito a passadas repetidas
            def target_score(p):
                f0 = p["mean_f0_corrected"]
                f2 = p["mean_f2_corrected"]
                den_f0 = target_f0 if abs(target_f0) > 1e-9 else 1.0
                den_f2 = target_f2 if abs(target_f2) > 1e-9 else 1.0
                return math.hypot((f0 - target_f0) / den_f0, (f2 - target_f2) / den_f2)

            ranked = sorted(valid_pairs, key=target_score)

            best_combination = []
            used_runs = set()

            for p in ranked:
                if len(best_combination) >= k:
                    break

                if avoid_repeated:
                    run_ids = _extract_run_ids(p["pair_id"])
                    if any(r in used_runs for r in run_ids):
                        continue

                best_combination.append(p)
                if avoid_repeated:
                    used_runs.update(_extract_run_ids(p["pair_id"]))

            if len(best_combination) < k:
                st.warning(f"⚠️ Apenas {len(best_combination)} pares selecionados (de {k} desejados).")
                if len(best_combination) == 0:
                    st.error("❌ Nenhum par pôde ser selecionado!")
                    return

            # Calcula score final
            mean_f0_comb = statistics.mean(p["mean_f0_corrected"] for p in best_combination)
            mean_f2_comb = statistics.mean(p["mean_f2_corrected"] for p in best_combination)
            percent_diff_f0 = abs(mean_f0_comb - target_f0) / (abs(target_f0) if abs(target_f0) > 1e-9 else 1.0)
            percent_diff_f2 = abs(mean_f2_comb - target_f2) / (abs(target_f2) if abs(target_f2) > 1e-9 else 1.0)
            best_score = math.hypot(percent_diff_f0, percent_diff_f2)

    # Verificação final
    if not best_combination:
        st.error(f"❌ Nenhum conjunto de {k} pares pôde ser selecionado.")
        return

    # ===== LIMPA APENAS A FLAG DO ALGORITMO ATUAL =====
    # Preserva a flag do outro algoritmo para que o usuário possa ver
    # simultaneamente quais pares cada algoritmo selecionou (cores distintas).
    if algorithm_mode == "Menor Energia":
        for pair_id in st.session_state.calculated_pairs:
            st.session_state.calculated_pairs[pair_id]["selected_by_energy_algo"] = False
    elif algorithm_mode == "Proximidade ao Target":
        for pair_id in st.session_state.calculated_pairs:
            st.session_state.calculated_pairs[pair_id]["selected_by_target_algo"] = False

    # ===== ADICIONA PARES AO CALCULATED_PAIRS E MARCA FLAGS =====
    st.session_state.pares_finais_selecionados = []

    for p in best_combination:
        pair_id = p["pair_id"]

        # Adiciona ao calculated_pairs se não existir
        if pair_id not in st.session_state.calculated_pairs:
            st.session_state.calculated_pairs[pair_id] = p

        # Marca flag do algoritmo
        if algorithm_mode == "Menor Energia":
            st.session_state.calculated_pairs[pair_id]["selected_by_energy_algo"] = True
        elif algorithm_mode == "Proximidade ao Target":
            st.session_state.calculated_pairs[pair_id]["selected_by_target_algo"] = True

        # Marca como selecionado
        st.session_state.calculated_pairs[pair_id]["selected"] = True

        st.session_state.pares_finais_selecionados.append(pair_id)

    st.session_state.pairs_calculated = True

    # ===== CALCULA ESTATÍSTICAS FINAIS =====
    f0_values_final = [p["mean_f0_corrected"] for p in best_combination]
    f2_values_final = [p["mean_f2_corrected"] for p in best_combination]
    energy_values_final = [p["mean_energy_corrected"] for p in best_combination]

    cv_f0_final = (statistics.stdev(f0_values_final) / statistics.mean(f0_values_final)) * 100 if len(f0_values_final) > 1 and statistics.mean(f0_values_final) != 0 else 0.0
    cv_f2_final = (statistics.stdev(f2_values_final) / statistics.mean(f2_values_final)) * 100 if len(f2_values_final) > 1 and statistics.mean(f2_values_final) != 0 else 0.0
    mean_f0_final = statistics.mean(f0_values_final)
    mean_f2_final = statistics.mean(f2_values_final)
    mean_energy_final = statistics.mean(energy_values_final)

    # Armazena resultados
    results = {
        "algorithm": algorithm_mode,
        "num_pairs": len(best_combination),
        "mean_f0": mean_f0_final,
        "mean_f2": mean_f2_final,
        "mean_energy": mean_energy_final,
        "cv_f0": cv_f0_final,
        "cv_f2": cv_f2_final,
        "score": best_score,
        "selected_pairs": best_combination,
        "target_f0": target_f0,
        "target_f2": target_f2,
    }

    st.session_state.algorithm_results = results
    st.success("✅ Seleção concluída!")
    st.rerun()


def display_algorithm_results(t, results):
    """Exibe os resultados do algoritmo."""

    st.subheader("📊 Resultados da Seleção")

    # Indicador de cor
    if results["algorithm"] == "Menor Energia":
        st.markdown("🟢 **Algoritmo:** Menor Energia")
        color = "#D1FFBD"
    else:
        st.markdown("🔵 **Algoritmo:** Proximidade ao Target")
        color = "#ADD8E6"

    # Métricas
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("F0 Médio Corrigido", f"{results['mean_f0']:.4f} N")
        st.metric("CV F0", f"{results['cv_f0']:.2f}%")

    with col2:
        st.metric("F2 Médio Corrigido", f"{results['mean_f2']:.6f}")
        st.metric("CV F2", f"{results['cv_f2']:.2f}%")

    with col3:
        st.metric("Energia Média", f"{results['mean_energy']:.4f} MJ/km")
        st.metric("Pares Selecionados", results['num_pairs'])

    if results["algorithm"] == "Proximidade ao Target" and results.get("target_f0"):
        st.markdown(f"**Target F0:** {results['target_f0']:.2f} N | **Target F2:** {results['target_f2']:.6f}")

    st.markdown(f"**Score:** {results['score']:.6f}")

    # Tabela de pares selecionados
    st.markdown("### Pares Selecionados:")

    table_data = []
    for p in results["selected_pairs"]:
        row = {
            "Par": p.get("pair_id", "N/A"),
            "F0 Corr. (N)": f"{p.get('mean_f0_corrected', 0):.4f}",
            "F2 Corr.": f"{p.get('mean_f2_corrected', 0):.6f}",
            "Energia (MJ/km)": f"{p.get('mean_energy_corrected', 0):.4f}",
            "CV F0 (%)": f"{p.get('cv_f0_corrected', 0):.2f}",
            "CV F2 (%)": f"{p.get('cv_f2_corrected', 0):.2f}",
        }
        # Adiciona temp/press se disponível
        if p.get("temp") is not None:
            row["Temp (°C)"] = f"{p['temp']:.1f}"
        if p.get("press") is not None:
            row["Press (kPa)"] = f"{p['press']:.2f}"
        table_data.append(row)

    df_selected = pd.DataFrame(table_data)
    st.dataframe(df_selected, use_container_width=True, hide_index=True)

    st.markdown("---")

    st.success(f"✅ Os {results['num_pairs']} pares foram adicionados ao **Comparativo Final** com cores correspondentes ao algoritmo.")

    if st.button("➡️ Ir para Comparativo Final", type="primary", key="goto_comparativo_from_algo"):
        st.session_state.current_page = "5_comparativo"
        st.rerun()
