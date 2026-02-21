"""Tests de validation pour les formules Engine v4 — Enterprise Pack.

50 formules couvrant : Audit & Amortissements, Ingénierie & Matrices,
Statistiques de Décision, Texte Industriel, D-Functions,
Manipulation Avancée, Utilitaires Data.
"""

import math
import pytest

from app.engine.logic import (
    FORMULA_META,
    FORMULAS,
    formule_abs_val,
    formule_amordegr,
    formule_amorl,
    formule_bdmax,
    formule_bdmin,
    formule_bdmoyenne,
    formule_bdnb,
    formule_bdsomme,
    formule_bycol,
    formule_byrow,
    formule_cherche,
    formule_choose,
    formule_cnum,
    formule_coordonnees,
    formule_correlation,
    formule_ctxt,
    formule_cumul_inter,
    formule_cumul_princ,
    formule_determinant,
    formule_ecart_type_p,
    formule_ecart_type_s,
    formule_esterreur,
    formule_estna,
    formule_flatten,
    formule_indirect_ext,
    formule_intper,
    formule_lambda_recursive,
    formule_let_advanced,
    formule_majuscule,
    formule_makearray,
    formule_matrice_inverse,
    formule_minuscule,
    formule_mod,
    formule_moyenne_reduite,
    formule_nbcar,
    formule_ordonnee_origine,
    formule_pente,
    formule_percentile,
    formule_plafond_plancher,
    formule_princper,
    formule_produitmat,
    formule_puissance,
    formule_quartile,
    formule_remplacer,
    formule_rept,
    formule_syd,
    formule_texte_join,
    formule_transpose,
    formule_type_val,
    formule_valeur,
)


# ═══════════════════════════════════════════════════════════════════════════════
# REGISTRE — 112 formules au total (v1=11, v2=20, v3=31, v4=50)
# ═══════════════════════════════════════════════════════════════════════════════

class TestRegistryV4:
    def test_total_count(self):
        assert len(FORMULAS) == 112

    def test_meta_count_matches(self):
        assert len(FORMULA_META) == 112

    def test_all_v4_audit_keys(self):
        audit_keys = ["intper", "princper", "cumul_inter", "cumul_princ", "amorl", "amordegr", "syd"]
        for k in audit_keys:
            assert k in FORMULAS, f"Clé manquante : {k}"

    def test_all_v4_engineering_keys(self):
        eng_keys = ["transpose", "produitmat", "matrice_inverse", "determinant", "flatten",
                     "byrow", "bycol", "makearray"]
        for k in eng_keys:
            assert k in FORMULAS, f"Clé manquante : {k}"

    def test_all_v4_stats_keys(self):
        stat_keys = ["correlation", "pente", "ordonnee_origine", "ecart_type_p", "ecart_type_s",
                      "quartile", "percentile", "moyenne_reduite"]
        for k in stat_keys:
            assert k in FORMULAS, f"Clé manquante : {k}"

    def test_all_v4_text_keys(self):
        text_keys = ["rept", "cherche", "remplacer_texte", "texte_join", "valeur_texte", "ctxt"]
        for k in text_keys:
            assert k in FORMULAS, f"Clé manquante : {k}"

    def test_all_v4_dfunc_keys(self):
        df_keys = ["bdsomme", "bdnb", "bdmax", "bdmin", "bdmoyenne"]
        for k in df_keys:
            assert k in FORMULAS, f"Clé manquante : {k}"

    def test_all_v4_advanced_keys(self):
        adv_keys = ["lambda_recursive", "let_advanced", "choose", "byrow", "bycol", "makearray"]
        for k in adv_keys:
            assert k in FORMULAS, f"Clé manquante : {k}"

    def test_all_v4_utility_keys(self):
        util_keys = ["esterreur", "estna", "type_val", "coordonnees", "indirect_ext",
                      "nbcar", "majuscule", "minuscule", "cnum", "abs_val", "mod_val",
                      "puissance", "plafond_plancher"]
        for k in util_keys:
            assert k in FORMULAS, f"Clé manquante : {k}"

    def test_v4_categories_present(self):
        categories = {m["category"] for m in FORMULA_META.values()}
        for cat in ["Audit Financier", "Ingénierie", "Statistiques Avancées", "Gestion de Données"]:
            assert cat in categories, f"Catégorie manquante : {cat}"


