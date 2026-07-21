# coding: utf-8
"""Compatibility tests for the inherited corrected-pair APIs."""

from inspect import Parameter, signature
import unittest
from unittest.mock import patch

import core
from core import calculations, corrections


RICH_KEYS = (
    "pair_id", "run1", "run2", "f0_ida_raw", "f2_ida_raw",
    "f0_volta_raw", "f2_volta_raw", "f0_ida_corr", "f2_ida_corr",
    "f0_volta_corr", "f2_volta_corr", "mean_f0_corrected",
    "mean_f2_corrected", "cv_f0_corrected", "cv_f2_corrected", "energy",
    "mean_energy_corrected", "temp_ida_used", "temp_volta_used",
    "press_ida_used", "press_volta_used", "f0_mean", "f2_mean", "f0_corr",
    "f2_corr", "cv_f0", "cv_f2", "corrected",
)
DIRECT_KEYS = (
    "f0_ida_raw", "f2_ida_raw", "f0_volta_raw", "f2_volta_raw",
    "f0_ida_corr", "f2_ida_corr", "f0_volta_corr", "f2_volta_corr",
    "mean_f0_corrected", "mean_f2_corrected", "cv_f0_corrected",
    "cv_f2_corrected", "energy", "temp", "press",
)
SHARED_KEYS = DIRECT_KEYS[:-2]


