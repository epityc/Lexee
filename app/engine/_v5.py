"""
v5 — 50 formules expertes supplémentaires.

Module isolé pour éviter de surcharger logic.py.
Toutes les fonctions suivent la signature standard : (v: dict) -> dict.
Les erreurs métier remontent via ValueError / TypeError / KeyError.
"""

from __future__ import annotations

import math
import random
import re
from datetime import date, datetime


# ═══════════════════════════════════════════════════════════════════════════════
# INTELLIGENCE MODERNE (5)
# ═══════════════════════════════════════════════════════════════════════════════


def formule_groupby(v: dict) -> dict:
    """Regroupe une liste d'objets par clé et applique une agrégation."""
    donnees = v["donnees"]  # list of dicts
    cle = str(v["cle"])
    champ = str(v.get("champ", ""))
    agregation = str(v.get("agregation", "count")).lower()

    groupes: dict = {}
    for ligne in donnees:
        if cle not in ligne:
            raise KeyError(f"Clé '{cle}' absente de la ligne.")
        g = ligne[cle]
        groupes.setdefault(g, []).append(ligne)

    resultat = {}
    for g, lignes in groupes.items():
        if agregation == "count":
            resultat[str(g)] = len(lignes)
        else:
            if not champ:
                raise ValueError("Le champ est requis pour cette agrégation.")
            vals = [float(l[champ]) for l in lignes if champ in l]
            if agregation == "sum":
                resultat[str(g)] = round(sum(vals), 6)
            elif agregation == "avg":
                resultat[str(g)] = round(sum(vals) / len(vals), 6) if vals else 0
            elif agregation == "min":
                resultat[str(g)] = round(min(vals), 6) if vals else None
            elif agregation == "max":
                resultat[str(g)] = round(max(vals), 6) if vals else None
            else:
                raise ValueError(f"Agrégation inconnue : {agregation}")

    return {"groupes": resultat, "nb_groupes": len(resultat)}


def formule_pivotby(v: dict) -> dict:
    """Tableau croisé dynamique simple : lignes × colonnes → somme d'un champ."""
    donnees = v["donnees"]
    ligne_cle = str(v["ligne_cle"])
    colonne_cle = str(v["colonne_cle"])
    champ = str(v["champ"])

    pivot: dict = {}
    colonnes: set = set()
    for row in donnees:
        l = str(row[ligne_cle])
        c = str(row[colonne_cle])
        val = float(row[champ])
        colonnes.add(c)
        pivot.setdefault(l, {}).setdefault(c, 0)
        pivot[l][c] += val

    # Remplir les cellules manquantes avec 0
    colonnes_tri = sorted(colonnes)
    matrice = []
    for l in sorted(pivot.keys()):
        ligne = {"_": l}
        for c in colonnes_tri:
            ligne[c] = round(pivot[l].get(c, 0), 6)
        matrice.append(ligne)

    return {"pivot": matrice, "colonnes": colonnes_tri, "nb_lignes": len(matrice)}


def formule_regex_extract(v: dict) -> dict:
    """Extrait toutes les correspondances d'un motif regex."""
    texte = str(v["texte"])
    motif = str(v["motif"])
    try:
        correspondances = re.findall(motif, texte)
    except re.error as e:
        raise ValueError(f"Regex invalide : {e}")
    return {"correspondances": correspondances, "nombre": len(correspondances)}


def formule_regex_match(v: dict) -> dict:
    """Teste si un motif regex correspond à un texte."""
    texte = str(v["texte"])
    motif = str(v["motif"])
    try:
        m = re.search(motif, texte)
    except re.error as e:
        raise ValueError(f"Regex invalide : {e}")
    return {
        "correspond": m is not None,
        "match": m.group(0) if m else None,
        "position": m.start() if m else -1,
    }