# ═══════════════════════════════════════════════════════════════════════════════
# AUDIT & AMORTISSEMENTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestIntper:
    """IPMT — part d'intérêts d'une période."""

    def test_basic_period_1(self):
        r = formule_intper({
            "taux_periodique": 0.833333,  # 10%/12 converti en pourcentage
            "periode": 1, "nb_periodes": 36, "valeur_actuelle": 100000
        })
        # Période 1 : intérêts = VA * taux
        assert "interets" in r
        assert abs(r["interets"]) > 0

    def test_ipmt_plus_ppmt_equals_pmt(self):
        """IPMT + PPMT doit être égal à PMT (propriété fondamentale)."""
        params = {
            "taux_periodique": 0.5,  # 0.5% par mois = 6%/12
            "periode": 1, "nb_periodes": 60, "valeur_actuelle": 200000
        }
        ipmt = formule_intper(params)["interets"]
        ppmt = formule_princper(params)["principal"]

        # Calcul PMT attendu
        taux = 0.005
        n = 60
        va = 200000
        pmt = -(va * (1 + taux) ** n) / (((1 + taux) ** n - 1) / taux)

        assert abs(ipmt + ppmt - round(pmt, 2)) <= 0.02

    def test_period_out_of_range(self):
        with pytest.raises(ValueError, match="hors limites"):
            formule_intper({
                "taux_periodique": 1, "periode": 0, "nb_periodes": 12, "valeur_actuelle": 10000
            })

    def test_zero_rate(self):
        r = formule_intper({
            "taux_periodique": 0, "periode": 5, "nb_periodes": 10, "valeur_actuelle": 5000
        })
        assert r["interets"] == 0.0


class TestPrincper:
    """PPMT — part de principal d'une période."""

    def test_basic(self):
        r = formule_princper({
            "taux_periodique": 0.5, "periode": 1, "nb_periodes": 12, "valeur_actuelle": 10000
        })
        assert "principal" in r
        assert abs(r["principal"]) > 0

    def test_zero_rate(self):
        r = formule_princper({
            "taux_periodique": 0, "periode": 1, "nb_periodes": 10, "valeur_actuelle": 5000
        })
        # PMT = -(5000+0)/10 = -500, IPMT=0, PPMT=-500
        assert r["principal"] == -500.0


class TestCumulInter:
    """CUMIPMT — cumul d'intérêts sur une plage."""

    def test_full_range(self):
        r = formule_cumul_inter({
            "taux_periodique": 1, "nb_periodes": 12, "valeur_actuelle": 10000,
            "periode_debut": 1, "periode_fin": 12
        })
        assert "cumul_interets" in r
        assert r["cumul_interets"] != 0  # Des intérêts ont été payés

    def test_single_period(self):
        r = formule_cumul_inter({
            "taux_periodique": 1, "nb_periodes": 12, "valeur_actuelle": 10000,
            "periode_debut": 1, "periode_fin": 1
        })
        ipmt = formule_intper({
            "taux_periodique": 1, "periode": 1, "nb_periodes": 12, "valeur_actuelle": 10000
        })
        assert abs(r["cumul_interets"] - ipmt["interets"]) < 0.01

    def test_invalid_range(self):
        with pytest.raises(ValueError, match="invalide"):
            formule_cumul_inter({
                "taux_periodique": 1, "nb_periodes": 12, "valeur_actuelle": 10000,
                "periode_debut": 5, "periode_fin": 3
            })


class TestCumulPrinc:
    """CUMPRINC — cumul de principal sur une plage."""

    def test_basic(self):
        r = formule_cumul_princ({
            "taux_periodique": 1, "nb_periodes": 12, "valeur_actuelle": 10000,
            "periode_debut": 1, "periode_fin": 12
        })
        assert "cumul_principal" in r

    def test_cumul_inter_plus_princ(self):
        """Cumul intérêts + cumul principal = total des paiements."""
        params = {
            "taux_periodique": 0.5, "nb_periodes": 12, "valeur_actuelle": 10000,
            "periode_debut": 1, "periode_fin": 12
        }
        ci = formule_cumul_inter(params)["cumul_interets"]
        cp = formule_cumul_princ(params)["cumul_principal"]

        # Total des paiements = nb_periodes * PMT
        taux = 0.005
        n = 12
        va = 10000
        pmt = -(va * (1 + taux) ** n) / (((1 + taux) ** n - 1) / taux)
        total_paid = round(pmt, 2) * n

        assert abs((ci + cp) - total_paid) < 1.0  # tolérance pour arrondis


class TestAmorl:
    """SLN — amortissement linéaire."""

    def test_basic(self):
        r = formule_amorl({"cout": 10000, "valeur_residuelle": 1000, "duree_vie": 10})
        assert r["amortissement_annuel"] == 900.0
        assert r["duree"] == 10

    def test_no_residual(self):
        r = formule_amorl({"cout": 5000, "valeur_residuelle": 0, "duree_vie": 5})
        assert r["amortissement_annuel"] == 1000.0

    def test_zero_duration(self):
        with pytest.raises(ValueError, match="doit être > 0"):
            formule_amorl({"cout": 10000, "valeur_residuelle": 0, "duree_vie": 0})


