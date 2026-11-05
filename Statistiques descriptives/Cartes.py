import pandas as pd
df = pd.read_csv(r'C:\Users\leona\Projet-python - ENSAE\Projet-Python-\Importation des données (Elisa)\data\commerce_usa_2010_2025.csv', sep = ',')

df['douane_en_%'] = (df['droits_douane']/ df['importations_generales'])*100

print(df['douane_en_%'].head(50))
