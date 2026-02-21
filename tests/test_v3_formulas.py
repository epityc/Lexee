"""Tests de validation pour les formules Engine v3.

Compare les résultats Python aux valeurs de référence Excel/bancaires
avec précision étendue (8 décimales pour les fonctions financières).
"""

import math
import pytest

from app.engine.logic import (
    FORMULA_META,
    FORMULAS,
    formule_agregat,
    formule_alea_entre_bornes,
    formule_assemb_h,
    formule_changer,
    formule_choisir_lignes,
    formule_danscol,
    formule_dansligne,
    formule_developper,
    formule_estnum,
    formule_esttexte,
    formule_exact,
    formule_exclure,
    formule_fraction_annee,
    formule_fractionner_texte,
    formule_frequence,
    formule_max_si_ens,
    formule_mediane,
    formule_min_si_ens,
    formule_npm,
    formule_prendre,
    formule_prevision,
    formule_rang_egal,
    formule_recherche_v,
    formule_rechercheh,
    formule_scan_map_reduce,
    formule_taux,
    formule_unicode_car,
    formule_va,
    formule_valeurnomb,
    formule_vc,
    formule_wraprows_wrapcols,
)


# ═══════════════════════════════════════════════════════════════════════════════
# REGISTRE — 62 formules au total (v1=11, v2=20, v3=31)
# ═══════════════════════════════════════════════════════════════════════════════

class TestRegistryV3:
    def test_total_count(self):
        assert len(FORMULAS) == 112

    def test_all_v3_keys_present(self):
        v3_keys = [
            "max_si_ens", "min_si_ens", "rang_egal", "mediane", "agregat",
            "taux", "npm", "vc", "va", "fraction_annee",
            "choisir_lignes", "prendre", "exclure", "developper",
            "fractionner_texte", "unicode_car",
            "exact", "estnum", "esttexte", "changer", "rechercheh",
            "prevision", "frequence", "alea_entre_bornes",
            "scan_map_reduce", "danscol", "dansligne",
            "wraprows_wrapcols", "assemb_h", "valeurnomb", "recherche_v",
        ]
        for key in v3_keys:
            assert key in FORMULAS, f"Missing FORMULAS key: {key}"
            assert key in FORMULA_META, f"Missing FORMULA_META key: {key}"


# ═══════════════════════════════════════════════════════════════════════════════
# STATISTIQUES & PERFORMANCE
# ═══════════════════════════════════════════════════════════════════════════════

class TestMaxSiEns:
    def test_basic(self):
        data = [
            {"dept": "Ventes", "ca": 100},
            {"dept": "Ventes", "ca": 250},
            {"dept": "RH", "ca": 80},
            {"dept": "Ventes", "ca": 180},
        ]
        r = formule_max_si_ens({
            "donnees": data,
            "colonne_valeur": "ca",
            "criteres": [{"colonne": "dept", "valeur": "Ventes"}],
        })
        assert r["max"] == 250
        assert r["lignes_correspondantes"] == 3

    def test_no_match_raises(self):
        with pytest.raises(ValueError):
            formule_max_si_ens({
                "donnees": [{"dept": "IT", "ca": 50}],
                "colonne_valeur": "ca",
                "criteres": [{"colonne": "dept", "valeur": "RH"}],
            })


class TestMinSiEns:
    def test_basic(self):
        data = [
            {"dept": "RH", "ca": 60},
            {"dept": "RH", "ca": 45},
            {"dept": "Ventes", "ca": 200},
        ]
        r = formule_min_si_ens({
            "donnees": data,
            "colonne_valeur": "ca",
            "criteres": [{"colonne": "dept", "valeur": "RH"}],
        })
        assert r["min"] == 45


