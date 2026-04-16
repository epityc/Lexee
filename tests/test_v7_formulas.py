"""Tests v7 — Ingénierie (suite) & Nombres Complexes (29 formules)."""

import math

import pytest

from app.engine.logic import FORMULAS


# ─────────────────────────────────────────────────────────────────────────────
# Fonctions d'erreur & step
# ─────────────────────────────────────────────────────────────────────────────
def test_erf_precis():
    r = FORMULAS["erf_precis"]({"x": 1})
    assert abs(r["resultat"] - math.erf(1)) < 1e-9


def test_erfc():
    assert FORMULAS["erfc"]({"x": 0})["resultat"] == 1.0


def test_erfc_precis():
    r = FORMULAS["erfc_precis"]({"x": 1})
    assert abs(r["resultat"] - math.erfc(1)) < 1e-9


def test_gestep_au_dessus():
    assert FORMULAS["gestep"]({"nombre": 5, "seuil": 3})["resultat"] == 1


def test_gestep_en_dessous():
    assert FORMULAS["gestep"]({"nombre": 2, "seuil": 3})["resultat"] == 0


def test_gestep_egal():
    # >= : 1 quand égal
    assert FORMULAS["gestep"]({"nombre": 3, "seuil": 3})["resultat"] == 1


def test_gestep_seuil_defaut():
    assert FORMULAS["gestep"]({"nombre": -1})["resultat"] == 0
    assert FORMULAS["gestep"]({"nombre": 1})["resultat"] == 1


# ─────────────────────────────────────────────────────────────────────────────
# Conversions hexadécimales
# ─────────────────────────────────────────────────────────────────────────────
def test_hex2bin():
    r = FORMULAS["hex2bin"]({"nombre": "FF"})
    assert r["resultat"] == "11111111"


def test_hex2oct():
    r = FORMULAS["hex2oct"]({"nombre": "FF"})
    assert r["resultat"] == "377"


def test_hex2bin_invalide():
    with pytest.raises(ValueError):
        FORMULAS["hex2bin"]({"nombre": "GHI"})


# ─────────────────────────────────────────────────────────────────────────────
# Propriétés complexes
# ─────────────────────────────────────────────────────────────────────────────
def test_im_abs():
    r = FORMULAS["im_abs"]({"complexe": "3+4i"})
    assert r["resultat"] == 5.0


def test_im_part_imag():
    r = FORMULAS["im_part_imag"]({"complexe": "3+4i"})
    assert r["resultat"] == 4.0


def test_im_part_reelle():
    r = FORMULAS["im_part_reelle"]({"complexe": "3+4i"})
    assert r["resultat"] == 3.0


def test_im_argument():
    r = FORMULAS["im_argument"]({"complexe": "1+i"})
    assert abs(r["resultat"] - math.pi / 4) < 1e-9


def test_im_argument_zero():
    with pytest.raises(ValueError):
        FORMULAS["im_argument"]({"complexe": "0"})


def test_im_conjugue():
    r = FORMULAS["im_conjugue"]({"complexe": "3+4i"})
    assert r["complexe"] == "3-4i"


def test_im_conjugue_j_suffixe():
    r = FORMULAS["im_conjugue"]({"complexe": "2+3j"})
    assert "j" in r["complexe"]


# ─────────────────────────────────────────────────────────────────────────────
# Arithmétique complexe
# ─────────────────────────────────────────────────────────────────────────────
def test_im_div():
    r = FORMULAS["im_div"]({"z1": "4+8i", "z2": "2+2i"})
    assert r["complexe"] == "3+i"


def test_im_div_zero():
    with pytest.raises(ValueError):
        FORMULAS["im_div"]({"z1": "1+i", "z2": "0"})


def test_im_sub():
    r = FORMULAS["im_sub"]({"z1": "5+3i", "z2": "2+i"})
    assert r["complexe"] == "3+2i"


def test_im_sum():
    r = FORMULAS["im_sum"]({"complexes": ["1+2i", "3+4i", "5+6i"]})
    assert r["complexe"] == "9+12i"


def test_im_product():
    # (1+i)*(1+i) = 1 + 2i + i² = 2i
    r = FORMULAS["im_product"]({"complexes": ["1+i", "1+i"]})
    assert r["complexe"] == "2i"


