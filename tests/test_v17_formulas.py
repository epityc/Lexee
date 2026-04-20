"""Tests v17 — Ingénierie/Maths & Logique moderne (Groupe 12, 16 formules)."""

import math

import pytest

from app.engine.logic import FORMULAS


# ─────────────────────────────────────────────────────────────────────────────
# BITRSHIFT / BITLSHIFT / BITOR / BITAND
# ─────────────────────────────────────────────────────────────────────────────
def test_bitrshift():
    assert FORMULAS["bitrshift"]({"nombre": 16, "decalage": 2})["resultat"] == 4


def test_bitlshift():
    assert FORMULAS["bitlshift"]({"nombre": 4, "decalage": 2})["resultat"] == 16


def test_bitor():
    # 5=101, 3=011 → 111=7
    assert FORMULAS["bitor"]({"nombre1": 5, "nombre2": 3})["resultat"] == 7


def test_bitand():
    # 5=101, 3=011 → 001=1
    assert FORMULAS["bitand"]({"nombre1": 5, "nombre2": 3})["resultat"] == 1


def test_bit_ops_identity():
    # a & a == a, a | a == a, a ^ a == 0
    assert FORMULAS["bitand"]({"nombre1": 42, "nombre2": 42})["resultat"] == 42
    assert FORMULAS["bitor"]({"nombre1": 42, "nombre2": 42})["resultat"] == 42


def test_bitrshift_negative():
    with pytest.raises(ValueError):
        FORMULAS["bitrshift"]({"nombre": -1, "decalage": 1})


# ─────────────────────────────────────────────────────────────────────────────
# ACOT / ACOTH
# ─────────────────────────────────────────────────────────────────────────────
def test_acot():
    r = FORMULAS["acot"]({"nombre": 1})
    assert abs(r["resultat"] - math.pi / 4) < 1e-9


def test_acot_zero():
    r = FORMULAS["acot"]({"nombre": 0})
    assert abs(r["resultat"] - math.pi / 2) < 1e-9


def test_acoth():
    r = FORMULAS["acoth"]({"nombre": 2})
    expected = 0.5 * math.log(3)  # atanh(1/2) = 0.5*ln(3)
    assert abs(r["resultat"] - expected) < 1e-9


def test_acoth_invalid():
    with pytest.raises(ValueError):
        FORMULAS["acoth"]({"nombre": 0.5})


# ─────────────────────────────────────────────────────────────────────────────
# BASE / DECIMAL
# ─────────────────────────────────────────────────────────────────────────────
def test_base_hex():
    assert FORMULAS["base_val"]({"nombre": 255, "base": 16})["resultat"] == "FF"


def test_base_binary():
    assert FORMULAS["base_val"]({"nombre": 10, "base": 2})["resultat"] == "1010"


def test_base_min_length():
    assert FORMULAS["base_val"]({"nombre": 10, "base": 2, "longueur_min": 8})["resultat"] == "00001010"


def test_decimal_hex():
    assert FORMULAS["decimal_val"]({"texte": "FF", "base": 16})["resultat"] == 255


def test_decimal_binary():
    assert FORMULAS["decimal_val"]({"texte": "1010", "base": 2})["resultat"] == 10


def test_base_decimal_roundtrip():
    for n in [0, 1, 42, 255, 1000]:
        b = FORMULAS["base_val"]({"nombre": n, "base": 16})["resultat"]
        back = FORMULAS["decimal_val"]({"texte": b, "base": 16})["resultat"]
        assert back == n


# ─────────────────────────────────────────────────────────────────────────────
# COMBINA
# ─────────────────────────────────────────────────────────────────────────────
def test_combina():
    # C(5+3-1, 3) = C(7,3) = 35
    assert FORMULAS["combina"]({"nombre": 5, "choisi": 3})["resultat"] == 35


def test_combina_zero():
    assert FORMULAS["combina"]({"nombre": 0, "choisi": 0})["resultat"] == 1


# ─────────────────────────────────────────────────────────────────────────────
# TEXTJOIN
# ─────────────────────────────────────────────────────────────────────────────
def test_textjoin():
    r = FORMULAS["textjoin"]({"delimiteur": ", ", "textes": ["A", "B", "C"]})
    assert r["resultat"] == "A, B, C"


