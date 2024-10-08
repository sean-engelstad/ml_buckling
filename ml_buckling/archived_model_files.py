"""
Paths to archived models
"""
__all__ = [
    "axialGP_csv",
    "shearGP_csv",
    "cripplingGP_csv",
    "axial_theta_csv",
    "shear_theta_csv",
]

import os

base_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(base_dir)
model_dir = os.path.join(root_dir, "archived_models")

axialGP_csv = os.path.join(model_dir, "axialGP.csv")
shearGP_csv = os.path.join(model_dir, "shearGP.csv")
cripplingGP_csv = os.path.join(model_dir, "cripplingGP.csv")
axial_theta_csv = os.path.join(model_dir, "axial_theta_opt.csv")
shear_theta_csv = os.path.join(model_dir, "shear_theta_opt.csv")
