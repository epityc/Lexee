"""
v9 — Finance (Titres/Bons) & Statistiques de Distribution (Groupe 4).

29 nouvelles formules :
- Finance : PRICE, PRICEDISC, PRICEMAT, RECEIVED, TBILLEQ, TBILLPRICE,
  TBILLYIELD, VDB, YIELD, YIELDDISC, YIELDMAT, AVEDEV
- Distributions : BETA.DIST, BETA.INV, BINOM.DIST, BINOM.DIST.RANGE,
  BINOM.INV, CHISQ.DIST, CHISQ.DIST.RT, CHISQ.INV, CHISQ.INV.RT,
  CHISQ.TEST, CONFIDENCE.NORM, CONFIDENCE.T, COVARIANCE.S, DEVSQ,
  EXPON.DIST, F.DIST, F.DIST.RT

COVARIANCE.P existe déjà en v5 (clé 'covariance_p').
"""

from __future__ import annotations

import math
from datetime import datetime, date

from app.engine._stat_helpers import (
    regularized_beta,
    regularized_gamma_p,
    norm_ppf,
    t_ppf,
    bisect_inverse,
)
from app.engine._v8 import _parse_date, _year_fraction


# ═══════════════════════════════════════════════════════════════════════════════
# FINANCE — OBLIGATIONS (PRICE, PRICEDISC, PRICEMAT, YIELD, YIELDDISC, YIELDMAT)
# ═══════════════════════════════════════════════════════════════════════════════


def formule_price(v: dict) -> dict:
    """PRICE — prix d'une obligation à coupons périodiques."""
    taux_coupon = float(v["taux_coupon"])
    rendement = float(v["rendement"])
    periodes = int(v["periodes"])
    frequence = int(v.get("frequence", 2))
    valeur_nominale = float(v.get("valeur_nominale", 100))

    if frequence not in (1, 2, 4):
        raise ValueError("Fréquence invalide : 1, 2 ou 4.")

    coupon = valeur_nominale * taux_coupon / frequence
    taux_p = rendement / frequence
    n = periodes * frequence

    prix = 0
    for t in range(1, n + 1):
        cf = coupon + (valeur_nominale if t == n else 0)
        prix += cf / (1 + taux_p) ** t
    return {"prix": round(prix, 6)}


def formule_pricedisc(v: dict) -> dict:
    """PRICEDISC — prix d'un titre escompté."""
    reglement = _parse_date(v["reglement"])
    echeance = _parse_date(v["echeance"])
    escompte = float(v["escompte"])
    remboursement = float(v.get("remboursement", 100))
    basis = int(v.get("base", 0))

    fraction = _year_fraction(reglement, echeance, basis)
    prix = remboursement * (1 - escompte * fraction)
    return {"prix": round(prix, 6)}


def formule_pricemat(v: dict) -> dict:
    """PRICEMAT — prix d'un titre payant les intérêts à échéance."""
    reglement = _parse_date(v["reglement"])
    echeance = _parse_date(v["echeance"])
    emission = _parse_date(v["emission"])
    taux = float(v["taux"])
    rendement = float(v["rendement"])
    basis = int(v.get("base", 0))
    valeur_nominale = float(v.get("valeur_nominale", 100))

    dsm = _year_fraction(reglement, echeance, basis)
    dim = _year_fraction(emission, echeance, basis)
    dis = _year_fraction(emission, reglement, basis)

    prix = valeur_nominale * (1 + dim * taux) / (1 + dsm * rendement) - valeur_nominale * dis * taux
    return {"prix": round(prix, 6)}


def formule_received(v: dict) -> dict:
    """RECEIVED — montant reçu à échéance d'un titre entièrement investi."""
    reglement = _parse_date(v["reglement"])
    echeance = _parse_date(v["echeance"])
    investissement = float(v["investissement"])
    escompte = float(v["escompte"])
    basis = int(v.get("base", 0))

    fraction = _year_fraction(reglement, echeance, basis)
    denom = 1 - escompte * fraction
    if abs(denom) < 1e-15:
        raise ValueError("Dénominateur nul.")
    return {"montant": round(investissement / denom, 6)}


