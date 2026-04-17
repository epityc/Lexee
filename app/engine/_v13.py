"""
v13 — Web, Cube, Information & Maths complémentaires (Groupe 8).

28 nouvelles formules :
- Web : ENCODEURL, FILTERXML, WEBSERVICE
- Cube (stubs) : CUBEKPIMEMBER, CUBEMEMBER, CUBEMEMBERPROPERTY,
  CUBERANKEDMEMBER, CUBESET, CUBESETCOUNT, CUBEVALUE
- Information : ERROR.TYPE, INFO, ISFORMULA, ISNONTEXT, N, SHEET, SHEETS
- Maths complémentaires : AGGREGATE, ARABIC, CEILING.PRECISE, FACTDOUBLE,
  FLOOR.PRECISE, ISO.CEILING, MUNIT, MULTINOMIAL, ROMAN, SERIESSUM, SQRTPI
"""

from __future__ import annotations

import math
import platform
import re
import urllib.parse
import xml.etree.ElementTree as ET


# ═══════════════════════════════════════════════════════════════════════════════
# WEB
# ═══════════════════════════════════════════════════════════════════════════════


def formule_encodeurl(v: dict) -> dict:
    """ENCODEURL — encode une chaîne pour utilisation dans une URL."""
    texte = str(v["texte"])
    return {"resultat": urllib.parse.quote(texte, safe="")}


def formule_filterxml(v: dict) -> dict:
    """FILTERXML — extrait des données d'un contenu XML via XPath."""
    xml_str = str(v["xml"])
    xpath = str(v["xpath"])
    root = ET.fromstring(xml_str)
    elements = root.findall(xpath)
    if not elements:
        found = root.find(xpath)
        if found is not None:
            return {"resultat": found.text or ""}
        raise ValueError(f"XPath '{xpath}' n'a retourné aucun résultat.")
    if len(elements) == 1:
        return {"resultat": elements[0].text or ""}
    return {"resultat": [e.text or "" for e in elements]}


