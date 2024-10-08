import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import niceplots, scipy, time, os
import argparse
from mpl_toolkits import mplot3d
from matplotlib import cm
import shutil, random

"""
This time I'll try a Gaussian Process model to fit the axial critical load surrogate model
Inputs: D*, a0/b0, ln(b/h)
Output: k_x0
"""

np.random.seed(1234567)

# parse the arguments
parent_parser = argparse.ArgumentParser(add_help=False)
parent_parser.add_argument("--plotraw", type=bool, default=False)
parent_parser.add_argument("--plotmodel", type=bool, default=False)
parent_parser.add_argument("--kernel", type=int, default=2)

args = parent_parser.parse_args()

# load the stiffener crippling dataset
df = pd.read_csv("data/stiffener_crippling.csv")

# extract only the model columns
X = df[["x0", "x1", "x2", "x3"]].to_numpy()
Y = df["y"].to_numpy()
Y = np.reshape(Y, newshape=(Y.shape[0], 1))

N_data = X.shape[0]

# n_train = int(0.9 * N_data)
n_train = 2000  # 1000, 4000
n_test = min([4000, N_data - n_train])


def relu(x):
    return max([0.0, x])


def soft_relu(x, rho=10):
    return 1.0 / rho * np.log(1 + np.exp(rho * x))


sigma_n = 1e-1  # 1e-1 was old value

# this one was a pretty good model except for high geneps, middle rho0 for one region of the design
kernel_option = args.kernel  # best is 7 right now
if kernel_option == 1:
    # this one works great with the xi dimension and doesn't have any funky d/dgeneps slopes becoming negative
    # at higher xi values

    def kernel(xp, xq, theta):
        # xp, xq are Nx1,Mx1 vectors (ln(xi), ln(rho_0), ln(1 + 10^3 * zeta), ln(1 + geneps))
        vec = xp - xq

        d1 = vec[1]  # first two entries
        d2 = vec[2]
        d3 = vec[3]

        # log(xi) direction
        kernel0 = 1.0 + xp[0] * xq[0]
        # log(rho_0) direction
        kernel1_1 = soft_relu(2.0 - xp[1]) * soft_relu(2.0 - xq[1]) + 0.1
        kernel1_2 = (
            0.02  # * np.exp(-0.5 * (xp[3] + xq[3]) / 1.0) # 0.2
            # * np.exp(-0.5 * (d1 ** 2 / (0.2 ** 2))
            * np.exp(-0.5 * (d1 ** 2 / 2.0 ** 2))
            * soft_relu(3.0 - xp[1])
            * soft_relu(xp[1])
            * soft_relu(3.0 - xq[1])
            * soft_relu(xq[1])
        )
        # log(gen eps) direction
        #  kernel2 = xp[2] * xq[2] + 0.1 * np.exp(-0.5 * d2 ** 2 / 9.0)
        kernel2 = 1.0 + 0.5 * xp[2] * xq[2] + 0.1 * np.exp(-0.5 * d2 ** 2 / 9.0)
        # log(zeta) direction
        kernel3 = (1.0 + 0.2 * xp[3] * xq[3]) ** 2 + 0.1 * np.exp(-0.5 * d3 ** 2 / 9.0)
        return (kernel1_1 + kernel1_2) * kernel0 * kernel2 * kernel3

elif kernel_option == 2:
    # this one works great with the xi dimension and doesn't have any funky d/dgeneps slopes becoming negative
    # at higher xi values

    def kernel(xp, xq, theta):
        # xp, xq are Nx1,Mx1 vectors (ln(xi), ln(rho_0), ln(1 + 10^3 * zeta), ln(1 + geneps))
        vec = xp - xq

        d1 = vec[1]  # first two entries
        d2 = vec[2]
        d3 = vec[3]

        # log(xi) direction
        kernel0 = 1.0 + xp[0] * xq[0]
        # log(rho_0) direction
        kernel1 = (
            1.0 + 0.2 * soft_relu(2.0 - xp[1]) * soft_relu(2.0 - xq[1])
        ) ** 2 + 0.2 * np.exp(-0.5 * d1 ** 2 / 0.5 ** 2)
        # log(gen eps) direction
        #  kernel2 = xp[2] * xq[2] + 0.1 * np.exp(-0.5 * d2 ** 2 / 9.0)
        kernel2 = 0.2 + 0.5 * xp[2] * xq[2] + 0.5 * np.exp(-0.5 * d2 ** 2 / 0.2 ** 2)
        # log(zeta) direction
        # kernel3 = (1.0 + 0.2 * xp[3] * xq[3])**2 + 0.1 * np.exp(-0.5 * d3 ** 2 / 1.0)
        kernel3 = (0.2 + 0.1 * xp[3] * xq[3]) + 0.5 * np.exp(-0.5 * d3 ** 2 / 0.5 ** 2)
        return kernel1 + kernel0 + kernel2 + kernel3
        # return kernel0 * kernel1 * kernel2 * kernel3

