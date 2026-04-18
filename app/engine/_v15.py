"""
v15 — Compatibilité & Nouveautés IA/Regex (Groupe 10).

20 nouvelles formules (QUARTILE, GROUPBY, PIVOTBY déjà existantes) :
- Alias compat : RANK, STDEV, STDEVP, TDIST, TINV, TTEST, VAR, VARP,
  WEIBULL, ZTEST
- Regex (O365) : REGEXEXTRACT, REGEXMATCH, REGEXREPLACE
- Texte moderne (O365) : TEXTBEFORE, TEXTAFTER, TEXTSPLIT
- Agrégation moderne (O365) : PERCENTOF
"""

from __future__ import annotations

import math
import re
import statistics

from app.engine._v11 import (
    formule_t_dist as _formule_t_dist,
    formule_t_inv as _formule_t_inv,
    formule_t_test as _formule_t_test,
    formule_weibull_dist as _formule_weibull_dist,
    formule_z_test as _formule_z_test,
)


# ═══════════════════════════════════════════════════════════════════════════════
# ALIAS COMPATIBILITÉ (statistiques)
# ═══════════════════════════════════════════════════════════════════════════════


def formule_rank(v: dict) -> dict:
    """RANK — rang d'une valeur (alias de RANK.EQ, ordre décroissant par défaut)."""
    valeurs = [float(x) for x in v["valeurs"]]
    nombre = float(v["nombre"])
    ordre = int(v.get("ordre", 0))
    if nombre not in valeurs:
        raise ValueError(f"{nombre} n'est pas dans la liste.")
    if ordre == 0:
        s = sorted(valeurs, reverse=True)
    else:
        s = sorted(valeurs)
    return {"rang": s.index(nombre) + 1}


def formule_stdev(v: dict) -> dict:
    """STDEV — écart-type échantillon (alias de STDEV.S)."""
    valeurs = [float(x) for x in v["valeurs"]]
    if len(valeurs) < 2:
        raise ValueError("Au moins 2 valeurs requises.")
    mean = sum(valeurs) / len(valeurs)
    var = sum((x - mean)**2 for x in valeurs) / (len(valeurs) - 1)
    return {"resultat": math.sqrt(var)}


def formule_stdevp(v: dict) -> dict:
    """STDEVP — écart-type population (alias de STDEV.P)."""
    valeurs = [float(x) for x in v["valeurs"]]
    if len(valeurs) < 1:
        raise ValueError("Au moins 1 valeur requise.")
    mean = sum(valeurs) / len(valeurs)
    var = sum((x - mean)**2 for x in valeurs) / len(valeurs)
    return {"resultat": math.sqrt(var)}


def formule_tdist(v: dict) -> dict:
    """TDIST — alias compat de T.DIST (CDF bilatérale par défaut)."""
    return _formule_t_dist(v)


def formule_tinv(v: dict) -> dict:
    """TINV — alias compat de T.INV."""
    return _formule_t_inv(v)


def formule_ttest(v: dict) -> dict:
    """TTEST — alias compat de T.TEST."""
    return _formule_t_test(v)


def formule_var_val(v: dict) -> dict:
    """VAR — variance échantillon (alias de VAR.S)."""
    valeurs = [float(x) for x in v["valeurs"]]
    if len(valeurs) < 2:
        raise ValueError("Au moins 2 valeurs requises.")
    mean = sum(valeurs) / len(valeurs)
    return {"resultat": sum((x - mean)**2 for x in valeurs) / (len(valeurs) - 1)}


def formule_varp(v: dict) -> dict:
    """VARP — variance population (alias de VAR.P)."""
    valeurs = [float(x) for x in v["valeurs"]]
    if len(valeurs) < 1:
        raise ValueError("Au moins 1 valeur requise.")
    mean = sum(valeurs) / len(valeurs)
    return {"resultat": sum((x - mean)**2 for x in valeurs) / len(valeurs)}


