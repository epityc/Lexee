"""
v18 — Ingénierie & Nombres Complexes (Groupe 13).

25 nouvelles formules :
- Bessel : BESSELI, BESSELJ, BESSELK, BESSELY
- Complexes : COMPLEX, IMABS, IMAGINARY, IMARGUMENT, IMCONJUGATE,
  IMCOS, IMCOT, IMCSC, IMCSCH, IMDIV, IMEXP, IMLN, IMLOG10, IMLOG2,
  IMPOWER, IMPRODUCT, IMREAL, IMSEC, IMSECH, IMSIN
- Conversion : CONVERT
"""

from __future__ import annotations

import cmath
import math


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS — Complex string parse/format (Excel "3+4i" convention)
# ═══════════════════════════════════════════════════════════════════════════════


def _parse_complex(s) -> complex:
    if isinstance(s, (int, float)):
        return complex(s, 0)
    if isinstance(s, complex):
        return s
    s = str(s).strip().replace(" ", "")
    if not s:
        raise ValueError("Chaîne complexe vide.")
    if s.endswith("i") or s.endswith("j"):
        s = s[:-1] + "j"
    elif "j" not in s:
        return complex(float(s), 0)
    try:
        return complex(s)
    except ValueError:
        pass
    # Handle "3+4j" / "3-4j" without explicit j at end already handled
    # Try adding j if missing
    raise ValueError(f"Format complexe invalide : {s}")


def _format_complex(c: complex) -> str:
    r, im = c.real, c.imag
    if im == 0:
        return str(int(r)) if r == int(r) else str(r)
    if r == 0:
        if im == 1:
            return "i"
        if im == -1:
            return "-i"
        return f"{int(im)}i" if im == int(im) else f"{im}i"
    im_str = ""
    if im == 1:
        im_str = "+i"
    elif im == -1:
        im_str = "-i"
    elif im > 0:
        im_part = int(im) if im == int(im) else im
        im_str = f"+{im_part}i"
    else:
        im_part = int(im) if im == int(im) else im
        im_str = f"{im_part}i"
    r_str = str(int(r)) if r == int(r) else str(r)
    return f"{r_str}{im_str}"


# ═══════════════════════════════════════════════════════════════════════════════
# BESSEL FUNCTIONS (pure Python series)
# ═══════════════════════════════════════════════════════════════════════════════


def _bessel_j_real(n: float, x: float) -> float:
    """J_n for real n via series expansion."""
    total = 0.0
    for m in range(80):
        sign = (-1) ** m
        num = (x / 2) ** (2 * m + n)
        denom = math.factorial(m) * math.gamma(m + n + 1)
        total += sign * num / denom
    return total


def _bessel_i_real(n: float, x: float) -> float:
    """I_n for real n via series expansion."""
    total = 0.0
    for m in range(80):
        num = (x / 2) ** (2 * m + n)
        denom = math.factorial(m) * math.gamma(m + n + 1)
        total += num / denom
    return total


def _bessel_j(n: int, x: float) -> float:
    return _bessel_j_real(float(n), x)


def _bessel_i(n: int, x: float) -> float:
    return _bessel_i_real(float(n), x)


def _bessel_y(n: int, x: float) -> float:
    """Bessel Y_n(x) — limit formula for integer n."""
    if x <= 0:
        raise ValueError("x doit être > 0 pour BESSELY.")
    eps = 1e-3
    n_f = n + eps
    return (_bessel_j_real(n_f, x) * math.cos(n_f * math.pi) - _bessel_j_real(-n_f, x)) / math.sin(n_f * math.pi)


def _bessel_k(n: int, x: float) -> float:
    """Modified Bessel K_n(x) — limit formula for integer n."""
    if x <= 0:
        raise ValueError("x doit être > 0 pour BESSELK.")
    eps = 1e-3
    n_f = n + eps
    return (math.pi / 2) * (_bessel_i_real(-n_f, x) - _bessel_i_real(n_f, x)) / math.sin(n_f * math.pi)


