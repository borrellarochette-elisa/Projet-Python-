import requests
import pandas as pd

# ============================================================
# PARAMETRES
# ============================================================

API_KEY = "7f8c6c8b349cc9fec3fe5f7af79015cac587e76b"

# Décembre + variable _YR = total cumulé de l'année 2025
DATE = "2025-12"

URL_IMPORTS = (
    "https://api.census.gov/data/timeseries/"
    "intltrade/imports/statehsimport"
)

URL_EXPORTS = (
    "https://api.census.gov/data/timeseries/"
    "intltrade/exports/statehsexport"
)


# ============================================================
# FONCTION POUR APPELER L'API
# ============================================================

def census_request(url, params):
    r = requests.get(url, params=params)
    r.raise_for_status()

    data = r.json()

    return pd.DataFrame(
        data[1:],
        columns=data[0]
    )


# ============================================================
# 1. IMPORTATIONS PAR ETAT ET HS2
# ============================================================

params_imports = {
    "get": (
        "US_STATE,"
        "US_STATE_LABEL,"
        "I_COMMODITY,"
        "I_COMMODITY_LABEL,"
        "GEN_VAL_YR"
    ),
    "for": "world:1",
    "COMM_LVL": "HS2",
    "time": DATE,
    "key": API_KEY
}

imports = census_request(
    URL_IMPORTS,
    params_imports
)

imports["GEN_VAL_YR"] = pd.to_numeric(
    imports["GEN_VAL_YR"]
)


# ============================================================
# 2. EXPORTATIONS PAR ETAT ET HS2
# ============================================================

params_exports = {
    "get": (
        "US_STATE,"
        "US_STATE_LABEL,"
        "E_COMMODITY,"
        "E_COMMODITY_LABEL,"
        "ALL_VAL_YR"
    ),
    "for": "world:1",
    "COMM_LVL": "HS2",
    "time": DATE,
    "key": API_KEY
}

exports = census_request(
    URL_EXPORTS,
    params_exports
)

exports["ALL_VAL_YR"] = pd.to_numeric(
    exports["ALL_VAL_YR"]
)


# ============================================================
# 3. GARDER LES 50 ETATS + DC
# ============================================================

states = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE",
    "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS",
    "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS",
    "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY",
    "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV",
    "WI", "WY", "DC"
}

imports = imports[
    imports["US_STATE"].isin(states)
].copy()

exports = exports[
    exports["US_STATE"].isin(states)
].copy()


# ============================================================
# 4. IMPORTS / EXPORTS TOTAUX PAR ETAT
# ============================================================

imports_totaux = (
    imports.groupby(
        ["US_STATE", "US_STATE_LABEL"],
        as_index=False
    )["GEN_VAL_YR"]
    .sum()
    .rename(
        columns={
            "GEN_VAL_YR": "imports_2025"
        }
    )
)

exports_totaux = (
    exports.groupby(
        ["US_STATE", "US_STATE_LABEL"],
        as_index=False
    )["ALL_VAL_YR"]
    .sum()
    .rename(
        columns={
            "ALL_VAL_YR": "exports_2025"
        }
    )
)

commerce_etats = imports_totaux.merge(
    exports_totaux,
    on=["US_STATE", "US_STATE_LABEL"],
    how="outer"
)


# ============================================================
# 5. GRANDES CATEGORIES DE PRODUITS
# ============================================================

def categorie_hs(hs):
    try:
        h = int(hs)
    except (TypeError, ValueError):
        return "Autres"

    if 1 <= h <= 5:
        return "Animaux et produits animaux"

    elif 6 <= h <= 14:
        return "Produits végétaux"

    elif h == 15:
        return "Huiles et graisses"

    elif 16 <= h <= 24:
        return "Agroalimentaire, boissons et tabac"

    elif 25 <= h <= 27:
        return "Produits minéraux et énergie"

    elif 28 <= h <= 38:
        return "Produits chimiques"

    elif 39 <= h <= 40:
        return "Plastiques et caoutchouc"

    elif 41 <= h <= 43:
        return "Cuirs et peaux"

    elif 44 <= h <= 46:
        return "Bois"

    elif 47 <= h <= 49:
        return "Papier et imprimerie"

    elif 50 <= h <= 63:
        return "Textile"

    elif 64 <= h <= 67:
        return "Chaussures et accessoires"

    elif 68 <= h <= 70:
        return "Pierre, céramique et verre"

    elif h == 71:
        return "Métaux précieux et joaillerie"

    elif 72 <= h <= 83:
        return "Métaux"

    elif 84 <= h <= 85:
        return "Machines et électronique"

    elif 86 <= h <= 89:
        return "Matériel de transport"

    elif 90 <= h <= 92:
        return "Instruments et appareils de précision"

    elif h == 93:
        return "Armes et munitions"

    elif 94 <= h <= 96:
        return "Produits manufacturés divers"

    elif h == 97:
        return "Art et antiquités"

    elif 98 <= h <= 99:
        return "Catégories spéciales"

    return "Autres"


exports["categorie"] = (
    exports["E_COMMODITY"]
    .apply(categorie_hs)
)


# ============================================================
# 6. EXPORTATIONS PAR ETAT ET GRANDE CATEGORIE
# ============================================================

exports_categories = (
    exports.groupby(
        [
            "US_STATE",
            "US_STATE_LABEL",
            "categorie"
        ],
        as_index=False
    )["ALL_VAL_YR"]
    .sum()
    .rename(
        columns={
            "ALL_VAL_YR":
            "exports_2025"
        }
    )
)


# ============================================================
# 7. AFFICHAGE
# ============================================================

print("\n=== COMMERCE TOTAL PAR ETAT ===")
print(
    commerce_etats
    .sort_values(
        "exports_2025",
        ascending=False
    )
    .head(20)
)

print("\n=== EXPORTATIONS PAR CATEGORIE ===")
print(
    exports_categories
    .sort_values(
        "exports_2025",
        ascending=False
    )
    .head(30)
)


# ============================================================
# 8. SAUVEGARDE
# ============================================================

commerce_etats.to_csv(
    "commerce_etats_2025.csv",
    index=False
)

exports_categories.to_csv(
    "exports_categories_etats_2025.csv",
    index=False
)

exports.to_csv(
    "exports_hs2_etats_2025.csv",
    index=False
)