class TestRangEgal:
    def test_rank_desc(self):
        r = formule_rang_egal({"nombre": 85, "valeurs": [95, 85, 70, 60, 90]})
        assert r["rang"] == 3  # 95, 90, 85

    def test_rank_asc(self):
        r = formule_rang_egal({"nombre": 85, "valeurs": [95, 85, 70, 60, 90], "ordre": "asc"})
        assert r["rang"] == 3  # 60, 70, 85

    def test_not_in_list(self):
        with pytest.raises(ValueError):
            formule_rang_egal({"nombre": 50, "valeurs": [10, 20, 30]})


class TestMediane:
    def test_odd(self):
        r = formule_mediane({"valeurs": [3, 1, 5, 2, 4]})
        assert r["mediane"] == 3

    def test_even(self):
        r = formule_mediane({"valeurs": [1, 2, 3, 4]})
        assert r["mediane"] == 2.5

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            formule_mediane({"valeurs": []})


class TestAgregat:
    def test_somme_ignore_errors(self):
        r = formule_agregat({
            "valeurs": [10, 20, "erreur", 30, None],
            "fonction": 9,
        })
        assert r["resultat"] == 60.0
        assert r["erreurs_ignorees"] == 2

    def test_moyenne(self):
        r = formule_agregat({"valeurs": [10, 20, 30], "fonction": 1})
        assert r["resultat"] == 20.0

    def test_unknown_function(self):
        with pytest.raises(ValueError, match="non supportée"):
            formule_agregat({"valeurs": [1, 2], "fonction": 99})


# ═══════════════════════════════════════════════════════════════════════════════
# FINANCE HIGH-TICKET — Précision bancaire (8 décimales)
# ═══════════════════════════════════════════════════════════════════════════════

class TestTaux:
    def test_rate_standard(self):
        """Excel: =RATE(240, -1319.91, 200000) ≈ 0.4167% par mois → 5% annuel"""
        r = formule_taux({
            "nb_periodes": 240,
            "mensualite": -1319.91,
            "valeur_actuelle": 200000,
        })
        assert abs(r["taux_annuel_pct"] - 5.0) < 0.01

    def test_rate_high(self):
        """Excel: =RATE(360, -3085.84, 300000) ≈ 1% mensuel → 12% annuel"""
        r = formule_taux({
            "nb_periodes": 360,
            "mensualite": -3085.84,
            "valeur_actuelle": 300000,
        })
        assert abs(r["taux_annuel_pct"] - 12.0) < 0.01


class TestNPM:
    def test_nper_standard(self):
        """Combien de mois pour rembourser 200000€ à 0.5%/mois avec -1500€/mois ?"""
        r = formule_npm({
            "taux_periodique": 0.5,
            "mensualite": -1500,
            "valeur_actuelle": 200000,
        })
        assert r["nb_periodes"] > 0
        assert r["nb_annees"] > 0

    def test_nper_zero_rate(self):
        r = formule_npm({
            "taux_periodique": 0,
            "mensualite": -1000,
            "valeur_actuelle": 120000,
        })
        assert r["nb_periodes"] == 120.0

    def test_nper_zero_pmt_zero_rate_raises(self):
        with pytest.raises(ValueError):
            formule_npm({
                "taux_periodique": 0,
                "mensualite": 0,
                "valeur_actuelle": 100000,
            })


class TestVC:
    def test_fv_savings(self):
        """500€/mois pendant 10 ans à 0.5%/mois"""
        r = formule_vc({
            "taux_periodique": 0.5,
            "nb_periodes": 120,
            "mensualite": -500,
        })
        assert r["valeur_future"] > 0  # Should accumulate value

    def test_fv_zero_rate(self):
        """Sans intérêts : FV = -(PV + PMT * N)"""
        r = formule_vc({
            "taux_periodique": 0,
            "nb_periodes": 120,
            "mensualite": -500,
            "valeur_actuelle": 0,
        })
        assert r["valeur_future"] == 60000.0

    def test_fv_lump_sum(self):
        """10000€ placés à 0.5%/mois pendant 120 mois (pas de versement)
        FV = 10000 * (1.005)^120 ≈ 18193.97"""
        r = formule_vc({
            "taux_periodique": 0.5,
            "nb_periodes": 120,
            "valeur_actuelle": -10000,
        })
        expected = 10000 * (1.005 ** 120)
        assert abs(r["valeur_future"] - round(expected, 2)) < 0.01