def formule_besseli(v: dict) -> dict:
    """BESSELI — fonction de Bessel modifiée I_n(x)."""
    x = float(v["x"])
    n = int(v["n"])
    if n < 0:
        raise ValueError("n doit être >= 0.")
    return {"resultat": _bessel_i(n, x)}


def formule_besselj(v: dict) -> dict:
    """BESSELJ — fonction de Bessel J_n(x)."""
    x = float(v["x"])
    n = int(v["n"])
    if n < 0:
        raise ValueError("n doit être >= 0.")
    return {"resultat": _bessel_j(n, x)}


def formule_besselk(v: dict) -> dict:
    """BESSELK — fonction de Bessel modifiée K_n(x)."""
    x = float(v["x"])
    n = int(v["n"])
    if n < 0:
        raise ValueError("n doit être >= 0.")
    return {"resultat": _bessel_k(n, x)}


def formule_bessely(v: dict) -> dict:
    """BESSELY — fonction de Bessel Y_n(x)."""
    x = float(v["x"])
    n = int(v["n"])
    if n < 0:
        raise ValueError("n doit être >= 0.")
    return {"resultat": _bessel_y(n, x)}


# ═══════════════════════════════════════════════════════════════════════════════
# COMPLEX
# ═══════════════════════════════════════════════════════════════════════════════


def formule_complex_val(v: dict) -> dict:
    """COMPLEX — crée un nombre complexe à partir de partie réelle et imaginaire."""
    r = float(v["reel"])
    im = float(v["imaginaire"])
    return {"resultat": _format_complex(complex(r, im))}


# ═══════════════════════════════════════════════════════════════════════════════
# IM* — Opérations sur nombres complexes
# ═══════════════════════════════════════════════════════════════════════════════


def formule_imabs(v: dict) -> dict:
    """IMABS — module (valeur absolue) d'un nombre complexe."""
    c = _parse_complex(v["nombre"])
    return {"resultat": abs(c)}


def formule_imaginary(v: dict) -> dict:
    """IMAGINARY — partie imaginaire d'un nombre complexe."""
    c = _parse_complex(v["nombre"])
    return {"resultat": c.imag}


def formule_imargument(v: dict) -> dict:
    """IMARGUMENT — argument (angle en radians) d'un nombre complexe."""
    c = _parse_complex(v["nombre"])
    if c == 0:
        raise ValueError("L'argument de 0 n'est pas défini.")
    return {"resultat": cmath.phase(c)}


def formule_imconjugate(v: dict) -> dict:
    """IMCONJUGATE — conjugué d'un nombre complexe."""
    c = _parse_complex(v["nombre"])
    return {"resultat": _format_complex(c.conjugate())}


def formule_imcos(v: dict) -> dict:
    """IMCOS — cosinus d'un nombre complexe."""
    c = _parse_complex(v["nombre"])
    return {"resultat": _format_complex(cmath.cos(c))}


def formule_imcot(v: dict) -> dict:
    """IMCOT — cotangente d'un nombre complexe."""
    c = _parse_complex(v["nombre"])
    s = cmath.sin(c)
    if abs(s) < 1e-15:
        raise ValueError("Division par zéro (sin = 0).")
    return {"resultat": _format_complex(cmath.cos(c) / s)}


def formule_imcsc(v: dict) -> dict:
    """IMCSC — cosécante d'un nombre complexe."""
    c = _parse_complex(v["nombre"])
    s = cmath.sin(c)
    if abs(s) < 1e-15:
        raise ValueError("Division par zéro (sin = 0).")
    return {"resultat": _format_complex(1 / s)}


def formule_imcsch(v: dict) -> dict:
    """IMCSCH — cosécante hyperbolique d'un nombre complexe."""
    c = _parse_complex(v["nombre"])
    s = cmath.sinh(c)
    if abs(s) < 1e-15:
        raise ValueError("Division par zéro (sinh = 0).")
    return {"resultat": _format_complex(1 / s)}


def formule_imdiv(v: dict) -> dict:
    """IMDIV — division de deux nombres complexes."""
    a = _parse_complex(v["nombre1"])
    b = _parse_complex(v["nombre2"])
    if abs(b) < 1e-15:
        raise ValueError("Division par zéro.")
    return {"resultat": _format_complex(a / b)}


