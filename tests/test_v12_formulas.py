"""Tests v12 — Texte Avancé & Recherche Moderne / O365 (Groupe 7, 27 formules)."""

import pytest

from app.engine.logic import FORMULAS


# ─────────────────────────────────────────────────────────────────────────────
# MIDB
# ─────────────────────────────────────────────────────────────────────────────
def test_midb_ascii():
    r = FORMULAS["midb"]({"texte": "Hello World", "position": 7, "nb_octets": 5})
    assert r["resultat"] == "World"


def test_midb_utf8():
    r = FORMULAS["midb"]({"texte": "Héllo", "position": 1, "nb_octets": 3})
    assert r["resultat"] == "Hé"


# ─────────────────────────────────────────────────────────────────────────────
# PHONETIC
# ─────────────────────────────────────────────────────────────────────────────
def test_phonetic():
    r = FORMULAS["phonetic"]({"texte": "Tokyo"})
    assert r["resultat"] == "Tokyo"


# ─────────────────────────────────────────────────────────────────────────────
# REPLACEB
# ─────────────────────────────────────────────────────────────────────────────
def test_replaceb_ascii():
    r = FORMULAS["replaceb"]({"texte": "Hello", "position": 1, "nb_octets": 2, "nouveau_texte": "YY"})
    assert r["resultat"] == "YYllo"


def test_replaceb_utf8():
    r = FORMULAS["replaceb"]({"texte": "Héllo", "position": 1, "nb_octets": 3, "nouveau_texte": "Ha"})
    assert r["resultat"] == "Hallo"


# ─────────────────────────────────────────────────────────────────────────────
# RIGHTB
# ─────────────────────────────────────────────────────────────────────────────
def test_rightb_ascii():
    r = FORMULAS["rightb"]({"texte": "Hello", "nb_octets": 3})
    assert r["resultat"] == "llo"


def test_rightb_default():
    r = FORMULAS["rightb"]({"texte": "Hello"})
    assert r["resultat"] == "o"


# ─────────────────────────────────────────────────────────────────────────────
# SEARCHB
# ─────────────────────────────────────────────────────────────────────────────
def test_searchb_case_insensitive():
    r = FORMULAS["searchb"]({"cherche": "LO", "texte": "Hello World"})
    assert r["position"] == 4


def test_searchb_not_found():
    with pytest.raises(ValueError):
        FORMULAS["searchb"]({"cherche": "xyz", "texte": "Hello"})


# ─────────────────────────────────────────────────────────────────────────────
# T
# ─────────────────────────────────────────────────────────────────────────────
def test_t_val_text():
    r = FORMULAS["t_val"]({"valeur": "Hello"})
    assert r["resultat"] == "Hello"


def test_t_val_number():
    r = FORMULAS["t_val"]({"valeur": 42})
    assert r["resultat"] == ""


def test_t_val_bool():
    r = FORMULAS["t_val"]({"valeur": True})
    assert r["resultat"] == ""


# ─────────────────────────────────────────────────────────────────────────────
# UNICHAR / UNICODE
# ─────────────────────────────────────────────────────────────────────────────
def test_unichar():
    assert FORMULAS["unichar"]({"nombre": 65})["resultat"] == "A"


def test_unichar_emoji():
    assert FORMULAS["unichar"]({"nombre": 128512})["resultat"] == "\U0001F600"


def test_unichar_invalid():
    with pytest.raises(ValueError):
        FORMULAS["unichar"]({"nombre": 0})


def test_unicode_val():
    assert FORMULAS["unicode_val"]({"texte": "A"})["resultat"] == 65


def test_unicode_roundtrip():
    code = FORMULAS["unicode_val"]({"texte": "\u00e9"})["resultat"]
    ch = FORMULAS["unichar"]({"nombre": code})["resultat"]
    assert ch == "\u00e9"


# ─────────────────────────────────────────────────────────────────────────────
# VALUETOTEXT / ARRAYTOTEXT
# ─────────────────────────────────────────────────────────────────────────────
def test_valuetotext_concis():
    r = FORMULAS["valuetotext"]({"valeur": 123.45})
    assert r["resultat"] == "123.45"


def test_valuetotext_strict():
    r = FORMULAS["valuetotext"]({"valeur": "hello", "format": 1})
    assert r["resultat"] == '"hello"'


def test_arraytotext_concis():
    r = FORMULAS["arraytotext"]({"tableau": [1, 2, 3]})
    assert r["resultat"] == "1, 2, 3"


def test_arraytotext_strict():
    r = FORMULAS["arraytotext"]({"tableau": [1, 2, 3], "format": 1})
    assert r["resultat"] == "[1, 2, 3]"


def test_arraytotext_2d():
    r = FORMULAS["arraytotext"]({"tableau": [[1, 2], [3, 4]]})
    assert r["resultat"] == "1, 2, 3, 4"


