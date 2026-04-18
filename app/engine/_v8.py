"""
v8 — Ingénierie (suite) & Finance Obligations/Titres (Groupe 3).

30 nouvelles formules :
- Hyperboliques & trigo : SEC, SECH, SINH, TANH, IMTAN
- Conversions octales : OCT2BIN, OCT2DEC, OCT2HEX
- Finance - Amortissement : AMORLINC, AMORDEGRC
- Finance - Intérêts courus : ACCRINT, ACCRINTM, INTRATE, DISC
- Finance - Coupons : COUPDAYBS, COUPDAYS, COUPDAYSNC, COUPNCD, COUPNUM, COUPPCD
- Finance - Taux : EFFECT, NOMINAL
- Finance - Duration : DURATION, MDURATION
- Finance - Dollar : DOLLARDE, DOLLARFR
- Finance - Obligations atypiques : ODDFPRICE, ODDFYIELD, ODDLPRICE, ODDLYIELD
"""

from __future__ import annotations

import cmath
import math
from datetime import date, datetime, timedelta


# ═══════════════════════════════════════════════════════════════════════════════
# HYPERBOLIQUES, TRIGO & CONVERSIONS OCTALES
# ═══════════════════════════════════════════════════════════════════════════════


def formule_sinh(v: dict) -> dict:
    """SINH — sinus hyperbolique."""
    return {"resultat": round(math.sinh(float(v["x"])), 10)}


def formule_tanh(v: dict) -> dict:
    """TANH — tangente hyperbolique."""
    return {"resultat": round(math.tanh(float(v["x"])), 10)}


def formule_sec(v: dict) -> dict:
    """SEC — sécante = 1/cos(x)."""
    x = float(v["x"])
    c = math.cos(x)
    if abs(c) < 1e-15:
        raise ValueError("sec(x) indéfini : cos(x) = 0.")
    return {"resultat": round(1 / c, 10)}


def formule_sech(v: dict) -> dict:
    """SECH — sécante hyperbolique = 1/cosh(x)."""
    return {"resultat": round(1 / math.cosh(float(v["x"])), 10)}


def formule_imtan(v: dict) -> dict:
    """IMTAN — tangente d'un nombre complexe."""
    from app.engine._v7 import _parse_complex, _sortie_complexe

    c = _parse_complex(v["nombre"])
    suffixe = "j" if "j" in str(v["nombre"]).lower() else "i"
    return _sortie_complexe(cmath.tan(c), suffixe)


def formule_oct2bin(v: dict) -> dict:
    """OCT2BIN — octal → binaire."""
    texte = str(v["nombre"]).strip()
    try:
        n = int(texte, 8)
    except ValueError:
        raise ValueError(f"'{texte}' n'est pas un octal valide.")
    return {"resultat": format(n, "b")}


def formule_oct2dec(v: dict) -> dict:
    """OCT2DEC — octal → décimal."""
    texte = str(v["nombre"]).strip()
    try:
        return {"resultat": int(texte, 8)}
    except ValueError:
        raise ValueError(f"'{texte}' n'est pas un octal valide.")


def formule_oct2hex(v: dict) -> dict:
    """OCT2HEX — octal → hexadécimal."""
    texte = str(v["nombre"]).strip()
    try:
        n = int(texte, 8)
    except ValueError:
        raise ValueError(f"'{texte}' n'est pas un octal valide.")
    return {"resultat": format(n, "X")}


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS DATES & BASES DE COMPTAGE (financière)
# ═══════════════════════════════════════════════════════════════════════════════


def _parse_date(d) -> date:
    """Accepte une str ISO 'YYYY-MM-DD' ou un objet date/datetime."""
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    return datetime.strptime(str(d), "%Y-%m-%d").date()


