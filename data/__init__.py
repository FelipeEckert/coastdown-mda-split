# coding: utf-8
"""Split parsing and shared data-loading package."""

import sys
from importlib import import_module
from types import ModuleType

__all__ = [
    'carregar_dados_csv_robusto',
    'default_split_interval_config',
    'extract_interval_record',
    'normalize_run_intervals',
    'parse_split_sources',
]

_EXPORTS = {
    'loaders': ('.loaders', None),
    'split_parser': ('.split_parser', None),
    'carregar_dados_csv_robusto': ('.loaders', 'carregar_dados_csv_robusto'),
    'default_split_interval_config': ('.split_parser', 'default_split_interval_config'),
    'extract_interval_record': ('.split_parser', 'extract_interval_record'),
    'normalize_run_intervals': ('.split_parser', 'normalize_run_intervals'),
    'parse_split_sources': ('.split_parser', 'parse_split_sources'),
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
