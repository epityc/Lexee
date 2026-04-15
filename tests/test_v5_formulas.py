"""Tests pour les 50 formules v5."""

import math

import pytest

from app.engine.logic import FORMULAS


# ─────────────────────────────────────────────────────────────────────────────
# Intelligence Moderne
# ─────────────────────────────────────────────────────────────────────────────
def test_groupby_count():
    donnees = [{"r": "EU", "x": 10}, {"r": "EU", "x": 20}, {"r": "US", "x": 5}]
    r = FORMULAS["groupby"]({"donnees": donnees, "cle": "r"})
    assert r["groupes"] == {"EU": 2, "US": 1}


def test_groupby_sum():
    donnees = [{"r": "EU", "x": 10}, {"r": "EU", "x": 20}, {"r": "US", "x": 5}]
    r = FORMULAS["groupby"]({
        "donnees": donnees, "cle": "r", "champ": "x", "agregation": "sum",
    })
    assert r["groupes"]["EU"] == 30
    assert r["groupes"]["US"] == 5


def test_pivotby():
    donnees = [
        {"p": "A", "r": "EU", "v": 10},
        {"p": "A", "r": "US", "v": 20},
        {"p": "B", "r": "EU", "v": 30},
    ]
    r = FORMULAS["pivotby"]({
        "donnees": donnees, "ligne_cle": "p", "colonne_cle": "r", "champ": "v",
    })
    assert len(r["pivot"]) == 2
    assert set(r["colonnes"]) == {"EU", "US"}


def test_regex_extract():
    r = FORMULAS["regex_extract"]({
        "texte": "Emails: a@b.co, x@y.fr",
        "motif": r"\w+@\w+\.\w+",
    })
    assert r["nombre"] == 2
    assert "a@b.co" in r["correspondances"]


def test_regex_match_ok():
    r = FORMULAS["regex_match"]({"texte": "Hello World", "motif": r"^H\w+"})
    assert r["correspond"] is True
    assert r["match"] == "Hello"


def test_regex_match_ko():
    r = FORMULAS["regex_match"]({"texte": "hello", "motif": r"^\d"})
    assert r["correspond"] is False


def test_regex_replace():
    r = FORMULAS["regex_replace"]({
        "texte": "Paris 2024 - Londres 2025",
        "motif": r"\d+",
        "remplacement": "XXXX",
    })
    assert r["resultat"] == "Paris XXXX - Londres XXXX"
    assert r["remplacements"] == 2


# ─────────────────────────────────────────────────────────────────────────────
# Statistiques avancées
# ─────────────────────────────────────────────────────────────────────────────
def test_tendance():
    r = FORMULAS["tendance"]({
        "y_connus": [10, 20, 30], "x_connus": [1, 2, 3], "x_nouveaux": [4, 5],
    })
    assert r["y_nouveaux"] == [40.0, 50.0]
    assert r["pente"] == 10.0


def test_croissance():
    r = FORMULAS["croissance"]({
        "y_connus": [2, 4, 8], "x_connus": [1, 2, 3], "x_nouveaux": [4],
    })
    # factor = 2
    assert abs(r["y_nouveaux"][0] - 16) < 0.001


def test_covariance_p():
    r = FORMULAS["covariance_p"]({"x": [1, 2, 3], "y": [2, 4, 6]})
    # cov population = 4/3
    assert abs(r["covariance"] - 4 / 3) < 1e-6


def test_prevision_ets():
    r = FORMULAS["prevision_ets"]({"valeurs": [10, 12, 14, 16], "periodes": 2})
    assert len(r["previsions"]) == 2
    assert r["previsions"][0] > 10


def test_percentile_exc():
    r = FORMULAS["percentile_exc"]({"valeurs": [1, 2, 3, 4], "k": 0.5})
    assert r["percentile"] == 2.5


# ─────────────────────────────────────────────────────────────────────────────
# Ingénierie & Conversion
# ─────────────────────────────────────────────────────────────────────────────
def test_convertir_longueur():
    r = FORMULAS["convertir"]({"nombre": 1000, "depuis": "m", "vers": "km"})
    assert r["resultat"] == 1.0


def test_convertir_temperature():
    r = FORMULAS["convertir"]({"nombre": 100, "depuis": "c", "vers": "f"})
    assert abs(r["resultat"] - 212) < 0.01


def test_convertir_incompat():
    with pytest.raises(ValueError):
        FORMULAS["convertir"]({"nombre": 1, "depuis": "m", "vers": "kg"})


def test_bin2hex():
    r = FORMULAS["bin2hex"]({"nombre": "1010"})
    assert r["resultat"] == "A"


def test_hex2dec():
    r = FORMULAS["hex2dec"]({"nombre": "FF"})
    assert r["resultat"] == 255


