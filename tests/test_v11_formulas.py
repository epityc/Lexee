"""Tests v11 — Statistiques, D-Functions & Texte/Octets (Groupe 6, 30 formules)."""

import math

import pytest

from app.engine.logic import FORMULAS

BASE = [
    {"region": "EU", "ca": 100, "nom": "Alice"},
    {"region": "EU", "ca": 200, "nom": "Bob"},
    {"region": "US", "ca": 150, "nom": "Carol"},
]


# ─────────────────────────────────────────────────────────────────────────────
# RSQ
# ─────────────────────────────────────────────────────────────────────────────
def test_rsq_perfect():
    r = FORMULAS["rsq"]({"x": [1, 2, 3, 4, 5], "y": [2, 4, 6, 8, 10]})
    assert abs(r["resultat"] - 1.0) < 1e-9


def test_rsq_zero():
    # constant y → stddev=0 → ValueError
    with pytest.raises(ValueError):
        FORMULAS["rsq"]({"x": [1, 2, 3], "y": [5, 5, 5]})


# ─────────────────────────────────────────────────────────────────────────────
# SKEW / SKEW.P
# ─────────────────────────────────────────────────────────────────────────────
def test_skew_positive():
    r = FORMULAS["skew"]({"valeurs": [1, 2, 3, 4, 10]})
    assert r["resultat"] > 0  # right-skewed


def test_skew_symmetric():
    r = FORMULAS["skew"]({"valeurs": [1, 2, 3, 4, 5]})
    assert abs(r["resultat"]) < 0.01


def test_skew_p():
    r = FORMULAS["skew_p"]({"valeurs": [1, 2, 3, 4, 10]})
    assert r["resultat"] > 0


# ─────────────────────────────────────────────────────────────────────────────
# STANDARDIZE
# ─────────────────────────────────────────────────────────────────────────────
def test_standardize():
    r = FORMULAS["standardize"]({"x": 75, "moyenne": 70, "ecart_type": 5})
    assert abs(r["resultat"] - 1.0) < 1e-9


def test_standardize_zero():
    r = FORMULAS["standardize"]({"x": 70, "moyenne": 70, "ecart_type": 5})
    assert r["resultat"] == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# T.DIST / T.INV
# ─────────────────────────────────────────────────────────────────────────────
def test_t_dist_cdf():
    r = FORMULAS["t_dist"]({"x": 0, "df": 10})
    assert abs(r["resultat"] - 0.5) < 1e-6


def test_t_dist_2t_symmetry():
    r = FORMULAS["t_dist_2t"]({"x": 1.96, "df": 100})
    assert abs(r["resultat"] - 0.052) < 0.002


def test_t_dist_rt():
    cdf = FORMULAS["t_dist"]({"x": 2, "df": 10})["resultat"]
    rt = FORMULAS["t_dist_rt"]({"x": 2, "df": 10})["resultat"]
    assert abs(cdf + rt - 1) < 1e-6


def test_t_inv_roundtrip():
    r = FORMULAS["t_inv"]({"probabilite": 0.975, "df": 30})
    assert abs(r["resultat"] - 2.042) < 0.01


def test_t_inv_2t():
    r = FORMULAS["t_inv_2t"]({"probabilite": 0.05, "df": 30})
    assert abs(r["resultat"] - 2.042) < 0.01


def test_t_test_equal_means():
    r = FORMULAS["t_test"]({
        "x": [1, 2, 3, 4, 5],
        "y": [1, 2, 3, 4, 5],
    })
    assert r["p_value"] == 1.0 or r["t_stat"] == 0.0


def test_t_test_paired():
    # differences [5,6,7,8,9], mean=7, sd≈1.58 → t≈9.9, p<<0.001
    r = FORMULAS["t_test"]({
        "x": [6, 8, 10, 12, 14],
        "y": [1, 2, 3, 4, 5],
        "queues": 2, "type": 1,
    })
    assert r["p_value"] < 0.001


# ─────────────────────────────────────────────────────────────────────────────
# WEIBULL.DIST
# ─────────────────────────────────────────────────────────────────────────────
def test_weibull_cdf():
    r = FORMULAS["weibull_dist"]({"x": 1, "alpha": 1, "beta": 1})
    assert abs(r["resultat"] - (1 - math.exp(-1))) < 1e-6


def test_weibull_pdf():
    r = FORMULAS["weibull_dist"]({"x": 1, "alpha": 2, "beta": 1, "cumulatif": False})
    # f(1; k=2, λ=1) = 2 * e^{-1} ≈ 0.7358
    assert abs(r["resultat"] - 2 * math.exp(-1)) < 1e-6


# ─────────────────────────────────────────────────────────────────────────────
# Z.TEST
# ─────────────────────────────────────────────────────────────────────────────
def test_z_test_at_mean():
    r = FORMULAS["z_test"]({"valeurs": [1, 2, 3, 4, 5], "mu": 3})
    assert abs(r["p_value"] - 0.5) < 0.01


def test_z_test_above_mean():
    r = FORMULAS["z_test"]({"valeurs": [1, 2, 3, 4, 5], "mu": 1})
    assert r["p_value"] < 0.05


