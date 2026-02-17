"""
Moteur de calcul protégé — les formules ne sont jamais exposées à l'utilisateur.
Chaque fonction reçoit un dict de variables et renvoie un dict de résultats.

IMPORTANT : ce fichier est le cœur de la propriété intellectuelle.
Ne jamais exposer le code source via l'API.
"""

from __future__ import annotations

import calendar
import re
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


# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║                    ENGINE v2 — 20 NOUVELLES FORMULES                        ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝

# ─────────────────────────────────────────────────────────────────────────────
# NETTOYAGE DE TEXTE
# ─────────────────────────────────────────────────────────────────────────────

# 12. SUPPRESPACE (TRIM)
def formule_supprespace(v: dict) -> dict:
    texte = str(v["texte"])
    resultat = " ".join(texte.split())
    return {
        "resultat": resultat,
        "espaces_supprimes": len(texte) - len(resultat),
    }


# 13. SUBSTITUE (SUBSTITUTE)
def formule_substitue(v: dict) -> dict:
    texte = str(v["texte"])
    ancien = str(v["ancien"])
    nouveau = str(v["nouveau"])
    occurrence = v.get("occurrence")  # None = toutes

    if occurrence is not None:
        occurrence = int(occurrence)
        count = 0
        pos = 0
        while True:
            idx = texte.find(ancien, pos)
            if idx == -1:
                break
            count += 1
            if count == occurrence:
                resultat = texte[:idx] + nouveau + texte[idx + len(ancien):]
                return {"resultat": resultat, "remplacements": 1}
            pos = idx + 1
        return {"resultat": texte, "remplacements": 0}

    nb = texte.count(ancien)
    return {"resultat": texte.replace(ancien, nouveau), "remplacements": nb}


# 14. TEXTE.AVANT / TEXTE.APRES (TEXTBEFORE / TEXTAFTER)
def formule_texte_avant_apres(v: dict) -> dict:
    texte = str(v["texte"])
    delimiteur = str(v["delimiteur"])
    n = int(v.get("occurrence", 1))

    # TEXTBEFORE : texte avant la n-ième occurrence
    avant = texte
    pos = 0
    for _ in range(n):
        idx = texte.find(delimiteur, pos)
        if idx == -1:
            avant = texte
            break
        avant = texte[:idx]
        pos = idx + len(delimiteur)

    # TEXTAFTER : texte après la n-ième occurrence
    apres = texte
    pos = 0
    for _ in range(n):
        idx = texte.find(delimiteur, pos)
        if idx == -1:
            apres = ""
            break
        apres = texte[idx + len(delimiteur):]
        pos = idx + len(delimiteur)

    return {"avant": avant, "apres": apres}


# 15. NOMPROPRE (PROPER)
def formule_nompropre(v: dict) -> dict:
    texte = str(v["texte"])
    resultat = texte.title()
    return {"resultat": resultat}


# ─────────────────────────────────────────────────────────────────────────────
# FINANCE
# ─────────────────────────────────────────────────────────────────────────────

# 16. VPM (PMT) — Mensualité d'un prêt
def formule_vpm(v: dict) -> dict:
    taux_annuel = float(v["taux_annuel"])  # ex: 5 pour 5 %
    nb_periodes = int(v["nb_periodes"])    # nombre total de mensualités
    valeur_actuelle = float(v["valeur_actuelle"])  # montant emprunté (positif)
    valeur_future = float(v.get("valeur_future", 0))
    debut_periode = int(v.get("debut_periode", 0))  # 0=fin, 1=début

    if nb_periodes <= 0:
        raise ValueError("nb_periodes doit être > 0.")

    taux = (taux_annuel / 100) / 12

    if taux == 0:
        pmt = -(valeur_actuelle + valeur_future) / nb_periodes
    else:
        factor = (1 + taux) ** nb_periodes
        pmt = -(valeur_actuelle * factor + valeur_future) * taux / (
            (factor - 1) * (1 + taux * debut_periode)
        )

    cout_total = pmt * nb_periodes
    total_interets = cout_total + valeur_actuelle + valeur_future

    return {
        "mensualite": round(pmt, 2),
        "cout_total": round(abs(cout_total), 2),
        "total_interets": round(abs(total_interets), 2),
    }