class TestAmordegr:
    """DB — amortissement dégressif."""

    def test_basic(self):
        r = formule_amordegr({"cout": 10000, "valeur_residuelle": 1000, "duree_vie": 5, "periode": 1})
        assert r["amortissement"] > 0
        assert r["valeur_nette"] < 10000
        assert r["taux"] > 0

    def test_decreasing_depreciation(self):
        """L'amortissement diminue d'une période à l'autre."""
        r1 = formule_amordegr({"cout": 10000, "valeur_residuelle": 1000, "duree_vie": 5, "periode": 1})
        r2 = formule_amordegr({"cout": 10000, "valeur_residuelle": 1000, "duree_vie": 5, "periode": 2})
        assert r1["amortissement"] > r2["amortissement"]

    def test_period_out_of_range(self):
        with pytest.raises(ValueError, match="hors limites"):
            formule_amordegr({"cout": 10000, "valeur_residuelle": 1000, "duree_vie": 5, "periode": 6})


class TestSyd:
    """SYD — amortissement à taux décroissant."""

    def test_basic(self):
        # SYD(10000, 1000, 5, 1) = 9000 * 5/15 = 3000
        r = formule_syd({"cout": 10000, "valeur_residuelle": 1000, "duree_vie": 5, "periode": 1})
        assert r["amortissement"] == 3000.0

    def test_sum_equals_depreciable_amount(self):
        """La somme de toutes les périodes = coût - valeur résiduelle."""
        total = 0
        for p in range(1, 6):
            r = formule_syd({"cout": 10000, "valeur_residuelle": 1000, "duree_vie": 5, "periode": p})
            total += r["amortissement"]
        assert abs(total - 9000) < 0.01

    def test_last_period(self):
        # SYD(10000, 1000, 5, 5) = 9000 * 1/15 = 600
        r = formule_syd({"cout": 10000, "valeur_residuelle": 1000, "duree_vie": 5, "periode": 5})
        assert r["amortissement"] == 600.0


# ═══════════════════════════════════════════════════════════════════════════════
# INGÉNIERIE & MATRICES
# ═══════════════════════════════════════════════════════════════════════════════

class TestTranspose:
    def test_2x3(self):
        r = formule_transpose({"matrice": [[1, 2, 3], [4, 5, 6]]})
        assert r["resultat"] == [[1.0, 4.0], [2.0, 5.0], [3.0, 6.0]]
        assert r["dimensions"] == "3x2"

    def test_1d(self):
        r = formule_transpose({"matrice": [1, 2, 3]})
        assert r["resultat"] == [[1.0], [2.0], [3.0]]

    def test_square(self):
        r = formule_transpose({"matrice": [[1, 2], [3, 4]]})
        assert r["resultat"] == [[1.0, 3.0], [2.0, 4.0]]


class TestProduitmat:
    def test_identity(self):
        """A * I = A."""
        a = [[1, 2], [3, 4]]
        identity = [[1, 0], [0, 1]]
        r = formule_produitmat({"matrice_a": a, "matrice_b": identity})
        assert r["resultat"] == [[1.0, 2.0], [3.0, 4.0]]

    def test_2x2_multiplication(self):
        a = [[1, 2], [3, 4]]
        b = [[5, 6], [7, 8]]
        r = formule_produitmat({"matrice_a": a, "matrice_b": b})
        # [1*5+2*7, 1*6+2*8] = [19, 22]
        # [3*5+4*7, 3*6+4*8] = [43, 50]
        assert r["resultat"] == [[19.0, 22.0], [43.0, 50.0]]

    def test_incompatible_dimensions(self):
        with pytest.raises(ValueError, match="incompatibles"):
            formule_produitmat({"matrice_a": [[1, 2]], "matrice_b": [[1, 2]]})


class TestMatriceInverse:
    def test_2x2(self):
        # Inverse of [[1,2],[3,4]] = [[-2, 1], [1.5, -0.5]]
        r = formule_matrice_inverse({"matrice": [[1, 2], [3, 4]]})
        inv = r["resultat"]
        assert abs(inv[0][0] - (-2.0)) < 1e-6
        assert abs(inv[0][1] - 1.0) < 1e-6
        assert abs(inv[1][0] - 1.5) < 1e-6
        assert abs(inv[1][1] - (-0.5)) < 1e-6

    def test_inverse_times_original_is_identity(self):
        """A^-1 * A = I."""
        m = [[2, 1], [5, 3]]
        inv_r = formule_matrice_inverse({"matrice": m})
        product = formule_produitmat({"matrice_a": inv_r["resultat"], "matrice_b": m})
        for i in range(2):
            for j in range(2):
                expected = 1.0 if i == j else 0.0
                assert abs(product["resultat"][i][j] - expected) < 1e-6

    def test_singular_matrix(self):
        with pytest.raises(ValueError, match="singulière"):
            formule_matrice_inverse({"matrice": [[1, 2], [2, 4]]})

    def test_non_square(self):
        with pytest.raises(ValueError, match="carrée"):
            formule_matrice_inverse({"matrice": [[1, 2, 3], [4, 5, 6]]})