class CorrectedPairCompatibilityTest(unittest.TestCase):
    coeffs = {
        7: {"f0": 123.45678901234567, "f2": 0.9876543210987654},
        9: {"f0": 98.76543210987654, "f2": 0.4567890123456789},
    }
    rich_args = (7, 9, coeffs, 23.456789, 97.654321, 23.456789, 97.654321)
    direct_args = (
        coeffs[7]["f0"], coeffs[7]["f2"], coeffs[9]["f0"],
        coeffs[9]["f2"], 23.456789, 97.654321,
    )

    def test_all_import_paths_preserve_valid_contracts(self):
        self.assertIs(
            core.calculate_single_pair_corrected_data,
            corrections.calculate_single_pair_corrected_data,
        )
        self.assertIs(
            core.calculate_single_pair_corrected_data2,
            corrections.calculate_single_pair_corrected_data2,
        )
        rich_functions = (
            corrections.calculate_single_pair_corrected_data,
            calculations.calculate_single_pair_corrected_data,
        )
        direct_functions = (
            corrections.calculate_single_pair_corrected_data2,
            calculations.calculate_single_pair_corrected_data2,
        )
        for function in rich_functions:
            parameters = tuple(signature(function).parameters.values())
            self.assertEqual(
                tuple(parameter.name for parameter in parameters),
                (
                    "run_ida_id", "run_volta_id", "individual_coeffs",
                    "temp_ida_c", "press_ida_kpa", "temp_volta_c",
                    "press_volta_kpa",
                ),
            )
            self.assertTrue(
                all(parameter.default is Parameter.empty for parameter in parameters)
            )
        for function in direct_functions:
            parameters = tuple(signature(function).parameters.values())
            self.assertEqual(
                tuple(parameter.name for parameter in parameters),
                (
                    "f0_ida_raw", "f2_ida_raw", "f0_volta_raw",
                    "f2_volta_raw", "temp_c", "press_kpa",
                ),
            )
            self.assertTrue(
                all(parameter.default is Parameter.empty for parameter in parameters)
            )
        rich = corrections.calculate_single_pair_corrected_data(*self.rich_args)
        direct = corrections.calculate_single_pair_corrected_data2(*self.direct_args)

        self.assertEqual(tuple(rich), RICH_KEYS)
        self.assertEqual(tuple(direct), DIRECT_KEYS)
        self.assertEqual(
            [rich[key] for key in SHARED_KEYS],
            [direct[key] for key in SHARED_KEYS],
        )
        self.assertEqual(direct["f0_ida_corr"], 127.12696001635118)
        self.assertEqual(direct["f2_volta_corr"], 0.03696382076625303)
        self.assertEqual(direct["energy"], 6.717838107889561)
        self.assertEqual(
            {key: type(value) for key, value in rich.items()},
            {
                **{key: float for key in RICH_KEYS[3:-1]},
                "pair_id": str,
                "run1": int,
                "run2": int,
                "corrected": bool,
            },
        )
        self.assertTrue(all(type(value) is float for value in direct.values()))

        for function in rich_functions[1:]:
            self.assertEqual(function(*self.rich_args), rich)
        for function in direct_functions[1:]:
            self.assertEqual(function(*self.direct_args), direct)

    def test_missing_coefficients_keep_zero_default_behavior(self):
        rich = corrections.calculate_single_pair_corrected_data(
            7, 9, {7: {"f0": 1.25}, 9: {"f2": 0.5}},
            20.0, 101.325, 20.0, 101.325,
        )
        direct = corrections.calculate_single_pair_corrected_data2(
            1.25, 0.0, 0.0, 0.5, 20.0, 101.325,
        )

        self.assertEqual(rich["f2_ida_raw"], 0.0)
        self.assertEqual(rich["f0_volta_raw"], 0.0)
        self.assertEqual(
            [rich[key] for key in SHARED_KEYS],
            [direct[key] for key in SHARED_KEYS],
        )
        with self.assertRaises(TypeError):
            corrections.calculate_single_pair_corrected_data(*self.rich_args[:-1])
        with self.assertRaises(TypeError):
            corrections.calculate_single_pair_corrected_data2(*self.direct_args[:-1])

    def test_invalid_inputs_raise_equivalent_exceptions(self):
        cases = (
            (
                (7, 9, self.coeffs, 20.0, 0.0, 20.0, 101.325),
                (*self.direct_args[:4], 20.0, 0.0),
                ZeroDivisionError,
                ("float division by zero",),
            ),
            (
                (7, 9, self.coeffs, None, 101.325, None, 101.325),
                (*self.direct_args[:4], None, 101.325),
                TypeError,
                ("unsupported operand type(s) for +: 'NoneType' and 'float'",),
            ),
        )

        for rich_args, direct_args, error_type, error_args in cases:
            with self.subTest(error=error_type.__name__):
                with self.assertRaises(error_type) as rich_error:
                    corrections.calculate_single_pair_corrected_data(*rich_args)
                with self.assertRaises(error_type) as direct_error:
                    corrections.calculate_single_pair_corrected_data2(*direct_args)
                self.assertEqual(rich_error.exception.args, error_args)
                self.assertEqual(direct_error.exception.args, error_args)

    def test_adapters_delegate_through_runtime_lookup(self):
        sentinel = object()
        with patch(
            "core.corrections._calculate_single_pair_corrected_data",
            return_value=sentinel,
        ) as correction_entry:
            self.assertIs(
                corrections.calculate_single_pair_corrected_data(*self.rich_args),
                sentinel,
            )
            correction_entry.assert_called_once_with(
                *self.rich_args,
                corrections.calcular_energia,
            )

        canonical_result = {key: float(index) for index, key in enumerate(SHARED_KEYS)}
        with patch(
            "core.corrections._calculate_single_pair_corrected_data",
            return_value=canonical_result,
        ) as canonical:
            result = corrections.calculate_single_pair_corrected_data2(*self.direct_args)

        canonical.assert_called_once_with(
            0, 1,
            {
                0: {"f0": self.direct_args[0], "f2": self.direct_args[1]},
                1: {"f0": self.direct_args[2], "f2": self.direct_args[3]},
            },
            self.direct_args[4], self.direct_args[5],
            self.direct_args[4], self.direct_args[5],
            corrections.calcular_energia,
        )
        self.assertEqual(
            result,
            {
                **canonical_result,
                "temp": self.direct_args[4],
                "press": self.direct_args[5],
            },
        )

        with patch(
            "core.corrections._calculate_single_pair_corrected_data",
            return_value=sentinel,
        ) as rich_compat:
            self.assertIs(
                calculations.calculate_single_pair_corrected_data(*self.rich_args),
                sentinel,
            )
            rich_compat.assert_called_once_with(
                *self.rich_args,
                calculations.calcular_energia,
            )

        with patch(
            "core.corrections._calculate_single_pair_corrected_data2",
            return_value=sentinel,
        ) as direct_compat:
            self.assertIs(
                calculations.calculate_single_pair_corrected_data2(*self.direct_args),
                sentinel,
            )
            direct_compat.assert_called_once_with(
                *self.direct_args,
                calculations.calcular_energia,
            )

    def test_calculations_wrappers_keep_their_energy_runtime_lookup(self):
        expected_rich = corrections.calculate_single_pair_corrected_data(
            *self.rich_args
        )
        expected_direct = corrections.calculate_single_pair_corrected_data2(
            *self.direct_args
        )
        sentinel = object()

        with patch(
            "core.calculations.calcular_energia",
            return_value=sentinel,
        ) as patched_energy:
            rich = calculations.calculate_single_pair_corrected_data(*self.rich_args)
            direct = calculations.calculate_single_pair_corrected_data2(
                *self.direct_args
            )
            correction_rich = corrections.calculate_single_pair_corrected_data(
                *self.rich_args
            )
            correction_direct = corrections.calculate_single_pair_corrected_data2(
                *self.direct_args
            )

        self.assertIs(rich["energy"], sentinel)
        self.assertIs(rich["mean_energy_corrected"], sentinel)
        self.assertIs(direct["energy"], sentinel)
        self.assertEqual(patched_energy.call_count, 2)
        self.assertEqual(correction_rich, expected_rich)
        self.assertEqual(correction_direct, expected_direct)


if __name__ == "__main__":
    unittest.main()