# ─── Bons du Trésor ──────────────────────────────────────────────────────────

def formule_tbilleq(v: dict) -> dict:
    """TBILLEQ — rendement équivalent obligation d'un bon du Trésor."""
    reglement = _parse_date(v["reglement"])
    echeance = _parse_date(v["echeance"])
    escompte = float(v["escompte"])

    jours = (echeance - reglement).days
    if jours <= 0:
        raise ValueError("L'échéance doit être après le règlement.")
    prix = 100 * (1 - escompte * jours / 360)
    rendement = (100 - prix) / prix * (365 / jours)
    return {"rendement": round(rendement, 8)}


def formule_tbillprice(v: dict) -> dict:
    """TBILLPRICE — prix d'un bon du Trésor."""
    reglement = _parse_date(v["reglement"])
    echeance = _parse_date(v["echeance"])
    escompte = float(v["escompte"])

    jours = (echeance - reglement).days
    if jours <= 0:
        raise ValueError("L'échéance doit être après le règlement.")
    prix = 100 * (1 - escompte * jours / 360)
    return {"prix": round(prix, 6)}


def formule_tbillyield(v: dict) -> dict:
    """TBILLYIELD — rendement d'un bon du Trésor."""
    reglement = _parse_date(v["reglement"])
    echeance = _parse_date(v["echeance"])
    prix = float(v["prix"])

    jours = (echeance - reglement).days
    if jours <= 0 or prix <= 0:
        raise ValueError("Jours et prix doivent être positifs.")
    rendement = (100 - prix) / prix * (360 / jours)
    return {"rendement": round(rendement, 8)}


# ─── VDB (Variable Declining Balance) ────────────────────────────────────────

def formule_vdb(v: dict) -> dict:
    """VDB — amortissement variable (DDB puis linéaire)."""
    cout = float(v["cout"])
    residuel = float(v["valeur_residuelle"])
    duree = int(v["duree"])
    debut = float(v["debut"])
    fin = float(v["fin"])
    facteur = float(v.get("facteur", 2))

    if debut < 0 or fin > duree or debut >= fin:
        raise ValueError("Période invalide.")

    valeur = cout
    total = 0
    for p in range(duree):
        ddb = valeur * facteur / duree
        sln = (valeur - residuel) / (duree - p) if duree - p > 0 else 0
        amort = max(ddb, sln)
        if valeur - amort < residuel:
            amort = valeur - residuel
        if amort < 0:
            amort = 0
        if p >= debut and p < fin:
            total += amort
        elif p >= debut:
            frac = fin - int(fin)
            if frac > 0 and p == int(fin):
                total += amort * frac
        valeur -= amort
    return {"amortissement": round(total, 2)}


# ─── YIELD, YIELDDISC, YIELDMAT ──────────────────────────────────────────────

def formule_yield_val(v: dict) -> dict:
    """YIELD — rendement d'une obligation (bisection)."""
    taux_coupon = float(v["taux_coupon"])
    prix_cible = float(v["prix"])
    periodes = int(v["periodes"])
    frequence = int(v.get("frequence", 2))
    valeur_nominale = float(v.get("valeur_nominale", 100))

    def f(y):
        return formule_price({
            "taux_coupon": taux_coupon, "rendement": y, "periodes": periodes,
            "frequence": frequence, "valeur_nominale": valeur_nominale,
        })["prix"] - prix_cible

    lo, hi = 0.0001, 2.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if f(mid) > 0:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-10:
            break
    return {"rendement": round((lo + hi) / 2, 8)}


def formule_yielddisc(v: dict) -> dict:
    """YIELDDISC — rendement d'un titre escompté."""
    reglement = _parse_date(v["reglement"])
    echeance = _parse_date(v["echeance"])
    prix = float(v["prix"])
    remboursement = float(v.get("remboursement", 100))
    basis = int(v.get("base", 0))

    fraction = _year_fraction(reglement, echeance, basis)
    if fraction <= 0 or prix <= 0:
        raise ValueError("Prix et fraction doivent être positifs.")
    rendement = (remboursement - prix) / prix / fraction
    return {"rendement": round(rendement, 8)}


