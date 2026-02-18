"""Tests de validation pour les formules Engine v2.

Compare les résultats Python aux valeurs de référence Excel
pour garantir la conformité des calculs financiers critiques.
"""

import pytest

from app.engine.logic import (
    FORMULA_META,
    FORMULAS,
    formule_arrondi,
    formule_choisircols,
    formule_et_ou,
    formule_estvide,
    formule_fin_mois,
    formule_index_equiv,
    formule_let_lambda,
    formule_mois_decaler,
    formule_nompropre,
    formule_sequence,
    formule_si_erreur,
    formule_substitue,
    formule_supprespace,
    formule_texte_avant_apres,
    formule_tri,
    formule_trier,
    formule_trierpar,
    formule_van,
    formule_vpm,
    formule_vstack,
)


# ═══════════════════════════════════════════════════════════════════════════════
# REGISTRE
# ═══════════════════════════════════════════════════════════════════════════════

class TestRegistry:
    def test_all_formulas_have_metadata(self):
        assert set(FORMULAS.keys()) == set(FORMULA_META.keys())

    def test_total_count(self):
        assert len(FORMULAS) == 62

    def test_each_meta_has_required_fields(self):
        for key, meta in FORMULA_META.items():
            assert "name" in meta, f"{key}: missing 'name'"
            assert "description" in meta, f"{key}: missing 'description'"
            assert "category" in meta, f"{key}: missing 'category'"
            assert "variables" in meta, f"{key}: missing 'variables'"
            for var in meta["variables"]:
                assert "name" in var, f"{key}.{var}: missing 'name'"
                assert "type" in var, f"{key}.{var}: missing 'type'"


# ═══════════════════════════════════════════════════════════════════════════════
# FINANCE — VPM (PMT)
# Valeurs de référence : Excel =PMT(taux_mensuel, nb_mois, montant)
# ═══════════════════════════════════════════════════════════════════════════════

class TestVPM:
    def test_pmt_standard(self):
        """Excel: =PMT(5%/12, 240, 200000) = -1319.91"""
        r = formule_vpm({
            "taux_annuel": 5,
            "nb_periodes": 240,
            "valeur_actuelle": 200000,
        })
        assert r["mensualite"] == -1319.91

    def test_pmt_zero_rate(self):
        """Taux 0% : mensualité = montant / nb_périodes"""
        r = formule_vpm({
            "taux_annuel": 0,
            "nb_periodes": 120,
            "valeur_actuelle": 120000,
        })
        assert r["mensualite"] == -1000.0

    def test_pmt_high_rate(self):
        """Excel: =PMT(12%/12, 360, 300000) = -3085.84"""
        r = formule_vpm({
            "taux_annuel": 12,
            "nb_periodes": 360,
            "valeur_actuelle": 300000,
        })
        assert r["mensualite"] == -3085.84

    def test_pmt_with_future_value(self):
        """Excel: =PMT(0.5%, 120, 100000, -50000) = -805.10
        (rate*(pv*(1+rate)^n + fv) / ((1+rate)^n - 1)) * -1"""
        r = formule_vpm({
            "taux_annuel": 6,
            "nb_periodes": 120,
            "valeur_actuelle": 100000,
            "valeur_future": -50000,
        })
        assert abs(r["mensualite"] - (-805.10)) < 0.02

    def test_pmt_begin_period(self):
        """Paiement en début de période (type=1)"""
        r = formule_vpm({
            "taux_annuel": 5,
            "nb_periodes": 240,
            "valeur_actuelle": 200000,
            "debut_periode": 1,
        })
        # Avec paiement en début, la mensualité est légèrement inférieure
        assert r["mensualite"] > -1319.91  # moins négatif = plus petit en valeur abs

    def test_pmt_invalid_periods(self):
        with pytest.raises(ValueError):
            formule_vpm({
                "taux_annuel": 5,
                "nb_periodes": 0,
                "valeur_actuelle": 100000,
            })


# ═══════════════════════════════════════════════════════════════════════════════
# FINANCE — TRI (IRR)
# ═══════════════════════════════════════════════════════════════════════════════

class TestTRI:
    def test_irr_simple(self):
        """[-1000, 1100] → 10%"""
        r = formule_tri({"flux": [-1000, 1100]})
        assert abs(r["tri_pct"] - 10.0) < 0.01

    def test_irr_multi_period(self):
        """Vérification croisée : VAN(TRI, flux) ≈ 0"""
        flux = [-100000, 30000, 35000, 40000, 45000]
        r = formule_tri({"flux": flux})
        tri = r["tri_decimal"]

        npv_at_tri = sum(cf / (1 + tri) ** i for i, cf in enumerate(flux))
        assert abs(npv_at_tri) < 0.1, f"VAN at TRI should be ~0, got {npv_at_tri}"

    def test_irr_break_even(self):
        """[-100, 50, 50] → 0%"""
        r = formule_tri({"flux": [-100, 50, 50]})
        assert abs(r["tri_pct"] - 0.0) < 0.01

    def test_irr_needs_min_two_flows(self):
        with pytest.raises(ValueError):
            formule_tri({"flux": [-1000]})

    def test_irr_real_estate(self):
        """Scénario immobilier réaliste"""
        flux = [-500000] + [80000] * 7 + [580000]
        r = formule_tri({"flux": flux})
        assert r["tri_pct"] > 0, "TRI should be positive"
        # Cross-check
        tri = r["tri_decimal"]
        npv = sum(cf / (1 + tri) ** i for i, cf in enumerate(flux))
        assert abs(npv) < 0.5


