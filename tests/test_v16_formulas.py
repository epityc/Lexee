"""Tests v16 — Analyse de Données & Divers (Groupe 11, 19 formules)."""

import math
from datetime import date

import pytest

from app.engine.logic import FORMULAS


# ─────────────────────────────────────────────────────────────────────────────
# IMAGE / ANCHORARRAY / FORMULATEXT (stubs)
# ─────────────────────────────────────────────────────────────────────────────
def test_image():
    r = FORMULAS["image"]({"url": "https://example.com/img.png", "alt_text": "test"})
    assert "IMAGE" in r["resultat"]
    assert r["url"] == "https://example.com/img.png"


def test_anchorarray():
    r = FORMULAS["anchorarray"]({"reference": "B2"})
    assert r["resultat"] == "#B2"


def test_formulatext():
    r = FORMULAS["formulatext"]({"formule": "=SUM(A1:A10)"})
    assert r["resultat"] == "=SUM(A1:A10)"


# ─────────────────────────────────────────────────────────────────────────────
# GETPIVOTDATA / HYPERLINK / RTD / STOCKHISTORY (stubs)
# ─────────────────────────────────────────────────────────────────────────────
def test_getpivotdata():
    r = FORMULAS["getpivotdata"]({"champ": "Revenue"})
    assert r["champ"] == "Revenue"


def test_hyperlink():
    r = FORMULAS["hyperlink"]({"url": "https://example.com", "texte": "Click"})
    assert r["resultat"] == "Click"
    assert r["url"] == "https://example.com"


def test_rtd():
    r = FORMULAS["rtd"]({})
    assert "message" in r


def test_stockhistory():
    r = FORMULAS["stockhistory"]({"symbole": "AAPL"})
    assert r["symbole"] == "AAPL"


# ─────────────────────────────────────────────────────────────────────────────
# EUROCONVERT
# ─────────────────────────────────────────────────────────────────────────────
def test_euroconvert_frf_eur():
    # 100 FRF → EUR : 100 / 6.55957 ≈ 15.2449
    r = FORMULAS["euroconvert"]({"nombre": 100, "source": "FRF", "cible": "EUR"})
    assert abs(r["resultat"] - 15.2449) < 0.01


def test_euroconvert_dem_frf():
    r = FORMULAS["euroconvert"]({"nombre": 100, "source": "DEM", "cible": "FRF"})
    assert r["resultat"] > 300  # 100 DEM ≈ 335 FRF


def test_euroconvert_roundtrip():
    r1 = FORMULAS["euroconvert"]({"nombre": 100, "source": "EUR", "cible": "DEM"})
    r2 = FORMULAS["euroconvert"]({"nombre": r1["resultat"], "source": "DEM", "cible": "EUR"})
    assert abs(r2["resultat"] - 100) < 0.01


def test_euroconvert_invalid():
    with pytest.raises(ValueError):
        FORMULAS["euroconvert"]({"nombre": 100, "source": "USD", "cible": "EUR"})


# ─────────────────────────────────────────────────────────────────────────────
# SINGLE
# ─────────────────────────────────────────────────────────────────────────────
def test_single_2d():
    r = FORMULAS["single"]({"valeur": [[1, 2], [3, 4]]})
    assert r["resultat"] == 1


def test_single_1d():
    r = FORMULAS["single"]({"valeur": [10, 20, 30]})
    assert r["resultat"] == 10


def test_single_scalar():
    r = FORMULAS["single"]({"valeur": 42})
    assert r["resultat"] == 42


# ─────────────────────────────────────────────────────────────────────────────
# LET
# ─────────────────────────────────────────────────────────────────────────────
def test_let_val():
    r = FORMULAS["let_val"]({"variables": {"x": 10, "y": 20}, "expression": "x + y"})
    assert r["resultat"] == 30


def test_let_val_math():
    r = FORMULAS["let_val"]({"variables": {"r": 5}, "expression": "math.pi * r ** 2"})
    assert abs(r["resultat"] - 78.5398) < 0.01


# ─────────────────────────────────────────────────────────────────────────────
# ISPMT
# ─────────────────────────────────────────────────────────────────────────────
def test_ispmt():
    # ISPMT(0.01, 1, 36, 100000) = -100000 * 0.01 * (1 - 1/36) ≈ -972.22
    r = FORMULAS["ispmt"]({"taux": 0.01, "periode": 1, "nb_periodes": 36, "valeur_actuelle": 100000})
    assert abs(r["resultat"] - (-972.222)) < 1


def test_ispmt_last_period():
    # Last period: interest ≈ 0
    r = FORMULAS["ispmt"]({"taux": 0.01, "periode": 36, "nb_periodes": 36, "valeur_actuelle": 100000})
    assert abs(r["resultat"]) < 1