def formule_yieldmat(v: dict) -> dict:
    """YIELDMAT — rendement d'un titre payant les intérêts à échéance."""
    reglement = _parse_date(v["reglement"])
    echeance = _parse_date(v["echeance"])
    emission = _parse_date(v["emission"])
    taux = float(v["taux"])
    prix = float(v["prix"])
    basis = int(v.get("base", 0))

    dsm = _year_fraction(reglement, echeance, basis)
    dim = _year_fraction(emission, echeance, basis)
    dis = _year_fraction(emission, reglement, basis)

    if dsm <= 0:
        raise ValueError("L'échéance doit être après le règlement.")

    rendement = ((1 + dim * taux) / (prix / 100 + dis * taux) - 1) / dsm
    return {"rendement": round(rendement, 8)}


# ─── AVEDEV ───────────────────────────────────────────────────────────────────

def formule_avedev(v: dict) -> dict:
    """AVEDEV — écart absolu moyen."""
    valeurs = [float(x) for x in v["valeurs"]]
    if not valeurs:
        raise ValueError("Liste vide.")
    moy = sum(valeurs) / len(valeurs)
    return {"resultat": round(sum(abs(x - moy) for x in valeurs) / len(valeurs), 10)}


# ═══════════════════════════════════════════════════════════════════════════════
# DISTRIBUTIONS — BETA
# ═══════════════════════════════════════════════════════════════════════════════


def formule_beta_dist(v: dict) -> dict:
    """BETA.DIST — distribution bêta (CDF ou PDF)."""
    x = float(v["x"])
    alpha = float(v["alpha"])
    beta_p = float(v["beta"])
    cumulatif = bool(v.get("cumulatif", True))
    a = float(v.get("a", 0))
    b = float(v.get("b", 1))

    if alpha <= 0 or beta_p <= 0:
        raise ValueError("alpha et beta doivent être positifs.")
    if b <= a:
        raise ValueError("b doit être supérieur à a.")

    z = (x - a) / (b - a)  # normalise sur [0, 1]
    if z < 0 or z > 1:
        return {"resultat": 0.0}

    if cumulatif:
        return {"resultat": round(regularized_beta(z, alpha, beta_p), 10)}
    else:
        # PDF
        log_pdf = ((alpha - 1) * math.log(z) + (beta_p - 1) * math.log(1 - z)
                   - math.lgamma(alpha) - math.lgamma(beta_p) + math.lgamma(alpha + beta_p)
                   - math.log(b - a))
        return {"resultat": round(math.exp(log_pdf), 10)}


def formule_beta_inv(v: dict) -> dict:
    """BETA.INV — inverse de la distribution bêta."""
    p = float(v["probabilite"])
    alpha = float(v["alpha"])
    beta_p = float(v["beta"])
    a = float(v.get("a", 0))
    b = float(v.get("b", 1))

    if not (0 < p < 1):
        raise ValueError("probabilite doit être dans ]0, 1[.")

    z = bisect_inverse(lambda x: regularized_beta(x, alpha, beta_p), p, 0, 1)
    return {"resultat": round(a + z * (b - a), 10)}


# ═══════════════════════════════════════════════════════════════════════════════
# DISTRIBUTIONS — BINOMIALE
# ═══════════════════════════════════════════════════════════════════════════════


def _binom_pmf(k: int, n: int, p: float) -> float:
    return math.comb(n, k) * p ** k * (1 - p) ** (n - k)


def formule_binom_dist(v: dict) -> dict:
    """BINOM.DIST — distribution binomiale (PMF ou CDF)."""
    k = int(v["succes"])
    n = int(v["essais"])
    p = float(v["probabilite"])
    cumulatif = bool(v.get("cumulatif", True))

    if not (0 <= p <= 1) or n < 0 or k < 0:
        raise ValueError("Paramètres invalides.")

    if cumulatif:
        total = sum(_binom_pmf(i, n, p) for i in range(k + 1))
        return {"resultat": round(total, 10)}
    return {"resultat": round(_binom_pmf(k, n, p), 10)}


