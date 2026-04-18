"""
v10 — Statistiques Avancées (Groupe 5).

29 nouvelles formules :
- F.INV, F.INV.RT, F.TEST, FISHER, FISHERINV
- GAMMA, GAMMA.DIST, GAMMA.INV, GAMMALN, GAMMALN.PRECISE, GAUSS
- HARMEAN, HYPGEOM.DIST, KURT
- LOGNORM.DIST, LOGNORM.INV, NEGBINOM.DIST
- NORM.DIST, NORM.INV, NORM.S.DIST, NORM.S.INV
- PEARSON, PERCENTRANK, PERCENTRANK.EXC, PERCENTRANK.INC
- PHI, POISSON.DIST, PROB, QUARTILE.EXC

PERCENTILE.EXC existe déjà en v5 (clé 'percentile_exc').
"""

from __future__ import annotations

import math

from app.engine._stat_helpers import (
    regularized_beta,
    regularized_gamma_p,
    norm_cdf,
    norm_pdf,
    norm_ppf,
    bisect_inverse,
)
from app.engine._v9 import _f_cdf


# ═══════════════════════════════════════════════════════════════════════════════
# F — INVERSE & TEST
# ═══════════════════════════════════════════════════════════════════════════════


def formule_f_inv(v: dict) -> dict:
    """F.INV — inverse de la distribution F (queue gauche)."""
    p = float(v["probabilite"])
    d1 = float(v["d1"])
    d2 = float(v["d2"])
    if not (0 < p < 1) or d1 <= 0 or d2 <= 0:
        raise ValueError("probabilite dans ]0,1[, d1 > 0, d2 > 0.")
    x = bisect_inverse(lambda x: _f_cdf(x, d1, d2), p, 0, 1000)
    return {"resultat": round(x, 8)}


def formule_f_inv_rt(v: dict) -> dict:
    """F.INV.RT — inverse de la distribution F (queue droite) = F.INV(1-p)."""
    p = float(v["probabilite"])
    d1 = float(v["d1"])
    d2 = float(v["d2"])
    x = bisect_inverse(lambda x: _f_cdf(x, d1, d2), 1 - p, 0, 1000)
    return {"resultat": round(x, 8)}


def formule_f_test(v: dict) -> dict:
    """F.TEST — test F (rapport des variances, p-value bilatérale)."""
    x = [float(i) for i in v["x"]]
    y = [float(i) for i in v["y"]]
    if len(x) < 2 or len(y) < 2:
        raise ValueError("Au moins 2 valeurs dans chaque échantillon.")
    mx = sum(x) / len(x)
    my = sum(y) / len(y)
    var_x = sum((xi - mx) ** 2 for xi in x) / (len(x) - 1)
    var_y = sum((yi - my) ** 2 for yi in y) / (len(y) - 1)
    if var_y == 0:
        raise ValueError("Variance de y nulle.")
    f_stat = var_x / var_y
    d1, d2 = len(x) - 1, len(y) - 1
    p = 1 - _f_cdf(f_stat, d1, d2)
    p_value = 2 * min(p, 1 - p)
    return {"f_stat": round(f_stat, 6), "p_value": round(p_value, 8)}


# ═══════════════════════════════════════════════════════════════════════════════
# FISHER / FISHERINV
# ═══════════════════════════════════════════════════════════════════════════════


def formule_fisher(v: dict) -> dict:
    """FISHER — transformation de Fisher : 0.5 * ln((1+x)/(1-x))."""
    x = float(v["x"])
    if x <= -1 or x >= 1:
        raise ValueError("x doit être dans ]-1, 1[.")
    return {"resultat": round(0.5 * math.log((1 + x) / (1 - x)), 10)}


def formule_fisherinv(v: dict) -> dict:
    """FISHERINV — inverse de la transformation de Fisher."""
    y = float(v["y"])
    e2y = math.exp(2 * y)
    return {"resultat": round((e2y - 1) / (e2y + 1), 10)}


# ═══════════════════════════════════════════════════════════════════════════════
# GAMMA, GAMMALN, GAUSS
# ═══════════════════════════════════════════════════════════════════════════════


def formule_gamma_val(v: dict) -> dict:
    """GAMMA — fonction gamma Γ(x)."""
    x = float(v["x"])
    if x <= 0 and x == int(x):
        raise ValueError("Gamma indéfini pour les entiers négatifs ou nuls.")
    return {"resultat": round(math.gamma(x), 10)}