def test_dec2bin():
    r = FORMULAS["dec2bin"]({"nombre": 10})
    assert r["resultat"] == "1010"


def test_dec2hex():
    r = FORMULAS["dec2hex"]({"nombre": 255})
    assert r["resultat"] == "FF"


def test_delta():
    assert FORMULAS["delta"]({"a": 5, "b": 5})["resultat"] == 1
    assert FORMULAS["delta"]({"a": 5, "b": 4})["resultat"] == 0


def test_bit_et():
    r = FORMULAS["bit_et"]({"a": 12, "b": 10})
    assert r["resultat"] == 8


def test_bit_ou():
    r = FORMULAS["bit_ou"]({"a": 12, "b": 10})
    assert r["resultat"] == 14


def test_bit_xou():
    r = FORMULAS["bit_xou"]({"a": 12, "b": 10})
    assert r["resultat"] == 6


def test_erf_val():
    r = FORMULAS["erf_val"]({"x": 0})
    assert r["resultat"] == 0
    r2 = FORMULAS["erf_val"]({"x": 1})
    assert abs(r2["resultat"] - math.erf(1)) < 1e-6


# ─────────────────────────────────────────────────────────────────────────────
# Finance Professionnelle
# ─────────────────────────────────────────────────────────────────────────────
def test_taux_effectif():
    r = FORMULAS["taux_effectif"]({"taux_nominal": 0.05, "periodes": 12})
    assert abs(r["taux_effectif"] - 0.05116) < 0.0001


def test_taux_nominal():
    r = FORMULAS["taux_nominal"]({"taux_effectif": 0.05116, "periodes": 12})
    assert abs(r["taux_nominal"] - 0.05) < 0.0001


def test_tri_modifie():
    r = FORMULAS["tri_modifie"]({
        "flux": [-1000, 300, 400, 500],
        "taux_financement": 0.08,
        "taux_reinvestissement": 0.1,
    })
    assert 0 < r["tri_modifie"] < 0.3


def test_van_dates():
    r = FORMULAS["van_dates"]({
        "taux": 0.09,
        "flux": [-10000, 2500, 5000, 5000],
        "dates": ["2024-01-01", "2024-06-01", "2025-01-01", "2025-06-01"],
    })
    assert isinstance(r["van"], float)


def test_tri_dates():
    r = FORMULAS["tri_dates"]({
        "flux": [-10000, 5000, 6000],
        "dates": ["2024-01-01", "2024-12-31", "2025-06-30"],
    })
    assert r["tri"] > 0


def test_amort_ddb():
    r = FORMULAS["amort_ddb"]({
        "cout": 10000, "valeur_residuelle": 1000, "duree": 5, "periode": 1,
    })
    assert r["amortissement"] == 4000


def test_prix_obligation():
    r = FORMULAS["prix_obligation"]({
        "valeur_nominale": 100, "taux_coupon": 0.05, "rendement": 0.05,
        "periodes": 10, "frequence": 2,
    })
    assert abs(r["prix"] - 100) < 0.01  # au pair


# ─────────────────────────────────────────────────────────────────────────────
# Bases de Données
# ─────────────────────────────────────────────────────────────────────────────
def test_bdlire_unique():
    base = [
        {"ref": "A", "prix": 10},
        {"ref": "B", "prix": 20},
    ]
    r = FORMULAS["bdlire"]({"base": base, "champ": "prix", "criteres": {"ref": "B"}})
    assert r["resultat"] == 20


def test_bdlire_multiple_erreur():
    base = [{"r": "A"}, {"r": "A"}]
    with pytest.raises(ValueError):
        FORMULAS["bdlire"]({"base": base, "champ": "r", "criteres": {"r": "A"}})


def test_bdproduit():
    base = [
        {"region": "EU", "facteur": 2},
        {"region": "EU", "facteur": 3},
        {"region": "US", "facteur": 4},
    ]
    r = FORMULAS["bdproduit"]({
        "base": base, "champ": "facteur", "criteres": {"region": "EU"},
    })
    assert r["produit"] == 6


def test_bdecartype():
    base = [
        {"y": 2020, "ca": 100},
        {"y": 2020, "ca": 200},
        {"y": 2020, "ca": 300},
    ]
    r = FORMULAS["bdecartype"]({
        "base": base, "champ": "ca", "criteres": {"y": 2020},
    })
    assert abs(r["ecart_type"] - 100) < 1e-6


# ─────────────────────────────────────────────────────────────────────────────
# Mathématiques Spécialisées
# ─────────────────────────────────────────────────────────────────────────────
def test_arrondi_multiple():
    r = FORMULAS["arrondi_multiple"]({"nombre": 10.3, "multiple": 0.25})
    assert r["resultat"] == 10.25