# 17. VAN (NPV) — Valeur Actuelle Nette
def formule_van(v: dict) -> dict:
    taux = float(v["taux"]) / 100  # ex: 10 pour 10 %
    flux = [float(f) for f in v["flux"]]  # [CF1, CF2, CF3, …]

    if taux <= -1:
        raise ValueError("Le taux doit être > -100 %.")

    npv = sum(cf / (1 + taux) ** (i + 1) for i, cf in enumerate(flux))

    return {"van": round(npv, 2)}


# 18. TRI (IRR) — Taux de Rendement Interne (méthode de Newton)
def formule_tri(v: dict) -> dict:
    flux = [float(f) for f in v["flux"]]  # [CF0, CF1, CF2, …] — CF0 négatif typiquement

    if len(flux) < 2:
        raise ValueError("Au moins 2 flux requis (investissement initial + 1 retour).")

    # Newton-Raphson
    guess = float(v.get("estimation", 10)) / 100
    for _ in range(500):
        npv = sum(cf / (1 + guess) ** i for i, cf in enumerate(flux))
        d_npv = sum(-i * cf / (1 + guess) ** (i + 1) for i, cf in enumerate(flux))
        if abs(d_npv) < 1e-14:
            break
        new_guess = guess - npv / d_npv
        if abs(new_guess - guess) < 1e-10:
            guess = new_guess
            break
        guess = new_guess

    # Vérification
    npv_check = sum(cf / (1 + guess) ** i for i, cf in enumerate(flux))
    if abs(npv_check) > 0.01:
        raise ValueError("Convergence impossible. Essayez une autre estimation initiale.")

    return {
        "tri_pct": round(guess * 100, 4),
        "tri_decimal": round(guess, 6),
    }


# 19. MOIS.DECALER (EDATE)
def _add_months(d: date, months: int) -> date:
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def formule_mois_decaler(v: dict) -> dict:
    date_depart = _parse_date(str(v["date_depart"]))
    nb_mois = int(v["nb_mois"])

    resultat = _add_months(date_depart, nb_mois)
    return {
        "date_resultat": resultat.isoformat(),
        "date_depart": date_depart.isoformat(),
        "decalage_mois": nb_mois,
    }


# 20. FIN.MOIS (EOMONTH)
def formule_fin_mois(v: dict) -> dict:
    date_depart = _parse_date(str(v["date_depart"]))
    nb_mois = int(v.get("nb_mois", 0))

    d = _add_months(date_depart, nb_mois)
    dernier_jour = calendar.monthrange(d.year, d.month)[1]
    resultat = date(d.year, d.month, dernier_jour)

    return {
        "fin_de_mois": resultat.isoformat(),
        "date_depart": date_depart.isoformat(),
        "decalage_mois": nb_mois,
    }


# ─────────────────────────────────────────────────────────────────────────────
# LOGIQUE AVANCÉE
# ─────────────────────────────────────────────────────────────────────────────

# 21. SI.ERREUR (IFERROR) — évalue une expression, retourne une valeur de secours si erreur
def formule_si_erreur(v: dict) -> dict:
    expression = str(v["expression"])
    valeur_si_erreur = v.get("valeur_si_erreur", 0)

    try:
        # Évaluation sécurisée : on accepte uniquement des opérations numériques
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expression):
            raise ValueError("Caractères non autorisés dans l'expression.")
        resultat = eval(expression, {"__builtins__": {}}, {})  # noqa: S307
        return {"resultat": resultat, "erreur": False}
    except Exception:
        return {"resultat": valeur_si_erreur, "erreur": True}