def formule_imexp(v: dict) -> dict:
    """IMEXP — exponentielle d'un nombre complexe."""
    c = _parse_complex(v["nombre"])
    return {"resultat": _format_complex(cmath.exp(c))}


def formule_imln(v: dict) -> dict:
    """IMLN — logarithme naturel d'un nombre complexe."""
    c = _parse_complex(v["nombre"])
    if abs(c) < 1e-15:
        raise ValueError("ln(0) n'est pas défini.")
    return {"resultat": _format_complex(cmath.log(c))}


def formule_imlog10(v: dict) -> dict:
    """IMLOG10 — logarithme base 10 d'un nombre complexe."""
    c = _parse_complex(v["nombre"])
    if abs(c) < 1e-15:
        raise ValueError("log10(0) n'est pas défini.")
    return {"resultat": _format_complex(cmath.log10(c))}


def formule_imlog2(v: dict) -> dict:
    """IMLOG2 — logarithme base 2 d'un nombre complexe."""
    c = _parse_complex(v["nombre"])
    if abs(c) < 1e-15:
        raise ValueError("log2(0) n'est pas défini.")
    return {"resultat": _format_complex(cmath.log(c) / cmath.log(2))}


def formule_impower(v: dict) -> dict:
    """IMPOWER — puissance d'un nombre complexe."""
    c = _parse_complex(v["nombre"])
    n = float(v["puissance"])
    if abs(c) < 1e-15 and n <= 0:
        raise ValueError("0 élevé à une puissance <= 0 n'est pas défini.")
    return {"resultat": _format_complex(c ** n)}


def formule_improduct(v: dict) -> dict:
    """IMPRODUCT — produit de nombres complexes."""
    nombres = v["nombres"]
    if not isinstance(nombres, list):
        nombres = [nombres]
    result = complex(1, 0)
    for n in nombres:
        result *= _parse_complex(n)
    return {"resultat": _format_complex(result)}


def formule_imreal(v: dict) -> dict:
    """IMREAL — partie réelle d'un nombre complexe."""
    c = _parse_complex(v["nombre"])
    return {"resultat": c.real}


def formule_imsec(v: dict) -> dict:
    """IMSEC — sécante d'un nombre complexe."""
    c = _parse_complex(v["nombre"])
    cs = cmath.cos(c)
    if abs(cs) < 1e-15:
        raise ValueError("Division par zéro (cos = 0).")
    return {"resultat": _format_complex(1 / cs)}


def formule_imsech(v: dict) -> dict:
    """IMSECH — sécante hyperbolique d'un nombre complexe."""
    c = _parse_complex(v["nombre"])
    ch = cmath.cosh(c)
    if abs(ch) < 1e-15:
        raise ValueError("Division par zéro (cosh = 0).")
    return {"resultat": _format_complex(1 / ch)}


def formule_imsin(v: dict) -> dict:
    """IMSIN — sinus d'un nombre complexe."""
    c = _parse_complex(v["nombre"])
    return {"resultat": _format_complex(cmath.sin(c))}


def formule_imsinh(v: dict) -> dict:
    """IMSINH — sinus hyperbolique d'un nombre complexe."""
    c = _parse_complex(v["nombre"])
    return {"resultat": _format_complex(cmath.sinh(c))}


def formule_imsqrt(v: dict) -> dict:
    """IMSQRT — racine carrée d'un nombre complexe."""
    c = _parse_complex(v["nombre"])
    return {"resultat": _format_complex(cmath.sqrt(c))}


def formule_imsub(v: dict) -> dict:
    """IMSUB — soustraction de deux nombres complexes."""
    a = _parse_complex(v["nombre1"])
    b = _parse_complex(v["nombre2"])
    return {"resultat": _format_complex(a - b)}


def formule_imsum(v: dict) -> dict:
    """IMSUM — somme de nombres complexes."""
    nombres = v["nombres"]
    if not isinstance(nombres, list):
        nombres = [nombres]
    result = complex(0, 0)
    for n in nombres:
        result += _parse_complex(n)
    return {"resultat": _format_complex(result)}


