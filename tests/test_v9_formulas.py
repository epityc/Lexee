"""Tests v9 — Finance (Titres/Bons) & Distributions (Groupe 4, 29 formules)."""

import math

import pytest

from app.engine.logic import FORMULAS


# ─────────────────────────────────────────────────────────────────────────────
# PRICE / YIELD
# ─────────────────────────────────────────────────────────────────────────────
def test_price_at_par():
    r = FORMULAS["price"]({"taux_coupon": 0.05, "rendement": 0.05, "periodes": 10})
    assert abs(r["prix"] - 100) < 0.01


def test_price_discount():
    r = FORMULAS["price"]({"taux_coupon": 0.04, "rendement": 0.06, "periodes": 10})
    assert r["prix"] < 100


def test_yield_at_par():
    r = FORMULAS["yield_val"]({"taux_coupon": 0.05, "prix": 100, "periodes": 10})
    assert abs(r["rendement"] - 0.05) < 0.01


def test_yield_roundtrip():
    prix = FORMULAS["price"]({"taux_coupon": 0.06, "rendement": 0.07, "periodes": 5})["prix"]
    r = FORMULAS["yield_val"]({"taux_coupon": 0.06, "prix": prix, "periodes": 5})
    assert abs(r["rendement"] - 0.07) < 0.01


# ─────────────────────────────────────────────────────────────────────────────
# PRICEDISC / YIELDDISC
# ─────────────────────────────────────────────────────────────────────────────
def test_pricedisc():
    r = FORMULAS["pricedisc"]({
        "reglement": "2024-01-01", "echeance": "2025-01-01", "escompte": 0.05,
    })
    assert abs(r["prix"] - 95) < 0.5


def test_yielddisc():
    r = FORMULAS["yielddisc"]({
        "reglement": "2024-01-01", "echeance": "2025-01-01", "prix": 95,
    })
    assert abs(r["rendement"] - 0.0526) < 0.01


# ─────────────────────────────────────────────────────────────────────────────
# PRICEMAT / YIELDMAT
# ─────────────────────────────────────────────────────────────────────────────
def test_pricemat():
    r = FORMULAS["pricemat"]({
        "reglement": "2024-01-01", "echeance": "2025-01-01",
        "emission": "2023-01-01", "taux": 0.05, "rendement": 0.05,
    })
    assert r["prix"] > 90


def test_yieldmat():
    r = FORMULAS["yieldmat"]({
        "reglement": "2024-01-01", "echeance": "2025-01-01",
        "emission": "2023-01-01", "taux": 0.05, "prix": 100,
    })
    assert r["rendement"] > 0


# ─────────────────────────────────────────────────────────────────────────────
# RECEIVED
# ─────────────────────────────────────────────────────────────────────────────
def test_received():
    r = FORMULAS["received"]({
        "reglement": "2024-01-01", "echeance": "2025-01-01",
        "investissement": 1000, "escompte": 0.05,
    })
    assert r["montant"] > 1000


# ─────────────────────────────────────────────────────────────────────────────
# T-BILLS
# ─────────────────────────────────────────────────────────────────────────────
def test_tbillprice():
    r = FORMULAS["tbillprice"]({
        "reglement": "2024-01-01", "echeance": "2024-07-01", "escompte": 0.05,
    })
    assert 97 < r["prix"] < 100


def test_tbillyield():
    r = FORMULAS["tbillyield"]({
        "reglement": "2024-01-01", "echeance": "2024-07-01", "prix": 97.5,
    })
    assert r["rendement"] > 0


def test_tbilleq():
    r = FORMULAS["tbilleq"]({
        "reglement": "2024-01-01", "echeance": "2024-07-01", "escompte": 0.05,
    })
    assert r["rendement"] > 0.05  # bond-equivalent > discount


# ─────────────────────────────────────────────────────────────────────────────
# VDB
# ─────────────────────────────────────────────────────────────────────────────
def test_vdb():
    r = FORMULAS["vdb"]({
        "cout": 10000, "valeur_residuelle": 1000, "duree": 5, "debut": 0, "fin": 1,
    })
    assert r["amortissement"] > 0


def test_vdb_full():
    r = FORMULAS["vdb"]({
        "cout": 10000, "valeur_residuelle": 1000, "duree": 5, "debut": 0, "fin": 5,
    })
    assert abs(r["amortissement"] - 9000) < 1  # total = coût - résiduel


# ─────────────────────────────────────────────────────────────────────────────
# AVEDEV
# ─────────────────────────────────────────────────────────────────────────────
def test_avedev():
    r = FORMULAS["avedev"]({"valeurs": [4, 5, 6, 7, 8]})
    assert abs(r["resultat"] - 1.2) < 1e-6


# ─────────────────────────────────────────────────────────────────────────────
# BETA
# ─────────────────────────────────────────────────────────────────────────────
def test_beta_dist_cdf():
    r = FORMULAS["beta_dist"]({"x": 0.5, "alpha": 2, "beta": 5})
    assert 0.8 < r["resultat"] < 1.0


