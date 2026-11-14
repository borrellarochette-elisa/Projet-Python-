# Importation des packages 

import pandas as pd
import numpy as np
from pathlib import Path
import plotly.express as px # Package utilisé pour les cartes 
import pycountry # Packages utilisé pour encodé le noms des pays pour les cartes     
import statsmodels.formula.api as smf
from scipy import stats
from scipy.spatial.distance import cdist

# Importation du dataset commerce_usa_2010_2025.csv

df = pd.read_csv(r'Importation des données (Elisa)\data\commerce_usa_2010_2025.csv', sep = ',')

# Création de la variable droits_douane en %

df['douane_en_%'] = (df['droits_douane']/ df['importations_generales'])*100

print(df['douane_en_%'].head(50))

# Encodage des noms des pays en ISO3

def trouver_iso3(nom):
    if pd.isna(nom):
        return None

    try:
        pays = pycountry.countries.lookup(nom.strip())
        return pays.alpha_3

    except LookupError:
        return None

df["ISO3"] = df["CTY_NAME"].map(trouver_iso3) # colonne de noms des pays encodés en ISO3

# ------------------------------------------------
#  Merge data set avec les données complémentaires
# ------------------------------------------------

df_wb = pd.read_csv(r'Données complémentaire\banque_mondiale_2010_2025.csv')

df["annee"] = df["time"].str[:4].astype(int)            # "2025-04" -> 2025
df_merge = df.merge(df_wb, on=["ISO3", "annee"], how="left", validate="m:1")

# ------------------------------------------------
# DiD classique 
# ------------------------------------------------

# Créer deux groupes
df["douane_en_%"] = df["douane_en_%"].replace([np.inf, -np.inf], np.nan) # Nettoyage data

# Moyenne des droits de douane sur l'année avant  04-2025
avant = (
    df[(df["time"] >= "2024-04") & (df["time"] < "2025-04")]
    .groupby(["CTY_NAME", "ISO3"], as_index=False)[["douane_en_%", "exportations"]]
    .mean()
    .rename(columns={"douane_en_%": "douane_moy_avant", "exportations": "exportations_avant"})
)

# Moyenne des droits de douane après 04-2025
apres = (
    df[(df["time"] >= "2025-04")]
    .groupby(["CTY_NAME", "ISO3"], as_index=False)[["douane_en_%", "exportations"]]
    .mean()
    .rename(columns={"douane_en_%": "douane_moy_apres", "exportations": "exportations_apres"})
)

# Création du df pour le DiD
df_DiD = avant.merge(apres, on=["CTY_NAME", "ISO3"], how="outer")

# Séparation en groupe control et groupe traité 
df_DiD["traite"] = (df_DiD["douane_moy_apres"] - df_DiD["douane_moy_avant"] > 8).astype(int)

df_DiD["var_exportations"] = ((df_DiD["exportations_apres"] - df_DiD["exportations_avant"])/df_DiD["exportations_avant"])*100

# On flitre pour enlever les petits pays avec qui exportent exportent <1M/mois au USA
df_DiD_filtered = df_DiD[df_DiD["exportations_avant"] > 1000000]
effet_causal_DiD = df_DiD_filtered[df_DiD_filtered["traite"] == 1]["var_exportations"].mean() - df_DiD_filtered[df_DiD_filtered["traite"] == 0]["var_exportations"].mean()

# Test sur de comparaison de moyenne 
traites = df_DiD_filtered.loc[df_DiD_filtered["traite"] == 1, "var_exportations"].dropna()
temoins = df_DiD_filtered.loc[df_DiD_filtered["traite"] == 0, "var_exportations"].dropna()
test = stats.ttest_ind(traites, temoins, equal_var=False)    # equal_var=False = test de Welch

print(f"l'effet causal mesuré par le DiD simple est de {effet_causal_DiD}")
print(f"t = {test.statistic:.2f}, p-value = {test.pvalue:.3f}")

# ------------------------------------------------
# DiD avec contrôle
# ------------------------------------------------

# on ajoute les contrôles et on définit les valeurs en log
controles = df_wb.loc[df_wb["annee"] == 2024, ["ISO3", "pib_usd", "pib_hab_ppa", "distance_usa_km", "inflation"]]
df_DiD_control = df_DiD_filtered.merge(controles, on="ISO3", how="left", validate="m:1")
df_DiD_control["log_pib"] = np.log(df_DiD_control["pib_usd"])
df_DiD_control["log_pib_hab"] = np.log(df_DiD_control["pib_hab_ppa"])
df_DiD_control["log_distance"] = np.log(df_DiD_control["distance_usa_km"])

# On passe au format long 
df_long = pd.concat(
    [
        df_DiD_control.assign(post=0, exportations=df_DiD_control["exportations_avant"]),
        df_DiD_control.assign(post=1, exportations=df_DiD_control["exportations_apres"]),
    ],
    ignore_index=True,
)
df_long["log_export"] = np.log(df_long["exportations"])

# On définit le set de variable pour l'OLS
variables = ["log_export", "traite", "post", "ISO3", "log_pib", "log_pib_hab", "log_distance", "inflation"]
reg = df_long.dropna(subset=variables)

# On applique l'OLS 
did_controles = smf.ols(
    "log_export ~ traite * post + (log_pib + log_pib_hab + log_distance + inflation) * post",
    data=reg,
).fit(cov_type="cluster", cov_kwds={"groups" : reg["ISO3"]})
print(did_controles.summary())

print(
    "\n" + "-" * 80 + "\n"
    "Sur les partenaires recevant au moins 1 M$/mois d'exportations US avant avril 2025, "
    "l'effet du DiD n'est pas significatif et change même de sens avec les contrôles :\n"
    f"  - sans contrôle  : effet = {effet_causal_DiD:.2f}, p-value = {test.pvalue:.3f}\n"
    f"  - avec contrôles : coef = {did_controles.params['traite:post']:.3f}, p-value = {did_controles.pvalues['traite:post']:.3f}\n"
    "Finalement on observe un effet significatif des droits de douane sur les exportations\n"
    + "-" * 80
)