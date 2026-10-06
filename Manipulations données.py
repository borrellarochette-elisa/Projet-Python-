import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

pd.set_option("display.float_format", "{:.2f}".format) #enlever les écritures scientifiques 

data = pd.read_csv('/home/onyxia/work/commerce_etats_2025.csv')
print(data.head())

print(data.describe())
