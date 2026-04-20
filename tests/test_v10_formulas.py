"""Tests v10 — Statistiques Avancées (Groupe 5, 29 formules)."""

import math

import pytest

from app.engine.logic import FORMULAS


# ─────────────────────────────────────────────────────────────────────────────
# F.INV / F.TEST
# ─────────────────────────────────────────────────────────────────────────────
def test_f_inv():
    r = FORMULAS["f_inv"]({"probabilite": 0.95, "d1": 5, "d2": 10})
    assert abs(r["resultat"] - 3.3258) < 0.05


def test_f_inv_rt():
    r = FORMULAS["f_inv_rt"]({"probabilite": 0.05, "d1": 5, "d2": 10})
    assert abs(r["resultat"] - 3.3258) < 0.05


def test_f_test():
    r = FORMULAS["f_test"]({"x": [1, 2, 3, 4, 5], "y": [2, 4, 6, 8, 10]})
    assert r["f_stat"] > 0
    assert 0 <= r["p_value"] <= 1


# ─────────────────────────────────────────────────────────────────────────────
# FISHER / FISHERINV
# ─────────────────────────────────────────────────────────────────────────────
def test_fisher():
    r = FORMULAS["fisher"]({"x": 0.5})
    assert abs(r["resultat"] - 0.5493) < 0.001


def test_fisherinv():
    r = FORMULAS["fisherinv"]({"y": 0.5493})
    assert abs(r["resultat"] - 0.5) < 0.001


def test_fisher_roundtrip():
    f = FORMULAS["fisher"]({"x": 0.75})["resultat"]
    inv = FORMULAS["fisherinv"]({"y": f})
    assert abs(inv["resultat"] - 0.75) < 0.001


# ─────────────────────────────────────────────────────────────────────────────
# GAMMA
# ─────────────────────────────────────────────────────────────────────────────
def test_gamma_val():
    assert abs(FORMULAS["gamma_val"]({"x": 5})["resultat"] - 24) < 1e-6


def test_gamma_val_half():
    r = FORMULAS["gamma_val"]({"x": 0.5})
    assert abs(r["resultat"] - math.sqrt(math.pi)) < 1e-6


def test_gamma_dist_cdf():
    r = FORMULAS["gamma_dist"]({"x": 2, "alpha": 2, "beta": 1})
    assert 0.5 < r["resultat"] < 1


def test_gamma_inv_roundtrip():
    cdf = FORMULAS["gamma_dist"]({"x": 3, "alpha": 2, "beta": 1})["resultat"]
    inv = FORMULAS["gamma_inv"]({"probabilite": cdf, "alpha": 2, "beta": 1})
    assert abs(inv["resultat"] - 3) < 0.05


def test_gammaln():
    r = FORMULAS["gammaln"]({"x": 5})
    assert abs(r["resultat"] - math.lgamma(5)) < 1e-6


def test_gammaln_precis():
    r = FORMULAS["gammaln_precis"]({"x": 5})
    assert abs(r["resultat"] - math.lgamma(5)) < 1e-6


# ─────────────────────────────────────────────────────────────────────────────
# GAUSS
# ─────────────────────────────────────────────────────────────────────────────
def test_gauss_196():
    r = FORMULAS["gauss"]({"x": 1.96})
    assert abs(r["resultat"] - 0.475) < 0.001


def test_gauss_zero():
    assert FORMULAS["gauss"]({"x": 0})["resultat"] == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# HARMEAN
# ─────────────────────────────────────────────────────────────────────────────
def test_harmean():
    r = FORMULAS["harmean"]({"valeurs": [2, 4, 4]})
    assert abs(r["resultat"] - 3) < 1e-6


# ─────────────────────────────────────────────────────────────────────────────
# HYPGEOM.DIST
# ─────────────────────────────────────────────────────────────────────────────
def test_hypgeom_dist_pmf():
    r = FORMULAS["hypgeom_dist"]({
        "succes_echantillon": 1, "taille_echantillon": 4,
        "succes_population": 8, "taille_population": 20, "cumulatif": False,
    })
    assert 0 < r["resultat"] < 1


def test_hypgeom_dist_cdf():
    r = FORMULAS["hypgeom_dist"]({
        "succes_echantillon": 2, "taille_echantillon": 4,
        "succes_population": 8, "taille_population": 20,
    })
    assert 0 < r["resultat"] < 1


# ─────────────────────────────────────────────────────────────────────────────
# KURT
# ─────────────────────────────────────────────────────────────────────────────
def test_kurt_uniform():
    r = FORMULAS["kurt"]({"valeurs": [1, 2, 3, 4, 5, 6, 7, 8]})
    assert abs(r["resultat"] - (-1.2)) < 0.01  # platykurtic


def test_kurt_minimum_values():
    with pytest.raises(ValueError):
        FORMULAS["kurt"]({"valeurs": [1, 2, 3]})


# ─────────────────────────────────────────────────────────────────────────────
# LOGNORM
# ─────────────────────────────────────────────────────────────────────────────
def test_lognorm_dist_cdf():
    r = FORMULAS["lognorm_dist"]({"x": 1, "moyenne": 0, "ecart_type": 1})
    assert abs(r["resultat"] - 0.5) < 0.01  # median of lognormal(0,1)


def test_lognorm_inv_roundtrip():
    cdf = FORMULAS["lognorm_dist"]({"x": 2, "moyenne": 0, "ecart_type": 1})["resultat"]
    inv = FORMULAS["lognorm_inv"]({"probabilite": cdf, "moyenne": 0, "ecart_type": 1})
    assert abs(inv["resultat"] - 2) < 0.01