# ═══════════════════════════════════════════════════════════════════════════════
# CONVERT — Conversion d'unités
# ═══════════════════════════════════════════════════════════════════════════════

_CONVERT_TABLE: dict[str, dict[str, float]] = {
    "mass": {
        "g": 1.0, "kg": 1000.0, "mg": 0.001, "lbm": 453.59237,
        "ozm": 28.349523125, "ton": 907184.74, "tonne": 1e6,
        "sg": 14593.903, "grain": 0.06479891, "cwt": 45359.237,
        "uk_cwt": 50802.34544, "stone": 6350.29318,
    },
    "distance": {
        "m": 1.0, "km": 1000.0, "cm": 0.01, "mm": 0.001,
        "mi": 1609.344, "yd": 0.9144, "ft": 0.3048, "in": 0.0254,
        "Nmi": 1852.0, "ang": 1e-10, "um": 1e-6, "pica": 0.00423333333,
    },
    "time": {
        "s": 1.0, "sec": 1.0, "min": 60.0, "hr": 3600.0,
        "day": 86400.0, "yr": 31557600.0,
    },
    "temperature": {
        "C": "C", "F": "F", "K": "K",
    },
    "volume": {
        "l": 1.0, "lt": 1.0, "ml": 0.001, "gal": 3.785411784,
        "qt": 0.946352946, "pt": 0.473176473, "cup": 0.236588236,
        "oz": 0.029573529, "tbs": 0.014786764, "tsp": 0.004928921,
        "uk_gal": 4.54609, "uk_pt": 0.56826125,
    },
    "area": {
        "m2": 1.0, "km2": 1e6, "ha": 10000.0, "acre": 4046.8564224,
        "ft2": 0.09290304, "in2": 0.00064516, "yd2": 0.83612736,
        "mi2": 2589988.110336,
    },
    "speed": {
        "m/s": 1.0, "km/h": 1 / 3.6, "mph": 0.44704, "kn": 0.514444,
    },
    "energy": {
        "J": 1.0, "kJ": 1000.0, "cal": 4.1868, "kcal": 4186.8,
        "BTU": 1055.05585, "eV": 1.602176634e-19, "Wh": 3600.0, "kWh": 3.6e6,
    },
    "power": {
        "W": 1.0, "kW": 1000.0, "MW": 1e6, "HP": 745.69987158,
    },
    "pressure": {
        "Pa": 1.0, "kPa": 1000.0, "atm": 101325.0, "bar": 100000.0,
        "mmHg": 133.322, "psi": 6894.757, "Torr": 133.322,
    },
    "force": {
        "N": 1.0, "kN": 1000.0, "lbf": 4.44822, "dyn": 1e-5,
    },
    "information": {
        "bit": 1.0, "byte": 8.0, "kbit": 1000.0, "kbyte": 8000.0,
        "Mbit": 1e6, "Mbyte": 8e6, "Gbit": 1e9, "Gbyte": 8e9,
        "Tbit": 1e12, "Tbyte": 8e12,
    },
}


def _convert_temp(val: float, from_u: str, to_u: str) -> float:
    if from_u == to_u:
        return val
    if from_u == "C":
        k = val + 273.15
    elif from_u == "F":
        k = (val - 32) * 5 / 9 + 273.15
    else:
        k = val
    if to_u == "C":
        return k - 273.15
    if to_u == "F":
        return (k - 273.15) * 9 / 5 + 32
    return k


def formule_convert(v: dict) -> dict:
    """CONVERT — convertit une valeur d'une unité à une autre."""
    nombre = float(v["nombre"])
    de = str(v["de"])
    a = str(v["a"])

    if de == a:
        return {"resultat": nombre}

    for category, units in _CONVERT_TABLE.items():
        if de in units and a in units:
            if category == "temperature":
                return {"resultat": _convert_temp(nombre, de, a)}
            return {"resultat": nombre * units[de] / units[a]}

    raise ValueError(f"Conversion non supportée : {de} → {a}")
