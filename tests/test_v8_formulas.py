"""Tests v8 — Ingénierie (suite) & Finance Obligations/Titres (30 formules)."""

import math

import pytest

from app.engine.logic import FORMULAS


# ─────────────────────────────────────────────────────────────────────────────
# Hyperboliques & trigo
# ─────────────────────────────────────────────────────────────────────────────
def test_sinh():
    r = FORMULAS["sinh"]({"x": 1})
    assert abs(r["resultat"] - math.sinh(1)) < 1e-9


def test_sinh_zero():
    assert FORMULAS["sinh"]({"x": 0})["resultat"] == 0.0


def test_tanh():
    r = FORMULAS["tanh"]({"x": 1})
    assert abs(r["resultat"] - math.tanh(1)) < 1e-9


def test_tanh_zero():
    assert FORMULAS["tanh"]({"x": 0})["resultat"] == 0.0


def test_sec_zero():
    assert FORMULAS["sec"]({"x": 0})["resultat"] == 1.0


def test_sec_pi_3():
    r = FORMULAS["sec"]({"x": math.pi / 3})
    assert abs(r["resultat"] - 2.0) < 1e-9


def test_sec_invalide():
    with pytest.raises(ValueError):
        FORMULAS["sec"]({"x": math.pi / 2})


def test_sech_zero():
    assert FORMULAS["sech"]({"x": 0})["resultat"] == 1.0


def test_sech_val():
    r = FORMULAS["sech"]({"x": 1})
    assert abs(r["resultat"] - (1 / math.cosh(1))) < 1e-9


# ─────────────────────────────────────────────────────────────────────────────
# IMTAN (nombre complexe)
# ─────────────────────────────────────────────────────────────────────────────
def test_imtan():
    import cmath
    r = FORMULAS["imtan"]({"nombre": "1+2i"})
    expected = cmath.tan(complex(1, 2))
    assert abs(r["reel"] - expected.real) < 1e-6
    assert abs(r["imaginaire"] - expected.imag) < 1e-6


def test_imtan_reel():
    r = FORMULAS["imtan"]({"nombre": "0"})
    assert abs(r["reel"]) < 1e-9
    assert abs(r["imaginaire"]) < 1e-9


# ─────────────────────────────────────────────────────────────────────────────
# Conversions octales
# ─────────────────────────────────────────────────────────────────────────────
def test_oct2bin():
    r = FORMULAS["oct2bin"]({"nombre": "10"})
    assert r["resultat"] == "1000"


def test_oct2bin_7():
    r = FORMULAS["oct2bin"]({"nombre": "7"})
    assert r["resultat"] == "111"


def test_oct2dec():
    assert FORMULAS["oct2dec"]({"nombre": "10"})["resultat"] == 8
    assert FORMULAS["oct2dec"]({"nombre": "77"})["resultat"] == 63


def test_oct2hex():
    r = FORMULAS["oct2hex"]({"nombre": "77"})
    assert r["resultat"] == "3F"


def test_oct_invalide():
    with pytest.raises(ValueError):
        FORMULAS["oct2bin"]({"nombre": "89"})  # 8 et 9 ne sont pas octaux


# ─────────────────────────────────────────────────────────────────────────────
# ACCRINT / ACCRINTM
# ─────────────────────────────────────────────────────────────────────────────
def test_accrint_basic():
    r = FORMULAS["accrint"]({
        "emission": "2024-01-01", "reglement": "2024-07-01", "taux": 0.05,
    })
    assert r["interets"] == 25.0  # 1000 * 0.05 * 0.5


def test_accrint_custom_nominal():
    r = FORMULAS["accrint"]({
        "emission": "2024-01-01", "reglement": "2025-01-01",
        "taux": 0.06, "valeur_nominale": 5000,
    })
    assert r["interets"] == 300.0  # 5000 * 0.06 * 1


