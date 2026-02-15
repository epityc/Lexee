"""
Moteur de calcul protégé — les formules ne sont jamais exposées à l'utilisateur.
Chaque fonction reçoit un dict de variables et renvoie un dict de résultats.
"""

from __future__ import annotations


def calcul_rentabilite_immobiliere(variables: dict) -> dict:
    """Simule une formule Excel complexe de rentabilité immobilière.

    Variables attendues:
        prix_achat          – Prix d'achat du bien (€)
        frais_notaire_pct   – Frais de notaire (%, ex: 7.5)
        cout_travaux        – Coût des travaux (€)
        loyer_mensuel       – Loyer mensuel brut (€)
        charges_annuelles   – Charges annuelles (taxe foncière, copro, assurance…) (€)
        vacance_pct         – Taux de vacance locative (%, ex: 5)
        duree_emprunt       – Durée de l'emprunt (années)
        taux_interet        – Taux d'intérêt annuel (%, ex: 3.5)
        apport              – Apport personnel (€)
    """

    # --- Extraction des variables -----------------------------------------------
    prix_achat = float(variables["prix_achat"])
    frais_notaire_pct = float(variables.get("frais_notaire_pct", 7.5))
    cout_travaux = float(variables.get("cout_travaux", 0))
    loyer_mensuel = float(variables["loyer_mensuel"])
    charges_annuelles = float(variables.get("charges_annuelles", 0))
    vacance_pct = float(variables.get("vacance_pct", 5))
    duree_emprunt = int(variables.get("duree_emprunt", 20))
    taux_interet = float(variables.get("taux_interet", 3.5))
    apport = float(variables.get("apport", 0))

    # --- Coût total d'acquisition -----------------------------------------------
    frais_notaire = prix_achat * (frais_notaire_pct / 100)
    cout_total = prix_achat + frais_notaire + cout_travaux

    # --- Revenus locatifs ajustés -----------------------------------------------
    loyer_annuel_brut = loyer_mensuel * 12
    perte_vacance = loyer_annuel_brut * (vacance_pct / 100)
    loyer_annuel_net = loyer_annuel_brut - perte_vacance - charges_annuelles

    # --- Rendements -------------------------------------------------------------
    rendement_brut = (loyer_annuel_brut / cout_total) * 100
    rendement_net = (loyer_annuel_net / cout_total) * 100

    # --- Mensualité d'emprunt (formule d'annuité constante) ---------------------
    montant_emprunte = cout_total - apport
    if montant_emprunte > 0 and taux_interet > 0:
        taux_mensuel = (taux_interet / 100) / 12
        nb_mensualites = duree_emprunt * 12
        mensualite = montant_emprunte * (
            taux_mensuel / (1 - (1 + taux_mensuel) ** -nb_mensualites)
        )
    elif montant_emprunte > 0:
        mensualite = montant_emprunte / (duree_emprunt * 12)
    else:
        mensualite = 0.0

    cout_total_credit = mensualite * duree_emprunt * 12

    # --- Cash-flow mensuel ------------------------------------------------------
    cash_flow_mensuel = (loyer_annuel_net / 12) - mensualite

    # --- Résultat ---------------------------------------------------------------
    return {
        "cout_total_acquisition": round(cout_total, 2),
        "loyer_annuel_brut": round(loyer_annuel_brut, 2),
        "loyer_annuel_net": round(loyer_annuel_net, 2),
        "rendement_brut_pct": round(rendement_brut, 2),
        "rendement_net_pct": round(rendement_net, 2),
        "mensualite_emprunt": round(mensualite, 2),
        "cout_total_credit": round(cout_total_credit, 2),
        "cash_flow_mensuel": round(cash_flow_mensuel, 2),
        "montant_emprunte": round(montant_emprunte, 2),
    }


# ---------------------------------------------------------------------------
# Registre des formules disponibles.
# Pour ajouter une nouvelle formule, il suffit de créer la fonction ci-dessus
# puis de l'enregistrer ici.
# ---------------------------------------------------------------------------
FORMULAS: dict[str, callable] = {
    "rentabilite_immobiliere": calcul_rentabilite_immobiliere,
}