def formule_binom_dist_range(v: dict) -> dict:
    """BINOM.DIST.RANGE — probabilité binomiale sur un intervalle [s1, s2]."""
    n = int(v["essais"])
    p = float(v["probabilite"])
    s1 = int(v["succes_min"])
    s2 = int(v.get("succes_max", s1))

    total = sum(_binom_pmf(i, n, p) for i in range(s1, s2 + 1))
    return {"resultat": round(total, 10)}


def formule_binom_inv(v: dict) -> dict:
    """BINOM.INV — plus petit k tel que CDF(k) >= alpha."""
    n = int(v["essais"])
    p = float(v["probabilite"])
    alpha = float(v["alpha"])

    cum = 0
    for k in range(n + 1):
        cum += _binom_pmf(k, n, p)
        if cum >= alpha:
            return {"resultat": k}
    return {"resultat": n}


# ═══════════════════════════════════════════════════════════════════════════════
# DISTRIBUTIONS — CHI-DEUX
# ═══════════════════════════════════════════════════════════════════════════════


def formule_chisq_dist(v: dict) -> dict:
    """CHISQ.DIST — distribution du chi-deux (CDF ou PDF)."""
    x = float(v["x"])
    df = float(v["df"])
    cumulatif = bool(v.get("cumulatif", True))

    if x < 0 or df <= 0:
        raise ValueError("x >= 0 et df > 0 requis.")

    if cumulatif:
        return {"resultat": round(regularized_gamma_p(df / 2, x / 2), 10)}
    else:
        k = df / 2
        pdf = math.exp((k - 1) * math.log(x / 2) - x / 2 - math.lgamma(k)) / 2
        return {"resultat": round(pdf, 10)}


def formule_chisq_dist_rt(v: dict) -> dict:
    """CHISQ.DIST.RT — queue droite du chi-deux."""
    x = float(v["x"])
    df = float(v["df"])
    return {"resultat": round(1 - regularized_gamma_p(df / 2, x / 2), 10)}


def formule_chisq_inv(v: dict) -> dict:
    """CHISQ.INV — inverse du chi-deux (queue gauche)."""
    p = float(v["probabilite"])
    df = float(v["df"])

    if not (0 < p < 1) or df <= 0:
        raise ValueError("probabilite dans ]0,1[ et df > 0.")

    return {"resultat": round(
        bisect_inverse(lambda x: regularized_gamma_p(df / 2, x / 2), p, 0, df * 10 + 100),
        8,
    )}


def formule_chisq_inv_rt(v: dict) -> dict:
    """CHISQ.INV.RT — inverse du chi-deux (queue droite) = CHISQ.INV(1-p)."""
    p = float(v["probabilite"])
    df = float(v["df"])

    return {"resultat": round(
        bisect_inverse(lambda x: regularized_gamma_p(df / 2, x / 2), 1 - p, 0, df * 10 + 100),
        8,
    )}


def formule_chisq_test(v: dict) -> dict:
    """CHISQ.TEST — test d'indépendance du chi-deux."""
    observees = v["observees"]
    attendues = v["attendues"]

    if len(observees) != len(attendues):
        raise ValueError("Les tableaux doivent avoir la même taille.")

    chi2 = 0
    for o, e in zip(observees, attendues):
        if e == 0:
            raise ValueError("Valeur attendue nulle.")
        chi2 += (float(o) - float(e)) ** 2 / float(e)

    df = len(observees) - 1
    if df <= 0:
        raise ValueError("Au moins 2 catégories requises.")
    p_value = 1 - regularized_gamma_p(df / 2, chi2 / 2)
    return {"chi2": round(chi2, 6), "p_value": round(p_value, 8), "df": df}


# ═══════════════════════════════════════════════════════════════════════════════
# INTERVALLES DE CONFIANCE
# ═══════════════════════════════════════════════════════════════════════════════


def formule_confidence_norm(v: dict) -> dict:
    """CONFIDENCE.NORM — demi-intervalle de confiance (loi normale)."""
    alpha = float(v["alpha"])
    ecart_type = float(v["ecart_type"])
    taille = int(v["taille"])

    if alpha <= 0 or alpha >= 1 or ecart_type <= 0 or taille <= 0:
        raise ValueError("Paramètres invalides.")

    z = norm_ppf(1 - alpha / 2)
    return {"resultat": round(z * ecart_type / math.sqrt(taille), 8)}


