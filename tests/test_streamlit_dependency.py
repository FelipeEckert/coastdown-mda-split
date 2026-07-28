"""Dependency contract tests for active Streamlit APIs."""

from pathlib import Path
import unittest

from packaging.requirements import Requirement
from packaging.version import Version


ROOT_DIR = Path(__file__).resolve().parents[1]
REQUIRED_STREAMLIT_VERSION = Version("1.60.0")


class StreamlitDependencyTests(unittest.TestCase):
    def test_declared_minimum_supports_active_apis(self):
        requirements = [
            Requirement(line)
            for line in (ROOT_DIR / "requirements.txt").read_text().splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        streamlit = next(
            requirement
            for requirement in requirements
            if requirement.name.lower() == "streamlit"
        )
        lower_bounds = [
            Version(specifier.version)
            for specifier in streamlit.specifier
            if specifier.operator in {">", ">=", "~="}
        ]

        self.assertEqual(max(lower_bounds), REQUIRED_STREAMLIT_VERSION)
        self.assertTrue(streamlit.specifier.contains(REQUIRED_STREAMLIT_VERSION))


if __name__ == "__main__":
    unittest.main()
