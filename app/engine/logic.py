"""
Moteur de calcul protégé — les formules ne sont jamais exposées à l'utilisateur.
Chaque fonction reçoit un dict de variables et renvoie un dict de résultats.

IMPORTANT : ce fichier est le cœur de la propriété intellectuelle.
Ne jamais exposer le code source via l'API.
"""

from __future__ import annotations

import calendar
import math
import random
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


# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║                    ENGINE v3 — 30 NOUVELLES FORMULES                        ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝

# ─────────────────────────────────────────────────────────────────────────────
# STATISTIQUES & PERFORMANCE
# ─────────────────────────────────────────────────────────────────────────────

# 32. MAX.SI.ENS (MAXIFS)
def formule_max_si_ens(v: dict) -> dict:
    donnees = v["donnees"]
    colonne_valeur = str(v["colonne_valeur"])
    criteres = v["criteres"]
    vals = [float(row[colonne_valeur]) for row in donnees if _match_row(row, criteres)]
    if not vals:
        raise ValueError("Aucune ligne ne correspond aux critères.")
    return {"max": max(vals), "lignes_correspondantes": len(vals)}


# 33. MIN.SI.ENS (MINIFS)
def formule_min_si_ens(v: dict) -> dict:
    donnees = v["donnees"]
    colonne_valeur = str(v["colonne_valeur"])
    criteres = v["criteres"]
    vals = [float(row[colonne_valeur]) for row in donnees if _match_row(row, criteres)]
    if not vals:
        raise ValueError("Aucune ligne ne correspond aux critères.")
    return {"min": min(vals), "lignes_correspondantes": len(vals)}


# 34. RANG.EGAL (RANK.EQ)
def formule_rang_egal(v: dict) -> dict:
    nombre = float(v["nombre"])
    valeurs = [float(x) for x in v["valeurs"]]
    ordre = str(v.get("ordre", "desc")).lower()

    sorted_vals = sorted(set(valeurs), reverse=(ordre == "desc"))
    try:
        rang = sorted_vals.index(nombre) + 1
    except ValueError:
        raise ValueError(f"La valeur {nombre} n'existe pas dans la liste.")

    return {"rang": rang, "total": len(valeurs), "valeurs_distinctes": len(sorted_vals)}