def test_accrint_bad_dates():
    with pytest.raises(ValueError):
        FORMULAS["accrint"]({"emission": "2024-07-01", "reglement": "2024-01-01", "taux": 0.05})


def test_accrintm():
    r = FORMULAS["accrintm"]({
        "emission": "2024-01-01", "echeance": "2024-12-31", "taux": 0.06,
    })
    # 1000 * 0.06 * (360/360) = 60 approx
    assert abs(r["interets"] - 60.0) < 0.5


# ─────────────────────────────────────────────────────────────────────────────
# INTRATE / DISC
# ─────────────────────────────────────────────────────────────────────────────
def test_intrate():
    r = FORMULAS["intrate"]({
        "reglement": "2024-01-01", "echeance": "2025-01-01",
        "investissement": 1000, "remboursement": 1050,
    })
    assert abs(r["taux"] - 0.05) < 0.001


def test_disc():
    r = FORMULAS["disc"]({
        "reglement": "2024-01-01", "echeance": "2025-01-01",
        "prix": 95, "remboursement": 100,
    })
    assert abs(r["taux_escompte"] - 0.05) < 0.001


# ─────────────────────────────────────────────────────────────────────────────
# COUPONS
# ─────────────────────────────────────────────────────────────────────────────
def test_coupnum_semi():
    r = FORMULAS["coupnum"]({
        "reglement": "2024-03-15", "echeance": "2027-01-15", "frequence": 2,
    })
    assert r["nombre"] == 6


def test_coupnum_annuel():
    r = FORMULAS["coupnum"]({
        "reglement": "2024-03-15", "echeance": "2027-01-15", "frequence": 1,
    })
    assert r["nombre"] == 3


def test_coupdaybs():
    r = FORMULAS["coupdaybs"]({
        "reglement": "2024-03-15", "echeance": "2027-01-15", "frequence": 2,
    })
    assert r["jours"] == 60  # 30/360: jan15 → mar15 = 60 jours


def test_coupdays():
    r = FORMULAS["coupdays"]({
        "reglement": "2024-03-15", "echeance": "2027-01-15", "frequence": 2,
    })
    assert r["jours"] == 180  # semestriel, 30/360


def test_coupdaysnc():
    r = FORMULAS["coupdaysnc"]({
        "reglement": "2024-03-15", "echeance": "2027-01-15", "frequence": 2,
    })
    assert r["jours"] == 120  # mar15 → jul15 = 120 jours (30/360)


def test_coupncd():
    r = FORMULAS["coupncd"]({
        "reglement": "2024-03-15", "echeance": "2027-01-15", "frequence": 2,
    })
    assert r["date_coupon"] == "2024-07-15"


def test_couppcd():
    r = FORMULAS["couppcd"]({
        "reglement": "2024-03-15", "echeance": "2027-01-15", "frequence": 2,
    })
    assert r["date_coupon"] == "2024-01-15"


# ─────────────────────────────────────────────────────────────────────────────
# AMORTISSEMENTS
# ─────────────────────────────────────────────────────────────────────────────
def test_amorlinc():
    r = FORMULAS["amorlinc"]({"cout": 10000, "valeur_residuelle": 1000, "periode": 1, "taux": 0.2})
    assert r["amortissement"] == 2000.0


def test_amorlinc_first_period():
    r = FORMULAS["amorlinc"]({"cout": 10000, "valeur_residuelle": 0, "periode": 0, "taux": 0.2})
    assert r["amortissement"] == 1000.0  # prorata 50%


def test_amordegrc():
    r = FORMULAS["amordegrc"]({"cout": 10000, "valeur_residuelle": 1000, "periode": 1, "taux": 0.2})
    assert r["amortissement"] > 0


# ─────────────────────────────────────────────────────────────────────────────
# TAUX (EFFECT, NOMINAL)
# ─────────────────────────────────────────────────────────────────────────────
def test_effect():
    r = FORMULAS["effect"]({"taux_nominal": 0.05, "periodes": 12})
    assert abs(r["taux_effectif"] - 0.05116) < 0.0001