def formule_regex_replace(v: dict) -> dict:
    """Remplace toutes les occurrences d'un motif regex."""
    texte = str(v["texte"])
    motif = str(v["motif"])
    remplacement = str(v.get("remplacement", ""))
    try:
        resultat, nb = re.subn(motif, remplacement, texte)
    except re.error as e:
        raise ValueError(f"Regex invalide : {e}")
    return {"resultat": resultat, "remplacements": nb}


# ═══════════════════════════════════════════════════════════════════════════════
# STATISTIQUES AVANCÉES (5)
# ═══════════════════════════════════════════════════════════════════════════════


def _regression_lineaire(xs, ys):
    n = len(xs)
    if n < 2:
        raise ValueError("Au moins 2 points requis.")
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    den = sum((x - mx) ** 2 for x in xs)
    if den == 0:
        raise ValueError("Variance de X nulle.")
    pente = num / den
    ordonnee = my - pente * mx
    return pente, ordonnee


def formule_tendance(v: dict) -> dict:
    """TREND — projection par régression linéaire."""
    y_connus = [float(x) for x in v["y_connus"]]
    x_connus = [float(x) for x in v.get("x_connus", list(range(1, len(y_connus) + 1)))]
    x_nouveaux = [float(x) for x in v["x_nouveaux"]]

    pente, ordonnee = _regression_lineaire(x_connus, y_connus)
    y_nouveaux = [round(pente * x + ordonnee, 6) for x in x_nouveaux]
    return {"y_nouveaux": y_nouveaux, "pente": round(pente, 6), "ordonnee": round(ordonnee, 6)}


def formule_croissance(v: dict) -> dict:
    """GROWTH — régression exponentielle y = b * m^x."""
    y_connus = [float(x) for x in v["y_connus"]]
    x_connus = [float(x) for x in v.get("x_connus", list(range(1, len(y_connus) + 1)))]
    x_nouveaux = [float(x) for x in v["x_nouveaux"]]

    if any(y <= 0 for y in y_connus):
        raise ValueError("Tous les y_connus doivent être strictement positifs.")

    ln_y = [math.log(y) for y in y_connus]
    pente, ordonnee = _regression_lineaire(x_connus, ln_y)
    y_nouveaux = [round(math.exp(pente * x + ordonnee), 6) for x in x_nouveaux]
    return {
        "y_nouveaux": y_nouveaux,
        "base": round(math.exp(ordonnee), 6),
        "facteur": round(math.exp(pente), 6),
    }


def formule_covariance_p(v: dict) -> dict:
    """COVARIANCE.P — covariance sur population."""
    xs = [float(x) for x in v["x"]]
    ys = [float(y) for y in v["y"]]
    if len(xs) != len(ys):
        raise ValueError("Les deux séries doivent avoir la même taille.")
    n = len(xs)
    if n == 0:
        raise ValueError("Séries vides.")
    mx = sum(xs) / n
    my = sum(ys) / n
    cov = sum((xs[i] - mx) * (ys[i] - my) for i in range(n)) / n
    return {"covariance": round(cov, 8)}


def formule_prevision_ets(v: dict) -> dict:
    """FORECAST.ETS simplifié — lissage exponentiel."""
    valeurs = [float(x) for x in v["valeurs"]]
    periodes = int(v.get("periodes", 1))
    alpha = float(v.get("alpha", 0.3))

    if not 0 < alpha < 1:
        raise ValueError("alpha doit être entre 0 et 1.")
    if len(valeurs) < 2:
        raise ValueError("Au moins 2 valeurs requises.")

    # Lissage exponentiel simple (SES)
    niveau = valeurs[0]
    for val in valeurs[1:]:
        niveau = alpha * val + (1 - alpha) * niveau

    previsions = [round(niveau, 6)] * periodes
    return {"previsions": previsions, "niveau_final": round(niveau, 6)}


