# Importation des packages 

import pandas as pd
from pathlib import Path
import plotly.express as px # Package utilisé pour les cartes 
import pycountry # Packages utilisé pour encodé le noms des pays pour les cartes     

# Importation du dataset commerce_usa_2010_2025.csv

df = pd.read_csv(r'Importation des données (Elisa)\data\commerce_usa_2010_2025.csv', sep = ',')

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

#--------------------------------------------------------------------
#  Carte dynamique représentant l'évolution des exportations en %.
#--------------------------------------------------------------------

# Création de la variable : variation des exportations par rapport à la moyenne
# roulante des exportations sur les 12 derniers mois  
df["exports_moy_12m"] = (
    df.groupby("CTY_NAME")["exportations"]
    .transform(lambda s: s.shift(1).rolling(12).mean())
)

df["delta_exports_roulant"] = (df["exportations"] - df["exports_moy_12m"]) / df["exports_moy_12m"] * 100

df_anim = df.sort_values("time")
fig = px.choropleth(
    df_anim,
    locations="ISO3",
    color="delta_exports_roulant",
    hover_name="CTY_NAME",
    animation_frame="time",                
    color_continuous_scale=["darkred", "white", "darkgreen"],
    range_color=(-20, 20),
    projection="natural earth",
    title="Exportations vers les États-Unis"
)

fig.show()
fig.write_html("Statistiques descriptives/Cartes/carte_dynamique_exportations.html") 

#--------------------------------------------------------------------
#  Carte dynamique représentant l'évolution des exportations après avril 2025.
#--------------------------------------------------------------------

ref_mars = df[df["time"] == "2025-03"].set_index("CTY_NAME")["exportations"]

# On ne garde que les mois à partir d'avril 2025
df_avril = df[df["time"] >= "2025-03"].copy()
reference = df_avril["CTY_NAME"].map(ref_mars)      
df_avril["delta_exports_from_april"] = ((df_avril["exportations"] - reference) / reference * 100)

df_anim = df_avril.dropna(subset=["ISO3", "delta_exports_from_april"]).sort_values("time")
fig = px.choropleth(
    df_anim,
    locations="ISO3",
    color="delta_exports_from_april",
    hover_name="CTY_NAME",
    animation_frame="time",
    color_continuous_scale=["darkred", "white", "darkgreen"],
    range_color=(-40, 40),
    projection="natural earth",
    title="Exportations des États-Unis vers chaque pays (variation par rapport à Mars 2025, %)",
)

fig.show()
fig.write_html("Statistiques descriptives/Cartes/carte_dynamique_exportations_from_april_2025.html") 