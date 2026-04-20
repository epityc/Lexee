"""Tests v18 — Ingénierie & Nombres Complexes (Groupe 13, 25 formules)."""

import cmath
import math

import pytest

from app.engine.logic import FORMULAS


# ─────────────────────────────────────────────────────────────────────────────
# BESSEL FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────
def test_besseli_zero_order():
    r = FORMULAS["besseli"]({"x": 0, "n": 0})
    assert abs(r["resultat"] - 1.0) < 1e-6


def test_besseli_positive():
    r = FORMULAS["besseli"]({"x": 1, "n": 0})
    assert abs(r["resultat"] - 1.2661) < 0.001


def test_besselj_zero_order():
    r = FORMULAS["besselj"]({"x": 0, "n": 0})
    assert abs(r["resultat"] - 1.0) < 1e-6


def test_besselj_first_order():
    r = FORMULAS["besselj"]({"x": 1, "n": 1})
    assert abs(r["resultat"] - 0.4401) < 0.001


def test_besselk_positive():
    r = FORMULAS["besselk"]({"x": 1, "n": 0})
    assert abs(r["resultat"] - 0.4210) < 0.01


def test_besselk_invalid():
    with pytest.raises(ValueError):
        FORMULAS["besselk"]({"x": 0, "n": 0})


def test_bessely_positive():
    r = FORMULAS["bessely"]({"x": 1, "n": 0})
    assert abs(r["resultat"] - 0.0883) < 0.01


def test_bessely_invalid():
    with pytest.raises(ValueError):
        FORMULAS["bessely"]({"x": 0, "n": 0})


# ─────────────────────────────────────────────────────────────────────────────
# COMPLEX
# ─────────────────────────────────────────────────────────────────────────────
def test_complex_val():
    r = FORMULAS["complex_val"]({"reel": 3, "imaginaire": 4})
    assert r["resultat"] == "3+4i"


def test_complex_val_negative_imag():
    r = FORMULAS["complex_val"]({"reel": 3, "imaginaire": -4})
    assert r["resultat"] == "3-4i"


def test_complex_val_pure_real():
    r = FORMULAS["complex_val"]({"reel": 5, "imaginaire": 0})
    assert r["resultat"] == "5"


def test_complex_val_pure_imag():
    r = FORMULAS["complex_val"]({"reel": 0, "imaginaire": 4})
    assert r["resultat"] == "4i"


def test_complex_val_unit_imag():
    r = FORMULAS["complex_val"]({"reel": 0, "imaginaire": 1})
    assert r["resultat"] == "i"


# ─────────────────────────────────────────────────────────────────────────────
# IMABS / IMAGINARY / IMREAL / IMARGUMENT / IMCONJUGATE
# ─────────────────────────────────────────────────────────────────────────────
def test_imabs():
    r = FORMULAS["imabs"]({"nombre": "3+4i"})
    assert abs(r["resultat"] - 5.0) < 1e-9


def test_imaginary():
    r = FORMULAS["imaginary"]({"nombre": "3+4i"})
    assert r["resultat"] == 4.0


def test_imreal():
    r = FORMULAS["imreal"]({"nombre": "3+4i"})
    assert r["resultat"] == 3.0


def test_imargument():
    r = FORMULAS["imargument"]({"nombre": "1+1i"})
    assert abs(r["resultat"] - math.pi / 4) < 1e-9


def test_imargument_zero():
    with pytest.raises(ValueError):
        FORMULAS["imargument"]({"nombre": "0"})


def test_imconjugate():
    r = FORMULAS["imconjugate"]({"nombre": "3+4i"})
    assert r["resultat"] == "3-4i"


# ─────────────────────────────────────────────────────────────────────────────
# IMCOS / IMSIN / IMCOT / IMCSC / IMSEC / IMCSCH / IMSECH
# ─────────────────────────────────────────────────────────────────────────────
def test_imcos():
    from app.engine._v18 import _parse_complex, _format_complex
    r = FORMULAS["imcos"]({"nombre": "0"})
    c = _parse_complex(r["resultat"])
    assert abs(c - 1.0) < 1e-9


