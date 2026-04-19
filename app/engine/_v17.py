"""
v17 — Dernières fonctions Ingénierie/Maths & Logique moderne (Groupe 12).

16 nouvelles formules (19 déjà existantes) :
- Bits : BITRSHIFT, BITLSHIFT, BITOR, BITAND
- Trigonométrie : ACOT, ACOTH
- Maths : BASE, DECIMAL, COMBINA
- Texte : TEXTJOIN
- Logique : IFS, SWITCH
- Agrégation conditionnelle : MAXIFS, MINIFS, SUMIFS, COUNTIFS
"""

from __future__ import annotations

import math


# ═══════════════════════════════════════════════════════════════════════════════
# BITS
# ═══════════════════════════════════════════════════════════════════════════════


def formule_bitrshift(v: dict) -> dict:
    """BITRSHIFT — décalage à droite bit à bit."""
    nombre = int(v["nombre"])
    decalage = int(v["decalage"])
    if nombre < 0:
        raise ValueError("Le nombre doit être >= 0.")
    return {"resultat": nombre >> decalage}


def formule_bitlshift(v: dict) -> dict:
    """BITLSHIFT — décalage à gauche bit à bit."""
    nombre = int(v["nombre"])
    decalage = int(v["decalage"])
    if nombre < 0:
        raise ValueError("Le nombre doit être >= 0.")
    return {"resultat": nombre << decalage}


def formule_bitor(v: dict) -> dict:
    """BITOR — OR bit à bit de deux entiers."""
    a = int(v["nombre1"])
    b = int(v["nombre2"])
    if a < 0 or b < 0:
        raise ValueError("Les nombres doivent être >= 0.")
    return {"resultat": a | b}


def formule_bitand(v: dict) -> dict:
    """BITAND — AND bit à bit de deux entiers."""
    a = int(v["nombre1"])
    b = int(v["nombre2"])
    if a < 0 or b < 0:
        raise ValueError("Les nombres doivent être >= 0.")
    return {"resultat": a & b}


# ═══════════════════════════════════════════════════════════════════════════════
# TRIGONOMÉTRIE
# ═══════════════════════════════════════════════════════════════════════════════


def formule_acot(v: dict) -> dict:
    """ACOT — arc cotangente (résultat en radians)."""
    x = float(v["nombre"])
    return {"resultat": math.atan2(1, x)}


def formule_acoth(v: dict) -> dict:
    """ACOTH — arc cotangente hyperbolique."""
    x = float(v["nombre"])
    if abs(x) <= 1:
        raise ValueError("|x| doit être > 1.")
    return {"resultat": 0.5 * math.log((x + 1) / (x - 1))}


# ═══════════════════════════════════════════════════════════════════════════════
# MATHS
# ═══════════════════════════════════════════════════════════════════════════════


def formule_base_val(v: dict) -> dict:
    """BASE — convertit un nombre en texte dans une base donnée."""
    nombre = int(v["nombre"])
    base = int(v["base"])
    longueur_min = int(v.get("longueur_min", 0))
    if base < 2 or base > 36:
        raise ValueError("La base doit être entre 2 et 36.")
    if nombre < 0:
        raise ValueError("Le nombre doit être >= 0.")
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if nombre == 0:
        result = "0"
    else:
        result = ""
        n = nombre
        while n > 0:
            result = digits[n % base] + result
            n //= base
    if longueur_min > 0:
        result = result.zfill(longueur_min)
    return {"resultat": result}


def formule_decimal_val(v: dict) -> dict:
    """DECIMAL — convertit un texte d'une base donnée en nombre décimal."""
    texte = str(v["texte"]).upper().strip()
    base = int(v["base"])
    if base < 2 or base > 36:
        raise ValueError("La base doit être entre 2 et 36.")
    return {"resultat": int(texte, base)}


def formule_combina(v: dict) -> dict:
    """COMBINA — combinaisons avec répétition C(n+k-1, k)."""
    n = int(v["nombre"])
    k = int(v["choisi"])
    if n < 0 or k < 0:
        raise ValueError("Les valeurs doivent être >= 0.")
    if n == 0 and k == 0:
        return {"resultat": 1}
    return {"resultat": math.comb(n + k - 1, k)}


# ═══════════════════════════════════════════════════════════════════════════════
# TEXTE
# ═══════════════════════════════════════════════════════════════════════════════


def formule_textjoin(v: dict) -> dict:
    """TEXTJOIN — joint des textes avec un délimiteur, option ignorer vides."""
    delimiteur = str(v["delimiteur"])
    ignorer_vides = bool(v.get("ignorer_vides", True))
    textes = v["textes"]
    if not isinstance(textes, list):
        textes = [textes]
    flat = []
    for item in textes:
        if isinstance(item, list):
            flat.extend(str(x) for x in item)
        else:
            flat.append(str(item))
    if ignorer_vides:
        flat = [t for t in flat if t != ""]
    return {"resultat": delimiteur.join(flat)}