def _days_360(d1: date, d2: date, european: bool = False) -> int:
    """Nombre de jours entre deux dates selon la convention 30/360."""
    y1, m1, jour1 = d1.year, d1.month, d1.day
    y2, m2, jour2 = d2.year, d2.month, d2.day
    if european:
        if jour1 == 31:
            jour1 = 30
        if jour2 == 31:
            jour2 = 30
    else:
        # US 30/360
        if jour1 == 31:
            jour1 = 30
        if jour2 == 31 and jour1 >= 30:
            jour2 = 30
    return (y2 - y1) * 360 + (m2 - m1) * 30 + (jour2 - jour1)


def _year_fraction(d1: date, d2: date, basis: int = 0) -> float:
    """Fraction d'année entre deux dates selon la base.

    Bases :
    - 0 : 30/360 US (défaut Excel)
    - 1 : actual/actual
    - 2 : actual/360
    - 3 : actual/365
    - 4 : 30/360 européen
    """
    if basis == 0:
        return _days_360(d1, d2) / 360
    if basis == 1:
        # Approximation : actual/actual avec moyenne
        days = (d2 - d1).days
        y1_days = 366 if _is_leap(d1.year) else 365
        return days / y1_days
    if basis == 2:
        return (d2 - d1).days / 360
    if basis == 3:
        return (d2 - d1).days / 365
    if basis == 4:
        return _days_360(d1, d2, european=True) / 360
    raise ValueError(f"Base invalide : {basis} (attendu 0, 1, 2, 3 ou 4).")


def _is_leap(y: int) -> bool:
    return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)


def _days_in_year(d: date, basis: int) -> int:
    if basis in (0, 2, 4):
        return 360
    if basis == 3:
        return 365
    return 366 if _is_leap(d.year) else 365


def _add_months(d: date, months: int) -> date:
    """Ajoute des mois à une date en préservant le jour si possible."""
    total = d.month - 1 + months
    y = d.year + total // 12
    m = total % 12 + 1
    import calendar
    dim = calendar.monthrange(y, m)[1]
    jour = min(d.day, dim)
    return date(y, m, jour)


# ═══════════════════════════════════════════════════════════════════════════════
# FINANCE — AMORTISSEMENTS (AMORLINC, AMORDEGRC)
# ═══════════════════════════════════════════════════════════════════════════════


def formule_amorlinc(v: dict) -> dict:
    """AMORLINC — amortissement linéaire prorata (convention française)."""
    cout = float(v["cout"])
    valeur_residuelle = float(v.get("valeur_residuelle", 0))
    periode = int(v["periode"])
    taux = float(v["taux"])

    if taux <= 0 or taux >= 1:
        raise ValueError("Le taux doit être entre 0 et 1 (exclus).")

    amort_annuel = cout * taux
    duree_totale = (cout - valeur_residuelle) / amort_annuel

    if periode < 0:
        raise ValueError("La période doit être positive.")

    # Simplification : prorata première année = 0.5, dernière année résiduelle
    if periode == 0:
        resultat = amort_annuel * 0.5
    elif periode >= int(duree_totale):
        resultat = max(0, cout - valeur_residuelle - amort_annuel * (periode - 0.5))
    else:
        resultat = amort_annuel
    return {"amortissement": round(resultat, 2)}


def formule_amordegrc(v: dict) -> dict:
    """AMORDEGRC — amortissement dégressif avec coefficient (convention française)."""
    cout = float(v["cout"])
    valeur_residuelle = float(v.get("valeur_residuelle", 0))
    periode = int(v["periode"])
    taux = float(v["taux"])

    # Coefficient dégressif selon la durée de vie
    duree = 1 / taux
    if duree < 3:
        coef = 1.0
    elif duree < 5:
        coef = 1.5
    elif duree <= 6:
        coef = 2.0
    else:
        coef = 2.5

    taux_deg = taux * coef
    valeur_residuelle_courante = cout
    amort = 0
    for p in range(periode + 1):
        amort = valeur_residuelle_courante * taux_deg
        if amort < (cout - valeur_residuelle) * taux:
            amort = (cout - valeur_residuelle) * taux
        if valeur_residuelle_courante - amort < valeur_residuelle:
            amort = valeur_residuelle_courante - valeur_residuelle
            valeur_residuelle_courante = valeur_residuelle
            break
        valeur_residuelle_courante -= amort
    return {"amortissement": round(amort, 2)}