class TestDeterminant:
    def test_2x2(self):
        # det([[1,2],[3,4]]) = 1*4 - 2*3 = -2
        r = formule_determinant({"matrice": [[1, 2], [3, 4]]})
        assert abs(r["determinant"] - (-2.0)) < 1e-6

    def test_3x3(self):
        # det([[1,2,3],[4,5,6],[7,8,0]]) = 1(0-48) - 2(0-42) + 3(32-35) = -48+84-9 = 27
        r = formule_determinant({"matrice": [[1, 2, 3], [4, 5, 6], [7, 8, 0]]})
        assert abs(r["determinant"] - 27.0) < 1e-6

    def test_identity_det_is_one(self):
        r = formule_determinant({"matrice": [[1, 0, 0], [0, 1, 0], [0, 0, 1]]})
        assert abs(r["determinant"] - 1.0) < 1e-6

    def test_singular_matrix_det_zero(self):
        r = formule_determinant({"matrice": [[1, 2], [2, 4]]})
        assert abs(r["determinant"]) < 1e-6


class TestFlatten:
    def test_nested(self):
        r = formule_flatten({"donnees": [[1, 2], [3, [4, 5]]]})
        assert r["resultat"] == [1, 2, 3, 4, 5]
        assert r["total"] == 5

    def test_already_flat(self):
        r = formule_flatten({"donnees": [1, 2, 3]})
        assert r["resultat"] == [1, 2, 3]

    def test_deeply_nested(self):
        r = formule_flatten({"donnees": [[[1]], [[2, [3]]]]})
        assert r["resultat"] == [1, 2, 3]


class TestByrow:
    def test_somme(self):
        r = formule_byrow({"matrice": [[1, 2, 3], [4, 5, 6]], "operation": "somme"})
        assert r["resultat"] == [6.0, 15.0]

    def test_max(self):
        r = formule_byrow({"matrice": [[10, 20], [5, 30]], "operation": "max"})
        assert r["resultat"] == [20.0, 30.0]

    def test_unknown_operation(self):
        with pytest.raises(ValueError, match="inconnue"):
            formule_byrow({"matrice": [[1, 2]], "operation": "invalid"})


class TestBycol:
    def test_somme(self):
        r = formule_bycol({"matrice": [[1, 2], [3, 4], [5, 6]], "operation": "somme"})
        assert r["resultat"] == [9.0, 12.0]

    def test_moyenne(self):
        r = formule_bycol({"matrice": [[10, 20], [30, 40]], "operation": "moyenne"})
        assert r["resultat"] == [20.0, 30.0]


class TestMakearray:
    def test_basic(self):
        r = formule_makearray({"lignes": 2, "colonnes": 3, "expression": "row * 3 + col + 1"})
        assert r["resultat"] == [[1, 2, 3], [4, 5, 6]]
        assert r["dimensions"] == "2x3"

    def test_size_limit(self):
        with pytest.raises(ValueError, match="trop grand"):
            formule_makearray({"lignes": 1000, "colonnes": 101, "expression": "1"})

    def test_unsafe_token(self):
        with pytest.raises(ValueError, match="non autorisé"):
            formule_makearray({"lignes": 2, "colonnes": 2, "expression": "__import__('os')"})


# ═══════════════════════════════════════════════════════════════════════════════
# STATISTIQUES DE DÉCISION
# ═══════════════════════════════════════════════════════════════════════════════

class TestCorrelation:
    def test_perfect_positive(self):
        r = formule_correlation({"x": [1, 2, 3, 4, 5], "y": [2, 4, 6, 8, 10]})
        assert abs(r["correlation"] - 1.0) < 1e-6
        assert abs(r["r_carre"] - 1.0) < 1e-6

    def test_perfect_negative(self):
        r = formule_correlation({"x": [1, 2, 3, 4, 5], "y": [10, 8, 6, 4, 2]})
        assert abs(r["correlation"] - (-1.0)) < 1e-6

    def test_no_correlation(self):
        r = formule_correlation({"x": [1, 2, 3, 4], "y": [1, -1, 1, -1]})
        assert abs(r["correlation"]) < 0.5

    def test_mismatched_lengths(self):
        with pytest.raises(ValueError, match="même taille"):
            formule_correlation({"x": [1, 2], "y": [1, 2, 3]})