def test_nominal():
    r = FORMULAS["nominal"]({"taux_effectif": 0.05116, "periodes": 12})
    assert abs(r["taux_nominal"] - 0.05) < 0.0001


# ─────────────────────────────────────────────────────────────────────────────
# DURATION / MDURATION
# ─────────────────────────────────────────────────────────────────────────────
def test_duration_at_par():
    r = FORMULAS["duration"]({
        "taux_coupon": 0.05, "rendement": 0.05, "periodes": 10,
    })
    assert r["duration"] > 7 and r["duration"] < 9


def test_mduration_at_par():
    r = FORMULAS["mduration"]({
        "taux_coupon": 0.05, "rendement": 0.05, "periodes": 10,
    })
    assert r["duration_modifiee"] < r["duration_modifiee"] + 1  # sanity
    # mduration < duration
    d = FORMULAS["duration"]({"taux_coupon": 0.05, "rendement": 0.05, "periodes": 10})
    assert r["duration_modifiee"] < d["duration"]


# ─────────────────────────────────────────────────────────────────────────────
# DOLLAR (DOLLARDE, DOLLARFR)
# ─────────────────────────────────────────────────────────────────────────────
def test_dollarde():
    r = FORMULAS["dollarde"]({"prix_fractionnaire": 1.02, "fraction": 16})
    assert abs(r["resultat"] - 1.125) < 0.001


def test_dollarfr():
    r = FORMULAS["dollarfr"]({"prix_decimal": 1.125, "fraction": 16})
    assert abs(r["resultat"] - 1.02) < 0.001


def test_dollar_roundtrip():
    orig = 1.02
    dec = FORMULAS["dollarde"]({"prix_fractionnaire": orig, "fraction": 16})["resultat"]
    frac = FORMULAS["dollarfr"]({"prix_decimal": dec, "fraction": 16})["resultat"]
    assert abs(frac - orig) < 0.001


# ─────────────────────────────────────────────────────────────────────────────
# OBLIGATIONS ATYPIQUES (ODDFPRICE, ODDFYIELD, ODDLPRICE, ODDLYIELD)
# ─────────────────────────────────────────────────────────────────────────────
def test_oddfprice_standard():
    """Sans ajustement, retourne le prix standard."""
    r = FORMULAS["oddfprice"]({
        "taux_coupon": 0.05, "rendement": 0.05, "periodes": 10,
    })
    assert abs(r["prix"] - 100) < 3  # au pair approximatif


def test_oddfyield_at_par():
    prix = FORMULAS["oddfprice"]({
        "taux_coupon": 0.06, "rendement": 0.06, "periodes": 5,
    })["prix"]
    r = FORMULAS["oddfyield"]({
        "taux_coupon": 0.06, "prix": prix, "periodes": 5,
    })
    assert abs(r["rendement"] - 0.06) < 0.01


def test_oddlprice_standard():
    r = FORMULAS["oddlprice"]({
        "taux_coupon": 0.05, "rendement": 0.05, "periodes": 10,
    })
    assert abs(r["prix"] - 100) < 3


def test_oddlyield_at_par():
    prix = FORMULAS["oddlprice"]({
        "taux_coupon": 0.06, "rendement": 0.06, "periodes": 5,
    })["prix"]
    r = FORMULAS["oddlyield"]({
        "taux_coupon": 0.06, "prix": prix, "periodes": 5,
    })
    assert abs(r["rendement"] - 0.06) < 0.01


# ─────────────────────────────────────────────────────────────────────────────
# Smoke test registre
# ─────────────────────────────────────────────────────────────────────────────
def test_registre_complet_v8():
    from app.engine.logic import FORMULA_META
    assert len(FORMULAS) == 448
    assert len(FORMULA_META) == 448
    assert set(FORMULAS.keys()) == set(FORMULA_META.keys())
