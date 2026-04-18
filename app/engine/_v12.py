"""
v12 — Texte Avancé & Recherche Moderne / O365 (Groupe 7).

27 nouvelles formules :
- Texte avancé : MIDB, PHONETIC, REPLACEB, RIGHTB, SEARCHB, T, UNICHAR,
  UNICODE, VALUETOTEXT, ARRAYTOTEXT
- Compatibilité : CALL, REGISTER.ID
- Tableaux dynamiques : CHOOSECOLS, CHOOSEROWS, DROP, EXPAND, HSTACK, TAKE,
  TOCOL, TOROW, WRAPCOLS, WRAPROWS
- Lambda / fonctionnel : ISOMITTED, LAMBDA, MAP, REDUCE, SCAN
"""

from __future__ import annotations

import json
import math
import re


# ═══════════════════════════════════════════════════════════════════════════════
# TEXTE AVANCÉ (octets / Unicode)
# ═══════════════════════════════════════════════════════════════════════════════


def formule_midb(v: dict) -> dict:
    """MIDB — extrait des octets au milieu d'une chaîne (UTF-8)."""
    texte = str(v["texte"])
    position = int(v["position"])
    nb_octets = int(v["nb_octets"])
    encoded = texte.encode("utf-8")
    start = max(position - 1, 0)
    trunc = encoded[start:start + nb_octets]
    return {"resultat": trunc.decode("utf-8", errors="ignore")}


def formule_phonetic(v: dict) -> dict:
    """PHONETIC — extrait la lecture phonétique (furigana) d'un texte japonais."""
    texte = str(v["texte"])
    result = []
    for ch in texte:
        if "\u3041" <= ch <= "\u3096":
            result.append(ch)
        elif "\u30A1" <= ch <= "\u30F6":
            result.append(ch)
        elif "\u4E00" <= ch <= "\u9FFF":
            result.append(ch)
        else:
            result.append(ch)
    return {"resultat": "".join(result)}


def formule_replaceb(v: dict) -> dict:
    """REPLACEB — remplace des octets dans une chaîne (UTF-8)."""
    texte = str(v["texte"])
    position = int(v["position"])
    nb_octets = int(v["nb_octets"])
    nouveau = str(v["nouveau_texte"])
    encoded = texte.encode("utf-8")
    start = max(position - 1, 0)
    result = encoded[:start] + nouveau.encode("utf-8") + encoded[start + nb_octets:]
    return {"resultat": result.decode("utf-8", errors="ignore")}


def formule_rightb(v: dict) -> dict:
    """RIGHTB — n derniers octets d'une chaîne (UTF-8)."""
    texte = str(v["texte"])
    nb_octets = int(v.get("nb_octets", 1))
    encoded = texte.encode("utf-8")
    trunc = encoded[max(0, len(encoded) - nb_octets):]
    return {"resultat": trunc.decode("utf-8", errors="ignore")}


def formule_searchb(v: dict) -> dict:
    """SEARCHB — recherche insensible à la casse en octets (UTF-8)."""
    cherche = str(v["cherche"]).lower()
    texte = str(v["texte"])
    debut = int(v.get("debut", 1))
    texte_lower = texte.lower()
    texte_bytes = texte_lower.encode("utf-8")
    cherche_bytes = cherche.encode("utf-8")
    debut_bytes = len(texte_lower[:debut - 1].encode("utf-8"))
    idx = texte_bytes.find(cherche_bytes, debut_bytes)
    if idx == -1:
        raise ValueError(f"'{v['cherche']}' non trouvé dans '{texte}'.")
    return {"position": idx + 1}


def formule_t_val(v: dict) -> dict:
    """T — renvoie le texte si la valeur est du texte, sinon chaîne vide."""
    val = v["valeur"]
    if isinstance(val, str):
        return {"resultat": val}
    return {"resultat": ""}


def formule_unichar(v: dict) -> dict:
    """UNICHAR — renvoie le caractère Unicode d'un code point."""
    code = int(v["nombre"])
    if code < 1 or code > 0x10FFFF:
        raise ValueError(f"Code point {code} hors limites (1..1114111).")
    return {"resultat": chr(code)}