def test_imsin():
    from app.engine._v18 import _parse_complex
    r = FORMULAS["imsin"]({"nombre": "0"})
    c = _parse_complex(r["resultat"])
    assert abs(c) < 1e-9


def test_imcot():
    from app.engine._v18 import _parse_complex
    r = FORMULAS["imcot"]({"nombre": "1"})
    c = _parse_complex(r["resultat"])
    expected = math.cos(1) / math.sin(1)
    assert abs(c.real - expected) < 1e-6


def test_imcsc():
    from app.engine._v18 import _parse_complex
    r = FORMULAS["imcsc"]({"nombre": "1"})
    c = _parse_complex(r["resultat"])
    expected = 1 / math.sin(1)
    assert abs(c.real - expected) < 1e-6


def test_imsec():
    from app.engine._v18 import _parse_complex
    r = FORMULAS["imsec"]({"nombre": "1"})
    c = _parse_complex(r["resultat"])
    expected = 1 / math.cos(1)
    assert abs(c.real - expected) < 1e-6


def test_imcsch():
    from app.engine._v18 import _parse_complex
    r = FORMULAS["imcsch"]({"nombre": "1"})
    c = _parse_complex(r["resultat"])
    expected = 1 / math.sinh(1)
    assert abs(c.real - expected) < 1e-6


def test_imsech():
    from app.engine._v18 import _parse_complex
    r = FORMULAS["imsech"]({"nombre": "1"})
    c = _parse_complex(r["resultat"])
    expected = 1 / math.cosh(1)
    assert abs(c.real - expected) < 1e-6


# ─────────────────────────────────────────────────────────────────────────────
# IMDIV / IMEXP / IMLN / IMLOG10 / IMLOG2 / IMPOWER / IMPRODUCT
# ─────────────────────────────────────────────────────────────────────────────
def test_imdiv():
    from app.engine._v18 import _parse_complex
    r = FORMULAS["imdiv"]({"nombre1": "2+4i", "nombre2": "1+1i"})
    c = _parse_complex(r["resultat"])
    expected = (2 + 4j) / (1 + 1j)
    assert abs(c - expected) < 1e-9


def test_imdiv_zero():
    with pytest.raises(ValueError):
        FORMULAS["imdiv"]({"nombre1": "1+1i", "nombre2": "0"})


def test_imexp():
    from app.engine._v18 import _parse_complex
    r = FORMULAS["imexp"]({"nombre": "0"})
    c = _parse_complex(r["resultat"])
    assert abs(c - 1.0) < 1e-9


def test_imln():
    from app.engine._v18 import _parse_complex
    r = FORMULAS["imln"]({"nombre": "1"})
    c = _parse_complex(r["resultat"])
    assert abs(c) < 1e-9


def test_imln_zero():
    with pytest.raises(ValueError):
        FORMULAS["imln"]({"nombre": "0"})


def test_imlog10():
    from app.engine._v18 import _parse_complex
    r = FORMULAS["imlog10"]({"nombre": "100"})
    c = _parse_complex(r["resultat"])
    assert abs(c.real - 2.0) < 1e-9


def test_imlog2():
    from app.engine._v18 import _parse_complex
    r = FORMULAS["imlog2"]({"nombre": "8"})
    c = _parse_complex(r["resultat"])
    assert abs(c.real - 3.0) < 1e-9


def test_impower():
    from app.engine._v18 import _parse_complex
    r = FORMULAS["impower"]({"nombre": "2+0i", "puissance": 3})
    c = _parse_complex(r["resultat"])
    assert abs(c.real - 8.0) < 1e-9


def test_improduct():
    from app.engine._v18 import _parse_complex
    r = FORMULAS["improduct"]({"nombres": ["1+1i", "1-1i"]})
    c = _parse_complex(r["resultat"])
    assert abs(c - 2.0) < 1e-9


def test_improduct_three():
    from app.engine._v18 import _parse_complex
    r = FORMULAS["improduct"]({"nombres": ["2", "3", "4"]})
    c = _parse_complex(r["resultat"])
    assert abs(c - 24.0) < 1e-9