elif kernel_option == 3:
    # this one works great with the xi dimension and doesn't have any funky d/dgeneps slopes becoming negative
    # at higher xi values

    def kernel(xp, xq, theta):
        # xp, xq are Nx1,Mx1 vectors (ln(xi), ln(rho_0), ln(1 + 10^3 * zeta), ln(1 + geneps))
        vec = xp - xq

        d1 = vec[1]  # first two entries
        d2 = vec[2]
        d3 = vec[3]

        # log(xi) direction
        kernel0 = 1.0 + xp[0] * xq[0]
        # log(rho_0) direction
        kernel1 = (
            soft_relu(3.0 - xp[1])
            * soft_relu(3.0 - xq[1])
            * (1.0 + np.exp(-0.5 * d1 ** 2 / 0.5 ** 2))
        )
        # geneps direction
        #  kernel2 = xp[2] * xq[2] + 0.1 * np.exp(-0.5 * d2 ** 2 / 9.0)
        kernel2 = np.exp(-0.5 * d2 ** 2 / 1.0)
        # log(zeta) direction
        kernel3 = np.exp(-0.5 * d3 ** 2 / 1.0)
        return kernel1 * kernel0 * kernel2 * kernel3

elif kernel_option == 4:
    # this one works great with the xi dimension and doesn't have any funky d/dgeneps slopes becoming negative
    # at higher xi values

    def kernel(xp, xq, theta):
        # xp, xq are Nx1,Mx1 vectors (ln(xi), ln(rho_0), ln(1 + 10^3 * zeta), ln(1 + geneps))
        vec = xp - xq

        d1 = vec[1]  # first two entries
        d2 = vec[2]
        d3 = vec[3]

        # log(xi) direction
        kernel0 = 1.0 + xp[0] * xq[0]
        # log(rho_0) direction
        bilinear_factor = soft_relu(2.0 - xp[1]) * soft_relu(2.0 - xq[1])
        kernel1 = (1.0 + 0.2 * bilinear_factor) ** 2 + 0.2 * np.exp(
            -0.5 * d1 ** 2 / 0.5 ** 2
        ) * bilinear_factor
        # log(gen eps) direction
        #  kernel2 = xp[2] * xq[2] + 0.1 * np.exp(-0.5 * d2 ** 2 / 9.0)
        kernel2 = 1.0 + np.exp(-0.5 * d2 ** 2 / 1.0)
        # log(zeta) direction
        kernel3 = 1.0 + np.exp(-0.5 * d3 ** 2 / 1.0)
        return kernel1 + kernel0 + kernel2 + kernel3
        # return kernel0 * kernel1 * kernel2 * kernel3


print(f"Monte Carlo #data training {n_train} / {X.shape[0]} data points")

# print bounds of the data
xi = X[:, 0]
print(f"\txi or x0: min {np.min(xi)}, max {np.max(xi)}")
rho0 = X[:, 1]
print(f"\trho0 or x1: min {np.min(rho0)}, max {np.max(rho0)}")
gen_eps = X[:, 2]
print(f"\tgen_eps or x2: min {np.min(gen_eps)}, max {np.max(gen_eps)}")
zeta = X[:, 3]
print(f"\tzeta or x3: min {np.min(zeta)}, max {np.max(zeta)}")

# bins for the data (in log space)
xi_bins = [[0.2, 0.4], [0.4, 0.6], [0.6, 0.8], [0.8, 1.0]]
rho0_bins = [[-2.5, -1.0], [-1.0, 0.0], [0.0, 1.0], [1.0, 2.5]]
geneps_bins = [[0.15, 0.2], [0.2, 0.25], [0.25, 0.3]]
zeta_bins = [[0.0, 0.1], [0.1, 0.5], [0.5, 1.0], [1.0, 2.0]]

# randomly permute the arrays
rand_perm = np.random.permutation(N_data)
X = X[rand_perm, :]
Y = Y[rand_perm, :]