def formule_unicode_val(v: dict) -> dict:
    """UNICODE — renvoie le code point du premier caractère."""
    texte = str(v["texte"])
    if not texte:
        raise ValueError("Texte vide.")
    return {"resultat": ord(texte[0])}


def formule_valuetotext(v: dict) -> dict:
    """VALUETOTEXT — convertit une valeur en texte."""
    val = v["valeur"]
    fmt = int(v.get("format", 0))
    if fmt == 1:
        if isinstance(val, str):
            return {"resultat": f'"{val}"'}
        return {"resultat": str(val)}
    return {"resultat": str(val)}


def formule_arraytotext(v: dict) -> dict:
    """ARRAYTOTEXT — convertit un tableau en texte."""
    tableau = v["tableau"]
    fmt = int(v.get("format", 0))
    if fmt == 1:
        return {"resultat": json.dumps(tableau, ensure_ascii=False)}
    if isinstance(tableau, list):
        flat = []
        for item in tableau:
            if isinstance(item, list):
                flat.extend(str(x) for x in item)
            else:
                flat.append(str(item))
        return {"resultat": ", ".join(flat)}
    return {"resultat": str(tableau)}


# ═══════════════════════════════════════════════════════════════════════════════
# COMPATIBILITÉ (CALL / REGISTER.ID)
# ═══════════════════════════════════════════════════════════════════════════════


def formule_call_val(v: dict) -> dict:
    """CALL — simule un appel de fonction externe (stub)."""
    nom_fonction = str(v.get("nom_fonction", ""))
    args = v.get("arguments", [])
    return {
        "resultat": f"CALL({nom_fonction})",
        "message": "Fonction externe non disponible dans cet environnement.",
        "arguments": args,
    }


