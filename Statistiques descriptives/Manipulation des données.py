print('Hello')
from pathlib import Path
import pandas as pd

# 1. Définition du chemin vers le dossier de ton projet
# On pointe directement vers le sous-dossier data où se trouve ton fichier consolidé
dossier_projet = Path(
    "/home/onyxia/work/Projet-Python-/Importation des données (Elisa)"
)
chemin_fichier = dossier_projet / "data" / "commerce_usa_2010_2025.csv"

# Si ton script est placé directement dans le dossier "Importation des données (Elisa)",
# tu peux aussi utiliser un chemin relatif direct :
# chemin_fichier = Path("data/commerce_usa_2010_2025.csv")

# 2. Chargement des données dans Pandas
df = pd.read_csv(chemin_fichier)

# 3. Vérification du chargement
print("--- Dataset chargé avec succès ! ---")
print(f"Dimensions : {df.shape[0]} lignes et {df.shape[1]} colonnes")
print("\nAperçu des 5 premières lignes :")
print(df.head())

# 1. Création de la colonne de pourcentage (par rapport aux importations générales)
df['douane_pourcentage'] = (df['droits_douane'] / df['importations_generales']) * 100

# 2. Remplacer les éventuelles divisions par zéro (NaN ou inf) par 0 si besoin
df['douane_pourcentage'] = df['douane_pourcentage'].fillna(0)

# 3. Afficher un aperçu pour vérifier le calcul
print(df[['CTY_NAME', 'time', 'importations_generales', 'droits_douane', 'douane_pourcentage']].head())

# Afficher les lignes où les droits de douane sont strictement supérieurs à 0
print(
    df[df['droits_douane'] > 0][
        ['CTY_NAME', 'time', 'importations_generales', 'droits_douane', 'douane_pourcentage']
    ].head(10)
)

# Voir la valeur maximale des droits de douane dans tout le dataset
print("\nValeur max des droits de douane :", df['droits_douane'].max())