# ═══════════════════════════════════════════════════════════════════════════════
# LOGIQUE MODERNE
# ═══════════════════════════════════════════════════════════════════════════════

_SAFE_NS = {
    "__builtins__": {}, "abs": abs, "min": min, "max": max, "sum": sum,
    "round": round, "int": int, "float": float, "str": str, "len": len,
    "True": True, "False": False, "None": None, "math": math,
}


def formule_ifs(v: dict) -> dict:
    """IFS — évalue plusieurs conditions et renvoie la première vraie."""
    conditions = v["conditions"]
    for cond in conditions:
        test = cond.get("test")
        valeur = cond.get("valeur")
        if isinstance(test, str):
            result = eval(test, dict(_SAFE_NS))
        else:
            result = bool(test)
        if result:
            return {"resultat": valeur}
    raise ValueError("Aucune condition n'est vraie.")


def formule_switch(v: dict) -> dict:
    """SWITCH — compare une expression à des valeurs et renvoie le résultat correspondant."""
    expression = v["expression"]
    cas = v["cas"]
    defaut = v.get("defaut")
    for c in cas:
        if c["valeur"] == expression:
            return {"resultat": c["resultat"]}
    if defaut is not None:
        return {"resultat": defaut}
    raise ValueError("Aucune correspondance trouvée et pas de valeur par défaut.")


# ═══════════════════════════════════════════════════════════════════════════════
# AGRÉGATION CONDITIONNELLE
# ═══════════════════════════════════════════════════════════════════════════════


def _eval_critere(valeur, critere):
    """Évalue si une valeur satisfait un critère (style Excel)."""
    if isinstance(critere, (int, float)):
        return valeur == critere
    critere = str(critere)
    if critere.startswith(">="):
        return float(valeur) >= float(critere[2:])
    if critere.startswith("<="):
        return float(valeur) <= float(critere[2:])
    if critere.startswith("<>"):
        return str(valeur) != critere[2:]
    if critere.startswith(">"):
        return float(valeur) > float(critere[1:])
    if critere.startswith("<"):
        return float(valeur) < float(critere[1:])
    if critere.startswith("="):
        try:
            return float(valeur) == float(critere[1:])
        except (ValueError, TypeError):
            return str(valeur) == critere[1:]
    try:
        return float(valeur) == float(critere)
    except (ValueError, TypeError):
        return str(valeur) == critere


def formule_maxifs(v: dict) -> dict:
    """MAXIFS — maximum des valeurs qui satisfont tous les critères."""
    valeurs = v["valeurs"]
    criteres = v["criteres"]
    n = len(valeurs)
    filtered = []
    for i in range(n):
        match = True
        for crit in criteres:
            plage = crit["plage"]
            critere = crit["critere"]
            if i >= len(plage) or not _eval_critere(plage[i], critere):
                match = False
                break
        if match:
            filtered.append(float(valeurs[i]))
    if not filtered:
        return {"resultat": 0}
    return {"resultat": max(filtered)}


def formule_minifs(v: dict) -> dict:
    """MINIFS — minimum des valeurs qui satisfont tous les critères."""
    valeurs = v["valeurs"]
    criteres = v["criteres"]
    n = len(valeurs)
    filtered = []
    for i in range(n):
        match = True
        for crit in criteres:
            plage = crit["plage"]
            critere = crit["critere"]
            if i >= len(plage) or not _eval_critere(plage[i], critere):
                match = False
                break
        if match:
            filtered.append(float(valeurs[i]))
    if not filtered:
        return {"resultat": 0}
    return {"resultat": min(filtered)}


def formule_sumifs(v: dict) -> dict:
    """SUMIFS — somme des valeurs qui satisfont tous les critères."""
    valeurs = v["valeurs"]
    criteres = v["criteres"]
    n = len(valeurs)
    total = 0.0
    for i in range(n):
        match = True
        for crit in criteres:
            plage = crit["plage"]
            critere = crit["critere"]
            if i >= len(plage) or not _eval_critere(plage[i], critere):
                match = False
                break
        if match:
            total += float(valeurs[i])
    return {"resultat": total}


def formule_countifs(v: dict) -> dict:
    """COUNTIFS — compte les éléments qui satisfont tous les critères."""
    criteres = v["criteres"]
    if not criteres:
        return {"resultat": 0}
    n = len(criteres[0]["plage"])
    count = 0
    for i in range(n):
        match = True
        for crit in criteres:
            plage = crit["plage"]
            critere = crit["critere"]
            if i >= len(plage) or not _eval_critere(plage[i], critere):
                match = False
                break
        if match:
            count += 1
    return {"resultat": count}
