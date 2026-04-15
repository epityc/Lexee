"""
v7 — Ingénierie (suite) & Nombres Complexes (Groupe 2).

29 nouvelles formules :
- Fonctions d'erreur avancées : ERF.PRECISE, ERFC, ERFC.PRECISE, GESTEP
- Conversions hexa : HEX2BIN, HEX2OCT
- Nombres complexes (23) : toutes les fonctions IM* d'Excel

HEX2DEC existe déjà en v5.
"""

from __future__ import annotations

import cmath
import math
import re


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS D'ERREUR & STEP (ERF.PRECISE, ERFC, ERFC.PRECISE, GESTEP)
# ═══════════════════════════════════════════════════════════════════════════════


def formule_erf_precis(v: dict) -> dict:
    """ERF.PRECISE — fonction d'erreur (signature simple, un seul argument)."""
    x = float(v["x"])
    return {"resultat": round(math.erf(x), 10)}


def formule_erfc(v: dict) -> dict:
    """ERFC — fonction d'erreur complémentaire : 1 - erf(x)."""
    x = float(v["x"])
    return {"resultat": round(math.erfc(x), 10)}


def formule_erfc_precis(v: dict) -> dict:
    """ERFC.PRECISE — identique à ERFC."""
    x = float(v["x"])
    return {"resultat": round(math.erfc(x), 10)}


def formule_gestep(v: dict) -> dict:
    """GESTEP — 1 si nombre >= seuil, 0 sinon."""
    nombre = float(v["nombre"])
    seuil = float(v.get("seuil", 0))
    return {"resultat": 1 if nombre >= seuil else 0}


# ═══════════════════════════════════════════════════════════════════════════════
# CONVERSIONS HEXADÉCIMALES (HEX2BIN, HEX2OCT)
# ═══════════════════════════════════════════════════════════════════════════════


def formule_hex2bin(v: dict) -> dict:
    """HEX2BIN — hexadécimal → binaire."""
    texte = str(v["nombre"]).strip().upper()
    try:
        n = int(texte, 16)
    except ValueError:
        raise ValueError(f"'{texte}' n'est pas un hexadécimal valide.")
    return {"resultat": format(n, "b")}


def formule_hex2oct(v: dict) -> dict:
    """HEX2OCT — hexadécimal → octal."""
    texte = str(v["nombre"]).strip().upper()
    try:
        n = int(texte, 16)
    except ValueError:
        raise ValueError(f"'{texte}' n'est pas un hexadécimal valide.")
    return {"resultat": format(n, "o")}


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS NOMBRES COMPLEXES
# ═══════════════════════════════════════════════════════════════════════════════


def _parse_complex(s) -> complex:
    """Accepte 'a+bi', 'a+bj', 'a', 'bi', 'i', '-j'... Retourne un complex Python."""
    if isinstance(s, (int, float)):
        return complex(s, 0)
    if isinstance(s, complex):
        return s
    texte = str(s).strip().replace(" ", "")
    if not texte:
        raise ValueError("Chaîne complexe vide.")
    # Normalisation : 'i' → 'j', '+j'/'-j' isolés → '+1j'/'-1j'
    texte = texte.replace("i", "j")
    texte = re.sub(r"([+-])j", r"\g<1>1j", texte)
    if texte == "j":
        texte = "1j"
    try:
        return complex(texte)
    except ValueError:
        raise ValueError(f"Format complexe invalide : '{s}'")


def _fmt_nombre(x: float) -> str:
    if abs(x) < 1e-12:
        return "0"
    if x == int(x):
        return str(int(x))
    return f"{x:.10g}"


def _format_complex(c: complex, suffixe: str = "i") -> str:
    """Formate un complex Python en 'a+bi' à la mode Excel."""
    if suffixe not in ("i", "j"):
        raise ValueError("suffixe doit être 'i' ou 'j'.")
    reel = c.real if abs(c.real) > 1e-12 else 0.0
    imag = c.imag if abs(c.imag) > 1e-12 else 0.0

    if imag == 0:
        return _fmt_nombre(reel)
    if reel == 0:
        if imag == 1:
            return suffixe
        if imag == -1:
            return "-" + suffixe
        return f"{_fmt_nombre(imag)}{suffixe}"

    part_r = _fmt_nombre(reel)
    if imag == 1:
        part_i = f"+{suffixe}"
    elif imag == -1:
        part_i = f"-{suffixe}"
    elif imag > 0:
        part_i = f"+{_fmt_nombre(imag)}{suffixe}"
    else:
        part_i = f"{_fmt_nombre(imag)}{suffixe}"
    return part_r + part_i


def _sortie_complexe(c: complex, suffixe: str = "i") -> dict:
    return {
        "complexe": _format_complex(c, suffixe),
        "reel": round(c.real, 10) if abs(c.real) > 1e-12 else 0.0,
        "imaginaire": round(c.imag, 10) if abs(c.imag) > 1e-12 else 0.0,
    }