def formule_gamma_dist(v: dict) -> dict:
    """GAMMA.DIST — distribution gamma (CDF ou PDF)."""
    x = float(v["x"])
    alpha = float(v["alpha"])
    beta = float(v["beta"])
    cumulatif = bool(v.get("cumulatif", True))

    if alpha <= 0 or beta <= 0:
        raise ValueError("alpha et beta doivent être positifs.")
    if x < 0:
        return {"resultat": 0.0}

    if cumulatif:
        return {"resultat": round(regularized_gamma_p(alpha, x / beta), 10)}
    else:
        log_pdf = ((alpha - 1) * math.log(x) - x / beta
                   - alpha * math.log(beta) - math.lgamma(alpha))
        return {"resultat": round(math.exp(log_pdf), 10)}


def formule_gamma_inv(v: dict) -> dict:
    """GAMMA.INV — inverse de la distribution gamma."""
    p = float(v["probabilite"])
    alpha = float(v["alpha"])
    beta = float(v["beta"])

    if not (0 < p < 1):
        raise ValueError("probabilite dans ]0, 1[.")
    x = bisect_inverse(
        lambda x: regularized_gamma_p(alpha, x / beta), p, 0, alpha * beta * 20 + 100,
    )
    return {"resultat": round(x, 8)}


def formule_gammaln(v: dict) -> dict:
    """GAMMALN — logarithme de la fonction gamma."""
    x = float(v["x"])
    if x <= 0:
        raise ValueError("x doit être positif.")
    return {"resultat": round(math.lgamma(x), 10)}


def formule_gammaln_precis(v: dict) -> dict:
    """GAMMALN.PRECISE — identique à GAMMALN."""
    return formule_gammaln(v)


def formule_gauss(v: dict) -> dict:
    """GAUSS — Φ(x) - 0.5 (probabilité entre 0 et x de la loi normale)."""
    x = float(v["x"])
    return {"resultat": round(norm_cdf(x) - 0.5, 10)}


# ═══════════════════════════════════════════════════════════════════════════════
# HARMEAN
# ═══════════════════════════════════════════════════════════════════════════════


def formule_harmean(v: dict) -> dict:
    """HARMEAN — moyenne harmonique."""
    valeurs = [float(x) for x in v["valeurs"]]
    if not valeurs:
        raise ValueError("Liste vide.")
    if any(x <= 0 for x in valeurs):
        raise ValueError("Toutes les valeurs doivent être positives.")
    return {"resultat": round(len(valeurs) / sum(1 / x for x in valeurs), 10)}


# ═══════════════════════════════════════════════════════════════════════════════
# HYPGEOM.DIST
# ═══════════════════════════════════════════════════════════════════════════════


def formule_hypgeom_dist(v: dict) -> dict:
    """HYPGEOM.DIST — distribution hypergéométrique."""
    s = int(v["succes_echantillon"])
    n = int(v["taille_echantillon"])
    ps = int(v["succes_population"])
    pn = int(v["taille_population"])
    cumulatif = bool(v.get("cumulatif", True))

    def _pmf(k):
        return math.comb(ps, k) * math.comb(pn - ps, n - k) / math.comb(pn, n)

    if cumulatif:
        total = sum(_pmf(k) for k in range(s + 1))
        return {"resultat": round(total, 10)}
    return {"resultat": round(_pmf(s), 10)}


# ═══════════════════════════════════════════════════════════════════════════════
# KURT (kurtosis)
# ═══════════════════════════════════════════════════════════════════════════════


def formule_kurt(v: dict) -> dict:
    """KURT — kurtosis (excès) d'un échantillon."""
    valeurs = [float(x) for x in v["valeurs"]]
    n = len(valeurs)
    if n < 4:
        raise ValueError("Au moins 4 valeurs requises.")
    moy = sum(valeurs) / n
    s2 = sum((x - moy) ** 2 for x in valeurs) / (n - 1)
    if s2 == 0:
        raise ValueError("Variance nulle.")
    s = math.sqrt(s2)
    m4 = sum(((x - moy) / s) ** 4 for x in valeurs)
    kurt = (n * (n + 1) * m4 / ((n - 1) * (n - 2) * (n - 3))
            - 3 * (n - 1) ** 2 / ((n - 2) * (n - 3)))
    return {"resultat": round(kurt, 8)}


# ═══════════════════════════════════════════════════════════════════════════════
# LOGNORM
# ═══════════════════════════════════════════════════════════════════════════════


