"""amortissements : plans d'amortissement linéaire et dégressif (règles françaises).

Linéaire : prorata temporis en jours, à partir de la date de mise en service,
sur une année de 360 jours (mois de 30 jours).

Dégressif fiscal (article 39 A du CGI) : taux linéaire multiplié par 1,25
(durée de 3 ou 4 ans), 1,75 (5 ou 6 ans) ou 2,25 (plus de 6 ans) ; prorata
en mois entiers à partir du premier jour du mois d'acquisition ; passage au
linéaire dès que l'annuité linéaire sur la durée restante devient supérieure.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import TextIO, Union

__version__ = "0.1.0"

CENT = Decimal("0.01")
Montant = Union[int, float, str, Decimal]


@dataclass(frozen=True)
class Annuite:
    exercice: int          # année de clôture de l'exercice
    base: Decimal          # valeur nette comptable en début d'exercice
    taux: Decimal          # taux appliqué (en fraction : 0.35 pour 35 %)
    prorata: Decimal       # fraction d'année retenue (1 pour un exercice complet)
    annuite: Decimal
    cumul: Decimal
    vnc: Decimal           # valeur nette comptable en fin d'exercice
    methode: str           # "lineaire" ou "degressif"


def _d(x: Montant) -> Decimal:
    return x if isinstance(x, Decimal) else Decimal(str(x))


def _arrondi(x: Decimal) -> Decimal:
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


def coefficient_degressif(duree: int) -> Decimal:
    """Coefficient fiscal de l'article 39 A du CGI pour une durée d'utilisation en années."""
    if duree < 3:
        raise ValueError("l'amortissement dégressif suppose une durée d'utilisation d'au moins 3 ans")
    if duree <= 4:
        return Decimal("1.25")
    if duree <= 6:
        return Decimal("1.75")
    return Decimal("2.25")


def _fin_exercice(annee: int, mois_cloture: int) -> date:
    if mois_cloture == 12:
        return date(annee, 12, 31)
    return date(annee, mois_cloture + 1, 1) - timedelta(days=1)


def _premier_exercice(debut: date, mois_cloture: int) -> int:
    """Année de clôture de l'exercice qui contient la date ``debut``."""
    return debut.year if debut.month <= mois_cloture else debut.year + 1


def jours_360(debut: date, fin: date) -> int:
    """Nombre de jours de ``debut`` à ``fin`` inclus, en base 360 (mois de 30 jours)."""
    d1 = min(debut.day, 30)
    d2 = 30 if fin.day >= 30 or (fin.month == 2 and fin.day >= 28) else fin.day
    return (fin.year - debut.year) * 360 + (fin.month - debut.month) * 30 + (d2 - d1) + 1


def lineaire(
    valeur: Montant,
    duree: int,
    mise_en_service: date,
    mois_cloture: int = 12,
    valeur_residuelle: Montant = 0,
) -> list:
    """Plan d'amortissement linéaire avec prorata temporis en jours (base 360)."""
    valeur, residuel = _d(valeur), _d(valeur_residuelle)
    if duree < 1:
        raise ValueError("la durée doit être d'au moins 1 an")
    if not 1 <= mois_cloture <= 12:
        raise ValueError("mois de clôture entre 1 et 12")
    base = valeur - residuel
    if base <= 0:
        raise ValueError("la base amortissable doit être positive")
    taux = Decimal(1) / Decimal(duree)
    annuite_pleine = base * taux

    exercice = _premier_exercice(mise_en_service, mois_cloture)
    jours = jours_360(mise_en_service, _fin_exercice(exercice, mois_cloture))
    prorata = Decimal(jours) / Decimal(360)

    # Avec un prorata la première année, le plan s'étend sur duree + 1 exercices.
    nb_exercices = duree if prorata == 1 else duree + 1

    plan, cumul = [], Decimal(0)
    for rang in range(1, nb_exercices + 1):
        restant = base - cumul
        a = _arrondi(annuite_pleine * prorata)
        if rang == nb_exercices or a >= restant:
            a, prorata_ligne = restant, (restant / annuite_pleine)
        else:
            prorata_ligne = prorata
        vnc_debut = valeur - cumul
        cumul += a
        plan.append(Annuite(exercice, vnc_debut, taux, _arrondi_prorata(prorata_ligne), a, cumul, valeur - cumul, "lineaire"))
        exercice += 1
        prorata = Decimal(1)
        if cumul >= base:
            break
    return plan


def _arrondi_prorata(p: Decimal) -> Decimal:
    return p.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def degressif(
    valeur: Montant,
    duree: int,
    acquisition: date,
    mois_cloture: int = 12,
) -> list:
    """Plan d'amortissement dégressif fiscal avec passage au linéaire.

    Le plan compte autant d'exercices que la durée d'utilisation : la réduction
    de la première annuité (prorata en mois) n'est pas reportée au-delà.
    """
    valeur = _d(valeur)
    if valeur <= 0:
        raise ValueError("la valeur doit être positive")
    if not 1 <= mois_cloture <= 12:
        raise ValueError("mois de clôture entre 1 et 12")
    coef = coefficient_degressif(duree)
    taux_deg = coef / Decimal(duree)

    exercice = _premier_exercice(acquisition, mois_cloture)
    mois = (mois_cloture - acquisition.month) % 12 + 1
    prorata = Decimal(mois) / Decimal(12)

    plan, cumul = [], Decimal(0)
    for rang in range(1, duree + 1):
        vnc = valeur - cumul
        restantes = duree - rang + 1
        taux_lin = Decimal(1) / Decimal(restantes)
        if rang == duree:
            taux, methode, a = taux_lin, "lineaire", vnc
        elif taux_lin > taux_deg:
            taux, methode = taux_lin, "lineaire"
            a = _arrondi(vnc * taux * prorata)
        else:
            taux, methode = taux_deg, "degressif"
            a = _arrondi(vnc * taux * prorata)
        cumul += a
        plan.append(Annuite(exercice, vnc, taux, _arrondi_prorata(prorata), a, cumul, valeur - cumul, methode))
        exercice += 1
        prorata = Decimal(1)
    return plan


def ecrire_csv(plan: list, sortie: TextIO, separateur: str = ";") -> None:
    """Écrit un plan au format CSV (virgule décimale, lisible par Excel en français)."""
    w = csv.writer(sortie, delimiter=separateur)
    w.writerow(["Exercice", "Base", "Taux", "Prorata", "Annuite", "Cumul", "VNC", "Methode"])

    def fr(x: Decimal) -> str:
        return str(x).replace(".", ",")

    for l in plan:
        w.writerow([l.exercice, fr(l.base), fr(_arrondi_prorata(l.taux)), fr(l.prorata),
                    fr(l.annuite), fr(l.cumul), fr(l.vnc), l.methode])


__all__ = ["Annuite", "coefficient_degressif", "degressif", "ecrire_csv", "jours_360", "lineaire"]