class TestVA:
    def test_pv_standard(self):
        """VPM(5%/12, 240, 200000) = -1319.91 → taux_periodique = 5/12 ≈ 0.41667%"""
        r = formule_va({
            "taux_periodique": 5 / 12,  # 5% annuel → mensuel
            "nb_periodes": 240,
            "mensualite": -1319.91,
        })
        assert abs(r["valeur_actuelle"] - 200000) < 100

    def test_pv_zero_rate(self):
        r = formule_va({
            "taux_periodique": 0,
            "nb_periodes": 120,
            "mensualite": -1000,
        })
        assert r["valeur_actuelle"] == 120000.0


class TestFractionAnnee:
    def test_actual_actual(self):
        """Base 1 (Actual/Actual) : 182 jours / 365 = ~0.4986"""
        r = formule_fraction_annee({
            "date_debut": "2025-01-01",
            "date_fin": "2025-07-02",
        })
        assert abs(r["fraction"] - (182 / 365)) < 0.0001
        assert r["jours"] == 182

    def test_us_30_360(self):
        """Base 0 (US 30/360)"""
        r = formule_fraction_annee({
            "date_debut": "2025-01-15",
            "date_fin": "2025-07-15",
            "base": 0,
        })
        assert r["fraction"] == 0.5  # 6 mois exactement en 30/360

    def test_actual_360(self):
        """Base 2 (Actual/360)"""
        r = formule_fraction_annee({
            "date_debut": "2025-01-01",
            "date_fin": "2025-07-01",
            "base": 2,
        })
        assert r["jours"] == 181
        assert abs(r["fraction"] - 181 / 360) < 0.0001


# ═══════════════════════════════════════════════════════════════════════════════
# MANIPULATION DE DONNÉES
# ═══════════════════════════════════════════════════════════════════════════════

class TestChoisirLignes:
    def test_positive_indices(self):
        r = formule_choisir_lignes({
            "donnees": ["A", "B", "C", "D", "E"],
            "indices": [1, 3, 5],
        })
        assert r["resultat"] == ["A", "C", "E"]

    def test_negative_indices(self):
        r = formule_choisir_lignes({
            "donnees": ["A", "B", "C", "D"],
            "indices": [-1, -2],
        })
        assert r["resultat"] == ["D", "C"]

    def test_out_of_bounds(self):
        with pytest.raises(ValueError):
            formule_choisir_lignes({"donnees": [1, 2], "indices": [5]})


class TestPrendre:
    def test_take_first(self):
        r = formule_prendre({"donnees": [10, 20, 30, 40, 50], "nb_lignes": 3})
        assert r["resultat"] == [10, 20, 30]

    def test_take_last(self):
        r = formule_prendre({"donnees": [10, 20, 30, 40, 50], "nb_lignes": -2})
        assert r["resultat"] == [40, 50]


class TestExclure:
    def test_drop_first(self):
        r = formule_exclure({"donnees": [10, 20, 30, 40, 50], "nb_lignes": 2})
        assert r["resultat"] == [30, 40, 50]

    def test_drop_last(self):
        r = formule_exclure({"donnees": [10, 20, 30, 40, 50], "nb_lignes": -2})
        assert r["resultat"] == [10, 20, 30]


class TestDevelopper:
    def test_expand(self):
        r = formule_developper({"donnees": ["A", "B"], "nb_lignes": 5, "valeur_defaut": "N/A"})
        assert r["resultat"] == ["A", "B", "N/A", "N/A", "N/A"]

    def test_expand_truncate(self):
        r = formule_developper({"donnees": [1, 2, 3, 4, 5], "nb_lignes": 3})
        assert r["resultat"] == [1, 2, 3]


