# coding: utf-8
"""
Funções de carregamento de dados para análise de coastdown.

Este módulo contém todas as funções de leitura de arquivos CSV,
dados meteorológicos e sincronização.

IMPORTANTE: Não altere os nomes das funções ou variáveis para manter compatibilidade.
"""

import os
import re
import csv
import chardet
import numpy as np
import pandas as pd
from datetime import datetime, time, timedelta

from data.split_parser import parse_speed_bin_label
from utils.file_utils import detect_encoding_and_dialect, normalize_column_names


def carregar_dados_csv_robusto(file_path, using_split_method=False, is_alta=True):
    """
    Carrega e processa dados de um arquivo CSV de coastdown VBOX.
    
    Args:
        file_path: Caminho do arquivo CSV
        using_split_method: Se está usando método Split
        is_alta: Se é arquivo de alta velocidade (para Split)
        
    Returns:
        tuple: (df_filtered, all_data, test_date)
    """
    if not file_path or not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo não encontrado ou caminho inválido: {file_path}")

    test_date = None
    test_start_datetime = None  # <--- NOVO: data+hora absoluta do início do teste (linha 1)
    debug_output = []

    # --- Extração da Data (Linha 3, Coluna B) --- 
    # --- Extração da Data (Prioridade: Linha 3, Coluna B; Fallback: Linha 1, Coluna A) ---
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            debug_output.append(f"Total de linhas lidas: {len(lines)}")
            
            # Tenta extrair da Linha 3, Coluna B
            if len(lines) >= 3: # Garante que há pelo menos 3 linhas
                line_3_content = lines[2].strip() # Linha 3 é índice 2
                debug_output.append(f"Conteúdo da linha 3 (índice 2): '{line_3_content}'")
                
                delimiter = ','
                if ';' in line_3_content and ',' not in line_3_content:
                    delimiter = ';'
                debug_output.append(f"Delimitador detectado para linha 3: '{delimiter}'")

                line_3_parts = line_3_content.split(delimiter)
                debug_output.append(f"Partes da linha 3 (split por '{delimiter}'): {line_3_parts}")

                if len(line_3_parts) > 1: # Garante que há pelo menos 2 colunas
                    date_str_raw = line_3_parts[1].strip() # Coluna B é índice 1
                    debug_output.append(f"  -> Parte da data bruta extraída da coluna B: '{date_str_raw}'")
                    
                    if date_str_raw: # VERIFICA SE A STRING NÃO ESTÁ VAZIA
                        try:
                            test_date = datetime.strptime(date_str_raw, '%d-%b-%Y').date()
                            debug_output.append(f"  -> Data parseada com sucesso (formato %d-%b-%Y): {test_date}")
                        except ValueError as ve_yyyy:
                            debug_output.append(f"  -> ERRO ao parsear com %d-%b-%Y: {ve_yyyy}")
                            try:
                                test_date = datetime.strptime(date_str_raw, '%d-%b-%y').date()
                                debug_output.append(f"  -> Data parseada com sucesso (formato %d-%b-%y): {test_date}")
                            except ValueError as ve_yy:
                                debug_output.append(f"  -> ERRO ao parsear com %d-%b-%y: {ve_yy}")
                                test_date = None
                    else:
                        debug_output.append(f"  -> A parte da data da Linha 3, Coluna B está vazia.")
                else:
                    debug_output.append(f"  -> ERRO: Linha 3 não tem colunas suficientes para extrair a data da coluna B. Partes: {line_3_parts}")
            else:
                debug_output.append(f"ERRO: Arquivo tem menos de 3 linhas. Não foi possível ler a linha 3 para a data.")

            # Fallback: Tenta extrair da Linha 1, Coluna A, se a data ainda não foi encontrada
            if test_date is None and len(lines) >= 1:
                line_1_content = lines[0].strip() # Linha 1 é índice 0
                debug_output.append(f"Tentando fallback: Conteúdo da linha 1 (índice 0): \'{line_1_content}\'")
                
                # Procura pelo padrão "Test Date: DD/MM/YYYY HH:MM" ou "Test Date: DD/MM/YYYY"
                match = re.search(r'Test Date: (\d{2}/\d{2}/\d{4})(?:\s(\d{2}:\d{2}))?', line_1_content)
                if match:
                    date_part = match.group(1)
                    time_part = match.group(2)
                    full_date_str = f"{date_part} {time_part}" if time_part else date_part
                    debug_output.append(f"  -> Padrão de data/hora encontrado na linha 1: \'{full_date_str}\'")
                    try:
                        # Tenta parsear com hora, se disponível
                        if time_part:
                            dt = datetime.strptime(full_date_str, '%d/%m/%Y %H:%M')
                            test_date = dt.date()
                            test_start_datetime = dt  # <--- NOVO
                            debug_output.append(
                                f"  -> Data parseada com sucesso (formato %d/%m/%Y %H:%M): {test_date} (start {test_start_datetime})"
                            )
                        else:
                            dt = datetime.strptime(full_date_str, '%d/%m/%Y')
                            test_date = dt.date()
                            test_start_datetime = None  # sem hora, não dá pra compor elapsed
                            debug_output.append(f"  -> Data parseada com sucesso (formato %d/%m/%Y): {test_date}")

                    except ValueError as ve_line1:
                        debug_output.append(f"  -> ERRO ao parsear data da linha 1: {ve_line1}")
                else:
                    debug_output.append(f"  -> Padrão \"Test Date: DD/MM/YYYY HH:MM\" não encontrado na linha 1.")

    except Exception as e:
        debug_output.append(f"ERRO inesperado ao tentar extrair a data do cabeçalho: {e}")
        
    # --- SEGUNDA PASSADA: SEMPRE tentar extrair a HORA da linha 1 (mesmo se a data já veio da linha 3) ---
    try:
        if len(lines) >= 1:
            line_1_content = lines[0].strip()
            # aceita "Test Date: DD/MM/YYYY HH:MM" OU "Test Date: DD/MM/YYYY HH:MM:SS" OU só data
            m = re.search(
                r'Test Date:\s*(\d{2}/\d{2}/\d{4})(?:\s+(\d{2}:\d{2}(?::\d{2})?))?',
                line_1_content
            )
            if m:
                date_part = m.group(1)
                time_part = m.group(2)  # pode ser None
                # se não temos test_date ainda, usa a data da linha 1
                if test_date is None:
                    try:
                        test_date = datetime.strptime(date_part, '%d/%m/%Y').date()
                        debug_output.append(f"  -> (2ª passada) Data (linha 1) parseada: {test_date}")
                    except ValueError as ve:
                        debug_output.append(f"  -> (2ª passada) ERRO parse data linha 1: {ve}")
                # se temos hora, monta o datetime de início absoluto
                if time_part and test_date is not None:
                    # tenta HH:MM:SS e depois HH:MM
                    dt = None
                    for fmt in ('%d/%m/%Y %H:%M:%S', '%d/%m/%Y %H:%M'):
                        try:
                            dt = datetime.strptime(f"{date_part} {time_part}", fmt)
                            break
                        except ValueError:
                            continue
                    if dt is not None:
                        test_start_datetime = dt
                        debug_output.append(f"  -> (2ª passada) Hora inicial do teste (linha 1): {test_start_datetime}")
                    else:
                        # se hora não tinha segundos e a data da linha 1 diverge da da linha 3,
                        # ainda assim dá pra compor usando test_date + HH:MM
                        try:
                            hm = datetime.strptime(time_part, '%H:%M').time()
                            test_start_datetime = datetime.combine(test_date, hm)
                            debug_output.append(f"  -> (2ª passada) Hora inicial combinada com test_date: {test_start_datetime}")
                        except Exception as ehm:
                            debug_output.append(f"  -> (2ª passada) ERRO compondo hora com test_date: {ehm}")
            else:
                debug_output.append("  -> (2ª passada) Linha 1 não bateu com regex de Test Date.")
    except Exception as e:
        debug_output.append(f"  -> (2ª passada) ERRO inesperado: {e}")


    if test_date is None:
        # Write debug_output before raising error
        with open("debug_vbox_date.txt", "w", encoding="utf-8") as debug_f:
            debug_f.write("\n".join(debug_output))
        raise ValueError("Não foi possível encontrar a 'Test Date' no cabeçalho do arquivo VBOX. Necessário para sincronização. Verifique o arquivo debug_vbox_date.txt para mais detalhes.")

    # --- Leitura do CSV com cabeçalho fixo na linha 15 --- 
    try:
        encoding, _ = detect_encoding_and_dialect(file_path)
        start_row = 14 # Linha 15 é índice 14
        
        class ForcedDialect:
            delimiter = ','
            quotechar = '"'
            doublequote = True
            skipinitialspace = False
            lineterminator = '\r\n'
            quoting = csv.QUOTE_MINIMAL

        dialect = ForcedDialect()


        # Lendo o cabeçalho da linha 15 separadamente
        header_line_content = lines[start_row].strip()
        debug_output.append(f"\n--- Header Line (Row {start_row + 1}) Details ---")
        debug_output.append(f"Content of header line: '{header_line_content}'")
        
         # Processando os nomes do cabeçalho para garantir unicidade
        raw_header_parts = header_line_content.split(dialect.delimiter) # Usar o delimitador detectado para os dados
        header_names = []
        raw_column_labels = []
        unnamed_counter = 0
        seen_names = set() # Para controlar nomes duplicados

        for h in raw_header_parts:
            stripped_h = h.strip()
            raw_column_labels.append(stripped_h)
            if not stripped_h:
                # Se o cabeçalho está vazio, atribui um nome Unnamed_Col_X
                current_name = f"Unnamed_Col_{unnamed_counter}"
                unnamed_counter += 1
            else:
                current_name = stripped_h
            
            # Verifica se o nome já foi visto e adiciona um sufixo se for duplicado
            original_current_name = current_name
            suffix_counter = 0
            while current_name in seen_names:
                current_name = f"{original_current_name}_{suffix_counter}"
                suffix_counter += 1
            
            header_names.append(current_name)
            seen_names.add(current_name)
        header_names = normalize_column_names(header_names)

        # Lendo o CSV, usando a linha 15 como cabeçalho
        # Lendo o CSV, pulando a linha do cabeçalho e usando os nomes de coluna extraídos
        df = pd.read_csv(
            file_path,
            skiprows=start_row + 1, # Pula a linha do cabeçalho também
            header=None, # Não usa o cabeçalho do arquivo, usaremos 'names'
            names=header_names, # Define os nomes das colunas manualmente
            encoding=encoding,
            sep=dialect.delimiter, # Mantém o delimitador detectado para os dados
            skipinitialspace=dialect.skipinitialspace,
            quoting=dialect.quoting,
            engine="python",
            on_bad_lines="warn"
        )

        if df.empty:
            # Write debug_output before raising error
            with open("debug_vbox_date.txt", "w", encoding="utf-8") as debug_f:
                debug_f.write("\n".join(debug_output))
            raise ValueError("O DataFrame resultante está vazio após a leitura do CSV.")

        # Normaliza os nomes das colunas APÓS a leitura do Pandas
        original_columns = raw_column_labels

        # DEBUG: Print column information
        debug_output.append(f"\n--- Column Detection Debug ---")
        debug_output.append(f"Original Columns (as read by Pandas): {original_columns}")
        debug_output.append(f"Normalized Columns (used for internal logic): {df.columns.tolist()}")

        col_mapping = {
            "run_use": ["run_use", "runuse"],
            "run": ["run", "run_num"],
            "time_s": ["time_s", "times"],
            "distance_m": ["distance_m", "distancem"], 
            "start_time": ["start_time", "starttime"], 
            "max_decel_g": ["max_decel_g", "maxdecelg"],
            "heading": ["heading"],
            "notes": ["notes"] 
        }

        found_cols = {}
        missing_core_cols = []
        for core_name, possible_names in col_mapping.items():
            found = False
            for possible in possible_names:
                matched_col = next((col for col in df.columns if col == possible or col.startswith(possible + "_")), None)
                if matched_col:
                    found_cols[core_name] = matched_col
                    found = True
                    break
            if not found and core_name in ["run_use", "run", "time_s", "heading", "start_time"]:
                missing_core_cols.append(core_name)

        if missing_core_cols:
            # Write debug_output before raising error
            with open("debug_vbox_date.txt", "w", encoding="utf-8") as debug_f:
                debug_f.write("\n".join(debug_output))
            raise ValueError(f"Colunas essenciais não encontradas após normalização: {missing_core_cols}. Colunas detectadas: {df.columns.tolist()}")

        run_use_col = found_cols["run_use"]
        run_col = found_cols["run"]
        heading_col = found_cols["heading"]
        start_time_col = found_cols["start_time"]

        df_filtered = df[df[run_use_col].astype(str).str.strip().str.lower() == "on"].copy()
        df_filtered[run_col] = pd.to_numeric(df_filtered[run_col], errors="coerce")
        df_filtered.dropna(subset=[run_col], inplace=True)
        df_filtered = df_filtered.drop_duplicates(subset=[run_col], keep="first")
        df_filtered[run_col] = df_filtered[run_col].astype(int)

        if df_filtered.empty:
            # Write debug_output before raising error
            with open("debug_vbox_date.txt", "w", encoding="utf-8") as debug_f:
                debug_f.write("\n".join(debug_output))
            raise ValueError("Nenhuma linha válida com 'Run-Use' == 'On' e 'Run' numérico encontrada após filtragem.")

        runs = sorted(df_filtered[run_col].unique())
        all_data = {}
        header_list_normalized = df.columns.tolist()

        # --- Lógica para encontrar coluna inicial dos tempos (SIMPLIFICADA E FOCADA NO VAZIO, UNNAMED OU NUMÉRICO) --- 
        col_inicio_tempos = -1
        notes_col_index = -1
        if "notes" in found_cols:
             try:
                 notes_col_index = header_list_normalized.index(found_cols["notes"])
             except ValueError:
                 notes_col_index = -1

        # Encontra o índice da última coluna de metadados conhecida (antes dos tempos)
        known_meta_cols_in_order = ["run_use", "heading", "run", "time_s", "distance_m", "start_time", "max_decel_g"]
        last_meta_col_index = -1
        for meta_key in known_meta_cols_in_order:
            if meta_key in found_cols:
                try:
                    idx = header_list_normalized.index(found_cols[meta_key])
                    if idx > last_meta_col_index:
                        last_meta_col_index = idx
                except ValueError:
                    pass
        
        # Inicia a busca pela coluna de tempos após a última coluna de metadados conhecida
        start_search_index = last_meta_col_index + 1

        debug_output.append(f"\n--- Time Column Detection Details ---")
        debug_output.append(f"Last Meta Column Index: {last_meta_col_index} (Column: {original_columns[last_meta_col_index] if last_meta_col_index != -1 else 'N/A'})")
        debug_output.append(f"Start Search Index for Times: {start_search_index}")
        debug_output.append(f"Notes Column Index: {notes_col_index}")

        # Procura a primeira coluna que tem cabeçalho VAZIO, 'Unnamed: X' ou NUMÉRICO.
        for i in range(start_search_index, len(header_list_normalized)):
            original_col_name = original_columns[i]
            normalized_col_name = header_list_normalized[i]
            
            is_empty_header = (not isinstance(original_col_name, str) or not original_col_name.strip())
            is_unnamed_header = isinstance(normalized_col_name, str) and normalized_col_name.startswith("unnamed_col_") # ATUALIZADO: Verifica o nome normalizado
            is_numeric_header = False
            try:
                # Tenta converter o cabeçalho original para float (ex: '100', '95')
                float(original_col_name)
                is_numeric_header = True
            except (ValueError, TypeError):
                pass
            is_interval_label = parse_speed_bin_label(original_col_name) is not None
            
            debug_output.append(f"  Checking column {i} (Original: '{original_col_name}', Normalized: '{normalized_col_name}'):")
            debug_output.append(f"    is_empty_header: {is_empty_header}")
            debug_output.append(f"    is_unnamed_header: {is_unnamed_header}")
            debug_output.append(f"    is_numeric_header: {is_numeric_header}")
            debug_output.append(f"    is_interval_label: {is_interval_label}")
            debug_output.append(f"    Is before Notes column ({notes_col_index}): {i < notes_col_index if notes_col_index != -1 else 'N/A'}")

            # A condição principal: se o cabeçalho é vazio/unnamed/numérico E está antes da coluna 'Notes'
            if (is_empty_header or is_unnamed_header or is_numeric_header or is_interval_label) and \
               (notes_col_index == -1 or i < notes_col_index):
                col_inicio_tempos = i
                debug_output.append(f"  Found start column for times at index: {col_inicio_tempos}")
                break
            else:
                debug_output.append(f"  Column {i} NOT selected as start of times. Conditions: Empty={is_empty_header}, Unnamed={is_unnamed_header}, Numeric={is_numeric_header}, BeforeNotes={i < notes_col_index if notes_col_index != -1 else 'N/A'}")

        if col_inicio_tempos == -1:
            # Write debug_output before raising error
            with open("debug_vbox_date.txt", "w", encoding="utf-8") as debug_f:
                debug_f.write("\n".join(debug_output))
            raise ValueError("Não foi possível determinar a coluna inicial dos tempos de intervalo. Nenhuma coluna com cabeçalho vazio, 'Unnamed: X' ou numérico foi encontrada na linha 15 após as colunas de metadados conhecidas.")

        for run_id in runs:
            try:
                run_data_row = df_filtered.loc[df_filtered[run_col] == run_id].iloc[0]
                run_heading = str(run_data_row[heading_col]).strip()
                start_time_str = str(run_data_row[start_time_col]).strip()

                # Parsing robusto do start_time com detecção de elapsed vs absoluto
                start_timestamp = None
                s = (str(start_time_str) or "").strip()
                s = s.replace(",", ".")  # normaliza vírgula para ponto

                # 1) Tenta HH:MM:SS(.fração)
                m_hms = re.match(r'^(\d{1,2}):([0-5]\d):([0-5]\d)(?:\.(\d+))?$', s)
                # 2) Tenta MM:SS(.fração)
                m_ms  = re.match(r'^(\d{1,2}):([0-5]\d)(?:\.(\d+))?$', s)

                if m_hms:
                    hh = int(m_hms.group(1))
                    mm = int(m_hms.group(2))
                    ss = int(m_hms.group(3))
                    frac = m_hms.group(4)
                    sec_total = ss + (float(f"0.{frac}") if frac else 0.0)

                    if hh == 0:
                        # 00:MM:SS(.f) => ELAPSED
                        if test_start_datetime is not None:
                            start_timestamp = test_start_datetime + timedelta(minutes=mm, seconds=sec_total)
                            debug_output.append(
                                f"  -> Start Time '{s}' (HH=00) tratado como ELAPSED {mm}m{sec_total:.3f}s "
                                f"desde {test_start_datetime} -> {start_timestamp}"
                            )
                        else:
                            debug_output.append(
                                f"  -> Start Time '{s}' sugere ELAPSED, mas 'test_start_datetime' não está disponível."
                            )
                    else:
                        # HH>0 => Absoluto no dia do teste
                        try:
                            microsecond = int((frac or "").ljust(6, "0")[:6]) if frac else 0
                            time_with_sec = time(hh, mm, ss, microsecond)
                            start_timestamp = datetime.combine(test_date, time_with_sec)
                            debug_output.append(
                                f"  -> Start Time '{s}' interpretado como ABSOLUTO -> {start_timestamp}"
                            )
                        except Exception as eabs:
                            debug_output.append(f"  -> ERRO ao interpretar '{s}' como absoluto HH:MM:SS: {eabs}")

                elif m_ms:
                    # MM:SS(.f) => ELAPSED
                    mm = int(m_ms.group(1))
                    ss = int(m_ms.group(2))
                    frac = m_ms.group(3)
                    sec_total = ss + (float(f"0.{frac}") if frac else 0.0)

                    if test_start_datetime is not None:
                        start_timestamp = test_start_datetime + timedelta(minutes=mm, seconds=sec_total)
                        debug_output.append(
                            f"  -> Start Time '{s}' (MM:SS) tratado como ELAPSED {mm}m{sec_total:.3f}s "
                            f"desde {test_start_datetime} -> {start_timestamp}"
                        )
                    else:
                        debug_output.append(
                            f"  -> Start Time '{s}' (MM:SS) sugere ELAPSED, mas 'test_start_datetime' não está disponível."
                        )
                else:
                    # Fallback: tenta formatos antigos/absolutos
                    time_formats = [
                        "%H:%M:%S.%f",
                        "%H:%M:%S",
                        "%H:%M",
                        "%I:%M:%S %p",
                        "%I:%M %p",
                    ]
                    for fmt in time_formats:
                        try:
                            time_obj = datetime.strptime(s, fmt).time()
                            start_timestamp = datetime.combine(test_date, time_obj)
                            debug_output.append(f"  -> Start time parseado (fallback fmt {fmt}): {start_timestamp}")
                            break
                        except ValueError:
                            continue

                if start_timestamp is None:
                    debug_output.append(f"  -> ERRO: Não foi possível interpretar start_time '{s}' como elapsed nem absoluto.")


            except IndexError:
                continue
            except KeyError as ke:
                continue
           
            interval_measurements = []
            col_idx = col_inicio_tempos

            while col_idx < len(header_list_normalized) and (notes_col_index == -1 or col_idx < notes_col_index):
                try:
                    time_interval_str = str(run_data_row.iloc[col_idx]).replace(",", ".")
                    time_interval = pd.to_numeric(time_interval_str, errors="coerce")
                except IndexError:
                    break
                except Exception as e_conv:
                    time_interval = np.nan

                if pd.isna(time_interval) or time_interval < 0: 
                    break

                interval_measurements.append(
                    {
                        "column": header_list_normalized[col_idx],
                        "label": original_columns[col_idx],
                        "time_s": float(time_interval),
                    }
                )
                col_idx += 1

            if interval_measurements:
                if using_split_method:
                    all_data[run_id] = {
                        "interval_measurements": interval_measurements,
                        "heading": run_heading,
                        "start_timestamp": start_timestamp,
                        "start_time_str": start_time_str,
                    }
                    continue

                velocities = [100.0]
                times = [0.0]
                cumulative_time = 0.0
                for measurement in interval_measurements:
                    cumulative_time += measurement["time_s"]
                    velocities.append(velocities[-1] - 5.0)
                    times.append(cumulative_time)
                all_data[run_id] = {
                    "times": times,
                    "velocities": velocities,
                    "heading": run_heading,
                    "start_timestamp": start_timestamp,
                    "start_time_str": start_time_str,
                }

            else:
                print(f"Aviso: Run {run_id} não produziu dados de intervalo suficientes. Pulando run.")

        if not all_data:
            # Write debug_output before raising error
            with open("debug_vbox_date.txt", "w", encoding="utf-8") as debug_f:
                debug_f.write("\n".join(debug_output))
            raise ValueError("Nenhum dado de 'Run' válido foi extraído do arquivo após processamento.")

        return df_filtered, all_data, test_date

    except Exception as e:
        import traceback
        # Ensure debug_output is written even on unexpected errors
        with open("debug_vbox_date.txt", "w", encoding="utf-8") as debug_f:
            debug_f.write("\n".join(debug_output))
        if isinstance(e, FileNotFoundError):
            raise
        elif isinstance(e, ValueError):
            raise
        elif isinstance(e, pd.errors.ParserError):
             raise ValueError(f"Erro de parsing do Pandas: Verifique delimitadores, aspas e estrutura geral do CSV. Detalhe: {e}")
        elif isinstance(e, KeyError):
             raise ValueError(f"Erro de chave/coluna não encontrada: Verifique se as colunas esperadas existem. Detalhe: {e}")
        else:
             raise ValueError(f"Erro inesperado ao processar o arquivo CSV. Verifique o formato e conteúdo. Detalhe: {e}")