# ─────────────────────────────────────────────────────────────────────────────
# CALL / REGISTER.ID (stubs)
# ─────────────────────────────────────────────────────────────────────────────
def test_call_val():
    r = FORMULAS["call_val"]({"nom_fonction": "test_fn", "arguments": [1, 2]})
    assert "CALL" in r["resultat"]
    assert r["arguments"] == [1, 2]


def test_register_id():
    r = FORMULAS["register_id"]({"module": "user32", "procedure": "GetWindow"})
    assert "user32" in r["resultat"]


# ─────────────────────────────────────────────────────────────────────────────
# CHOOSECOLS / CHOOSEROWS
# ─────────────────────────────────────────────────────────────────────────────
def test_choosecols():
    r = FORMULAS["choosecols"]({"tableau": [[1, 2, 3], [4, 5, 6]], "colonnes": [1, 3]})
    assert r["resultat"] == [[1, 3], [4, 6]]


def test_choosecols_negative():
    r = FORMULAS["choosecols"]({"tableau": [[1, 2, 3], [4, 5, 6]], "colonnes": [-1]})
    assert r["resultat"] == [[3], [6]]


def test_chooserows():
    r = FORMULAS["chooserows"]({"tableau": [[1, 2], [3, 4], [5, 6]], "lignes": [1, 3]})
    assert r["resultat"] == [[1, 2], [5, 6]]


def test_chooserows_negative():
    r = FORMULAS["chooserows"]({"tableau": [[1, 2], [3, 4], [5, 6]], "lignes": [-1]})
    assert r["resultat"] == [[5, 6]]


# ─────────────────────────────────────────────────────────────────────────────
# DROP / TAKE
# ─────────────────────────────────────────────────────────────────────────────
def test_drop_rows():
    r = FORMULAS["drop_val"]({"tableau": [[1, 2], [3, 4], [5, 6]], "lignes": 1})
    assert r["resultat"] == [[3, 4], [5, 6]]


def test_drop_rows_negative():
    r = FORMULAS["drop_val"]({"tableau": [[1, 2], [3, 4], [5, 6]], "lignes": -1})
    assert r["resultat"] == [[1, 2], [3, 4]]


def test_drop_cols():
    r = FORMULAS["drop_val"]({"tableau": [[1, 2, 3], [4, 5, 6]], "colonnes": 1})
    assert r["resultat"] == [[2, 3], [5, 6]]


def test_take_rows():
    r = FORMULAS["take_val"]({"tableau": [[1, 2], [3, 4], [5, 6]], "lignes": 2})
    assert r["resultat"] == [[1, 2], [3, 4]]


def test_take_rows_negative():
    r = FORMULAS["take_val"]({"tableau": [[1, 2], [3, 4], [5, 6]], "lignes": -1})
    assert r["resultat"] == [[5, 6]]


def test_take_cols():
    r = FORMULAS["take_val"]({"tableau": [[1, 2, 3], [4, 5, 6]], "colonnes": 2})
    assert r["resultat"] == [[1, 2], [4, 5]]


# ─────────────────────────────────────────────────────────────────────────────
# EXPAND
# ─────────────────────────────────────────────────────────────────────────────
def test_expand():
    r = FORMULAS["expand"]({"tableau": [[1, 2], [3, 4]], "lignes": 3, "colonnes": 3, "pad": 0})
    assert r["resultat"] == [[1, 2, 0], [3, 4, 0], [0, 0, 0]]


def test_expand_default_pad():
    r = FORMULAS["expand"]({"tableau": [[1]], "lignes": 2, "colonnes": 2})
    assert r["resultat"] == [[1, ""], ["", ""]]


# ─────────────────────────────────────────────────────────────────────────────
# HSTACK
# ─────────────────────────────────────────────────────────────────────────────
def test_hstack():
    r = FORMULAS["hstack"]({"tableaux": [[[1], [2]], [[3], [4]]]})
    assert r["resultat"] == [[1, 3], [2, 4]]


def test_hstack_unequal():
    r = FORMULAS["hstack"]({"tableaux": [[[1], [2], [3]], [[4], [5]]]})
    assert len(r["resultat"]) == 3
    assert r["resultat"][0] == [1, 4]


# ─────────────────────────────────────────────────────────────────────────────
# TOCOL / TOROW
# ─────────────────────────────────────────────────────────────────────────────
def test_tocol():
    r = FORMULAS["tocol"]({"tableau": [[1, 2], [3, 4]]})
    assert r["resultat"] == [[1], [2], [3], [4]]


def test_tocol_by_col():
    r = FORMULAS["tocol"]({"tableau": [[1, 2], [3, 4]], "scan_par_colonne": 1})
    assert r["resultat"] == [[1], [3], [2], [4]]