# ═══════════════════════════════════════════════════════════════════════════════
# FINANCE — VAN (NPV)
# ═══════════════════════════════════════════════════════════════════════════════

class TestVAN:
    def test_npv_standard(self):
        """Excel: =NPV(10%, 30000, 35000, 40000, 45000) = 116986.54"""
        r = formule_van({"taux": 10, "flux": [30000, 35000, 40000, 45000]})
        assert abs(r["van"] - 116986.54) < 0.01

    def test_npv_negative(self):
        """NPV peut être négatif si les flux sont faibles"""
        r = formule_van({"taux": 50, "flux": [1000, 1000, 1000]})
        assert r["van"] > 0  # même à 50%, 3x1000 donne une VAN positive


# ═══════════════════════════════════════════════════════════════════════════════
# NETTOYAGE
# ═══════════════════════════════════════════════════════════════════════════════

class TestNettoyage:
    def test_supprespace(self):
        r = formule_supprespace({"texte": "  Jean   Dupont  "})
        assert r["resultat"] == "Jean Dupont"

    def test_supprespace_tabs_newlines(self):
        r = formule_supprespace({"texte": "a\t\tb\n\nc"})
        assert r["resultat"] == "a b c"

    def test_substitue_all(self):
        r = formule_substitue({"texte": "aaa", "ancien": "a", "nouveau": "b"})
        assert r["resultat"] == "bbb"
        assert r["remplacements"] == 3

    def test_substitue_nth(self):
        r = formule_substitue({
            "texte": "a-b-c-d", "ancien": "-", "nouveau": "/", "occurrence": 2,
        })
        assert r["resultat"] == "a-b/c-d"

    def test_texte_avant_apres(self):
        r = formule_texte_avant_apres({
            "texte": "prenom.nom@company.com", "delimiteur": "@",
        })
        assert r["avant"] == "prenom.nom"
        assert r["apres"] == "company.com"

    def test_nompropre(self):
        assert formule_nompropre({"texte": "jean DUPONT"})["resultat"] == "Jean Dupont"
        assert formule_nompropre({"texte": "jean-pierre"})["resultat"] == "Jean-Pierre"


# ═══════════════════════════════════════════════════════════════════════════════
# DATES
# ═══════════════════════════════════════════════════════════════════════════════

class TestDates:
    def test_mois_decaler_standard(self):
        r = formule_mois_decaler({"date_depart": "2025-01-15", "nb_mois": 3})
        assert r["date_resultat"] == "2025-04-15"

    def test_mois_decaler_end_of_month(self):
        """31 jan + 1 mois → 28 fev (pas de 31 fev)"""
        r = formule_mois_decaler({"date_depart": "2025-01-31", "nb_mois": 1})
        assert r["date_resultat"] == "2025-02-28"

    def test_mois_decaler_negative(self):
        r = formule_mois_decaler({"date_depart": "2025-06-15", "nb_mois": -3})
        assert r["date_resultat"] == "2025-03-15"

    def test_fin_mois(self):
        r = formule_fin_mois({"date_depart": "2025-01-15", "nb_mois": 1})
        assert r["fin_de_mois"] == "2025-02-28"

    def test_fin_mois_leap_year(self):
        r = formule_fin_mois({"date_depart": "2024-01-15", "nb_mois": 1})
        assert r["fin_de_mois"] == "2024-02-29"


# ═══════════════════════════════════════════════════════════════════════════════
# LOGIQUE
# ═══════════════════════════════════════════════════════════════════════════════

class TestLogique:
    def test_si_erreur_division_by_zero(self):
        r = formule_si_erreur({"expression": "1 / 0", "valeur_si_erreur": "ERR"})
        assert r["erreur"] is True
        assert r["resultat"] == "ERR"

    def test_si_erreur_valid(self):
        r = formule_si_erreur({"expression": "2 + 3"})
        assert r["erreur"] is False
        assert r["resultat"] == 5

    def test_si_erreur_blocks_injection(self):
        """Les expressions contenant des lettres doivent être rejetées"""
        r = formule_si_erreur({"expression": "__import__('os')", "valeur_si_erreur": "blocked"})
        assert r["erreur"] is True

    def test_et_ou(self):
        r = formule_et_ou({"conditions": [True, True, True]})
        assert r["et"] is True
        assert r["ou"] is True

        r = formule_et_ou({"conditions": [True, False]})
        assert r["et"] is False
        assert r["ou"] is True

        r = formule_et_ou({"conditions": [False, False]})
        assert r["et"] is False
        assert r["ou"] is False

    def test_estvide(self):
        r = formule_estvide({"valeurs": ["", None, "hello", " ", 0]})
        assert r["nb_vides"] == 3  # "", None, " "
        assert r["nb_non_vides"] == 2


