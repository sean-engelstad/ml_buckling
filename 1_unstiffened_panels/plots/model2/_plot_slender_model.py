import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
import ml_buckling as mlb
import niceplots

islender = 2
model_df = pd.read_csv(f"slender{islender}-model-fit_model.csv")
rho_0 = model_df['rho_0'].to_numpy()
mean = model_df['mean'].to_numpy()
# model standard deviation needs to be fixed
std_dev = model_df['std_dev'].to_numpy() * 4

data_df = pd.read_csv(f"slender{islender}-model-fit_data.csv")
AR = data_df['AR'].to_numpy()
lam = data_df['lam'].to_numpy()

plt.style.use(niceplots.get_style())
plt.figure("check model")#, figsize=(8, 6))
plt.margins(x=0.05, y=0.05)
# plt.title(f"b/h in [50,100]")
ax = plt.subplot(111)

# colors = plt.cm.viridis(np.linspace(0, 1, 5))
colors = mlb.four_colors6

ax.fill_between(
    x=rho_0,
    y1=mean - 3 * std_dev,
    y2=mean + 3 * std_dev,
    label='3-sigma',
    color=colors[0]
)
ax.fill_between(
    x=rho_0,
    y1=mean - std_dev,
    y2=mean + std_dev,
    label='1-sigma',
    color=colors[1]
)
ax.plot(
   rho_0, mean, colors[2], label="mean", linewidth=2
)  # , label=f"D*-[{Dstar_bin[0]},{Dstar_bin[1]}]""
ax.plot(
    AR, lam, "o", markersize=3, label="train-data",
    color=colors[3], markeredgecolor=colors[3]
)  # , label=f"D*-[{Dstar_bin[0]},{Dstar_bin[1]}]""

# outside of for loop save the plot
plt.xlabel(r"$\mathbf{\ln(\rho_0)}$", fontsize=18, fontweight='bold')
# plt.xlabel(r"$\log(\rho_0)|\rho_0 = \frac{a}{b} \cdot \sqrt[4]{D_{22}^p/D_{11}^p}$")
plt.ylabel(r"$\mathbf{\ln(N_{11,cr}^*)}$", fontsize=18, fontweight='bold')
plt.legend(prop={'size' : 14})

plt.xticks(fontsize=14, fontweight='bold')
plt.yticks(fontsize=14, fontweight='bold')
# plt.xlim(np.log(0.1), np.log(20.0))
# plt.ylim(np.log(2.0), np.log(20.0))
plt.savefig(f"slender{islender}-model-fit.svg", dpi=400)
plt.savefig(f"slender{islender}-model-fit.png", dpi=400)