# ─────────────────────────────────────────────────────────────────────────────
# D-FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────
def test_daverage():
    r = FORMULAS["daverage"]({"base": BASE, "champ": "ca", "criteres": {"region": "EU"}})
    assert abs(r["resultat"] - 150) < 1e-6


def test_dcount():
    r = FORMULAS["dcount"]({"base": BASE, "champ": "ca", "criteres": {"region": "EU"}})
    assert r["resultat"] == 2


def test_dcounta():
    r = FORMULAS["dcounta"]({"base": BASE, "champ": "nom", "criteres": {"region": "EU"}})
    assert r["resultat"] == 2


def test_dget_unique():
    r = FORMULAS["dget"]({"base": BASE, "champ": "ca", "criteres": {"nom": "Carol"}})
    assert r["resultat"] == 150


def test_dget_multiple_error():
    with pytest.raises(ValueError):
        FORMULAS["dget"]({"base": BASE, "champ": "ca", "criteres": {"region": "EU"}})


def test_dmax():
    r = FORMULAS["dmax"]({"base": BASE, "champ": "ca", "criteres": {"region": "EU"}})
    assert r["resultat"] == 200.0


def test_dmin():
    r = FORMULAS["dmin"]({"base": BASE, "champ": "ca", "criteres": {"region": "EU"}})
    assert r["resultat"] == 100.0


def test_dproduct():
    r = FORMULAS["dproduct"]({"base": BASE, "champ": "ca", "criteres": {"region": "EU"}})
    assert r["produit"] == 20000.0


def test_dstdev():
    r = FORMULAS["dstdev"]({"base": BASE, "champ": "ca", "criteres": {"region": "EU"}})
    assert abs(r["ecart_type"] - math.sqrt(5000)) < 1e-6


def test_dstdevp():
    r = FORMULAS["dstdevp"]({"base": BASE, "champ": "ca", "criteres": {"region": "EU"}})
    assert abs(r["ecart_type"] - 50) < 1e-6


def test_dsum():
    r = FORMULAS["dsum"]({"base": BASE, "champ": "ca", "criteres": {"region": "EU"}})
    assert r["somme"] == 300.0


def test_dvar():
    r = FORMULAS["dvar"]({"base": BASE, "champ": "ca", "criteres": {"region": "EU"}})
    assert abs(r["variance"] - 5000) < 1e-6


def test_dvarp():
    r = FORMULAS["dvarp"]({"base": BASE, "champ": "ca", "criteres": {"region": "EU"}})
    assert abs(r["variance"] - 2500) < 1e-6


# ─────────────────────────────────────────────────────────────────────────────
# ASC / DBCS
# ─────────────────────────────────────────────────────────────────────────────
def test_asc():
    r = FORMULAS["asc_val"]({"texte": "Ａｌｉｃｅ"})
    assert r["resultat"] == "Alice"


def test_dbcs():
    r = FORMULAS["dbcs"]({"texte": "Hi"})
    assert r["resultat"] == "Ｈｉ"


def test_asc_dbcs_roundtrip():
    original = "Hello"
    wide = FORMULAS["dbcs"]({"texte": original})["resultat"]
    back = FORMULAS["asc_val"]({"texte": wide})["resultat"]
    assert back == original


# ─────────────────────────────────────────────────────────────────────────────
# BAHTTEXT
# ─────────────────────────────────────────────────────────────────────────────
def test_bahttext_entier():
    r = FORMULAS["bahttext"]({"nombre": 100})
    assert "100" in r["resultat"]
    assert "บาท" in r["resultat"]


def test_bahttext_decimal():
    r = FORMULAS["bahttext"]({"nombre": 12.5})
    assert "สตางค์" in r["resultat"]


# ─────────────────────────────────────────────────────────────────────────────
# FINDB / LEFTB / LENB
# ─────────────────────────────────────────────────────────────────────────────
def test_lenb_ascii():
    r = FORMULAS["lenb"]({"texte": "Hello"})
    assert r["resultat"] == 5


def test_lenb_utf8():
    r = FORMULAS["lenb"]({"texte": "Héllo"})
    assert r["resultat"] == 6  # é = 2 octets UTF-8


def test_leftb_ascii():
    r = FORMULAS["leftb"]({"texte": "Hello", "nb_octets": 3})
    assert r["resultat"] == "Hel"


def test_findb():
    r = FORMULAS["findb"]({"cherche": "lo", "texte": "Hello World"})
    assert r["position"] == 4


def test_findb_not_found():
    with pytest.raises(ValueError):
        FORMULAS["findb"]({"cherche": "xyz", "texte": "Hello"})


# ─────────────────────────────────────────────────────────────────────────────
# Smoke test registre
# ─────────────────────────────────────────────────────────────────────────────
def test_registre_complet_v11():
    from app.engine.logic import FORMULA_META
    assert len(FORMULAS) == 385
    assert len(FORMULA_META) == 385
    assert set(FORMULAS.keys()) == set(FORMULA_META.keys())