def test_pgcd():
    r = FORMULAS["pgcd"]({"nombres": [12, 18, 24]})
    assert r["pgcd"] == 6


def test_ppcm():
    r = FORMULAS["ppcm"]({"nombres": [4, 6, 8]})
    assert r["ppcm"] == 24


def test_quotient():
    r = FORMULAS["quotient"]({"numerateur": 17, "denominateur": 5})
    assert r["quotient"] == 3


def test_tableau_alea_forme():
    r = FORMULAS["tableau_alea"]({"lignes": 2, "colonnes": 3, "graine": 42})
    assert len(r["matrice"]) == 2
    assert len(r["matrice"][0]) == 3


def test_tableau_alea_determinisme():
    a = FORMULAS["tableau_alea"]({"lignes": 2, "colonnes": 2, "graine": 7})
    b = FORMULAS["tableau_alea"]({"lignes": 2, "colonnes": 2, "graine": 7})
    assert a["matrice"] == b["matrice"]


def test_combinaison():
    r = FORMULAS["combinaison"]({"n": 10, "k": 3})
    assert r["combinaison"] == 120


def test_factorielle():
    r = FORMULAS["factorielle"]({"n": 6})
    assert r["factorielle"] == 720


def test_sommeprod():
    r = FORMULAS["sommeprod"]({"tableaux": [[1, 2, 3], [4, 5, 6]]})
    assert r["resultat"] == 1 * 4 + 2 * 5 + 3 * 6


def test_romain():
    assert FORMULAS["romain"]({"nombre": 1999})["romain"] == "MCMXCIX"
    assert FORMULAS["romain"]({"nombre": 4})["romain"] == "IV"


def test_signe():
    assert FORMULAS["signe"]({"nombre": -42})["signe"] == -1
    assert FORMULAS["signe"]({"nombre": 0})["signe"] == 0
    assert FORMULAS["signe"]({"nombre": 3.14})["signe"] == 1


# ─────────────────────────────────────────────────────────────────────────────
# Logique de précision
# ─────────────────────────────────────────────────────────────────────────────
def test_si_na_na():
    r = FORMULAS["si_na"]({"valeur": "#N/A", "fallback": "Néant"})
    assert r["resultat"] == "Néant"


def test_si_na_valide():
    r = FORMULAS["si_na"]({"valeur": 42, "fallback": "x"})
    assert r["resultat"] == 42


def test_esterr():
    assert FORMULAS["esterr"]({"valeur": "#DIV/0!"})["resultat"] is True
    assert FORMULAS["esterr"]({"valeur": 42})["resultat"] is False


def test_nb_val():
    r = FORMULAS["nb_val"]({"valeurs": [1, "", "a", None, 0]})
    assert r["resultat"] == 3


def test_nb_vide():
    r = FORMULAS["nb_vide"]({"valeurs": [1, "", "a", None, 0]})
    assert r["resultat"] == 2


# ─────────────────────────────────────────────────────────────────────────────
# Statistiques supplémentaires
# ─────────────────────────────────────────────────────────────────────────────
def test_mode_val():
    r = FORMULAS["mode_val"]({"valeurs": [1, 2, 2, 3, 4]})
    assert r["mode"] == 2
    assert r["frequence"] == 2


def test_mode_val_unique_erreur():
    with pytest.raises(ValueError):
        FORMULAS["mode_val"]({"valeurs": [1, 2, 3]})


def test_grande_valeur():
    r = FORMULAS["grande_valeur"]({"valeurs": [10, 7, 3, 9], "k": 2})
    assert r["resultat"] == 9


def test_petite_valeur():
    r = FORMULAS["petite_valeur"]({"valeurs": [10, 7, 3, 9], "k": 2})
    assert r["resultat"] == 7


def test_moyenne_geo():
    r = FORMULAS["moyenne_geo"]({"valeurs": [2, 8]})
    assert abs(r["resultat"] - 4) < 1e-6


def test_moyenne_harm():
    r = FORMULAS["moyenne_harm"]({"valeurs": [2, 4, 4]})
    # 3 / (1/2 + 1/4 + 1/4) = 3
    assert abs(r["resultat"] - 3) < 1e-6


def test_ecart_moyen():
    r = FORMULAS["ecart_moyen"]({"valeurs": [4, 5, 6, 7, 8]})
    # moyenne = 6 ; écarts = 2+1+0+1+2 = 6 ; /5 = 1.2
    assert abs(r["resultat"] - 1.2) < 1e-6


# ─────────────────────────────────────────────────────────────────────────────
# Smoke test du registre
# ─────────────────────────────────────────────────────────────────────────────
def test_registre_complet():
    from app.engine.logic import FORMULA_META
    assert len(FORMULAS) == 183
    assert len(FORMULA_META) == 183
    assert set(FORMULAS.keys()) == set(FORMULA_META.keys())