# 2d plots
_plot_geneps = True
_plot_zeta = True
_plot_xi = True
_plot_xi2 = True
# 3d plots
_plot_3d = True

# make a folder for the model fitting
plots_folder = os.path.join(os.getcwd(), "plots")
GP_folder = os.path.join(plots_folder, "GP")
for ifolder, folder in enumerate(
    [
        # plots_folder,
        # sub_plots_folder,
        GP_folder,
    ]
):
    if ifolder > 0 and os.path.exists(folder):
        shutil.rmtree(folder)
    if not os.path.exists(folder):
        os.mkdir(folder)

plt.style.use(niceplots.get_style())

n_data = X.shape[0]

# split into training and test datasets
n_total = X.shape[0]
assert n_test > 100

# reorder the data
indices = [_ for _ in range(n_total)]
train_indices = np.random.choice(indices, size=n_train)
test_indices = [_ for _ in range(n_total) if not (_ in train_indices)]

X_train = X[train_indices, :]
X_test = X[test_indices[:n_test], :]
Y_train = Y[train_indices, :]
Y_test = Y[test_indices[:n_test], :]

# y is the training set observations
y = Y_train


# plot the model and some of the data near the model range in D*=1, AR from 0.5 to 5.0, b/h=100
# ---------------------------------------------------------------------------------------------