def formule_percentile_exc(v: dict) -> dict:
    """PERCENTILE.EXC — percentile exclusif."""
    valeurs = sorted(float(x) for x in v["valeurs"])
    k = float(v["k"])
    n = len(valeurs)
    if n == 0:
        raise ValueError("Liste vide.")
    if k <= 1 / (n + 1) or k >= n / (n + 1):
        raise ValueError(f"k doit être entre {1/(n+1):.4f} et {n/(n+1):.4f}.")

    position = k * (n + 1)
    idx = int(position)
    frac = position - idx
    # idx est 1-based ici
    resultat = valeurs[idx - 1] + frac * (valeurs[idx] - valeurs[idx - 1])
    return {"percentile": round(resultat, 8)}


# ═══════════════════════════════════════════════════════════════════════════════
# INGÉNIERIE & CONVERSION (10)
# ═══════════════════════════════════════════════════════════════════════════════


_UNITES = {
    # longueur → mètre
    "m": ("longueur", 1.0),
    "km": ("longueur", 1000.0),
    "cm": ("longueur", 0.01),
    "mm": ("longueur", 0.001),
    "mi": ("longueur", 1609.344),
    "ft": ("longueur", 0.3048),
    "in": ("longueur", 0.0254),
    "yd": ("longueur", 0.9144),
    # masse → kg
    "kg": ("masse", 1.0),
    "g": ("masse", 0.001),
    "mg": ("masse", 1e-6),
    "lbm": ("masse", 0.45359237),
    "ozm": ("masse", 0.028349523125),
    # temps → seconde
    "sec": ("temps", 1.0),
    "mn": ("temps", 60.0),
    "hr": ("temps", 3600.0),
    "day": ("temps", 86400.0),
    "yr": ("temps", 31557600.0),
    # volume → litre
    "l": ("volume", 1.0),
    "ml": ("volume", 0.001),
    "gal": ("volume", 3.785411784),
    # énergie → joule
    "j": ("energie", 1.0),
    "kj": ("energie", 1000.0),
    "cal": ("energie", 4.184),
    "kcal": ("energie", 4184.0),
    "wh": ("energie", 3600.0),
    "kwh": ("energie", 3_600_000.0),
    # puissance → watt
    "w": ("puissance", 1.0),
    "kw": ("puissance", 1000.0),
    "hp": ("puissance", 745.6998715822702),
    # angle → radian
    "rad": ("angle", 1.0),
    "deg": ("angle", math.pi / 180),
    "grad": ("angle", math.pi / 200),
}


def formule_convertir(v: dict) -> dict:
    """CONVERT — conversion d'unités (longueur, masse, temps, volume, énergie,
    puissance, angle, température)."""
    nombre = float(v["nombre"])
    depuis = str(v["depuis"]).lower()
    vers = str(v["vers"]).lower()

    # Cas spécial : température (conversion affine)
    temp = {"c", "f", "k"}
    if depuis in temp and vers in temp:
        # Vers Celsius
        if depuis == "c":
            c = nombre
        elif depuis == "f":
            c = (nombre - 32) * 5 / 9
        else:  # K
            c = nombre - 273.15
        # Depuis Celsius
        if vers == "c":
            r = c
        elif vers == "f":
            r = c * 9 / 5 + 32
        else:
            r = c + 273.15
        return {"resultat": round(r, 8)}

    if depuis not in _UNITES or vers not in _UNITES:
        raise ValueError(f"Unité inconnue : {depuis} ou {vers}.")

    cat_d, fac_d = _UNITES[depuis]
    cat_v, fac_v = _UNITES[vers]
    if cat_d != cat_v:
        raise ValueError(f"Catégories incompatibles : {cat_d} vs {cat_v}.")

    return {"resultat": round(nombre * fac_d / fac_v, 8)}


def _parse_base(s: str, base: int) -> int:
    s = str(s).strip().upper()
    if not s:
        raise ValueError("Valeur vide.")
    return int(s, base)


def formule_bin2hex(v: dict) -> dict:
    """BIN2HEX — binaire vers hexadécimal."""
    n = _parse_base(v["nombre"], 2)
    return {"resultat": format(n, "X")}