def read_weather_station_csv(file_path):
    """
    Lê dados de uma estação meteorológica a partir de um arquivo CSV.
    
    Args:
        file_path: Caminho do arquivo CSV
        
    Returns:
        list: Lista de dicionários com dados meteorológicos
    """
    # Detecta o encoding (mantém seu comportamento atual)
    with open(file_path, 'rb') as f:
        raw_data = f.read(2048)
        encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'

    # Nomes conforme seu arquivo (linha de cabeçalho na 12ª linha = skiprows=11)
    column_names = [
        "Time", "Temp", "Wet Bulb Temp.", "Rel. Hum.", "Baro.", "Altitude", "Station P.",
        "Wind Speed", "Heat Index", "Dew Point", "Dens. Alt.", "Air Flow", "Crosswind",
        "Headwind", "Mag. Dir.", "True Dir.", "Wind Chill", "Delta T", "Unknown1", "Unknown2"
    ]

    df = pd.read_csv(
        file_path,
        skiprows=11,
        names=column_names,
        encoding=encoding,
        engine="python",
        on_bad_lines="skip"
    )

    # Converte 'Time' para datetime (se houver formatos mistos)
    df['Time'] = pd.to_datetime(df['Time'], errors='coerce', dayfirst=True)

    # Converte numéricos com segurança
    for col in ['Temp', 'Baro.', 'Wind Speed', 'Crosswind', 'Headwind']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Converte pressão de mb para kPa (mb ÷ 10)
    if 'Baro.' in df.columns:
        df['Baro.'] = df['Baro.'] / 10.0

    # Filtra linhas válidas (precisamos pelo menos de timestamp, temp e baro para correção)
    df = df.dropna(subset=['Time', 'Temp', 'Baro.'])

    def _weather_wind_ms(row):
        """Retorna vento em m/s, preferindo Wind Speed e usando componentes como fallback."""
        wind_speed = row.get('Wind Speed')
        if wind_speed is not None and not pd.isna(wind_speed) and float(wind_speed) != 0.0:
            return float(wind_speed)

        crosswind = row.get('Crosswind')
        headwind = row.get('Headwind')
        if (
            crosswind is not None and not pd.isna(crosswind)
            and headwind is not None and not pd.isna(headwind)
        ):
            wind_from_components = float(np.hypot(float(crosswind), float(headwind)))
            if wind_from_components != 0.0:
                return wind_from_components

        if wind_speed is not None and not pd.isna(wind_speed):
            return float(wind_speed)

        return None

    # Monta a lista de dicionários, incluindo wind_ms (pode ser None)
    weather_data = []
    for _, row in df.iterrows():
        weather_data.append({
            'timestamp': row['Time'].to_pydatetime(),
            'baro_kpa' : float(row['Baro.']),
            'temp_c'   : float(row['Temp']),
            'wind_ms'  : _weather_wind_ms(row)
        })

    # Ordena por tempo (bom para buscas por "mais próximo")
    weather_data.sort(key=lambda x: x['timestamp'])
    
    return weather_data


