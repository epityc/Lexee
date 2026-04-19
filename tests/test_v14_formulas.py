"""Tests v14 — Compatibilité anciennes fonctions Excel (Groupe 9, 24 formules)."""

import math

import pytest

from app.engine.logic import FORMULAS


# ─────────────────────────────────────────────────────────────────────────────
# SUMSQ
# ─────────────────────────────────────────────────────────────────────────────
def test_sumsq():
    assert FORMULAS["sumsq"]({"valeurs": [3, 4]})["resultat"] == 25


def test_sumsq_single():
    assert FORMULAS["sumsq"]({"valeurs": [5]})["resultat"] == 25


# ─────────────────────────────────────────────────────────────────────────────
# SUMX2MY2 / SUMX2PY2 / SUMXMY2
# ─────────────────────────────────────────────────────────────────────────────
def test_sumx2my2():
    # (1²-4²) + (2²-5²) + (3²-6²) = -15 + -21 + -27 = -63
    r = FORMULAS["sumx2my2"]({"x": [1, 2, 3], "y": [4, 5, 6]})
    assert r["resultat"] == -63


def test_sumx2py2():
    # (1²+4²) + (2²+5²) + (3²+6²) = 17 + 29 + 45 = 91
    r = FORMULAS["sumx2py2"]({"x": [1, 2, 3], "y": [4, 5, 6]})
    assert r["resultat"] == 91


def test_sumxmy2():
    # (1-4)² + (2-5)² + (3-6)² = 9 + 9 + 9 = 27
    r = FORMULAS["sumxmy2"]({"x": [1, 2, 3], "y": [4, 5, 6]})
    assert r["resultat"] == 27