# ─────────────────────────────────────────────────────────────────────────────
# CUMIPMT / CUMPRINC
# ─────────────────────────────────────────────────────────────────────────────
def test_cumipmt():
    r = FORMULAS["cumipmt"]({
        "taux": 0.01, "nb_periodes": 12, "valeur_actuelle": 10000,
        "periode_debut": 1, "periode_fin": 12,
    })
    assert r["resultat"] > 0


def test_cumprinc():
    r = FORMULAS["cumprinc"]({
        "taux": 0.01, "nb_periodes": 12, "valeur_actuelle": 10000,
        "periode_debut": 1, "periode_fin": 12,
    })
    assert abs(r["resultat"] - 10000) < 1  # total principal ≈ loan amount


def test_cumipmt_plus_cumprinc():
    params = {"taux": 0.01, "nb_periodes": 12, "valeur_actuelle": 10000,
              "periode_debut": 1, "periode_fin": 12}
    interest = FORMULAS["cumipmt"](params)["resultat"]
    principal = FORMULAS["cumprinc"](params)["resultat"]
    pmt = 10000 * 0.01 / (1 - 1.01 ** -12)
    assert abs(interest + principal - pmt * 12) < 0.01


# ─────────────────────────────────────────────────────────────────────────────
# PDURATION / RRI
# ─────────────────────────────────────────────────────────────────────────────
def test_pduration():
    # Time to double at 5%: ln(2)/ln(1.05) ≈ 14.2067
    r = FORMULAS["pduration"]({"taux": 0.05, "valeur_actuelle": 1000, "valeur_future": 2000})
    assert abs(r["resultat"] - 14.2067) < 0.01


def test_rri():
    # Rate to double in 10 periods: 2^(1/10) - 1 ≈ 0.07177
    r = FORMULAS["rri"]({"nb_periodes": 10, "valeur_actuelle": 1000, "valeur_future": 2000})
    assert abs(r["resultat"] - 0.07177) < 0.001


def test_pduration_rri_roundtrip():
    taux = 0.08
    n = FORMULAS["pduration"]({"taux": taux, "valeur_actuelle": 500, "valeur_future": 1000})["resultat"]
    r = FORMULAS["rri"]({"nb_periodes": round(n), "valeur_actuelle": 500, "valeur_future": 1000})
    assert abs(r["resultat"] - taux) < 0.01


# ─────────────────────────────────────────────────────────────────────────────
# ISOWEEKNUM
# ─────────────────────────────────────────────────────────────────────────────
def test_isoweeknum():
    assert FORMULAS["isoweeknum"]({"date": "2024-01-01"})["resultat"] == 1


def test_isoweeknum_dec():
    assert FORMULAS["isoweeknum"]({"date": "2024-12-31"})["resultat"] == 1  # belongs to week 1 of 2025


# ─────────────────────────────────────────────────────────────────────────────
# NETWORKDAYS.INTL
# ─────────────────────────────────────────────────────────────────────────────
def test_networkdays_intl_standard():
    # Jan 2024: 23 workdays (Mon-Fri)
    r = FORMULAS["networkdays_intl"]({"date_debut": "2024-01-01", "date_fin": "2024-01-31"})
    assert r["resultat"] == 23


def test_networkdays_intl_with_holidays():
    r = FORMULAS["networkdays_intl"]({
        "date_debut": "2024-01-01", "date_fin": "2024-01-31",
        "jours_feries": ["2024-01-15"],
    })
    assert r["resultat"] == 22


# ─────────────────────────────────────────────────────────────────────────────
# WORKDAY.INTL
# ─────────────────────────────────────────────────────────────────────────────
def test_workday_intl():
    r = FORMULAS["workday_intl"]({"date_debut": "2024-01-01", "jours": 5})
    assert r["resultat"] == "2024-01-08"  # skip weekend


def test_workday_intl_negative():
    r = FORMULAS["workday_intl"]({"date_debut": "2024-01-08", "jours": -5})
    assert r["resultat"] == "2024-01-01"


# ─────────────────────────────────────────────────────────────────────────────
# BITXOR
# ─────────────────────────────────────────────────────────────────────────────
def test_bitxor():
    assert FORMULAS["bitxor"]({"nombre1": 5, "nombre2": 3})["resultat"] == 6  # 101 ^ 011 = 110


def test_bitxor_same():
    assert FORMULAS["bitxor"]({"nombre1": 7, "nombre2": 7})["resultat"] == 0


def test_bitxor_negative():
    with pytest.raises(ValueError):
        FORMULAS["bitxor"]({"nombre1": -1, "nombre2": 3})


# ─────────────────────────────────────────────────────────────────────────────
# Smoke test registre
# ─────────────────────────────────────────────────────────────────────────────
def test_registre_complet_v16():
    from app.engine.logic import FORMULA_META
    assert len(FORMULAS) == 494
    assert len(FORMULA_META) == 494
    assert set(FORMULAS.keys()) == set(FORMULA_META.keys())