# 35. MEDIANE (MEDIAN)
def formule_mediane(v: dict) -> dict:
    valeurs = sorted(float(x) for x in v["valeurs"])
    n = len(valeurs)
    if n == 0:
        raise ValueError("La liste est vide.")
    if n % 2 == 1:
        mediane = valeurs[n // 2]
    else:
        mediane = (valeurs[n // 2 - 1] + valeurs[n // 2]) / 2
    return {"mediane": round(mediane, 6), "count": n}


# 36. AGREGAT (AGGREGATE)
_AGG_FUNCS = {
    1: ("MOYENNE", lambda v: sum(v) / len(v)),
    2: ("NB", lambda v: len(v)),
    4: ("MAX", lambda v: max(v)),
    5: ("MIN", lambda v: min(v)),
    7: ("ECARTYPE", lambda v: math.sqrt(sum((x - sum(v)/len(v))**2 for x in v) / (len(v) - 1)) if len(v) > 1 else 0),
    9: ("SOMME", lambda v: sum(v)),
    12: ("MEDIANE", lambda v: sorted(v)[len(v)//2] if len(v) % 2 else (sorted(v)[len(v)//2-1]+sorted(v)[len(v)//2])/2),
}


def formule_agregat(v: dict) -> dict:
    valeurs_brutes = v["valeurs"]
    fonction = int(v["fonction"])
    ignorer_erreurs = v.get("ignorer_erreurs", True)

    valeurs = []
    erreurs = 0
    for val in valeurs_brutes:
        try:
            valeurs.append(float(val))
        except (ValueError, TypeError):
            erreurs += 1
            if not ignorer_erreurs:
                raise ValueError(f"Valeur non numérique : {val}")

    if not valeurs:
        raise ValueError("Aucune valeur numérique valide.")

    if fonction not in _AGG_FUNCS:
        raise ValueError(f"Fonction {fonction} non supportée. Disponibles : {list(_AGG_FUNCS.keys())}")

    nom, fn = _AGG_FUNCS[fonction]
    return {"resultat": round(fn(valeurs), 8), "fonction": nom, "erreurs_ignorees": erreurs}


# ─────────────────────────────────────────────────────────────────────────────
# FINANCE HIGH-TICKET
# ─────────────────────────────────────────────────────────────────────────────

# 37. TAUX (RATE) — Newton-Raphson (précision bancaire)
def formule_taux(v: dict) -> dict:
    nper = int(v["nb_periodes"])
    pmt = float(v["mensualite"])
    pv = float(v["valeur_actuelle"])
    fv = float(v.get("valeur_future", 0))
    type_ = int(v.get("debut_periode", 0))

    # f(r) = pv*(1+r)^n + pmt*(1+r*type)*((1+r)^n - 1)/r + fv = 0
    guess = float(v.get("estimation", 1)) / 100

    for _ in range(1000):
        if abs(guess) < 1e-12:
            guess = 1e-12
        rn = (1 + guess) ** nper
        f = pv * rn + pmt * (1 + guess * type_) * (rn - 1) / guess + fv

        # Derivative
        drn = nper * (1 + guess) ** (nper - 1)
        df = (pv * drn
              + pmt * type_ * (rn - 1) / guess
              + pmt * (1 + guess * type_) * (drn * guess - (rn - 1)) / guess**2)

        if abs(df) < 1e-18:
            break
        new_guess = guess - f / df
        if abs(new_guess - guess) < 1e-12:
            guess = new_guess
            break
        guess = new_guess

    return {
        "taux_periodique_pct": round(guess * 100, 8),
        "taux_annuel_pct": round(guess * 12 * 100, 8),
    }


# 38. NPM (NPER)
def formule_npm(v: dict) -> dict:
    taux = float(v["taux_periodique"]) / 100
    pmt = float(v["mensualite"])
    pv = float(v["valeur_actuelle"])
    fv = float(v.get("valeur_future", 0))

    if taux == 0:
        if pmt == 0:
            raise ValueError("Mensualité ne peut pas être 0 avec taux 0.")
        nper = -(pv + fv) / pmt
    else:
        # nper = log((pmt - fv*r) / (pmt + pv*r)) / log(1+r)
        numerator = pmt - fv * taux
        denominator = pmt + pv * taux
        if denominator == 0 or numerator / denominator <= 0:
            raise ValueError("Impossible de calculer NPER avec ces paramètres.")
        nper = math.log(numerator / denominator) / math.log(1 + taux)

    return {
        "nb_periodes": round(nper, 6),
        "nb_annees": round(nper / 12, 2),
    }


# 39. VC (FV — Future Value)
def formule_vc(v: dict) -> dict:
    taux = float(v["taux_periodique"]) / 100
    nper = int(v["nb_periodes"])
    pmt = float(v.get("mensualite", 0))
    pv = float(v.get("valeur_actuelle", 0))
    type_ = int(v.get("debut_periode", 0))

    if taux == 0:
        fv = -(pv + pmt * nper)
    else:
        rn = (1 + taux) ** nper
        fv = -(pv * rn + pmt * (1 + taux * type_) * (rn - 1) / taux)

    return {"valeur_future": round(fv, 2)}


# 40. VA (PV — Present Value)
def formule_va(v: dict) -> dict:
    taux = float(v["taux_periodique"]) / 100
    nper = int(v["nb_periodes"])
    pmt = float(v.get("mensualite", 0))
    fv = float(v.get("valeur_future", 0))
    type_ = int(v.get("debut_periode", 0))

    if taux == 0:
        pv = -(fv + pmt * nper)
    else:
        rn = (1 + taux) ** nper
        pv = -(fv / rn + pmt * (1 + taux * type_) * (rn - 1) / (taux * rn))

    return {"valeur_actuelle": round(pv, 2)}


# 41. FRACTION.ANNEE (YEARFRAC)
def formule_fraction_annee(v: dict) -> dict:
    d1 = _parse_date(str(v["date_debut"]))
    d2 = _parse_date(str(v["date_fin"]))
    base = int(v.get("base", 1))  # 0=US30/360, 1=Actual/Actual, 2=Actual/360, 3=Actual/365

    if d1 > d2:
        d1, d2 = d2, d1

    days = (d2 - d1).days

    if base == 0:  # US 30/360
        y1, m1, day1 = d1.year, d1.month, min(d1.day, 30)
        y2, m2, day2 = d2.year, d2.month, min(d2.day, 30)
        if day1 == 30:
            day2 = min(day2, 30)
        fraction = ((y2 - y1) * 360 + (m2 - m1) * 30 + (day2 - day1)) / 360
    elif base == 1:  # Actual/Actual
        year_days = 366 if calendar.isleap(d1.year) else 365
        fraction = days / year_days
    elif base == 2:  # Actual/360
        fraction = days / 360
    elif base == 3:  # Actual/365
        fraction = days / 365
    else:
        raise ValueError(f"Base {base} non supportée (0-3).")

    return {"fraction": round(fraction, 10), "jours": days, "base": base}


# ─────────────────────────────────────────────────────────────────────────────
# MANIPULATION DE DONNÉES
# ─────────────────────────────────────────────────────────────────────────────

# 42. CHOISIR.LIGNES (CHOOSEROWS)
def formule_choisir_lignes(v: dict) -> dict:
    donnees = v["donnees"]
    indices = [int(i) for i in v["indices"]]  # 1-indexed, négatif = depuis la fin

    resultat = []
    for idx in indices:
        if idx > 0:
            pos = idx - 1
        else:
            pos = len(donnees) + idx
        if 0 <= pos < len(donnees):
            resultat.append(donnees[pos])
        else:
            raise ValueError(f"Indice {idx} hors limites (1 à {len(donnees)}).")

    return {"resultat": resultat, "lignes_selectionnees": len(resultat)}


# 43. PRENDRE (TAKE)
def formule_prendre(v: dict) -> dict:
    donnees = v["donnees"]
    nb = int(v["nb_lignes"])

    if nb > 0:
        resultat = donnees[:nb]
    else:
        resultat = donnees[nb:]  # négatif = depuis la fin

    return {"resultat": resultat, "lignes": len(resultat)}


# 44. EXCLURE (DROP)
def formule_exclure(v: dict) -> dict:
    donnees = v["donnees"]
    nb = int(v["nb_lignes"])

    if nb > 0:
        resultat = donnees[nb:]
    else:
        resultat = donnees[:nb]  # négatif = exclure depuis la fin

    return {"resultat": resultat, "lignes": len(resultat)}


# 45. DÉVELOPPER (EXPAND)
def formule_developper(v: dict) -> dict:
    donnees = v["donnees"]
    nb_lignes = int(v["nb_lignes"])
    valeur_defaut = v.get("valeur_defaut", None)

    resultat = list(donnees)
    while len(resultat) < nb_lignes:
        resultat.append(valeur_defaut)

    return {"resultat": resultat[:nb_lignes], "lignes": nb_lignes}


# 46. FRACTIONNER.TEXTE (TEXTSPLIT)
def formule_fractionner_texte(v: dict) -> dict:
    texte = str(v["texte"])
    delimiteur_col = str(v.get("delimiteur_col", ","))
    delimiteur_ligne = v.get("delimiteur_ligne")

    if delimiteur_ligne:
        lignes = texte.split(str(delimiteur_ligne))
        resultat = [ligne.split(delimiteur_col) for ligne in lignes]
        resultat = [[c.strip() for c in row] for row in resultat]
    else:
        resultat = [c.strip() for c in texte.split(delimiteur_col)]

    return {"resultat": resultat}


# 47. UNICODE / CAR (UNICODE / CHAR)
def formule_unicode_car(v: dict) -> dict:
    resultats = {}
    if "caractere" in v:
        c = str(v["caractere"])
        if len(c) != 1:
            raise ValueError("Un seul caractère attendu.")
        resultats["code_unicode"] = ord(c)
    if "code" in v:
        code = int(v["code"])
        resultats["caractere"] = chr(code)
    if not resultats:
        raise ValueError("Fournir 'caractere' ou 'code'.")
    return resultats


# ─────────────────────────────────────────────────────────────────────────────
# LOGIQUE & VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

# 48. EXACT
def formule_exact(v: dict) -> dict:
    texte1 = str(v["texte1"])
    texte2 = str(v["texte2"])
    return {"identique": texte1 == texte2}


# 49. ESTNUM (ISNUMBER)
def formule_estnum(v: dict) -> dict:
    valeurs = v["valeurs"]
    resultats = []
    for val in valeurs:
        try:
            float(val)
            resultats.append(True)
        except (ValueError, TypeError):
            resultats.append(False)
    return {"resultats": resultats, "nb_numeriques": sum(resultats)}


# 50. ESTTEXTE (ISTEXT)
def formule_esttexte(v: dict) -> dict:
    valeurs = v["valeurs"]
    resultats = []
    for val in valeurs:
        is_text = isinstance(val, str) and val.strip() != ""
        try:
            float(val)
            is_text = False  # C'est un nombre représenté en texte
        except (ValueError, TypeError):
            pass
        resultats.append(is_text)
    return {"resultats": resultats, "nb_textes": sum(resultats)}


# 51. CHANGER (SWITCH)
def formule_changer(v: dict) -> dict:
    expression = v["expression"]
    cas = v["cas"]  # [{"valeur": "A", "resultat": "Alpha"}, ...]
    defaut = v.get("defaut")

    expr_str = str(expression).lower().strip()
    for c in cas:
        if str(c["valeur"]).lower().strip() == expr_str:
            return {"resultat": c["resultat"], "cas_matche": c["valeur"]}

    return {"resultat": defaut, "cas_matche": None}


# 52. RECHERCHEH (HLOOKUP)
def formule_rechercheh(v: dict) -> dict:
    valeur_cherchee = v["valeur_cherchee"]
    en_tetes = v["en_tetes"]  # première ligne
    donnees = v["donnees"]    # lignes suivantes (liste de listes)
    ligne_retour = int(v.get("ligne_retour", 1)) - 1

    needle = str(valeur_cherchee).lower()
    for col_idx, header in enumerate(en_tetes):
        if str(header).lower() == needle:
            if ligne_retour < 0 or ligne_retour >= len(donnees):
                raise ValueError(f"Ligne {ligne_retour+1} hors limites.")
            return {
                "resultat": donnees[ligne_retour][col_idx] if col_idx < len(donnees[ligne_retour]) else None,
                "colonne": col_idx + 1,
                "trouve": True,
            }

    return {"resultat": None, "colonne": -1, "trouve": False}


# ─────────────────────────────────────────────────────────────────────────────
# ANALYSE & PRÉDICTION
# ─────────────────────────────────────────────────────────────────────────────

# 53. PREVISION.ETS (FORECAST — régression linéaire)
def formule_prevision(v: dict) -> dict:
    x_cible = float(v["x_cible"])
    x_connus = [float(x) for x in v["x_connus"]]
    y_connus = [float(y) for y in v["y_connus"]]

    if len(x_connus) != len(y_connus):
        raise ValueError("x_connus et y_connus doivent avoir la même taille.")
    n = len(x_connus)
    if n < 2:
        raise ValueError("Au moins 2 points requis.")

    x_mean = sum(x_connus) / n
    y_mean = sum(y_connus) / n

    ss_xy = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_connus, y_connus))
    ss_xx = sum((x - x_mean) ** 2 for x in x_connus)

    if ss_xx == 0:
        raise ValueError("Les valeurs x sont toutes identiques.")

    pente = ss_xy / ss_xx
    ordonnee = y_mean - pente * x_mean
    y_prevu = ordonnee + pente * x_cible

    # R² (coefficient de détermination)
    ss_yy = sum((y - y_mean) ** 2 for y in y_connus)
    r_squared = (ss_xy ** 2) / (ss_xx * ss_yy) if ss_yy > 0 else 1.0

    return {
        "prevision": round(y_prevu, 8),
        "pente": round(pente, 8),
        "ordonnee_origine": round(ordonnee, 8),
        "r_carre": round(r_squared, 8),
    }


# 54. FREQUENCE (FREQUENCY)
def formule_frequence(v: dict) -> dict:
    donnees = [float(x) for x in v["donnees"]]
    bornes = sorted(float(b) for b in v["bornes"])

    freq = [0] * (len(bornes) + 1)
    for val in donnees:
        placed = False
        for i, borne in enumerate(bornes):
            if val <= borne:
                freq[i] += 1
                placed = True
                break
        if not placed:
            freq[-1] += 1

    labels = []
    for i, borne in enumerate(bornes):
        if i == 0:
            labels.append(f"<= {borne}")
        else:
            labels.append(f"{bornes[i-1]} - {borne}")
    labels.append(f"> {bornes[-1]}")

    return {"frequences": freq, "labels": labels, "total": len(donnees)}


# 55. ALEA.ENTRE.BORNES (RANDBETWEEN)
def formule_alea_entre_bornes(v: dict) -> dict:
    borne_inf = int(v["borne_inf"])
    borne_sup = int(v["borne_sup"])
    nb = int(v.get("nombre", 1))

    if borne_inf > borne_sup:
        raise ValueError("borne_inf doit être <= borne_sup.")
    if nb < 1 or nb > 10000:
        raise ValueError("nombre doit être entre 1 et 10 000.")

    valeurs = [random.randint(borne_inf, borne_sup) for _ in range(nb)]
    return {
        "valeurs": valeurs if nb > 1 else valeurs[0],
        "nombre_genere": nb,
    }


# ─────────────────────────────────────────────────────────────────────────────
# STRUCTURE & TABLEAUX
# ─────────────────────────────────────────────────────────────────────────────

# 56. SCAN / MAP / REDUCE
def formule_scan_map_reduce(v: dict) -> dict:
    valeurs = v["valeurs"]
    operation = str(v["operation"]).lower()

    allowed_ops = set("0123456789+-*/.() xval")
    safe_globals = {"__builtins__": {}, "abs": abs, "round": round,
                    "min": min, "max": max, "sqrt": math.sqrt,
                    "pow": pow, "log": math.log}

    if operation == "somme_cumul":
        # SCAN — somme cumulée
        acc = 0
        result = []
        for val in valeurs:
            acc += float(val)
            result.append(round(acc, 6))
        return {"resultat": result, "operation": "scan_somme_cumulee"}

    elif operation == "produit_cumul":
        acc = 1
        result = []
        for val in valeurs:
            acc *= float(val)
            result.append(round(acc, 6))
        return {"resultat": result, "operation": "scan_produit_cumule"}

    elif operation == "somme":
        # REDUCE — somme
        return {"resultat": round(sum(float(x) for x in valeurs), 6), "operation": "reduce_somme"}

    elif operation == "produit":
        acc = 1
        for val in valeurs:
            acc *= float(val)
        return {"resultat": round(acc, 6), "operation": "reduce_produit"}

    elif operation == "carre":
        # MAP — carré
        return {"resultat": [round(float(x)**2, 6) for x in valeurs], "operation": "map_carre"}

    elif operation == "racine":
        return {"resultat": [round(math.sqrt(float(x)), 6) for x in valeurs], "operation": "map_racine"}

    elif operation == "abs":
        return {"resultat": [abs(float(x)) for x in valeurs], "operation": "map_abs"}

    else:
        raise ValueError(f"Opération inconnue : {operation}. "
                         "Disponibles : somme_cumul, produit_cumul, somme, produit, carre, racine, abs")


# 57. DANSCOL (TOCOL)
def formule_danscol(v: dict) -> dict:
    donnees = v["donnees"]
    resultat = []
    for item in donnees:
        if isinstance(item, list):
            resultat.extend(item)
        elif isinstance(item, dict):
            resultat.extend(item.values())
        else:
            resultat.append(item)
    return {"resultat": resultat, "total": len(resultat)}


# 58. DANSLIGNE (TOROW)
def formule_dansligne(v: dict) -> dict:
    donnees = v["donnees"]
    resultat = []
    for item in donnees:
        if isinstance(item, list):
            resultat.extend(item)
        elif isinstance(item, dict):
            resultat.extend(item.values())
        else:
            resultat.append(item)
    return {"resultat": resultat, "total": len(resultat)}


# 59. WRAPROWS / WRAPCOLS
def formule_wraprows_wrapcols(v: dict) -> dict:
    valeurs = v["valeurs"]
    taille = int(v["taille"])
    mode = str(v.get("mode", "rows")).lower()  # rows ou cols
    pad = v.get("valeur_pad")

    if taille <= 0:
        raise ValueError("taille doit être > 0.")

    flat = list(valeurs)
    # Compléter pour que la taille soit divisible
    while len(flat) % taille != 0:
        flat.append(pad)

    if mode in ("rows", "lignes"):
        resultat = [flat[i:i + taille] for i in range(0, len(flat), taille)]
    else:
        nb_cols = taille
        nb_rows = len(flat) // nb_cols
        resultat = [[flat[r * nb_cols + c] for c in range(nb_cols)] for r in range(nb_rows)]

    return {"resultat": resultat, "dimensions": f"{len(resultat)}x{taille}"}


# 60. ASSEMB.H (HSTACK)
def formule_assemb_h(v: dict) -> dict:
    tableaux = v["tableaux"]

    if not tableaux:
        raise ValueError("Au moins un tableau requis.")

    # Déterminer la hauteur max
    max_len = max(len(t) if isinstance(t, list) else 1 for t in tableaux)

    # Normaliser : chaque tableau = liste de listes (lignes)
    normalized = []
    for t in tableaux:
        if not isinstance(t, list):
            normalized.append([[t]] * max_len)
        elif not t:
            normalized.append([[None]] * max_len)
        elif not isinstance(t[0], list):
            # Colonne simple → transformer en liste de listes
            col = [[item] for item in t]
            while len(col) < max_len:
                col.append([None])
            normalized.append(col)
        else:
            while len(t) < max_len:
                t.append([None] * len(t[0]))
            normalized.append(t)

    # Assembler horizontalement
    resultat = []
    for row_idx in range(max_len):
        row = []
        for t in normalized:
            row.extend(t[row_idx] if row_idx < len(t) else [None])
        resultat.append(row)

    return {"resultat": resultat, "lignes": len(resultat)}


# 61. VALEURNOMB (NUMBERVALUE)
def formule_valeurnomb(v: dict) -> dict:
    texte = str(v["texte"]).strip()
    sep_decimal = str(v.get("sep_decimal", "."))
    sep_milliers = str(v.get("sep_milliers", ""))

    cleaned = texte
    if sep_milliers:
        cleaned = cleaned.replace(sep_milliers, "")
    if sep_decimal != ".":
        cleaned = cleaned.replace(sep_decimal, ".")

    # Supprimer symboles monétaires courants
    for sym in ("€", "$", "£", "¥", "%", " "):
        cleaned = cleaned.replace(sym, "")

    is_pct = "%" in texte
    nombre = float(cleaned)
    if is_pct:
        nombre /= 100

    return {"nombre": nombre}


# 62. RECHERCHE Vector (LOOKUP)
def formule_recherche_v(v: dict) -> dict:
    valeur_cherchee = float(v["valeur_cherchee"])
    vecteur_recherche = [float(x) for x in v["vecteur_recherche"]]
    vecteur_retour = v["vecteur_retour"]

    if len(vecteur_recherche) != len(vecteur_retour):
        raise ValueError("Les vecteurs doivent avoir la même taille.")

    # LOOKUP recherche la plus grande valeur <= valeur_cherchée (vecteur trié croissant)
    result_idx = -1
    for i, val in enumerate(vecteur_recherche):
        if val <= valeur_cherchee:
            result_idx = i
        else:
            break

    if result_idx == -1:
        raise ValueError("Aucune valeur <= à la valeur cherchée.")

    return {
        "resultat": vecteur_retour[result_idx],
        "position": result_idx + 1,
        "valeur_exacte": vecteur_recherche[result_idx],
    }


# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║              ENGINE v4 — 50 FORMULES ENTERPRISE PACK                       ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝

# ─────────────────────────────────────────────────────────────────────────────
# AUDIT & AMORTISSEMENTS FINANCIERS
# ─────────────────────────────────────────────────────────────────────────────

# 63. INTPER (IPMT) — Intérêts d'une période
def formule_intper(v: dict) -> dict:
    taux = float(v["taux_periodique"]) / 100
    periode = int(v["periode"])
    nb_periodes = int(v["nb_periodes"])
    va = float(v["valeur_actuelle"])
    vf = float(v.get("valeur_future", 0))
    type_ = int(v.get("debut_periode", 0))

    if periode < 1 or periode > nb_periodes:
        raise ValueError(f"Période {periode} hors limites (1 à {nb_periodes}).")

    if taux == 0:
        return {"interets": 0.0, "periode": periode}

    # PMT
    rn = (1 + taux) ** nb_periodes
    pmt = -(va * rn + vf) / ((1 + taux * type_) * (rn - 1) / taux)

    # FV at period-1
    if type_ == 0:
        fv_prev = va * (1 + taux) ** (periode - 1) + pmt * ((1 + taux) ** (periode - 1) - 1) / taux
    else:
        fv_prev = va * (1 + taux) ** (periode - 1) + pmt * (1 + taux) * ((1 + taux) ** (periode - 1) - 1) / taux

    ipmt = fv_prev * taux
    if type_ == 1:
        ipmt = ipmt / (1 + taux)

    return {"interets": round(ipmt, 2), "periode": periode}


# 64. PRINCPER (PPMT) — Principal d'une période
def formule_princper(v: dict) -> dict:
    taux = float(v["taux_periodique"]) / 100
    periode = int(v["periode"])
    nb_periodes = int(v["nb_periodes"])
    va = float(v["valeur_actuelle"])
    vf = float(v.get("valeur_future", 0))
    type_ = int(v.get("debut_periode", 0))

    if periode < 1 or periode > nb_periodes:
        raise ValueError(f"Période {periode} hors limites (1 à {nb_periodes}).")

    if taux == 0:
        pmt = -(va + vf) / nb_periodes
        return {"principal": round(pmt, 2), "periode": periode}

    rn = (1 + taux) ** nb_periodes
    pmt = -(va * rn + vf) / ((1 + taux * type_) * (rn - 1) / taux)

    ipmt_result = formule_intper(v)
    ppmt = pmt - ipmt_result["interets"]

    return {"principal": round(ppmt, 2), "periode": periode}


# 65. CUMUL.INTER (CUMIPMT)
def formule_cumul_inter(v: dict) -> dict:
    taux = float(v["taux_periodique"]) / 100
    nb_periodes = int(v["nb_periodes"])
    va = float(v["valeur_actuelle"])
    debut = int(v["periode_debut"])
    fin = int(v["periode_fin"])

    if debut < 1 or fin > nb_periodes or debut > fin:
        raise ValueError(f"Plage [{debut}, {fin}] invalide.")

    total = 0.0
    for p in range(debut, fin + 1):
        r = formule_intper({
            "taux_periodique": v["taux_periodique"],
            "periode": p,
            "nb_periodes": nb_periodes,
            "valeur_actuelle": va,
        })
        total += r["interets"]

    return {"cumul_interets": round(total, 2), "periodes": f"{debut}-{fin}"}


# 66. CUMUL.PRINC (CUMPRINC)
def formule_cumul_princ(v: dict) -> dict:
    taux = float(v["taux_periodique"]) / 100
    nb_periodes = int(v["nb_periodes"])
    va = float(v["valeur_actuelle"])
    debut = int(v["periode_debut"])
    fin = int(v["periode_fin"])

    if debut < 1 or fin > nb_periodes or debut > fin:
        raise ValueError(f"Plage [{debut}, {fin}] invalide.")

    total = 0.0
    for p in range(debut, fin + 1):
        r = formule_princper({
            "taux_periodique": v["taux_periodique"],
            "periode": p,
            "nb_periodes": nb_periodes,
            "valeur_actuelle": va,
        })
        total += r["principal"]

    return {"cumul_principal": round(total, 2), "periodes": f"{debut}-{fin}"}


# 67. AMORL (SLN — amortissement linéaire)
def formule_amorl(v: dict) -> dict:
    cout = float(v["cout"])
    residuel = float(v.get("valeur_residuelle", 0))
    duree = int(v["duree_vie"])

    if duree <= 0:
        raise ValueError("Durée de vie doit être > 0.")

    sln = (cout - residuel) / duree
    return {"amortissement_annuel": round(sln, 2), "duree": duree}


# 68. AMORDEGR (DB — amortissement dégressif)
def formule_amordegr(v: dict) -> dict:
    cout = float(v["cout"])
    residuel = float(v.get("valeur_residuelle", 0))
    duree = int(v["duree_vie"])
    periode = int(v["periode"])

    if duree <= 0 or periode < 1 or periode > duree:
        raise ValueError("Paramètres hors limites.")

    taux = round(1 - (residuel / cout) ** (1 / duree), 3) if residuel > 0 else 1 / duree
    valeur = cout
    amort = 0.0
    for p in range(1, periode + 1):
        amort = round(valeur * taux, 2)
        valeur -= amort

    return {"amortissement": amort, "valeur_nette": round(valeur, 2), "taux": round(taux, 4)}


# 69. SYD (amortissement dégressif à taux décroissant)
def formule_syd(v: dict) -> dict:
    cout = float(v["cout"])
    residuel = float(v.get("valeur_residuelle", 0))
    duree = int(v["duree_vie"])
    periode = int(v["periode"])

    if duree <= 0 or periode < 1 or periode > duree:
        raise ValueError("Paramètres hors limites.")

    somme = duree * (duree + 1) / 2
    amort = (cout - residuel) * (duree - periode + 1) / somme

    return {"amortissement": round(amort, 2), "periode": periode}


# ─────────────────────────────────────────────────────────────────────────────
# INGÉNIERIE & MATRICES
# ─────────────────────────────────────────────────────────────────────────────

def _to_matrix(data) -> list[list[float]]:
    """Convertit des données en matrice 2D de float."""
    if not data:
        raise ValueError("Matrice vide.")
    if not isinstance(data[0], list):
        return [[float(x) for x in data]]
    return [[float(x) for x in row] for row in data]


# 70. TRANSPOSE
def formule_transpose(v: dict) -> dict:
    m = _to_matrix(v["matrice"])
    rows, cols = len(m), len(m[0])
    result = [[m[r][c] for r in range(rows)] for c in range(cols)]
    return {"resultat": result, "dimensions": f"{cols}x{rows}"}


# 71. PRODUITMAT (MMULT)
def formule_produitmat(v: dict) -> dict:
    a = _to_matrix(v["matrice_a"])
    b = _to_matrix(v["matrice_b"])
    ra, ca = len(a), len(a[0])
    rb, cb = len(b), len(b[0])

    if ca != rb:
        raise ValueError(f"Dimensions incompatibles : {ra}x{ca} * {rb}x{cb}")

    if ra * cb > 10000:
        raise ValueError("Résultat trop grand (max 10 000 cellules).")

    result = [[sum(a[i][k] * b[k][j] for k in range(ca)) for j in range(cb)] for i in range(ra)]
    result = [[round(x, 8) for x in row] for row in result]
    return {"resultat": result, "dimensions": f"{ra}x{cb}"}


# 72. MATRICE.INVERSE (MINVERSE)
def formule_matrice_inverse(v: dict) -> dict:
    m = _to_matrix(v["matrice"])
    n = len(m)
    if any(len(row) != n for row in m):
        raise ValueError("La matrice doit être carrée.")
    if n > 50:
        raise ValueError("Matrice trop grande (max 50x50).")

    # Gauss-Jordan
    aug = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(m)]

    for col in range(n):
        max_row = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[max_row][col]) < 1e-12:
            raise ValueError("Matrice singulière (non inversible).")
        aug[col], aug[max_row] = aug[max_row], aug[col]
        pivot = aug[col][col]
        aug[col] = [x / pivot for x in aug[col]]
        for row in range(n):
            if row != col:
                factor = aug[row][col]
                aug[row] = [aug[row][j] - factor * aug[col][j] for j in range(2 * n)]

    inverse = [[round(aug[i][n + j], 8) for j in range(n)] for i in range(n)]
    return {"resultat": inverse, "dimensions": f"{n}x{n}"}


# 73. DETERMINANT.MAT (MDETERM)
def formule_determinant(v: dict) -> dict:
    m = _to_matrix(v["matrice"])
    n = len(m)
    if any(len(row) != n for row in m):
        raise ValueError("La matrice doit être carrée.")
    if n > 50:
        raise ValueError("Matrice trop grande (max 50x50).")

    # LU-style with row swaps
    mat = [row[:] for row in m]
    det = 1.0
    for col in range(n):
        max_row = max(range(col, n), key=lambda r: abs(mat[r][col]))
        if abs(mat[max_row][col]) < 1e-12:
            return {"determinant": 0.0}
        if max_row != col:
            mat[col], mat[max_row] = mat[max_row], mat[col]
            det *= -1
        det *= mat[col][col]
        for row in range(col + 1, n):
            factor = mat[row][col] / mat[col][col]
            for j in range(col + 1, n):
                mat[row][j] -= factor * mat[col][j]

    return {"determinant": round(det, 8)}


# 74. FLATTEN (fusion de matrices)
def formule_flatten(v: dict) -> dict:
    data = v["donnees"]

    def _flat(item):
        if isinstance(item, list):
            for sub in item:
                yield from _flat(sub)
        else:
            yield item

    result = list(_flat(data))
    return {"resultat": result, "total": len(result)}


# ─────────────────────────────────────────────────────────────────────────────
# STATISTIQUES DE DÉCISION
# ─────────────────────────────────────────────────────────────────────────────

# 75. COEFFICIENT.CORRELATION (CORREL)
def formule_correlation(v: dict) -> dict:
    x = [float(a) for a in v["x"]]
    y = [float(a) for a in v["y"]]
    n = len(x)
    if n != len(y) or n < 2:
        raise ValueError("x et y doivent avoir la même taille (>= 2).")

    mx, my = sum(x) / n, sum(y) / n
    sxy = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    sxx = sum((xi - mx) ** 2 for xi in x)
    syy = sum((yi - my) ** 2 for yi in y)

    if sxx == 0 or syy == 0:
        raise ValueError("Variance nulle — corrélation indéfinie.")

    r = sxy / math.sqrt(sxx * syy)
    return {"correlation": round(r, 8), "r_carre": round(r ** 2, 8), "n": n}


# 76. PENTE (SLOPE)
def formule_pente(v: dict) -> dict:
    x = [float(a) for a in v["x"]]
    y = [float(a) for a in v["y"]]
    n = len(x)
    if n != len(y) or n < 2:
        raise ValueError("x et y doivent avoir la même taille (>= 2).")

    mx, my = sum(x) / n, sum(y) / n
    sxy = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    sxx = sum((xi - mx) ** 2 for xi in x)

    if sxx == 0:
        raise ValueError("Variance x nulle.")

    return {"pente": round(sxy / sxx, 8)}


# 77. ORDONNEE.ORIGINE (INTERCEPT)
def formule_ordonnee_origine(v: dict) -> dict:
    x = [float(a) for a in v["x"]]
    y = [float(a) for a in v["y"]]
    n = len(x)
    if n != len(y) or n < 2:
        raise ValueError("x et y doivent avoir la même taille (>= 2).")

    mx, my = sum(x) / n, sum(y) / n
    sxy = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    sxx = sum((xi - mx) ** 2 for xi in x)

    if sxx == 0:
        raise ValueError("Variance x nulle.")

    pente = sxy / sxx
    intercept = my - pente * mx
    return {"ordonnee_origine": round(intercept, 8)}


# 78. ECART.TYPE.P (population)
def formule_ecart_type_p(v: dict) -> dict:
    vals = [float(x) for x in v["valeurs"]]
    n = len(vals)
    if n == 0:
        raise ValueError("Liste vide.")
    moy = sum(vals) / n
    variance = sum((x - moy) ** 2 for x in vals) / n
    return {"ecart_type": round(math.sqrt(variance), 8), "variance": round(variance, 8), "n": n}


# 79. ECART.TYPE.S (échantillon)
def formule_ecart_type_s(v: dict) -> dict:
    vals = [float(x) for x in v["valeurs"]]
    n = len(vals)
    if n < 2:
        raise ValueError("Au moins 2 valeurs requises.")
    moy = sum(vals) / n
    variance = sum((x - moy) ** 2 for x in vals) / (n - 1)
    return {"ecart_type": round(math.sqrt(variance), 8), "variance": round(variance, 8), "n": n}


# 80. QUARTILE
def formule_quartile(v: dict) -> dict:
    vals = sorted(float(x) for x in v["valeurs"])
    n = len(vals)
    if n == 0:
        raise ValueError("Liste vide.")
    q = int(v.get("quartile", 2))
    if q < 0 or q > 4:
        raise ValueError("Quartile doit être entre 0 et 4.")

    k = q * (n - 1) / 4
    f = int(k)
    c = k - f
    if f + 1 < n:
        result = vals[f] + c * (vals[f + 1] - vals[f])
    else:
        result = vals[f]

    labels = {0: "Min", 1: "Q1", 2: "Médiane", 3: "Q3", 4: "Max"}
    return {"valeur": round(result, 8), "quartile": labels.get(q, f"Q{q}")}


# 81. PERCENTILE
def formule_percentile(v: dict) -> dict:
    vals = sorted(float(x) for x in v["valeurs"])
    n = len(vals)
    if n == 0:
        raise ValueError("Liste vide.")
    k = float(v["k"])
    if k < 0 or k > 1:
        raise ValueError("k doit être entre 0 et 1.")

    pos = k * (n - 1)
    f = int(pos)
    c = pos - f
    if f + 1 < n:
        result = vals[f] + c * (vals[f + 1] - vals[f])
    else:
        result = vals[f]

    return {"valeur": round(result, 8), "percentile": round(k * 100, 1)}


# 82. MOYENNE.REDUITE (TRIMMEAN)
def formule_moyenne_reduite(v: dict) -> dict:
    vals = sorted(float(x) for x in v["valeurs"])
    n = len(vals)
    if n == 0:
        raise ValueError("Liste vide.")
    pct = float(v.get("pourcentage", 10)) / 100
    if pct < 0 or pct >= 1:
        raise ValueError("Pourcentage doit être entre 0 et 100.")

    trim_count = int(n * pct / 2)
    trimmed = vals[trim_count:n - trim_count] if trim_count > 0 else vals
    if not trimmed:
        raise ValueError("Trop de valeurs éliminées.")

    return {
        "moyenne_reduite": round(sum(trimmed) / len(trimmed), 8),
        "valeurs_gardees": len(trimmed),
        "valeurs_eliminees": n - len(trimmed),
    }


# ─────────────────────────────────────────────────────────────────────────────
# TRAITEMENT DE TEXTE INDUSTRIEL
# ─────────────────────────────────────────────────────────────────────────────

# 83. REPT
def formule_rept(v: dict) -> dict:
    texte = str(v["texte"])
    nb = int(v["nombre"])
    if nb < 0 or nb > 10000:
        raise ValueError("Nombre de répétitions entre 0 et 10 000.")
    return {"resultat": texte * nb}


# 84. CHERCHE (SEARCH — insensible à la casse)
def formule_cherche(v: dict) -> dict:
    cherche = str(v["texte_cherche"]).lower()
    dans = str(v["texte_source"]).lower()
    debut = int(v.get("position_debut", 1)) - 1

    pos = dans.find(cherche, debut)
    if pos == -1:
        raise ValueError(f"'{v['texte_cherche']}' introuvable.")

    return {"position": pos + 1, "trouve": True}


# 85. REMPLACER (REPLACE)
def formule_remplacer(v: dict) -> dict:
    texte = str(v["texte"])
    debut = int(v["position_debut"]) - 1
    nb_car = int(v["nb_caracteres"])
    nouveau = str(v["nouveau_texte"])

    resultat = texte[:debut] + nouveau + texte[debut + nb_car:]
    return {"resultat": resultat}


# 86. TEXTE.JOIN (TEXTJOIN)
def formule_texte_join(v: dict) -> dict:
    delimiteur = str(v.get("delimiteur", ","))
    ignorer_vides = v.get("ignorer_vides", True)
    textes = v["textes"]

    if not isinstance(textes, list):
        textes = [textes]

    if ignorer_vides:
        textes = [str(t) for t in textes if t is not None and str(t).strip() != ""]
    else:
        textes = [str(t) if t is not None else "" for t in textes]

    return {"resultat": delimiteur.join(textes)}


# 87. VALEUR (VALUE)
def formule_valeur(v: dict) -> dict:
    texte = str(v["texte"]).strip()
    cleaned = texte.replace(" ", "").replace("\u00a0", "")
    for sym in ("€", "$", "£", "¥", "%"):
        cleaned = cleaned.replace(sym, "")

    # Gestion séparateur décimal français
    if "," in cleaned and "." not in cleaned:
        cleaned = cleaned.replace(",", ".")

    nombre = float(cleaned)
    if "%" in texte:
        nombre /= 100

    return {"nombre": nombre}


# 88. CTXT (FIXED)
def formule_ctxt(v: dict) -> dict:
    nombre = float(v["nombre"])
    decimales = int(v.get("decimales", 2))
    pas_separateur = v.get("pas_separateur", False)

    formatted = f"{nombre:,.{decimales}f}" if not pas_separateur else f"{nombre:.{decimales}f}"
    return {"resultat": formatted}


# ─────────────────────────────────────────────────────────────────────────────
# FONCTIONS DE BASE DE DONNÉES (D-Functions)
# ─────────────────────────────────────────────────────────────────────────────

def _db_filter(donnees: list[dict], criteres: list[dict]) -> list[dict]:
    """Filtre des enregistrements selon des critères DB."""
    result = []
    for row in donnees:
        match = True
        for c in criteres:
            col = c["colonne"]
            val = c["valeur"]
            cell = row.get(col)
            if cell is None:
                match = False
                break
            if str(cell).lower() != str(val).lower():
                match = False
                break
        if match:
            result.append(row)
    return result


# 89. BDSOMME (DSUM)
def formule_bdsomme(v: dict) -> dict:
    donnees = v["donnees"]
    champ = str(v["champ"])
    criteres = v["criteres"]

    filtre = _db_filter(donnees, criteres)
    total = sum(float(row[champ]) for row in filtre if champ in row)
    return {"somme": round(total, 8), "lignes": len(filtre)}


# 90. BDNB (DCOUNT)
def formule_bdnb(v: dict) -> dict:
    donnees = v["donnees"]
    champ = str(v["champ"])
    criteres = v["criteres"]

    filtre = _db_filter(donnees, criteres)
    count = sum(1 for row in filtre if champ in row and row[champ] is not None)
    return {"count": count}


# 91. BDMAX
def formule_bdmax(v: dict) -> dict:
    donnees = v["donnees"]
    champ = str(v["champ"])
    criteres = v["criteres"]

    filtre = _db_filter(donnees, criteres)
    vals = [float(row[champ]) for row in filtre if champ in row]
    if not vals:
        raise ValueError("Aucune donnée correspondante.")
    return {"max": max(vals), "lignes": len(vals)}


# 92. BDMIN
def formule_bdmin(v: dict) -> dict:
    donnees = v["donnees"]
    champ = str(v["champ"])
    criteres = v["criteres"]

    filtre = _db_filter(donnees, criteres)
    vals = [float(row[champ]) for row in filtre if champ in row]
    if not vals:
        raise ValueError("Aucune donnée correspondante.")
    return {"min": min(vals), "lignes": len(vals)}


# 93. BDMOYENNE
def formule_bdmoyenne(v: dict) -> dict:
    donnees = v["donnees"]
    champ = str(v["champ"])
    criteres = v["criteres"]

    filtre = _db_filter(donnees, criteres)
    vals = [float(row[champ]) for row in filtre if champ in row]
    if not vals:
        raise ValueError("Aucune donnée correspondante.")
    return {"moyenne": round(sum(vals) / len(vals), 8), "lignes": len(vals)}


# ─────────────────────────────────────────────────────────────────────────────
# MANIPULATION AVANCÉE
# ─────────────────────────────────────────────────────────────────────────────

# 94. LAMBDA_RECURSIVE
def formule_lambda_recursive(v: dict) -> dict:
    """Lambda récursive limitée : applique une expression de manière récursive N fois."""
    expression = str(v["expression"])
    valeur_init = float(v["valeur_initiale"])
    iterations = int(v.get("iterations", 10))

    if iterations < 1 or iterations > 1000:
        raise ValueError("Itérations entre 1 et 1 000.")

    # Sécurité : whitelist de tokens
    import math as _math
    safe_names = {"x", "abs", "round", "min", "max", "sqrt", "pow", "log", "log10", "pi", "e"}
    tokens = re.findall(r'[a-zA-Z_]\w*', expression)
    for token in tokens:
        if token not in safe_names:
            raise ValueError(f"Nom non autorisé : '{token}'")

    safe_globals = {"__builtins__": {}, "abs": abs, "round": round, "min": min, "max": max,
                    "sqrt": _math.sqrt, "pow": pow, "log": _math.log, "log10": _math.log10,
                    "pi": _math.pi, "e": _math.e}

    x = valeur_init
    resultats = [x]
    for _ in range(iterations):
        x = eval(expression, safe_globals, {"x": x})  # noqa: S307
        if isinstance(x, float):
            x = round(x, 10)
        resultats.append(x)

    return {"resultat_final": resultats[-1], "iterations": iterations, "historique": resultats[-5:]}


# 95. LET_ADVANCED (optimisation de variables locales multiples)
def formule_let_advanced(v: dict) -> dict:
    variables = v["variables"]  # {"a": 10, "b": 20, ...}
    etapes = v["etapes"]  # [{"nom": "c", "expression": "a + b"}, ...]
    expression_finale = str(v["expression_finale"])

    import math as _math
    safe_globals = {"__builtins__": {}, "abs": abs, "round": round, "min": min, "max": max,
                    "sum": sum, "pow": pow, "sqrt": _math.sqrt, "log": _math.log,
                    "pi": _math.pi, "e": _math.e}

    context = {k: float(val) for k, val in variables.items()}

    for etape in etapes:
        nom = str(etape["nom"])
        expr = str(etape["expression"])
        tokens = re.findall(r'[a-zA-Z_]\w*', expr)
        allowed = set(context.keys()) | {"abs", "round", "min", "max", "sum", "pow", "sqrt", "log", "pi", "e"}
        for t in tokens:
            if t not in allowed:
                raise ValueError(f"Nom non autorisé dans étape : '{t}'")
        context[nom] = eval(expr, safe_globals, context)  # noqa: S307

    tokens = re.findall(r'[a-zA-Z_]\w*', expression_finale)
    allowed = set(context.keys()) | {"abs", "round", "min", "max", "sum", "pow", "sqrt", "log", "pi", "e"}
    for t in tokens:
        if t not in allowed:
            raise ValueError(f"Nom non autorisé dans expression finale : '{t}'")

    resultat = eval(expression_finale, safe_globals, context)  # noqa: S307
    return {
        "resultat": round(resultat, 8) if isinstance(resultat, float) else resultat,
        "variables_calculees": {k: round(v, 8) if isinstance(v, float) else v for k, v in context.items()},
    }


# 96. CHOOSE (CHOISIR)
def formule_choose(v: dict) -> dict:
    index = int(v["index"])
    valeurs = v["valeurs"]
    if index < 1 or index > len(valeurs):
        raise ValueError(f"Index {index} hors limites (1 à {len(valeurs)}).")
    return {"resultat": valeurs[index - 1], "index": index}


# 97. BYROW
def formule_byrow(v: dict) -> dict:
    matrice = v["matrice"]
    operation = str(v["operation"]).lower()

    ops = {
        "somme": lambda row: sum(float(x) for x in row),
        "moyenne": lambda row: sum(float(x) for x in row) / len(row),
        "max": lambda row: max(float(x) for x in row),
        "min": lambda row: min(float(x) for x in row),
        "count": lambda row: len(row),
        "produit": lambda row: math.prod(float(x) for x in row),
    }
    if operation not in ops:
        raise ValueError(f"Opération inconnue : {operation}. Disponibles : {list(ops.keys())}")

    result = [round(ops[operation](row), 8) for row in matrice]
    return {"resultat": result, "lignes": len(result)}


# 98. BYCOL
def formule_bycol(v: dict) -> dict:
    matrice = v["matrice"]
    operation = str(v["operation"]).lower()

    if not matrice:
        raise ValueError("Matrice vide.")

    nb_cols = len(matrice[0])

    ops = {
        "somme": lambda col: sum(col),
        "moyenne": lambda col: sum(col) / len(col),
        "max": lambda col: max(col),
        "min": lambda col: min(col),
        "count": lambda col: len(col),
    }
    if operation not in ops:
        raise ValueError(f"Opération inconnue : {operation}. Disponibles : {list(ops.keys())}")

    result = []
    for c in range(nb_cols):
        col_vals = [float(matrice[r][c]) for r in range(len(matrice))]
        result.append(round(ops[operation](col_vals), 8))

    return {"resultat": result, "colonnes": nb_cols}


# 99. MAKEARRAY
def formule_makearray(v: dict) -> dict:
    lignes = int(v["lignes"])
    colonnes = int(v["colonnes"])
    expression = str(v.get("expression", "row * colonnes + col + 1"))

    if lignes * colonnes > 100000:
        raise ValueError("Tableau trop grand (max 100 000 cellules).")

    import math as _math
    safe_names = {"row", "col", "lignes", "colonnes", "abs", "round", "min", "max",
                  "sqrt", "pow", "log", "pi", "e"}
    tokens = re.findall(r'[a-zA-Z_]\w*', expression)
    for t in tokens:
        if t not in safe_names:
            raise ValueError(f"Nom non autorisé : '{t}'")

    safe_globals = {"__builtins__": {}, "abs": abs, "round": round, "min": min, "max": max,
                    "sqrt": _math.sqrt, "pow": pow, "log": _math.log,
                    "pi": _math.pi, "e": _math.e}

    result = []
    for r in range(lignes):
        row = []
        for c in range(colonnes):
            val = eval(expression, safe_globals, {"row": r, "col": c, "lignes": lignes, "colonnes": colonnes})  # noqa: S307
            row.append(round(val, 8) if isinstance(val, float) else val)
        result.append(row)

    return {"resultat": result, "dimensions": f"{lignes}x{colonnes}"}


# ─────────────────────────────────────────────────────────────────────────────
# UTILITAIRES DATA
# ─────────────────────────────────────────────────────────────────────────────

# 100. ESTERREUR
def formule_esterreur(v: dict) -> dict:
    valeurs = v["valeurs"]
    resultats = []
    for val in valeurs:
        try:
            float(val)
            resultats.append(False)
        except (ValueError, TypeError):
            is_err = val is None or str(val).strip().upper() in (
                "#N/A", "#REF!", "#VALUE!", "#DIV/0!", "#NAME?", "#NULL!", "#NUM!", "ERR", "ERROR", "ERREUR"
            )
            resultats.append(is_err)
    return {"resultats": resultats, "nb_erreurs": sum(resultats)}


# 101. ESTNA
def formule_estna(v: dict) -> dict:
    valeurs = v["valeurs"]
    resultats = []
    for val in valeurs:
        is_na = val is None or str(val).strip().upper() in ("#N/A", "NA", "N/A")
        resultats.append(is_na)
    return {"resultats": resultats, "nb_na": sum(resultats)}


# 102. TYPE
def formule_type_val(v: dict) -> dict:
    valeur = v["valeur"]
    if valeur is None:
        return {"type": 1, "type_nom": "Nombre", "note": "null traité comme 0"}
    if isinstance(valeur, bool):
        return {"type": 4, "type_nom": "Booléen"}
    try:
        float(valeur)
        return {"type": 1, "type_nom": "Nombre"}
    except (ValueError, TypeError):
        pass
    if isinstance(valeur, str):
        if valeur.strip().upper() in ("#N/A", "#REF!", "#VALUE!", "#DIV/0!", "#NAME?"):
            return {"type": 16, "type_nom": "Erreur"}
        return {"type": 2, "type_nom": "Texte"}
    if isinstance(valeur, list):
        return {"type": 64, "type_nom": "Tableau"}
    return {"type": 2, "type_nom": "Texte"}


# 103. COORDONNEES (ADDRESS)
def formule_coordonnees(v: dict) -> dict:
    ligne = int(v["ligne"])
    colonne = int(v["colonne"])
    absolu = int(v.get("type_reference", 1))

    if colonne < 1 or colonne > 16384:
        raise ValueError("Colonne entre 1 et 16384.")
    if ligne < 1 or ligne > 1048576:
        raise ValueError("Ligne entre 1 et 1048576.")

    # Convertir colonne en lettres
    col_str = ""
    c = colonne
    while c > 0:
        c, remainder = divmod(c - 1, 26)
        col_str = chr(65 + remainder) + col_str

    if absolu == 1:
        return {"adresse": f"${col_str}${ligne}"}
    elif absolu == 2:
        return {"adresse": f"{col_str}${ligne}"}
    elif absolu == 3:
        return {"adresse": f"${col_str}{ligne}"}
    else:
        return {"adresse": f"{col_str}{ligne}"}


# 104. INDIRECT.EXT (simulé pour mapping)
def formule_indirect_ext(v: dict) -> dict:
    reference = str(v["reference"])
    donnees = v["donnees"]  # dict ou liste

    parts = reference.replace("[", ".").replace("]", "").split(".")
    current = donnees
    for part in parts:
        if isinstance(current, dict):
            if part in current:
                current = current[part]
            else:
                raise ValueError(f"Clé '{part}' introuvable.")
        elif isinstance(current, list):
            try:
                idx = int(part)
                current = current[idx]
            except (ValueError, IndexError):
                raise ValueError(f"Index '{part}' invalide.")
        else:
            raise ValueError(f"Navigation impossible à '{part}'.")

    return {"resultat": current}


# 105–112: Formules supplémentaires pour compléter les 50

# 105. NBCAR (LEN)
def formule_nbcar(v: dict) -> dict:
    texte = str(v["texte"])
    return {"longueur": len(texte)}


# 106. MAJUSCULE (UPPER)
def formule_majuscule(v: dict) -> dict:
    texte = str(v["texte"])
    return {"resultat": texte.upper()}


# 107. MINUSCULE (LOWER)
def formule_minuscule(v: dict) -> dict:
    texte = str(v["texte"])
    return {"resultat": texte.lower()}


# 108. CNUM (N)
def formule_cnum(v: dict) -> dict:
    valeur = v["valeur"]
    if isinstance(valeur, bool):
        return {"nombre": 1 if valeur else 0}
    try:
        return {"nombre": float(valeur)}
    except (ValueError, TypeError):
        return {"nombre": 0}


# 109. ABS
def formule_abs_val(v: dict) -> dict:
    nombre = float(v["nombre"])
    return {"resultat": abs(nombre)}


# 110. MOD
def formule_mod(v: dict) -> dict:
    nombre = float(v["nombre"])
    diviseur = float(v["diviseur"])
    if diviseur == 0:
        raise ValueError("Division par zéro.")
    return {"resultat": round(nombre % diviseur, 8)}


# 111. PUISSANCE (POWER)
def formule_puissance(v: dict) -> dict:
    base = float(v["base"])
    exposant = float(v["exposant"])
    return {"resultat": round(base ** exposant, 8)}


# 112. PLAFOND / PLANCHER (CEILING / FLOOR avec incrément)
def formule_plafond_plancher(v: dict) -> dict:
    nombre = float(v["nombre"])
    increment = float(v.get("increment", 1))

    if increment == 0:
        raise ValueError("Incrément ne peut pas être 0.")

    plafond = math.ceil(nombre / increment) * increment
    plancher = math.floor(nombre / increment) * increment

    return {
        "plafond": round(plafond, 8),
        "plancher": round(plancher, 8),
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
    # v3 — Statistiques & Performance
    "max_si_ens": formule_max_si_ens,
    "min_si_ens": formule_min_si_ens,
    "rang_egal": formule_rang_egal,
    "mediane": formule_mediane,
    "agregat": formule_agregat,
    # v3 — Finance High-Ticket
    "taux": formule_taux,
    "npm": formule_npm,
    "vc": formule_vc,
    "va": formule_va,
    "fraction_annee": formule_fraction_annee,
    # v3 — Manipulation de Données
    "choisir_lignes": formule_choisir_lignes,
    "prendre": formule_prendre,
    "exclure": formule_exclure,
    "developper": formule_developper,
    "fractionner_texte": formule_fractionner_texte,
    "unicode_car": formule_unicode_car,
    # v3 — Logique & Validation
    "exact": formule_exact,
    "estnum": formule_estnum,
    "esttexte": formule_esttexte,
    "changer": formule_changer,
    "rechercheh": formule_rechercheh,
    # v3 — Analyse & Prédiction
    "prevision": formule_prevision,
    "frequence": formule_frequence,
    "alea_entre_bornes": formule_alea_entre_bornes,
    # v3 — Structure & Tableaux
    "scan_map_reduce": formule_scan_map_reduce,
    "danscol": formule_danscol,
    "dansligne": formule_dansligne,
    "wraprows_wrapcols": formule_wraprows_wrapcols,
    "assemb_h": formule_assemb_h,
    "valeurnomb": formule_valeurnomb,
    "recherche_v": formule_recherche_v,
    # v4 — Audit & Amortissements
    "intper": formule_intper,
    "princper": formule_princper,
    "cumul_inter": formule_cumul_inter,
    "cumul_princ": formule_cumul_princ,
    "amorl": formule_amorl,
    "amordegr": formule_amordegr,
    "syd": formule_syd,
    # v4 — Ingénierie & Matrices
    "transpose": formule_transpose,
    "produitmat": formule_produitmat,
    "matrice_inverse": formule_matrice_inverse,
    "determinant": formule_determinant,
    "flatten": formule_flatten,
    # v4 — Statistiques de Décision
    "correlation": formule_correlation,
    "pente": formule_pente,
    "ordonnee_origine": formule_ordonnee_origine,
    "ecart_type_p": formule_ecart_type_p,
    "ecart_type_s": formule_ecart_type_s,
    "quartile": formule_quartile,
    "percentile": formule_percentile,
    "moyenne_reduite": formule_moyenne_reduite,
    # v4 — Texte Industriel
    "rept": formule_rept,
    "cherche": formule_cherche,
    "remplacer_texte": formule_remplacer,
    "texte_join": formule_texte_join,
    "valeur_texte": formule_valeur,
    "ctxt": formule_ctxt,
    # v4 — D-Functions
    "bdsomme": formule_bdsomme,
    "bdnb": formule_bdnb,
    "bdmax": formule_bdmax,
    "bdmin": formule_bdmin,
    "bdmoyenne": formule_bdmoyenne,
    # v4 — Manipulation Avancée
    "lambda_recursive": formule_lambda_recursive,
    "let_advanced": formule_let_advanced,
    "choose": formule_choose,
    "byrow": formule_byrow,
    "bycol": formule_bycol,
    "makearray": formule_makearray,
    # v4 — Utilitaires Data
    "esterreur": formule_esterreur,
    "estna": formule_estna,
    "type_val": formule_type_val,
    "coordonnees": formule_coordonnees,
    "indirect_ext": formule_indirect_ext,
    "nbcar": formule_nbcar,
    "majuscule": formule_majuscule,
    "minuscule": formule_minuscule,
    "cnum": formule_cnum,
    "abs_val": formule_abs_val,
    "mod_val": formule_mod,
    "puissance": formule_puissance,
    "plafond_plancher": formule_plafond_plancher,
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

    # ── v3 — Statistiques & Performance ────────────────────────────────────
    "max_si_ens": {
        "name": "MAX.SI.ENS (MAXIFS)",
        "description": "Renvoie la valeur maximale parmi les cellules correspondant à plusieurs critères",
        "category": "Statistiques",
        "variables": [
            {"name": "donnees", "label": "Données (table JSON)", "type": "json",
             "required": True,
             "placeholder": '[{"dept":"Ventes","trimestre":"T1","ca":120000}]'},
            {"name": "colonne_valeur", "label": "Colonne à évaluer", "type": "string",
             "required": True, "placeholder": "ca"},
            {"name": "criteres", "label": "Critères (JSON)", "type": "json",
             "required": True,
             "placeholder": '[{"colonne":"dept","valeur":"Ventes"}]'},
        ],
    },
    "min_si_ens": {
        "name": "MIN.SI.ENS (MINIFS)",
        "description": "Renvoie la valeur minimale parmi les cellules correspondant à plusieurs critères",
        "category": "Statistiques",
        "variables": [
            {"name": "donnees", "label": "Données (table JSON)", "type": "json",
             "required": True,
             "placeholder": '[{"dept":"RH","trimestre":"T2","ca":45000}]'},
            {"name": "colonne_valeur", "label": "Colonne à évaluer", "type": "string",
             "required": True, "placeholder": "ca"},
            {"name": "criteres", "label": "Critères (JSON)", "type": "json",
             "required": True,
             "placeholder": '[{"colonne":"dept","valeur":"RH"}]'},
        ],
    },
    "rang_egal": {
        "name": "RANG.EGAL (RANK.EQ)",
        "description": "Renvoie le rang d'un nombre dans une série (classement)",
        "category": "Statistiques",
        "variables": [
            {"name": "nombre", "label": "Nombre à classer", "type": "number",
             "required": True, "placeholder": "85"},
            {"name": "valeurs", "label": "Série de valeurs", "type": "number[]",
             "required": True, "placeholder": "95, 85, 70, 60, 90"},
            {"name": "ordre", "label": "Ordre (asc/desc)", "type": "string",
             "required": False, "placeholder": "desc"},
        ],
    },
    "mediane": {
        "name": "MEDIANE (MEDIAN)",
        "description": "Renvoie la valeur médiane d'une série de nombres",
        "category": "Statistiques",
        "variables": [
            {"name": "valeurs", "label": "Valeurs", "type": "number[]",
             "required": True, "placeholder": "12, 7, 3, 14, 9"},
        ],
    },
    "agregat": {
        "name": "AGREGAT (AGGREGATE)",
        "description": "Appliquer une fonction d'agrégation (MOYENNE, SOMME, MAX, etc.) en ignorant les erreurs",
        "category": "Statistiques",
        "variables": [
            {"name": "valeurs", "label": "Valeurs (peut contenir des erreurs)", "type": "json",
             "required": True, "placeholder": '[10, 20, "erreur", 30, 40]'},
            {"name": "fonction", "label": "N° fonction (1=MOY, 4=MAX, 5=MIN, 9=SOMME)", "type": "number",
             "required": True, "placeholder": "9"},
            {"name": "ignorer_erreurs", "label": "Ignorer les erreurs (true/false)", "type": "string",
             "required": False, "placeholder": "true"},
        ],
    },

    # ── v3 — Finance High-Ticket ──────────────────────────────────────────
    "taux": {
        "name": "TAUX (RATE)",
        "description": "Calculer le taux d'intérêt par période d'un emprunt (Newton-Raphson, précision bancaire)",
        "category": "Finance",
        "variables": [
            {"name": "nb_periodes", "label": "Nombre de mensualités", "type": "number",
             "required": True, "placeholder": "240"},
            {"name": "mensualite", "label": "Mensualité (€)", "type": "number",
             "required": True, "placeholder": "-1319.91"},
            {"name": "valeur_actuelle", "label": "Montant emprunté (€)", "type": "number",
             "required": True, "placeholder": "200000"},
            {"name": "valeur_future", "label": "Valeur future (€)", "type": "number",
             "required": False, "placeholder": "0"},
            {"name": "debut_periode", "label": "Paiement début de période (0/1)", "type": "number",
             "required": False, "placeholder": "0"},
            {"name": "estimation", "label": "Estimation initiale (%)", "type": "number",
             "required": False, "placeholder": "1"},
        ],
    },
    "npm": {
        "name": "NPM (NPER)",
        "description": "Calculer le nombre de périodes nécessaires pour rembourser un emprunt",
        "category": "Finance",
        "variables": [
            {"name": "taux_periodique", "label": "Taux par période (%)", "type": "number",
             "required": True, "placeholder": "0.5"},
            {"name": "mensualite", "label": "Mensualité (€)", "type": "number",
             "required": True, "placeholder": "-1500"},
            {"name": "valeur_actuelle", "label": "Montant emprunté (€)", "type": "number",
             "required": True, "placeholder": "200000"},
            {"name": "valeur_future", "label": "Valeur future (€)", "type": "number",
             "required": False, "placeholder": "0"},
        ],
    },
    "vc": {
        "name": "VC (FV)",
        "description": "Calculer la valeur future d'un investissement à versements périodiques constants",
        "category": "Finance",
        "variables": [
            {"name": "taux_periodique", "label": "Taux par période (%)", "type": "number",
             "required": True, "placeholder": "0.5"},
            {"name": "nb_periodes", "label": "Nombre de périodes", "type": "number",
             "required": True, "placeholder": "120"},
            {"name": "mensualite", "label": "Versement périodique (€)", "type": "number",
             "required": False, "placeholder": "-500"},
            {"name": "valeur_actuelle", "label": "Valeur initiale (€)", "type": "number",
             "required": False, "placeholder": "-10000"},
            {"name": "debut_periode", "label": "Paiement début de période (0/1)", "type": "number",
             "required": False, "placeholder": "0"},
        ],
    },
    "va": {
        "name": "VA (PV)",
        "description": "Calculer la valeur actuelle d'un investissement (flux futurs actualisés)",
        "category": "Finance",
        "variables": [
            {"name": "taux_periodique", "label": "Taux par période (%)", "type": "number",
             "required": True, "placeholder": "0.5"},
            {"name": "nb_periodes", "label": "Nombre de périodes", "type": "number",
             "required": True, "placeholder": "120"},
            {"name": "mensualite", "label": "Versement périodique (€)", "type": "number",
             "required": False, "placeholder": "-500"},
            {"name": "valeur_future", "label": "Valeur future (€)", "type": "number",
             "required": False, "placeholder": "0"},
            {"name": "debut_periode", "label": "Paiement début de période (0/1)", "type": "number",
             "required": False, "placeholder": "0"},
        ],
    },
    "fraction_annee": {
        "name": "FRACTION.ANNEE (YEARFRAC)",
        "description": "Calculer la fraction d'année entre deux dates (conventions bancaires US30/360, Actual/Actual, etc.)",
        "category": "Finance",
        "variables": [
            {"name": "date_debut", "label": "Date de début", "type": "string",
             "required": True, "placeholder": "2024-01-15"},
            {"name": "date_fin", "label": "Date de fin", "type": "string",
             "required": True, "placeholder": "2024-07-15"},
            {"name": "base", "label": "Convention (0=US30/360, 1=Actual/Actual, 2=Actual/360, 3=Actual/365)", "type": "number",
             "required": False, "placeholder": "1"},
        ],
    },

    # ── v3 — Manipulation de Données ──────────────────────────────────────
    "choisir_lignes": {
        "name": "CHOISIR.LIGNES (CHOOSEROWS)",
        "description": "Extraire des lignes spécifiques d'un tableau par leurs indices (positifs ou négatifs)",
        "category": "Données",
        "variables": [
            {"name": "donnees", "label": "Données (JSON array)", "type": "json",
             "required": True, "placeholder": '["Alice", "Bob", "Charlie", "Diana"]'},
            {"name": "indices", "label": "Indices (1=premier, -1=dernier)", "type": "number[]",
             "required": True, "placeholder": "1, -1"},
        ],
    },
    "prendre": {
        "name": "PRENDRE (TAKE)",
        "description": "Prendre les N premières ou dernières lignes d'un tableau",
        "category": "Données",
        "variables": [
            {"name": "donnees", "label": "Données (JSON array)", "type": "json",
             "required": True, "placeholder": '[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]'},
            {"name": "nb_lignes", "label": "Nombre de lignes (négatif = depuis la fin)", "type": "number",
             "required": True, "placeholder": "3"},
        ],
    },
    "exclure": {
        "name": "EXCLURE (DROP)",
        "description": "Exclure les N premières ou dernières lignes d'un tableau",
        "category": "Données",
        "variables": [
            {"name": "donnees", "label": "Données (JSON array)", "type": "json",
             "required": True, "placeholder": '[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]'},
            {"name": "nb_lignes", "label": "Lignes à exclure (négatif = depuis la fin)", "type": "number",
             "required": True, "placeholder": "2"},
        ],
    },
    "developper": {
        "name": "DÉVELOPPER (EXPAND)",
        "description": "Étendre un tableau à un nombre de lignes donné en remplissant avec une valeur par défaut",
        "category": "Données",
        "variables": [
            {"name": "donnees", "label": "Données (JSON array)", "type": "json",
             "required": True, "placeholder": '["A", "B", "C"]'},
            {"name": "nb_lignes", "label": "Nombre total de lignes", "type": "number",
             "required": True, "placeholder": "6"},
            {"name": "valeur_defaut", "label": "Valeur de remplissage", "type": "string",
             "required": False, "placeholder": "N/A"},
        ],
    },
    "fractionner_texte": {
        "name": "FRACTIONNER.TEXTE (TEXTSPLIT)",
        "description": "Découper un texte en colonnes et/ou lignes selon des délimiteurs",
        "category": "Texte",
        "variables": [
            {"name": "texte", "label": "Texte à fractionner", "type": "string",
             "required": True, "placeholder": "Jean,Dupont,Paris"},
            {"name": "delimiteur_col", "label": "Délimiteur de colonnes", "type": "string",
             "required": False, "placeholder": ","},
            {"name": "delimiteur_ligne", "label": "Délimiteur de lignes", "type": "string",
             "required": False, "placeholder": ";"},
        ],
    },
    "unicode_car": {
        "name": "UNICODE / CAR",
        "description": "Convertir un caractère en code Unicode ou un code en caractère",
        "category": "Texte",
        "variables": [
            {"name": "caractere", "label": "Caractère → code", "type": "string",
             "required": False, "placeholder": "A"},
            {"name": "code", "label": "Code → caractère", "type": "number",
             "required": False, "placeholder": "65"},
        ],
    },

    # ── v3 — Logique & Validation ─────────────────────────────────────────
    "exact": {
        "name": "EXACT",
        "description": "Comparer deux textes de manière stricte (sensible à la casse)",
        "category": "Logique",
        "variables": [
            {"name": "texte1", "label": "Texte 1", "type": "string",
             "required": True, "placeholder": "Excel"},
            {"name": "texte2", "label": "Texte 2", "type": "string",
             "required": True, "placeholder": "excel"},
        ],
    },
    "estnum": {
        "name": "ESTNUM (ISNUMBER)",
        "description": "Vérifier quelles valeurs sont numériques dans une liste",
        "category": "Logique",
        "variables": [
            {"name": "valeurs", "label": "Valeurs à tester", "type": "json",
             "required": True, "placeholder": '[42, "texte", 3.14, null, "100"]'},
        ],
    },
    "esttexte": {
        "name": "ESTTEXTE (ISTEXT)",
        "description": "Vérifier quelles valeurs sont du texte (non numérique) dans une liste",
        "category": "Logique",
        "variables": [
            {"name": "valeurs", "label": "Valeurs à tester", "type": "json",
             "required": True, "placeholder": '["Paris", 42, "hello", 3.14]'},
        ],
    },
    "changer": {
        "name": "CHANGER (SWITCH)",
        "description": "Évaluer une expression et renvoyer un résultat selon le premier cas correspondant",
        "category": "Logique",
        "variables": [
            {"name": "expression", "label": "Expression à évaluer", "type": "string",
             "required": True, "placeholder": "B"},
            {"name": "cas", "label": "Cas (JSON)", "type": "json",
             "required": True,
             "placeholder": '[{"valeur":"A","resultat":"Alpha"},{"valeur":"B","resultat":"Beta"}]'},
            {"name": "defaut", "label": "Valeur par défaut", "type": "string",
             "required": False, "placeholder": "Inconnu"},
        ],
    },
    "rechercheh": {
        "name": "RECHERCHEH (HLOOKUP)",
        "description": "Recherche horizontale dans un tableau (chercher dans les en-têtes, retourner une ligne)",
        "category": "Recherche",
        "variables": [
            {"name": "valeur_cherchee", "label": "Valeur cherchée", "type": "string",
             "required": True, "placeholder": "Mars"},
            {"name": "en_tetes", "label": "En-têtes (première ligne)", "type": "json",
             "required": True, "placeholder": '["Janvier","Février","Mars","Avril"]'},
            {"name": "donnees", "label": "Lignes de données (JSON)", "type": "json",
             "required": True, "placeholder": '[[100, 200, 350, 400], [50, 80, 120, 150]]'},
            {"name": "ligne_retour", "label": "Ligne de retour (1=première)", "type": "number",
             "required": False, "placeholder": "1"},
        ],
    },

    # ── v3 — Analyse & Prédiction ─────────────────────────────────────────
    "prevision": {
        "name": "PREVISION.ETS (FORECAST)",
        "description": "Prédire une valeur par régression linéaire (avec R² et pente)",
        "category": "Analyse",
        "variables": [
            {"name": "x_cible", "label": "Valeur X à prédire", "type": "number",
             "required": True, "placeholder": "13"},
            {"name": "x_connus", "label": "Valeurs X connues", "type": "number[]",
             "required": True, "placeholder": "1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12"},
            {"name": "y_connus", "label": "Valeurs Y connues", "type": "number[]",
             "required": True, "placeholder": "100, 120, 135, 160, 180, 200, 215, 240, 260, 280, 300, 320"},
        ],
    },
    "frequence": {
        "name": "FREQUENCE (FREQUENCY)",
        "description": "Calculer la distribution de fréquence d'un jeu de données par tranches",
        "category": "Analyse",
        "variables": [
            {"name": "donnees", "label": "Données", "type": "number[]",
             "required": True, "placeholder": "45, 72, 38, 91, 55, 67, 83, 29, 60, 74"},
            {"name": "bornes", "label": "Bornes des tranches", "type": "number[]",
             "required": True, "placeholder": "30, 50, 70, 90"},
        ],
    },
    "alea_entre_bornes": {
        "name": "ALEA.ENTRE.BORNES (RANDBETWEEN)",
        "description": "Générer un ou plusieurs nombres entiers aléatoires entre deux bornes",
        "category": "Analyse",
        "variables": [
            {"name": "borne_inf", "label": "Borne inférieure", "type": "number",
             "required": True, "placeholder": "1"},
            {"name": "borne_sup", "label": "Borne supérieure", "type": "number",
             "required": True, "placeholder": "100"},
            {"name": "nombre", "label": "Nombre de valeurs à générer", "type": "number",
             "required": False, "placeholder": "1"},
        ],
    },

    # ── v3 — Structure & Tableaux ─────────────────────────────────────────
    "scan_map_reduce": {
        "name": "SCAN / MAP / REDUCE",
        "description": "Appliquer une opération sur chaque élément (MAP), cumuler (SCAN) ou réduire (REDUCE) une liste",
        "category": "Tableaux Dynamiques",
        "variables": [
            {"name": "valeurs", "label": "Valeurs", "type": "json",
             "required": True, "placeholder": '[10, 20, 30, 40, 50]'},
            {"name": "operation", "label": "Opération", "type": "string",
             "required": True, "placeholder": "somme_cumul"},
        ],
    },
    "danscol": {
        "name": "DANSCOL (TOCOL)",
        "description": "Aplatir un tableau 2D en une seule colonne",
        "category": "Tableaux Dynamiques",
        "variables": [
            {"name": "donnees", "label": "Données (2D ou nested)", "type": "json",
             "required": True, "placeholder": '[[1,2,3],[4,5,6]]'},
        ],
    },
    "dansligne": {
        "name": "DANSLIGNE (TOROW)",
        "description": "Aplatir un tableau 2D en une seule ligne",
        "category": "Tableaux Dynamiques",
        "variables": [
            {"name": "donnees", "label": "Données (2D ou nested)", "type": "json",
             "required": True, "placeholder": '[[1,2,3],[4,5,6]]'},
        ],
    },
    "wraprows_wrapcols": {
        "name": "WRAPROWS / WRAPCOLS",
        "description": "Réorganiser un vecteur plat en grille 2D (par lignes ou par colonnes)",
        "category": "Tableaux Dynamiques",
        "variables": [
            {"name": "valeurs", "label": "Valeurs à réorganiser", "type": "json",
             "required": True, "placeholder": '[1,2,3,4,5,6,7,8,9]'},
            {"name": "taille", "label": "Taille (nb éléments par ligne/colonne)", "type": "number",
             "required": True, "placeholder": "3"},
            {"name": "mode", "label": "Mode (rows/cols)", "type": "string",
             "required": False, "placeholder": "rows"},
            {"name": "valeur_pad", "label": "Valeur de remplissage", "type": "string",
             "required": False, "placeholder": ""},
        ],
    },
    "assemb_h": {
        "name": "ASSEMB.H (HSTACK)",
        "description": "Assembler horizontalement plusieurs tableaux côte à côte",
        "category": "Tableaux Dynamiques",
        "variables": [
            {"name": "tableaux", "label": "Tableaux à assembler (JSON)", "type": "json",
             "required": True,
             "placeholder": '[["A","B","C"], [1,2,3]]'},
        ],
    },
    "valeurnomb": {
        "name": "VALEURNOMB (NUMBERVALUE)",
        "description": "Convertir un texte formaté en nombre (gère les séparateurs et symboles monétaires)",
        "category": "Texte",
        "variables": [
            {"name": "texte", "label": "Texte à convertir", "type": "string",
             "required": True, "placeholder": "1 234,56 €"},
            {"name": "sep_decimal", "label": "Séparateur décimal", "type": "string",
             "required": False, "placeholder": ","},
            {"name": "sep_milliers", "label": "Séparateur de milliers", "type": "string",
             "required": False, "placeholder": " "},
        ],
    },
    "recherche_v": {
        "name": "RECHERCHE (LOOKUP)",
        "description": "Recherche vectorielle : trouver la plus grande valeur ≤ à la cible dans un vecteur trié",
        "category": "Recherche",
        "variables": [
            {"name": "valeur_cherchee", "label": "Valeur cherchée", "type": "number",
             "required": True, "placeholder": "75"},
            {"name": "vecteur_recherche", "label": "Vecteur de recherche (trié)", "type": "number[]",
             "required": True, "placeholder": "10, 20, 50, 80, 100"},
            {"name": "vecteur_retour", "label": "Vecteur de retour", "type": "json",
             "required": True, "placeholder": '["F","E","D","C","B"]'},
        ],
    },

    # ── v4 — Audit & Amortissements ───────────────────────────────────────
    "intper": {
        "name": "INTPER (IPMT)", "description": "Intérêts payés pour une période spécifique d'un emprunt",
        "category": "Audit Financier",
        "variables": [
            {"name": "taux_periodique", "label": "Taux par période (%)", "type": "number", "required": True, "placeholder": "0.5"},
            {"name": "periode", "label": "Période", "type": "number", "required": True, "placeholder": "1"},
            {"name": "nb_periodes", "label": "Nombre de périodes", "type": "number", "required": True, "placeholder": "240"},
            {"name": "valeur_actuelle", "label": "Montant emprunté (€)", "type": "number", "required": True, "placeholder": "200000"},
            {"name": "valeur_future", "label": "Valeur future (€)", "type": "number", "required": False, "placeholder": "0"},
            {"name": "debut_periode", "label": "Début de période (0/1)", "type": "number", "required": False, "placeholder": "0"},
        ],
    },
    "princper": {
        "name": "PRINCPER (PPMT)", "description": "Part du principal remboursé pour une période spécifique",
        "category": "Audit Financier",
        "variables": [
            {"name": "taux_periodique", "label": "Taux par période (%)", "type": "number", "required": True, "placeholder": "0.5"},
            {"name": "periode", "label": "Période", "type": "number", "required": True, "placeholder": "1"},
            {"name": "nb_periodes", "label": "Nombre de périodes", "type": "number", "required": True, "placeholder": "240"},
            {"name": "valeur_actuelle", "label": "Montant emprunté (€)", "type": "number", "required": True, "placeholder": "200000"},
            {"name": "valeur_future", "label": "Valeur future (€)", "type": "number", "required": False, "placeholder": "0"},
            {"name": "debut_periode", "label": "Début de période (0/1)", "type": "number", "required": False, "placeholder": "0"},
        ],
    },
    "cumul_inter": {
        "name": "CUMUL.INTER (CUMIPMT)", "description": "Cumul des intérêts payés entre deux périodes",
        "category": "Audit Financier",
        "variables": [
            {"name": "taux_periodique", "label": "Taux par période (%)", "type": "number", "required": True, "placeholder": "0.5"},
            {"name": "nb_periodes", "label": "Nombre de périodes", "type": "number", "required": True, "placeholder": "240"},
            {"name": "valeur_actuelle", "label": "Montant emprunté (€)", "type": "number", "required": True, "placeholder": "200000"},
            {"name": "periode_debut", "label": "Période début", "type": "number", "required": True, "placeholder": "1"},
            {"name": "periode_fin", "label": "Période fin", "type": "number", "required": True, "placeholder": "12"},
        ],
    },
    "cumul_princ": {
        "name": "CUMUL.PRINC (CUMPRINC)", "description": "Cumul du principal remboursé entre deux périodes",
        "category": "Audit Financier",
        "variables": [
            {"name": "taux_periodique", "label": "Taux par période (%)", "type": "number", "required": True, "placeholder": "0.5"},
            {"name": "nb_periodes", "label": "Nombre de périodes", "type": "number", "required": True, "placeholder": "240"},
            {"name": "valeur_actuelle", "label": "Montant emprunté (€)", "type": "number", "required": True, "placeholder": "200000"},
            {"name": "periode_debut", "label": "Période début", "type": "number", "required": True, "placeholder": "1"},
            {"name": "periode_fin", "label": "Période fin", "type": "number", "required": True, "placeholder": "12"},
        ],
    },
    "amorl": {
        "name": "AMORL (SLN)", "description": "Amortissement linéaire annuel d'un actif",
        "category": "Audit Financier",
        "variables": [
            {"name": "cout", "label": "Coût d'acquisition (€)", "type": "number", "required": True, "placeholder": "100000"},
            {"name": "valeur_residuelle", "label": "Valeur résiduelle (€)", "type": "number", "required": False, "placeholder": "10000"},
            {"name": "duree_vie", "label": "Durée de vie (années)", "type": "number", "required": True, "placeholder": "10"},
        ],
    },
    "amordegr": {
        "name": "AMORDEGR (DB)", "description": "Amortissement dégressif d'un actif pour une période donnée",
        "category": "Audit Financier",
        "variables": [
            {"name": "cout", "label": "Coût d'acquisition (€)", "type": "number", "required": True, "placeholder": "100000"},
            {"name": "valeur_residuelle", "label": "Valeur résiduelle (€)", "type": "number", "required": False, "placeholder": "10000"},
            {"name": "duree_vie", "label": "Durée de vie (années)", "type": "number", "required": True, "placeholder": "10"},
            {"name": "periode", "label": "Période", "type": "number", "required": True, "placeholder": "1"},
        ],
    },
    "syd": {
        "name": "SYD", "description": "Amortissement dégressif à somme des années (Sum-of-Years' Digits)",
        "category": "Audit Financier",
        "variables": [
            {"name": "cout", "label": "Coût d'acquisition (€)", "type": "number", "required": True, "placeholder": "100000"},
            {"name": "valeur_residuelle", "label": "Valeur résiduelle (€)", "type": "number", "required": False, "placeholder": "10000"},
            {"name": "duree_vie", "label": "Durée de vie (années)", "type": "number", "required": True, "placeholder": "10"},
            {"name": "periode", "label": "Période", "type": "number", "required": True, "placeholder": "1"},
        ],
    },

    # ── v4 — Ingénierie & Matrices ────────────────────────────────────────
    "transpose": {
        "name": "TRANSPOSE", "description": "Transposer une matrice (lignes ↔ colonnes)",
        "category": "Ingénierie",
        "variables": [
            {"name": "matrice", "label": "Matrice (JSON 2D)", "type": "json", "required": True, "placeholder": "[[1,2,3],[4,5,6]]"},
        ],
    },
    "produitmat": {
        "name": "PRODUITMAT (MMULT)", "description": "Multiplier deux matrices (produit matriciel)",
        "category": "Ingénierie",
        "variables": [
            {"name": "matrice_a", "label": "Matrice A (JSON 2D)", "type": "json", "required": True, "placeholder": "[[1,2],[3,4]]"},
            {"name": "matrice_b", "label": "Matrice B (JSON 2D)", "type": "json", "required": True, "placeholder": "[[5,6],[7,8]]"},
        ],
    },
    "matrice_inverse": {
        "name": "MATRICE.INVERSE (MINVERSE)", "description": "Calculer l'inverse d'une matrice carrée (Gauss-Jordan)",
        "category": "Ingénierie",
        "variables": [
            {"name": "matrice", "label": "Matrice carrée (JSON 2D)", "type": "json", "required": True, "placeholder": "[[4,7],[2,6]]"},
        ],
    },
    "determinant": {
        "name": "DETERMINANT.MAT (MDETERM)", "description": "Calculer le déterminant d'une matrice carrée",
        "category": "Ingénierie",
        "variables": [
            {"name": "matrice", "label": "Matrice carrée (JSON 2D)", "type": "json", "required": True, "placeholder": "[[1,2],[3,4]]"},
        ],
    },
    "flatten": {
        "name": "FLATTEN", "description": "Aplatir une structure imbriquée en un vecteur plat",
        "category": "Ingénierie",
        "variables": [
            {"name": "donnees", "label": "Données imbriquées (JSON)", "type": "json", "required": True, "placeholder": "[[1,[2,3]],[4,5]]"},
        ],
    },

    # ── v4 — Statistiques de Décision ─────────────────────────────────────
    "correlation": {
        "name": "COEFFICIENT.CORRELATION (CORREL)", "description": "Coefficient de corrélation de Pearson entre deux séries",
        "category": "Statistiques Avancées",
        "variables": [
            {"name": "x", "label": "Valeurs X", "type": "number[]", "required": True, "placeholder": "1, 2, 3, 4, 5"},
            {"name": "y", "label": "Valeurs Y", "type": "number[]", "required": True, "placeholder": "2, 4, 5, 4, 5"},
        ],
    },
    "pente": {
        "name": "PENTE (SLOPE)", "description": "Pente de la droite de régression linéaire",
        "category": "Statistiques Avancées",
        "variables": [
            {"name": "x", "label": "Valeurs X", "type": "number[]", "required": True, "placeholder": "1, 2, 3, 4, 5"},
            {"name": "y", "label": "Valeurs Y", "type": "number[]", "required": True, "placeholder": "2, 4, 5, 4, 5"},
        ],
    },
    "ordonnee_origine": {
        "name": "ORDONNEE.ORIGINE (INTERCEPT)", "description": "Ordonnée à l'origine de la droite de régression",
        "category": "Statistiques Avancées",
        "variables": [
            {"name": "x", "label": "Valeurs X", "type": "number[]", "required": True, "placeholder": "1, 2, 3, 4, 5"},
            {"name": "y", "label": "Valeurs Y", "type": "number[]", "required": True, "placeholder": "2, 4, 5, 4, 5"},
        ],
    },
    "ecart_type_p": {
        "name": "ECART.TYPE.P", "description": "Écart-type de la population entière",
        "category": "Statistiques Avancées",
        "variables": [
            {"name": "valeurs", "label": "Valeurs", "type": "number[]", "required": True, "placeholder": "10, 20, 30, 40, 50"},
        ],
    },
    "ecart_type_s": {
        "name": "ECART.TYPE.S", "description": "Écart-type d'un échantillon (avec correction de Bessel)",
        "category": "Statistiques Avancées",
        "variables": [
            {"name": "valeurs", "label": "Valeurs", "type": "number[]", "required": True, "placeholder": "10, 20, 30, 40, 50"},
        ],
    },
    "quartile": {
        "name": "QUARTILE", "description": "Calculer un quartile (Q0=Min, Q1, Q2=Médiane, Q3, Q4=Max)",
        "category": "Statistiques Avancées",
        "variables": [
            {"name": "valeurs", "label": "Valeurs", "type": "number[]", "required": True, "placeholder": "10, 20, 30, 40, 50, 60, 70, 80, 90, 100"},
            {"name": "quartile", "label": "Quartile (0-4)", "type": "number", "required": False, "placeholder": "2"},
        ],
    },
    "percentile": {
        "name": "PERCENTILE", "description": "Calculer le k-ième percentile d'une série (k entre 0 et 1)",
        "category": "Statistiques Avancées",
        "variables": [
            {"name": "valeurs", "label": "Valeurs", "type": "number[]", "required": True, "placeholder": "10, 20, 30, 40, 50, 60, 70, 80, 90, 100"},
            {"name": "k", "label": "Percentile (0 à 1)", "type": "number", "required": True, "placeholder": "0.75"},
        ],
    },
    "moyenne_reduite": {
        "name": "MOYENNE.REDUITE (TRIMMEAN)", "description": "Moyenne en excluant un pourcentage de valeurs extrêmes",
        "category": "Statistiques Avancées",
        "variables": [
            {"name": "valeurs", "label": "Valeurs", "type": "number[]", "required": True, "placeholder": "1, 2, 3, 4, 5, 100"},
            {"name": "pourcentage", "label": "% à exclure", "type": "number", "required": False, "placeholder": "20"},
        ],
    },

    # ── v4 — Texte Industriel ─────────────────────────────────────────────
    "rept": {
        "name": "REPT", "description": "Répéter un texte N fois",
        "category": "Texte",
        "variables": [
            {"name": "texte", "label": "Texte", "type": "string", "required": True, "placeholder": "AB"},
            {"name": "nombre", "label": "Nombre de répétitions", "type": "number", "required": True, "placeholder": "5"},
        ],
    },
    "cherche": {
        "name": "CHERCHE (SEARCH)", "description": "Trouver la position d'un texte dans un autre (insensible à la casse)",
        "category": "Texte",
        "variables": [
            {"name": "texte_cherche", "label": "Texte à chercher", "type": "string", "required": True, "placeholder": "monde"},
            {"name": "texte_source", "label": "Texte source", "type": "string", "required": True, "placeholder": "Bonjour le Monde"},
            {"name": "position_debut", "label": "Position de départ", "type": "number", "required": False, "placeholder": "1"},
        ],
    },
    "remplacer_texte": {
        "name": "REMPLACER (REPLACE)", "description": "Remplacer N caractères à partir d'une position dans un texte",
        "category": "Texte",
        "variables": [
            {"name": "texte", "label": "Texte source", "type": "string", "required": True, "placeholder": "Hello World"},
            {"name": "position_debut", "label": "Position de départ", "type": "number", "required": True, "placeholder": "7"},
            {"name": "nb_caracteres", "label": "Nb caractères à remplacer", "type": "number", "required": True, "placeholder": "5"},
            {"name": "nouveau_texte", "label": "Nouveau texte", "type": "string", "required": True, "placeholder": "Monde"},
        ],
    },
    "texte_join": {
        "name": "TEXTE.JOIN (TEXTJOIN)", "description": "Joindre des textes avec un délimiteur, en ignorant optionnellement les vides",
        "category": "Texte",
        "variables": [
            {"name": "textes", "label": "Textes (JSON array)", "type": "json", "required": True, "placeholder": '["A","","B","","C"]'},
            {"name": "delimiteur", "label": "Délimiteur", "type": "string", "required": False, "placeholder": ", "},
            {"name": "ignorer_vides", "label": "Ignorer vides (true/false)", "type": "string", "required": False, "placeholder": "true"},
        ],
    },
    "valeur_texte": {
        "name": "VALEUR (VALUE)", "description": "Convertir un texte en nombre (gère €, $, %, espaces, virgule française)",
        "category": "Texte",
        "variables": [
            {"name": "texte", "label": "Texte à convertir", "type": "string", "required": True, "placeholder": "1 234,56 €"},
        ],
    },
    "ctxt": {
        "name": "CTXT (FIXED)", "description": "Formater un nombre avec un nombre fixe de décimales",
        "category": "Texte",
        "variables": [
            {"name": "nombre", "label": "Nombre", "type": "number", "required": True, "placeholder": "1234567.891"},
            {"name": "decimales", "label": "Décimales", "type": "number", "required": False, "placeholder": "2"},
            {"name": "pas_separateur", "label": "Sans séparateur milliers (true/false)", "type": "string", "required": False, "placeholder": "false"},
        ],
    },

    # ── v4 — D-Functions ──────────────────────────────────────────────────
    "bdsomme": {
        "name": "BDSOMME (DSUM)", "description": "Somme d'un champ dans une base de données filtrée par critères",
        "category": "Gestion de Données",
        "variables": [
            {"name": "donnees", "label": "Base de données (JSON)", "type": "json", "required": True, "placeholder": '[{"dept":"Ventes","ca":100}]'},
            {"name": "champ", "label": "Champ à sommer", "type": "string", "required": True, "placeholder": "ca"},
            {"name": "criteres", "label": "Critères (JSON)", "type": "json", "required": True, "placeholder": '[{"colonne":"dept","valeur":"Ventes"}]'},
        ],
    },
    "bdnb": {
        "name": "BDNB (DCOUNT)", "description": "Compter les enregistrements non vides d'un champ filtré",
        "category": "Gestion de Données",
        "variables": [
            {"name": "donnees", "label": "Base de données (JSON)", "type": "json", "required": True, "placeholder": '[{"dept":"Ventes","ca":100}]'},
            {"name": "champ", "label": "Champ à compter", "type": "string", "required": True, "placeholder": "ca"},
            {"name": "criteres", "label": "Critères (JSON)", "type": "json", "required": True, "placeholder": '[{"colonne":"dept","valeur":"Ventes"}]'},
        ],
    },
    "bdmax": {
        "name": "BDMAX", "description": "Valeur maximale d'un champ dans une base de données filtrée",
        "category": "Gestion de Données",
        "variables": [
            {"name": "donnees", "label": "Base de données (JSON)", "type": "json", "required": True, "placeholder": '[{"dept":"Ventes","ca":100}]'},
            {"name": "champ", "label": "Champ", "type": "string", "required": True, "placeholder": "ca"},
            {"name": "criteres", "label": "Critères (JSON)", "type": "json", "required": True, "placeholder": '[{"colonne":"dept","valeur":"Ventes"}]'},
        ],
    },
    "bdmin": {
        "name": "BDMIN", "description": "Valeur minimale d'un champ dans une base de données filtrée",
        "category": "Gestion de Données",
        "variables": [
            {"name": "donnees", "label": "Base de données (JSON)", "type": "json", "required": True, "placeholder": '[{"dept":"Ventes","ca":100}]'},
            {"name": "champ", "label": "Champ", "type": "string", "required": True, "placeholder": "ca"},
            {"name": "criteres", "label": "Critères (JSON)", "type": "json", "required": True, "placeholder": '[{"colonne":"dept","valeur":"Ventes"}]'},
        ],
    },
    "bdmoyenne": {
        "name": "BDMOYENNE", "description": "Moyenne d'un champ dans une base de données filtrée",
        "category": "Gestion de Données",
        "variables": [
            {"name": "donnees", "label": "Base de données (JSON)", "type": "json", "required": True, "placeholder": '[{"dept":"Ventes","ca":100}]'},
            {"name": "champ", "label": "Champ", "type": "string", "required": True, "placeholder": "ca"},
            {"name": "criteres", "label": "Critères (JSON)", "type": "json", "required": True, "placeholder": '[{"colonne":"dept","valeur":"Ventes"}]'},
        ],
    },

    # ── v4 — Manipulation Avancée ─────────────────────────────────────────
    "lambda_recursive": {
        "name": "LAMBDA Récursive", "description": "Appliquer une expression récursivement N fois sur une valeur",
        "category": "Architecture",
        "variables": [
            {"name": "expression", "label": "Expression (utiliser x)", "type": "string", "required": True, "placeholder": "x * 1.05"},
            {"name": "valeur_initiale", "label": "Valeur initiale", "type": "number", "required": True, "placeholder": "1000"},
            {"name": "iterations", "label": "Nombre d'itérations", "type": "number", "required": False, "placeholder": "10"},
        ],
    },
    "let_advanced": {
        "name": "LET Avancé", "description": "Définir des variables par étapes et évaluer une expression finale",
        "category": "Architecture",
        "variables": [
            {"name": "variables", "label": "Variables initiales (JSON)", "type": "json", "required": True, "placeholder": '{"prix":100,"quantite":50}'},
            {"name": "etapes", "label": "Étapes de calcul (JSON)", "type": "json", "required": True, "placeholder": '[{"nom":"total","expression":"prix * quantite"}]'},
            {"name": "expression_finale", "label": "Expression finale", "type": "string", "required": True, "placeholder": "total * 1.2"},
        ],
    },
    "choose": {
        "name": "CHOISIR (CHOOSE)", "description": "Sélectionner une valeur par son index dans une liste",
        "category": "Logique",
        "variables": [
            {"name": "index", "label": "Index (1-based)", "type": "number", "required": True, "placeholder": "2"},
            {"name": "valeurs", "label": "Liste de valeurs (JSON)", "type": "json", "required": True, "placeholder": '["Lundi","Mardi","Mercredi","Jeudi","Vendredi"]'},
        ],
    },
    "byrow": {
        "name": "BYROW", "description": "Appliquer une opération à chaque ligne d'une matrice",
        "category": "Ingénierie",
        "variables": [
            {"name": "matrice", "label": "Matrice (JSON 2D)", "type": "json", "required": True, "placeholder": "[[1,2,3],[4,5,6]]"},
            {"name": "operation", "label": "Opération (somme, moyenne, max, min, produit)", "type": "string", "required": True, "placeholder": "somme"},
        ],
    },
    "bycol": {
        "name": "BYCOL", "description": "Appliquer une opération à chaque colonne d'une matrice",
        "category": "Ingénierie",
        "variables": [
            {"name": "matrice", "label": "Matrice (JSON 2D)", "type": "json", "required": True, "placeholder": "[[1,2,3],[4,5,6]]"},
            {"name": "operation", "label": "Opération (somme, moyenne, max, min)", "type": "string", "required": True, "placeholder": "somme"},
        ],
    },
    "makearray": {
        "name": "MAKEARRAY", "description": "Générer une matrice avec une expression utilisant row et col",
        "category": "Ingénierie",
        "variables": [
            {"name": "lignes", "label": "Nombre de lignes", "type": "number", "required": True, "placeholder": "3"},
            {"name": "colonnes", "label": "Nombre de colonnes", "type": "number", "required": True, "placeholder": "3"},
            {"name": "expression", "label": "Expression (row, col)", "type": "string", "required": False, "placeholder": "row * colonnes + col + 1"},
        ],
    },

    # ── v4 — Utilitaires Data ─────────────────────────────────────────────
    "esterreur": {
        "name": "ESTERREUR", "description": "Vérifier quelles valeurs sont des erreurs (#N/A, #REF!, etc.)",
        "category": "Logique",
        "variables": [
            {"name": "valeurs", "label": "Valeurs à tester (JSON)", "type": "json", "required": True, "placeholder": '[42, "#N/A", "texte", "#DIV/0!"]'},
        ],
    },
    "estna": {
        "name": "ESTNA", "description": "Vérifier quelles valeurs sont #N/A",
        "category": "Logique",
        "variables": [
            {"name": "valeurs", "label": "Valeurs à tester (JSON)", "type": "json", "required": True, "placeholder": '[42, "#N/A", "texte", null]'},
        ],
    },
    "type_val": {
        "name": "TYPE", "description": "Identifier le type d'une valeur (1=Nombre, 2=Texte, 4=Booléen, 16=Erreur, 64=Tableau)",
        "category": "Logique",
        "variables": [
            {"name": "valeur", "label": "Valeur à tester", "type": "json", "required": True, "placeholder": "42"},
        ],
    },
    "coordonnees": {
        "name": "COORDONNEES (ADDRESS)", "description": "Construire une référence de cellule Excel ($A$1, B$2, etc.)",
        "category": "Gestion de Données",
        "variables": [
            {"name": "ligne", "label": "Numéro de ligne", "type": "number", "required": True, "placeholder": "5"},
            {"name": "colonne", "label": "Numéro de colonne", "type": "number", "required": True, "placeholder": "3"},
            {"name": "type_reference", "label": "Type (1=absolu, 4=relatif)", "type": "number", "required": False, "placeholder": "1"},
        ],
    },
    "indirect_ext": {
        "name": "INDIRECT.EXT", "description": "Naviguer dans une structure JSON par chemin (ex: 'clients.0.nom')",
        "category": "Gestion de Données",
        "variables": [
            {"name": "reference", "label": "Chemin de référence", "type": "string", "required": True, "placeholder": "clients.0.nom"},
            {"name": "donnees", "label": "Données (JSON)", "type": "json", "required": True, "placeholder": '{"clients":[{"nom":"Alice"}]}'},
        ],
    },
    "nbcar": {
        "name": "NBCAR (LEN)", "description": "Compter le nombre de caractères d'un texte",
        "category": "Texte",
        "variables": [
            {"name": "texte", "label": "Texte", "type": "string", "required": True, "placeholder": "Bonjour"},
        ],
    },
    "majuscule": {
        "name": "MAJUSCULE (UPPER)", "description": "Convertir un texte en majuscules",
        "category": "Texte",
        "variables": [
            {"name": "texte", "label": "Texte", "type": "string", "required": True, "placeholder": "bonjour"},
        ],
    },
    "minuscule": {
        "name": "MINUSCULE (LOWER)", "description": "Convertir un texte en minuscules",
        "category": "Texte",
        "variables": [
            {"name": "texte", "label": "Texte", "type": "string", "required": True, "placeholder": "BONJOUR"},
        ],
    },
    "cnum": {
        "name": "CNUM (N)", "description": "Convertir une valeur en nombre (texte→0, bool→0/1)",
        "category": "Logique",
        "variables": [
            {"name": "valeur", "label": "Valeur", "type": "json", "required": True, "placeholder": "42"},
        ],
    },
    "abs_val": {
        "name": "ABS", "description": "Valeur absolue d'un nombre",
        "category": "Mathématiques",
        "variables": [
            {"name": "nombre", "label": "Nombre", "type": "number", "required": True, "placeholder": "-42"},
        ],
    },
    "mod_val": {
        "name": "MOD", "description": "Reste de la division euclidienne (modulo)",
        "category": "Mathématiques",
        "variables": [
            {"name": "nombre", "label": "Nombre", "type": "number", "required": True, "placeholder": "17"},
            {"name": "diviseur", "label": "Diviseur", "type": "number", "required": True, "placeholder": "5"},
        ],
    },
    "puissance": {
        "name": "PUISSANCE (POWER)", "description": "Élever un nombre à une puissance",
        "category": "Mathématiques",
        "variables": [
            {"name": "base", "label": "Base", "type": "number", "required": True, "placeholder": "2"},
            {"name": "exposant", "label": "Exposant", "type": "number", "required": True, "placeholder": "10"},
        ],
    },
    "plafond_plancher": {
        "name": "PLAFOND / PLANCHER", "description": "Arrondir au plafond et au plancher avec incrément personnalisé",
        "category": "Mathématiques",
        "variables": [
            {"name": "nombre", "label": "Nombre", "type": "number", "required": True, "placeholder": "7.3"},
            {"name": "increment", "label": "Incrément", "type": "number", "required": False, "placeholder": "0.5"},
        ],
    },
}