# ═══════════════════════════════════════════════════════════════════════════════
# FINANCE — INTÉRÊTS COURUS (ACCRINT, ACCRINTM, INTRATE, DISC)
# ═══════════════════════════════════════════════════════════════════════════════


def formule_accrint(v: dict) -> dict:
    """ACCRINT — intérêts courus d'un titre à coupons périodiques."""
    emission = _parse_date(v["emission"])
    reglement = _parse_date(v["reglement"])
    taux = float(v["taux"])
    valeur_nominale = float(v.get("valeur_nominale", 1000))
    basis = int(v.get("base", 0))

    if reglement <= emission:
        raise ValueError("La date de règlement doit être après l'émission.")

    fraction = _year_fraction(emission, reglement, basis)
    interets = valeur_nominale * taux * fraction
    return {"interets": round(interets, 2)}


def formule_accrintm(v: dict) -> dict:
    """ACCRINTM — intérêts courus à échéance (un seul paiement)."""
    emission = _parse_date(v["emission"])
    echeance = _parse_date(v["echeance"])
    taux = float(v["taux"])
    valeur_nominale = float(v.get("valeur_nominale", 1000))
    basis = int(v.get("base", 0))

    fraction = _year_fraction(emission, echeance, basis)
    return {"interets": round(valeur_nominale * taux * fraction, 2)}


def formule_intrate(v: dict) -> dict:
    """INTRATE — taux d'intérêt d'un titre entièrement investi."""
    reglement = _parse_date(v["reglement"])
    echeance = _parse_date(v["echeance"])
    investissement = float(v["investissement"])
    remboursement = float(v["remboursement"])
    basis = int(v.get("base", 0))

    if investissement <= 0:
        raise ValueError("L'investissement doit être positif.")

    fraction = _year_fraction(reglement, echeance, basis)
    if fraction <= 0:
        raise ValueError("L'échéance doit être après le règlement.")

    taux = (remboursement - investissement) / investissement / fraction
    return {"taux": round(taux, 8)}


def formule_disc(v: dict) -> dict:
    """DISC — taux d'escompte d'un titre."""
    reglement = _parse_date(v["reglement"])
    echeance = _parse_date(v["echeance"])
    prix = float(v["prix"])
    remboursement = float(v["remboursement"])
    basis = int(v.get("base", 0))

    if remboursement <= 0:
        raise ValueError("Le remboursement doit être positif.")

    fraction = _year_fraction(reglement, echeance, basis)
    if fraction <= 0:
        raise ValueError("L'échéance doit être après le règlement.")

    taux = (remboursement - prix) / remboursement / fraction
    return {"taux_escompte": round(taux, 8)}


# ═══════════════════════════════════════════════════════════════════════════════
# FINANCE — COUPONS (COUPDAYBS, COUPDAYS, COUPDAYSNC, COUPNCD, COUPNUM, COUPPCD)
# ═══════════════════════════════════════════════════════════════════════════════


def _coup_dates(reglement: date, echeance: date, frequence: int) -> tuple[date, date]:
    """Retourne (coupon_precedent, coupon_suivant) autour de la date de règlement."""
    if frequence not in (1, 2, 4):
        raise ValueError("Fréquence invalide : 1 (annuel), 2 (semestriel) ou 4 (trimestriel).")
    mois_coupon = 12 // frequence

    # On recule depuis l'échéance jusqu'à trouver les deux coupons entourant le règlement
    courant = echeance
    while courant > reglement:
        precedent = _add_months(courant, -mois_coupon)
        if precedent <= reglement:
            return precedent, courant
        courant = precedent
    # Cas limite
    return courant, _add_months(courant, mois_coupon)