def formule_hex2dec(v: dict) -> dict:
    """HEX2DEC — hexadécimal vers décimal."""
    n = _parse_base(v["nombre"], 16)
    return {"resultat": n}


def formule_dec2bin(v: dict) -> dict:
    """DEC2BIN — décimal vers binaire."""
    n = int(v["nombre"])
    if n < 0:
        raise ValueError("Nombre négatif non supporté.")
    return {"resultat": format(n, "b")}


def formule_dec2hex(v: dict) -> dict:
    """DEC2HEX — décimal vers hexadécimal."""
    n = int(v["nombre"])
    if n < 0:
        raise ValueError("Nombre négatif non supporté.")
    return {"resultat": format(n, "X")}


def formule_delta(v: dict) -> dict:
    """DELTA — renvoie 1 si a==b, 0 sinon."""
    a = float(v["a"])
    b = float(v.get("b", 0))
    return {"resultat": 1 if a == b else 0}


def formule_bit_et(v: dict) -> dict:
    """BITAND — ET bit à bit."""
    a = int(v["a"])
    b = int(v["b"])
    if a < 0 or b < 0:
        raise ValueError("Entiers positifs uniquement.")
    return {"resultat": a & b}


def formule_bit_ou(v: dict) -> dict:
    """BITOR — OU bit à bit."""
    a = int(v["a"])
    b = int(v["b"])
    if a < 0 or b < 0:
        raise ValueError("Entiers positifs uniquement.")
    return {"resultat": a | b}


def formule_bit_xou(v: dict) -> dict:
    """BITXOR — OU exclusif bit à bit."""
    a = int(v["a"])
    b = int(v["b"])
    if a < 0 or b < 0:
        raise ValueError("Entiers positifs uniquement.")
    return {"resultat": a ^ b}


def formule_erf_val(v: dict) -> dict:
    """ERF — fonction d'erreur de Gauss."""
    x = float(v["x"])
    borne_sup = v.get("borne_sup")
    if borne_sup is None:
        return {"resultat": round(math.erf(x), 8)}
    return {"resultat": round(math.erf(float(borne_sup)) - math.erf(x), 8)}


# ═══════════════════════════════════════════════════════════════════════════════
# FINANCE PROFESSIONNELLE (7)
# ═══════════════════════════════════════════════════════════════════════════════


def formule_taux_effectif(v: dict) -> dict:
    """EFFECT — taux effectif annuel."""
    taux_nominal = float(v["taux_nominal"])
    periodes = int(v["periodes"])
    if periodes <= 0:
        raise ValueError("periodes doit être > 0.")
    effectif = (1 + taux_nominal / periodes) ** periodes - 1
    return {"taux_effectif": round(effectif, 8)}


def formule_taux_nominal(v: dict) -> dict:
    """NOMINAL — taux nominal annuel."""
    taux_effectif = float(v["taux_effectif"])
    periodes = int(v["periodes"])
    if periodes <= 0:
        raise ValueError("periodes doit être > 0.")
    nominal = periodes * ((1 + taux_effectif) ** (1 / periodes) - 1)
    return {"taux_nominal": round(nominal, 8)}


def formule_tri_modifie(v: dict) -> dict:
    """MIRR — TRI modifié."""
    flux = [float(x) for x in v["flux"]]
    taux_financement = float(v["taux_financement"])
    taux_reinvestissement = float(v["taux_reinvestissement"])
    n = len(flux) - 1
    if n < 1:
        raise ValueError("Au moins 2 flux requis.")

    neg = sum(f / (1 + taux_financement) ** i for i, f in enumerate(flux) if f < 0)
    pos = sum(f * (1 + taux_reinvestissement) ** (n - i) for i, f in enumerate(flux) if f > 0)

    if neg == 0 or pos == 0:
        raise ValueError("Flux positifs et négatifs requis.")

    mirr = (-pos / neg) ** (1 / n) - 1
    return {"tri_modifie": round(mirr, 8)}


def _to_date(d) -> date:
    if isinstance(d, date):
        return d
    if isinstance(d, datetime):
        return d.date()
    return datetime.strptime(str(d), "%Y-%m-%d").date()


