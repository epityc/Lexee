"""
v11 — Statistiques Avancées, D-Functions & Texte Asiatique (Groupe 6).

30 nouvelles formules :
- Statistiques : RSQ, SKEW, SKEW.P, STANDARDIZE, T.DIST, T.DIST.2T, T.DIST.RT,
  T.INV, T.INV.2T, T.TEST, WEIBULL.DIST, Z.TEST
- Bases de données (D-Functions) : DAVERAGE, DCOUNT, DCOUNTA, DGET, DMAX, DMIN,
  DPRODUCT, DSTDEV, DSTDEVP, DSUM, DVAR, DVARP
- Texte/Octets : ASC, BAHTTEXT, DBCS, FINDB, LEFTB, LENB
"""

from __future__ import annotations

import math
import unicodedata

from app.engine._stat_helpers import norm_cdf, norm_ppf, t_cdf, t_ppf, bisect_inverse


# ═══════════════════════════════════════════════════════════════════════════════
# STATISTIQUES — RSQ, SKEW, SKEW.P, STANDARDIZE
# ═══════════════════════════════════════════════════════════════════════════════


def formule_rsq(v: dict) -> dict:
    """RSQ — coefficient de détermination R² entre deux séries."""
    x = [float(i) for i in v["x"]]
    y = [float(i) for i in v["y"]]
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("x et y doivent avoir la même taille >= 2.")
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sx = math.sqrt(sum((xi - mx) ** 2 for xi in x))
    sy = math.sqrt(sum((yi - my) ** 2 for yi in y))
    if sx == 0 or sy == 0:
        raise ValueError("Variance nulle.")
    r = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y)) / (sx * sy)
    return {"resultat": round(r ** 2, 10)}


def formule_skew(v: dict) -> dict:
    """SKEW — asymétrie d'un échantillon."""
    valeurs = [float(x) for x in v["valeurs"]]
    n = len(valeurs)
    if n < 3:
        raise ValueError("Au moins 3 valeurs requises.")
    moy = sum(valeurs) / n
    s = math.sqrt(sum((x - moy) ** 2 for x in valeurs) / (n - 1))
    if s == 0:
        raise ValueError("Écart-type nul.")
    m3 = sum(((x - moy) / s) ** 3 for x in valeurs)
    skew = n * m3 / ((n - 1) * (n - 2))
    return {"resultat": round(skew, 10)}


def formule_skew_p(v: dict) -> dict:
    """SKEW.P — asymétrie d'une population."""
    valeurs = [float(x) for x in v["valeurs"]]
    n = len(valeurs)
    if n < 3:
        raise ValueError("Au moins 3 valeurs requises.")
    moy = sum(valeurs) / n
    s = math.sqrt(sum((x - moy) ** 2 for x in valeurs) / n)
    if s == 0:
        raise ValueError("Écart-type nul.")
    m3 = sum(((x - moy) / s) ** 3 for x in valeurs) / n
    return {"resultat": round(m3, 10)}


def formule_standardize(v: dict) -> dict:
    """STANDARDIZE — valeur centrée réduite (z-score)."""
    x = float(v["x"])
    moyenne = float(v["moyenne"])
    ecart_type = float(v["ecart_type"])
    if ecart_type <= 0:
        raise ValueError("ecart_type doit être positif.")
    return {"resultat": round((x - moyenne) / ecart_type, 10)}


# ═══════════════════════════════════════════════════════════════════════════════
# DISTRIBUTION T DE STUDENT
# ═══════════════════════════════════════════════════════════════════════════════


def formule_t_dist(v: dict) -> dict:
    """T.DIST — distribution t de Student (CDF ou PDF, queue gauche)."""
    x = float(v["x"])
    df = float(v["df"])
    cumulatif = bool(v.get("cumulatif", True))

    if df <= 0:
        raise ValueError("df doit être positif.")

    if cumulatif:
        return {"resultat": round(t_cdf(x, df), 10)}
    else:
        # PDF de Student
        log_pdf = (
            math.lgamma((df + 1) / 2) - math.lgamma(df / 2)
            - 0.5 * math.log(df * math.pi)
            - ((df + 1) / 2) * math.log(1 + x * x / df)
        )
        return {"resultat": round(math.exp(log_pdf), 10)}


def formule_t_dist_2t(v: dict) -> dict:
    """T.DIST.2T — distribution t bilatérale (p-value)."""
    x = float(v["x"])
    df = float(v["df"])
    if x < 0:
        raise ValueError("x doit être >= 0 pour T.DIST.2T.")
    return {"resultat": round(2 * (1 - t_cdf(x, df)), 10)}


