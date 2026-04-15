"""
v6 — Ingénierie & Mathématiques Avancées (Groupe 1).

21 nouvelles formules : fonctions hyperboliques, trigonométriques réciproques,
conversions de bases, fonctions de Bessel, nombres complexes.

Les 9 autres du groupe (BIN2HEX, BITAND, BITOR, BITXOR, CONVERT, DEC2BIN,
DEC2HEX, DELTA, ERF) existent déjà en v5.
"""

from __future__ import annotations

import math


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS HYPERBOLIQUES RÉCIPROQUES (ACOSH, ASINH, ATANH, COSH)
# ═══════════════════════════════════════════════════════════════════════════════


def formule_acosh(v: dict) -> dict:
    """ACOSH — argument cosinus hyperbolique. x >= 1 requis."""
    x = float(v["x"])
    if x < 1:
        raise ValueError("x doit être >= 1.")
    return {"resultat": round(math.acosh(x), 10)}


def formule_asinh(v: dict) -> dict:
    """ASINH — argument sinus hyperbolique."""
    x = float(v["x"])
    return {"resultat": round(math.asinh(x), 10)}


def formule_atanh(v: dict) -> dict:
    """ATANH — argument tangente hyperbolique. -1 < x < 1 requis."""
    x = float(v["x"])
    if not -1 < x < 1:
        raise ValueError("x doit être strictement entre -1 et 1.")
    return {"resultat": round(math.atanh(x), 10)}


def formule_cosh(v: dict) -> dict:
    """COSH — cosinus hyperbolique."""
    x = float(v["x"])
    return {"resultat": round(math.cosh(x), 10)}


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS TRIGONOMÉTRIQUES RÉCIPROQUES (COT, COTH, CSC, CSCH)
# ═══════════════════════════════════════════════════════════════════════════════


def formule_cot(v: dict) -> dict:
    """COT — cotangente (1/tan)."""
    x = float(v["x"])
    t = math.tan(x)
    if t == 0:
        raise ValueError("tan(x) = 0 : cotangente non définie.")
    return {"resultat": round(1 / t, 10)}


def formule_coth(v: dict) -> dict:
    """COTH — cotangente hyperbolique (1/tanh). x != 0."""
    x = float(v["x"])
    if x == 0:
        raise ValueError("x = 0 : coth non définie.")
    return {"resultat": round(1 / math.tanh(x), 10)}


def formule_csc(v: dict) -> dict:
    """CSC — cosécante (1/sin)."""
    x = float(v["x"])
    s = math.sin(x)
    if s == 0:
        raise ValueError("sin(x) = 0 : cosécante non définie.")
    return {"resultat": round(1 / s, 10)}


def formule_csch(v: dict) -> dict:
    """CSCH — cosécante hyperbolique (1/sinh). x != 0."""
    x = float(v["x"])
    if x == 0:
        raise ValueError("x = 0 : csch non définie.")
    return {"resultat": round(1 / math.sinh(x), 10)}


# ═══════════════════════════════════════════════════════════════════════════════
# CONVERSIONS DE BASES (BASE, DECIMAL, BIN2DEC, BIN2OCT, DEC2OCT)
# ═══════════════════════════════════════════════════════════════════════════════


_BASE_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _to_base(n: int, base: int) -> str:
    if n == 0:
        return "0"
    neg = n < 0
    n = abs(n)
    out = ""
    while n > 0:
        n, r = divmod(n, base)
        out = _BASE_CHARS[r] + out
    return ("-" + out) if neg else out


def formule_base(v: dict) -> dict:
    """BASE — convertit un entier décimal en chaîne dans une base (2-36)."""
    nombre = int(v["nombre"])
    base = int(v["base"])
    longueur_min = int(v.get("longueur_min", 0))
    if not 2 <= base <= 36:
        raise ValueError("base doit être entre 2 et 36.")
    if nombre < 0:
        raise ValueError("nombre doit être >= 0.")
    s = _to_base(nombre, base)
    if longueur_min > len(s):
        s = s.zfill(longueur_min)
    return {"resultat": s}


def formule_decimal_base(v: dict) -> dict:
    """DECIMAL — convertit une chaîne d'une base donnée (2-36) en décimal."""
    texte = str(v["texte"]).strip().upper()
    base = int(v["base"])
    if not 2 <= base <= 36:
        raise ValueError("base doit être entre 2 et 36.")
    try:
        return {"resultat": int(texte, base)}
    except ValueError:
        raise ValueError(f"Chaîne '{texte}' invalide en base {base}.")


