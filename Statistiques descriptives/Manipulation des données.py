import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# 1 & 2. Chargement des données directement depuis le stockage cloud (MinIO)
url = "https://minio.lab.sspcloud.fr/elisaborrel/diffusion/commerce_usa/commerce_usa_2010_2025.csv"
commerce_usa = pd.read_csv(url, dtype={"CTY_CODE": str})
df = commerce_usa.copy()

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

# 6bis. Taux non nuls
df_avec_douanes = df[df['douane_pourcentage'] > 0]
print(f"\nNombre de lignes avec un taux de douane non nul : {len(df_avec_douanes)} sur {len(df)} total")

print("\n" + "=" * 65)
print("STATISTIQUES DESCRIPTIVES : douane_pourcentage (Taux > 0 %)")
print("=" * 65)
print(df_avec_douanes['douane_pourcentage'].describe().round(4))

# 6bis'. Taux non nuls et <= 200 %
df_filtre = df[(df['douane_pourcentage'] > 0) & (df['douane_pourcentage'] <= 200)]
print(f"Nombre de lignes après nettoyage des anomalies : {len(df_filtre)} sur {len(df)}")
print("\n" + "=" * 65)
print("STATISTIQUES DESCRIPTIVES : douane_pourcentage (Taux entre 0% et 200%)")
print("=" * 65)
print(df_filtre['douane_pourcentage'].describe().round(4))

# 7. Analyse des anomalies (taux strictement supérieur à 200 %)
anomalies = df[df['douane_pourcentage'] > 200].sort_values(
    by='douane_pourcentage', ascending=False
)

print("\n" + "=" * 65)
print(f"ANOMALIES DÉTECTÉES (Taux > 200 %) : {len(anomalies)} lignes au total")
print("=" * 65)
print(
    anomalies[
        ['CTY_NAME', 'time', 'importations_generales', 'droits_douane', 'douane_pourcentage']
    ].head(20).to_string()
)

# 8. Evolution temporelle des droits de douane
df['time'] = pd.to_datetime(df['time'])
df_temp = df[df['douane_pourcentage'] <= 200].groupby('time')['douane_pourcentage'].mean().reset_index()

plt.figure(figsize=(12, 6))
sns.lineplot(data=df_temp, x='time', y='douane_pourcentage', color='b', linewidth=2)
plt.title("Évolution mensuelle du taux de douane moyen (2010-2025)")
plt.xlabel("Année")
plt.ylabel("Taux de douane moyen (%)")
plt.grid(True, linestyle='--', alpha=0.6)
plt.savefig("evolution_douanes.png", dpi=300, bbox_inches="tight")
print("Graphique sauvegardé avec succès sous 'evolution_douanes.png' !")

# 9. Top 10 (en ignorant les anomalies > 200 %)
totaux_pays = df[df['douane_pourcentage'] <= 200].groupby('CTY_NAME')[['droits_douane', 'importations_generales']].sum()
totaux_pays['taux_global'] = (totaux_pays['droits_douane'] / totaux_pays['importations_generales']) * 100

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

# 10. Evolution moyenne des droits de douane : comparaison dans le temps
df['time_dt'] = pd.to_datetime(df['time'])
df['annee'] = df['time_dt'].dt.year

df_propre = df[(df['douane_pourcentage'] > 0) & (df['douane_pourcentage'] <= 200)].copy()

periode_historique = df_propre[df_propre['annee'] < 2025]
periode_recente = df_propre[df_propre['annee'] >= 2025]

print("=" * 65)
print("COMPARAISON DES TAUX DE DOUANE MOYENS ENTRE LES PÉRIODES")
print("=" * 65)
print(f"Moyenne (2010 - 2024) : {periode_historique['douane_pourcentage'].mean():.2f} %")
print(f"Moyenne récente (2025 - 2026) : {periode_recente['douane_pourcentage'].mean():.2f} %")

def calcul_top_periode(sous_df, nom_periode):
    totaux = sous_df.groupby('CTY_NAME')[['droits_douane', 'importations_generales']].sum()
    totaux['taux'] = (totaux['droits_douane'] / totaux['importations_generales']) * 100
    top = totaux['taux'].sort_values(ascending=False).head(5)
    print(f"\n--- Top 5 des pays ({nom_periode}) ---")
    for pays, taux in top.items():
        print(f"• {pays} : {taux:.2f} %")

calcul_top_periode(periode_historique, "2010-2024")
calcul_top_periode(periode_recente, "2025-2026")

# 11. Test statistique
série_historique = periode_historique['douane_pourcentage']
série_recente = periode_recente['douane_pourcentage']

t_stat, p_value = stats.ttest_ind(série_historique, série_recente, equal_var=False)

print("=" * 65)
print("TEST STATISTIQUE DE COMPARAISON DES MOYENNES (BALANCE CHECK)")
print("=" * 65)
print(f"Moyenne 2010-2024 : {série_historique.mean():.2f} %")
print(f"Moyenne 2025-2026 : {série_recente.mean():.2f} %")
print(f"Statistique t     : {t_stat:.4f}")
print(f"P-value           : {p_value:.4e}")

if p_value < 0.001:
    print("\n Résultat : La différence est TRES SIGNIFICATIVE (p < 0.001).")
else:
    print(f"\n Résultat : P-value = {p_value}")