# 22. ET / OU (AND / OR)
def formule_et_ou(v: dict) -> dict:
    conditions = v["conditions"]  # liste de booléens ou valeurs truthy

    bools = []
    for c in conditions:
        if isinstance(c, bool):
            bools.append(c)
        elif isinstance(c, str):
            bools.append(c.lower().strip() not in ("false", "0", "", "non", "faux"))
        else:
            bools.append(bool(c))

    return {
        "et": all(bools),
        "ou": any(bools),
        "nb_vrai": sum(bools),
        "nb_faux": len(bools) - sum(bools),
    }


# 23. ESTVIDE (ISBLANK)
def formule_estvide(v: dict) -> dict:
    valeurs = v["valeurs"]

    resultats = []
    nb_vides = 0
    for val in valeurs:
        est_vide = val is None or (isinstance(val, str) and val.strip() == "")
        if est_vide:
            nb_vides += 1
        resultats.append(est_vide)

    return {
        "resultats": resultats,
        "nb_vides": nb_vides,
        "nb_non_vides": len(valeurs) - nb_vides,
    }


# ─────────────────────────────────────────────────────────────────────────────
# TABLEAUX DYNAMIQUES
# ─────────────────────────────────────────────────────────────────────────────

# 24. TRIER (SORT)
def formule_trier(v: dict) -> dict:
    valeurs = list(v["valeurs"])
    ordre = str(v.get("ordre", "asc")).lower()
    reverse = ordre in ("desc", "descending", "z-a", "-1")

    # Tri numérique si possible, sinon alphabétique
    try:
        resultat = sorted(valeurs, key=lambda x: float(x), reverse=reverse)
    except (ValueError, TypeError):
        resultat = sorted(valeurs, key=lambda x: str(x).lower(), reverse=reverse)

    return {"resultat": resultat}


# 25. TRIERPAR (SORTBY)
def formule_trierpar(v: dict) -> dict:
    donnees = v["donnees"]   # [{…}, …]
    colonne = str(v["colonne_tri"])
    ordre = str(v.get("ordre", "asc")).lower()
    reverse = ordre in ("desc", "descending", "z-a", "-1")

    try:
        resultat = sorted(donnees, key=lambda r: float(r.get(colonne, 0)), reverse=reverse)
    except (ValueError, TypeError):
        resultat = sorted(donnees, key=lambda r: str(r.get(colonne, "")).lower(), reverse=reverse)

    return {"resultat": resultat, "lignes": len(resultat)}


# 26. SEQUENCE
def formule_sequence(v: dict) -> dict:
    lignes = int(v.get("lignes", 1))
    colonnes = int(v.get("colonnes", 1))
    debut = float(v.get("debut", 1))
    pas = float(v.get("pas", 1))

    if lignes <= 0 or colonnes <= 0:
        raise ValueError("lignes et colonnes doivent être > 0.")
    if lignes * colonnes > 10000:
        raise ValueError("Séquence limitée à 10 000 éléments.")

    seq = []
    val = debut
    for _ in range(lignes):
        row = []
        for _ in range(colonnes):
            row.append(round(val, 6) if val != int(val) else int(val))
            val += pas
        seq.append(row)

    # Aplatir si 1 colonne
    if colonnes == 1:
        seq = [r[0] for r in seq]

    return {"sequence": seq, "total_elements": lignes * colonnes}


# 27. CHOISIRCOLS (CHOOSECOLS)
def formule_choisircols(v: dict) -> dict:
    donnees = v["donnees"]  # [{…}, …]
    colonnes = v["colonnes"]  # ["nom", "email"]

    if not colonnes:
        raise ValueError("Aucune colonne spécifiée.")

    resultat = []
    for row in donnees:
        new_row = {col: row.get(col) for col in colonnes}
        resultat.append(new_row)

    return {"resultat": resultat, "colonnes_selectionnees": colonnes}