# ─────────────────────────────────────────────────────────────────────────────
# CONVERT
# ─────────────────────────────────────────────────────────────────────────────
def test_convert_km_to_mi():
    r = FORMULAS["convert"]({"nombre": 100, "de": "km", "a": "mi"})
    assert abs(r["resultat"] - 62.1371) < 0.01


def test_convert_kg_to_lbm():
    r = FORMULAS["convert"]({"nombre": 1, "de": "kg", "a": "lbm"})
    assert abs(r["resultat"] - 2.2046) < 0.01


def test_convert_celsius_to_fahrenheit():
    r = FORMULAS["convert"]({"nombre": 100, "de": "C", "a": "F"})
    assert abs(r["resultat"] - 212.0) < 0.01


def test_convert_fahrenheit_to_celsius():
    r = FORMULAS["convert"]({"nombre": 32, "de": "F", "a": "C"})
    assert abs(r["resultat"] - 0.0) < 0.01


def test_convert_same_unit():
    r = FORMULAS["convert"]({"nombre": 42, "de": "m", "a": "m"})
    assert r["resultat"] == 42


def test_convert_liters_to_gal():
    r = FORMULAS["convert"]({"nombre": 1, "de": "gal", "a": "l"})
    assert abs(r["resultat"] - 3.7854) < 0.01


def test_convert_invalid():
    with pytest.raises(ValueError):
        FORMULAS["convert"]({"nombre": 1, "de": "kg", "a": "m"})


def test_convert_kelvin():
    r = FORMULAS["convert"]({"nombre": 0, "de": "C", "a": "K"})
    assert abs(r["resultat"] - 273.15) < 0.01


def test_convert_energy():
    r = FORMULAS["convert"]({"nombre": 1, "de": "kWh", "a": "J"})
    assert abs(r["resultat"] - 3.6e6) < 100


# ─────────────────────────────────────────────────────────────────────────────
# IMSINH / IMSQRT / IMSUB / IMSUM (Groupe 14)
# ─────────────────────────────────────────────────────────────────────────────
def test_imsinh():
    from app.engine._v18 import _parse_complex
    r = FORMULAS["imsinh"]({"nombre": "0"})
    c = _parse_complex(r["resultat"])
    assert abs(c) < 1e-9


def test_imsinh_real():
    from app.engine._v18 import _parse_complex
    r = FORMULAS["imsinh"]({"nombre": "1"})
    c = _parse_complex(r["resultat"])
    assert abs(c.real - math.sinh(1)) < 1e-6


def test_imsqrt():
    from app.engine._v18 import _parse_complex
    r = FORMULAS["imsqrt"]({"nombre": "3+4i"})
    c = _parse_complex(r["resultat"])
    assert abs(c - (2 + 1j)) < 1e-9


def test_imsqrt_negative():
    from app.engine._v18 import _parse_complex
    r = FORMULAS["imsqrt"]({"nombre": "-1"})
    c = _parse_complex(r["resultat"])
    assert abs(c - 1j) < 1e-9


def test_imsub():
    from app.engine._v18 import _parse_complex
    r = FORMULAS["imsub"]({"nombre1": "5+3i", "nombre2": "2+i"})
    c = _parse_complex(r["resultat"])
    assert abs(c - (3 + 2j)) < 1e-9


def test_imsum():
    from app.engine._v18 import _parse_complex
    r = FORMULAS["imsum"]({"nombres": ["1+2i", "3+4i", "5+6i"]})
    c = _parse_complex(r["resultat"])
    assert abs(c - (9 + 12j)) < 1e-9


def test_imsum_single():
    from app.engine._v18 import _parse_complex
    r = FORMULAS["imsum"]({"nombres": ["3+4i"]})
    c = _parse_complex(r["resultat"])
    assert abs(c - (3 + 4j)) < 1e-9


# ─────────────────────────────────────────────────────────────────────────────
# Smoke test registre
# ─────────────────────────────────────────────────────────────────────────────
def test_registre_complet_v18():
    from app.engine.logic import FORMULA_META
    assert len(FORMULAS) == 493
    assert len(FORMULA_META) == 493
    assert set(FORMULAS.keys()) == set(FORMULA_META.keys())