def formule_confidence_t(v: dict) -> dict:
    """CONFIDENCE.T — demi-intervalle de confiance (loi t de Student)."""
    alpha = float(v["alpha"])
    ecart_type = float(v["ecart_type"])
    taille = int(v["taille"])

    if alpha <= 0 or alpha >= 1 or ecart_type <= 0 or taille <= 1:
        raise ValueError("Paramètres invalides (taille >= 2 pour Student).")

    t = t_ppf(1 - alpha / 2, taille - 1)
    return {"resultat": round(t * ecart_type / math.sqrt(taille), 8)}


# ═══════════════════════════════════════════════════════════════════════════════
# COVARIANCE.S, DEVSQ
# ═══════════════════════════════════════════════════════════════════════════════


def formule_covariance_s(v: dict) -> dict:
    """COVARIANCE.S — covariance d'échantillon."""
    x = [float(i) for i in v["x"]]
    y = [float(i) for i in v["y"]]
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("x et y doivent avoir la même taille >= 2.")
    n = len(x)
    mx = sum(x) / n
    my = sum(y) / n
    cov = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y)) / (n - 1)
    return {"covariance": round(cov, 10)}


def formule_devsq(v: dict) -> dict:
    """DEVSQ — somme des carrés des écarts à la moyenne."""
    valeurs = [float(x) for x in v["valeurs"]]
    if not valeurs:
        raise ValueError("Liste vide.")
    moy = sum(valeurs) / len(valeurs)
    return {"resultat": round(sum((x - moy) ** 2 for x in valeurs), 10)}


# ═══════════════════════════════════════════════════════════════════════════════
# DISTRIBUTION EXPONENTIELLE
# ═══════════════════════════════════════════════════════════════════════════════


def formule_expon_dist(v: dict) -> dict:
    """EXPON.DIST — distribution exponentielle (CDF ou PDF)."""
    x = float(v["x"])
    lam = float(v["lambda"])
    cumulatif = bool(v.get("cumulatif", True))

    if lam <= 0:
        raise ValueError("lambda doit être positif.")
    if x < 0:
        return {"resultat": 0.0}

    if cumulatif:
        return {"resultat": round(1 - math.exp(-lam * x), 10)}
    return {"resultat": round(lam * math.exp(-lam * x), 10)}


# ═══════════════════════════════════════════════════════════════════════════════
# DISTRIBUTION F (Fisher-Snedecor)
# ═══════════════════════════════════════════════════════════════════════════════


def _f_cdf(x: float, d1: float, d2: float) -> float:
    """CDF de la distribution F."""
    if x <= 0:
        return 0.0
    z = d1 * x / (d1 * x + d2)
    return regularized_beta(z, d1 / 2, d2 / 2)


def formule_f_dist(v: dict) -> dict:
    """F.DIST — distribution F (CDF ou PDF)."""
    x = float(v["x"])
    d1 = float(v["d1"])
    d2 = float(v["d2"])
    cumulatif = bool(v.get("cumulatif", True))

    if d1 <= 0 or d2 <= 0:
        raise ValueError("d1 et d2 doivent être positifs.")

    if cumulatif:
        return {"resultat": round(_f_cdf(x, d1, d2), 10)}
    else:
        if x <= 0:
            return {"resultat": 0.0}
        log_pdf = (
            math.lgamma((d1 + d2) / 2) - math.lgamma(d1 / 2) - math.lgamma(d2 / 2)
            + (d1 / 2) * math.log(d1 / d2) + (d1 / 2 - 1) * math.log(x)
            - ((d1 + d2) / 2) * math.log(1 + d1 * x / d2)
        )
        return {"resultat": round(math.exp(log_pdf), 10)}


def formule_f_dist_rt(v: dict) -> dict:
    """F.DIST.RT — queue droite de la distribution F."""
    x = float(v["x"])
    d1 = float(v["d1"])
    d2 = float(v["d2"])
    return {"resultat": round(1 - _f_cdf(x, d1, d2), 10)}
