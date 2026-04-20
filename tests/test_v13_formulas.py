"""Tests v13 — Web, Cube, Information & Maths complémentaires (Groupe 8, 28 formules)."""

import math

import pytest

from app.engine.logic import FORMULAS


# ─────────────────────────────────────────────────────────────────────────────
# ENCODEURL
# ─────────────────────────────────────────────────────────────────────────────
def test_encodeurl_spaces():
    r = FORMULAS["encodeurl"]({"texte": "Hello World"})
    assert r["resultat"] == "Hello%20World"


def test_encodeurl_special():
    r = FORMULAS["encodeurl"]({"texte": "a=1&b=2"})
    assert r["resultat"] == "a%3D1%26b%3D2"


# ─────────────────────────────────────────────────────────────────────────────
# FILTERXML
# ─────────────────────────────────────────────────────────────────────────────
def test_filterxml_single():
    xml = "<root><item>Hello</item></root>"
    r = FORMULAS["filterxml"]({"xml": xml, "xpath": ".//item"})
    assert r["resultat"] == "Hello"


def test_filterxml_multiple():
    xml = "<root><item>A</item><item>B</item></root>"
    r = FORMULAS["filterxml"]({"xml": xml, "xpath": ".//item"})
    assert r["resultat"] == ["A", "B"]


def test_filterxml_not_found():
    with pytest.raises(ValueError):
        FORMULAS["filterxml"]({"xml": "<root/>", "xpath": ".//missing"})


# ─────────────────────────────────────────────────────────────────────────────
# WEBSERVICE (stub)
# ─────────────────────────────────────────────────────────────────────────────
def test_webservice():
    r = FORMULAS["webservice"]({"url": "https://example.com"})
    assert "WEBSERVICE" in r["resultat"]


# ─────────────────────────────────────────────────────────────────────────────
# CUBE (stubs)
# ─────────────────────────────────────────────────────────────────────────────
def test_cubekpimember():
    r = FORMULAS["cubekpimember"]({"connexion": "C", "expression": "Revenue"})
    assert "KPI" in r["resultat"]


def test_cubemember():
    r = FORMULAS["cubemember"]({"connexion": "C", "expression": "[Product]"})
    assert "MEMBER" in r["resultat"]


def test_cubememberproperty():
    r = FORMULAS["cubememberproperty"]({"connexion": "C", "expression": "[P]", "propriete": "Name"})
    assert "PROP" in r["resultat"]


def test_cuberankedmember():
    r = FORMULAS["cuberankedmember"]({"connexion": "C", "expression": "Set", "rang": 1})
    assert "RANKED" in r["resultat"]


def test_cubeset():
    r = FORMULAS["cubeset"]({"connexion": "C", "expression": "Members"})
    assert "SET" in r["resultat"]


def test_cubesetcount():
    r = FORMULAS["cubesetcount"]({"ensemble": "test"})
    assert r["resultat"] == 0


