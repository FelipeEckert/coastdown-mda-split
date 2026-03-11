# coding: utf-8
"""
Módulo de utilitários para análise de coastdown.
"""

from .file_utils import (
    detect_encoding_and_dialect,
    find_data_start_flexible,
    normalize_column_names,
)

__all__ = [
    'detect_encoding_and_dialect',
    'find_data_start_flexible',
    'normalize_column_names',
]