def formule_coupdaybs(v: dict) -> dict:
    """COUPDAYBS — jours entre le dernier coupon et le règlement."""
    reglement = _parse_date(v["reglement"])
    echeance = _parse_date(v["echeance"])
    frequence = int(v["frequence"])
    basis = int(v.get("base", 0))

    precedent, _ = _coup_dates(reglement, echeance, frequence)
    if basis in (0, 4):
        jours = _days_360(precedent, reglement, european=(basis == 4))
    else:
        jours = (reglement - precedent).days
    return {"jours": jours}


def formule_coupdays(v: dict) -> dict:
    """COUPDAYS — jours dans la période de coupon contenant le règlement."""
    reglement = _parse_date(v["reglement"])
    echeance = _parse_date(v["echeance"])
    frequence = int(v["frequence"])
    basis = int(v.get("base", 0))

    precedent, suivant = _coup_dates(reglement, echeance, frequence)
    if basis in (0, 4):
        jours = _days_360(precedent, suivant, european=(basis == 4))
    elif basis == 2:
        jours = 360 // frequence
    elif basis == 3:
        jours = 365 // frequence
    else:
        jours = (suivant - precedent).days
    return {"jours": jours}


def formule_coupdaysnc(v: dict) -> dict:
    """COUPDAYSNC — jours entre le règlement et le prochain coupon."""
    reglement = _parse_date(v["reglement"])
    echeance = _parse_date(v["echeance"])
    frequence = int(v["frequence"])
    basis = int(v.get("base", 0))

    _, suivant = _coup_dates(reglement, echeance, frequence)
    if basis in (0, 4):
        jours = _days_360(reglement, suivant, european=(basis == 4))
    else:
        jours = (suivant - reglement).days
    return {"jours": jours}


def formule_coupncd(v: dict) -> dict:
    """COUPNCD — date du prochain coupon après le règlement."""
    reglement = _parse_date(v["reglement"])
    echeance = _parse_date(v["echeance"])
    frequence = int(v["frequence"])

    _, suivant = _coup_dates(reglement, echeance, frequence)
    return {"date_coupon": suivant.isoformat()}


def formule_coupnum(v: dict) -> dict:
    """COUPNUM — nombre de coupons payables entre règlement et échéance."""
    reglement = _parse_date(v["reglement"])
    echeance = _parse_date(v["echeance"])
    frequence = int(v["frequence"])

    if frequence not in (1, 2, 4):
        raise ValueError("Fréquence invalide : 1, 2 ou 4.")
    mois_coupon = 12 // frequence

    count = 0
    courant = echeance
    while courant > reglement:
        count += 1
        courant = _add_months(courant, -mois_coupon)
    return {"nombre": count}


def formule_couppcd(v: dict) -> dict:
    """COUPPCD — date du coupon précédent le règlement."""
    reglement = _parse_date(v["reglement"])
    echeance = _parse_date(v["echeance"])
    frequence = int(v["frequence"])

    precedent, _ = _coup_dates(reglement, echeance, frequence)
    return {"date_coupon": precedent.isoformat()}


# ═══════════════════════════════════════════════════════════════════════════════
# FINANCE — TAUX (EFFECT, NOMINAL)
# ═══════════════════════════════════════════════════════════════════════════════


def formule_effect(v: dict) -> dict:
    """EFFECT — taux effectif annuel = (1 + nominal/n)^n - 1."""
    taux_nominal = float(v["taux_nominal"])
    periodes = int(v["periodes"])

    if periodes <= 0:
        raise ValueError("Le nombre de périodes doit être positif.")
    if taux_nominal <= 0:
        raise ValueError("Le taux nominal doit être positif.")

    taux_effectif = (1 + taux_nominal / periodes) ** periodes - 1
    return {"taux_effectif": round(taux_effectif, 10)}


def formule_nominal(v: dict) -> dict:
    """NOMINAL — taux nominal annuel depuis le taux effectif."""
    taux_effectif = float(v["taux_effectif"])
    periodes = int(v["periodes"])

    if periodes <= 0:
        raise ValueError("Le nombre de périodes doit être positif.")
    if taux_effectif <= 0:
        raise ValueError("Le taux effectif doit être positif.")

    taux_nominal = ((1 + taux_effectif) ** (1 / periodes) - 1) * periodes
    return {"taux_nominal": round(taux_nominal, 10)}