def test_torow():
    r = FORMULAS["torow"]({"tableau": [[1, 2], [3, 4]]})
    assert r["resultat"] == [[1, 2, 3, 4]]


def test_torow_by_col():
    r = FORMULAS["torow"]({"tableau": [[1, 2], [3, 4]], "scan_par_colonne": 1})
    assert r["resultat"] == [[1, 3, 2, 4]]


# ─────────────────────────────────────────────────────────────────────────────
# WRAPCOLS / WRAPROWS
# ─────────────────────────────────────────────────────────────────────────────
def test_wrapcols():
    r = FORMULAS["wrapcols"]({"vecteur": [1, 2, 3, 4, 5, 6], "taille": 3})
    assert r["resultat"] == [[1, 4], [2, 5], [3, 6]]


def test_wrapcols_pad():
    r = FORMULAS["wrapcols"]({"vecteur": [1, 2, 3, 4, 5], "taille": 3, "pad": 0})
    assert r["resultat"] == [[1, 4], [2, 5], [3, 0]]


def test_wraprows():
    r = FORMULAS["wraprows"]({"vecteur": [1, 2, 3, 4, 5, 6], "taille": 3})
    assert r["resultat"] == [[1, 2, 3], [4, 5, 6]]


def test_wraprows_pad():
    r = FORMULAS["wraprows"]({"vecteur": [1, 2, 3, 4, 5], "taille": 3, "pad": 0})
    assert r["resultat"] == [[1, 2, 3], [4, 5, 0]]


# ─────────────────────────────────────────────────────────────────────────────
# ISOMITTED
# ─────────────────────────────────────────────────────────────────────────────
def test_isomitted_true():
    assert FORMULAS["isomitted"]({"valeur": None})["resultat"] is True


def test_isomitted_false():
    assert FORMULAS["isomitted"]({"valeur": 42})["resultat"] is False


def test_isomitted_missing():
    assert FORMULAS["isomitted"]({})["resultat"] is True


# ─────────────────────────────────────────────────────────────────────────────
# LAMBDA
# ─────────────────────────────────────────────────────────────────────────────
def test_lambda_basic():
    r = FORMULAS["lambda_val"]({"parametres": {"x": 5, "y": 3}, "expression": "x + y"})
    assert r["resultat"] == 8


def test_lambda_math():
    r = FORMULAS["lambda_val"]({"parametres": {"r": 5}, "expression": "math.pi * r ** 2"})
    assert abs(r["resultat"] - 78.5398) < 0.01


# ─────────────────────────────────────────────────────────────────────────────
# MAP
# ─────────────────────────────────────────────────────────────────────────────
def test_map_1d():
    r = FORMULAS["map_val"]({"tableau": [1, 2, 3, 4], "expression": "x * 2"})
    assert r["resultat"] == [2, 4, 6, 8]


def test_map_2d():
    r = FORMULAS["map_val"]({"tableau": [[1, 2], [3, 4]], "expression": "x ** 2"})
    assert r["resultat"] == [[1, 4], [9, 16]]


# ─────────────────────────────────────────────────────────────────────────────
# REDUCE
# ─────────────────────────────────────────────────────────────────────────────
def test_reduce_sum():
    r = FORMULAS["reduce_val"]({"tableau": [1, 2, 3, 4], "initial": 0, "expression": "acc + x"})
    assert r["resultat"] == 10


def test_reduce_product():
    r = FORMULAS["reduce_val"]({"tableau": [1, 2, 3, 4], "initial": 1, "expression": "acc * x"})
    assert r["resultat"] == 24


def test_reduce_max():
    r = FORMULAS["reduce_val"]({"tableau": [3, 1, 4, 1, 5], "initial": 0, "expression": "max(acc, x)"})
    assert r["resultat"] == 5


# ─────────────────────────────────────────────────────────────────────────────
# SCAN
# ─────────────────────────────────────────────────────────────────────────────
def test_scan_cumsum():
    r = FORMULAS["scan_val"]({"tableau": [1, 2, 3, 4], "initial": 0, "expression": "acc + x"})
    assert r["resultat"] == [1, 3, 6, 10]


def test_scan_cumproduct():
    r = FORMULAS["scan_val"]({"tableau": [1, 2, 3, 4], "initial": 1, "expression": "acc * x"})
    assert r["resultat"] == [1, 2, 6, 24]


# ─────────────────────────────────────────────────────────────────────────────
# Smoke test registre
# ─────────────────────────────────────────────────────────────────────────────
def test_registre_complet_v12():
    from app.engine.logic import FORMULA_META
    assert len(FORMULAS) == 464
    assert len(FORMULA_META) == 464
    assert set(FORMULAS.keys()) == set(FORMULA_META.keys())