def formule_van_dates(v: dict) -> dict:
    """XNPV — valeur actuelle nette avec dates irrégulières."""
    taux = float(v["taux"])
    flux = [float(x) for x in v["flux"]]
    dates = [_to_date(d) for d in v["dates"]]
    if len(flux) != len(dates):
        raise ValueError("flux et dates doivent avoir la même taille.")
    if len(flux) == 0:
        raise ValueError("Flux vides.")

    d0 = dates[0]
    van = sum(
        flux[i] / (1 + taux) ** ((dates[i] - d0).days / 365.0)
        for i in range(len(flux))
    )
    return {"van": round(van, 6)}


def formule_tri_dates(v: dict) -> dict:
    """XIRR — TRI avec dates irrégulières (méthode Newton)."""
    flux = [float(x) for x in v["flux"]]
    dates = [_to_date(d) for d in v["dates"]]
    estimation = float(v.get("estimation", 0.1))

    if len(flux) != len(dates) or len(flux) < 2:
        raise ValueError("Au moins 2 flux/dates alignés requis.")

    d0 = dates[0]
    jours = [(d - d0).days / 365.0 for d in dates]

    def npv(r):
        return sum(flux[i] / (1 + r) ** jours[i] for i in range(len(flux)))

    def dnpv(r):
        return sum(-jours[i] * flux[i] / (1 + r) ** (jours[i] + 1) for i in range(len(flux)))

    r = estimation
    for _ in range(100):
        f = npv(r)
        if abs(f) < 1e-9:
            return {"tri": round(r, 8)}
        d = dnpv(r)
        if d == 0:
            break
        r_new = r - f / d
        if abs(r_new - r) < 1e-10:
            r = r_new
            break
        r = r_new

    if abs(npv(r)) > 1e-4:
        raise ValueError("TRI non convergent.")
    return {"tri": round(r, 8)}


def formule_amort_ddb(v: dict) -> dict:
    """DDB — amortissement dégressif double."""
    cout = float(v["cout"])
    valeur_residuelle = float(v["valeur_residuelle"])
    duree = int(v["duree"])
    periode = int(v["periode"])
    facteur = float(v.get("facteur", 2))

    if duree <= 0 or periode <= 0 or periode > duree:
        raise ValueError("Paramètres de durée/période invalides.")

    vnc = cout
    total = 0.0
    amort_periode = 0.0
    for p in range(1, periode + 1):
        amort = min(vnc * facteur / duree, vnc - valeur_residuelle)
        amort = max(amort, 0)
        if p == periode:
            amort_periode = amort
        vnc -= amort
        total += amort

    return {
        "amortissement": round(amort_periode, 6),
        "vnc_fin": round(vnc, 6),
        "amortissement_cumule": round(total, 6),
    }


def formule_prix_obligation(v: dict) -> dict:
    """PRICE simplifié — prix d'une obligation à partir du rendement."""
    valeur_nominale = float(v.get("valeur_nominale", 100))
    taux_coupon = float(v["taux_coupon"])
    rendement = float(v["rendement"])
    periodes = int(v["periodes"])
    frequence = int(v.get("frequence", 1))

    if periodes <= 0 or frequence <= 0:
        raise ValueError("periodes et frequence doivent être > 0.")

    coupon = valeur_nominale * taux_coupon / frequence
    r = rendement / frequence
    n = periodes * frequence

    # VA des coupons + VA du nominal
    if r == 0:
        prix = coupon * n + valeur_nominale
    else:
        prix = coupon * (1 - (1 + r) ** -n) / r + valeur_nominale / (1 + r) ** n

    return {"prix": round(prix, 6), "coupon": round(coupon, 6)}


# ═══════════════════════════════════════════════════════════════════════════════
# BASES DE DONNÉES (3)
# ═══════════════════════════════════════════════════════════════════════════════