if args.plotraw:
    print(f"start plot")
    # get the available colors
    prop_cycle = plt.rcParams["axes.prop_cycle"]
    colors = prop_cycle.by_key()["color"]

    plt.style.use(niceplots.get_style())

    if _plot_geneps:

        print(f"start 2d geneps plots...")

        for ixi, xi_bin in enumerate(xi_bins):
            xi_mask = np.logical_and(xi_bin[0] <= X[:, 0], X[:, 0] <= xi_bin[1])
            avg_xi = 0.5 * (xi_bin[0] + xi_bin[1])

            for izeta, zeta_bin in enumerate(zeta_bins):
                zeta_mask = np.logical_and(
                    zeta_bin[0] <= X[:, 3], X[:, 3] <= zeta_bin[1]
                )
                avg_zeta = 0.5 * (zeta_bin[0] + zeta_bin[1])
                xi_zeta_mask = np.logical_and(xi_mask, zeta_mask)

                if np.sum(xi_zeta_mask) == 0:
                    continue

                plt.figure(f"xi = {avg_xi:.2f}, zeta = {avg_zeta:.2f}", figsize=(8, 6))

                colors = plt.cm.jet(np.linspace(0.0, 1.0, len(geneps_bins)))

                for igeneps, geneps_bin in enumerate(geneps_bins[::-1]):

                    geneps_mask = np.logical_and(
                        geneps_bin[0] <= X[:, 2], X[:, 2] <= geneps_bin[1]
                    )
                    mask = np.logical_and(xi_zeta_mask, geneps_mask)

                    if np.sum(mask) == 0:
                        continue

                    X_in_range = X[mask, :]
                    Y_in_range = Y[mask, :]

                    plt.plot(
                        X_in_range[:, 1],
                        Y_in_range[:, 0],
                        "o",
                        color=colors[igeneps],
                        zorder=1 + igeneps,
                        label=f"geneps in [{geneps_bin[0]:.0f},{geneps_bin[1]:.0f}]",
                    )

                plt.legend()
                plt.xlabel(r"$\log{\rho_0}$")
                plt.ylabel(r"$N_{cr}^*$")

                plt.savefig(
                    os.path.join(GP_folder, f"2d-geneps_xi{ixi}_zeta{izeta}.png"),
                    dpi=400,
                )
                plt.close(f"xi = {avg_xi:.2f}, zeta = {avg_zeta:.2f}")

    if _plot_zeta:

        print(f"start 2d zeta plots...")

        for ixi, xi_bin in enumerate(xi_bins):
            xi_mask = np.logical_and(xi_bin[0] <= X[:, 0], X[:, 0] <= xi_bin[1])
            avg_xi = 0.5 * (xi_bin[0] + xi_bin[1])

            for igeneps, geneps_bin in enumerate(geneps_bins[::-1]):
                geneps_mask = np.logical_and(
                    geneps_bin[0] <= X[:, 2], X[:, 2] <= geneps_bin[1]
                )
                avg_geneps = 0.5 * (geneps_bin[0] + geneps_bin[1])
                xi_geneps_mask = np.logical_and(xi_mask, geneps_mask)

                for izeta, zeta_bin in enumerate(zeta_bins):
                    zeta_mask = np.logical_and(
                        zeta_bin[0] <= X[:, 3], X[:, 3] <= zeta_bin[1]
                    )
                    avg_zeta = 0.5 * (zeta_bin[0] + zeta_bin[1])
                    mask = np.logical_and(xi_geneps_mask, zeta_mask)

                    if np.sum(mask) == 0:
                        continue

                    plt.figure(
                        f"xi = {avg_xi:.2f}, geneps = {avg_geneps:.2f}", figsize=(8, 6)
                    )

                    colors = plt.cm.jet(np.linspace(0.0, 1.0, len(zeta_bins)))

                    if np.sum(mask) == 0:
                        continue

                    X_in_range = X[mask, :]
                    Y_in_range = Y[mask, :]

                    plt.plot(
                        X_in_range[:, 1],
                        Y_in_range[:, 0],
                        "o",
                        color=colors[izeta],
                        zorder=1 + izeta,
                        label=f"Lzeta in [{zeta_bin[0]:.0f},{zeta_bin[1]:.0f}]",
                    )

                plt.legend()
                plt.xlabel(r"$\log{\rho_0}$")
                plt.ylabel(r"$N_{cr}^*$")

                plt.savefig(
                    os.path.join(GP_folder, f"2d-zeta_xi{ixi}_geneps{igeneps}.png"),
                    dpi=400,
                )
                plt.close(f"xi = {avg_xi:.2f}, geneps = {avg_geneps:.2f}")

    if _plot_xi:

        print(f"start 2d zeta plots...")

        for igeneps, geneps_bin in enumerate(geneps_bins[::-1]):
            geneps_mask = np.logical_and(
                geneps_bin[0] <= X[:, 2], X[:, 2] <= geneps_bin[1]
            )
            avg_geneps = 0.5 * (geneps_bin[0] + geneps_bin[1])

            for izeta, zeta_bin in enumerate(zeta_bins):
                zeta_mask = np.logical_and(
                    zeta_bin[0] <= X[:, 3], X[:, 3] <= zeta_bin[1]
                )
                avg_zeta = 0.5 * (zeta_bin[0] + zeta_bin[1])
                geneps_zeta_mask = np.logical_and(geneps_mask, zeta_mask)

                for ixi, xi_bin in enumerate(xi_bins):
                    xi_mask = np.logical_and(xi_bin[0] <= X[:, 0], X[:, 0] <= xi_bin[1])
                    avg_xi = 0.5 * (xi_bin[0] + xi_bin[1])
                    mask = np.logical_and(geneps_zeta_mask, xi_mask)

                    if np.sum(mask) == 0:
                        continue

                    plt.figure(
                        f"zeta = {avg_zeta:.2f}, geneps = {avg_geneps:.2f}",
                        figsize=(8, 6),
                    )

                    colors = plt.cm.jet(np.linspace(0.0, 1.0, len(xi_bins)))

                    if np.sum(mask) == 0:
                        continue

                    X_in_range = X[mask, :]
                    Y_in_range = Y[mask, :]

                    plt.plot(
                        X_in_range[:, 1],
                        Y_in_range[:, 0],
                        "o",
                        color=colors[ixi],
                        zorder=1 + ixi,
                        label=f"Lxi in [{xi_bin[0]:.1f},{xi_bin[1]:.1f}]",
                    )

                plt.legend()
                plt.xlabel(r"$\log{\rho_0}$")
                plt.ylabel(r"$N_{cr}^*$")

                plt.savefig(
                    os.path.join(GP_folder, f"2d-xi_zeta{izeta}_geneps{igeneps}.png"),
                    dpi=400,
                )
                plt.close(f"zeta = {avg_zeta:.2f}, geneps = {avg_geneps:.2f}")

    if _plot_xi2:

        print(f"start 2d xi2 plots...")

        for izeta, zeta_bin in enumerate(zeta_bins):
            zeta_mask = np.logical_and(zeta_bin[0] <= X[:, 3], X[:, 3] <= zeta_bin[1])
            avg_zeta = 0.5 * (zeta_bin[0] + zeta_bin[1])

            for ixi, xi_bin in enumerate(xi_bins):
                xi_mask = np.logical_and(xi_bin[0] <= X[:, 0], X[:, 0] <= xi_bin[1])
                avg_xi = 0.5 * (xi_bin[0] + xi_bin[1])
                mask = np.logical_and(zeta_mask, xi_mask)

                if np.sum(mask) == 0:
                    continue

                plt.figure(f"zeta = {avg_zeta:.2f}", figsize=(8, 6))

                colors = plt.cm.jet(np.linspace(0.0, 1.0, len(xi_bins)))

                if np.sum(mask) == 0:
                    continue

                X_in_range = X[mask, :]
                Y_in_range = Y[mask, :]

                plt.plot(
                    X_in_range[:, 1],
                    Y_in_range[:, 0],
                    "o",
                    color=colors[ixi],
                    zorder=1 + ixi,
                    label=f"Lxi in [{xi_bin[0]:.1f},{xi_bin[1]:.1f}]",
                )

            plt.legend()
            plt.xlabel(r"$\log{\rho_0}$")
            plt.ylabel(r"$N_{cr}^*$")

            plt.savefig(os.path.join(GP_folder, f"2d-xi2_zeta{izeta}.png"), dpi=400)
            plt.close(f"zeta = {avg_zeta:.2f}")