class TestPente:
    def test_perfect_slope(self):
        # y = 2x, so slope = 2
        r = formule_pente({"x": [1, 2, 3, 4], "y": [2, 4, 6, 8]})
        assert abs(r["pente"] - 2.0) < 1e-6

    def test_negative_slope(self):
        r = formule_pente({"x": [1, 2, 3], "y": [6, 4, 2]})
        assert abs(r["pente"] - (-2.0)) < 1e-6


class TestOrdonneeOrigine:
    def test_basic(self):
        # y = 2x + 1
        r = formule_ordonnee_origine({"x": [0, 1, 2], "y": [1, 3, 5]})
        assert abs(r["ordonnee_origine"] - 1.0) < 1e-6

    def test_zero_intercept(self):
        # y = 3x
        r = formule_ordonnee_origine({"x": [1, 2, 3], "y": [3, 6, 9]})
        assert abs(r["ordonnee_origine"]) < 1e-6


class TestEcartTypeP:
    def test_population(self):
        # stdev.p([2,4,4,4,5,5,7,9]) = 2.0
        vals = [2, 4, 4, 4, 5, 5, 7, 9]
        r = formule_ecart_type_p({"valeurs": vals})
        assert abs(r["ecart_type"] - 2.0) < 1e-6
        assert r["n"] == 8

    def test_empty(self):
        with pytest.raises(ValueError, match="vide"):
            formule_ecart_type_p({"valeurs": []})


class TestEcartTypeS:
    def test_sample(self):
        # stdev.s([2,4,4,4,5,5,7,9]) = sqrt(32/7) ≈ 2.13809
        vals = [2, 4, 4, 4, 5, 5, 7, 9]
        r = formule_ecart_type_s({"valeurs": vals})
        expected = math.sqrt(32 / 7)
        assert abs(r["ecart_type"] - expected) < 1e-4
        assert r["n"] == 8

    def test_too_few(self):
        with pytest.raises(ValueError, match="Au moins 2"):
            formule_ecart_type_s({"valeurs": [42]})


class TestQuartile:
    def test_q1(self):
        vals = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        r = formule_quartile({"valeurs": vals, "quartile": 1})
        assert r["quartile"] == "Q1"
        assert r["valeur"] > 0

    def test_q2_is_median(self):
        vals = [1, 2, 3, 4, 5]
        r = formule_quartile({"valeurs": vals, "quartile": 2})
        assert abs(r["valeur"] - 3.0) < 1e-6

    def test_q0_is_min(self):
        vals = [5, 3, 1, 4, 2]
        r = formule_quartile({"valeurs": vals, "quartile": 0})
        assert abs(r["valeur"] - 1.0) < 1e-6

    def test_q4_is_max(self):
        vals = [5, 3, 1, 4, 2]
        r = formule_quartile({"valeurs": vals, "quartile": 4})
        assert abs(r["valeur"] - 5.0) < 1e-6


class TestPercentile:
    def test_50th(self):
        vals = [1, 2, 3, 4, 5]
        r = formule_percentile({"valeurs": vals, "k": 0.5})
        assert abs(r["valeur"] - 3.0) < 1e-6
        assert r["percentile"] == 50.0

    def test_0th(self):
        r = formule_percentile({"valeurs": [10, 20, 30], "k": 0})
        assert abs(r["valeur"] - 10.0) < 1e-6

    def test_100th(self):
        r = formule_percentile({"valeurs": [10, 20, 30], "k": 1})
        assert abs(r["valeur"] - 30.0) < 1e-6

    def test_invalid_k(self):
        with pytest.raises(ValueError, match="entre 0 et 1"):
            formule_percentile({"valeurs": [1, 2], "k": 1.5})


class TestMoyenneReduite:
    def test_basic(self):
        vals = [1, 2, 3, 4, 5, 6, 7, 8, 9, 100]
        r = formule_moyenne_reduite({"valeurs": vals, "pourcentage": 20})
        # Removes 10% from each end (1 value each): [2,3,4,5,6,7,8,9]
        expected = sum([2, 3, 4, 5, 6, 7, 8, 9]) / 8
        assert abs(r["moyenne_reduite"] - expected) < 1e-6
        assert r["valeurs_gardees"] == 8
        assert r["valeurs_eliminees"] == 2

    def test_zero_trim(self):
        vals = [1, 2, 3]
        r = formule_moyenne_reduite({"valeurs": vals, "pourcentage": 0})
        assert abs(r["moyenne_reduite"] - 2.0) < 1e-6


# ═══════════════════════════════════════════════════════════════════════════════
# TEXTE INDUSTRIEL
# ═══════════════════════════════════════════════════════════════════════════════

class TestRept:
    def test_basic(self):
        r = formule_rept({"texte": "abc", "nombre": 3})
        assert r["resultat"] == "abcabcabc"

    def test_zero(self):
        r = formule_rept({"texte": "x", "nombre": 0})
        assert r["resultat"] == ""

    def test_limit(self):
        with pytest.raises(ValueError, match="10 000"):
            formule_rept({"texte": "x", "nombre": 10001})