class TestFractionnerTexte:
    def test_simple_split(self):
        r = formule_fractionner_texte({"texte": "a,b,c", "delimiteur_col": ","})
        assert r["resultat"] == ["a", "b", "c"]

    def test_2d_split(self):
        r = formule_fractionner_texte({
            "texte": "a,b;c,d",
            "delimiteur_col": ",",
            "delimiteur_ligne": ";",
        })
        assert r["resultat"] == [["a", "b"], ["c", "d"]]


class TestUnicodeCar:
    def test_char_to_code(self):
        r = formule_unicode_car({"caractere": "A"})
        assert r["code_unicode"] == 65

    def test_code_to_char(self):
        r = formule_unicode_car({"code": 8364})
        assert r["caractere"] == "€"

    def test_bidirectional(self):
        r = formule_unicode_car({"caractere": "Z", "code": 90})
        assert r["code_unicode"] == 90
        assert r["caractere"] == "Z"

    def test_multi_char_raises(self):
        with pytest.raises(ValueError):
            formule_unicode_car({"caractere": "AB"})


# ═══════════════════════════════════════════════════════════════════════════════
# LOGIQUE & VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

class TestExact:
    def test_identical(self):
        r = formule_exact({"texte1": "Excel", "texte2": "Excel"})
        assert r["identique"] is True

    def test_case_sensitive(self):
        r = formule_exact({"texte1": "Excel", "texte2": "excel"})
        assert r["identique"] is False


class TestEstnum:
    def test_mixed(self):
        r = formule_estnum({"valeurs": [42, "texte", 3.14, None, "100"]})
        assert r["resultats"] == [True, False, True, False, True]
        assert r["nb_numeriques"] == 3


class TestEsttexte:
    def test_mixed(self):
        r = formule_esttexte({"valeurs": ["Paris", 42, "hello", 3.14, None]})
        assert r["resultats"] == [True, False, True, False, False]
        assert r["nb_textes"] == 2


class TestChanger:
    def test_switch_match(self):
        r = formule_changer({
            "expression": "B",
            "cas": [
                {"valeur": "A", "resultat": "Alpha"},
                {"valeur": "B", "resultat": "Beta"},
                {"valeur": "C", "resultat": "Charlie"},
            ],
        })
        assert r["resultat"] == "Beta"
        assert r["cas_matche"] == "B"

    def test_switch_default(self):
        r = formule_changer({
            "expression": "Z",
            "cas": [{"valeur": "A", "resultat": "Alpha"}],
            "defaut": "Inconnu",
        })
        assert r["resultat"] == "Inconnu"
        assert r["cas_matche"] is None


class TestRechercheh:
    def test_found(self):
        r = formule_rechercheh({
            "valeur_cherchee": "Mars",
            "en_tetes": ["Janvier", "Février", "Mars", "Avril"],
            "donnees": [[100, 200, 350, 400], [50, 80, 120, 150]],
            "ligne_retour": 1,
        })
        assert r["resultat"] == 350
        assert r["trouve"] is True

    def test_not_found(self):
        r = formule_rechercheh({
            "valeur_cherchee": "Décembre",
            "en_tetes": ["Janvier", "Février"],
            "donnees": [[100, 200]],
        })
        assert r["trouve"] is False

    def test_second_row(self):
        r = formule_rechercheh({
            "valeur_cherchee": "Mars",
            "en_tetes": ["Janvier", "Février", "Mars"],
            "donnees": [[10, 20, 30], [40, 50, 60]],
            "ligne_retour": 2,
        })
        assert r["resultat"] == 60


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSE & PRÉDICTION
# ═══════════════════════════════════════════════════════════════════════════════

