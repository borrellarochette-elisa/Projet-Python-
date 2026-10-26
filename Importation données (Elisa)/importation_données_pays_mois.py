import requests     # package pour demander les données au site Census
import pandas as pd
from pathlib import Path

cle_api = input("Coller la clé Census puis appuyer sur Entrée :").strip()
url_imports = "https://api.census.gov/data/timeseries/intltrade/imports/hs"


# importation des données pour janvier 2010 (vérification no erreur)
periode = "2010-01"

parametres = {            # paramètres du dictionnaire indiqué sur le site Census
    "time": periode,
    "key": cle_api,
    "get": "CTY_CODE,CTY_NAME,GEN_VAL_MO,CON_VAL_MO,CAL_DUT_MO",     # importation des colonnes
    "SUMMARY_LVL": "DET"     # importation des pays individuellement
    }

reponse = requests.get(url_imports, params=parametres)
print(reponse.status_code)      # si sortie 200, signifie que le serveur a répondu avec succès
data = reponse.json()

dataset = pd.DataFrame(data[1:], columns=data[0])      # construction du tableau
dataset = dataset[dataset["CTY_CODE"] != "-"].copy()     # on enlève la ligne correspondant au total de tous les pays
dataset = dataset.drop(columns=["SUMMARY_LVL"])      # on enlève la colonne SUMMARY_LVL qui contient toujours DET (filtre pour avoir tous les pays)
# print(dataset[["CTY_CODE", "CTY_NAME"]].to_string(index=False))     # afficher tous les partenaires des USA

# On transforme les colonnes contenant des montants en nombres 
dataset["GEN_VAL_MO"] = pd.to_numeric(dataset["GEN_VAL_MO"])
dataset["CON_VAL_MO"] = pd.to_numeric(dataset["CON_VAL_MO"])
dataset["CAL_DUT_MO"] = pd.to_numeric(dataset["CAL_DUT_MO"])
print(dataset.dtypes)

print(dataset.head())

# Enregistrement sous CSV
dossier_data = Path(__file__).resolve().parent / "data"
dossier_data.mkdir(exist_ok=True)     # création d'un dossier data

fichier = dossier_data / f"imports_{periode}.csv" 
dataset.to_csv(fichier, index=False)


# importation des données de février 2010 à décembre 2025
periodes = pd.period_range(start="2010-02", end="2025-12", freq="M").astype(str).tolist()     # lister les mois

for periode in periodes:
    parametres = {
        "time": periode,
        "key": cle_api,
        "get": "CTY_CODE,CTY_NAME,GEN_VAL_MO,CON_VAL_MO,CAL_DUT_MO",     # importation des colonnes
        "SUMMARY_LVL": "DET"
        }

    reponse = requests.get(url_imports, params=parametres)
    data = reponse.json()

    dataset = pd.DataFrame(data[1:], columns=data[0])      # construction du tableau
    dataset = dataset[dataset["CTY_CODE"] != "-"].copy()     # on enlève la ligne correspondant au total de tous les pays
    dataset = dataset.drop(columns=["SUMMARY_LVL"])      # on enlève la colonne SUMMARY_LVL qui contient toujours DET (filtre pour avoir tous les pays)

    # On transforme les colonnes contenant des montants en nombres 
    dataset["GEN_VAL_MO"] = pd.to_numeric(dataset["GEN_VAL_MO"])
    dataset["CON_VAL_MO"] = pd.to_numeric(dataset["CON_VAL_MO"])
    dataset["CAL_DUT_MO"] = pd.to_numeric(dataset["CAL_DUT_MO"])

    # Enregistrement sous CSV
    fichier = dossier_data / f"imports_{periode}.csv" 
    dataset.to_csv(fichier, index=False)

print("Importation réussie")

