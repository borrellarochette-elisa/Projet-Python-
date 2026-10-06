import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tabulate import tabulate

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
