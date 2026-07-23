# coding: utf-8
"""Neutral energy calculation shared by the active Split workflow."""


def calcular_energia(f0, f2):
    """
    Calcula a energia combinada a partir dos coeficientes F0 e F2.

    Args:
        f0: Coeficiente F0
        f2: Coeficiente F2

    Returns:
        float: Energia combinada em MJ/km
    """
    # Constantes conforme planilha original
    const_F0_city = 79.0100212980278
    const_F2_city = 101261.439856478
    const_F0_hwy = 73.4212978755833
    const_F2_hwy = 190140.972556837
    const_mph0 = 4.4497179
    const_mph2 = 1.7381710546875

    # Calcula energia em MJ/km
    energy_city = ((f0 / const_mph0) * const_F0_city + (f2 / const_mph2) * const_F2_city) / 1000
    energy_hwy = ((f0 / const_mph0) * const_F0_hwy + (f2 / const_mph2) * const_F2_hwy) / 1000
    energy_comb = (energy_city * 0.55) + (energy_hwy * 0.45)
    return energy_comb