def _seconds_since_midnight(value):
    """Converte datetime/time/string HH:MM[:SS] para segundos desde meia-noite."""
    if value is None:
        return None

    if isinstance(value, datetime):
        time_obj = value.time()
    elif isinstance(value, time):
        time_obj = value
    else:
        text = str(value).strip().replace(",", ".")
        if not text:
            return None

        formats = ("%H:%M:%S.%f", "%H:%M:%S", "%H:%M")
        time_obj = None
        for fmt in formats:
            try:
                time_obj = datetime.strptime(text, fmt).time()
                break
            except ValueError:
                continue

        if time_obj is None:
            return None

    return (
        time_obj.hour * 3600
        + time_obj.minute * 60
        + time_obj.second
        + time_obj.microsecond / 1_000_000
    )


def find_closest_weather_record(run_or_time, weather_data, time_only=False):
    """
    Retorna o registro meteorológico mais próximo de uma passada.

    Modo normal: compara timestamp completo (data + horário), preservando o
    comportamento existente. Modo flexível: compara apenas horário do dia.
    """
    if not weather_data:
        return None

    if isinstance(run_or_time, dict):
        target_time = run_or_time.get("start_timestamp") or run_or_time.get("start_time_str")
    else:
        target_time = run_or_time

    if time_only:
        target_seconds = _seconds_since_midnight(target_time)
        if target_seconds is None:
            return None

        candidates = []
        for record in weather_data:
            record_seconds = _seconds_since_midnight(record.get("timestamp"))
            if record_seconds is not None:
                candidates.append((abs(record_seconds - target_seconds), record))

        if not candidates:
            return None

        return min(candidates, key=lambda item: item[0])[1]

    if not isinstance(target_time, datetime):
        return None

    valid_records = [
        record for record in weather_data
        if isinstance(record.get("timestamp"), datetime)
    ]
    if not valid_records:
        return None

    return min(
        valid_records,
        key=lambda record: abs((record["timestamp"] - target_time).total_seconds())
    )