def formule_register_id(v: dict) -> dict:
    """REGISTER.ID — renvoie un identifiant de registre (stub)."""
    module = str(v.get("module", ""))
    procedure = str(v.get("procedure", ""))
    return {
        "resultat": f"REG:{module}:{procedure}",
        "message": "Registre externe non disponible dans cet environnement.",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# TABLEAUX DYNAMIQUES (O365)
# ═══════════════════════════════════════════════════════════════════════════════


def _ensure_2d(arr):
    """Normalise un tableau en 2D."""
    if not arr:
        return [[]]
    if not isinstance(arr[0], list):
        return [arr]
    return [list(row) for row in arr]


def formule_choosecols(v: dict) -> dict:
    """CHOOSECOLS — sélectionne des colonnes d'un tableau."""
    tableau = _ensure_2d(v["tableau"])
    cols = [int(c) for c in v["colonnes"]]
    nb_cols = len(tableau[0]) if tableau and tableau[0] else 0
    for c in cols:
        if c == 0 or abs(c) > nb_cols:
            raise ValueError(f"Indice de colonne {c} hors limites.")
    result = []
    for row in tableau:
        new_row = []
        for c in cols:
            idx = c - 1 if c > 0 else nb_cols + c
            new_row.append(row[idx])
        result.append(new_row)
    return {"resultat": result}


def formule_chooserows(v: dict) -> dict:
    """CHOOSEROWS — sélectionne des lignes d'un tableau."""
    tableau = _ensure_2d(v["tableau"])
    rows = [int(r) for r in v["lignes"]]
    nb_rows = len(tableau)
    for r in rows:
        if r == 0 or abs(r) > nb_rows:
            raise ValueError(f"Indice de ligne {r} hors limites.")
    result = []
    for r in rows:
        idx = r - 1 if r > 0 else nb_rows + r
        result.append(list(tableau[idx]))
    return {"resultat": result}


def formule_drop_val(v: dict) -> dict:
    """DROP — supprime des lignes/colonnes du début ou de la fin."""
    tableau = _ensure_2d(v["tableau"])
    lignes = int(v.get("lignes", 0))
    colonnes = int(v.get("colonnes", 0))
    if lignes > 0:
        tableau = tableau[lignes:]
    elif lignes < 0:
        tableau = tableau[:lignes]
    if colonnes > 0:
        tableau = [row[colonnes:] for row in tableau]
    elif colonnes < 0:
        tableau = [row[:colonnes] for row in tableau]
    if not tableau or not tableau[0]:
        raise ValueError("Le résultat est vide après suppression.")
    return {"resultat": tableau}


def formule_expand(v: dict) -> dict:
    """EXPAND — étend un tableau aux dimensions spécifiées."""
    tableau = _ensure_2d(v["tableau"])
    nb_lignes = int(v["lignes"])
    nb_colonnes = int(v["colonnes"])
    pad = v.get("pad", "")
    cur_rows = len(tableau)
    cur_cols = max((len(r) for r in tableau), default=0)
    result = []
    for i in range(nb_lignes):
        row = []
        for j in range(nb_colonnes):
            if i < cur_rows and j < cur_cols and j < len(tableau[i]):
                row.append(tableau[i][j])
            else:
                row.append(pad)
        result.append(row)
    return {"resultat": result}


def formule_hstack(v: dict) -> dict:
    """HSTACK — empile horizontalement plusieurs tableaux."""
    tableaux = v["tableaux"]
    if not tableaux:
        raise ValueError("Au moins un tableau requis.")
    arrays = [_ensure_2d(t) for t in tableaux]
    max_rows = max(len(a) for a in arrays)
    result = []
    for i in range(max_rows):
        row = []
        for a in arrays:
            if i < len(a):
                row.extend(a[i])
            else:
                row.extend([""] * len(a[0]))
        result.append(row)
    return {"resultat": result}


def formule_take_val(v: dict) -> dict:
    """TAKE — prend des lignes/colonnes du début ou de la fin."""
    tableau = _ensure_2d(v["tableau"])
    lignes = int(v.get("lignes", 0)) if "lignes" in v else None
    colonnes = int(v.get("colonnes", 0)) if "colonnes" in v else None
    if lignes is not None and lignes != 0:
        if lignes > 0:
            tableau = tableau[:lignes]
        else:
            tableau = tableau[lignes:]
    if colonnes is not None and colonnes != 0:
        if colonnes > 0:
            tableau = [row[:colonnes] for row in tableau]
        else:
            tableau = [row[colonnes:] for row in tableau]
    return {"resultat": tableau}


def formule_tocol(v: dict) -> dict:
    """TOCOL — convertit un tableau en une seule colonne."""
    tableau = _ensure_2d(v["tableau"])
    ignore = int(v.get("ignore", 0))
    scan_by_col = int(v.get("scan_par_colonne", 0))
    flat = []
    if scan_by_col:
        max_cols = max((len(r) for r in tableau), default=0)
        for j in range(max_cols):
            for row in tableau:
                if j < len(row):
                    flat.append(row[j])
    else:
        for row in tableau:
            flat.extend(row)
    if ignore == 1:
        flat = [x for x in flat if x != "" and x is not None]
    elif ignore == 2:
        flat = [x for x in flat if not (isinstance(x, str) and x.startswith("#"))]
    elif ignore == 3:
        flat = [x for x in flat if x != "" and x is not None and not (isinstance(x, str) and x.startswith("#"))]
    return {"resultat": [[x] for x in flat]}


def formule_torow(v: dict) -> dict:
    """TOROW — convertit un tableau en une seule ligne."""
    tableau = _ensure_2d(v["tableau"])
    ignore = int(v.get("ignore", 0))
    scan_by_col = int(v.get("scan_par_colonne", 0))
    flat = []
    if scan_by_col:
        max_cols = max((len(r) for r in tableau), default=0)
        for j in range(max_cols):
            for row in tableau:
                if j < len(row):
                    flat.append(row[j])
    else:
        for row in tableau:
            flat.extend(row)
    if ignore == 1:
        flat = [x for x in flat if x != "" and x is not None]
    elif ignore == 2:
        flat = [x for x in flat if not (isinstance(x, str) and x.startswith("#"))]
    elif ignore == 3:
        flat = [x for x in flat if x != "" and x is not None and not (isinstance(x, str) and x.startswith("#"))]
    return {"resultat": [flat]}


def formule_wrapcols(v: dict) -> dict:
    """WRAPCOLS — enveloppe un vecteur en colonnes de taille fixe."""
    vecteur = list(v["vecteur"])
    taille = int(v["taille"])
    pad = v.get("pad", "")
    if taille < 1:
        raise ValueError("La taille doit être >= 1.")
    nb_cols = math.ceil(len(vecteur) / taille)
    while len(vecteur) < nb_cols * taille:
        vecteur.append(pad)
    result = []
    for i in range(taille):
        row = []
        for j in range(nb_cols):
            row.append(vecteur[j * taille + i])
        result.append(row)
    return {"resultat": result}


def formule_wraprows(v: dict) -> dict:
    """WRAPROWS — enveloppe un vecteur en lignes de taille fixe."""
    vecteur = list(v["vecteur"])
    taille = int(v["taille"])
    pad = v.get("pad", "")
    if taille < 1:
        raise ValueError("La taille doit être >= 1.")
    while len(vecteur) % taille != 0:
        vecteur.append(pad)
    result = []
    for i in range(0, len(vecteur), taille):
        result.append(vecteur[i:i + taille])
    return {"resultat": result}


# ═══════════════════════════════════════════════════════════════════════════════
# LAMBDA / FONCTIONNEL
# ═══════════════════════════════════════════════════════════════════════════════

_SAFE_BUILTINS = {
    "abs": abs, "min": min, "max": max, "sum": sum, "len": len,
    "round": round, "int": int, "float": float, "str": str,
    "True": True, "False": False, "None": None,
    "math": math,
}

_SAFE_OPS = {
    "somme": sum,
    "moyenne": lambda lst: sum(lst) / len(lst) if lst else 0,
    "max": max,
    "min": min,
    "produit": lambda lst: math.prod(lst),
    "count": len,
}


def _safe_eval(expression: str, variables: dict):
    ns = dict(_SAFE_BUILTINS)
    ns.update(variables)
    return eval(expression, {"__builtins__": {}}, ns)


def formule_isomitted(v: dict) -> dict:
    """ISOMITTED — vérifie si un paramètre est omis (None ou absent)."""
    val = v.get("valeur")
    return {"resultat": val is None}


def formule_lambda_val(v: dict) -> dict:
    """LAMBDA — crée et évalue une fonction lambda personnalisée."""
    params = v.get("parametres", {})
    expression = str(v["expression"])
    result = _safe_eval(expression, params)
    return {"resultat": result}


def formule_map_val(v: dict) -> dict:
    """MAP — applique une expression à chaque élément d'un tableau."""
    tableau = v["tableau"]
    expression = str(v["expression"])
    flat = tableau if not isinstance(tableau, list) else tableau
    if isinstance(flat, list) and flat and isinstance(flat[0], list):
        result = []
        for row in flat:
            result.append([_safe_eval(expression, {"x": x}) for x in row])
        return {"resultat": result}
    if isinstance(flat, list):
        return {"resultat": [_safe_eval(expression, {"x": x}) for x in flat]}
    return {"resultat": _safe_eval(expression, {"x": flat})}


def formule_reduce_val(v: dict) -> dict:
    """REDUCE — réduit un tableau avec un accumulateur."""
    tableau = list(v["tableau"])
    initial = v.get("initial", 0)
    expression = str(v["expression"])
    acc = initial
    for item in tableau:
        acc = _safe_eval(expression, {"acc": acc, "x": item})
    return {"resultat": acc}


def formule_scan_val(v: dict) -> dict:
    """SCAN — comme REDUCE mais renvoie les résultats intermédiaires."""
    tableau = list(v["tableau"])
    initial = v.get("initial", 0)
    expression = str(v["expression"])
    acc = initial
    results = []
    for item in tableau:
        acc = _safe_eval(expression, {"acc": acc, "x": item})
        results.append(acc)
    return {"resultat": results}