class TestPrevision:
    def test_linear(self):
        """y = 2x + 1 → prédiction pour x=6 → 13"""
        r = formule_prevision({
            "x_cible": 6,
            "x_connus": [1, 2, 3, 4, 5],
            "y_connus": [3, 5, 7, 9, 11],
        })
        assert abs(r["prevision"] - 13.0) < 0.0001
        assert abs(r["pente"] - 2.0) < 0.0001
        assert abs(r["r_carre"] - 1.0) < 0.0001

    def test_needs_two_points(self):
        with pytest.raises(ValueError):
            formule_prevision({"x_cible": 1, "x_connus": [1], "y_connus": [1]})


class TestFrequence:
    def test_distribution(self):
        r = formule_frequence({
            "donnees": [10, 25, 35, 45, 55, 65, 75, 85, 95],
            "bornes": [30, 60, 90],
        })
        assert r["frequences"] == [2, 3, 3, 1]
        assert r["total"] == 9
        assert len(r["labels"]) == 4

    def test_all_below(self):
        r = formule_frequence({
            "donnees": [1, 2, 3],
            "bornes": [10],
        })
        assert r["frequences"] == [3, 0]


class TestAleaEntreBornes:
    def test_single(self):
        r = formule_alea_entre_bornes({"borne_inf": 1, "borne_sup": 1})
        assert r["valeurs"] == 1

    def test_multiple(self):
        r = formule_alea_entre_bornes({"borne_inf": 1, "borne_sup": 100, "nombre": 50})
        assert len(r["valeurs"]) == 50
        assert all(1 <= v <= 100 for v in r["valeurs"])

    def test_invalid_bounds(self):
        with pytest.raises(ValueError):
            formule_alea_entre_bornes({"borne_inf": 100, "borne_sup": 1})


# ═══════════════════════════════════════════════════════════════════════════════
# STRUCTURE & TABLEAUX
# ═══════════════════════════════════════════════════════════════════════════════

class TestScanMapReduce:
    def test_scan_cumul(self):
        r = formule_scan_map_reduce({"valeurs": [10, 20, 30], "operation": "somme_cumul"})
        assert r["resultat"] == [10.0, 30.0, 60.0]

    def test_reduce_produit(self):
        r = formule_scan_map_reduce({"valeurs": [2, 3, 4], "operation": "produit"})
        assert r["resultat"] == 24.0

    def test_map_carre(self):
        r = formule_scan_map_reduce({"valeurs": [2, 3, 4], "operation": "carre"})
        assert r["resultat"] == [4.0, 9.0, 16.0]

    def test_map_racine(self):
        r = formule_scan_map_reduce({"valeurs": [4, 9, 16], "operation": "racine"})
        assert r["resultat"] == [2.0, 3.0, 4.0]

    def test_unknown_op(self):
        with pytest.raises(ValueError, match="inconnue"):
            formule_scan_map_reduce({"valeurs": [1], "operation": "invalid"})


class TestDanscol:
    def test_flatten_2d(self):
        r = formule_danscol({"donnees": [[1, 2], [3, 4]]})
        assert r["resultat"] == [1, 2, 3, 4]

    def test_flatten_mixed(self):
        r = formule_danscol({"donnees": [1, [2, 3], 4]})
        assert r["resultat"] == [1, 2, 3, 4]


class TestDansligne:
    def test_flatten(self):
        r = formule_dansligne({"donnees": [[1, 2, 3], [4, 5, 6]]})
        assert r["resultat"] == [1, 2, 3, 4, 5, 6]


class TestWraprowsWrapcols:
    def test_wraprows(self):
        r = formule_wraprows_wrapcols({
            "valeurs": [1, 2, 3, 4, 5, 6],
            "taille": 3,
            "mode": "rows",
        })
        assert r["resultat"] == [[1, 2, 3], [4, 5, 6]]

    def test_with_padding(self):
        r = formule_wraprows_wrapcols({
            "valeurs": [1, 2, 3, 4, 5],
            "taille": 3,
            "valeur_pad": 0,
        })
        assert r["resultat"] == [[1, 2, 3], [4, 5, 0]]

    def test_invalid_size(self):
        with pytest.raises(ValueError):
            formule_wraprows_wrapcols({"valeurs": [1, 2], "taille": 0})