def formule_lognorm_dist(v: dict) -> dict:
    """LOGNORM.DIST — distribution log-normale (CDF ou PDF)."""
    x = float(v["x"])
    mu = float(v["moyenne"])
    sigma = float(v["ecart_type"])
    cumulatif = bool(v.get("cumulatif", True))

    if sigma <= 0 or x <= 0:
        raise ValueError("x > 0 et ecart_type > 0 requis.")

    if cumulatif:
        return {"resultat": round(norm_cdf((math.log(x) - mu) / sigma), 10)}
    pdf = math.exp(-0.5 * ((math.log(x) - mu) / sigma) ** 2) / (x * sigma * math.sqrt(2 * math.pi))
    return {"resultat": round(pdf, 10)}


def formule_lognorm_inv(v: dict) -> dict:
    """LOGNORM.INV — inverse de la distribution log-normale."""
    p = float(v["probabilite"])
    mu = float(v["moyenne"])
    sigma = float(v["ecart_type"])

    if not (0 < p < 1):
        raise ValueError("probabilite dans ]0, 1[.")
    z = norm_ppf(p)
    return {"resultat": round(math.exp(mu + sigma * z), 8)}


# ═══════════════════════════════════════════════════════════════════════════════
# NEGBINOM.DIST
# ═══════════════════════════════════════════════════════════════════════════════


def formule_negbinom_dist(v: dict) -> dict:
    """NEGBINOM.DIST — distribution binomiale négative."""
    echecs = int(v["echecs"])
    succes = int(v["succes"])
    p = float(v["probabilite"])
    cumulatif = bool(v.get("cumulatif", True))

    if not (0 < p < 1) or succes < 1 or echecs < 0:
        raise ValueError("Paramètres invalides.")

    def _pmf(f):
        return math.comb(f + succes - 1, f) * p ** succes * (1 - p) ** f

    if cumulatif:
        total = sum(_pmf(f) for f in range(echecs + 1))
        return {"resultat": round(total, 10)}
    return {"resultat": round(_pmf(echecs), 10)}


# ═══════════════════════════════════════════════════════════════════════════════
# NORM.DIST, NORM.INV, NORM.S.DIST, NORM.S.INV
# ═══════════════════════════════════════════════════════════════════════════════


def formule_norm_dist(v: dict) -> dict:
    """NORM.DIST — distribution normale (CDF ou PDF)."""
    x = float(v["x"])
    mu = float(v["moyenne"])
    sigma = float(v["ecart_type"])
    cumulatif = bool(v.get("cumulatif", True))

    if sigma <= 0:
        raise ValueError("ecart_type doit être positif.")
    z = (x - mu) / sigma
    if cumulatif:
        return {"resultat": round(norm_cdf(z), 10)}
    return {"resultat": round(norm_pdf(z) / sigma, 10)}


def formule_norm_inv(v: dict) -> dict:
    """NORM.INV — inverse de la distribution normale."""
    p = float(v["probabilite"])
    mu = float(v["moyenne"])
    sigma = float(v["ecart_type"])

    if not (0 < p < 1) or sigma <= 0:
        raise ValueError("Paramètres invalides.")
    return {"resultat": round(mu + sigma * norm_ppf(p), 8)}


def formule_norm_s_dist(v: dict) -> dict:
    """NORM.S.DIST — distribution normale standard (CDF ou PDF)."""
    z = float(v["z"])
    cumulatif = bool(v.get("cumulatif", True))
    if cumulatif:
        return {"resultat": round(norm_cdf(z), 10)}
    return {"resultat": round(norm_pdf(z), 10)}


def formule_norm_s_inv(v: dict) -> dict:
    """NORM.S.INV — inverse de la distribution normale standard."""
    p = float(v["probabilite"])
    if not (0 < p < 1):
        raise ValueError("probabilite dans ]0, 1[.")
    return {"resultat": round(norm_ppf(p), 10)}


# ═══════════════════════════════════════════════════════════════════════════════
# PEARSON
# ═══════════════════════════════════════════════════════════════════════════════


def formule_pearson(v: dict) -> dict:
    """PEARSON — coefficient de corrélation de Pearson."""
    x = [float(i) for i in v["x"]]
    y = [float(i) for i in v["y"]]
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("x et y même taille >= 2.")
    n = len(x)
    mx = sum(x) / n
    my = sum(y) / n
    sx = math.sqrt(sum((xi - mx) ** 2 for xi in x))
    sy = math.sqrt(sum((yi - my) ** 2 for yi in y))
    if sx == 0 or sy == 0:
        raise ValueError("Variance nulle.")
    r = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y)) / (sx * sy)
    return {"resultat": round(r, 10)}