# 28. VSTACK
def formule_vstack(v: dict) -> dict:
    tableaux = v["tableaux"]  # [[…], […]] ou [[{…}], [{…}]]

    if not tableaux or not isinstance(tableaux, list):
        raise ValueError("Au moins un tableau requis.")

    resultat = []
    for t in tableaux:
        if isinstance(t, list):
            resultat.extend(t)
        else:
            resultat.append(t)

    return {"resultat": resultat, "total_lignes": len(resultat)}


# ─────────────────────────────────────────────────────────────────────────────
# ARCHITECTURE (INDEX/EQUIV, ARRONDI, LET/LAMBDA)
# ─────────────────────────────────────────────────────────────────────────────

# 29. INDEX/EQUIV (INDEX/MATCH)
def formule_index_equiv(v: dict) -> dict:
    donnees = v["donnees"]      # [{…}, …]
    colonne_recherche = str(v["colonne_recherche"])
    valeur_cherchee = v["valeur_cherchee"]
    colonne_retour = str(v["colonne_retour"])

    needle = str(valeur_cherchee).lower()
    for i, row in enumerate(donnees):
        if str(row.get(colonne_recherche, "")).lower() == needle:
            return {
                "resultat": row.get(colonne_retour),
                "ligne": i + 1,
                "trouve": True,
            }

    return {"resultat": None, "ligne": -1, "trouve": False}