def test_sumxmy2_equal():
    r = FORMULAS["sumxmy2"]({"x": [1, 2, 3], "y": [1, 2, 3]})
    assert r["resultat"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# BETADIST / BETAINV (aliases)
# ─────────────────────────────────────────────────────────────────────────────
def test_betadist():
    r = FORMULAS["betadist"]({"x": 0.5, "alpha": 2, "beta": 5})
    modern = FORMULAS["beta_dist"]({"x": 0.5, "alpha": 2, "beta": 5})
    assert abs(r["resultat"] - modern["resultat"]) < 1e-9


def test_betainv():
    cdf = FORMULAS["betadist"]({"x": 0.3, "alpha": 2, "beta": 5})["resultat"]
    inv = FORMULAS["betainv"]({"probabilite": cdf, "alpha": 2, "beta": 5})
    assert abs(inv["resultat"] - 0.3) < 0.001


# ─────────────────────────────────────────────────────────────────────────────
# BINOMDIST (alias)
# ─────────────────────────────────────────────────────────────────────────────
def test_binomdist():
    r = FORMULAS["binomdist"]({"succes": 3, "essais": 10, "probabilite": 0.5, "cumulatif": False})
    assert abs(r["resultat"] - 0.1172) < 0.001


# ─────────────────────────────────────────────────────────────────────────────
# CHIDIST / CHIINV / CHITEST (aliases)
# ─────────────────────────────────────────────────────────────────────────────
def test_chidist():
    r = FORMULAS["chidist"]({"x": 7.815, "df": 3})
    assert abs(r["resultat"] - 0.05) < 0.01


def test_chiinv():
    r = FORMULAS["chiinv"]({"probabilite": 0.05, "df": 3})
    assert abs(r["resultat"] - 7.815) < 0.05


def test_chitest():
    r = FORMULAS["chitest"]({"observees": [10, 20, 30], "attendues": [15, 15, 30]})
    assert r["chi2"] > 0
    assert 0 <= r["p_value"] <= 1


# ─────────────────────────────────────────────────────────────────────────────
# COVAR
# ─────────────────────────────────────────────────────────────────────────────
def test_covar_perfect():
    r = FORMULAS["covar"]({"x": [1, 2, 3], "y": [2, 4, 6]})
    # population cov = 2/3 * 2 = 4/3 ≈ 1.333
    assert abs(r["covariance"] - 4/3) < 1e-6


def test_covar_zero():
    r = FORMULAS["covar"]({"x": [1, 2, 3], "y": [5, 5, 5]})
    assert abs(r["covariance"]) < 1e-9


# ─────────────────────────────────────────────────────────────────────────────
# CRITBINOM (alias BINOM.INV)
# ─────────────────────────────────────────────────────────────────────────────
def test_critbinom():
    r = FORMULAS["critbinom"]({"essais": 10, "probabilite": 0.5, "alpha": 0.5})
    assert r["resultat"] == 5


# ─────────────────────────────────────────────────────────────────────────────
# EXPONDIST (alias)
# ─────────────────────────────────────────────────────────────────────────────
def test_expondist():
    r = FORMULAS["expondist"]({"x": 1, "lambda": 1})
    assert abs(r["resultat"] - (1 - math.exp(-1))) < 1e-6


# ─────────────────────────────────────────────────────────────────────────────
# FDIST / FINV / FTEST (aliases)
# ─────────────────────────────────────────────────────────────────────────────
def test_fdist():
    r = FORMULAS["fdist"]({"x": 3, "d1": 5, "d2": 10})
    assert 0 < r["resultat"] < 1


def test_finv():
    r = FORMULAS["finv"]({"probabilite": 0.95, "d1": 5, "d2": 10})
    assert r["resultat"] > 0


def test_ftest():
    r = FORMULAS["ftest"]({"x": [1, 2, 3, 4, 5], "y": [2, 4, 6, 8, 10]})
    assert r["f_stat"] > 0


# ─────────────────────────────────────────────────────────────────────────────
# GAMMADIST / GAMMAINV (aliases)
# ─────────────────────────────────────────────────────────────────────────────
def test_gammadist():
    r = FORMULAS["gammadist"]({"x": 2, "alpha": 2, "beta": 1})
    assert 0.5 < r["resultat"] < 1


def test_gammainv_roundtrip():
    cdf = FORMULAS["gammadist"]({"x": 3, "alpha": 2, "beta": 1})["resultat"]
    inv = FORMULAS["gammainv"]({"probabilite": cdf, "alpha": 2, "beta": 1})
    assert abs(inv["resultat"] - 3) < 0.05


# ─────────────────────────────────────────────────────────────────────────────
# HYPGEOMDIST (alias)
# ─────────────────────────────────────────────────────────────────────────────
def test_hypgeomdist():
    r = FORMULAS["hypgeomdist"]({
        "succes_echantillon": 1, "taille_echantillon": 4,
        "succes_population": 8, "taille_population": 20, "cumulatif": False,
    })
    assert 0 < r["resultat"] < 1


# ─────────────────────────────────────────────────────────────────────────────
# LOGNORMDIST / LOGINV (aliases)
# ─────────────────────────────────────────────────────────────────────────────
def test_lognormdist():
    r = FORMULAS["lognormdist"]({"x": 1, "moyenne": 0, "ecart_type": 1})
    assert abs(r["resultat"] - 0.5) < 0.01


def test_loginv():
    cdf = FORMULAS["lognormdist"]({"x": 2, "moyenne": 0, "ecart_type": 1})["resultat"]
    inv = FORMULAS["loginv"]({"probabilite": cdf, "moyenne": 0, "ecart_type": 1})
    assert abs(inv["resultat"] - 2) < 0.01


# ─────────────────────────────────────────────────────────────────────────────
# NEGBINOMDIST (alias)
# ─────────────────────────────────────────────────────────────────────────────
def test_negbinomdist():
    r = FORMULAS["negbinomdist"]({"echecs": 2, "succes": 3, "probabilite": 0.5, "cumulatif": False})
    assert abs(r["resultat"] - 0.1875) < 0.001


# ─────────────────────────────────────────────────────────────────────────────
# NORMDIST / NORMINV / NORMSDIST / NORMSINV (aliases)
# ─────────────────────────────────────────────────────────────────────────────
def test_normdist():
    r = FORMULAS["normdist"]({"x": 0, "moyenne": 0, "ecart_type": 1})
    assert abs(r["resultat"] - 0.5) < 1e-6


def test_norminv():
    r = FORMULAS["norminv"]({"probabilite": 0.975, "moyenne": 0, "ecart_type": 1})
    assert abs(r["resultat"] - 1.96) < 0.01


def test_normsdist():
    r = FORMULAS["normsdist"]({"z": 1.96})
    assert abs(r["resultat"] - 0.975) < 0.001


def test_normsinv():
    r = FORMULAS["normsinv"]({"probabilite": 0.975})
    assert abs(r["resultat"] - 1.96) < 0.01


# ─────────────────────────────────────────────────────────────────────────────
# POISSON (alias)
# ─────────────────────────────────────────────────────────────────────────────
def test_poisson():
    r = FORMULAS["poisson"]({"x": 3, "moyenne": 2.5, "cumulatif": False})
    assert abs(r["resultat"] - 0.2138) < 0.001


# ─────────────────────────────────────────────────────────────────────────────
# Smoke test registre
# ─────────────────────────────────────────────────────────────────────────────
def test_registre_complet_v14():
    from app.engine.logic import FORMULA_META
    assert len(FORMULAS) == 464
    assert len(FORMULA_META) == 464
    assert set(FORMULAS.keys()) == set(FORMULA_META.keys())