# ═══════════════════════════════════════════════════════════════════════════════
# PERCENTRANK, PERCENTRANK.EXC, PERCENTRANK.INC
# ═══════════════════════════════════════════════════════════════════════════════


def formule_percentrank(v: dict) -> dict:
    """PERCENTRANK — rang en pourcentage (inclusif, par défaut)."""
    valeurs = sorted(float(x) for x in v["valeurs"])
    x = float(v["x"])
    n = len(valeurs)
    if n == 0:
        raise ValueError("Liste vide.")
    if x < valeurs[0] or x > valeurs[-1]:
        raise ValueError("x hors de la plage des valeurs.")
    count_below = sum(1 for vi in valeurs if vi < x)
    count_equal = sum(1 for vi in valeurs if vi == x)
    rank = (count_below + 0.5 * count_equal - 0.5) / (n - 1) if n > 1 else 0
    return {"resultat": round(max(0, min(1, rank)), 10)}


def formule_percentrank_exc(v: dict) -> dict:
    """PERCENTRANK.EXC — rang en pourcentage (exclusif)."""
    valeurs = sorted(float(x) for x in v["valeurs"])
    x = float(v["x"])
    n = len(valeurs)
    if n == 0:
        raise ValueError("Liste vide.")
    count_below = sum(1 for vi in valeurs if vi < x)
    count_equal = sum(1 for vi in valeurs if vi == x)
    rank = (count_below + 0.5 * count_equal) / (n + 1)
    return {"resultat": round(rank, 10)}


def formule_percentrank_inc(v: dict) -> dict:
    """PERCENTRANK.INC — rang en pourcentage (inclusif)."""
    return formule_percentrank(v)


# ═══════════════════════════════════════════════════════════════════════════════
# PHI
# ═══════════════════════════════════════════════════════════════════════════════


def formule_phi(v: dict) -> dict:
    """PHI — densité de la loi normale standard φ(x)."""
    x = float(v["x"])
    return {"resultat": round(norm_pdf(x), 10)}


# ═══════════════════════════════════════════════════════════════════════════════
# POISSON.DIST
# ═══════════════════════════════════════════════════════════════════════════════


def formule_poisson_dist(v: dict) -> dict:
    """POISSON.DIST — distribution de Poisson (PMF ou CDF)."""
    x = int(v["x"])
    mu = float(v["moyenne"])
    cumulatif = bool(v.get("cumulatif", True))

    if mu <= 0 or x < 0:
        raise ValueError("moyenne > 0 et x >= 0 requis.")

    def _pmf(k):
        return math.exp(-mu + k * math.log(mu) - math.lgamma(k + 1))

    if cumulatif:
        total = sum(_pmf(k) for k in range(x + 1))
        return {"resultat": round(total, 10)}
    return {"resultat": round(_pmf(x), 10)}


# ═══════════════════════════════════════════════════════════════════════════════
# PROB
# ═══════════════════════════════════════════════════════════════════════════════


def formule_prob(v: dict) -> dict:
    """PROB — probabilité d'un intervalle à partir de valeurs et probabilités."""
    valeurs = [float(x) for x in v["valeurs"]]
    probabilites = [float(p) for p in v["probabilites"]]
    borne_inf = float(v["borne_inf"])
    borne_sup = float(v.get("borne_sup", borne_inf))

    if len(valeurs) != len(probabilites):
        raise ValueError("Même nombre de valeurs et probabilités requis.")

    total = sum(p for val, p in zip(valeurs, probabilites)
                if borne_inf <= val <= borne_sup)
    return {"resultat": round(total, 10)}


# ═══════════════════════════════════════════════════════════════════════════════
# QUARTILE.EXC
# ═══════════════════════════════════════════════════════════════════════════════


def formule_quartile_exc(v: dict) -> dict:
    """QUARTILE.EXC — quartile exclusif (quart = 1, 2 ou 3)."""
    valeurs = sorted(float(x) for x in v["valeurs"])
    quart = int(v["quart"])
    n = len(valeurs)

    if quart < 1 or quart > 3:
        raise ValueError("quart doit être 1, 2 ou 3.")
    if n < 3:
        raise ValueError("Au moins 3 valeurs requises.")

    # Méthode exclusive : k = quart * (n+1) / 4
    k = quart * (n + 1) / 4
    idx = int(k) - 1
    frac = k - int(k)
    if idx < 0:
        return {"resultat": valeurs[0]}
    if idx >= n - 1:
        return {"resultat": valeurs[-1]}
    result = valeurs[idx] + frac * (valeurs[idx + 1] - valeurs[idx])
    return {"resultat": round(result, 10)}