class TestCherche:
    def test_basic(self):
        r = formule_cherche({"texte_cherche": "world", "texte_source": "Hello World"})
        assert r["position"] == 7
        assert r["trouve"] is True

    def test_case_insensitive(self):
        r = formule_cherche({"texte_cherche": "HELLO", "texte_source": "hello world"})
        assert r["position"] == 1

    def test_not_found(self):
        with pytest.raises(ValueError, match="introuvable"):
            formule_cherche({"texte_cherche": "xyz", "texte_source": "hello"})

    def test_start_position(self):
        r = formule_cherche({"texte_cherche": "o", "texte_source": "hello world", "position_debut": 6})
        assert r["position"] == 8  # second 'o' in 'world'


class TestRemplacer:
    def test_basic(self):
        r = formule_remplacer({"texte": "Hello World", "position_debut": 7, "nb_caracteres": 5, "nouveau_texte": "Python"})
        assert r["resultat"] == "Hello Python"

    def test_insert(self):
        r = formule_remplacer({"texte": "AC", "position_debut": 2, "nb_caracteres": 0, "nouveau_texte": "B"})
        assert r["resultat"] == "ABC"


class TestTexteJoin:
    def test_basic(self):
        r = formule_texte_join({"textes": ["Hello", "World"], "delimiteur": " "})
        assert r["resultat"] == "Hello World"

    def test_ignore_empty(self):
        r = formule_texte_join({"textes": ["a", "", "b", None, "c"], "delimiteur": ",", "ignorer_vides": True})
        assert r["resultat"] == "a,b,c"

    def test_keep_empty(self):
        r = formule_texte_join({"textes": ["a", "", "b"], "delimiteur": "-", "ignorer_vides": False})
        assert r["resultat"] == "a--b"


class TestValeur:
    def test_simple_number(self):
        r = formule_valeur({"texte": "42.5"})
        assert r["nombre"] == 42.5

    def test_currency(self):
        r = formule_valeur({"texte": "1 250,50 €"})
        assert r["nombre"] == 1250.50

    def test_percentage(self):
        r = formule_valeur({"texte": "25%"})
        assert abs(r["nombre"] - 0.25) < 1e-8


class TestCtxt:
    def test_basic(self):
        r = formule_ctxt({"nombre": 1234.5678, "decimales": 2})
        assert r["resultat"] == "1,234.57"

    def test_no_separator(self):
        r = formule_ctxt({"nombre": 1234.5678, "decimales": 2, "pas_separateur": True})
        assert r["resultat"] == "1234.57"

    def test_zero_decimals(self):
        r = formule_ctxt({"nombre": 42.99, "decimales": 0})
        assert "43" in r["resultat"]


# ═══════════════════════════════════════════════════════════════════════════════
# D-FUNCTIONS (Fonctions de base de données)
# ═══════════════════════════════════════════════════════════════════════════════

DB_DATA = [
    {"nom": "Alice", "departement": "IT", "salaire": 50000},
    {"nom": "Bob", "departement": "IT", "salaire": 60000},
    {"nom": "Carol", "departement": "RH", "salaire": 45000},
    {"nom": "David", "departement": "IT", "salaire": 55000},
    {"nom": "Eve", "departement": "RH", "salaire": 48000},
]


class TestBdsomme:
    def test_sum_it(self):
        r = formule_bdsomme({
            "donnees": DB_DATA, "champ": "salaire",
            "criteres": [{"colonne": "departement", "valeur": "IT"}]
        })
        assert r["somme"] == 165000.0
        assert r["lignes"] == 3

    def test_no_match(self):
        r = formule_bdsomme({
            "donnees": DB_DATA, "champ": "salaire",
            "criteres": [{"colonne": "departement", "valeur": "Finance"}]
        })
        assert r["somme"] == 0.0
        assert r["lignes"] == 0


class TestBdnb:
    def test_count_rh(self):
        r = formule_bdnb({
            "donnees": DB_DATA, "champ": "salaire",
            "criteres": [{"colonne": "departement", "valeur": "RH"}]
        })
        assert r["count"] == 2


class TestBdmax:
    def test_max_it(self):
        r = formule_bdmax({
            "donnees": DB_DATA, "champ": "salaire",
            "criteres": [{"colonne": "departement", "valeur": "IT"}]
        })
        assert r["max"] == 60000.0

    def test_no_match(self):
        with pytest.raises(ValueError, match="Aucune donnée"):
            formule_bdmax({
                "donnees": DB_DATA, "champ": "salaire",
                "criteres": [{"colonne": "departement", "valeur": "X"}]
            })


