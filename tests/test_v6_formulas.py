"""Tests v6 — Ingénierie & Mathématiques Avancées (21 formules)."""

import math

import pytest

from app.engine.logic import FORMULAS


# ─────────────────────────────────────────────────────────────────────────────
# Hyperboliques & réciproques
# ─────────────────────────────────────────────────────────────────────────────
def test_acosh():
    r = FORMULAS["acosh"]({"x": 2})
    assert abs(r["resultat"] - math.acosh(2)) < 1e-9


def test_acosh_invalide():
    with pytest.raises(ValueError):
        FORMULAS["acosh"]({"x": 0.5})


def test_asinh():
    r = FORMULAS["asinh"]({"x": 1})
    assert abs(r["resultat"] - math.asinh(1)) < 1e-9


def test_atanh():
    r = FORMULAS["atanh"]({"x": 0.5})
    assert abs(r["resultat"] - math.atanh(0.5)) < 1e-9


def test_atanh_invalide():
    with pytest.raises(ValueError):
        FORMULAS["atanh"]({"x": 1})


def test_cosh():
    assert FORMULAS["cosh"]({"x": 0})["resultat"] == 1.0


def test_cot():
    r = FORMULAS["cot"]({"x": math.pi / 4})
    assert abs(r["resultat"] - 1) < 1e-9


def test_coth():
    r = FORMULAS["coth"]({"x": 1})
    assert abs(r["resultat"] - (1 / math.tanh(1))) < 1e-9


def test_csc():
    r = FORMULAS["csc"]({"x": math.pi / 2})
    assert abs(r["resultat"] - 1) < 1e-9


def test_csch():
    r = FORMULAS["csch"]({"x": 1})
    assert abs(r["resultat"] - (1 / math.sinh(1))) < 1e-9


# ─────────────────────────────────────────────────────────────────────────────
# Conversions de bases
# ─────────────────────────────────────────────────────────────────────────────
def test_base_16():
    r = FORMULAS["base"]({"nombre": 255, "base": 16})
    assert r["resultat"] == "FF"


def test_base_longueur_min():
    r = FORMULAS["base"]({"nombre": 5, "base": 2, "longueur_min": 8})
    assert r["resultat"] == "00000101"


def test_base_invalide():
    with pytest.raises(ValueError):
        FORMULAS["base"]({"nombre": 5, "base": 1})


def test_decimal_base_hex():
    r = FORMULAS["decimal_base"]({"texte": "FF", "base": 16})
    assert r["resultat"] == 255


def test_decimal_base_bin():
    r = FORMULAS["decimal_base"]({"texte": "1010", "base": 2})
    assert r["resultat"] == 10


def test_bin2dec():
    r = FORMULAS["bin2dec"]({"nombre": "1010"})
    assert r["resultat"] == 10


def test_bin2oct():
    r = FORMULAS["bin2oct"]({"nombre": "1000"})
    assert r["resultat"] == "10"  # 8 en octal


def test_dec2oct():
    r = FORMULAS["dec2oct"]({"nombre": 8})
    assert r["resultat"] == "10"


# ─────────────────────────────────────────────────────────────────────────────
# Opérations bit à bit
# ─────────────────────────────────────────────────────────────────────────────
def test_bit_lshift():
    r = FORMULAS["bit_lshift"]({"nombre": 4, "decalage": 2})
    assert r["resultat"] == 16


def test_bit_lshift_negatif():
    # décalage négatif = shift droite
    r = FORMULAS["bit_lshift"]({"nombre": 16, "decalage": -2})
    assert r["resultat"] == 4


def test_bit_rshift():
    r = FORMULAS["bit_rshift"]({"nombre": 16, "decalage": 2})
    assert r["resultat"] == 4


# ─────────────────────────────────────────────────────────────────────────────
# Combinatoire & complexes
# ─────────────────────────────────────────────────────────────────────────────
def test_combinaison_rep():
    # C(5+3-1, 3) = C(7, 3) = 35
    r = FORMULAS["combinaison_rep"]({"n": 5, "k": 3})
    assert r["resultat"] == 35