def test_im_power():
    # (2+3i)^3 = -46+9i
    r = FORMULAS["im_power"]({"complexe": "2+3i", "puissance": 3})
    assert r["complexe"] == "-46+9i"


def test_im_power_racine_carree():
    # z^0.5 = sqrt(z). sqrt(3+4i) = 2+i
    r = FORMULAS["im_power"]({"complexe": "3+4i", "puissance": 0.5})
    assert r["complexe"] == "2+i"


# ─────────────────────────────────────────────────────────────────────────────
# Exp / log / sqrt complexes
# ─────────────────────────────────────────────────────────────────────────────
def test_im_exp_zero():
    r = FORMULAS["im_exp"]({"complexe": "0"})
    assert r["complexe"] == "1"


def test_im_ln_unite():
    r = FORMULAS["im_ln"]({"complexe": "1"})
    assert r["complexe"] == "0"


def test_im_ln_zero():
    with pytest.raises(ValueError):
        FORMULAS["im_ln"]({"complexe": "0"})


def test_im_log10_unite():
    r = FORMULAS["im_log10"]({"complexe": "1"})
    assert r["complexe"] == "0"


def test_im_log2_unite():
    r = FORMULAS["im_log2"]({"complexe": "1"})
    assert r["complexe"] == "0"


def test_im_log2_puiss2():
    # log2(8) = 3
    r = FORMULAS["im_log2"]({"complexe": "8"})
    assert r["complexe"] == "3"


def test_im_sqrt():
    r = FORMULAS["im_sqrt"]({"complexe": "3+4i"})
    assert r["complexe"] == "2+i"


# ─────────────────────────────────────────────────────────────────────────────
# Trigo & hyperboliques complexes
# ─────────────────────────────────────────────────────────────────────────────
def test_im_cos_reel():
    r = FORMULAS["im_cos"]({"complexe": "0"})
    assert r["complexe"] == "1"


def test_im_sin_reel():
    r = FORMULAS["im_sin"]({"complexe": "0"})
    assert r["complexe"] == "0"


def test_im_sinh_reel():
    r = FORMULAS["im_sinh"]({"complexe": "0"})
    assert r["complexe"] == "0"


def test_im_cos_1_plus_i():
    # cos(1+i) = cos(1)cosh(1) - i sin(1)sinh(1) ≈ 0.8337 - 0.9889i
    r = FORMULAS["im_cos"]({"complexe": "1+i"})
    assert abs(r["reel"] - 0.8337300251) < 1e-8
    assert abs(r["imaginaire"] - (-0.9888977058)) < 1e-8


def test_im_cot():
    # cot(pi/4) ≈ 1
    r = FORMULAS["im_cot"]({"complexe": str(math.pi / 4)})
    assert abs(r["reel"] - 1) < 1e-8


def test_im_csc():
    # csc(pi/2) = 1
    r = FORMULAS["im_csc"]({"complexe": str(math.pi / 2)})
    assert abs(r["reel"] - 1) < 1e-8


def test_im_csch():
    # csch(x) = 1/sinh(x). sinh(1) ≈ 1.1752
    r = FORMULAS["im_csch"]({"complexe": "1"})
    assert abs(r["reel"] - (1 / math.sinh(1))) < 1e-8


def test_im_sec():
    r = FORMULAS["im_sec"]({"complexe": "0"})
    assert r["complexe"] == "1"


def test_im_sech():
    r = FORMULAS["im_sech"]({"complexe": "0"})
    assert r["complexe"] == "1"


# ─────────────────────────────────────────────────────────────────────────────
# Parsing robuste
# ─────────────────────────────────────────────────────────────────────────────
def test_parse_i_seul():
    r = FORMULAS["im_abs"]({"complexe": "i"})
    assert r["resultat"] == 1.0


def test_parse_moins_i():
    r = FORMULAS["im_conjugue"]({"complexe": "-i"})
    assert r["complexe"] == "i"


def test_parse_reel_pur():
    r = FORMULAS["im_abs"]({"complexe": "5"})
    assert r["resultat"] == 5.0


# ─────────────────────────────────────────────────────────────────────────────
# Smoke test registre
# ─────────────────────────────────────────────────────────────────────────────
def test_registre_complet_v7():
    from app.engine.logic import FORMULA_META
    assert len(FORMULAS) == 242
    assert len(FORMULA_META) == 242
    assert set(FORMULAS.keys()) == set(FORMULA_META.keys())
