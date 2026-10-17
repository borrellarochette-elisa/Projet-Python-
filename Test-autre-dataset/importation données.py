"""Collecte Census HS2. Test par défaut ; ajouter --complet pour toute la base.
Installer : python -m pip install pandas requests matplotlib
Lancer : python importer_commerce_hs2.py
Collecte complète : python importer_commerce_hs2.py --complet
Les données restent dans le dossier contenant ce script.
"""
import argparse
parser = argparse.ArgumentParser(description="Télécharger les données commerciales HS2")
parser.add_argument('--complet', action='store_true', help='Télécharger 2015–2019 pour les 11 ensembles')
args = parser.parse_args()

def display(tableau):
    print(tableau.to_string())

from pathlib import Path
from getpass import getpass
from datetime import datetime, timezone
import json
import time
import pandas as pd
import requests
import matplotlib.pyplot as plt
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'data' / 'raw' / 'hs2'
PROCESSED = ROOT / 'data' / 'processed'
RAW.mkdir(parents=True, exist_ok=True)
PROCESSED.mkdir(parents=True, exist_ok=True)
print('Dossier de travail :', ROOT)
API_KEY = getpass('Colle ta clé Census puis appuie sur Entrée : ').strip()
if not API_KEY:
    raise ValueError('La clé est vide. Relance cette cellule.')

PAYS = {'Chine': '5700', 'Mexique': '2010', 'Vietnam': '5520',
        'Canada': '1220', 'Japon': '5880', 'Allemagne': '4280',
        'Coree_du_Sud': '5800', 'Inde': '5330', 'Taiwan': '5830',
        'France': '4279', 'Monde': None}
MESURES = {
    'imports': ['GEN_VAL_MO', 'CON_VAL_MO', 'CAL_DUT_MO'],
    'exports': ['ALL_VAL_MO'],
}
session = requests.Session()
session.mount('https://', HTTPAdapter(max_retries=Retry(
    total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504]
)))

def telecharger(flux, pays, annee):
    produit = 'I_COMMODITY' if flux == 'imports' else 'E_COMMODITY'
    description = produit + '_LDESC'
    fichier = RAW / f'{flux}_{pays.lower()}_{annee}.json'
    if fichier.exists():
        archive = json.loads(fichier.read_text(encoding='utf-8'))
        contenu = archive['data']
    else:
        url = f'https://api.census.gov/data/timeseries/intltrade/{flux}/hs'
        params = {
            'get': ','.join([produit, description] + MESURES[flux]),
            'COMM_LVL': 'HS2',
            'time': f'from {annee}-01 to {annee}-12',
        }
        if PAYS[pays] is not None:
            params['CTY_CODE'] = PAYS[pays]
        try:
            reponse = session.get(url, params={**params, 'key': API_KEY}, timeout=90)
        except requests.RequestException:
            raise RuntimeError('Connexion impossible. Réessaie plus tard.') from None
        if reponse.status_code != 200:
            raise RuntimeError(
                f'Erreur HTTP {reponse.status_code} pour {flux}, {pays}, {annee}. '
                'Vérifie la clé et les paramètres. Ne partage pas une URL contenant ta clé.'
            )
        try:
            contenu = reponse.json()
        except ValueError:
            raise RuntimeError('Réponse non JSON : vérifie que la clé est activée.') from None
        archive = {'source': url, 'parametres': params,
                   'extraction_utc': datetime.now(timezone.utc).isoformat(),
                   'data': contenu}
        time.sleep(0.3)
    if not isinstance(contenu, list) or len(contenu) < 2:
        raise ValueError(f'Réponse vide ou inattendue : {flux}, {pays}, {annee}')
    df = pd.DataFrame(contenu[1:], columns=contenu[0])
    attendus = {f'{annee}-{mois:02d}' for mois in range(1, 13)}
    if 'time' not in df or set(df['time']) != attendus:
        raise ValueError(f'Les 12 mois sont attendus : {flux}, {pays}, {annee}. Arrêt pour vérification.')
    if not df[produit].astype(str).str.fullmatch(r'[0-9]{2}').all():
        raise ValueError('La réponse contient un niveau autre que HS2.')
    if df.duplicated(['time', produit]).any():
        raise ValueError('Doublons mois-produit : vérifier les agrégations de la requête.')
    for colonne in MESURES[flux]:
        df[colonne] = pd.to_numeric(df[colonne].replace('', None), errors='raise')
        if (df[colonne] < 0).any():
            raise ValueError(f'Valeur négative dans {colonne}. Arrêt pour vérification.')
    if not fichier.exists():
        fichier.write_text(json.dumps(archive, ensure_ascii=False, indent=2), encoding='utf-8')
    df['pays'] = pays
    df = df.rename(columns={produit: 'hs2', description: f'libelle_{flux}'})
    return df[['time', 'pays', 'hs2', f'libelle_{flux}'] + MESURES[flux]]