# ═══════════════════════════════════════════════════════════════════════════════
# FINANCE — DURATION (DURATION, MDURATION)
# ═══════════════════════════════════════════════════════════════════════════════


def formule_duration(v: dict) -> dict:
    """DURATION — duration de Macaulay simplifiée (années jusqu'à échéance pondérées)."""
    taux_coupon = float(v["taux_coupon"])
    rendement = float(v["rendement"])
    periodes = int(v["periodes"])
    frequence = int(v.get("frequence", 2))
    valeur_nominale = float(v.get("valeur_nominale", 100))

    if frequence not in (1, 2, 4):
        raise ValueError("Fréquence invalide : 1, 2 ou 4.")

    coupon = valeur_nominale * taux_coupon / frequence
    taux_periode = rendement / frequence
    n = periodes * frequence

    prix = 0
    poids = 0
    for t in range(1, n + 1):
        cf = coupon + (valeur_nominale if t == n else 0)
        pv = cf / (1 + taux_periode) ** t
        prix += pv
        poids += t * pv

    if prix == 0:
        raise ValueError("Prix nul — calcul de duration impossible.")
    duration_periodes = poids / prix
    return {"duration": round(duration_periodes / frequence, 6)}


def formule_mduration(v: dict) -> dict:
    """MDURATION — duration modifiée = duration / (1 + rendement/frequence)."""
    duration = formule_duration(v)["duration"]
    rendement = float(v["rendement"])
    frequence = int(v.get("frequence", 2))
    return {"duration_modifiee": round(duration / (1 + rendement / frequence), 6)}


# ═══════════════════════════════════════════════════════════════════════════════
# FINANCE — DOLLAR (DOLLARDE, DOLLARFR)
# ═══════════════════════════════════════════════════════════════════════════════


def formule_dollarde(v: dict) -> dict:
    """DOLLARDE — convertit un prix fractionnaire en prix décimal.

    Ex : 1.02 en 1/16 → 1 + 2/16 = 1.125
    """
    prix_frac = float(v["prix_fractionnaire"])
    fraction = int(v["fraction"])

    if fraction <= 0:
        raise ValueError("La fraction doit être positive.")

    partie_entiere = int(prix_frac)
    partie_decimale = prix_frac - partie_entiere
    # Normalise : .02 avec fraction=16 → 2/16
    diviseur = 10 ** len(str(fraction))
    numerateur = partie_decimale * diviseur
    resultat = partie_entiere + numerateur / fraction
    return {"resultat": round(resultat, 6)}


def formule_dollarfr(v: dict) -> dict:
    """DOLLARFR — convertit un prix décimal en prix fractionnaire."""
    prix_decimal = float(v["prix_decimal"])
    fraction = int(v["fraction"])

    if fraction <= 0:
        raise ValueError("La fraction doit être positive.")

    partie_entiere = int(prix_decimal)
    partie_decimale = prix_decimal - partie_entiere
    numerateur = partie_decimale * fraction
    diviseur = 10 ** len(str(fraction))
    resultat = partie_entiere + numerateur / diviseur
    return {"resultat": round(resultat, 6)}


# ═══════════════════════════════════════════════════════════════════════════════
# FINANCE — OBLIGATIONS ATYPIQUES (ODDFPRICE, ODDFYIELD, ODDLPRICE, ODDLYIELD)
# ═══════════════════════════════════════════════════════════════════════════════


def _bond_price_standard(
    taux_coupon: float,
    rendement: float,
    periodes: int,
    frequence: int,
    valeur_nominale: float = 100,
) -> float:
    """Prix d'une obligation standard (coupons périodiques + nominal à terme)."""
    coupon = valeur_nominale * taux_coupon / frequence
    taux_periode = rendement / frequence
    n = periodes * frequence
    prix = 0
    for t in range(1, n + 1):
        cf = coupon + (valeur_nominale if t == n else 0)
        prix += cf / (1 + taux_periode) ** t
    return prix


