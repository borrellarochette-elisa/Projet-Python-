# On crée un csv contenant les données sur les exportations de janvier 2010 à décembre 2025 
from pathlib import Path    # bibliothèque qui permet de manipuler les chemins de fichier
import pandas as pd


# On vérifie que les 192 mois sont bien importés
dossier_data = Path(__file__).resolve().parent / "data"

periodes = pd.period_range(start="2010-01", end="2025-12", freq="M").astype(str).tolist()

missing = []

for periode in periodes:
    file = dossier_data / f"exports_{periode}.csv"

    if not file.exists():
        missing.append(periode)

print("Mois manquants :", missing)

if len(missing) != 0:
    raise SystemExit("Arrêt du programme car des mois sont manquants")


# On réunit nos données dans un seul dataset
all_tables = []

for periode in periodes:                                # On crée un tableau de tableau avec les données de chaque mois
    file = dossier_data / f"exports_{periode}.csv"
    table = pd.read_csv(file, dtype={"CTY_CODE" : str})
    all_tables.append(table)

print(len(all_tables))

exportations_usa = pd.concat(all_tables, ignore_index = True)     # Concaténation dans un seul grand tableau
print(exportations_usa.shape)

# Enregistrement sous CSV du dataset complet 
file = dossier_data / "exportations_usa_2010_2025.csv"
exportations_usa.to_csv(file, index=False)