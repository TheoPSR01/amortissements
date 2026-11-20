from datetime import date
from decimal import Decimal

import pytest

from amortissements import coefficient_degressif, degressif, jours_360, lineaire
from amortissements.__main__ import main


def annuites(plan):
    return [str(l.annuite) for l in plan]


def test_coefficients():
    assert coefficient_degressif(3) == Decimal("1.25")
    assert coefficient_degressif(4) == Decimal("1.25")
    assert coefficient_degressif(5) == Decimal("1.75")
    assert coefficient_degressif(6) == Decimal("1.75")
    assert coefficient_degressif(10) == Decimal("2.25")
    with pytest.raises(ValueError):
        coefficient_degressif(2)


def test_jours_360():
    assert jours_360(date(2025, 4, 1), date(2025, 12, 31)) == 270
    assert jours_360(date(2025, 1, 1), date(2025, 12, 31)) == 360
    assert jours_360(date(2025, 7, 15), date(2025, 12, 31)) == 166
    assert jours_360(date(2025, 3, 1), date(2026, 2, 28)) == 360


def test_degressif_annee_complete():
    # Exemple classique : 100 000 €, 5 ans, taux 35 %, bascule au linéaire en 4e année
    plan = degressif(100000, 5, date(2025, 1, 1))
    assert annuites(plan) == ["35000.00", "22750.00", "14787.50", "13731.25", "13731.25"]
    assert [l.methode for l in plan] == ["degressif"] * 3 + ["lineaire"] * 2
    assert plan[-1].vnc == 0


def test_degressif_prorata_en_mois():
    # Acquis le 20 avril : 9 mois (avril compte en entier)
    plan = degressif(100000, 5, date(2025, 4, 20))
    assert plan[0].prorata == Decimal("0.75")
    assert plan[0].annuite == Decimal("26250.00")
    assert len(plan) == 5
    assert plan[-1].cumul == Decimal("100000")


def test_degressif_cloture_decalee():
    plan = degressif(9000, 3, date(2025, 10, 5), mois_cloture=3)
    assert plan[0].exercice == 2026
    assert plan[0].prorata == Decimal("0.5")      # octobre à mars
    assert plan[-1].vnc == 0


def test_lineaire_prorata_en_jours():
    plan = lineaire(10000, 5, date(2025, 4, 1))
    assert annuites(plan) == ["1500.00", "2000.00", "2000.00", "2000.00", "2000.00", "500.00"]
    assert plan[-1].vnc == 0


def test_lineaire_annee_complete_et_residuelle():
    plan = lineaire(12000, 4, date(2025, 1, 1), valeur_residuelle=2000)
    assert annuites(plan) == ["2500.00"] * 4
    assert plan[-1].vnc == Decimal("2000")


def test_lineaire_arrondis():
    plan = lineaire(1000, 3, date(2025, 1, 1))
    assert sum(l.annuite for l in plan) == Decimal("1000")
    assert annuites(plan) == ["333.33", "333.33", "333.34"]


@pytest.mark.parametrize("args", [
    (0, 5, date(2025, 1, 1)),
    (1000, 0, date(2025, 1, 1)),
])
def test_erreurs_lineaire(args):
    with pytest.raises(ValueError):
        lineaire(*args)


def test_cli(capsys):
    assert main(["degressif", "100000", "5", "2025-01-01"]) == 0
    out = capsys.readouterr().out
    assert "35 000,00" in out and "13 731,25" in out
    assert main(["lineaire", "10000", "5", "01/04/2025", "--csv"]) == 0
    assert "2025;10000;0,2000;0,7500;1500,00;1500,00;8500,00;lineaire" in capsys.readouterr().out


def test_cli_erreur(capsys):
    assert main(["degressif", "1000", "2", "2025-01-01"]) == 2