def formule_weibull(v: dict) -> dict:
    """WEIBULL — alias compat de WEIBULL.DIST."""
    return _formule_weibull_dist(v)


def formule_ztest(v: dict) -> dict:
    """ZTEST — alias compat de Z.TEST."""
    return _formule_z_test(v)


# ═══════════════════════════════════════════════════════════════════════════════
# REGEX (O365)
# ═══════════════════════════════════════════════════════════════════════════════


def formule_regexextract(v: dict) -> dict:
    """REGEXEXTRACT — extrait la première correspondance d'un motif regex."""
    texte = str(v["texte"])
    motif = str(v["motif"])
    match = re.search(motif, texte)
    if match is None:
        raise ValueError(f"Aucune correspondance pour '{motif}' dans '{texte}'.")
    if match.groups():
        return {"resultat": match.group(1)}
    return {"resultat": match.group(0)}


def formule_regexmatch(v: dict) -> dict:
    """REGEXMATCH — teste si un texte correspond à un motif regex."""
    texte = str(v["texte"])
    motif = str(v["motif"])
    return {"resultat": bool(re.search(motif, texte))}


def formule_regexreplace(v: dict) -> dict:
    """REGEXREPLACE — remplace les correspondances d'un motif regex."""
    texte = str(v["texte"])
    motif = str(v["motif"])
    remplacement = str(v["remplacement"])
    return {"resultat": re.sub(motif, remplacement, texte)}


# ═══════════════════════════════════════════════════════════════════════════════
# TEXTE MODERNE (O365)
# ═══════════════════════════════════════════════════════════════════════════════


def formule_textbefore(v: dict) -> dict:
    """TEXTBEFORE — texte avant un délimiteur."""
    texte = str(v["texte"])
    delimiteur = str(v["delimiteur"])
    instance = int(v.get("instance", 1))
    if instance < 1:
        raise ValueError("L'instance doit être >= 1.")
    idx = -1
    for _ in range(instance):
        idx = texte.find(delimiteur, idx + 1)
        if idx == -1:
            raise ValueError(f"Délimiteur '{delimiteur}' non trouvé (instance {instance}).")
    return {"resultat": texte[:idx]}


def formule_textafter(v: dict) -> dict:
    """TEXTAFTER — texte après un délimiteur."""
    texte = str(v["texte"])
    delimiteur = str(v["delimiteur"])
    instance = int(v.get("instance", 1))
    if instance < 1:
        raise ValueError("L'instance doit être >= 1.")
    idx = -1
    for _ in range(instance):
        idx = texte.find(delimiteur, idx + 1)
        if idx == -1:
            raise ValueError(f"Délimiteur '{delimiteur}' non trouvé (instance {instance}).")
    return {"resultat": texte[idx + len(delimiteur):]}


def formule_textsplit(v: dict) -> dict:
    """TEXTSPLIT — divise un texte par délimiteur(s) en colonnes/lignes."""
    texte = str(v["texte"])
    col_delim = v.get("delimiteur_col")
    row_delim = v.get("delimiteur_ligne")
    if row_delim:
        rows = texte.split(str(row_delim))
        if col_delim:
            result = [r.split(str(col_delim)) for r in rows]
        else:
            result = [[r] for r in rows]
        return {"resultat": result}
    if col_delim:
        return {"resultat": [texte.split(str(col_delim))]}
    return {"resultat": [[texte]]}


# ═══════════════════════════════════════════════════════════════════════════════
# PERCENTOF (O365)
# ═══════════════════════════════════════════════════════════════════════════════


def formule_percentof(v: dict) -> dict:
    """PERCENTOF — pourcentage d'une valeur par rapport à un total."""
    valeur = float(v["valeur"])
    total = float(v["total"])
    if total == 0:
        raise ValueError("Le total ne peut pas être zéro.")
    return {"resultat": valeur / total}