# Test des importations et des exportations
for flux in MESURES:
    test = telecharger(flux, 'Chine', 2015)
    print(flux, ':', len(test), 'lignes,', test['hs2'].nunique(),
          'catégories,', test['time'].nunique(), 'mois')
    display(test.head())

if not args.complet:
    print("Test terminé. Si les deux flux couvrent 12 mois, lance la commande avec --complet.")
else:

    tables = {'imports': [], 'exports': []}
    for flux in tables:
        for pays in PAYS:
            for annee in range(2015, 2020):
                tables[flux].append(telecharger(flux, pays, annee))
            print(flux, pays, ': terminé')

    imports = pd.concat(tables['imports'], ignore_index=True)
    exports = pd.concat(tables['exports'], ignore_index=True)
    print('Importations :', len(imports), 'lignes ; exportations :', len(exports), 'lignes')

    df = imports.merge(exports, on=['time', 'pays', 'hs2'], how='outer',
                       validate='one_to_one', indicator='presence_flux')
    df = df.rename(columns={
        'time': 'date', 'GEN_VAL_MO': 'importations_usd',
        'CON_VAL_MO': 'importations_consommation_usd',
        'CAL_DUT_MO': 'droits_calcules_usd', 'ALL_VAL_MO': 'exportations_usd',
    })
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m')
    df['presence_flux'] = df['presence_flux'].astype('string').replace({
        'both': 'deux_flux', 'left_only': 'imports_seuls', 'right_only': 'exports_seuls'
    })
    df['chapitre_special'] = df['hs2'].isin(['98', '99'])
    df['solde_commercial_usd'] = (
        df['exportations_usd'] - df['importations_usd']
    ).where(~df['chapitre_special'])
    denominateur = df['importations_consommation_usd'].where(
        df['importations_consommation_usd'] > 0
    )
    df['taux_effectif_pct'] = 100 * df['droits_calcules_usd'] / denominateur
    df = df.sort_values(['pays', 'date', 'hs2']).reset_index(drop=True)

    assert not df.duplicated(['date', 'pays', 'hs2']).any(), 'Doublons détectés.'
    assert set(df['pays']) == set(PAYS), 'Un partenaire manque.'
    assert df.groupby('pays')['date'].nunique().eq(60).all(), '60 mois attendus par partenaire.'
    assert df['hs2'].str.fullmatch(r'[0-9]{2}').all(), 'Codes HS2 incorrects.'
    couverture = df.groupby('pays').agg(
        lignes=('hs2', 'size'), categories=('hs2', 'nunique'), mois=('date', 'nunique')
    )
    couverture['combinaisons_absentes_des_deux_flux'] = 60 * df['hs2'].nunique() - couverture['lignes']
    print('Nombre réel de lignes :', len(df), '(66 000 était un ordre de grandeur)')
    display(couverture)
    display(df['presence_flux'].value_counts())
    display(df.isna().sum().rename('valeurs_manquantes'))
    display(df.head())

    sortie = PROCESSED / 'commerce_usa_hs2_2015_2019.csv'
    df.to_csv(sortie, index=False, date_format='%Y-%m-%d')
    couverture.to_csv(PROCESSED / 'couverture_hs2.csv')
    df.loc[df['presence_flux'].ne('deux_flux')].to_csv(
        PROCESSED / 'observations_flux_incomplets_hs2.csv', index=False
    )
    print('Fichier enregistré :', sortie)
    print('Taille :', round(sortie.stat().st_size / 1024 / 1024, 2), 'Mo')
