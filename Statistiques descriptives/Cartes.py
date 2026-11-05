# Importation des packages 

import pandas as pd
import plotly.express as px # Package utilisé pour les cartes 

# Importation du dataset commerce_usa_2010_2025.csv

df = pd.read_csv(r'C:\Users\leona\Projet-python - ENSAE\Projet-Python-\Importation des données (Elisa)\data\commerce_usa_2010_2025.csv', sep = ',')

# Création de la variable droits_douane en %

df['douane_en_%'] = (df['droits_douane']/ df['importations_generales'])*100

print(df['douane_en_%'].head(50))


