# coding: utf-8
"""Core modules for the active Split workflow."""

import sys
from importlib import import_module
from types import ModuleType

__all__ = [
    'calcular_energia',
    'DEFAULT_SPLIT_INTERVAL_CONFIG',
    'calculate_split_coefficients',
    'calculate_split_result',
    'coefficient_summary',
    'delta_v_kmh',
    'kmh_to_ms',
    'validate_split_inputs',
]

_EXPORTS = {
    'calculations': ('.calculations', None),
    'split_calculations': ('.split_calculations', None),
    'calcular_energia': ('.calculations', 'calcular_energia'),
    'DEFAULT_SPLIT_INTERVAL_CONFIG': ('.split_calculations', 'DEFAULT_SPLIT_INTERVAL_CONFIG'),
    'calculate_split_coefficients': ('.split_calculations', 'calculate_split_coefficients'),
    'calculate_split_result': ('.split_calculations', 'calculate_split_result'),
    'coefficient_summary': ('.split_calculations', 'coefficient_summary'),
    'delta_v_kmh': ('.split_calculations', 'delta_v_kmh'),
    'kmh_to_ms': ('.split_calculations', 'kmh_to_ms'),
    'validate_split_inputs': ('.split_calculations', 'validate_split_inputs'),
}


class _LazyExportsModule(ModuleType):
    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        source = f'.{name}'
        for export, (module_name, attribute) in _EXPORTS.items():
            if module_name == source and attribute is not None:
                self.__dict__.setdefault(export, getattr(value, attribute))


sys.modules[__name__].__class__ = _LazyExportsModule


def __getattr__(name):
    try:
        module_name, attribute = _EXPORTS[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None
    module = import_module(module_name, __name__)
    value = module if attribute is None else getattr(module, attribute)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(_EXPORTS))