def _filtrer_bd(base, criteres):
    """base: list of dicts, criteres: dict{champ: valeur_ou_operateur}."""
    resultat = []
    for ligne in base:
        ok = True
        for champ, cond in criteres.items():
            if champ not in ligne:
                ok = False
                break
            val = ligne[champ]
            if isinstance(cond, dict):
                op = cond.get("op", "==")
                ref = cond["valeur"]
                try:
                    va = float(val)
                    vr = float(ref)
                    if op == ">" and not va > vr:
                        ok = False
                    elif op == ">=" and not va >= vr:
                        ok = False
                    elif op == "<" and not va < vr:
                        ok = False
                    elif op == "<=" and not va <= vr:
                        ok = False
                    elif op == "==" and not va == vr:
                        ok = False
                    elif op == "!=" and not va != vr:
                        ok = False
                except (TypeError, ValueError):
                    if op == "==" and val != ref:
                        ok = False
                    elif op == "!=" and val == ref:
                        ok = False
            else:
                if val != cond:
                    ok = False
            if not ok:
                break
        if ok:
            resultat.append(ligne)
    return resultat


def formule_bdlire(v: dict) -> dict:
    """DGET — renvoie l'unique enregistrement correspondant aux critères."""
    base = v["base"]
    champ = str(v["champ"])
    criteres = v["criteres"]
    filtre = _filtrer_bd(base, criteres)
    if len(filtre) == 0:
        raise ValueError("Aucun enregistrement trouvé.")
    if len(filtre) > 1:
        raise ValueError("Plusieurs enregistrements trouvés.")
    if champ not in filtre[0]:
        raise KeyError(f"Champ '{champ}' absent.")
    return {"resultat": filtre[0][champ]}


def formule_bdproduit(v: dict) -> dict:
    """DPRODUCT — produit des valeurs d'un champ filtré."""
    base = v["base"]
    champ = str(v["champ"])
    criteres = v["criteres"]
    filtre = _filtrer_bd(base, criteres)
    produit = 1.0
    for ligne in filtre:
        produit *= float(ligne[champ])
    return {"produit": round(produit, 8), "nombre_enregistrements": len(filtre)}


def formule_bdecartype(v: dict) -> dict:
    """DSTDEV — écart-type échantillon sur champ filtré."""
    base = v["base"]
    champ = str(v["champ"])
    criteres = v["criteres"]
    filtre = _filtrer_bd(base, criteres)
    vals = [float(l[champ]) for l in filtre if champ in l]
    n = len(vals)
    if n < 2:
        raise ValueError("Au moins 2 enregistrements requis.")
    moy = sum(vals) / n
    var = sum((x - moy) ** 2 for x in vals) / (n - 1)
    return {"ecart_type": round(math.sqrt(var), 8), "nombre_enregistrements": n}


# ═══════════════════════════════════════════════════════════════════════════════
# MATHÉMATIQUES SPÉCIALISÉES (10)
# ═══════════════════════════════════════════════════════════════════════════════


def formule_arrondi_multiple(v: dict) -> dict:
    """MROUND — arrondi au multiple le plus proche."""
    nombre = float(v["nombre"])
    multiple = float(v["multiple"])
    if multiple == 0:
        return {"resultat": 0}
    if (nombre > 0 and multiple < 0) or (nombre < 0 and multiple > 0):
        raise ValueError("nombre et multiple doivent avoir le même signe.")
    return {"resultat": round(nombre / multiple) * multiple}


def formule_pgcd(v: dict) -> dict:
    """GCD — plus grand commun diviseur."""
    nombres = [int(x) for x in v["nombres"]]
    if not nombres:
        raise ValueError("Liste vide.")
    if any(n < 0 for n in nombres):
        raise ValueError("Entiers positifs uniquement.")
    result = nombres[0]
    for n in nombres[1:]:
        result = math.gcd(result, n)
    return {"pgcd": result}