def test_beta_inv_roundtrip():
    cdf = FORMULAS["beta_dist"]({"x": 0.3, "alpha": 2, "beta": 5})["resultat"]
    inv = FORMULAS["beta_inv"]({"probabilite": cdf, "alpha": 2, "beta": 5})
    assert abs(inv["resultat"] - 0.3) < 0.001


# ─────────────────────────────────────────────────────────────────────────────
# BINOMIALE
# ─────────────────────────────────────────────────────────────────────────────
def test_binom_dist_pmf():
    # C(10,3) * 0.5^10 = 120/1024 ≈ 0.1172
    r = FORMULAS["binom_dist"]({"succes": 3, "essais": 10, "probabilite": 0.5, "cumulatif": False})
    assert abs(r["resultat"] - 0.1172) < 0.001


def test_binom_dist_cdf():
    r = FORMULAS["binom_dist"]({"succes": 5, "essais": 10, "probabilite": 0.5})
    assert abs(r["resultat"] - 0.6230) < 0.001


def test_binom_dist_range():
    r = FORMULAS["binom_dist_range"]({"essais": 10, "probabilite": 0.5, "succes_min": 3, "succes_max": 7})
    assert r["resultat"] > 0.7


def test_binom_inv():
    r = FORMULAS["binom_inv"]({"essais": 10, "probabilite": 0.5, "alpha": 0.5})
    assert r["resultat"] == 5


# ─────────────────────────────────────────────────────────────────────────────
# CHI-DEUX
# ─────────────────────────────────────────────────────────────────────────────
def test_chisq_dist():
    r = FORMULAS["chisq_dist"]({"x": 7.815, "df": 3})
    assert abs(r["resultat"] - 0.95) < 0.01


def test_chisq_dist_rt():
    r = FORMULAS["chisq_dist_rt"]({"x": 7.815, "df": 3})
    assert abs(r["resultat"] - 0.05) < 0.01


def test_chisq_inv():
    r = FORMULAS["chisq_inv"]({"probabilite": 0.95, "df": 3})
    assert abs(r["resultat"] - 7.815) < 0.05


def test_chisq_inv_rt():
    r = FORMULAS["chisq_inv_rt"]({"probabilite": 0.05, "df": 3})
    assert abs(r["resultat"] - 7.815) < 0.05


def test_chisq_test():
    r = FORMULAS["chisq_test"]({"observees": [10, 20, 30], "attendues": [15, 15, 30]})
    assert r["chi2"] > 0
    assert 0 <= r["p_value"] <= 1


# ─────────────────────────────────────────────────────────────────────────────
# CONFIDENCE
# ─────────────────────────────────────────────────────────────────────────────
def test_confidence_norm():
    r = FORMULAS["confidence_norm"]({"alpha": 0.05, "ecart_type": 2.5, "taille": 50})
    assert abs(r["resultat"] - 0.693) < 0.01


def test_confidence_t():
    r = FORMULAS["confidence_t"]({"alpha": 0.05, "ecart_type": 2.5, "taille": 20})
    assert r["resultat"] > 0


# ─────────────────────────────────────────────────────────────────────────────
# COVARIANCE.S / DEVSQ
# ─────────────────────────────────────────────────────────────────────────────
def test_covariance_s():
    r = FORMULAS["covariance_s"]({"x": [1, 2, 3], "y": [2, 4, 6]})
    assert abs(r["covariance"] - 2) < 1e-6  # sample cov


def test_devsq():
    r = FORMULAS["devsq"]({"valeurs": [4, 5, 6, 7, 8]})
    assert abs(r["resultat"] - 10) < 1e-6


# ─────────────────────────────────────────────────────────────────────────────
# EXPONENTIELLE
# ─────────────────────────────────────────────────────────────────────────────
def test_expon_dist_cdf():
    r = FORMULAS["expon_dist"]({"x": 1, "lambda": 1})
    assert abs(r["resultat"] - (1 - math.exp(-1))) < 1e-6


def test_expon_dist_pdf():
    r = FORMULAS["expon_dist"]({"x": 0, "lambda": 2, "cumulatif": False})
    assert abs(r["resultat"] - 2) < 1e-6


# ─────────────────────────────────────────────────────────────────────────────
# F DISTRIBUTION
# ─────────────────────────────────────────────────────────────────────────────
def test_f_dist():
    r = FORMULAS["f_dist"]({"x": 3, "d1": 5, "d2": 10})
    assert 0 < r["resultat"] < 1


def test_f_dist_rt():
    r = FORMULAS["f_dist_rt"]({"x": 3, "d1": 5, "d2": 10})
    cdf = FORMULAS["f_dist"]({"x": 3, "d1": 5, "d2": 10})
    assert abs(r["resultat"] + cdf["resultat"] - 1) < 1e-6


# ─────────────────────────────────────────────────────────────────────────────
# Smoke test registre
# ─────────────────────────────────────────────────────────────────────────────
def test_registre_complet_v9():
    from app.engine.logic import FORMULA_META
    assert len(FORMULAS) == 489
    assert len(FORMULA_META) == 489
    assert set(FORMULAS.keys()) == set(FORMULA_META.keys())
