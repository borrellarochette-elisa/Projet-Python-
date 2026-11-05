# Importation des packages 

import pandas as pd
import plotly.express as px # Package utilisé pour les cartes 
import pycountry # Packages utilisé pour encodé le noms des pays pour les cartes     

# Importation du dataset commerce_usa_2010_2025.csv

df = pd.read_csv(r'C:\Users\leona\Projet-python - ENSAE\Projet-Python-\Importation des données (Elisa)\data\commerce_usa_2010_2025.csv', sep = ',')

# Création de la variable droits_douane en %

df['douane_en_%'] = (df['droits_douane']/ df['importations_generales'])*100

print(df['douane_en_%'].head(50))

# Encodage des noms des pays pour les cartes

def trouver_iso3(nom):
    if pd.isna(nom):
        return None

    try:
        pays = pycountry.countries.lookup(nom.strip())
        return pays.alpha_3

    except LookupError:
        return None

df["ISO3"] = df["CTY_NAME"].map(trouver_iso3) # colonne de noms des pays encodés en ISO3