class TestAssembH:
    def test_two_columns(self):
        r = formule_assemb_h({"tableaux": [[1, 2, 3], [4, 5, 6]]})
        assert r["resultat"] == [[1, 4], [2, 5], [3, 6]]
        assert r["lignes"] == 3

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            formule_assemb_h({"tableaux": []})


class TestValeurnomb:
    def test_french_format(self):
        r = formule_valeurnomb({
            "texte": "1 234,56",
            "sep_decimal": ",",
            "sep_milliers": " ",
        })
        assert r["nombre"] == 1234.56

    def test_with_currency(self):
        r = formule_valeurnomb({"texte": "$42.99"})
        assert r["nombre"] == 42.99

    def test_simple_number(self):
        r = formule_valeurnomb({"texte": "3.14"})
        assert r["nombre"] == 3.14


class TestRechercheV:
    def test_exact_match(self):
        r = formule_recherche_v({
            "valeur_cherchee": 50,
            "vecteur_recherche": [10, 20, 50, 80, 100],
            "vecteur_retour": ["F", "E", "D", "C", "B"],
        })
        assert r["resultat"] == "D"
        assert r["position"] == 3

    def test_approximate_match(self):
        """75 → plus grande valeur ≤ 75 = 50 (position 3)"""
        r = formule_recherche_v({
            "valeur_cherchee": 75,
            "vecteur_recherche": [10, 20, 50, 80, 100],
            "vecteur_retour": ["F", "E", "D", "C", "B"],
        })
        assert r["resultat"] == "D"

    def test_no_match_raises(self):
        with pytest.raises(ValueError):
            formule_recherche_v({
                "valeur_cherchee": 5,
                "vecteur_recherche": [10, 20, 30],
                "vecteur_retour": ["A", "B", "C"],
            })


# ═══════════════════════════════════════════════════════════════════════════════
# CROSS-VALIDATION FINANCE — Consistance entre formules liées
# ═══════════════════════════════════════════════════════════════════════════════

class TestFinanceCrossValidation:
    def test_rate_pv_roundtrip(self):
        """VPM → TAUX → vérifier cohérence"""
        from app.engine.logic import formule_vpm
        # 1) Calculer la mensualité
        pmt_r = formule_vpm({
            "taux_annuel": 6,
            "nb_periodes": 180,
            "valeur_actuelle": 250000,
        })
        pmt = pmt_r["mensualite"]

        # 2) Retrouver le taux depuis la mensualité
        rate_r = formule_taux({
            "nb_periodes": 180,
            "mensualite": pmt,
            "valeur_actuelle": 250000,
        })
        assert abs(rate_r["taux_annuel_pct"] - 6.0) < 0.01

    def test_pv_fv_consistency(self):
        """PV(taux, n, pmt) + FV(taux, n, pmt) doivent être cohérents"""
        # Si PV=100000 et pas de PMT, FV = -PV * (1+r)^n
        r_fv = formule_vc({
            "taux_periodique": 0.5,
            "nb_periodes": 60,
            "valeur_actuelle": -100000,
        })
        fv = r_fv["valeur_future"]

        # Retrouver PV à partir de FV
        r_pv = formule_va({
            "taux_periodique": 0.5,
            "nb_periodes": 60,
            "valeur_future": -fv,
        })
        assert abs(r_pv["valeur_actuelle"] - 100000) < 1.0

    def test_nper_consistency(self):
        """NPM doit être cohérent avec VPM"""
        from app.engine.logic import formule_vpm
        pmt_r = formule_vpm({
            "taux_annuel": 6,
            "nb_periodes": 360,
            "valeur_actuelle": 300000,
        })
        pmt = pmt_r["mensualite"]

        nper_r = formule_npm({
            "taux_periodique": 0.5,  # 6% / 12
            "mensualite": pmt,
            "valeur_actuelle": 300000,
        })
        assert abs(nper_r["nb_periodes"] - 360) < 0.1
