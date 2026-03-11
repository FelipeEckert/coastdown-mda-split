# coding: utf-8
"""
Funções utilitárias para manipulação de arquivos.

Este módulo contém funções para detecção de encoding, dialeto CSV
e normalização de nomes de colunas.

IMPORTANTE: Não altere os nomes das funções para manter compatibilidade.
"""

import csv
import re


def detect_encoding_and_dialect(file_path):
    """
    Detecta o encoding e dialeto de um arquivo CSV.
    
    Args:
        file_path: Caminho do arquivo CSV
        
    Returns:
        tuple: (encoding, dialect)
    """
    with open(file_path, 'rb') as f:
        raw_data = f.read(4096)
        try:
            raw_data.decode('utf-8')
            encoding = 'utf-8'
        except UnicodeDecodeError:
            encoding = 'ISO-8859-1'
    
    try:
        sample = raw_data.decode(encoding)
        dialect = csv.Sniffer().sniff(sample)
    except Exception:
        class DefaultDialect:
            delimiter = ','
            quotechar = '"'
            doublequote = True
            skipinitialspace = False
            lineterminator = '\r\n'
            quoting = csv.QUOTE_MINIMAL
        dialect = DefaultDialect()

    return encoding, dialect


def find_data_start_flexible(file_path, encoding, dialect):
    """
    Encontra a linha de início dos dados em um arquivo CSV.
    
    Args:
        file_path: Caminho do arquivo CSV
        encoding: Encoding do arquivo
        dialect: Dialeto CSV
        
    Returns:
        int ou None: Índice da linha do cabeçalho ou None se não encontrado
    """
    with open(file_path, 'r', encoding=encoding) as f:
        for i, line in enumerate(f):
            # Procura por uma linha que se pareça com o cabeçalho de dados de run
            # 'Run-Use,Heading,Run,Time (s),Distance (m),Start Time,'
            if 'Run-Use' in line and 'Heading' in line and 'Run' in line and 'Start Time' in line:
                return i  # Retorna o índice da linha do cabeçalho
    return None


def normalize_column_names(columns):
    """
    Normaliza os nomes das colunas de um DataFrame.
    
    Args:
        columns: Lista de nomes de colunas
        
    Returns:
        list: Lista de nomes normalizados
    """
    normalized = []
    seen_names = set()
    unnamed_counter = 0
    for col in columns:
        raw_name = str(col).strip()

        # Passo 1: Normalizar o nome bruto da coluna para TODOS os casos.
        # Isso lida com minúsculas, substituição de espaços, remoção de caracteres especiais, etc.
        # Ex: "Run-Use" -> "run_use", "Time (s)" -> "time_s"
        processed_name = re.sub(r'[^a-zA-Z0-9_]', '', raw_name.lower().replace(' ', '_').replace('(s)', 's').replace('(m)', 'm'))

        # Passo 2: Lidar com colunas 'Unnamed: X' geradas pelo Pandas ou strings vazias.
        # Se for uma coluna 'Unnamed:' ou vazia, atribuímos um nome genérico único.
        if raw_name.startswith('Unnamed:') or not raw_name:
            final_name = f"unnamed_col_{unnamed_counter}"
            unnamed_counter += 1
        else:
            # Caso contrário, usamos o nome já processado do Passo 1.
            final_name = processed_name

        # Passo 3: Garantir a unicidade para o nome final.
        # Se o nome final já foi visto, adicionamos um sufixo numérico.
        original_final_name = final_name
        suffix_counter = 0
        while final_name in seen_names:
            final_name = f"{original_final_name}_{suffix_counter}"
            suffix_counter += 1
        
        normalized.append(final_name)
        seen_names.add(final_name)
    return normalized