def test_cubevalue():
    r = FORMULAS["cubevalue"]({"connexion": "C", "expression": "[Measures]"})
    assert r["resultat"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# ERROR.TYPE
# ─────────────────────────────────────────────────────────────────────────────
def test_error_type_div0():
    assert FORMULAS["error_type"]({"valeur": "#DIV/0!"})["resultat"] == 2


def test_error_type_na():
    assert FORMULAS["error_type"]({"valeur": "#N/A"})["resultat"] == 7


def test_error_type_invalid():
    with pytest.raises(ValueError):
        FORMULAS["error_type"]({"valeur": "not_error"})


# ─────────────────────────────────────────────────────────────────────────────
# INFO
# ─────────────────────────────────────────────────────────────────────────────
def test_info_system():
    r = FORMULAS["info_val"]({"type_info": "system"})
    assert isinstance(r["resultat"], str)


def test_info_invalid():
    with pytest.raises(ValueError):
        FORMULAS["info_val"]({"type_info": "unknown"})


# ─────────────────────────────────────────────────────────────────────────────
# ISFORMULA / ISNONTEXT
# ─────────────────────────────────────────────────────────────────────────────
def test_isformula_true():
    assert FORMULAS["isformula"]({"valeur": "=A1+B1"})["resultat"] is True


def test_isformula_false():
    assert FORMULAS["isformula"]({"valeur": "Hello"})["resultat"] is False


def test_isnontext_number():
    assert FORMULAS["isnontext"]({"valeur": 42})["resultat"] is True


def test_isnontext_string():
    assert FORMULAS["isnontext"]({"valeur": "Hello"})["resultat"] is False


# ─────────────────────────────────────────────────────────────────────────────
# N
# ─────────────────────────────────────────────────────────────────────────────
def test_n_number():
    assert FORMULAS["n_val"]({"valeur": 42.5})["resultat"] == 42.5


def test_n_bool():
    assert FORMULAS["n_val"]({"valeur": True})["resultat"] == 1


def test_n_text():
    assert FORMULAS["n_val"]({"valeur": "hello"})["resultat"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# SHEET / SHEETS
# ─────────────────────────────────────────────────────────────────────────────
def test_sheet():
    assert FORMULAS["sheet"]({})["resultat"] == 1


def test_sheets():
    assert FORMULAS["sheets"]({"nombre": 3})["resultat"] == 3


# ─────────────────────────────────────────────────────────────────────────────
# AGGREGATE
# ─────────────────────────────────────────────────────────────────────────────
def test_aggregate_average():
    r = FORMULAS["aggregate"]({"num_fonction": 1, "valeurs": [1, 2, 3, 4, 5]})
    assert r["resultat"] == 3.0


def test_aggregate_sum():
    r = FORMULAS["aggregate"]({"num_fonction": 9, "valeurs": [1, 2, 3, 4, 5]})
    assert r["resultat"] == 15


def test_aggregate_max():
    r = FORMULAS["aggregate"]({"num_fonction": 4, "valeurs": [1, 2, 3, 4, 5]})
    assert r["resultat"] == 5


def test_aggregate_invalid():
    with pytest.raises(ValueError):
        FORMULAS["aggregate"]({"num_fonction": 99, "valeurs": [1, 2, 3]})


# ─────────────────────────────────────────────────────────────────────────────
# ARABIC / ROMAN roundtrip
# ─────────────────────────────────────────────────────────────────────────────
def test_arabic():
    assert FORMULAS["arabic"]({"texte": "MCMXCIV"})["resultat"] == 1994


def test_arabic_simple():
    assert FORMULAS["arabic"]({"texte": "XIV"})["resultat"] == 14


def test_roman():
    assert FORMULAS["roman"]({"nombre": 1994})["resultat"] == "MCMXCIV"


def test_roman_simple():
    assert FORMULAS["roman"]({"nombre": 14})["resultat"] == "XIV"


def test_arabic_roman_roundtrip():
    for n in [1, 42, 100, 999, 2024, 3999]:
        rom = FORMULAS["roman"]({"nombre": n})["resultat"]
        back = FORMULAS["arabic"]({"texte": rom})["resultat"]
        assert back == n


# ─────────────────────────────────────────────────────────────────────────────
# CEILING.PRECISE / FLOOR.PRECISE / ISO.CEILING
# ─────────────────────────────────────────────────────────────────────────────
def test_ceiling_precise():
    assert FORMULAS["ceiling_precise"]({"nombre": 4.3})["resultat"] == 5.0


def test_ceiling_precise_neg():
    assert FORMULAS["ceiling_precise"]({"nombre": -4.3})["resultat"] == -4.0


def test_floor_precise():
    assert FORMULAS["floor_precise"]({"nombre": 4.7})["resultat"] == 4.0


def test_floor_precise_neg():
    assert FORMULAS["floor_precise"]({"nombre": -4.7})["resultat"] == -5.0


def test_iso_ceiling():
    assert FORMULAS["iso_ceiling"]({"nombre": 4.3})["resultat"] == 5.0


def test_iso_ceiling_neg():
    assert FORMULAS["iso_ceiling"]({"nombre": -4.3})["resultat"] == -4.0


# ─────────────────────────────────────────────────────────────────────────────
# FACTDOUBLE
# ─────────────────────────────────────────────────────────────────────────────
def test_factdouble_7():
    # 7!! = 7*5*3*1 = 105
    assert FORMULAS["factdouble"]({"nombre": 7})["resultat"] == 105


def test_factdouble_6():
    # 6!! = 6*4*2 = 48
    assert FORMULAS["factdouble"]({"nombre": 6})["resultat"] == 48


def test_factdouble_0():
    assert FORMULAS["factdouble"]({"nombre": 0})["resultat"] == 1


# ─────────────────────────────────────────────────────────────────────────────
# MUNIT
# ─────────────────────────────────────────────────────────────────────────────
def test_munit_3():
    r = FORMULAS["munit"]({"dimension": 3})
    assert r["resultat"] == [[1, 0, 0], [0, 1, 0], [0, 0, 1]]


def test_munit_1():
    assert FORMULAS["munit"]({"dimension": 1})["resultat"] == [[1]]


# ─────────────────────────────────────────────────────────────────────────────
# MULTINOMIAL
# ─────────────────────────────────────────────────────────────────────────────
def test_multinomial():
    # (2+3+4)! / (2!*3!*4!) = 362880 / (2*6*24) = 1260
    assert FORMULAS["multinomial"]({"valeurs": [2, 3, 4]})["resultat"] == 1260


def test_multinomial_binomial():
    # C(5,2) = 5!/(2!*3!) = 10
    assert FORMULAS["multinomial"]({"valeurs": [2, 3]})["resultat"] == 10


# ─────────────────────────────────────────────────────────────────────────────
# SERIESSUM
# ─────────────────────────────────────────────────────────────────────────────
def test_seriessum():
    # 1*x^0 + 1*x^1 + 1*x^2 = 1 + 2 + 4 = 7
    r = FORMULAS["seriessum"]({"x": 2, "n": 0, "m": 1, "coefficients": [1, 1, 1]})
    assert r["resultat"] == 7.0


def test_seriessum_sin_approx():
    # sin(x) ≈ x - x^3/6 + x^5/120 with x=0.5
    x = 0.5
    r = FORMULAS["seriessum"]({"x": x, "n": 1, "m": 2, "coefficients": [1, -1/6, 1/120]})
    assert abs(r["resultat"] - math.sin(x)) < 1e-5


# ─────────────────────────────────────────────────────────────────────────────
# SQRTPI
# ─────────────────────────────────────────────────────────────────────────────
def test_sqrtpi_1():
    assert abs(FORMULAS["sqrtpi"]({"nombre": 1})["resultat"] - math.sqrt(math.pi)) < 1e-10


def test_sqrtpi_2():
    assert abs(FORMULAS["sqrtpi"]({"nombre": 2})["resultat"] - math.sqrt(2 * math.pi)) < 1e-10


def test_sqrtpi_negative():
    with pytest.raises(ValueError):
        FORMULAS["sqrtpi"]({"nombre": -1})


# ─────────────────────────────────────────────────────────────────────────────
# Smoke test registre
# ─────────────────────────────────────────────────────────────────────────────
def test_registre_complet_v13():
    from app.engine.logic import FORMULA_META
    assert len(FORMULAS) == 493
    assert len(FORMULA_META) == 493
    assert set(FORMULAS.keys()) == set(FORMULA_META.keys())