def formule_t_dist_rt(v: dict) -> dict:
    """T.DIST.RT — queue droite de la distribution t."""
    x = float(v["x"])
    df = float(v["df"])
    return {"resultat": round(1 - t_cdf(x, df), 10)}


def formule_t_inv(v: dict) -> dict:
    """T.INV — inverse de la distribution t (queue gauche)."""
    p = float(v["probabilite"])
    df = float(v["df"])
    if not (0 < p < 1) or df <= 0:
        raise ValueError("probabilite dans ]0,1[ et df > 0.")
    return {"resultat": round(t_ppf(p, df), 8)}


def formule_t_inv_2t(v: dict) -> dict:
    """T.INV.2T — inverse bilatéral de la distribution t."""
    p = float(v["probabilite"])
    df = float(v["df"])
    if not (0 < p <= 1) or df <= 0:
        raise ValueError("probabilite dans ]0,1] et df > 0.")
    return {"resultat": round(t_ppf(1 - p / 2, df), 8)}


def formule_t_test(v: dict) -> dict:
    """T.TEST — test t de Student (p-value)."""
    x = [float(i) for i in v["x"]]
    y = [float(i) for i in v["y"]]
    queues = int(v.get("queues", 2))
    type_test = int(v.get("type", 2))

    if len(x) < 2 or len(y) < 2:
        raise ValueError("Au moins 2 valeurs dans chaque groupe.")

    mx, my = sum(x) / len(x), sum(y) / len(y)

    if type_test == 1:
        # Apparié
        if len(x) != len(y):
            raise ValueError("Même taille requise pour test apparié.")
        d = [xi - yi for xi, yi in zip(x, y)]
        md = sum(d) / len(d)
        sd = math.sqrt(sum((di - md) ** 2 for di in d) / (len(d) - 1))
        if sd == 0:
            raise ValueError("Variance nulle.")
        t_stat = md / (sd / math.sqrt(len(d)))
        df = len(d) - 1
    else:
        # Deux échantillons indépendants (type 2 = égales variances, type 3 = inégales)
        vx = sum((xi - mx) ** 2 for xi in x) / (len(x) - 1)
        vy = sum((yi - my) ** 2 for yi in y) / (len(y) - 1)
        if type_test == 2:
            sp2 = ((len(x) - 1) * vx + (len(y) - 1) * vy) / (len(x) + len(y) - 2)
            t_stat = (mx - my) / math.sqrt(sp2 * (1 / len(x) + 1 / len(y)))
            df = len(x) + len(y) - 2
        else:
            se = math.sqrt(vx / len(x) + vy / len(y))
            t_stat = (mx - my) / se
            num = (vx / len(x) + vy / len(y)) ** 2
            denom = (vx / len(x)) ** 2 / (len(x) - 1) + (vy / len(y)) ** 2 / (len(y) - 1)
            df = num / denom

    p = 1 - t_cdf(abs(t_stat), df)
    p_value = 2 * p if queues == 2 else p
    return {"t_stat": round(t_stat, 6), "p_value": round(p_value, 8), "df": round(df, 2)}


# ═══════════════════════════════════════════════════════════════════════════════
# WEIBULL.DIST
# ═══════════════════════════════════════════════════════════════════════════════


def formule_weibull_dist(v: dict) -> dict:
    """WEIBULL.DIST — distribution de Weibull (CDF ou PDF)."""
    x = float(v["x"])
    alpha = float(v["alpha"])   # forme (k)
    beta = float(v["beta"])     # échelle (λ)
    cumulatif = bool(v.get("cumulatif", True))

    if alpha <= 0 or beta <= 0:
        raise ValueError("alpha et beta doivent être positifs.")
    if x < 0:
        return {"resultat": 0.0}

    if cumulatif:
        return {"resultat": round(1 - math.exp(-(x / beta) ** alpha), 10)}
    else:
        pdf = (alpha / beta) * (x / beta) ** (alpha - 1) * math.exp(-(x / beta) ** alpha)
        return {"resultat": round(pdf, 10)}


# ═══════════════════════════════════════════════════════════════════════════════
# Z.TEST
# ═══════════════════════════════════════════════════════════════════════════════


