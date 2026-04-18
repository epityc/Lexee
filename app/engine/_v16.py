"""
v16 — Analyse de Données & Divers (Groupe 11).

19 nouvelles formules (11 déjà existantes : LAMBDA, MAP, REDUCE, SCAN,
MAKEARRAY, NOMINAL, EFFECT, DOLLARDE, DOLLARFR, PHI, GAUSS) :
- Stubs : IMAGE, ANCHORARRAY, GETPIVOTDATA, RTD, STOCKHISTORY, SINGLE
- Info formule : FORMULATEXT, HYPERLINK
- Finance : EUROCONVERT, LET, ISPMT, CUMIPMT, CUMPRINC, PDURATION, RRI
- Date : ISOWEEKNUM, NETWORKDAYS.INTL, WORKDAY.INTL
- Maths : BITXOR
"""

from __future__ import annotations

import math
from datetime import date, timedelta


# ═══════════════════════════════════════════════════════════════════════════════
# STUBS (fonctionnalités hors contexte SaaS)
# ═══════════════════════════════════════════════════════════════════════════════


def formule_image(v: dict) -> dict:
    """IMAGE — insère une image depuis une URL (stub)."""
    url = str(v["url"])
    alt = str(v.get("alt_text", ""))
    return {
        "resultat": f"IMAGE({url})",
        "url": url,
        "alt_text": alt,
        "message": "Insertion d'images non disponible dans cet environnement.",
    }


def formule_anchorarray(v: dict) -> dict:
    """ANCHORARRAY — référence la plage d'un tableau dynamique (stub)."""
    reference = str(v.get("reference", "A1"))
    return {
        "resultat": f"#{reference}",
        "message": "Référence de plage dynamique (simulation).",
    }


def formule_formulatext(v: dict) -> dict:
    """FORMULATEXT — renvoie la formule sous forme de texte."""
    formule = str(v["formule"])
    return {"resultat": formule}


def formule_getpivotdata(v: dict) -> dict:
    """GETPIVOTDATA — extrait des données d'un tableau croisé dynamique (stub)."""
    champ = str(v.get("champ", ""))
    return {
        "resultat": 0,
        "champ": champ,
        "message": "Tableau croisé dynamique non disponible.",
    }


def formule_hyperlink(v: dict) -> dict:
    """HYPERLINK — crée un lien hypertexte."""
    url = str(v["url"])
    texte = str(v.get("texte", url))
    return {"resultat": texte, "url": url}


def formule_rtd(v: dict) -> dict:
    """RTD — données en temps réel depuis un serveur COM (stub)."""
    return {
        "resultat": 0,
        "message": "Serveur RTD non disponible dans cet environnement.",
    }


def formule_euroconvert(v: dict) -> dict:
    """EUROCONVERT — convertit entre devises de la zone euro (taux fixes 1999)."""
    nombre = float(v["nombre"])
    source = str(v["source"]).upper()
    cible = str(v["cible"]).upper()

    taux_euro = {
        "EUR": 1.0,
        "ATS": 13.7603,   # Schilling autrichien
        "BEF": 40.3399,   # Franc belge
        "DEM": 1.95583,   # Mark allemand
        "ESP": 166.386,   # Peseta espagnole
        "FIM": 5.94573,   # Mark finlandais
        "FRF": 6.55957,   # Franc français
        "GRD": 340.750,   # Drachme grecque
        "IEP": 0.787564,  # Livre irlandaise
        "ITL": 1936.27,   # Lire italienne
        "LUF": 40.3399,   # Franc luxembourgeois
        "NLG": 2.20371,   # Florin néerlandais
        "PTE": 200.482,   # Escudo portugais
    }
    if source not in taux_euro:
        raise ValueError(f"Devise source '{source}' non reconnue.")
    if cible not in taux_euro:
        raise ValueError(f"Devise cible '{cible}' non reconnue.")
    en_euro = nombre / taux_euro[source]
    resultat = en_euro * taux_euro[cible]
    return {"resultat": round(resultat, 6)}


def formule_stockhistory(v: dict) -> dict:
    """STOCKHISTORY — historique boursier (stub)."""
    symbole = str(v.get("symbole", ""))
    return {
        "resultat": [],
        "symbole": symbole,
        "message": "Données boursières non disponibles.",
    }


def formule_single(v: dict) -> dict:
    """SINGLE (opérateur @) — renvoie une valeur unique d'un tableau."""
    val = v["valeur"]
    if isinstance(val, list):
        if val and isinstance(val[0], list):
            return {"resultat": val[0][0]}
        if val:
            return {"resultat": val[0]}
    return {"resultat": val}


# ═══════════════════════════════════════════════════════════════════════════════
# FINANCE
# ═══════════════════════════════════════════════════════════════════════════════


def formule_let_val(v: dict) -> dict:
    """LET — définit des variables nommées et évalue une expression."""
    variables = v.get("variables", {})
    expression = str(v["expression"])
    ns = {"__builtins__": {}, "math": math, "abs": abs, "min": min, "max": max,
          "sum": sum, "round": round, "int": int, "float": float,
          "True": True, "False": False, "None": None}
    ns.update(variables)
    return {"resultat": eval(expression, ns)}


def formule_ispmt(v: dict) -> dict:
    """ISPMT — intérêts payés pendant une période spécifique (méthode linéaire)."""
    taux = float(v["taux"])
    periode = int(v["periode"])
    nb_periodes = int(v["nb_periodes"])
    valeur_actuelle = float(v["valeur_actuelle"])
    interet = -valeur_actuelle * taux * (1 - periode / nb_periodes)
    return {"resultat": interet}


