#Création du dataset final

from pathlib import Path
import pandas as pd

dossier_data = Path(__file__).resolve().parent / "data"

imports = pd.read_csv(dossier_data / "importations_usa_2010_2025.csv", dtype = {"CTY_CODE":str})
exports = pd.read_csv(dossier_data / "exportations_usa_2010_2025.csv", dtype = {"CTY_CODE":str})


# On s'assure qu'il n'y a pas de doublons
doublons_imports = imports.duplicated(subset=["CTY_CODE", "time"])
doublons_exports = exports.duplicated(subset=["CTY_CODE", "time"])
print("Doublons dans les importations :", doublons_imports.sum())
print("Doublons dans les exportations :", doublons_exports.sum())

# On joint les colonnes
commerce_usa = imports.merge(exports, on = ["CTY_CODE", "time"], how="outer", suffixes=("_imports", "_exports"), validate="one_to_one", indicator=True)

valeurs = commerce_usa["_merge"].value_counts()
#print(valeurs)
print("Nombre de couples (pays, mois) qui existent dans le tableau imports et dans le tableau exports :" ,valeurs["both"])
print("Nombre de couples (pays, mois) qui existent seulement dans les importations :" ,valeurs["left_only"])
print("Nombre de couples (pays, mois) qui existent seulement dans les exportations :" ,valeurs["right_only"])

print("Les colonnes de commerce_usa sont : ", commerce_usa.columns)
print(commerce_usa.head())

# On crée une seule colonne CTY_NAME
commerce_usa["CTY_NAME"] = commerce_usa["CTY_NAME_imports"].combine_first(commerce_usa["CTY_NAME_exports"])    

print(commerce_usa.head())
print("Les colonnes de commerce_usa sont : ", commerce_usa.columns)


# On observe que certaines lignes sont sans nom de pays 
print("Noms de pays manquants :", commerce_usa["CTY_NAME"].isna().sum())

sans_nom = commerce_usa[commerce_usa["CTY_NAME"].isna()]
print(sans_nom[["CTY_CODE","CTY_NAME", "time"]])
print("Le code 8220 correspond au payx non identifiés dans le dataset.")

commerce_usa.loc[commerce_usa["CTY_CODE"] == "8220", "CTY_NAME"] = "Pays non identifiés"     # On ajoute la catégorie des pays non identifié
print("On ajoute la catégorie des pays non identifiés dans le dataset")


# On supprime les colonnes en trop
print("Les colonnes de commerce_usa sont : ", commerce_usa.columns)
commerce_usa = commerce_usa.drop(["CTY_NAME_imports", "CTY_NAME_exports", "_merge"], axis= 1)

# On place la colonne CTY_NAME en seconde position et time en 3eme position pour faciliter la lecture
cols = list(commerce_usa.columns)
cols.remove("CTY_NAME")
cols.remove("time")
cols.insert(1, "CTY_NAME")
cols.insert(2, "time")
commerce_usa = commerce_usa[cols]

# On change le nom des variables pour faciliter la lecture
commerce_usa = commerce_usa.rename(columns={"GEN_VAL_MO" : "importations_generales", "CON_VAL_MO" : "importations_consommation", "CAL_DUT_MO" : "droits_douane", "ALL_VAL_MO" : "exportations"})
print("Les colonnes de commerce_usa sont : ", commerce_usa.columns)

# On enregistre le dataset final en csv
commerce_usa.to_csv( dossier_data / "commerce_usa_2010_2025.csv", index = False)
