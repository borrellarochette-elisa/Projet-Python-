print('Hello')
from pathlib import Path
import pandas as pd
import numpy as np

# 1. Définition du chemin vers le dossier de ton projet
dossier_projet = Path(
    "/home/onyxia/work/Projet-Python-/Importation des données (Elisa)"
)
chemin_fichier = dossier_projet / "data" / "commerce_usa_2010_2025.csv"

# 2. Chargement des données dans Pandas
df = pd.read_csv(chemin_fichier)

# 3. Vérification du chargement
print("--- Dataset chargé avec succès ! ---")
print(f"Dimensions : {df.shape[0]} lignes et {df.shape[1]} colonnes")
print("\nAperçu des 5 premières lignes :")
print(df.head())


# 4. Création sécurisée de la colonne de pourcentage (anti-division par zéro et anti-inf)
df['douane_pourcentage'] = 0.0
masque = df['importations_generales'] > 0
df.loc[masque, 'douane_pourcentage'] = (
    df.loc[masque, 'droits_douane'] / df.loc[masque, 'importations_generales']
) * 100
df['douane_pourcentage'] = df['douane_pourcentage'].replace([np.inf, -np.inf], 0).fillna(0)

# 5. Aperçus et vérifications
print("\nAperçu avec la colonne douane_pourcentage :")
print(df[['CTY_NAME', 'time', 'importations_generales', 'droits_douane', 'douane_pourcentage']].head())

print("\nNombre de lignes avec des droits de douane strictement supérieurs à 0 :")
print(
    df[df['droits_douane'] > 0][
        ['CTY_NAME', 'time', 'importations_generales', 'droits_douane', 'douane_pourcentage']
    ].shape
)

print("\nValeur max des droits de douane :", df['droits_douane'].max())


# 6. Statistiques descriptives de la nouvelle colonne
print("\n" + "=" * 65)
print("STATISTIQUES DESCRIPTIVES : douane_pourcentage")
print("=" * 65)
print(df['douane_pourcentage'].describe().round(4))

# 6bis. Dans le cas ou le pourcentage de droits de douanes est non nul seulement 
df_avec_douanes = df[df['douane_pourcentage'] > 0]

print(f"\nNombre de lignes avec un taux de douane non nul : {len(df_avec_douanes)} sur {len(df)} total")

print("\n" + "=" * 65)
print("STATISTIQUES DESCRIPTIVES : douane_pourcentage (Taux > 0 %)")
print("=" * 65)
print(df_avec_douanes['douane_pourcentage'].describe().round(4))

# 6bis'. Dans le cas ou le pourcentage de droits de douanes est non nul seulement / enlevant les valeurs aberrantes
df_filtre = df[(df['douane_pourcentage'] > 0) & (df['douane_pourcentage'] <= 100)]
print(f"Nombre de lignes après nettoyage des anomalies : {len(df_filtre)} sur {len(df)}")
print("\n" + "=" * 65)
print("STATISTIQUES DESCRIPTIVES : douane_pourcentage (Taux entre 0% et 100%)")
print("=" * 65)
print(df_filtre['douane_pourcentage'].describe().round(4))


# 7. Analyse des  anomalies (taux strictement supérieur à 100 %)
anomalies = df[df['douane_pourcentage'] > 100].sort_values(
    by='douane_pourcentage', ascending=False
)

print("\n" + "=" * 65)
print(f"ANOMALIES DÉTECTÉES (Taux > 100 %) : {len(anomalies)} lignes au total")
print("=" * 65)

print(
    anomalies[
        ['CTY_NAME', 'time', 'importations_generales', 'droits_douane', 'douane_pourcentage']
    ].head(20).to_string()
)



import matplotlib.pyplot as plt
import seaborn as sns

# 8. Evolution temporelle des droits de douane (convertir la colonne 'time' en format datetime)
df['time'] = pd.to_datetime(df['time'])
df_temp = df[df['douane_pourcentage'] <= 100].groupby('time')['douane_pourcentage'].mean().reset_index()

plt.figure(figsize=(12, 6))
sns.lineplot(data=df_temp, x='time', y='douane_pourcentage', color='b', linewidth=2)
plt.title("Évolution mensuelle du taux de douane moyen (2010-2025)")
plt.xlabel("Année")
plt.ylabel("Taux de douane moyen (%)")
plt.grid(True, linestyle='--', alpha=0.6)
plt.savefig("evolution_douanes.png", dpi=300, bbox_inches="tight")
print("Graphique sauvegardé avec succès sous 'evolution_douanes.png' !")


# 9. Top 10 (en ignorant les anomalies)
totaux_pays = df[df['douane_pourcentage'] <= 100].groupby('CTY_NAME')[['droits_douane', 'importations_generales']].sum()
totaux_pays['taux_global'] = (totaux_pays['droits_douane'] / totaux_pays['importations_generales']) * 100

# On prend le Top 10 et on trie dans l'ordre croissant pour l'affichage horizontal
top_10 = totaux_pays['taux_global'].sort_values(ascending=True).tail(10)

plt.figure(figsize=(10, 6))
top_10.plot(kind='barh', color='#2ca02c', edgecolor='black', alpha=0.85)

plt.title("Top 10 des partenaires par taux de douane global cumulé", fontsize=14, fontweight='bold')
plt.xlabel("Taux de douane effectif global (%)", fontsize=12)
plt.ylabel("Pays partenaire", fontsize=12)
plt.grid(axis='x', linestyle='--', alpha=0.6)
plt.tight_layout()

plt.savefig("top10_taux_douane.png", dpi=300)
plt.close()
print("Graphique 2 sauvegardé : top10_taux_douane.png")