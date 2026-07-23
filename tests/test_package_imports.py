"""Compatibility and dependency boundaries for package initializers."""

from importlib import import_module
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
CORE_EXPORTS = {
    "calcular_energia": "core.calculations",
    "DEFAULT_SPLIT_INTERVAL_CONFIG": "core.split_calculations",
    "calculate_split_coefficients": "core.split_calculations",
    "calculate_split_result": "core.split_calculations",
    "coefficient_summary": "core.split_calculations",
    "delta_v_kmh": "core.split_calculations",
    "kmh_to_ms": "core.split_calculations",
    "validate_split_inputs": "core.split_calculations",
}
DATA_EXPORTS = {
    "carregar_dados_csv_robusto": "data.loaders",
    "default_split_interval_config": "data.split_parser",
    "extract_interval_record": "data.split_parser",
    "normalize_run_intervals": "data.split_parser",
    "parse_split_sources": "data.split_parser",
}


def run_python(source):
    return subprocess.run(
        [sys.executable, "-c", source],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )


class PackageImportTests(unittest.TestCase):
    def test_representative_split_imports_skip_legacy_and_optional_modules(self):
        result = run_python(
            """
import sys

blocked = {"chardet", "numpy", "openpyxl", "pandas", "streamlit"}

class Blocker:
    def find_spec(self, fullname, path=None, target=None):
        if fullname.partition(".")[0] in blocked:
            raise ModuleNotFoundError(fullname)

sys.meta_path.insert(0, Blocker())
import core.split_calculations
import core.split_state
import data.split_parser

unrelated = {
    "core.calculations",
    "data.loaders",
    "streamlit",
}
assert unrelated.isdisjoint(sys.modules), unrelated & sys.modules.keys()
"""
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_supported_package_exports_keep_object_identity(self):
        for package_name, exports in (("core", CORE_EXPORTS), ("data", DATA_EXPORTS)):
            with self.subTest(package=package_name):
                namespace = {}
                exec(f"from {package_name} import {', '.join(exports)}", namespace)
                package = import_module(package_name)
                self.assertEqual(package.__all__, list(exports))
                for name, module_name in exports.items():
                    expected = getattr(import_module(module_name), name)
                    self.assertIs(namespace[name], expected)
                    self.assertIs(getattr(package, name), expected)

        from core import calculations, split_calculations
        from data import loaders, split_parser

        self.assertIs(calculations, import_module("core.calculations"))
        self.assertIs(split_calculations, import_module("core.split_calculations"))
        self.assertIs(loaders, import_module("data.loaders"))
        self.assertIs(split_parser, import_module("data.split_parser"))

    def test_package_export_identity_is_stable_before_first_access(self):
        for package_name, module_name, export in (
            ("core", "core.split_calculations", "calculate_split_result"),
            ("data", "data.split_parser", "default_split_interval_config"),
        ):
            with self.subTest(package=package_name, export=export):
                result = run_python(
                    f"""
from importlib import import_module
from unittest.mock import patch

package = import_module("{package_name}")
sentinel = object()
with patch("{module_name}.{export}", sentinel):
    package_export = getattr(package, "{export}")
source_export = getattr(import_module("{module_name}"), "{export}")
assert package_export is source_export
assert package_export is not sentinel
"""
                )
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_package_export_remains_patchable(self):
        import core
        from core.split_calculations import calculate_split_result

        self.assertIs(
            core.calculate_split_result,
            calculate_split_result,
        )
        sentinel = object()
        with patch.object(core, "calculate_split_result", sentinel):
            self.assertIs(core.calculate_split_result, sentinel)
        self.assertIs(
            core.calculate_split_result,
            calculate_split_result,
        )

    def test_package_and_submodule_import_orders_do_not_cycle(self):
        for source in (
            "import core; import data.split_parser; from data import carregar_dados_csv_robusto; from core import calculate_split_result",
            "import data; import core.split_calculations; from core import calcular_energia; from data import parse_split_sources",
        ):
            with self.subTest(source=source):
                result = run_python(source)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_heavy_dependency_error_is_deferred_until_export_access(self):
        result = run_python(
            """
import sys

sys.modules["pandas"] = None
package = __import__("data")
try:
    package.carregar_dados_csv_robusto
except ModuleNotFoundError as error:
    assert error.name == "pandas", error.name
else:
    raise AssertionError("expected missing pandas")
"""
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