def _detecte_suffixe(v: dict, *sources: str) -> str:
    """Reprend le suffixe (i/j) explicite ou déduit des entrées."""
    if "suffixe" in v and v["suffixe"] in ("i", "j"):
        return v["suffixe"]
    for key in sources:
        val = v.get(key)
        if isinstance(val, str) and "j" in val.lower():
            # Si l'entrée est du J, on garde J
            if re.search(r"\dj|[+\-]j|^j", val.replace(" ", "")):
                return "j"
    return "i"


# ═══════════════════════════════════════════════════════════════════════════════
# EXTRACTION & PROPRIÉTÉS (IMABS, IMAGINARY, IMARGUMENT, IMCONJUGATE, IMREAL)
# ═══════════════════════════════════════════════════════════════════════════════


def formule_im_abs(v: dict) -> dict:
    """IMABS — module |z| = √(a² + b²)."""
    c = _parse_complex(v["complexe"])
    return {"resultat": round(abs(c), 10)}


def formule_im_part_imag(v: dict) -> dict:
    """IMAGINARY — partie imaginaire."""
    c = _parse_complex(v["complexe"])
    return {"resultat": round(c.imag, 10)}


def formule_im_part_reelle(v: dict) -> dict:
    """IMREAL — partie réelle."""
    c = _parse_complex(v["complexe"])
    return {"resultat": round(c.real, 10)}


def formule_im_argument(v: dict) -> dict:
    """IMARGUMENT — argument θ (radians) = atan2(b, a)."""
    c = _parse_complex(v["complexe"])
    if c == 0:
        raise ValueError("Argument indéfini pour z = 0.")
    return {"resultat": round(cmath.phase(c), 10)}


def formule_im_conjugue(v: dict) -> dict:
    """IMCONJUGATE — conjugué a - bi."""
    c = _parse_complex(v["complexe"])
    suffixe = _detecte_suffixe(v, "complexe")
    return _sortie_complexe(c.conjugate(), suffixe)


# ═══════════════════════════════════════════════════════════════════════════════
# OPÉRATIONS ARITHMÉTIQUES (IMDIV, IMSUB, IMSUM, IMPRODUCT, IMPOWER)
# ═══════════════════════════════════════════════════════════════════════════════


def formule_im_div(v: dict) -> dict:
    """IMDIV — division z1 / z2."""
    z1 = _parse_complex(v["z1"])
    z2 = _parse_complex(v["z2"])
    if z2 == 0:
        raise ValueError("Division par zéro.")
    suffixe = _detecte_suffixe(v, "z1", "z2")
    return _sortie_complexe(z1 / z2, suffixe)


def formule_im_sub(v: dict) -> dict:
    """IMSUB — soustraction z1 - z2."""
    z1 = _parse_complex(v["z1"])
    z2 = _parse_complex(v["z2"])
    suffixe = _detecte_suffixe(v, "z1", "z2")
    return _sortie_complexe(z1 - z2, suffixe)


def formule_im_sum(v: dict) -> dict:
    """IMSUM — somme d'une liste de complexes."""
    complexes = v["complexes"]
    if not complexes:
        raise ValueError("Liste vide.")
    total = complex(0)
    for z in complexes:
        total += _parse_complex(z)
    suffixe = _detecte_suffixe(v, *[f"[{i}]" for i in range(len(complexes))])
    # Fallback simple : détecter sur le premier
    if "suffixe" not in v:
        first = str(complexes[0])
        suffixe = "j" if "j" in first.lower() and "i" not in first.lower() else "i"
    return _sortie_complexe(total, suffixe)


def formule_im_product(v: dict) -> dict:
    """IMPRODUCT — produit d'une liste de complexes."""
    complexes = v["complexes"]
    if not complexes:
        raise ValueError("Liste vide.")
    produit = complex(1)
    for z in complexes:
        produit *= _parse_complex(z)
    if "suffixe" in v:
        suffixe = v["suffixe"]
    else:
        first = str(complexes[0])
        suffixe = "j" if "j" in first.lower() and "i" not in first.lower() else "i"
    return _sortie_complexe(produit, suffixe)


def formule_im_power(v: dict) -> dict:
    """IMPOWER — z^n (n réel ou entier)."""
    z = _parse_complex(v["complexe"])
    n = float(v["puissance"])
    if z == 0 and n <= 0:
        raise ValueError("0 élevé à une puissance <= 0 est indéfini.")
    suffixe = _detecte_suffixe(v, "complexe")
    return _sortie_complexe(z ** n, suffixe)


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS EXPONENTIELLES & LOGARITHMIQUES (IMEXP, IMLN, IMLOG10, IMLOG2, IMSQRT)
# ═══════════════════════════════════════════════════════════════════════════════


