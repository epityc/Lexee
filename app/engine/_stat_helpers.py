"""
Primitives numériques pour les distributions statistiques.

Fournit les fonctions de base (gamma incomplet, bêta incomplet, CDF/PPF normale)
utilisées par _v9.py et _v10.py.
"""

from __future__ import annotations

import math


# ═══════════════════════════════════════════════════════════════════════════════
# GAMMA INCOMPLET RÉGULARISÉ  P(a, x) = γ(a,x) / Γ(a)
# ═══════════════════════════════════════════════════════════════════════════════

def _gamma_series(a: float, x: float) -> float:
    """P(a,x) par développement en série — converge bien quand x < a+1."""
    if x < 0:
        return 0.0
    if x == 0:
        return 0.0
    ap = a
    s = 1.0 / a
    ds = s
    for _ in range(300):
        ap += 1
        ds *= x / ap
        s += ds
        if abs(ds) < abs(s) * 1e-15:
            break
    return s * math.exp(-x + a * math.log(x) - math.lgamma(a))


def _gamma_cf(a: float, x: float) -> float:
    """Q(a,x) = 1 - P(a,x) par fraction continue (Lentz modifié)."""
    tiny = 1e-30
    b = x + 1 - a
    c = 1.0 / tiny
    d = 1.0 / b
    h = d
    for i in range(1, 300):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-15:
            break
    return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h


def regularized_gamma_p(a: float, x: float) -> float:
    """P(a, x) — fonction gamma incomplet régularisée (lower)."""
    if x < 0:
        return 0.0
    if x == 0:
        return 0.0
    if x < a + 1:
        return _gamma_series(a, x)
    return 1.0 - _gamma_cf(a, x)


def regularized_gamma_q(a: float, x: float) -> float:
    """Q(a, x) = 1 - P(a, x) — upper incomplete gamma."""
    return 1.0 - regularized_gamma_p(a, x)


# ═══════════════════════════════════════════════════════════════════════════════
# BÊTA INCOMPLET RÉGULARISÉ  I_x(a, b)
# ═══════════════════════════════════════════════════════════════════════════════

def _beta_cf(x: float, a: float, b: float) -> float:
    """Fraction continue pour I_x(a,b) (Lentz modifié)."""
    tiny = 1e-30
    qab = a + b
    qap = a + 1
    qam = a - 1
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        # even step
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        h *= d * c
        # odd step
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-15:
            break
    return h


def regularized_beta(x: float, a: float, b: float) -> float:
    """I_x(a, b) — fonction bêta incomplet régularisée."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    log_prefix = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                  + a * math.log(x) + b * math.log(1 - x))
    prefix = math.exp(log_prefix)
    if x < (a + 1) / (a + b + 2):
        return prefix * _beta_cf(x, a, b) / a
    else:
        return 1.0 - prefix * _beta_cf(1 - x, b, a) / b


# ═══════════════════════════════════════════════════════════════════════════════
# DISTRIBUTION NORMALE  (CDF, PDF, PPF)
# ═══════════════════════════════════════════════════════════════════════════════

_SQRT2 = math.sqrt(2)
_SQRT2PI = math.sqrt(2 * math.pi)


def norm_cdf(x: float) -> float:
    """Φ(x) — CDF normale standard."""
    return 0.5 * (1.0 + math.erf(x / _SQRT2))


def norm_pdf(x: float) -> float:
    """φ(x) — PDF normale standard."""
    return math.exp(-0.5 * x * x) / _SQRT2PI


def norm_ppf(p: float) -> float:
    """Φ⁻¹(p) — quantile de la loi normale standard (Acklam)."""
    if p <= 0:
        return float("-inf")
    if p >= 1:
        return float("inf")

    # Coefficients de Peter Acklam
    a = (-3.969683028665376e+01, 2.209460984245205e+02,
         -2.759285104469687e+02, 1.383577518672690e+02,
         -3.066479806614716e+01, 2.506628277459239e+00)
    b = (-5.447609879822406e+01, 1.615858368580409e+02,
         -1.556989798598866e+02, 6.680131188771972e+01,
         -1.328068155288572e+01)
    c = (-7.784894002430293e-03, -3.223964580411365e-01,
         -2.400758277161838e+00, -2.549732539343734e+00,
         4.374664141464968e+00, 2.938163982698783e+00)
    d = (7.784695709041462e-03, 3.224671290700398e-01,
         2.445134137142996e+00, 3.754408661907416e+00)

    p_low = 0.02425
    p_high = 1 - p_low

    if p < p_low:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    elif p <= p_high:
        q = p - 0.5
        r = q * q
        return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
               (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
    else:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
                ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)


# ═══════════════════════════════════════════════════════════════════════════════
# DISTRIBUTION T DE STUDENT (CDF, PPF)
# ═══════════════════════════════════════════════════════════════════════════════

def t_cdf(x: float, df: float) -> float:
    """CDF de la loi t de Student à df degrés de liberté."""
    if df <= 0:
        raise ValueError("df doit être positif.")
    xt = df / (df + x * x)
    ib = regularized_beta(xt, df / 2, 0.5)
    if x >= 0:
        return 1.0 - 0.5 * ib
    else:
        return 0.5 * ib


def t_ppf(p: float, df: float) -> float:
    """Quantile de la loi t (recherche par bissection + Newton)."""
    if p <= 0 or p >= 1:
        raise ValueError("p doit être dans ]0, 1[.")
    # Initialisation via approximation normale
    x = norm_ppf(p)
    # Raffinement par Newton
    for _ in range(50):
        cp = t_cdf(x, df)
        # PDF de Student
        pdf = math.exp(math.lgamma((df+1)/2) - math.lgamma(df/2)) / \
              (math.sqrt(df * math.pi) * (1 + x*x/df) ** ((df+1)/2))
        if abs(pdf) < 1e-30:
            break
        x -= (cp - p) / pdf
        if abs(cp - p) < 1e-12:
            break
    return x


# ═══════════════════════════════════════════════════════════════════════════════
# RECHERCHE INVERSE GÉNÉRIQUE (bisection)
# ═══════════════════════════════════════════════════════════════════════════════

def bisect_inverse(cdf_func, p: float, lo: float, hi: float, tol: float = 1e-10) -> float:
    """Recherche par bisection de x tel que cdf_func(x) = p."""
    for _ in range(200):
        mid = (lo + hi) / 2
        if cdf_func(mid) < p:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    return (lo + hi) / 2
