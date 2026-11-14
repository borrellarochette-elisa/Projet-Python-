from pathlib import Path

import numpy as np
import pandas as pd
import wbgapi as wb
import time
from tqdm import tqdm   

#--------------------------------------------------------
# Importation des données banque mondiale
#--------------------------------------------------------

# Liste des variables complémentaires
indicateurs = {
    "NY.GDP.MKTP.CD": "pib_usd",                          # PIB (USD courants)
    "TX.VAL.MRCH.CD.WT": "exportations_pays_usd",         # Exportations de marchandises du pays (USD)
    "TM.VAL.MRCH.CD.WT": "importations_pays_usd",         # Importations de marchandises du pays (USD)
    "SP.POP.TOTL": "population",
    "FP.CPI.TOTL.ZG": "inflation",                        # Inflation (%)
    "NY.GDP.PCAP.PP.KD": "pib_hab_ppa",                   # PIB/hab en PPA ($ internationaux constants 2021)
    "BN.CAB.XOKA.GD.ZS": "solde_courant_pct_pib",         # Solde du compte courant (% du PIB)
    "AG.SRF.TOTL.K2": "superficie_km2",                   # Superficie (km²)
}

# Téléchargement 
wb.per_page = 5000

def telecharger(code, essais=3, pause=10):
    """Télécharge un indicateur. En cas d'erreur du serveur, réessaie jusqu'à 3 fois."""
    for essai in range(1, essais + 1):
        try:
            return wb.data.DataFrame(
                code,
                economy="all",
                time=range(2010, 2026),
                skipAggs=True,
                columns="series",
                numericTimeKeys=True,
            )
        except Exception as erreur:
            tqdm.write(f"   {code} : essai {essai}/{essais} raté ({erreur.__class__.__name__}), "
                       f"nouvel essai dans {pause} s...")
            time.sleep(pause)
    raise RuntimeError(f"Impossible de télécharger {code} après {essais} essais")

morceaux = []
barre = tqdm(indicateurs.items(), total=len(indicateurs), desc="Banque mondiale", unit="indicateur")
debut_total = time.time()

# On importe 1 par 1 chaque indicateur via la fonction telecharger 

for code, nom in barre:
    barre.set_postfix_str(nom)      # affiche l'indicateur en cours à droite de la barre
    morceaux.append(telecharger(code).rename(columns={code: nom}))

# On fusionne en un df unique 

df_wb = pd.concat(morceaux, axis=1).reset_index()
df_wb = df_wb.rename(columns={"economy": "ISO3", "time": "annee"})
print(f"Banque mondiale terminée en {time.time() - debut_total:.0f} s : {df_wb.shape[0]} lignes")

# ------------------------------------------------------------
# Calcul de la distance à Washington par les données du CEPII
# ------------------------------------------------------------

# Lecture du fichier Stata directement depuis le site du CEPII
dist = pd.read_stata("https://www.cepii.fr/distance/dist_cepii.dta")

# On garde les paires "USA -> pays partenaire"
dist_usa = dist.loc[
    dist["iso_o"] == "USA",
    ["iso_d", "distw", "dist", "distcap", "contig", "comlang_off", "colony"],
].rename(columns={"iso_d": "ISO3", "distw": "distance_usa_km"})

# Le CEPII utilise d'anciens codes pays 
correspondances = {
    "ROM": "ROU",   # Roumanie
    "ZAR": "COD",   # RD Congo (ex-Zaïre)
    "TMP": "TLS",   # Timor oriental
    "PAL": "PSE",   # Palestine
    "YUG": "SRB",   # ex-Yougoslavie -> Serbie
}
dist_usa["ISO3"] = dist_usa["ISO3"].replace(correspondances)

# Fusion : les variables CEPII ne changent pas dans le temps,
df_wb = df_wb.merge(dist_usa, on="ISO3", how="left")

# Vérification : pays de la Banque mondiale sans distance CEPII (codes pays différents ?)
print(df_wb.loc[df_wb["distance_usa_km"].isna(), "ISO3"].unique())

# ------------------------------------------------------------
# Sauvegarde 
# ------------------------------------------------------------

dossier = Path(__file__).resolve().parent      
df_wb.to_csv(dossier / "banque_mondiale_2010_2025.csv", index=False)