"""
Moteur de calcul protégé — les formules ne sont jamais exposées à l'utilisateur.
Chaque fonction reçoit un dict de variables et renvoie un dict de résultats.

IMPORTANT : ce fichier est le cœur de la propriété intellectuelle.
Ne jamais exposer le code source via l'API.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta


# ═══════════════════════════════════════════════════════════════════════════════
# 1. SOMME & MOYENNE (SUM & AVERAGE)
# ═══════════════════════════════════════════════════════════════════════════════
def formule_somme_moyenne(v: dict) -> dict:
    valeurs = [float(x) for x in v["valeurs"]]
    n = len(valeurs)
    if n == 0:
        raise ValueError("La liste de valeurs est vide.")
    return {
        "somme": round(sum(valeurs), 6),
        "moyenne": round(sum(valeurs) / n, 6),
        "count": n,
        "min": round(min(valeurs), 6),
        "max": round(max(valeurs), 6),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 2. SI / SI.ENS (IF / IFS)
# ═══════════════════════════════════════════════════════════════════════════════
_OPS = {
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    ">":  lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "<":  lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
}


def formule_si(v: dict) -> dict:
    valeur = float(v["valeur"])
    conditions = v["conditions"]  # [{"operateur":">=","seuil":90,"resultat":"A"},…]
    defaut = v.get("defaut", "Néant")

    for cond in conditions:
        op_fn = _OPS.get(cond["operateur"])
        if op_fn is None:
            raise ValueError(f"Opérateur inconnu : {cond['operateur']}")
        if op_fn(valeur, float(cond["seuil"])):
            return {"resultat": cond["resultat"], "condition_matchee": cond}

    return {"resultat": defaut, "condition_matchee": None}


# ═══════════════════════════════════════════════════════════════════════════════
# 3. RECHERCHEX (XLOOKUP)
# ═══════════════════════════════════════════════════════════════════════════════
def formule_recherchex(v: dict) -> dict:
    valeur_cherchee = v["valeur_cherchee"]
    tableau_recherche = v["tableau_recherche"]
    tableau_retour = v["tableau_retour"]

    if len(tableau_recherche) != len(tableau_retour):
        raise ValueError("Les tableaux de recherche et de retour doivent avoir la même taille.")

    # Recherche exacte (insensible à la casse pour les chaînes)
    needle = str(valeur_cherchee).lower()
    for i, item in enumerate(tableau_recherche):
        if str(item).lower() == needle:
            return {"resultat": tableau_retour[i], "position": i + 1, "trouve": True}

    return {"resultat": None, "position": -1, "trouve": False}


# ═══════════════════════════════════════════════════════════════════════════════
# 4. SOMME.SI.ENS (SUMIFS)
# ═══════════════════════════════════════════════════════════════════════════════
def _match_row(row: dict, criteres: list[dict]) -> bool:
    for c in criteres:
        col = c["colonne"]
        expected = str(c["valeur"]).lower()
        actual = str(row.get(col, "")).lower()
        if actual != expected:
            return False
    return True


def formule_somme_si_ens(v: dict) -> dict:
    donnees = v["donnees"]  # [{"canal":"Facebook","ville":"Paris","montant":150},…]
    colonne_somme = v["colonne_somme"]
    criteres = v["criteres"]  # [{"colonne":"canal","valeur":"Facebook"},…]

    total = 0.0
    lignes_ok = 0
    for row in donnees:
        if _match_row(row, criteres):
            total += float(row.get(colonne_somme, 0))
            lignes_ok += 1

    return {
        "somme": round(total, 6),
        "lignes_correspondantes": lignes_ok,
        "lignes_totales": len(donnees),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 5. NB.SI.ENS (COUNTIFS)
# ═══════════════════════════════════════════════════════════════════════════════
def formule_nb_si_ens(v: dict) -> dict:
    donnees = v["donnees"]
    criteres = v["criteres"]

    count = sum(1 for row in donnees if _match_row(row, criteres))

    return {
        "count": count,
        "lignes_totales": len(donnees),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 6. CONCAT / JOINDRE.TEXTE (CONCAT / TEXTJOIN)
# ═══════════════════════════════════════════════════════════════════════════════
def formule_concat(v: dict) -> dict:
    textes = [str(t) for t in v["textes"]]
    separateur = str(v.get("separateur", ""))
    ignorer_vides = v.get("ignorer_vides", True)

    if ignorer_vides:
        textes = [t for t in textes if t.strip()]

    return {"resultat": separateur.join(textes)}


# ═══════════════════════════════════════════════════════════════════════════════
# 7. GAUCHE / DROITE / STXT (LEFT / RIGHT / MID)
# ═══════════════════════════════════════════════════════════════════════════════
def formule_extraction_texte(v: dict) -> dict:
    texte = str(v["texte"])
    nb_gauche = int(v.get("nb_gauche", 3))
    nb_droite = int(v.get("nb_droite", 3))
    position_milieu = int(v.get("position_milieu", 1)) - 1  # 1-indexed comme Excel
    nb_milieu = int(v.get("nb_milieu", 3))

    return {
        "gauche": texte[:nb_gauche],
        "droite": texte[-nb_droite:] if nb_droite > 0 else "",
        "milieu": texte[position_milieu:position_milieu + nb_milieu],
        "longueur_totale": len(texte),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 8. AUJOURDHUI & NB.JOURS.OUVRES (TODAY & NETWORKDAYS)
# ═══════════════════════════════════════════════════════════════════════════════
def _parse_date(s: str) -> date:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Format de date non reconnu : {s}. Utilisez YYYY-MM-DD ou DD/MM/YYYY.")


def _networkdays(start: date, end: date) -> int:
    if start > end:
        start, end = end, start
    count = 0
    current = start
    while current <= end:
        if current.weekday() < 5:  # Lundi=0 … Vendredi=4
            count += 1
        current += timedelta(days=1)
    return count


def formule_dates_ouvrees(v: dict) -> dict:
    aujourdhui = date.today()
    date_debut = _parse_date(v["date_debut"])
    date_fin = _parse_date(v["date_fin"])

    jours_calendaires = abs((date_fin - date_debut).days)
    jours_ouvres = _networkdays(date_debut, date_fin)

    return {
        "aujourdhui": aujourdhui.isoformat(),
        "date_debut": date_debut.isoformat(),
        "date_fin": date_fin.isoformat(),
        "jours_calendaires": jours_calendaires,
        "jours_ouvres": jours_ouvres,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 9. UNIQUE
# ═══════════════════════════════════════════════════════════════════════════════
def formule_unique(v: dict) -> dict:
    valeurs = v["valeurs"]
    seen = set()
    uniques = []
    for item in valeurs:
        key = str(item).lower().strip()
        if key not in seen:
            seen.add(key)
            uniques.append(item)

    return {
        "valeurs_uniques": uniques,
        "total_initial": len(valeurs),
        "doublons_supprimes": len(valeurs) - len(uniques),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 10. FILTRE (FILTER)
# ═══════════════════════════════════════════════════════════════════════════════
def formule_filtre(v: dict) -> dict:
    donnees = v["donnees"]  # [{...}, ...]
    criteres = v["criteres"]  # [{"colonne":"status","valeur":"actif"},…]

    resultats = [row for row in donnees if _match_row(row, criteres)]

    return {
        "resultats": resultats,
        "lignes_filtrees": len(resultats),
        "lignes_totales": len(donnees),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 11. RENTABILITÉ IMMOBILIÈRE (formule avancée existante)
# ═══════════════════════════════════════════════════════════════════════════════
def formule_rentabilite_immobiliere(v: dict) -> dict:
    prix_achat = float(v["prix_achat"])
    frais_notaire_pct = float(v.get("frais_notaire_pct", 7.5))
    cout_travaux = float(v.get("cout_travaux", 0))
    loyer_mensuel = float(v["loyer_mensuel"])
    charges_annuelles = float(v.get("charges_annuelles", 0))
    vacance_pct = float(v.get("vacance_pct", 5))
    duree_emprunt = int(v.get("duree_emprunt", 20))
    taux_interet = float(v.get("taux_interet", 3.5))
    apport = float(v.get("apport", 0))

    frais_notaire = prix_achat * (frais_notaire_pct / 100)
    cout_total = prix_achat + frais_notaire + cout_travaux

    loyer_annuel_brut = loyer_mensuel * 12
    perte_vacance = loyer_annuel_brut * (vacance_pct / 100)
    loyer_annuel_net = loyer_annuel_brut - perte_vacance - charges_annuelles

    rendement_brut = (loyer_annuel_brut / cout_total) * 100
    rendement_net = (loyer_annuel_net / cout_total) * 100

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
    cash_flow_mensuel = (loyer_annuel_net / 12) - mensualite

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


# ═══════════════════════════════════════════════════════════════════════════════
# REGISTRE DES FORMULES (clé → fonction)
# ═══════════════════════════════════════════════════════════════════════════════
FORMULAS: dict[str, callable] = {
    "somme_moyenne": formule_somme_moyenne,
    "si": formule_si,
    "recherchex": formule_recherchex,
    "somme_si_ens": formule_somme_si_ens,
    "nb_si_ens": formule_nb_si_ens,
    "concat": formule_concat,
    "extraction_texte": formule_extraction_texte,
    "dates_ouvrees": formule_dates_ouvrees,
    "unique": formule_unique,
    "filtre": formule_filtre,
    "rentabilite_immobiliere": formule_rentabilite_immobiliere,
}


# ═══════════════════════════════════════════════════════════════════════════════
# MÉTADONNÉES — exposées au frontend pour construire la grille dynamiquement.
# Seuls les noms de variables sont visibles, JAMAIS le code des formules.
# ═══════════════════════════════════════════════════════════════════════════════
FORMULA_META: dict[str, dict] = {
    "somme_moyenne": {
        "name": "SOMME & MOYENNE",
        "description": "Somme, moyenne, min et max d'une série de valeurs",
        "category": "Mathématiques",
        "variables": [
            {"name": "valeurs", "label": "Valeurs", "type": "number[]",
             "required": True, "placeholder": "10, 20, 30, 40, 50"},
        ],
    },
    "si": {
        "name": "SI / SI.ENS",
        "description": "Évaluation conditionnelle : SI condition ALORS résultat",
        "category": "Logique",
        "variables": [
            {"name": "valeur", "label": "Valeur à tester", "type": "number",
             "required": True, "placeholder": "85"},
            {"name": "conditions", "label": "Conditions (JSON)", "type": "json",
             "required": True,
             "placeholder": '[{"operateur":">=","seuil":90,"resultat":"Excellent"},{"operateur":">=","seuil":70,"resultat":"Bien"}]'},
            {"name": "defaut", "label": "Valeur par défaut", "type": "string",
             "required": False, "placeholder": "Insuffisant"},
        ],
    },
    "recherchex": {
        "name": "RECHERCHEX",
        "description": "Rechercher une valeur et retourner le résultat correspondant",
        "category": "Recherche",
        "variables": [
            {"name": "valeur_cherchee", "label": "Valeur cherchée", "type": "string",
             "required": True, "placeholder": "REF-003"},
            {"name": "tableau_recherche", "label": "Tableau de recherche", "type": "string[]",
             "required": True, "placeholder": "REF-001, REF-002, REF-003"},
            {"name": "tableau_retour", "label": "Tableau de retour", "type": "string[]",
             "required": True, "placeholder": "10.50, 20.00, 35.99"},
        ],
    },
    "somme_si_ens": {
        "name": "SOMME.SI.ENS",
        "description": "Somme conditionnelle sur plusieurs critères",
        "category": "Mathématiques",
        "variables": [
            {"name": "donnees", "label": "Données (table JSON)", "type": "json",
             "required": True,
             "placeholder": '[{"canal":"Facebook","ville":"Paris","montant":150}]'},
            {"name": "colonne_somme", "label": "Colonne à sommer", "type": "string",
             "required": True, "placeholder": "montant"},
            {"name": "criteres", "label": "Critères (JSON)", "type": "json",
             "required": True,
             "placeholder": '[{"colonne":"canal","valeur":"Facebook"}]'},
        ],
    },
    "nb_si_ens": {
        "name": "NB.SI.ENS",
        "description": "Compter les lignes répondant à plusieurs critères",
        "category": "Statistiques",
        "variables": [
            {"name": "donnees", "label": "Données (table JSON)", "type": "json",
             "required": True,
             "placeholder": '[{"client":"A","achats":5},{"client":"B","achats":2}]'},
            {"name": "criteres", "label": "Critères (JSON)", "type": "json",
             "required": True,
             "placeholder": '[{"colonne":"achats","valeur":"5"}]'},
        ],
    },
    "concat": {
        "name": "CONCAT / JOINDRE.TEXTE",
        "description": "Fusionner plusieurs textes avec un séparateur",
        "category": "Texte",
        "variables": [
            {"name": "textes", "label": "Textes à fusionner", "type": "string[]",
             "required": True, "placeholder": "Jean, Dupont"},
            {"name": "separateur", "label": "Séparateur", "type": "string",
             "required": False, "placeholder": " "},
            {"name": "ignorer_vides", "label": "Ignorer les vides (true/false)", "type": "string",
             "required": False, "placeholder": "true"},
        ],
    },
    "extraction_texte": {
        "name": "GAUCHE / DROITE / STXT",
        "description": "Extraire une partie d'un texte (gauche, droite, milieu)",
        "category": "Texte",
        "variables": [
            {"name": "texte", "label": "Texte source", "type": "string",
             "required": True, "placeholder": "CLIENT-2024-XK9284"},
            {"name": "nb_gauche", "label": "Nb caractères (gauche)", "type": "number",
             "required": False, "placeholder": "6"},
            {"name": "nb_droite", "label": "Nb caractères (droite)", "type": "number",
             "required": False, "placeholder": "6"},
            {"name": "position_milieu", "label": "Position début (milieu)", "type": "number",
             "required": False, "placeholder": "8"},
            {"name": "nb_milieu", "label": "Nb caractères (milieu)", "type": "number",
             "required": False, "placeholder": "4"},
        ],
    },
    "dates_ouvrees": {
        "name": "AUJOURDHUI & JOURS OUVRÉS",
        "description": "Calcul de jours ouvrés entre deux dates",
        "category": "Dates",
        "variables": [
            {"name": "date_debut", "label": "Date de début", "type": "string",
             "required": True, "placeholder": "2025-01-15"},
            {"name": "date_fin", "label": "Date de fin", "type": "string",
             "required": True, "placeholder": "2025-02-15"},
        ],
    },
    "unique": {
        "name": "UNIQUE",
        "description": "Extraire les valeurs uniques (suppression des doublons)",
        "category": "Données",
        "variables": [
            {"name": "valeurs", "label": "Valeurs", "type": "string[]",
             "required": True,
             "placeholder": "alice@mail.com, bob@mail.com, alice@mail.com, carol@mail.com"},
        ],
    },
    "filtre": {
        "name": "FILTRE",
        "description": "Filtrer un tableau selon des critères",
        "category": "Données",
        "variables": [
            {"name": "donnees", "label": "Données (table JSON)", "type": "json",
             "required": True,
             "placeholder": '[{"nom":"Alice","status":"actif"},{"nom":"Bob","status":"inactif"}]'},
            {"name": "criteres", "label": "Critères (JSON)", "type": "json",
             "required": True,
             "placeholder": '[{"colonne":"status","valeur":"actif"}]'},
        ],
    },
    "rentabilite_immobiliere": {
        "name": "Rentabilité Immobilière",
        "description": "Analyse complète de rentabilité d'un investissement locatif",
        "category": "Finance",
        "variables": [
            {"name": "prix_achat", "label": "Prix d'achat (€)", "type": "number",
             "required": True, "placeholder": "200000"},
            {"name": "loyer_mensuel", "label": "Loyer mensuel (€)", "type": "number",
             "required": True, "placeholder": "900"},
            {"name": "frais_notaire_pct", "label": "Frais de notaire (%)", "type": "number",
             "required": False, "placeholder": "7.5"},
            {"name": "cout_travaux", "label": "Coût travaux (€)", "type": "number",
             "required": False, "placeholder": "15000"},
            {"name": "charges_annuelles", "label": "Charges annuelles (€)", "type": "number",
             "required": False, "placeholder": "2500"},
            {"name": "vacance_pct", "label": "Vacance locative (%)", "type": "number",
             "required": False, "placeholder": "5"},
            {"name": "duree_emprunt", "label": "Durée emprunt (années)", "type": "number",
             "required": False, "placeholder": "20"},
            {"name": "taux_interet", "label": "Taux d'intérêt (%)", "type": "number",
             "required": False, "placeholder": "3.5"},
            {"name": "apport", "label": "Apport personnel (€)", "type": "number",
             "required": False, "placeholder": "30000"},
        ],
    },
}