# exit()
theta0 = []

# compute the training kernel matrix
K_y = np.array(
    [
        [kernel(X_train[i, :], X_train[j, :], theta0) for i in range(n_train)]
        for j in range(n_train)
    ]
) + sigma_n ** 2 * np.eye(n_train)

# print(f"K_y = {K_y}")
# exit()

alpha = np.linalg.solve(K_y, y)

if args.plotmodel:

    n_plot_2d = 100
    rho0_vec = np.linspace(-2.5, 3.5, n_plot_2d)

    if _plot_geneps:

        print(f"start 2d geneps plots...")

        for ixi, xi_bin in enumerate(xi_bins):
            xi_mask = np.logical_and(xi_bin[0] <= X[:, 0], X[:, 0] <= xi_bin[1])
            avg_xi = 0.5 * (xi_bin[0] + xi_bin[1])

            for izeta, zeta_bin in enumerate(zeta_bins):
                zeta_mask = np.logical_and(
                    zeta_bin[0] <= X[:, 3], X[:, 3] <= zeta_bin[1]
                )
                avg_zeta = 0.5 * (zeta_bin[0] + zeta_bin[1])
                xi_zeta_mask = np.logical_and(xi_mask, zeta_mask)

                plt.figure(f"xi = {avg_xi:.2f}, zeta = {avg_zeta:.2f}", figsize=(8, 6))

                colors = plt.cm.jet(np.linspace(0.0, 1.0, len(geneps_bins)))

                for igeneps, geneps_bin in enumerate(geneps_bins[::-1]):

                    geneps_mask = np.logical_and(
                        geneps_bin[0] <= X[:, 2], X[:, 2] <= geneps_bin[1]
                    )
                    avg_geneps = 0.5 * (geneps_bin[0] + geneps_bin[1])
                    mask = np.logical_and(xi_zeta_mask, geneps_mask)

                    # if np.sum(mask) == 0: continue

                    X_in_range = X[mask, :]
                    Y_in_range = Y[mask, :]

                    if np.sum(mask) != 0:
                        plt.plot(
                            X_in_range[:, 1],
                            Y_in_range[:, 0],
                            "o",
                            color=colors[igeneps],
                            zorder=1 + igeneps,
                            label=f"geneps in [{geneps_bin[0]:.0f},{geneps_bin[1]:.0f}]",
                        )

                    # predict the models, with the same colors, no labels
                    X_plot = np.zeros((n_plot_2d, 4))
                    for irho, crho0 in enumerate(rho0_vec):
                        X_plot[irho, :] = np.array(
                            [avg_xi, crho0, avg_zeta, avg_geneps]
                        )[:]

                    Kplot = np.array(
                        [
                            [
                                kernel(X_train[i, :], X_plot[j, :], theta0)
                                for i in range(n_train)
                            ]
                            for j in range(n_plot_2d)
                        ]
                    )
                    f_plot = Kplot @ alpha

                    plt.plot(rho0_vec, f_plot, "--", color=colors[igeneps], zorder=1)

                plt.legend()
                plt.xlabel(r"$\log{\rho_0}$")
                plt.ylabel(r"$N_{cr}^*$")

                plt.savefig(
                    os.path.join(GP_folder, f"2d-geneps-model_xi{ixi}_zeta{izeta}.png"),
                    dpi=400,
                )
                plt.close(f"xi = {avg_xi:.2f}, zeta = {avg_zeta:.2f}")

    if _plot_zeta:

        print(f"start 2d zeta plots...")

        for ixi, xi_bin in enumerate(xi_bins):
            xi_mask = np.logical_and(xi_bin[0] <= X[:, 0], X[:, 0] <= xi_bin[1])
            avg_xi = 0.5 * (xi_bin[0] + xi_bin[1])

            for igeneps, geneps_bin in enumerate(geneps_bins):
                geneps_mask = np.logical_and(
                    geneps_bin[0] <= X[:, 2], X[:, 2] <= geneps_bin[1]
                )
                avg_geneps = 0.5 * (geneps_bin[0] + geneps_bin[1])
                xi_geneps_mask = np.logical_and(xi_mask, geneps_mask)

                for izeta, zeta_bin in enumerate(zeta_bins):
                    zeta_mask = np.logical_and(
                        zeta_bin[0] <= X[:, 3], X[:, 3] <= zeta_bin[1]
                    )
                    avg_zeta = 0.5 * (zeta_bin[0] + zeta_bin[1])
                    mask = np.logical_and(xi_geneps_mask, zeta_mask)

                    # if np.sum(mask) == 0: continue

                    plt.figure(
                        f"xi = {avg_xi:.2f}, geneps = {avg_geneps:.2f}", figsize=(8, 6)
                    )

                    colors = plt.cm.jet(np.linspace(0.0, 1.0, len(zeta_bins)))

                    # if np.sum(mask) == 0: continue

                    X_in_range = X[mask, :]
                    Y_in_range = Y[mask, :]

                    if np.sum(mask) != 0:
                        plt.plot(
                            X_in_range[:, 1],
                            Y_in_range[:, 0],
                            "o",
                            color=colors[izeta],
                            zorder=1 + izeta,
                            label=f"Lzeta in [{zeta_bin[0]:.0f},{zeta_bin[1]:.0f}]",
                        )

                    # predict the models, with the same colors, no labels
                    X_plot = np.zeros((n_plot_2d, 4))
                    for irho, crho0 in enumerate(rho0_vec):
                        X_plot[irho, :] = np.array(
                            [avg_xi, crho0, avg_zeta, avg_geneps]
                        )[:]

                    Kplot = np.array(
                        [
                            [
                                kernel(X_train[i, :], X_plot[j, :], theta0)
                                for i in range(n_train)
                            ]
                            for j in range(n_plot_2d)
                        ]
                    )
                    f_plot = Kplot @ alpha

                    plt.plot(rho0_vec, f_plot, "--", color=colors[izeta], zorder=1)

                plt.legend()
                plt.xlabel(r"$\log{\rho_0}$")
                plt.ylabel(r"$N_{cr}^*$")

                plt.savefig(
                    os.path.join(
                        GP_folder, f"2d-zeta-model_xi{ixi}_geneps{igeneps}.png"
                    ),
                    dpi=400,
                )
                plt.close(f"xi = {avg_xi:.2f}, geneps = {avg_geneps:.2f}")

    if _plot_xi:

        print(f"start 2d zeta plots...")

        for igeneps, geneps_bin in enumerate(geneps_bins):
            geneps_mask = np.logical_and(
                geneps_bin[0] <= X[:, 2], X[:, 2] <= geneps_bin[1]
            )
            avg_geneps = 0.5 * (geneps_bin[0] + geneps_bin[1])

            for izeta, zeta_bin in enumerate(zeta_bins):
                zeta_mask = np.logical_and(
                    zeta_bin[0] <= X[:, 3], X[:, 3] <= zeta_bin[1]
                )
                avg_zeta = 0.5 * (zeta_bin[0] + zeta_bin[1])
                geneps_zeta_mask = np.logical_and(geneps_mask, zeta_mask)

                for ixi, xi_bin in enumerate(xi_bins):
                    xi_mask = np.logical_and(xi_bin[0] <= X[:, 0], X[:, 0] <= xi_bin[1])
                    avg_xi = 0.5 * (xi_bin[0] + xi_bin[1])
                    mask = np.logical_and(geneps_zeta_mask, xi_mask)

                    # if np.sum(mask) == 0: continue

                    plt.figure(
                        f"zeta = {avg_zeta:.2f}, geneps = {avg_geneps:.2f}",
                        figsize=(8, 6),
                    )

                    colors = plt.cm.jet(np.linspace(0.0, 1.0, len(xi_bins)))

                    # if np.sum(mask) == 0: continue

                    X_in_range = X[mask, :]
                    Y_in_range = Y[mask, :]

                    if np.sum(mask) != 0:
                        plt.plot(
                            X_in_range[:, 1],
                            Y_in_range[:, 0],
                            "o",
                            color=colors[ixi],
                            zorder=1 + ixi,
                            label=f"Lxi in [{xi_bin[0]:.1f},{xi_bin[1]:.1f}]",
                        )

                    # plot the model now
                    # predict the models, with the same colors, no labels
                    X_plot = np.zeros((n_plot_2d, 4))
                    for irho, crho0 in enumerate(rho0_vec):
                        X_plot[irho, :] = np.array(
                            [avg_xi, crho0, avg_zeta, avg_geneps]
                        )[:]

                    Kplot = np.array(
                        [
                            [
                                kernel(X_train[i, :], X_plot[j, :], theta0)
                                for i in range(n_train)
                            ]
                            for j in range(n_plot_2d)
                        ]
                    )
                    f_plot = Kplot @ alpha

                    plt.plot(rho0_vec, f_plot, "--", color=colors[ixi], zorder=1)

                plt.legend()
                plt.xlabel(r"$\log{\rho_0}$")
                plt.ylabel(r"$N_{cr}^*$")

                plt.savefig(
                    os.path.join(
                        GP_folder, f"2d-xi-model_zeta{izeta}_geneps{igeneps}.png"
                    ),
                    dpi=400,
                )
                plt.close(f"zeta = {avg_zeta:.2f}, geneps = {avg_geneps:.2f}")

    if _plot_3d:

        # 3d plot of rho_0, geneps, lam_star for a particular xi and zeta range
        # xi_bin = [-0.5, 0.5]
        # smaller values of xi have higher geneps
        xi_bin = [0.2, 0.4]
        # xi_bin = [-2.0, 2.0]
        xi_mask = np.logical_and(xi_bin[0] <= X[:, 0], X[:, 0] <= xi_bin[1])
        avg_xi = 0.3
        # zeta_bin = [0.0, 8.0]
        zeta_bin = [0, 1]
        # zeta_bin = [0.0, 8.0]
        zeta_mask = np.logical_and(zeta_bin[0] <= X[:, 3], X[:, 3] <= zeta_bin[1])
        avg_zeta = 0.5
        xi_zeta_mask = np.logical_and(xi_mask, zeta_mask)

        plt.figure(f"3d rho_0, geneps, lam_star")
        ax = plt.axes(projection="3d", computed_zorder=False)

        colors = plt.cm.jet(np.linspace(0.0, 1.0, len(geneps_bins)))

        for igeneps, geneps_bin in enumerate(geneps_bins):

            geneps_mask = np.logical_and(
                geneps_bin[0] <= X[:, 2], X[:, 2] <= geneps_bin[1]
            )
            mask = np.logical_and(xi_zeta_mask, geneps_mask)

            X_in_range = X[mask, :]
            Y_in_range = Y[mask, :]

            # print(f"X in range = {X_in_range}")
            # print(f"Y in range = {Y_in_range}")

            ax.scatter(
                X_in_range[:, 3],
                X_in_range[:, 1],
                Y_in_range[:, 0],
                s=20,
                color=colors[igeneps],
                edgecolors="black",
                zorder=2 + igeneps,
            )

        # plot the scatter plot
        n_plot = 3000
        X_plot_mesh = np.zeros((30, 100))
        X_plot = np.zeros((n_plot, 4))
        ct = 0
        geneps_vec = np.linspace(0.0, 4.0, 30)
        AR_vec = np.log(np.linspace(0.1, 10.0, 100))
        for igeneps in range(30):
            for iAR in range(100):
                X_plot[ct, :] = np.array(
                    [avg_xi, AR_vec[iAR], avg_zeta, geneps_vec[igeneps]]
                )
                ct += 1

        Kplot = np.array(
            [
                [kernel(X_train[i, :], X_plot[j, :], theta0) for i in range(n_train)]
                for j in range(n_plot)
            ]
        )
        f_plot = Kplot @ alpha

        # make meshgrid of outputs
        geneps = np.zeros((30, 100))
        AR = np.zeros((30, 100))
        KMIN = np.zeros((30, 100))
        ct = 0
        for igeneps in range(30):
            for iAR in range(100):
                geneps[igeneps, iAR] = geneps_vec[igeneps]
                AR[igeneps, iAR] = AR_vec[iAR]
                KMIN[igeneps, iAR] = f_plot[ct]
                ct += 1

        # plot the model curve
        # Creating plot
        face_colors = cm.jet((KMIN - 0.8) / np.log(10.0))
        ax.plot_surface(
            geneps,
            AR,
            KMIN,
            antialiased=False,
            facecolors=face_colors,
            alpha=0.4,
            zorder=1,
        )

        # save the figure
        ax.set_xlabel(r"$\log(1+\geneps)$")
        ax.set_ylabel(r"$log(\rho_0)$")
        ax.set_zlabel(r"$log(N_{11,cr}^*)$")
        ax.set_ylim3d(np.log(0.1), np.log(10.0))
        # ax.set_zlim3d(0.0, np.log(50.0))
        # ax.set_zlim3d(1.0, 3.0)
        ax.view_init(elev=20, azim=20, roll=0)
        plt.gca().invert_xaxis()
        # plt.title(f"")
        plt.show()
        # plt.savefig(os.path.join(GP_folder, f"geneps-3d.png"), dpi=400)
        plt.close(f"3d rho_0, geneps, lam_star")

