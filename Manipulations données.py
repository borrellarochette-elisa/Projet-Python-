import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tabulate import tabulate
import plotly.express as px

pd.set_option("display.float_format", "{:.2f}".format) #enlever les écritures scientifiques 

data = pd.read_csv('/home/onyxia/work/commerce_etats_2025.csv')
print(data.head())

print(data.describe())

print(
    tabulate(
        data.head(20),
        headers="keys",
        tablefmt="fancy_grid",
        showindex=False
    )
)

# Création de la balance commerciale 
data["balance_commerciale"] = (data["exports_2025"] - data["imports_2025"])

# Création de la palette de couleur
max_abs = data["balance_commerciale"].abs().max()

fig = px.choropleth(
    data,
    locations="US_STATE",
    locationmode="USA-states",
    color="balance_commerciale",
    scope="usa",
    hover_name="US_STATE_LABEL",
    hover_data={
        "US_STATE": True,
        "imports_2025": ":,.0f",
        "exports_2025": ":,.0f",
        "balance_commerciale": ":,.0f"
    },
    color_continuous_scale=[
        (0.0, "red"),
        (0.5, "white"),
        (1.0, "green")
    ],
    range_color=[-max_abs, max_abs],
    title="Balance commerciale des États américains en 2025"
)

fig.update_layout(
    coloraxis_colorbar_title="Balance commerciale",
    margin={"r": 0, "t": 50, "l": 0, "b": 0}
)

fig.show()