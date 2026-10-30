# Téléchargement des données et construction de la base.

## Objectif

Construire une base contenant une ligne par partenaire commercial et par mois,
avec les importations, les exportations et les droits de douane américains.

La période couvre janvier 2010 à décembre 2025, soit 192 mois.

## Source

Les données proviennent de l’API du U.S. Census Bureau :
Lien principal : https://www.census.gov/data/developers/data-sets/international-trade.html

- Importations : https://api.census.gov/data/timeseries/intltrade/imports/hs
- Exportations : https://api.census.gov/data/timeseries/intltrade/exports/hs

Une clé API est requise pour importer les données depuis le site.
Il est possible d'en demander une ici : https://api.census.gov/data/key_signup.html

## Fichier final

Le fichier final est `data/commerce_usa_2010_2025.csv`. Il contient les colonnes suivantes :
- CTY_CODE : Code Census du partenaire commercial 
- CTY_NAME : Nom du partenaire commercial 
- time : Mois et année au format YYYY-MM
- importations_generales : Valeur des importations générales des États-Unis depuis le partenaire en USD 
- importations_consommation : Valeur des importations mises à disposition du marché américain en USD 
- droits_douane : Montant des droits de douane calculés sur les importations pour consommation en USD 
- exportations : Valeur totale des exportations des États-Unis vers le partenaire en USD 

Les montants sont mensuels, exprimés en dollars américains courants, et regroupent toutes les catégories de produits. 
Lors de la lecture du CSV avec pandas, conserver le code du partenaire comme texte en utilisant dtype={"CTY_CODE": str}.

## Étapes de construction

1. Télécharger les importations pour chaque mois.
2. Télécharger les exportations pour chaque mois.
3. Assembler les fichiers mensuels d’importations.
4. Assembler les fichiers mensuels d’exportations.
5. Réunir les deux bases pour obtenir le fichier final "commerce_usa_2010_2025.csv".

Les fichiers intermédiaires et le fichier final sont enregistrés dans `data/`.

La jointure utilise le code du partenaire et le mois.
Elle conserve les couples présents dans au moins une des deux sources.

## Reproduire les données

Le dossier `data/` est exclu de Git par le fichier `.gitignore`.
Il faut exécuter les scripts pour récupérer les différents csv.

1. Demander une clé API
2. Exécuter "download_exportations_pays_mois.py" et "download_importations_pays_mois.py"
/!\ Cela prend du temps car on récupère un par un tous les mois de janvier 2010 à décembre 2025. (2x192 mois)
3. Exécuter "construction_dataset_importations.py" et "construction_dataset_exportations.py"
4. Exécuter "construction_dataset_commerce_usa_mois.py"