def formule_im_exp(v: dict) -> dict:
    """IMEXP — e^z."""
    z = _parse_complex(v["complexe"])
    suffixe = _detecte_suffixe(v, "complexe")
    return _sortie_complexe(cmath.exp(z), suffixe)


def formule_im_ln(v: dict) -> dict:
    """IMLN — logarithme naturel."""
    z = _parse_complex(v["complexe"])
    if z == 0:
        raise ValueError("ln(0) indéfini.")
    suffixe = _detecte_suffixe(v, "complexe")
    return _sortie_complexe(cmath.log(z), suffixe)


def formule_im_log10(v: dict) -> dict:
    """IMLOG10 — logarithme décimal."""
    z = _parse_complex(v["complexe"])
    if z == 0:
        raise ValueError("log(0) indéfini.")
    suffixe = _detecte_suffixe(v, "complexe")
    return _sortie_complexe(cmath.log10(z), suffixe)


def formule_im_log2(v: dict) -> dict:
    """IMLOG2 — logarithme base 2."""
    z = _parse_complex(v["complexe"])
    if z == 0:
        raise ValueError("log(0) indéfini.")
    suffixe = _detecte_suffixe(v, "complexe")
    return _sortie_complexe(cmath.log(z, 2), suffixe)


def formule_im_sqrt(v: dict) -> dict:
    """IMSQRT — racine carrée complexe."""
    z = _parse_complex(v["complexe"])
    suffixe = _detecte_suffixe(v, "complexe")
    return _sortie_complexe(cmath.sqrt(z), suffixe)


# ═══════════════════════════════════════════════════════════════════════════════
# TRIGONOMÉTRIQUES & HYPERBOLIQUES COMPLEXES
# IMCOS, IMSIN, IMCOT, IMCSC, IMCSCH, IMSEC, IMSECH, IMSINH
# ═══════════════════════════════════════════════════════════════════════════════


def formule_im_cos(v: dict) -> dict:
    """IMCOS — cos(z)."""
    z = _parse_complex(v["complexe"])
    suffixe = _detecte_suffixe(v, "complexe")
    return _sortie_complexe(cmath.cos(z), suffixe)


def formule_im_sin(v: dict) -> dict:
    """IMSIN — sin(z)."""
    z = _parse_complex(v["complexe"])
    suffixe = _detecte_suffixe(v, "complexe")
    return _sortie_complexe(cmath.sin(z), suffixe)


def formule_im_sinh(v: dict) -> dict:
    """IMSINH — sinh(z)."""
    z = _parse_complex(v["complexe"])
    suffixe = _detecte_suffixe(v, "complexe")
    return _sortie_complexe(cmath.sinh(z), suffixe)


def formule_im_cot(v: dict) -> dict:
    """IMCOT — cot(z) = cos(z) / sin(z)."""
    z = _parse_complex(v["complexe"])
    s = cmath.sin(z)
    if s == 0:
        raise ValueError("sin(z) = 0 : cot indéfini.")
    suffixe = _detecte_suffixe(v, "complexe")
    return _sortie_complexe(cmath.cos(z) / s, suffixe)


def formule_im_csc(v: dict) -> dict:
    """IMCSC — csc(z) = 1 / sin(z)."""
    z = _parse_complex(v["complexe"])
    s = cmath.sin(z)
    if s == 0:
        raise ValueError("sin(z) = 0 : csc indéfini.")
    suffixe = _detecte_suffixe(v, "complexe")
    return _sortie_complexe(1 / s, suffixe)


def formule_im_csch(v: dict) -> dict:
    """IMCSCH — csch(z) = 1 / sinh(z)."""
    z = _parse_complex(v["complexe"])
    s = cmath.sinh(z)
    if s == 0:
        raise ValueError("sinh(z) = 0 : csch indéfini.")
    suffixe = _detecte_suffixe(v, "complexe")
    return _sortie_complexe(1 / s, suffixe)


def formule_im_sec(v: dict) -> dict:
    """IMSEC — sec(z) = 1 / cos(z)."""
    z = _parse_complex(v["complexe"])
    c = cmath.cos(z)
    if c == 0:
        raise ValueError("cos(z) = 0 : sec indéfini.")
    suffixe = _detecte_suffixe(v, "complexe")
    return _sortie_complexe(1 / c, suffixe)


def formule_im_sech(v: dict) -> dict:
    """IMSECH — sech(z) = 1 / cosh(z)."""
    z = _parse_complex(v["complexe"])
    c = cmath.cosh(z)
    if c == 0:
        raise ValueError("cosh(z) = 0 : sech indéfini.")
    suffixe = _detecte_suffixe(v, "complexe")
    return _sortie_complexe(1 / c, suffixe)