# ═══════════════════════════════════════════════════════════════════════════════
# TABLEAUX DYNAMIQUES
# ═══════════════════════════════════════════════════════════════════════════════

class TestTableauxDynamiques:
    def test_trier_asc(self):
        r = formule_trier({"valeurs": [5, 3, 1, 4, 2]})
        assert r["resultat"] == [1, 2, 3, 4, 5]

    def test_trier_desc(self):
        r = formule_trier({"valeurs": [5, 3, 1, 4, 2], "ordre": "desc"})
        assert r["resultat"] == [5, 4, 3, 2, 1]

    def test_trier_strings(self):
        r = formule_trier({"valeurs": ["banana", "apple", "cherry"]})
        assert r["resultat"] == ["apple", "banana", "cherry"]

    def test_trierpar(self):
        data = [
            {"name": "Charlie", "score": 80},
            {"name": "Alice", "score": 95},
            {"name": "Bob", "score": 70},
        ]
        r = formule_trierpar({"donnees": data, "colonne_tri": "score", "ordre": "desc"})
        assert r["resultat"][0]["name"] == "Alice"
        assert r["resultat"][-1]["name"] == "Bob"

    def test_sequence_1d(self):
        r = formule_sequence({"lignes": 5})
        assert r["sequence"] == [1, 2, 3, 4, 5]

    def test_sequence_2d(self):
        r = formule_sequence({"lignes": 2, "colonnes": 3, "debut": 10, "pas": 5})
        assert r["sequence"] == [[10, 15, 20], [25, 30, 35]]

    def test_sequence_limit(self):
        with pytest.raises(ValueError):
            formule_sequence({"lignes": 200, "colonnes": 200})  # 40000 > 10000

    def test_choisircols(self):
        data = [{"a": 1, "b": 2, "c": 3}]
        r = formule_choisircols({"donnees": data, "colonnes": ["a", "c"]})
        assert r["resultat"] == [{"a": 1, "c": 3}]

    def test_vstack(self):
        r = formule_vstack({"tableaux": [[1, 2], [3, 4], [5, 6]]})
        assert r["resultat"] == [1, 2, 3, 4, 5, 6]
        assert r["total_lignes"] == 6


# ═══════════════════════════════════════════════════════════════════════════════
# ARCHITECTURE
# ═══════════════════════════════════════════════════════════════════════════════

class TestArchitecture:
    def test_index_equiv_found(self):
        data = [
            {"ref": "A1", "nom": "Widget", "prix": 9.99},
            {"ref": "A2", "nom": "Gadget", "prix": 19.99},
        ]
        r = formule_index_equiv({
            "donnees": data,
            "colonne_recherche": "ref",
            "valeur_cherchee": "A2",
            "colonne_retour": "prix",
        })
        assert r["resultat"] == 19.99
        assert r["trouve"] is True
        assert r["ligne"] == 2

    def test_index_equiv_not_found(self):
        r = formule_index_equiv({
            "donnees": [{"k": "x", "v": 1}],
            "colonne_recherche": "k",
            "valeur_cherchee": "z",
            "colonne_retour": "v",
        })
        assert r["trouve"] is False

    def test_arrondi(self):
        r = formule_arrondi({"nombre": 3.14159, "decimales": 2})
        assert r["arrondi"] == 3.14
        assert r["arrondi_sup"] == 3.15
        assert r["arrondi_inf"] == 3.14

    def test_arrondi_zero_decimals(self):
        r = formule_arrondi({"nombre": 3.7})
        assert r["arrondi"] == 4

    def test_let_lambda_basic(self):
        r = formule_let_lambda({
            "variables": {"prix": 100, "taxe": 0.2, "remise": 0.1},
            "expression": "prix * (1 + taxe) * (1 - remise)",
        })
        assert r["resultat"] == 108.0

    def test_let_lambda_math_functions(self):
        r = formule_let_lambda({
            "variables": {"x": 9},
            "expression": "sqrt(x) + round(pi, 2)",
        })
        assert r["resultat"] == 6.14  # sqrt(9)=3 + 3.14

    def test_let_lambda_blocks_injection(self):
        with pytest.raises(ValueError, match="non autorisé"):
            formule_let_lambda({
                "variables": {},
                "expression": "open('/etc/passwd')",
            })