def formule_webservice(v: dict) -> dict:
    """WEBSERVICE — simule un appel de service web (stub sécurisé)."""
    url = str(v["url"])
    return {
        "resultat": f"WEBSERVICE({url})",
        "message": "Appels HTTP externes désactivés dans cet environnement.",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CUBE (stubs — pas de connexion OLAP)
# ═══════════════════════════════════════════════════════════════════════════════


def formule_cubekpimember(v: dict) -> dict:
    """CUBEKPIMEMBER — renvoie un KPI d'un cube OLAP (stub)."""
    connexion = str(v.get("connexion", ""))
    expression = str(v.get("expression", ""))
    return {
        "resultat": f"KPI({expression})",
        "message": "Connexion OLAP non disponible.",
    }


def formule_cubemember(v: dict) -> dict:
    """CUBEMEMBER — renvoie un membre d'un cube OLAP (stub)."""
    connexion = str(v.get("connexion", ""))
    expression = str(v.get("expression", ""))
    return {
        "resultat": f"MEMBER({expression})",
        "message": "Connexion OLAP non disponible.",
    }


def formule_cubememberproperty(v: dict) -> dict:
    """CUBEMEMBERPROPERTY — propriété d'un membre du cube (stub)."""
    connexion = str(v.get("connexion", ""))
    expression = str(v.get("expression", ""))
    propriete = str(v.get("propriete", ""))
    return {
        "resultat": f"PROP({expression},{propriete})",
        "message": "Connexion OLAP non disponible.",
    }


def formule_cuberankedmember(v: dict) -> dict:
    """CUBERANKEDMEMBER — membre classé dans un ensemble du cube (stub)."""
    connexion = str(v.get("connexion", ""))
    expression = str(v.get("expression", ""))
    rang = int(v.get("rang", 1))
    return {
        "resultat": f"RANKED({expression},{rang})",
        "message": "Connexion OLAP non disponible.",
    }


def formule_cubeset(v: dict) -> dict:
    """CUBESET — définit un ensemble de membres du cube (stub)."""
    connexion = str(v.get("connexion", ""))
    expression = str(v.get("expression", ""))
    return {
        "resultat": f"SET({expression})",
        "message": "Connexion OLAP non disponible.",
    }


def formule_cubesetcount(v: dict) -> dict:
    """CUBESETCOUNT — nombre d'éléments dans un ensemble du cube (stub)."""
    ensemble = str(v.get("ensemble", ""))
    return {
        "resultat": 0,
        "message": "Connexion OLAP non disponible.",
    }


def formule_cubevalue(v: dict) -> dict:
    """CUBEVALUE — valeur agrégée du cube (stub)."""
    connexion = str(v.get("connexion", ""))
    expression = str(v.get("expression", ""))
    return {
        "resultat": 0,
        "message": "Connexion OLAP non disponible.",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# INFORMATION
# ═══════════════════════════════════════════════════════════════════════════════

_ERROR_TYPES = {
    "#NULL!": 1, "#DIV/0!": 2, "#VALUE!": 3, "#REF!": 4,
    "#NAME?": 5, "#NUM!": 6, "#N/A": 7, "#GETTING_DATA": 8,
}


def formule_error_type(v: dict) -> dict:
    """ERROR.TYPE — renvoie le numéro correspondant à un type d'erreur."""
    val = str(v["valeur"])
    upper = val.upper().strip()
    code = _ERROR_TYPES.get(upper)
    if code is None:
        raise ValueError(f"'{val}' n'est pas une erreur reconnue.")
    return {"resultat": code}


def formule_info_val(v: dict) -> dict:
    """INFO — renvoie des informations sur l'environnement."""
    type_info = str(v["type_info"]).lower().strip()
    info_map = {
        "directory": "/",
        "numfile": 0,
        "origin": "$A:$A$1",
        "osversion": platform.platform(),
        "recalc": "Automatique",
        "release": "1.0",
        "system": platform.system()[:3].lower(),
    }
    if type_info not in info_map:
        raise ValueError(f"Type d'info '{type_info}' non reconnu.")
    return {"resultat": info_map[type_info]}


def formule_isformula(v: dict) -> dict:
    """ISFORMULA — vérifie si une valeur ressemble à une formule."""
    val = str(v["valeur"])
    return {"resultat": val.startswith("=")}


def formule_isnontext(v: dict) -> dict:
    """ISNONTEXT — renvoie VRAI si la valeur n'est pas du texte."""
    val = v["valeur"]
    return {"resultat": not isinstance(val, str)}


def formule_n_val(v: dict) -> dict:
    """N — convertit une valeur en nombre."""
    val = v["valeur"]
    if isinstance(val, bool):
        return {"resultat": 1 if val else 0}
    if isinstance(val, (int, float)):
        return {"resultat": float(val)}
    if isinstance(val, str):
        try:
            return {"resultat": float(val)}
        except ValueError:
            return {"resultat": 0}
    return {"resultat": 0}


def formule_sheet(v: dict) -> dict:
    """SHEET — renvoie le numéro de feuille (simulation mono-feuille)."""
    return {"resultat": 1}


def formule_sheets(v: dict) -> dict:
    """SHEETS — renvoie le nombre de feuilles (simulation)."""
    nb = int(v.get("nombre", 1))
    return {"resultat": nb}


# ═══════════════════════════════════════════════════════════════════════════════
# MATHS COMPLÉMENTAIRES
# ═══════════════════════════════════════════════════════════════════════════════


def formule_aggregate(v: dict) -> dict:
    """AGGREGATE — applique une fonction d'agrégation avec options d'exclusion."""
    num_fonction = int(v["num_fonction"])
    valeurs = [float(x) for x in v["valeurs"]]
    if not valeurs:
        raise ValueError("Liste de valeurs vide.")

    funcs = {
        1: lambda vs: sum(vs) / len(vs),       # AVERAGE
        2: lambda vs: len(vs),                   # COUNT
        3: lambda vs: len(vs),                   # COUNTA
        4: lambda vs: max(vs),                   # MAX
        5: lambda vs: min(vs),                   # MIN
        6: lambda vs: math.prod(vs),             # PRODUCT
        7: lambda vs: (sum((x - sum(vs)/len(vs))**2 for x in vs) / (len(vs)-1))**0.5 if len(vs) > 1 else 0,  # STDEV.S
        8: lambda vs: (sum((x - sum(vs)/len(vs))**2 for x in vs) / len(vs))**0.5,  # STDEV.P
        9: lambda vs: sum(vs),                   # SUM
        10: lambda vs: sum((x - sum(vs)/len(vs))**2 for x in vs) / (len(vs)-1) if len(vs) > 1 else 0,  # VAR.S
        11: lambda vs: sum((x - sum(vs)/len(vs))**2 for x in vs) / len(vs),  # VAR.P
        12: lambda vs: sorted(vs)[len(vs)//2] if len(vs) % 2 == 1 else (sorted(vs)[len(vs)//2-1]+sorted(vs)[len(vs)//2])/2,  # MEDIAN
        14: lambda vs: max(vs) - min(vs),        # LARGE-SMALL range
        19: lambda vs: sorted(vs)[len(vs)//2] if len(vs) % 2 == 1 else (sorted(vs)[len(vs)//2-1]+sorted(vs)[len(vs)//2])/2,  # MODE approx
    }
    fn = funcs.get(num_fonction)
    if fn is None:
        raise ValueError(f"Fonction d'agrégation {num_fonction} non supportée (1-12, 14, 19).")
    return {"resultat": fn(valeurs)}


def formule_arabic(v: dict) -> dict:
    """ARABIC — convertit un nombre romain en nombre arabe."""
    texte = str(v["texte"]).upper().strip()
    if not texte:
        return {"resultat": 0}
    negativ = texte.startswith("-")
    if negativ:
        texte = texte[1:]
    roman_vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    prev = 0
    for ch in reversed(texte):
        val = roman_vals.get(ch)
        if val is None:
            raise ValueError(f"Caractère romain invalide : '{ch}'.")
        if val < prev:
            total -= val
        else:
            total += val
        prev = val
    return {"resultat": -total if negativ else total}


def formule_ceiling_precise(v: dict) -> dict:
    """CEILING.PRECISE — arrondit au multiple supérieur le plus proche."""
    nombre = float(v["nombre"])
    precision = abs(float(v.get("precision", 1)))
    if precision == 0:
        return {"resultat": 0.0}
    return {"resultat": math.ceil(nombre / precision) * precision}


def formule_factdouble(v: dict) -> dict:
    """FACTDOUBLE — double factorielle n!! ."""
    n = int(v["nombre"])
    if n < -1:
        raise ValueError("Le nombre doit être >= -1.")
    if n <= 0:
        return {"resultat": 1}
    result = 1
    k = n
    while k > 0:
        result *= k
        k -= 2
    return {"resultat": result}


def formule_floor_precise(v: dict) -> dict:
    """FLOOR.PRECISE — arrondit au multiple inférieur le plus proche."""
    nombre = float(v["nombre"])
    precision = abs(float(v.get("precision", 1)))
    if precision == 0:
        return {"resultat": 0.0}
    return {"resultat": math.floor(nombre / precision) * precision}


def formule_iso_ceiling(v: dict) -> dict:
    """ISO.CEILING — arrondit au multiple entier supérieur (norme ISO)."""
    nombre = float(v["nombre"])
    precision = abs(float(v.get("precision", 1)))
    if precision == 0:
        return {"resultat": 0.0}
    return {"resultat": math.ceil(nombre / precision) * precision}


def formule_munit(v: dict) -> dict:
    """MUNIT — renvoie la matrice identité de dimension n."""
    n = int(v["dimension"])
    if n < 1:
        raise ValueError("La dimension doit être >= 1.")
    return {"resultat": [[1 if i == j else 0 for j in range(n)] for i in range(n)]}


def formule_multinomial(v: dict) -> dict:
    """MULTINOMIAL — coefficient multinomial (n1+n2+...)! / (n1!*n2!*...)."""
    valeurs = [int(x) for x in v["valeurs"]]
    if any(x < 0 for x in valeurs):
        raise ValueError("Toutes les valeurs doivent être >= 0.")
    total = sum(valeurs)
    num = math.factorial(total)
    denom = 1
    for x in valeurs:
        denom *= math.factorial(x)
    return {"resultat": num // denom}


def formule_roman(v: dict) -> dict:
    """ROMAN — convertit un nombre arabe en nombre romain."""
    n = int(v["nombre"])
    if n < 0 or n > 3999:
        raise ValueError("Le nombre doit être entre 0 et 3999.")
    if n == 0:
        return {"resultat": ""}
    vals = [
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
        (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
    ]
    result = []
    for val, sym in vals:
        while n >= val:
            result.append(sym)
            n -= val
    return {"resultat": "".join(result)}


def formule_seriessum(v: dict) -> dict:
    """SERIESSUM — somme d'une série de puissances Σ a_i * x^(n + i*m)."""
    x = float(v["x"])
    n = float(v["n"])
    m = float(v["m"])
    coefficients = [float(c) for c in v["coefficients"]]
    total = 0.0
    for i, a in enumerate(coefficients):
        total += a * (x ** (n + i * m))
    return {"resultat": total}


def formule_sqrtpi(v: dict) -> dict:
    """SQRTPI — racine carrée de (nombre × π)."""
    nombre = float(v["nombre"])
    if nombre < 0:
        raise ValueError("Le nombre doit être >= 0.")
    return {"resultat": math.sqrt(nombre * math.pi)}