def test_textjoin_ignore_empty():
    r = FORMULAS["textjoin"]({"delimiteur": "-", "textes": ["A", "", "C"], "ignorer_vides": True})
    assert r["resultat"] == "A-C"


def test_textjoin_keep_empty():
    r = FORMULAS["textjoin"]({"delimiteur": "-", "textes": ["A", "", "C"], "ignorer_vides": False})
    assert r["resultat"] == "A--C"


# ─────────────────────────────────────────────────────────────────────────────
# IFS
# ─────────────────────────────────────────────────────────────────────────────
def test_ifs_first_true():
    r = FORMULAS["ifs"]({"conditions": [
        {"test": False, "valeur": "A"},
        {"test": True, "valeur": "B"},
        {"test": True, "valeur": "C"},
    ]})
    assert r["resultat"] == "B"


def test_ifs_none_true():
    with pytest.raises(ValueError):
        FORMULAS["ifs"]({"conditions": [{"test": False, "valeur": "X"}]})


# ─────────────────────────────────────────────────────────────────────────────
# SWITCH
# ─────────────────────────────────────────────────────────────────────────────
def test_switch_match():
    r = FORMULAS["switch"]({"expression": "B", "cas": [
        {"valeur": "A", "resultat": 1},
        {"valeur": "B", "resultat": 2},
    ]})
    assert r["resultat"] == 2


def test_switch_default():
    r = FORMULAS["switch"]({"expression": "Z", "cas": [
        {"valeur": "A", "resultat": 1},
    ], "defaut": 99})
    assert r["resultat"] == 99


def test_switch_no_match():
    with pytest.raises(ValueError):
        FORMULAS["switch"]({"expression": "Z", "cas": [{"valeur": "A", "resultat": 1}]})


# ─────────────────────────────────────────────────────────────────────────────
# MAXIFS / MINIFS / SUMIFS / COUNTIFS
# ─────────────────────────────────────────────────────────────────────────────
def test_sumifs():
    r = FORMULAS["sumifs"]({
        "valeurs": [10, 20, 30, 40],
        "criteres": [{"plage": ["A", "B", "A", "B"], "critere": "A"}],
    })
    assert r["resultat"] == 40  # 10 + 30


def test_sumifs_numeric():
    r = FORMULAS["sumifs"]({
        "valeurs": [100, 200, 300, 400],
        "criteres": [{"plage": [1, 2, 3, 4], "critere": ">2"}],
    })
    assert r["resultat"] == 700  # 300 + 400


def test_maxifs():
    r = FORMULAS["maxifs"]({
        "valeurs": [10, 20, 30, 40],
        "criteres": [{"plage": ["A", "B", "A", "B"], "critere": "A"}],
    })
    assert r["resultat"] == 30


def test_minifs():
    r = FORMULAS["minifs"]({
        "valeurs": [10, 20, 30, 40],
        "criteres": [{"plage": ["A", "B", "A", "B"], "critere": "A"}],
    })
    assert r["resultat"] == 10


def test_countifs():
    r = FORMULAS["countifs"]({
        "criteres": [{"plage": ["A", "B", "A", "B"], "critere": "A"}],
    })
    assert r["resultat"] == 2


def test_countifs_multi():
    r = FORMULAS["countifs"]({
        "criteres": [
            {"plage": ["A", "B", "A", "B"], "critere": "A"},
            {"plage": [1, 2, 3, 4], "critere": ">1"},
        ],
    })
    assert r["resultat"] == 1  # only index 2 (A, 3)


def test_sumifs_no_match():
    r = FORMULAS["sumifs"]({
        "valeurs": [10, 20],
        "criteres": [{"plage": ["A", "A"], "critere": "Z"}],
    })
    assert r["resultat"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# Smoke test registre
# ─────────────────────────────────────────────────────────────────────────────
def test_registre_complet_v17():
    from app.engine.logic import FORMULA_META
    assert len(FORMULAS) == 494
    assert len(FORMULA_META) == 494
    assert set(FORMULAS.keys()) == set(FORMULA_META.keys())