def formule_bin2dec(v: dict) -> dict:
    """BIN2DEC — binaire vers décimal."""
    texte = str(v["nombre"]).strip()
    try:
        return {"resultat": int(texte, 2)}
    except ValueError:
        raise ValueError(f"'{texte}' n'est pas un binaire valide.")


def formule_bin2oct(v: dict) -> dict:
    """BIN2OCT — binaire vers octal."""
    texte = str(v["nombre"]).strip()
    try:
        n = int(texte, 2)
    except ValueError:
        raise ValueError(f"'{texte}' n'est pas un binaire valide.")
    return {"resultat": format(n, "o")}


def formule_dec2oct(v: dict) -> dict:
    """DEC2OCT — décimal vers octal."""
    n = int(v["nombre"])
    if n < 0:
        raise ValueError("Nombre négatif non supporté.")
    return {"resultat": format(n, "o")}


# ═══════════════════════════════════════════════════════════════════════════════
# OPÉRATIONS BIT À BIT (BITLSHIFT, BITRSHIFT)
# ═══════════════════════════════════════════════════════════════════════════════


def formule_bit_lshift(v: dict) -> dict:
    """BITLSHIFT — décalage binaire à gauche."""
    n = int(v["nombre"])
    k = int(v["decalage"])
    if n < 0:
        raise ValueError("nombre doit être >= 0.")
    if k < 0:
        # décalage négatif = décalage à droite
        return {"resultat": n >> abs(k)}
    return {"resultat": n << k}


def formule_bit_rshift(v: dict) -> dict:
    """BITRSHIFT — décalage binaire à droite."""
    n = int(v["nombre"])
    k = int(v["decalage"])
    if n < 0:
        raise ValueError("nombre doit être >= 0.")
    if k < 0:
        return {"resultat": n << abs(k)}
    return {"resultat": n >> k}


# ═══════════════════════════════════════════════════════════════════════════════
# COMBINATOIRE & COMPLEXES (COMBINA, COMPLEX)
# ═══════════════════════════════════════════════════════════════════════════════


def formule_combinaison_rep(v: dict) -> dict:
    """COMBINA — combinaisons avec répétition : C(n+k-1, k)."""
    n = int(v["n"])
    k = int(v["k"])
    if n < 0 or k < 0:
        raise ValueError("n et k doivent être >= 0.")
    if n == 0 and k > 0:
        return {"resultat": 0}
    return {"resultat": math.comb(n + k - 1, k)}


def formule_complexe(v: dict) -> dict:
    """COMPLEX — construit une représentation texte d'un nombre complexe."""
    reel = float(v["reel"])
    imag = float(v["imaginaire"])
    suffixe = str(v.get("suffixe", "i"))
    if suffixe not in ("i", "j"):
        raise ValueError("suffixe doit être 'i' ou 'j'.")

    def fmt(x: float) -> str:
        if x == int(x):
            return str(int(x))
        return f"{x:g}"

    if imag == 0:
        texte = fmt(reel)
    elif reel == 0:
        if imag == 1:
            texte = suffixe
        elif imag == -1:
            texte = "-" + suffixe
        else:
            texte = f"{fmt(imag)}{suffixe}"
    else:
        part_r = fmt(reel)
        if imag == 1:
            part_i = f"+{suffixe}"
        elif imag == -1:
            part_i = f"-{suffixe}"
        elif imag > 0:
            part_i = f"+{fmt(imag)}{suffixe}"
        else:
            part_i = f"{fmt(imag)}{suffixe}"
        texte = part_r + part_i

    return {"complexe": texte, "reel": reel, "imaginaire": imag}


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS DE BESSEL (BESSELI, BESSELJ, BESSELK, BESSELY)
# ═══════════════════════════════════════════════════════════════════════════════

_GAMMA_EULER = 0.5772156649015329


def _bessel_j(x: float, n: int) -> float:
    """Série entière pour J_n(x), n >= 0 entier."""
    if n < 0:
        raise ValueError("n doit être >= 0.")
    if x == 0:
        return 1.0 if n == 0 else 0.0

    half = x / 2.0
    # Terme initial : (x/2)^n / n!
    term = 1.0
    for i in range(1, n + 1):
        term *= half / i

    result = term
    k = 1
    sign = -1
    while k < 200:
        term *= half * half / (k * (k + n))
        contribution = sign * term
        result += contribution
        if abs(contribution) < 1e-16 * (abs(result) + 1e-20):
            break
        k += 1
        sign = -sign
    return result