class TestBdmin:
    def test_min_it(self):
        r = formule_bdmin({
            "donnees": DB_DATA, "champ": "salaire",
            "criteres": [{"colonne": "departement", "valeur": "IT"}]
        })
        assert r["min"] == 50000.0


class TestBdmoyenne:
    def test_avg_rh(self):
        r = formule_bdmoyenne({
            "donnees": DB_DATA, "champ": "salaire",
            "criteres": [{"colonne": "departement", "valeur": "RH"}]
        })
        assert abs(r["moyenne"] - 46500.0) < 1e-6
        assert r["lignes"] == 2


# ═══════════════════════════════════════════════════════════════════════════════
# MANIPULATION AVANCÉE
# ═══════════════════════════════════════════════════════════════════════════════

class TestLambdaRecursive:
    def test_doubling(self):
        r = formule_lambda_recursive({"expression": "x * 2", "valeur_initiale": 1, "iterations": 5})
        assert r["resultat_final"] == 32  # 1 -> 2 -> 4 -> 8 -> 16 -> 32

    def test_sqrt_convergence(self):
        r = formule_lambda_recursive({"expression": "sqrt(x)", "valeur_initiale": 256, "iterations": 10})
        assert abs(r["resultat_final"] - 1.0) < 0.01

    def test_unsafe_token(self):
        with pytest.raises(ValueError, match="non autorisé"):
            formule_lambda_recursive({"expression": "os.system('rm')", "valeur_initiale": 1, "iterations": 1})

    def test_iteration_limit(self):
        with pytest.raises(ValueError, match="entre 1 et 1 000"):
            formule_lambda_recursive({"expression": "x + 1", "valeur_initiale": 0, "iterations": 1001})


class TestLetAdvanced:
    def test_basic(self):
        r = formule_let_advanced({
            "variables": {"a": 10, "b": 20},
            "etapes": [{"nom": "c", "expression": "a + b"}],
            "expression_finale": "c * 2"
        })
        assert r["resultat"] == 60.0

    def test_chained_steps(self):
        r = formule_let_advanced({
            "variables": {"x": 5},
            "etapes": [
                {"nom": "y", "expression": "x * x"},
                {"nom": "z", "expression": "y + x"},
            ],
            "expression_finale": "z"
        })
        assert r["resultat"] == 30.0  # 25 + 5

    def test_unsafe_token(self):
        with pytest.raises(ValueError, match="non autorisé"):
            formule_let_advanced({
                "variables": {"a": 1},
                "etapes": [],
                "expression_finale": "open('file')"
            })


class TestChoose:
    def test_basic(self):
        r = formule_choose({"index": 2, "valeurs": ["a", "b", "c"]})
        assert r["resultat"] == "b"
        assert r["index"] == 2

    def test_first(self):
        r = formule_choose({"index": 1, "valeurs": [10, 20, 30]})
        assert r["resultat"] == 10

    def test_out_of_range(self):
        with pytest.raises(ValueError, match="hors limites"):
            formule_choose({"index": 5, "valeurs": [1, 2, 3]})

    def test_zero_index(self):
        with pytest.raises(ValueError, match="hors limites"):
            formule_choose({"index": 0, "valeurs": [1, 2]})


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITAIRES DATA
# ═══════════════════════════════════════════════════════════════════════════════

class TestEsterreur:
    def test_errors_detected(self):
        r = formule_esterreur({"valeurs": [1, "#N/A", "hello", "#DIV/0!", 42]})
        assert r["resultats"] == [False, True, False, True, False]
        assert r["nb_erreurs"] == 2

    def test_no_errors(self):
        r = formule_esterreur({"valeurs": [1, 2, 3]})
        assert r["nb_erreurs"] == 0

    def test_null_is_error(self):
        r = formule_esterreur({"valeurs": [None]})
        assert r["resultats"] == [True]


class TestEstna:
    def test_na_detected(self):
        r = formule_estna({"valeurs": [1, "#N/A", "hello", None]})
        assert r["resultats"] == [False, True, False, True]
        assert r["nb_na"] == 2

    def test_no_na(self):
        r = formule_estna({"valeurs": [1, 2, "text"]})
        assert r["nb_na"] == 0


class TestTypeVal:
    def test_number(self):
        r = formule_type_val({"valeur": 42})
        assert r["type"] == 1
        assert r["type_nom"] == "Nombre"

    def test_text(self):
        r = formule_type_val({"valeur": "hello"})
        assert r["type"] == 2
        assert r["type_nom"] == "Texte"

    def test_boolean(self):
        r = formule_type_val({"valeur": True})
        assert r["type"] == 4
        assert r["type_nom"] == "Booléen"

    def test_error(self):
        r = formule_type_val({"valeur": "#N/A"})
        assert r["type"] == 16
        assert r["type_nom"] == "Erreur"

    def test_array(self):
        r = formule_type_val({"valeur": [1, 2, 3]})
        assert r["type"] == 64
        assert r["type_nom"] == "Tableau"

    def test_null(self):
        r = formule_type_val({"valeur": None})
        assert r["type"] == 1  # null traité comme 0


