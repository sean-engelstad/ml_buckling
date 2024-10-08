import numpy as np
import ml_buckling as mlb
import matplotlib.pyplot as plt
import niceplots, pandas, os
from mpi4py import MPI

comm = MPI.COMM_WORLD

ct = 0
flat_plates = []
# first solve uniaxial SS then shear SS and do modal comparison

nx = 30
ny = 30

# axial plate
# --------------------------------------------------
axial_plate = mlb.UnstiffenedPlateAnalysis(
    comm=comm,
    bdf_file="plate.bdf",
    a=1.0,
    b=1.0,
    h=0.01,  # slender near thin plate limit
    E11=70e9,
    nu12=0.33,
    plate_name="axial",
)

axial_plate.generate_bdf(
    nx=30,
    ny=30,
    exx=axial_plate.affine_exx,
    eyy=0.0,
    exy=0.0,
    clamped=False,
)

# avg_stresses = axial_plate.run_static_analysis(write_soln=True)

tacs_eigvals, _ = axial_plate.run_buckling_analysis(
    sigma=5.0, num_eig=8, write_soln=True
)

# sheared plate
# --------------------------------------------------
shear_plate = mlb.UnstiffenedPlateAnalysis(
    comm=comm,
    bdf_file="plate.bdf",
    a=1.0,
    b=1.0,
    h=0.01,  # slender near thin plate limit
    E11=70e9,
    nu12=0.33,
    plate_name="shear",
)

shear_plate.generate_bdf(
    nx=20,
    ny=30,
    exx=0.0,
    eyy=0.0,
    exy=shear_plate.affine_exy,
    clamped=False,
)

# avg_stresses = shear_plate.run_static_analysis(write_soln=True)

tacs_eigvals, _ = shear_plate.run_buckling_analysis(
    sigma=5.0, num_eig=16, write_soln=True
)

# perform modal assurance criterion between these two buckling analyses
# ---------------------------------------------------------------------
mlb.UnstiffenedPlateAnalysis.mac_permutation(axial_plate, shear_plate, num_modes=6)