def formule_cumipmt(v: dict) -> dict:
    """CUMIPMT — intérêts cumulés entre deux périodes."""
    taux = float(v["taux"])
    nb_periodes = int(v["nb_periodes"])
    valeur_actuelle = float(v["valeur_actuelle"])
    debut = int(v["periode_debut"])
    fin = int(v["periode_fin"])
    if taux <= 0 or nb_periodes <= 0 or valeur_actuelle <= 0:
        raise ValueError("Taux, périodes et VA doivent être > 0.")
    if debut < 1 or fin < debut:
        raise ValueError("Périodes invalides.")
    pmt = valeur_actuelle * taux / (1 - (1 + taux) ** -nb_periodes)
    total_int = 0.0
    solde = valeur_actuelle
    for p in range(1, fin + 1):
        interet = solde * taux
        principal = pmt - interet
        if p >= debut:
            total_int += interet
        solde -= principal
    return {"resultat": round(total_int, 6)}


def formule_cumprinc(v: dict) -> dict:
    """CUMPRINC — principal cumulé entre deux périodes."""
    taux = float(v["taux"])
    nb_periodes = int(v["nb_periodes"])
    valeur_actuelle = float(v["valeur_actuelle"])
    debut = int(v["periode_debut"])
    fin = int(v["periode_fin"])
    if taux <= 0 or nb_periodes <= 0 or valeur_actuelle <= 0:
        raise ValueError("Taux, périodes et VA doivent être > 0.")
    if debut < 1 or fin < debut:
        raise ValueError("Périodes invalides.")
    pmt = valeur_actuelle * taux / (1 - (1 + taux) ** -nb_periodes)
    total_princ = 0.0
    solde = valeur_actuelle
    for p in range(1, fin + 1):
        interet = solde * taux
        principal = pmt - interet
        if p >= debut:
            total_princ += principal
        solde -= principal
    return {"resultat": round(total_princ, 6)}


def formule_pduration(v: dict) -> dict:
    """PDURATION — nombre de périodes pour atteindre une valeur cible."""
    taux = float(v["taux"])
    valeur_actuelle = float(v["valeur_actuelle"])
    valeur_future = float(v["valeur_future"])
    if taux <= 0 or valeur_actuelle <= 0 or valeur_future <= 0:
        raise ValueError("Taux, VA et VF doivent être > 0.")
    n = (math.log(valeur_future) - math.log(valeur_actuelle)) / math.log(1 + taux)
    return {"resultat": n}


def formule_rri(v: dict) -> dict:
    """RRI — taux de rendement équivalent d'un investissement."""
    nb_periodes = int(v["nb_periodes"])
    valeur_actuelle = float(v["valeur_actuelle"])
    valeur_future = float(v["valeur_future"])
    if nb_periodes <= 0 or valeur_actuelle <= 0:
        raise ValueError("Périodes et VA doivent être > 0.")
    taux = (valeur_future / valeur_actuelle) ** (1 / nb_periodes) - 1
    return {"resultat": taux}


# ═══════════════════════════════════════════════════════════════════════════════
# DATE
# ═══════════════════════════════════════════════════════════════════════════════


def _parse_date(s):
    if isinstance(s, date):
        return s
    return date.fromisoformat(str(s)[:10])


def formule_isoweeknum(v: dict) -> dict:
    """ISOWEEKNUM — numéro de semaine ISO 8601."""
    d = _parse_date(v["date"])
    return {"resultat": d.isocalendar()[1]}


def formule_networkdays_intl(v: dict) -> dict:
    """NETWORKDAYS.INTL — jours ouvrés entre deux dates (week-end configurable)."""
    debut = _parse_date(v["date_debut"])
    fin = _parse_date(v["date_fin"])
    weekend = str(v.get("weekend", "0000011"))
    jours_feries = [_parse_date(d) for d in v.get("jours_feries", [])]

    if len(weekend) != 7:
        raise ValueError("Le masque weekend doit avoir 7 caractères (lun-dim, 1=repos).")

    count = 0
    step = 1 if fin >= debut else -1
    current = debut
    while (step == 1 and current <= fin) or (step == -1 and current >= fin):
        dow = current.weekday()  # 0=lun
        if weekend[dow] == "0" and current not in jours_feries:
            count += 1
        current += timedelta(days=step)
    return {"resultat": count}


def formule_workday_intl(v: dict) -> dict:
    """WORKDAY.INTL — date après N jours ouvrés (week-end configurable)."""
    debut = _parse_date(v["date_debut"])
    jours = int(v["jours"])
    weekend = str(v.get("weekend", "0000011"))
    jours_feries = [_parse_date(d) for d in v.get("jours_feries", [])]

    if len(weekend) != 7:
        raise ValueError("Le masque weekend doit avoir 7 caractères (lun-dim, 1=repos).")

    step = 1 if jours >= 0 else -1
    remaining = abs(jours)
    current = debut
    while remaining > 0:
        current += timedelta(days=step)
        dow = current.weekday()
        if weekend[dow] == "0" and current not in jours_feries:
            remaining -= 1
    return {"resultat": current.isoformat()}


# ═══════════════════════════════════════════════════════════════════════════════
# MATHS
# ═══════════════════════════════════════════════════════════════════════════════


def formule_bitxor(v: dict) -> dict:
    """BITXOR — XOR bit à bit de deux entiers."""
    a = int(v["nombre1"])
    b = int(v["nombre2"])
    if a < 0 or b < 0:
        raise ValueError("Les nombres doivent être >= 0.")
    return {"resultat": a ^ b}
