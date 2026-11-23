# Importation des packages 

import pandas as pd
import numpy as np
from pathlib import Path
import plotly.express as px # Package utilisé pour les cartes      
import country_converter as coco # Packages utilisé pour encodé le noms des pays pour les cartes
import logging

# Importation du dataset commerce_usa_2010_2025.csv depuis le stockage partagé (comme dans le notebook)

url = "https://minio.lab.sspcloud.fr/elisaborrel/diffusion/commerce_usa/commerce_usa_2010_2025.csv"
df = pd.read_csv(url, dtype={"CTY_CODE": str})

# Création de la variable droits_douane en %

df['douane_en_%'] = 0.0
masque = df['importations_generales'] > 0
df.loc[masque, 'douane_en_%'] = (
    df.loc[masque, 'droits_douane'] / df.loc[masque, 'importations_generales']
) * 100
df['douane_en_%'] = df['douane_en_%'].replace([np.inf, -np.inf], 0).fillna(0)

# Encodage des noms des pays pour les cartes

logging.getLogger("country_converter.country_converter").setLevel(logging.ERROR) # Supprime les alertes
cc = coco.CountryConverter()

codes_iso3 = {}
for nom in df["CTY_NAME"].dropna().unique():
    code = cc.convert(names=nom, to="ISO3")
    
    if isinstance(code, list) or code == "not found":
        print(f"{nom} not found in regex")
        code = pd.NA

    codes_iso3[nom] = (code)

df["ISO3"] = df["CTY_NAME"].map(codes_iso3) # colonne de noms des pays encodés en ISO3

pays_en_echec = df.loc[
    df["ISO3"].isna(), "CTY_NAME"
]
print(pays_en_echec.value_counts(dropna=False))

corrections = {
    "WEST BANK ADMINISTERED BY ISRAEL": "PSE",
    "GAZA STRIP ADMINISTERED BY ISRAEL": "PSE",
    "NAOERO": "NRU",
    "NETHERLANDS ANTILLES": "ANT",
}

df["ISO3"] = df["CTY_NAME"].map(corrections).fillna(df["ISO3"])

#--------------------------------------------------------------------
#  Carte statique représentant les droits de douane sur l'année 2025. 
#--------------------------------------------------------------------

# Création d'un df pour l'année 2025 et des droits de douane en % associé
df_2025 = df[df["time"].str.startswith("2025")]
df_2025 = (df_2025.groupby(["CTY_NAME", "ISO3"], as_index = False))[["droits_douane", "importations_consommation"]].sum()
df_2025["douane_en_%"] = (df_2025["droits_douane"] / df_2025["importations_consommation"])*100

# Création de la carte pour 2025 

fig = px.choropleth(
    df_2025,
    locations="ISO3",                      # la clé : le code pays
    color="douane_en_%",                   # la valeur qui donne la couleur
    hover_name="CTY_NAME",                 # le nom affiché au survol
    color_continuous_scale="Reds",
    range_color=(0, 20),                   # 0 % = clair, 20 % et plus = rouge foncé
    projection="natural earth",
    title="Droits de douane effectifs des États-Unis – 2025",
)
fig.write_image("Statistiques descriptives/Cartes/carte_droits_douane_2025.png")        

#--------------------------------------------------------------------
#  Carte dynamique représentant l'évolution des droits de douane.
#--------------------------------------------------------------------

df_anim = df.sort_values("time")
fig = px.choropleth(
    df_anim,
    locations="ISO3",
    color="douane_en_%",
    hover_name="CTY_NAME",
    animation_frame="time",                
    color_continuous_scale="Reds",
    range_color=(0, 20),
    projection="natural earth",
    title="Droits de douane effectifs des États-Unis",
)

fig.write_html("Statistiques descriptives/Cartes/carte_dynamique_douanes.html")        
fig.show()
#--------------------------------------------------------------------
#  Carte dynamique représentant l'évolution des importations_generales en %.
#--------------------------------------------------------------------

# Création de la variable : variation des importations_generales par rapport à la moyenne
# roulante des importations_generales sur les 12 derniers mois  
df["imports_moy_12m"] = (
    df.groupby("CTY_NAME")["importations_generales"]
    .transform(lambda s: s.shift(1).rolling(12).mean())
)

df["delta_imports_roulant"] = (df["importations_generales"] - df["imports_moy_12m"]) / df["imports_moy_12m"] * 100

df_anim = df.sort_values("time")
fig = px.choropleth(
    df_anim,
    locations="ISO3",
    color="delta_imports_roulant",
    hover_name="CTY_NAME",
    animation_frame="time",                
    color_continuous_scale=["darkred", "white", "darkgreen"],
    range_color=(-20, 20),
    projection="natural earth",
    title="importations_generales vers les États-Unis"
)

fig.show()
fig.write_html("Statistiques descriptives/Cartes/carte_dynamique_importations_generales.html") 

#--------------------------------------------------------------------
#  Carte dynamique représentant l'évolution des importations_generales 
#  par rapport au même mois de 2024.
#--------------------------------------------------------------------

df["date"] = pd.to_datetime(df["time"])
df["annee"] = df["date"].dt.year
df["mois"] = df["date"].dt.month

# Référence : le même mois en 2024
ref_2024 = (
    df[df["annee"] == 2024][["CTY_NAME", "mois", "importations_generales"]]
    .rename(columns={"importations_generales": "imports_2024"})
)

df_2025 = df[df["annee"] == 2025].merge(ref_2024, on=["CTY_NAME", "mois"], how="left")
df_2025["var_vs_2024"] = (df_2025["importations_generales"] / df_2025["imports_2024"] - 1) * 100

df_anim = df_2025.dropna(subset=["ISO3", "var_vs_2024"]).sort_values("date")

fig = px.choropleth(
    df_anim,
    locations="ISO3",
    color="var_vs_2024",
    hover_name="CTY_NAME",
    animation_frame="time",
    color_continuous_scale=["darkred", "white", "darkgreen"],
    range_color=(-40, 40),
    projection="natural earth",
    title="Importations des États-Unis (variation par rapport au même mois de 2024, %)",
)
fig.show()
fig.write_html("Statistiques descriptives/Cartes/carte_dynamique_importations_generales_variation.html") 