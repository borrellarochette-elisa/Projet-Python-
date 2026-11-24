# Importation des packages 

import pandas as pd
import numpy as np
from pathlib import Path
import plotly.express as px # Package utilisé pour les cartes 
import pycountry # Packages utilisé pour encodé le noms des pays pour les cartes     
import statsmodels.formula.api as smf
from scipy import stats
from scipy.spatial.distance import cdist

# Importation du dataset commerce_usa_2010_2025.csv depuis le stockage partagé (comme dans le notebook)

url = "https://minio.lab.sspcloud.fr/elisaborrel/diffusion/commerce_usa/commerce_usa_2010_2025.csv"
df = pd.read_csv(url, dtype={"CTY_CODE": str})

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
    .groupby(["CTY_NAME", "ISO3"], as_index=False)[["douane_en_%", "importations_generales"]]
    .mean()
    .rename(columns={"douane_en_%": "douane_moy_avant", "importations_generales": "importations_generales_avant"})
)

# Moyenne des droits de douane après 04-2025
apres = (
    df[(df["time"] >= "2025-04")]
    .groupby(["CTY_NAME", "ISO3"], as_index=False)[["douane_en_%", "importations_generales"]]
    .mean()
    .rename(columns={"douane_en_%": "douane_moy_apres", "importations_generales": "importations_generales_apres"})
)

# Création du df pour le DiD
df_DiD = avant.merge(apres, on=["CTY_NAME", "ISO3"], how="outer")

# Séparation en groupe control et groupe traité 
df_DiD["traite"] = (df_DiD["douane_moy_apres"] - df_DiD["douane_moy_avant"] > 8).astype(int)

df_DiD["var_importations_generales"] = ((df_DiD["importations_generales_apres"] - df_DiD["importations_generales_avant"])/df_DiD["importations_generales_avant"])*100

# On flitre pour enlever les petits pays avec qui exportent <1M/mois au USA
df_DiD_filtered = df_DiD[df_DiD["importations_generales_avant"] > 1000000]
effet_causal_DiD = df_DiD_filtered[df_DiD_filtered["traite"] == 1]["var_importations_generales"].mean() - df_DiD_filtered[df_DiD_filtered["traite"] == 0]["var_importations_generales"].mean()

# Test sur de comparaison de moyenne 
traites = df_DiD_filtered.loc[df_DiD_filtered["traite"] == 1, "var_importations_generales"].dropna()
temoins = df_DiD_filtered.loc[df_DiD_filtered["traite"] == 0, "var_importations_generales"].dropna()
test = stats.ttest_ind(traites, temoins, equal_var=False)    # equal_var=False = test de Welch

print(f"l'effet causal mesuré par le DiD simple est de {effet_causal_DiD}")
print(f"t = {test.statistic:.2f}, p-value = {test.pvalue:.3f}")

# ------------------------------------------------
# DiD avec contrôle
# ------------------------------------------------

# on ajoute les contrôles et on définit les valeurs en log
controles = df_wb.loc[df_wb["annee"] == 2024, ["ISO3", "pib_usd", "pib_hab_ppa", "distance_usa_km", "inflation", "superficie_km2"]]
df_DiD_control = df_DiD_filtered.merge(controles, on="ISO3", how="left", validate="m:1")
df_DiD_control["log_pib"] = np.log(df_DiD_control["pib_usd"])
df_DiD_control["log_pib_hab"] = np.log(df_DiD_control["pib_hab_ppa"])
df_DiD_control["log_distance"] = np.log(df_DiD_control["distance_usa_km"])

# On passe au format long 
df_long = pd.concat(
    [
        df_DiD_control.assign(post=0, importations_generales=df_DiD_control["importations_generales_avant"]),
        df_DiD_control.assign(post=1, importations_generales=df_DiD_control["importations_generales_apres"]),
    ],
    ignore_index=True,
)
df_long["log_import"] = np.log(df_long["importations_generales"])

# On définit le set de variable pour l'OLS
variables = ["log_import", "traite", "post", "ISO3", "log_pib", "log_pib_hab", "log_distance", "inflation", "superficie_km2"]
reg = df_long.dropna(subset=variables)

# On applique l'OLS 
did_controles = smf.ols(
    "log_import ~ traite * post + (log_pib + log_pib_hab + log_distance + inflation + superficie_km2) * post",
    data=reg,
).fit(cov_type="cluster", cov_kwds={"groups" : reg["ISO3"]})
print(did_controles.summary())

# Vérifications sur l'échantillon du DiD
pays = set(df_DiD_filtered["ISO3"])
pib = df_wb[df_wb["annee"] == 2024].dropna(subset=["pib_usd"]).sort_values("pib_usd", ascending=False)
dans_ech = pib["ISO3"].isin(pays)

print("\n" + "-" * 80)
print("VÉRIFICATIONS SUR L'ÉCHANTILLON DU DiD")
print("-" * 80)

print(f"{len(pays)} pays, dont {df_DiD_filtered['traite'].sum()} traités")
print(f"Part dans le top 170 du PIB : {len(pays & set(pib['ISO3'].head(170))) / len(pays):.0%}")
print(f"PIB médian : {pib.loc[dans_ech, 'pib_usd'].median() / 1e9:.1f} Md$ dans l'échantillon, "
      f"{pib.loc[~dans_ech, 'pib_usd'].median() / 1e9:.1f} Md$ hors échantillon")

# Pays perdus avec les contrôles
perdus = df_DiD_filtered[~df_DiD_filtered["ISO3"].isin(reg["ISO3"])]
print(f"Perdus : {perdus['traite'].sum()} traités, {(perdus['traite'] == 0).sum()} témoins, "
      f"{perdus['importations_generales_avant'].sum() / df_DiD_filtered['importations_generales_avant'].sum():.1%} des importations")

print(
    "\n" + "-" * 80 + "\n"
    "Sur les partenaires exportant au moins 1 M$/mois d'importations_generales US avant avril 2025, "
    "l'effet du DiD n'est pas significatif :\n"
    f"  - sans contrôle  : effet = {effet_causal_DiD:.2f}, p-value = {test.pvalue:.3f}\n"
    f"  - avec contrôles : coef = {did_controles.params['traite:post']:.3f}, p-value = {did_controles.pvalues['traite:post']:.3f}\n"
    "Finalement on observe pas d'effet significatif des droits de douane sur les importations_generales\n"
    + "-" * 80
)