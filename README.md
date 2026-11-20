# amortissements

Calculer un plan d'amortissement linéaire ou dégressif selon les règles françaises, en ligne de commande ou en Python. Aucune dépendance.

Utile aux étudiants en comptabilité et en contrôle de gestion pour vérifier leurs exercices, aux indépendants qui achètent du matériel, et à quiconque veut comparer les deux méthodes avant de choisir.

## Installation

```bash
pip install git+https://github.com/TheoPSR01/amortissements.git
```

Python 3.10 ou plus récent.

## En ligne de commande

```bash
amortissements degressif 100000 5 2025-01-01
```

```
Exercice           Base     Taux  Prorata       Annuité         Cumul           VNC  Méthode
2025         100 000,00  35,00 %   1,0000     35 000,00     35 000,00     65 000,00  degressif
2026          65 000,00  35,00 %   1,0000     22 750,00     57 750,00     42 250,00  degressif
2027          42 250,00  35,00 %   1,0000     14 787,50     72 537,50     27 462,50  degressif
2028          27 462,50  50,00 %   1,0000     13 731,25     86 268,75     13 731,25  lineaire
2029          13 731,25 100,00 %   1,0000     13 731,25    100 000,00          0,00  lineaire
```

```bash
amortissements lineaire 10000 5 01/04/2025                 # mise en service le 1er avril
amortissements lineaire 12000 4 2025-01-01 --residuelle 2000
amortissements degressif 9000 3 2025-10-05 --cloture 3     # exercice clos le 31 mars
amortissements lineaire 10000 5 2025-04-01 --csv > plan.csv  # pour Excel
```

## En Python

```python
from datetime import date
from amortissements import lineaire, degressif

for ligne in degressif(100000, 5, date(2025, 4, 20)):
    print(ligne.exercice, ligne.annuite, ligne.vnc, ligne.methode)
```

Chaque ligne du plan donne l'exercice, la base (valeur nette en début d'exercice), le taux, le prorata, l'annuité, le cumul, la valeur nette comptable de fin d'exercice et la méthode. Les montants sont des `Decimal` arrondis au centime ; la dernière annuité absorbe les écarts d'arrondi.

## Règles appliquées

Linéaire : annuité égale à la base amortissable divisée par la durée. La première annuité est réduite au prorata du nombre de jours entre la mise en service et la clôture, sur une année de 360 jours (mois de 30 jours). Le complément est pris sur un exercice supplémentaire à la fin du plan.

Dégressif fiscal (article 39 A du CGI) : le taux linéaire est multiplié par 1,25 pour une durée de 3 ou 4 ans, 1,75 pour 5 ou 6 ans, 2,25 au-delà de 6 ans. La première annuité est réduite en mois entiers à partir du premier jour du mois d'acquisition. Chaque année, l'annuité est calculée sur la valeur nette ; on passe au linéaire dès que l'annuité linéaire sur la durée restante devient plus forte. Le plan compte autant d'exercices que la durée d'utilisation.

## Limites

L'outil ne vérifie pas si le bien est éligible au dégressif (biens neufs, certaines catégories d'équipement) ; c'est à l'utilisateur de le savoir. Les exercices sont supposés durer 12 mois. Les amortissements dérogatoires, les dépréciations et les cessions en cours de plan ne sont pas traités.

## Contribuer

```bash
git clone https://github.com/TheoPSR01/amortissements.git
cd amortissements
pip install -e ".[dev]"
pytest
```

## Licence

MIT
