"""Tests v15 — Compatibilité & Nouveautés IA/Regex (Groupe 10, 20 formules)."""

import math

import pytest

from app.engine.logic import FORMULAS


# ─────────────────────────────────────────────────────────────────────────────
# RANK
# ─────────────────────────────────────────────────────────────────────────────
def test_rank_desc():
    r = FORMULAS["rank"]({"nombre": 3, "valeurs": [1, 2, 3, 4, 5]})
    assert r["rang"] == 3  # 3rd largest


def test_rank_asc():
    r = FORMULAS["rank"]({"nombre": 3, "valeurs": [1, 2, 3, 4, 5], "ordre": 1})
    assert r["rang"] == 3  # 3rd smallest


def test_rank_top():
    r = FORMULAS["rank"]({"nombre": 5, "valeurs": [1, 2, 3, 4, 5]})
    assert r["rang"] == 1


# ─────────────────────────────────────────────────────────────────────────────
# STDEV / STDEVP
# ─────────────────────────────────────────────────────────────────────────────
def test_stdev():
    r = FORMULAS["stdev"]({"valeurs": [2, 4, 4, 4, 5, 5, 7, 9]})
    assert abs(r["resultat"] - 2.1381) < 0.001


def test_stdevp():
    r = FORMULAS["stdevp"]({"valeurs": [2, 4, 4, 4, 5, 5, 7, 9]})
    assert abs(r["resultat"] - 2.0) < 0.001


# ─────────────────────────────────────────────────────────────────────────────
# TDIST / TINV / TTEST (aliases)
# ─────────────────────────────────────────────────────────────────────────────
def test_tdist():
    r = FORMULAS["tdist"]({"x": 0, "df": 10})
    assert abs(r["resultat"] - 0.5) < 1e-6


def test_tinv():
    r = FORMULAS["tinv"]({"probabilite": 0.975, "df": 30})
    assert abs(r["resultat"] - 2.042) < 0.01


def test_ttest():
    r = FORMULAS["ttest"]({"x": [1, 2, 3, 4, 5], "y": [1, 2, 3, 4, 5]})
    assert r["p_value"] == 1.0 or r["t_stat"] == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# VAR / VARP
# ─────────────────────────────────────────────────────────────────────────────
def test_var_val():
    r = FORMULAS["var_val"]({"valeurs": [1, 2, 3, 4, 5]})
    assert abs(r["resultat"] - 2.5) < 1e-9


def test_varp():
    r = FORMULAS["varp"]({"valeurs": [1, 2, 3, 4, 5]})
    assert abs(r["resultat"] - 2.0) < 1e-9


# ─────────────────────────────────────────────────────────────────────────────
# WEIBULL / ZTEST (aliases)
# ─────────────────────────────────────────────────────────────────────────────
def test_weibull():
    r = FORMULAS["weibull"]({"x": 1, "alpha": 1, "beta": 1})
    assert abs(r["resultat"] - (1 - math.exp(-1))) < 1e-6


def test_ztest():
    r = FORMULAS["ztest"]({"valeurs": [1, 2, 3, 4, 5], "mu": 3})
    assert abs(r["p_value"] - 0.5) < 0.01


# ─────────────────────────────────────────────────────────────────────────────
# REGEXEXTRACT
# ─────────────────────────────────────────────────────────────────────────────
def test_regexextract():
    r = FORMULAS["regexextract"]({"texte": "abc123def", "motif": r"\d+"})
    assert r["resultat"] == "123"


def test_regexextract_group():
    r = FORMULAS["regexextract"]({"texte": "prix: 42.50 EUR", "motif": r"(\d+\.\d+)"})
    assert r["resultat"] == "42.50"


def test_regexextract_not_found():
    with pytest.raises(ValueError):
        FORMULAS["regexextract"]({"texte": "abc", "motif": r"\d+"})


# ─────────────────────────────────────────────────────────────────────────────
# REGEXMATCH
# ─────────────────────────────────────────────────────────────────────────────
def test_regexmatch_true():
    assert FORMULAS["regexmatch"]({"texte": "abc123", "motif": r"\d+"})["resultat"] is True


def test_regexmatch_false():
    assert FORMULAS["regexmatch"]({"texte": "abcdef", "motif": r"\d+"})["resultat"] is False


# ─────────────────────────────────────────────────────────────────────────────
# REGEXREPLACE
# ─────────────────────────────────────────────────────────────────────────────
def test_regexreplace():
    r = FORMULAS["regexreplace"]({"texte": "abc123def456", "motif": r"\d+", "remplacement": "#"})
    assert r["resultat"] == "abc#def#"


def test_regexreplace_groups():
    r = FORMULAS["regexreplace"]({"texte": "2024-01-15", "motif": r"(\d{4})-(\d{2})-(\d{2})", "remplacement": r"\3/\2/\1"})
    assert r["resultat"] == "15/01/2024"


# ─────────────────────────────────────────────────────────────────────────────
# PERCENTOF
# ─────────────────────────────────────────────────────────────────────────────
def test_percentof():
    r = FORMULAS["percentof"]({"valeur": 25, "total": 100})
    assert r["resultat"] == 0.25


def test_percentof_zero():
    with pytest.raises(ValueError):
        FORMULAS["percentof"]({"valeur": 10, "total": 0})


# ─────────────────────────────────────────────────────────────────────────────
# TEXTBEFORE / TEXTAFTER
# ─────────────────────────────────────────────────────────────────────────────
def test_textbefore():
    r = FORMULAS["textbefore"]({"texte": "Hello-World-Test", "delimiteur": "-"})
    assert r["resultat"] == "Hello"


def test_textbefore_instance():
    r = FORMULAS["textbefore"]({"texte": "A-B-C-D", "delimiteur": "-", "instance": 2})
    assert r["resultat"] == "A-B"


def test_textafter():
    r = FORMULAS["textafter"]({"texte": "Hello-World-Test", "delimiteur": "-"})
    assert r["resultat"] == "World-Test"


def test_textafter_instance():
    r = FORMULAS["textafter"]({"texte": "A-B-C-D", "delimiteur": "-", "instance": 2})
    assert r["resultat"] == "C-D"


def test_textbefore_not_found():
    with pytest.raises(ValueError):
        FORMULAS["textbefore"]({"texte": "Hello", "delimiteur": "-"})


# ─────────────────────────────────────────────────────────────────────────────
# TEXTSPLIT
# ─────────────────────────────────────────────────────────────────────────────
def test_textsplit_cols():
    r = FORMULAS["textsplit"]({"texte": "A,B,C", "delimiteur_col": ","})
    assert r["resultat"] == [["A", "B", "C"]]


def test_textsplit_rows():
    r = FORMULAS["textsplit"]({"texte": "A;B;C", "delimiteur_ligne": ";"})
    assert r["resultat"] == [["A"], ["B"], ["C"]]


def test_textsplit_both():
    r = FORMULAS["textsplit"]({"texte": "A,B;C,D", "delimiteur_col": ",", "delimiteur_ligne": ";"})
    assert r["resultat"] == [["A", "B"], ["C", "D"]]


# ─────────────────────────────────────────────────────────────────────────────
# Smoke test registre
# ─────────────────────────────────────────────────────────────────────────────
def test_registre_complet_v15():
    from app.engine.logic import FORMULA_META
    assert len(FORMULAS) == 489
    assert len(FORMULA_META) == 489
    assert set(FORMULAS.keys()) == set(FORMULA_META.keys())
