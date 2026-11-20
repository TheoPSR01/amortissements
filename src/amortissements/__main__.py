"""Ligne de commande : ``amortissements lineaire 10000 5 2025-04-01``."""

from __future__ import annotations

import argparse
import sys
from datetime import date

from . import __version__, degressif, ecrire_csv, lineaire


def _date(v: str) -> date:
    for sep in ("-", "/"):
        parts = v.split(sep)
        if len(parts) == 3:
            try:
                if len(parts[0]) == 4:
                    return date(int(parts[0]), int(parts[1]), int(parts[2]))
                return date(int(parts[2]), int(parts[1]), int(parts[0]))
            except ValueError:
                break
    raise argparse.ArgumentTypeError(f"date invalide : {v!r} (AAAA-MM-JJ ou JJ/MM/AAAA)")


def _fr(x) -> str:
    return f"{x:,.2f}".replace(",", " ").replace(".", ",")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="amortissements", description="Plans d'amortissement linéaire et dégressif.")
    p.add_argument("--version", action="version", version=f"amortissements {__version__}")
    p.add_argument("methode", choices=["lineaire", "degressif"])
    p.add_argument("valeur", help="valeur d'origine (HT)")
    p.add_argument("duree", type=int, help="durée d'utilisation en années")
    p.add_argument("date", type=_date, help="mise en service (linéaire) ou acquisition (dégressif)")
    p.add_argument("--cloture", type=int, default=12, help="mois de clôture de l'exercice (défaut : 12)")
    p.add_argument("--residuelle", default="0", help="valeur résiduelle (linéaire seulement)")
    p.add_argument("--csv", action="store_true", help="sortie CSV pour Excel")
    args = p.parse_args(argv)

    valeur = args.valeur.replace(",", ".")
    try:
        if args.methode == "lineaire":
            plan = lineaire(valeur, args.duree, args.date, args.cloture, args.residuelle.replace(",", "."))
        else:
            plan = degressif(valeur, args.duree, args.date, args.cloture)
    except (ValueError, ArithmeticError) as exc:
        print(f"amortissements : {exc}", file=sys.stderr)
        return 2

    if args.csv:
        ecrire_csv(plan, sys.stdout)
        return 0
    print(f"{'Exercice':<9} {'Base':>13} {'Taux':>8} {'Prorata':>8} {'Annuité':>13} {'Cumul':>13} {'VNC':>13}  Méthode")
    for l in plan:
        taux = f"{l.taux * 100:.2f} %".replace(".", ",")
        print(f"{l.exercice:<9} {_fr(l.base):>13} {taux:>8} {str(l.prorata).replace('.', ','):>8} "
              f"{_fr(l.annuite):>13} {_fr(l.cumul):>13} {_fr(l.vnc):>13}  {l.methode}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