# 30. ARRONDI (ROUND)
def formule_arrondi(v: dict) -> dict:
    nombre = float(v["nombre"])
    decimales = int(v.get("decimales", 0))

    arrondi = round(nombre, decimales)
    arrondi_sup = -(-nombre // (10 ** -decimales)) * (10 ** -decimales) if decimales >= 0 else arrondi
    arrondi_inf = (nombre // (10 ** -decimales)) * (10 ** -decimales) if decimales >= 0 else arrondi

    import math
    return {
        "arrondi": arrondi,
        "arrondi_sup": round(math.ceil(nombre * 10**decimales) / 10**decimales, decimales),
        "arrondi_inf": round(math.floor(nombre * 10**decimales) / 10**decimales, decimales),
    }


# 31. LET/LAMBDA — exécution d'une séquence de calculs nommés
def formule_let_lambda(v: dict) -> dict:
    """Permet de définir des variables intermédiaires et une expression finale.

    variables : {"prix": 100, "taxe": 0.2, "remise": 0.1}
    expression : "prix * (1 + taxe) * (1 - remise)"
    """
    variables = v.get("variables", {})
    expression = str(v["expression"])

    # Validation sécurisée : seuls les noms de variables, chiffres, opérateurs
    # et fonctions mathématiques de base sont autorisés
    import math as _math
    safe_names = set(variables.keys()) | {
        "abs", "round", "min", "max", "sum", "pow",
        "sqrt", "log", "log10", "ceil", "floor", "pi", "e",
    }
    safe_globals = {"__builtins__": {}}
    safe_globals.update({
        "abs": abs, "round": round, "min": min, "max": max,
        "sum": sum, "pow": pow,
        "sqrt": _math.sqrt, "log": _math.log, "log10": _math.log10,
        "ceil": _math.ceil, "floor": _math.floor,
        "pi": _math.pi, "e": _math.e,
    })

    # Vérifier qu'il n'y a pas de mots-clés dangereux
    tokens = re.findall(r'[a-zA-Z_]\w*', expression)
    for token in tokens:
        if token not in safe_names:
            raise ValueError(f"Nom non autorisé dans l'expression : '{token}'")

    safe_locals = {k: float(val) for k, val in variables.items()}

    resultat = eval(expression, safe_globals, safe_locals)  # noqa: S307

    return {
        "resultat": round(resultat, 6) if isinstance(resultat, float) else resultat,
        "variables_utilisees": list(variables.keys()),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# REGISTRE DES FORMULES (clé → fonction)
# ═══════════════════════════════════════════════════════════════════════════════
FORMULAS: dict[str, callable] = {
    # v1
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
    # v2 — Nettoyage
    "supprespace": formule_supprespace,
    "substitue": formule_substitue,
    "texte_avant_apres": formule_texte_avant_apres,
    "nompropre": formule_nompropre,
    # v2 — Finance
    "vpm": formule_vpm,
    "van": formule_van,
    "tri": formule_tri,
    "mois_decaler": formule_mois_decaler,
    "fin_mois": formule_fin_mois,
    # v2 — Logique
    "si_erreur": formule_si_erreur,
    "et_ou": formule_et_ou,
    "estvide": formule_estvide,
    # v2 — Tableaux Dynamiques
    "trier": formule_trier,
    "trierpar": formule_trierpar,
    "sequence": formule_sequence,
    "choisircols": formule_choisircols,
    "vstack": formule_vstack,
    # v2 — Architecture
    "index_equiv": formule_index_equiv,
    "arrondi": formule_arrondi,
    "let_lambda": formule_let_lambda,
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

    # ── v2 — Nettoyage ──────────────────────────────────────────────────────
    "supprespace": {
        "name": "SUPPRESPACE",
        "description": "Supprimer les espaces superflus d'un texte (comme TRIM dans Excel)",
        "category": "Nettoyage",
        "variables": [
            {"name": "texte", "label": "Texte à nettoyer", "type": "string",
             "required": True, "placeholder": "  Jean   Dupont  "},
        ],
    },
    "substitue": {
        "name": "SUBSTITUE",
        "description": "Remplacer un texte par un autre dans une chaîne",
        "category": "Nettoyage",
        "variables": [
            {"name": "texte", "label": "Texte source", "type": "string",
             "required": True, "placeholder": "Hello World World"},
            {"name": "ancien", "label": "Texte à remplacer", "type": "string",
             "required": True, "placeholder": "World"},
            {"name": "nouveau", "label": "Nouveau texte", "type": "string",
             "required": True, "placeholder": "Monde"},
            {"name": "occurrence", "label": "N° occurrence (vide=toutes)", "type": "number",
             "required": False, "placeholder": "1"},
        ],
    },
    "texte_avant_apres": {
        "name": "TEXTE.AVANT / TEXTE.APRES",
        "description": "Extraire le texte avant et après un délimiteur",
        "category": "Nettoyage",
        "variables": [
            {"name": "texte", "label": "Texte source", "type": "string",
             "required": True, "placeholder": "nom.prenom@entreprise.com"},
            {"name": "delimiteur", "label": "Délimiteur", "type": "string",
             "required": True, "placeholder": "@"},
            {"name": "occurrence", "label": "N° occurrence", "type": "number",
             "required": False, "placeholder": "1"},
        ],
    },
    "nompropre": {
        "name": "NOMPROPRE",
        "description": "Mettre en majuscule la première lettre de chaque mot",
        "category": "Nettoyage",
        "variables": [
            {"name": "texte", "label": "Texte à formater", "type": "string",
             "required": True, "placeholder": "jean-pierre DUPONT"},
        ],
    },

    # ── v2 — Finance ────────────────────────────────────────────────────────
    "vpm": {
        "name": "VPM (PMT)",
        "description": "Calculer la mensualité d'un emprunt (identique à PMT dans Excel)",
        "category": "Finance",
        "variables": [
            {"name": "taux_annuel", "label": "Taux annuel (%)", "type": "number",
             "required": True, "placeholder": "5"},
            {"name": "nb_periodes", "label": "Nombre de mensualités", "type": "number",
             "required": True, "placeholder": "240"},
            {"name": "valeur_actuelle", "label": "Montant emprunté (€)", "type": "number",
             "required": True, "placeholder": "200000"},
            {"name": "valeur_future", "label": "Valeur future (€)", "type": "number",
             "required": False, "placeholder": "0"},
            {"name": "debut_periode", "label": "Paiement début de période (0/1)", "type": "number",
             "required": False, "placeholder": "0"},
        ],
    },
    "van": {
        "name": "VAN (NPV)",
        "description": "Valeur Actuelle Nette d'une série de flux de trésorerie",
        "category": "Finance",
        "variables": [
            {"name": "taux", "label": "Taux d'actualisation (%)", "type": "number",
             "required": True, "placeholder": "10"},
            {"name": "flux", "label": "Flux de trésorerie", "type": "number[]",
             "required": True, "placeholder": "-100000, 30000, 35000, 40000, 45000"},
        ],
    },
    "tri": {
        "name": "TRI (IRR)",
        "description": "Taux de Rendement Interne — le taux qui rend la VAN nulle",
        "category": "Finance",
        "variables": [
            {"name": "flux", "label": "Flux de trésorerie", "type": "number[]",
             "required": True, "placeholder": "-100000, 30000, 35000, 40000, 45000"},
            {"name": "estimation", "label": "Estimation initiale (%)", "type": "number",
             "required": False, "placeholder": "10"},
        ],
    },
    "mois_decaler": {
        "name": "MOIS.DECALER",
        "description": "Décaler une date d'un nombre de mois donné",
        "category": "Dates",
        "variables": [
            {"name": "date_depart", "label": "Date de départ", "type": "string",
             "required": True, "placeholder": "2025-01-31"},
            {"name": "nb_mois", "label": "Nombre de mois", "type": "number",
             "required": True, "placeholder": "3"},
        ],
    },
    "fin_mois": {
        "name": "FIN.MOIS",
        "description": "Dernier jour du mois après un décalage de N mois",
        "category": "Dates",
        "variables": [
            {"name": "date_depart", "label": "Date de départ", "type": "string",
             "required": True, "placeholder": "2025-01-15"},
            {"name": "nb_mois", "label": "Décalage en mois", "type": "number",
             "required": False, "placeholder": "2"},
        ],
    },

    # ── v2 — Logique ────────────────────────────────────────────────────────
    "si_erreur": {
        "name": "SI.ERREUR",
        "description": "Évaluer une expression numérique, retourner une valeur de secours si erreur",
        "category": "Logique",
        "variables": [
            {"name": "expression", "label": "Expression à évaluer", "type": "string",
             "required": True, "placeholder": "100 / 0"},
            {"name": "valeur_si_erreur", "label": "Valeur si erreur", "type": "string",
             "required": False, "placeholder": "0"},
        ],
    },
    "et_ou": {
        "name": "ET / OU",
        "description": "Tester si toutes (ET) ou au moins une (OU) des conditions sont vraies",
        "category": "Logique",
        "variables": [
            {"name": "conditions", "label": "Conditions (JSON)", "type": "json",
             "required": True, "placeholder": '[true, true, false]'},
        ],
    },
    "estvide": {
        "name": "ESTVIDE",
        "description": "Vérifier quelles valeurs sont vides dans une liste",
        "category": "Logique",
        "variables": [
            {"name": "valeurs", "label": "Valeurs à tester", "type": "json",
             "required": True, "placeholder": '["Alice", "", null, "Bob", " "]'},
        ],
    },

    # ── v2 — Tableaux Dynamiques ────────────────────────────────────────────
    "trier": {
        "name": "TRIER",
        "description": "Trier une liste de valeurs par ordre croissant ou décroissant",
        "category": "Tableaux Dynamiques",
        "variables": [
            {"name": "valeurs", "label": "Valeurs à trier", "type": "json",
             "required": True, "placeholder": '[50, 10, 30, 20, 40]'},
            {"name": "ordre", "label": "Ordre (asc/desc)", "type": "string",
             "required": False, "placeholder": "asc"},
        ],
    },
    "trierpar": {
        "name": "TRIERPAR",
        "description": "Trier un tableau d'objets par une colonne spécifique",
        "category": "Tableaux Dynamiques",
        "variables": [
            {"name": "donnees", "label": "Données (table JSON)", "type": "json",
             "required": True,
             "placeholder": '[{"nom":"Charlie","score":80},{"nom":"Alice","score":95}]'},
            {"name": "colonne_tri", "label": "Colonne de tri", "type": "string",
             "required": True, "placeholder": "score"},
            {"name": "ordre", "label": "Ordre (asc/desc)", "type": "string",
             "required": False, "placeholder": "desc"},
        ],
    },
    "sequence": {
        "name": "SEQUENCE",
        "description": "Générer une séquence numérique (grille de N lignes x M colonnes)",
        "category": "Tableaux Dynamiques",
        "variables": [
            {"name": "lignes", "label": "Nombre de lignes", "type": "number",
             "required": True, "placeholder": "5"},
            {"name": "colonnes", "label": "Nombre de colonnes", "type": "number",
             "required": False, "placeholder": "1"},
            {"name": "debut", "label": "Valeur de départ", "type": "number",
             "required": False, "placeholder": "1"},
            {"name": "pas", "label": "Incrément", "type": "number",
             "required": False, "placeholder": "1"},
        ],
    },
    "choisircols": {
        "name": "CHOISIRCOLS",
        "description": "Extraire uniquement certaines colonnes d'un tableau",
        "category": "Tableaux Dynamiques",
        "variables": [
            {"name": "donnees", "label": "Données (table JSON)", "type": "json",
             "required": True,
             "placeholder": '[{"nom":"Alice","age":30,"email":"a@mail.com"}]'},
            {"name": "colonnes", "label": "Colonnes à garder", "type": "string[]",
             "required": True, "placeholder": "nom, email"},
        ],
    },
    "vstack": {
        "name": "VSTACK",
        "description": "Empiler verticalement plusieurs tableaux en un seul",
        "category": "Tableaux Dynamiques",
        "variables": [
            {"name": "tableaux", "label": "Tableaux à empiler (JSON)", "type": "json",
             "required": True,
             "placeholder": '[[1,2,3],[4,5,6],[7,8,9]]'},
        ],
    },

    # ── v2 — Architecture ───────────────────────────────────────────────────
    "index_equiv": {
        "name": "INDEX / EQUIV",
        "description": "Chercher une valeur dans une colonne et retourner la valeur d'une autre colonne",
        "category": "Recherche",
        "variables": [
            {"name": "donnees", "label": "Données (table JSON)", "type": "json",
             "required": True,
             "placeholder": '[{"ref":"A1","nom":"Widget","prix":9.99}]'},
            {"name": "colonne_recherche", "label": "Colonne de recherche", "type": "string",
             "required": True, "placeholder": "ref"},
            {"name": "valeur_cherchee", "label": "Valeur cherchée", "type": "string",
             "required": True, "placeholder": "A1"},
            {"name": "colonne_retour", "label": "Colonne de retour", "type": "string",
             "required": True, "placeholder": "prix"},
        ],
    },
    "arrondi": {
        "name": "ARRONDI",
        "description": "Arrondir un nombre (standard, supérieur et inférieur)",
        "category": "Mathématiques",
        "variables": [
            {"name": "nombre", "label": "Nombre à arrondir", "type": "number",
             "required": True, "placeholder": "3.14159"},
            {"name": "decimales", "label": "Nombre de décimales", "type": "number",
             "required": False, "placeholder": "2"},
        ],
    },
    "let_lambda": {
        "name": "LET / LAMBDA",
        "description": "Définir des variables et évaluer une expression personnalisée",
        "category": "Architecture",
        "variables": [
            {"name": "variables", "label": "Variables (JSON objet)", "type": "json",
             "required": True,
             "placeholder": '{"prix":100,"taxe":0.2,"remise":0.1}'},
            {"name": "expression", "label": "Expression à évaluer", "type": "string",
             "required": True, "placeholder": "prix * (1 + taxe) * (1 - remise)"},
        ],
    },
}