class TestCoordonnees:
    def test_absolute(self):
        r = formule_coordonnees({"ligne": 1, "colonne": 1})
        assert r["adresse"] == "$A$1"

    def test_column_z(self):
        r = formule_coordonnees({"ligne": 5, "colonne": 26})
        assert r["adresse"] == "$Z$5"

    def test_column_aa(self):
        r = formule_coordonnees({"ligne": 1, "colonne": 27})
        assert r["adresse"] == "$AA$1"

    def test_relative(self):
        r = formule_coordonnees({"ligne": 3, "colonne": 2, "type_reference": 4})
        assert r["adresse"] == "B3"

    def test_mixed_row_abs(self):
        r = formule_coordonnees({"ligne": 3, "colonne": 2, "type_reference": 2})
        assert r["adresse"] == "B$3"


class TestIndirectExt:
    def test_dict_navigation(self):
        data = {"users": {"admin": {"name": "Alice"}}}
        r = formule_indirect_ext({"reference": "users.admin.name", "donnees": data})
        assert r["resultat"] == "Alice"

    def test_list_index(self):
        data = {"items": [10, 20, 30]}
        r = formule_indirect_ext({"reference": "items[1]", "donnees": data})
        assert r["resultat"] == 20

    def test_invalid_key(self):
        with pytest.raises(ValueError, match="introuvable"):
            formule_indirect_ext({"reference": "foo.bar", "donnees": {"foo": {"baz": 1}}})


class TestNbcar:
    def test_basic(self):
        assert formule_nbcar({"texte": "Hello"})["longueur"] == 5

    def test_empty(self):
        assert formule_nbcar({"texte": ""})["longueur"] == 0

    def test_unicode(self):
        assert formule_nbcar({"texte": "café"})["longueur"] == 4


class TestMajuscule:
    def test_basic(self):
        assert formule_majuscule({"texte": "hello"})["resultat"] == "HELLO"


class TestMinuscule:
    def test_basic(self):
        assert formule_minuscule({"texte": "HELLO"})["resultat"] == "hello"


class TestCnum:
    def test_number(self):
        assert formule_cnum({"valeur": 42})["nombre"] == 42.0

    def test_bool_true(self):
        assert formule_cnum({"valeur": True})["nombre"] == 1

    def test_bool_false(self):
        assert formule_cnum({"valeur": False})["nombre"] == 0

    def test_text_returns_zero(self):
        assert formule_cnum({"valeur": "abc"})["nombre"] == 0


class TestAbsVal:
    def test_positive(self):
        assert formule_abs_val({"nombre": 5})["resultat"] == 5.0

    def test_negative(self):
        assert formule_abs_val({"nombre": -7.3})["resultat"] == 7.3

    def test_zero(self):
        assert formule_abs_val({"nombre": 0})["resultat"] == 0.0


class TestMod:
    def test_basic(self):
        assert formule_mod({"nombre": 10, "diviseur": 3})["resultat"] == 1.0

    def test_decimal(self):
        r = formule_mod({"nombre": 7.5, "diviseur": 2.5})
        assert abs(r["resultat"]) < 1e-6  # 7.5 % 2.5 = 0

    def test_division_by_zero(self):
        with pytest.raises(ValueError, match="zéro"):
            formule_mod({"nombre": 5, "diviseur": 0})


class TestPuissance:
    def test_basic(self):
        assert formule_puissance({"base": 2, "exposant": 10})["resultat"] == 1024.0

    def test_square_root(self):
        assert abs(formule_puissance({"base": 9, "exposant": 0.5})["resultat"] - 3.0) < 1e-6

    def test_zero_exponent(self):
        assert formule_puissance({"base": 42, "exposant": 0})["resultat"] == 1.0


class TestPlafondPlancher:
    def test_basic(self):
        r = formule_plafond_plancher({"nombre": 4.3, "increment": 1})
        assert r["plafond"] == 5.0
        assert r["plancher"] == 4.0

    def test_custom_increment(self):
        r = formule_plafond_plancher({"nombre": 4.3, "increment": 0.5})
        assert r["plafond"] == 4.5
        assert r["plancher"] == 4.0

    def test_negative(self):
        r = formule_plafond_plancher({"nombre": -4.3, "increment": 1})
        assert r["plafond"] == -4.0
        assert r["plancher"] == -5.0

    def test_zero_increment(self):
        with pytest.raises(ValueError, match="ne peut pas être 0"):
            formule_plafond_plancher({"nombre": 5, "increment": 0})