def test_combinaison_rep_k0():
    r = FORMULAS["combinaison_rep"]({"n": 5, "k": 0})
    assert r["resultat"] == 1


def test_complexe_3_4i():
    r = FORMULAS["complexe"]({"reel": 3, "imaginaire": 4})
    assert r["complexe"] == "3+4i"


def test_complexe_reel_seul():
    r = FORMULAS["complexe"]({"reel": 5, "imaginaire": 0})
    assert r["complexe"] == "5"


def test_complexe_imag_seul():
    r = FORMULAS["complexe"]({"reel": 0, "imaginaire": 1})
    assert r["complexe"] == "i"


def test_complexe_imag_neg():
    r = FORMULAS["complexe"]({"reel": 3, "imaginaire": -4, "suffixe": "j"})
    assert r["complexe"] == "3-4j"


# ─────────────────────────────────────────────────────────────────────────────
# Fonctions de Bessel (valeurs de référence Excel/tables)
# ─────────────────────────────────────────────────────────────────────────────
def test_bessel_j_0_0():
    r = FORMULAS["bessel_j"]({"x": 0, "n": 0})
    assert r["resultat"] == 1.0


def test_bessel_j_1_0():
    # J_0(1) ≈ 0.7651976866
    r = FORMULAS["bessel_j"]({"x": 1, "n": 0})
    assert abs(r["resultat"] - 0.7651976866) < 1e-8


def test_bessel_j_2_1():
    # J_1(2) ≈ 0.5767248078
    r = FORMULAS["bessel_j"]({"x": 2, "n": 1})
    assert abs(r["resultat"] - 0.5767248078) < 1e-8


def test_bessel_i_1_0():
    # I_0(1) ≈ 1.2660658732
    r = FORMULAS["bessel_i"]({"x": 1, "n": 0})
    assert abs(r["resultat"] - 1.2660658732) < 1e-6


def test_bessel_i_2_1():
    # I_1(2) ≈ 1.5906368546
    r = FORMULAS["bessel_i"]({"x": 2, "n": 1})
    assert abs(r["resultat"] - 1.5906368546) < 1e-6


def test_bessel_y_1_0():
    # Y_0(1) ≈ 0.0882569642
    r = FORMULAS["bessel_y"]({"x": 1, "n": 0})
    assert abs(r["resultat"] - 0.0882569642) < 1e-6


def test_bessel_y_2_1():
    # Y_1(2) ≈ -0.1070324315
    r = FORMULAS["bessel_y"]({"x": 2, "n": 1})
    assert abs(r["resultat"] - (-0.1070324315)) < 1e-6


def test_bessel_y_x_invalide():
    with pytest.raises(ValueError):
        FORMULAS["bessel_y"]({"x": 0, "n": 0})


def test_bessel_k_1_0():
    # K_0(1) ≈ 0.4210244382
    r = FORMULAS["bessel_k"]({"x": 1, "n": 0})
    assert abs(r["resultat"] - 0.4210244382) < 1e-6


def test_bessel_k_2_1():
    # K_1(2) ≈ 0.1398658818
    r = FORMULAS["bessel_k"]({"x": 2, "n": 1})
    assert abs(r["resultat"] - 0.1398658818) < 1e-6


def test_bessel_k_x_invalide():
    with pytest.raises(ValueError):
        FORMULAS["bessel_k"]({"x": -1, "n": 0})


# ─────────────────────────────────────────────────────────────────────────────
# Smoke test registre
# ─────────────────────────────────────────────────────────────────────────────
def test_registre_complet_v6():
    from app.engine.logic import FORMULA_META
    assert len(FORMULAS) == 300
    assert len(FORMULA_META) == 300
    assert set(FORMULAS.keys()) == set(FORMULA_META.keys())