def formule_ppcm(v: dict) -> dict:
    """LCM — plus petit commun multiple."""
    nombres = [int(x) for x in v["nombres"]]
    if not nombres:
        raise ValueError("Liste vide.")
    if any(n < 0 for n in nombres):
        raise ValueError("Entiers positifs uniquement.")
    if any(n == 0 for n in nombres):
        return {"ppcm": 0}
    result = nombres[0]
    for n in nombres[1:]:
        result = result * n // math.gcd(result, n)
    return {"ppcm": result}


def formule_quotient(v: dict) -> dict:
    """QUOTIENT — partie entière de la division."""
    num = float(v["numerateur"])
    den = float(v["denominateur"])
    if den == 0:
        raise ValueError("Division par zéro.")
    return {"quotient": int(num / den) if (num * den >= 0) else -int(abs(num) // abs(den))}


def formule_tableau_alea(v: dict) -> dict:
    """RANDARRAY — matrice aléatoire."""
    lignes = int(v.get("lignes", 1))
    colonnes = int(v.get("colonnes", 1))
    mini = float(v.get("min", 0))
    maxi = float(v.get("max", 1))
    entier = bool(v.get("entier", False))
    graine = v.get("graine")

    if lignes < 1 or colonnes < 1:
        raise ValueError("Dimensions >= 1 requises.")
    if mini >= maxi:
        raise ValueError("min doit être < max.")

    rng = random.Random(graine) if graine is not None else random
    matrice = []
    for _ in range(lignes):
        row = []
        for _ in range(colonnes):
            if entier:
                row.append(rng.randint(int(mini), int(maxi)))
            else:
                row.append(round(rng.uniform(mini, maxi), 6))
        matrice.append(row)

    return {"matrice": matrice, "lignes": lignes, "colonnes": colonnes}


def formule_combinaison(v: dict) -> dict:
    """COMBIN — nombre de combinaisons C(n, k)."""
    n = int(v["n"])
    k = int(v["k"])
    if n < 0 or k < 0 or k > n:
        raise ValueError("Paramètres invalides (0 <= k <= n).")
    return {"combinaison": math.comb(n, k)}


def formule_factorielle(v: dict) -> dict:
    """FACT — factorielle n!."""
    n = int(v["n"])
    if n < 0:
        raise ValueError("n doit être >= 0.")
    if n > 170:
        raise ValueError("n trop grand (limite 170).")
    return {"factorielle": math.factorial(n)}


def formule_sommeprod(v: dict) -> dict:
    """SUMPRODUCT — somme des produits terme à terme."""
    tableaux = v["tableaux"]  # list of lists, all same length
    if not tableaux:
        raise ValueError("Aucun tableau fourni.")
    n = len(tableaux[0])
    if any(len(t) != n for t in tableaux):
        raise ValueError("Tous les tableaux doivent avoir la même taille.")
    total = 0.0
    for i in range(n):
        prod = 1.0
        for t in tableaux:
            prod *= float(t[i])
        total += prod
    return {"resultat": round(total, 8)}


def formule_romain(v: dict) -> dict:
    """ROMAN — convertit un entier en chiffres romains (forme classique)."""
    n = int(v["nombre"])
    if not 1 <= n <= 3999:
        raise ValueError("Nombre entre 1 et 3999.")
    pairs = [
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
        (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
    ]
    result = ""
    for val, sym in pairs:
        while n >= val:
            result += sym
            n -= val
    return {"romain": result}


def formule_signe(v: dict) -> dict:
    """SIGN — renvoie 1, 0 ou -1 selon le signe."""
    n = float(v["nombre"])
    return {"signe": 1 if n > 0 else (-1 if n < 0 else 0)}


# ═══════════════════════════════════════════════════════════════════════════════
# LOGIQUE DE PRÉCISION (4)
# ═══════════════════════════════════════════════════════════════════════════════


def formule_si_na(v: dict) -> dict:
    """IFNA — renvoie une valeur de repli si la valeur est N/A."""
    valeur = v.get("valeur")
    fallback = v.get("fallback", "")
    if valeur is None or valeur == "#N/A" or (isinstance(valeur, str) and valeur.upper() == "N/A"):
        return {"resultat": fallback}
    return {"resultat": valeur}


def formule_esterr(v: dict) -> dict:
    """ISERR — vrai si erreur (hors N/A)."""
    valeur = v.get("valeur")
    if valeur is None:
        return {"resultat": False}
    if isinstance(valeur, str):
        codes = {"#DIV/0!", "#VALUE!", "#REF!", "#NAME?", "#NUM!", "#NULL!"}
        return {"resultat": valeur in codes}
    return {"resultat": False}


def formule_nb_val(v: dict) -> dict:
    """COUNTA — nombre de cellules non vides."""
    valeurs = v["valeurs"]
    count = sum(1 for x in valeurs if x is not None and x != "")
    return {"resultat": count}


def formule_nb_vide(v: dict) -> dict:
    """COUNTBLANK — nombre de cellules vides."""
    valeurs = v["valeurs"]
    count = sum(1 for x in valeurs if x is None or x == "")
    return {"resultat": count}


# ═══════════════════════════════════════════════════════════════════════════════
# STATISTIQUES SUPPLÉMENTAIRES (6)
# ═══════════════════════════════════════════════════════════════════════════════


def formule_mode_val(v: dict) -> dict:
    """MODE — valeur la plus fréquente."""
    valeurs = [float(x) for x in v["valeurs"]]
    if not valeurs:
        raise ValueError("Liste vide.")
    compte: dict = {}
    for x in valeurs:
        compte[x] = compte.get(x, 0) + 1
    max_freq = max(compte.values())
    if max_freq == 1:
        raise ValueError("Aucun mode (toutes valeurs uniques).")
    modes = sorted(k for k, c in compte.items() if c == max_freq)
    return {"mode": modes[0], "tous_modes": modes, "frequence": max_freq}


def formule_grande_valeur(v: dict) -> dict:
    """LARGE — k-ième plus grande valeur."""
    valeurs = sorted((float(x) for x in v["valeurs"]), reverse=True)
    k = int(v["k"])
    if k < 1 or k > len(valeurs):
        raise ValueError(f"k doit être entre 1 et {len(valeurs)}.")
    return {"resultat": valeurs[k - 1]}


def formule_petite_valeur(v: dict) -> dict:
    """SMALL — k-ième plus petite valeur."""
    valeurs = sorted(float(x) for x in v["valeurs"])
    k = int(v["k"])
    if k < 1 or k > len(valeurs):
        raise ValueError(f"k doit être entre 1 et {len(valeurs)}.")
    return {"resultat": valeurs[k - 1]}


def formule_moyenne_geo(v: dict) -> dict:
    """GEOMEAN — moyenne géométrique."""
    valeurs = [float(x) for x in v["valeurs"]]
    if not valeurs:
        raise ValueError("Liste vide.")
    if any(x <= 0 for x in valeurs):
        raise ValueError("Toutes les valeurs doivent être > 0.")
    produit = 1.0
    for x in valeurs:
        produit *= x
    return {"resultat": round(produit ** (1 / len(valeurs)), 8)}


def formule_moyenne_harm(v: dict) -> dict:
    """HARMEAN — moyenne harmonique."""
    valeurs = [float(x) for x in v["valeurs"]]
    if not valeurs:
        raise ValueError("Liste vide.")
    if any(x <= 0 for x in valeurs):
        raise ValueError("Toutes les valeurs doivent être > 0.")
    return {"resultat": round(len(valeurs) / sum(1 / x for x in valeurs), 8)}


def formule_ecart_moyen(v: dict) -> dict:
    """AVEDEV — écart moyen absolu à la moyenne."""
    valeurs = [float(x) for x in v["valeurs"]]
    n = len(valeurs)
    if n == 0:
        raise ValueError("Liste vide.")
    moy = sum(valeurs) / n
    return {"resultat": round(sum(abs(x - moy) for x in valeurs) / n, 8)}