def formule_oddfprice(v: dict) -> dict:
    """ODDFPRICE — prix d'une obligation avec première période atypique (approximé)."""
    taux_coupon = float(v["taux_coupon"])
    rendement = float(v["rendement"])
    periodes = int(v["periodes"])
    frequence = int(v.get("frequence", 2))
    valeur_nominale = float(v.get("valeur_nominale", 100))
    premier_coupon_jours = float(v.get("premier_coupon_jours", 0))
    jours_periode = 365 / frequence

    prix_standard = _bond_price_standard(
        taux_coupon, rendement, periodes, frequence, valeur_nominale,
    )
    # Ajustement pro-rata de la première période
    ratio = premier_coupon_jours / jours_periode if jours_periode > 0 else 1
    ajustement = valeur_nominale * taux_coupon / frequence * (1 - ratio)
    return {"prix": round(prix_standard + ajustement, 4)}


def formule_oddfyield(v: dict) -> dict:
    """ODDFYIELD — rendement d'une obligation atypique (recherche par bissection)."""
    taux_coupon = float(v["taux_coupon"])
    prix = float(v["prix"])
    periodes = int(v["periodes"])
    frequence = int(v.get("frequence", 2))
    valeur_nominale = float(v.get("valeur_nominale", 100))
    premier_coupon_jours = float(v.get("premier_coupon_jours", 0))

    def f(y):
        return formule_oddfprice({
            "taux_coupon": taux_coupon, "rendement": y, "periodes": periodes,
            "frequence": frequence, "valeur_nominale": valeur_nominale,
            "premier_coupon_jours": premier_coupon_jours,
        })["prix"] - prix

    bas, haut = 0.0001, 1.0
    for _ in range(100):
        mid = (bas + haut) / 2
        if f(mid) > 0:
            bas = mid
        else:
            haut = mid
        if haut - bas < 1e-10:
            break
    return {"rendement": round((bas + haut) / 2, 8)}


def formule_oddlprice(v: dict) -> dict:
    """ODDLPRICE — prix d'une obligation avec dernière période atypique (approximé)."""
    taux_coupon = float(v["taux_coupon"])
    rendement = float(v["rendement"])
    periodes = int(v["periodes"])
    frequence = int(v.get("frequence", 2))
    valeur_nominale = float(v.get("valeur_nominale", 100))
    dernier_coupon_jours = float(v.get("dernier_coupon_jours", 0))
    jours_periode = 365 / frequence

    prix_standard = _bond_price_standard(
        taux_coupon, rendement, periodes, frequence, valeur_nominale,
    )
    ratio = dernier_coupon_jours / jours_periode if jours_periode > 0 else 1
    ajustement = valeur_nominale * taux_coupon / frequence * (ratio - 1)
    return {"prix": round(prix_standard + ajustement, 4)}


def formule_oddlyield(v: dict) -> dict:
    """ODDLYIELD — rendement avec dernière période atypique (bissection)."""
    taux_coupon = float(v["taux_coupon"])
    prix = float(v["prix"])
    periodes = int(v["periodes"])
    frequence = int(v.get("frequence", 2))
    valeur_nominale = float(v.get("valeur_nominale", 100))
    dernier_coupon_jours = float(v.get("dernier_coupon_jours", 0))

    def f(y):
        return formule_oddlprice({
            "taux_coupon": taux_coupon, "rendement": y, "periodes": periodes,
            "frequence": frequence, "valeur_nominale": valeur_nominale,
            "dernier_coupon_jours": dernier_coupon_jours,
        })["prix"] - prix

    bas, haut = 0.0001, 1.0
    for _ in range(100):
        mid = (bas + haut) / 2
        if f(mid) > 0:
            bas = mid
        else:
            haut = mid
        if haut - bas < 1e-10:
            break
    return {"rendement": round((bas + haut) / 2, 8)}
