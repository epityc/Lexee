"""
v14 — Compatibilité anciennes fonctions Excel (Groupe 9).

24 nouvelles formules (6 déjà existantes : CONCAT, PERCENTILE, PERCENTRANK,
QUARTILE, GROUPBY, PIVOTBY) :
- Maths : SUMSQ, SUMX2MY2, SUMX2PY2, SUMXMY2
- Statistiques compat : BETADIST, BETAINV, BINOMDIST, CHIDIST, CHIINV, CHITEST,
  COVAR, CRITBINOM, EXPONDIST, FDIST, FINV, FTEST, GAMMADIST, GAMMAINV,
  HYPGEOMDIST, LOGNORMDIST, LOGINV, NEGBINOMDIST, NORMDIST, NORMINV,
  NORMSDIST, NORMSINV, POISSON

Ces fonctions sont des alias de compatibilité qui délèguent aux implémentations
modernes (_v9, _v10, _v11).
"""

from __future__ import annotations

import math

from app.engine._stat_helpers import (
    regularized_beta,
    regularized_gamma_p,
    regularized_gamma_q,
    norm_cdf,
    norm_ppf,
    bisect_inverse,
)
from app.engine._v9 import (
    formule_beta_dist,
    formule_beta_inv,
    formule_binom_dist,
    formule_binom_inv,
    formule_chisq_dist_rt,
    formule_chisq_inv_rt,
    formule_chisq_test,
    formule_expon_dist,
    formule_f_dist_rt,
)
from app.engine._v10 import (
    formule_f_inv,
    formule_f_test,
    formule_gamma_dist,
    formule_gamma_inv,
    formule_hypgeom_dist,
    formule_lognorm_dist,
    formule_lognorm_inv,
    formule_negbinom_dist,
    formule_norm_dist,
    formule_norm_inv,
    formule_norm_s_dist,
    formule_norm_s_inv,
    formule_poisson_dist,
)


# ═══════════════════════════════════════════════════════════════════════════════
# MATHS — SUMSQ, SUMX2MY2, SUMX2PY2, SUMXMY2
# ═══════════════════════════════════════════════════════════════════════════════


def formule_sumsq(v: dict) -> dict:
    """SUMSQ — somme des carrés."""
    valeurs = [float(x) for x in v["valeurs"]]
    return {"resultat": sum(x * x for x in valeurs)}


def formule_sumx2my2(v: dict) -> dict:
    """SUMX2MY2 — Σ(x²−y²) pour deux séries appariées."""
    x = [float(i) for i in v["x"]]
    y = [float(i) for i in v["y"]]
    if len(x) != len(y):
        raise ValueError("x et y doivent avoir la même taille.")
    return {"resultat": sum(xi**2 - yi**2 for xi, yi in zip(x, y))}


def formule_sumx2py2(v: dict) -> dict:
    """SUMX2PY2 — Σ(x²+y²) pour deux séries appariées."""
    x = [float(i) for i in v["x"]]
    y = [float(i) for i in v["y"]]
    if len(x) != len(y):
        raise ValueError("x et y doivent avoir la même taille.")
    return {"resultat": sum(xi**2 + yi**2 for xi, yi in zip(x, y))}


def formule_sumxmy2(v: dict) -> dict:
    """SUMXMY2 — Σ(x−y)² pour deux séries appariées."""
    x = [float(i) for i in v["x"]]
    y = [float(i) for i in v["y"]]
    if len(x) != len(y):
        raise ValueError("x et y doivent avoir la même taille.")
    return {"resultat": sum((xi - yi)**2 for xi, yi in zip(x, y))}


# ═══════════════════════════════════════════════════════════════════════════════
# ALIAS COMPATIBILITÉ — délèguent aux implémentations modernes
# ═══════════════════════════════════════════════════════════════════════════════


def formule_betadist(v: dict) -> dict:
    """BETADIST — alias compat de BETA.DIST (CDF)."""
    return formule_beta_dist(v)


def formule_betainv(v: dict) -> dict:
    """BETAINV — alias compat de BETA.INV."""
    return formule_beta_inv(v)


def formule_binomdist(v: dict) -> dict:
    """BINOMDIST — alias compat de BINOM.DIST."""
    return formule_binom_dist(v)


def formule_chidist(v: dict) -> dict:
    """CHIDIST — alias compat de CHISQ.DIST.RT (queue droite)."""
    return formule_chisq_dist_rt(v)


def formule_chiinv(v: dict) -> dict:
    """CHIINV — alias compat de CHISQ.INV.RT."""
    return formule_chisq_inv_rt(v)


def formule_chitest(v: dict) -> dict:
    """CHITEST — alias compat de CHISQ.TEST."""
    return formule_chisq_test(v)


def formule_covar(v: dict) -> dict:
    """COVAR — covariance de population (non-échantillon)."""
    x = [float(i) for i in v["x"]]
    y = [float(i) for i in v["y"]]
    n = len(x)
    if n != len(y) or n < 1:
        raise ValueError("x et y doivent avoir la même taille >= 1.")
    mx = sum(x) / n
    my = sum(y) / n
    cov = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y)) / n
    return {"covariance": cov}


def formule_critbinom(v: dict) -> dict:
    """CRITBINOM — alias compat de BINOM.INV."""
    return formule_binom_inv(v)


def formule_expondist(v: dict) -> dict:
    """EXPONDIST — alias compat de EXPON.DIST."""
    return formule_expon_dist(v)


def formule_fdist(v: dict) -> dict:
    """FDIST — alias compat de F.DIST.RT (queue droite)."""
    return formule_f_dist_rt(v)


def formule_finv(v: dict) -> dict:
    """FINV — alias compat de F.INV (queue droite → F.INV.RT behavior)."""
    return formule_f_inv(v)


def formule_ftest(v: dict) -> dict:
    """FTEST — alias compat de F.TEST."""
    return formule_f_test(v)


def formule_gammadist(v: dict) -> dict:
    """GAMMADIST — alias compat de GAMMA.DIST."""
    return formule_gamma_dist(v)


def formule_gammainv(v: dict) -> dict:
    """GAMMAINV — alias compat de GAMMA.INV."""
    return formule_gamma_inv(v)


def formule_hypgeomdist(v: dict) -> dict:
    """HYPGEOMDIST — alias compat de HYPGEOM.DIST."""
    return formule_hypgeom_dist(v)


def formule_lognormdist(v: dict) -> dict:
    """LOGNORMDIST — alias compat de LOGNORM.DIST."""
    return formule_lognorm_dist(v)


def formule_loginv(v: dict) -> dict:
    """LOGINV — alias compat de LOGNORM.INV."""
    return formule_lognorm_inv(v)


def formule_negbinomdist(v: dict) -> dict:
    """NEGBINOMDIST — alias compat de NEGBINOM.DIST."""
    return formule_negbinom_dist(v)


def formule_normdist(v: dict) -> dict:
    """NORMDIST — alias compat de NORM.DIST."""
    return formule_norm_dist(v)


def formule_norminv(v: dict) -> dict:
    """NORMINV — alias compat de NORM.INV."""
    return formule_norm_inv(v)


def formule_normsdist(v: dict) -> dict:
    """NORMSDIST — alias compat de NORM.S.DIST."""
    return formule_norm_s_dist(v)


def formule_normsinv(v: dict) -> dict:
    """NORMSINV — alias compat de NORM.S.INV."""
    return formule_norm_s_inv(v)


def formule_poisson(v: dict) -> dict:
    """POISSON — alias compat de POISSON.DIST."""
    return formule_poisson_dist(v)