# ─────────────────────────────────────────────────────────────────────────────
# NEGBINOM
# ─────────────────────────────────────────────────────────────────────────────
def test_negbinom_dist_pmf():
    r = FORMULAS["negbinom_dist"]({"echecs": 2, "succes": 3, "probabilite": 0.5, "cumulatif": False})
    # C(4,2) * 0.5^5 = 6 * 0.03125 = 0.1875
    assert abs(r["resultat"] - 0.1875) < 0.001


def test_negbinom_dist_cdf():
    r = FORMULAS["negbinom_dist"]({"echecs": 5, "succes": 3, "probabilite": 0.5})
    assert 0 < r["resultat"] < 1


# ─────────────────────────────────────────────────────────────────────────────
# NORM
# ─────────────────────────────────────────────────────────────────────────────
def test_norm_dist_cdf():
    r = FORMULAS["norm_dist"]({"x": 0, "moyenne": 0, "ecart_type": 1})
    assert abs(r["resultat"] - 0.5) < 1e-6


def test_norm_inv():
    r = FORMULAS["norm_inv"]({"probabilite": 0.975, "moyenne": 0, "ecart_type": 1})
    assert abs(r["resultat"] - 1.96) < 0.01


def test_norm_s_dist():
    r = FORMULAS["norm_s_dist"]({"z": 1.96})
    assert abs(r["resultat"] - 0.975) < 0.001


def test_norm_s_inv():
    r = FORMULAS["norm_s_inv"]({"probabilite": 0.975})
    assert abs(r["resultat"] - 1.96) < 0.01


# ─────────────────────────────────────────────────────────────────────────────
# PEARSON
# ─────────────────────────────────────────────────────────────────────────────
def test_pearson_perfect():
    r = FORMULAS["pearson"]({"x": [1, 2, 3, 4, 5], "y": [2, 4, 6, 8, 10]})
    assert abs(r["resultat"] - 1) < 1e-6


def test_pearson_negative():
    r = FORMULAS["pearson"]({"x": [1, 2, 3], "y": [6, 4, 2]})
    assert abs(r["resultat"] - (-1)) < 1e-6


# ─────────────────────────────────────────────────────────────────────────────
# PERCENTRANK
# ─────────────────────────────────────────────────────────────────────────────
def test_percentrank():
    r = FORMULAS["percentrank"]({"valeurs": [1, 2, 3, 4, 5], "x": 3})
    assert abs(r["resultat"] - 0.5) < 0.01


def test_percentrank_exc():
    r = FORMULAS["percentrank_exc"]({"valeurs": [1, 2, 3, 4, 5], "x": 3})
    assert 0 < r["resultat"] < 1


def test_percentrank_inc():
    r = FORMULAS["percentrank_inc"]({"valeurs": [1, 2, 3, 4, 5], "x": 3})
    assert abs(r["resultat"] - 0.5) < 0.01


# ─────────────────────────────────────────────────────────────────────────────
# PHI
# ─────────────────────────────────────────────────────────────────────────────
def test_phi_zero():
    r = FORMULAS["phi"]({"x": 0})
    assert abs(r["resultat"] - 0.3989) < 0.001  # 1/sqrt(2*pi)


def test_phi_symmetric():
    a = FORMULAS["phi"]({"x": 1})["resultat"]
    b = FORMULAS["phi"]({"x": -1})["resultat"]
    assert abs(a - b) < 1e-9


# ─────────────────────────────────────────────────────────────────────────────
# POISSON
# ─────────────────────────────────────────────────────────────────────────────
def test_poisson_dist_pmf():
    # P(X=3 | λ=2.5) = e^{-2.5} * 2.5^3 / 3! ≈ 0.2138
    r = FORMULAS["poisson_dist"]({"x": 3, "moyenne": 2.5, "cumulatif": False})
    assert abs(r["resultat"] - 0.2138) < 0.001


def test_poisson_dist_cdf():
    r = FORMULAS["poisson_dist"]({"x": 3, "moyenne": 2.5})
    assert 0.7 < r["resultat"] < 0.8


# ─────────────────────────────────────────────────────────────────────────────
# PROB
# ─────────────────────────────────────────────────────────────────────────────
def test_prob():
    r = FORMULAS["prob"]({
        "valeurs": [1, 2, 3, 4],
        "probabilites": [0.1, 0.2, 0.3, 0.4],
        "borne_inf": 2, "borne_sup": 3,
    })
    assert abs(r["resultat"] - 0.5) < 1e-6


def test_prob_single():
    r = FORMULAS["prob"]({
        "valeurs": [10, 20, 30],
        "probabilites": [0.3, 0.4, 0.3],
        "borne_inf": 20,
    })
    assert abs(r["resultat"] - 0.4) < 1e-6


# ─────────────────────────────────────────────────────────────────────────────
# QUARTILE.EXC
# ─────────────────────────────────────────────────────────────────────────────
def test_quartile_exc_median():
    r = FORMULAS["quartile_exc"]({"valeurs": [1, 2, 3, 4, 5], "quart": 2})
    assert abs(r["resultat"] - 3) < 0.01


def test_quartile_exc_q1():
    r = FORMULAS["quartile_exc"]({"valeurs": [1, 2, 3, 4, 5, 6, 7], "quart": 1})
    assert r["resultat"] == 2.0


def test_quartile_exc_invalid():
    with pytest.raises(ValueError):
        FORMULAS["quartile_exc"]({"valeurs": [1, 2, 3], "quart": 4})


# ─────────────────────────────────────────────────────────────────────────────
# Smoke test registre
# ─────────────────────────────────────────────────────────────────────────────
def test_registre_complet_v10():
    from app.engine.logic import FORMULA_META
    assert len(FORMULAS) == 493
    assert len(FORMULA_META) == 493
    assert set(FORMULAS.keys()) == set(FORMULA_META.keys())