# only eval relative error on test set for zeta < 1
# because based on the model plots it appears that the patterns break down some for that
zeta_mask = X_test[:, 2] < 1.0
X_test = X_test[zeta_mask, :]
Y_test = Y_test[zeta_mask, :]
n_test = X_test.shape[0]

# predict and report the relative error on the test dataset
K_test_cross = np.array(
    [
        [kernel(X_train[i, :], X_test[j, :], theta0) for i in range(n_train)]
        for j in range(n_test)
    ]
)
Y_test_pred = K_test_cross @ alpha

crit_loads = np.exp(Y_test)
crit_loads_pred = np.exp(Y_test_pred)

abs_err = crit_loads_pred - crit_loads
rel_err = abs(abs_err / crit_loads)
avg_rel_err = np.mean(rel_err)
if args.plotraw or args.plotmodel:
    print(f"\n\n\n")
print(
    f"\navg rel err from n_train={n_train} on test set of n_test={n_test} = {avg_rel_err}"
)

# print out which data points have the highest relative error as this might help me improve the model
neg_avg_rel_err = -1.0 * rel_err
sort_indices = np.argsort(neg_avg_rel_err[:, 0])
n_worst = 100
hdl = open("axial-model-debug.txt", "w")
# (f"sort indices = {sort_indices}")
for i, sort_ind in enumerate(sort_indices[:n_worst]):  # first 10
    hdl.write(f"sort ind = {type(sort_ind)}\n")
    x_test = X_test[sort_ind, :]
    crit_load = crit_loads[sort_ind, 0]
    crit_load_pred = crit_loads_pred[sort_ind, 0]
    hdl.write(
        f"{sort_ind} - lxi={x_test[0]:.3f}, lrho0={x_test[1]:.3f}, l(1+geneps)={x_test[3]:.3f}, l(1+10^3*zeta)={x_test[2]:.3f}\n"
    )
    xi = np.exp(x_test[0])
    rho0 = np.exp(x_test[1])
    geneps = np.exp(x_test[3]) - 1.0
    zeta = (np.exp(x_test[2]) - 1.0) / 1000.0
    c_rel_err = (crit_load_pred - crit_load) / crit_load
    hdl.write(
        f"\txi = {xi:.3f}, rho0 = {rho0:.3f}, geneps = {geneps:.3f}, zeta = {zeta:.3f}\n"
    )
    hdl.write(f"\tcrit_load = {crit_load:.3f}, crit_load_pred = {crit_load_pred:.3f}\n")
    hdl.write(f"\trel err = {c_rel_err:.3e}\n")
hdl.close()


# archive the data to the format of the
filename = "cripplingGP.csv"
output_csv = "../../archived_models/" + filename
# [log(xi), log(rho0), log(1+geneps), log(1+10^3 * zeta)]
dataframe_dict = {
    "log(xi)": X_train[:, 0],
    "log(rho0)": X_train[:, 1],
    "log(1+geneps)": X_train[:, 2],
    "log(1+10^3*zeta)": X_train[:, 3],
    "alpha": alpha[:, 0],
}
model_df = pd.DataFrame(dataframe_dict)
model_df.to_csv(output_csv)
