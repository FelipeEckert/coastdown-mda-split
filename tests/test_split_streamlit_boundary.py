"""Behavioral dependency boundary for UI-neutral Split modules."""

from pathlib import Path
import subprocess
import sys
import unittest


ROOT_DIR = Path(__file__).resolve().parents[1]
STREAMLIT_FREE_MODULES = (
    "core.split_candidate_generation",
    "core.split_candidate_set_validation",
    "core.split_comparison_merge",
    "core.split_time_validation",
    "core.split_vehicle_mass",
)


class SplitStreamlitBoundaryTests(unittest.TestCase):
    def test_modules_import_when_streamlit_is_unavailable(self):
        for module_name in STREAMLIT_FREE_MODULES:
            with self.subTest(module=module_name):
                result = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        (
                            "import sys; "
                            "sys.modules['streamlit'] = None; "
                            f"import {module_name}"
                        ),
                    ],
                    cwd=ROOT_DIR,
                    capture_output=True,
                    text=True,
                    check=False,
                )

                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