def formule_z_test(v: dict) -> dict:
    """Z.TEST — p-value d'un test z (unilatéral supérieur)."""
    valeurs = [float(x) for x in v["valeurs"]]
    mu = float(v["mu"])
    sigma = float(v.get("sigma", 0))

    n = len(valeurs)
    if n < 1:
        raise ValueError("Liste vide.")

    moy = sum(valeurs) / n
    if sigma <= 0:
        sigma = math.sqrt(sum((x - moy) ** 2 for x in valeurs) / (n - 1))
    if sigma == 0:
        raise ValueError("Écart-type nul.")

    z = (moy - mu) / (sigma / math.sqrt(n))
    p_value = 1 - norm_cdf(z)
    return {"z": round(z, 6), "p_value": round(p_value, 8)}


# ═══════════════════════════════════════════════════════════════════════════════
# D-FUNCTIONS (Base de Données)
# ═══════════════════════════════════════════════════════════════════════════════


def _d_filter(base: list, criteres: dict) -> list:
    """Filtre les lignes d'une base correspondant aux critères."""
    result = []
    for row in base:
        if all(row.get(k) == v for k, v in criteres.items()):
            result.append(row)
    return result


def formule_daverage(v: dict) -> dict:
    """DAVERAGE — moyenne d'un champ filtré."""
    rows = _d_filter(v["base"], v["criteres"])
    champ = v["champ"]
    vals = [float(r[champ]) for r in rows if champ in r]
    if not vals:
        raise ValueError("Aucune ligne correspondante.")
    return {"resultat": round(sum(vals) / len(vals), 10)}


def formule_dcount(v: dict) -> dict:
    """DCOUNT — nombre de cellules numériques dans un champ filtré."""
    rows = _d_filter(v["base"], v["criteres"])
    champ = v["champ"]
    count = 0
    for r in rows:
        try:
            float(r[champ])
            count += 1
        except (TypeError, ValueError, KeyError):
            pass
    return {"resultat": count}


def formule_dcounta(v: dict) -> dict:
    """DCOUNTA — nombre de cellules non vides dans un champ filtré."""
    rows = _d_filter(v["base"], v["criteres"])
    champ = v["champ"]
    count = sum(1 for r in rows if r.get(champ) not in (None, "", " "))
    return {"resultat": count}


def formule_dget(v: dict) -> dict:
    """DGET — extrait une valeur unique d'un champ filtré."""
    rows = _d_filter(v["base"], v["criteres"])
    if len(rows) == 0:
        raise ValueError("Aucune ligne correspondante.")
    if len(rows) > 1:
        raise ValueError("Plusieurs lignes correspondent.")
    champ = v["champ"]
    return {"resultat": rows[0][champ]}


def formule_dmax(v: dict) -> dict:
    """DMAX — valeur maximale d'un champ filtré."""
    rows = _d_filter(v["base"], v["criteres"])
    champ = v["champ"]
    vals = [float(r[champ]) for r in rows if champ in r]
    if not vals:
        raise ValueError("Aucune valeur.")
    return {"resultat": max(vals)}


def formule_dmin(v: dict) -> dict:
    """DMIN — valeur minimale d'un champ filtré."""
    rows = _d_filter(v["base"], v["criteres"])
    champ = v["champ"]
    vals = [float(r[champ]) for r in rows if champ in r]
    if not vals:
        raise ValueError("Aucune valeur.")
    return {"resultat": min(vals)}


def formule_dproduct(v: dict) -> dict:
    """DPRODUCT — produit des valeurs d'un champ filtré."""
    rows = _d_filter(v["base"], v["criteres"])
    champ = v["champ"]
    vals = [float(r[champ]) for r in rows if champ in r]
    if not vals:
        raise ValueError("Aucune valeur.")
    result = 1
    for val in vals:
        result *= val
    return {"produit": result}


def formule_dstdev(v: dict) -> dict:
    """DSTDEV — écart-type échantillon d'un champ filtré."""
    rows = _d_filter(v["base"], v["criteres"])
    champ = v["champ"]
    vals = [float(r[champ]) for r in rows if champ in r]
    if len(vals) < 2:
        raise ValueError("Au moins 2 valeurs requises.")
    moy = sum(vals) / len(vals)
    return {"ecart_type": round(math.sqrt(sum((x - moy) ** 2 for x in vals) / (len(vals) - 1)), 10)}


def formule_dstdevp(v: dict) -> dict:
    """DSTDEVP — écart-type population d'un champ filtré."""
    rows = _d_filter(v["base"], v["criteres"])
    champ = v["champ"]
    vals = [float(r[champ]) for r in rows if champ in r]
    if not vals:
        raise ValueError("Aucune valeur.")
    moy = sum(vals) / len(vals)
    return {"ecart_type": round(math.sqrt(sum((x - moy) ** 2 for x in vals) / len(vals)), 10)}