def _bessel_i(x: float, n: int) -> float:
    """Série entière pour I_n(x), n >= 0 entier."""
    if n < 0:
        raise ValueError("n doit être >= 0.")
    if x == 0:
        return 1.0 if n == 0 else 0.0

    half = x / 2.0
    term = 1.0
    for i in range(1, n + 1):
        term *= half / i

    result = term
    k = 1
    while k < 500:
        term *= half * half / (k * (k + n))
        result += term
        if term < 1e-18 * (abs(result) + 1e-20):
            break
        k += 1
    return result


def formule_bessel_j(v: dict) -> dict:
    """BESSELJ — fonction de Bessel de première espèce J_n(x)."""
    x = float(v["x"])
    n = int(v["n"])
    if n < 0:
        raise ValueError("n doit être >= 0.")
    return {"resultat": round(_bessel_j(x, n), 10)}


def formule_bessel_i(v: dict) -> dict:
    """BESSELI — fonction de Bessel modifiée de première espèce I_n(x)."""
    x = float(v["x"])
    n = int(v["n"])
    if n < 0:
        raise ValueError("n doit être >= 0.")
    return {"resultat": round(_bessel_i(x, n), 10)}


def _psi(m: int) -> float:
    """Digamma entier : ψ(1) = -γ, ψ(m+1) = -γ + H_m."""
    if m < 1:
        raise ValueError("ψ défini pour m >= 1.")
    s = -_GAMMA_EULER
    for k in range(1, m):
        s += 1.0 / k
    return s


def formule_bessel_y(v: dict) -> dict:
    """BESSELY — fonction de Bessel de deuxième espèce Y_n(x). x > 0."""
    x = float(v["x"])
    n = int(v["n"])
    if x <= 0:
        raise ValueError("x doit être > 0.")
    if n < 0:
        raise ValueError("n doit être >= 0.")

    half = x / 2.0
    ln_half = math.log(half)

    # Partie 1 : -(1/π)(x/2)^(-n) Σ_{k=0}^{n-1} (n-k-1)!/k! * (x/2)^(2k)
    part1 = 0.0
    if n > 0:
        s1 = 0.0
        for k in range(n):
            s1 += math.factorial(n - k - 1) / math.factorial(k) * half ** (2 * k)
        part1 = -(half ** (-n)) * s1 / math.pi

    # Partie 2 : (2/π) ln(x/2) J_n(x)
    part2 = (2 / math.pi) * ln_half * _bessel_j(x, n)

    # Partie 3 : -(1/π)(x/2)^n Σ_{k=0}^∞ (-1)^k [ψ(k+1) + ψ(n+k+1)] (x/2)^(2k)
    #            / (k!(n+k)!)
    s3 = 0.0
    k = 0
    sign = 1
    while k < 200:
        coeff = (_psi(k + 1) + _psi(n + k + 1)) / (
            math.factorial(k) * math.factorial(n + k)
        )
        term = sign * coeff * half ** (2 * k)
        s3 += term
        if k > n and abs(term) < 1e-18 * (abs(s3) + 1e-20):
            break
        k += 1
        sign = -sign
    part3 = -(half ** n) * s3 / math.pi

    return {"resultat": round(part1 + part2 + part3, 8)}


def formule_bessel_k(v: dict) -> dict:
    """BESSELK — fonction de Bessel modifiée de deuxième espèce K_n(x)."""
    x = float(v["x"])
    n = int(v["n"])
    if x <= 0:
        raise ValueError("x doit être > 0.")
    if n < 0:
        raise ValueError("n doit être >= 0.")

    # K_n(x) = ∫[0,∞) e^(-x cosh t) cosh(n t) dt
    # Intégration de Simpson sur [0, L] où L = 20 suffit (décroissance double-exp)
    L = 20.0
    N = 4000  # intervalles (pair pour Simpson)
    h = L / N

    def f(t: float) -> float:
        return math.exp(-x * math.cosh(t)) * math.cosh(n * t)

    total = f(0.0) + f(L)
    for i in range(1, N):
        t = i * h
        total += (4 if i % 2 else 2) * f(t)
    integrale = total * h / 3

    return {"resultat": round(integrale, 8)}