def formule_dsum(v: dict) -> dict:
    """DSUM — somme des valeurs d'un champ filtré."""
    rows = _d_filter(v["base"], v["criteres"])
    champ = v["champ"]
    vals = [float(r[champ]) for r in rows if champ in r]
    return {"somme": round(sum(vals), 10)}


def formule_dvar(v: dict) -> dict:
    """DVAR — variance échantillon d'un champ filtré."""
    rows = _d_filter(v["base"], v["criteres"])
    champ = v["champ"]
    vals = [float(r[champ]) for r in rows if champ in r]
    if len(vals) < 2:
        raise ValueError("Au moins 2 valeurs requises.")
    moy = sum(vals) / len(vals)
    return {"variance": round(sum((x - moy) ** 2 for x in vals) / (len(vals) - 1), 10)}


def formule_dvarp(v: dict) -> dict:
    """DVARP — variance population d'un champ filtré."""
    rows = _d_filter(v["base"], v["criteres"])
    champ = v["champ"]
    vals = [float(r[champ]) for r in rows if champ in r]
    if not vals:
        raise ValueError("Aucune valeur.")
    moy = sum(vals) / len(vals)
    return {"variance": round(sum((x - moy) ** 2 for x in vals) / len(vals), 10)}


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS TEXTE / OCTETS (ASC, BAHTTEXT, DBCS, FINDB, LEFTB, LENB)
# ═══════════════════════════════════════════════════════════════════════════════


def formule_asc_val(v: dict) -> dict:
    """ASC — convertit les caractères pleine largeur en demi-largeur."""
    texte = str(v["texte"])
    result = []
    for ch in texte:
        cp = ord(ch)
        # Pleine largeur ASCII (！ à ～) → demi-largeur (! à ~)
        if 0xFF01 <= cp <= 0xFF5E:
            result.append(chr(cp - 0xFEE0))
        # Espace idéographique → espace normal
        elif cp == 0x3000:
            result.append(' ')
        else:
            result.append(ch)
    return {"resultat": ''.join(result)}


def formule_bahttext(v: dict) -> dict:
    """BAHTTEXT — représentation simplifiée d'un nombre en baht thaïlandais."""
    nombre = float(v["nombre"])
    # Implémentation simplifiée : retourne le montant formaté avec "บาท"
    entier = int(abs(nombre))
    decimal = round(abs(nombre) - entier, 2)
    signe = "-" if nombre < 0 else ""
    if decimal > 0:
        satang = round(decimal * 100)
        return {"resultat": f"{signe}{entier} บาท {satang} สตางค์"}
    return {"resultat": f"{signe}{entier} บาท"}


def formule_dbcs(v: dict) -> dict:
    """DBCS — convertit les caractères demi-largeur en pleine largeur."""
    texte = str(v["texte"])
    result = []
    for ch in texte:
        cp = ord(ch)
        # Demi-largeur ASCII (! à ~) → pleine largeur (！ à ～)
        if 0x21 <= cp <= 0x7E:
            result.append(chr(cp + 0xFEE0))
        elif cp == 0x20:
            result.append('\u3000')
        else:
            result.append(ch)
    return {"resultat": ''.join(result)}


def formule_findb(v: dict) -> dict:
    """FINDB — position d'un texte (en octets UTF-8) dans une chaîne."""
    cherche = str(v["cherche"])
    texte = str(v["texte"])
    debut = int(v.get("debut", 1))

    # Position en octets
    texte_bytes = texte.encode("utf-8")
    cherche_bytes = cherche.encode("utf-8")
    debut_bytes = len(texte[:debut - 1].encode("utf-8"))

    idx = texte_bytes.find(cherche_bytes, debut_bytes)
    if idx == -1:
        raise ValueError(f"'{cherche}' non trouvé dans '{texte}'.")
    return {"position": idx + 1}


def formule_leftb(v: dict) -> dict:
    """LEFTB — n premiers octets d'une chaîne (UTF-8)."""
    texte = str(v["texte"])
    nb_octets = int(v.get("nb_octets", 1))

    encoded = texte.encode("utf-8")
    trunc = encoded[:nb_octets]
    # Décode en ignorant les octets partiels
    return {"resultat": trunc.decode("utf-8", errors="ignore")}


def formule_lenb(v: dict) -> dict:
    """LENB — longueur d'une chaîne en octets (UTF-8)."""
    texte = str(v["texte"])
    return {"resultat": len(texte.encode("utf-8"))}
