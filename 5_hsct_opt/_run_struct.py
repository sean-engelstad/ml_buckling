"""
Sean P. Engelstad, Georgia Tech 2023

Local machine optimization for the panel thicknesses using all OML and LE panels (more design variables) but no shape variables
"""

from funtofem import *

# import openmdao.api as om
from mpi4py import MPI
from tacs import caps2tacs
import os
import argparse

parent_parser = argparse.ArgumentParser(add_help=False)
parent_parser.add_argument("--procs", type=int, default=4)
parent_parser.add_argument(
    "--hotstart", default=False, action=argparse.BooleanOptionalAction
)
parent_parser.add_argument(
    "--useML", default=False, action=argparse.BooleanOptionalAction
)
parent_parser.add_argument(
    "--newMesh", default=False, action=argparse.BooleanOptionalAction
)
args = parent_parser.parse_args()

comm = MPI.COMM_WORLD

if args.useML:
    from _gp_callback import gp_callback_generator

    model_name = "ML-oneway"
else:
    from _closed_form_callback import closed_form_callback as callback

    model_name = "CF-oneway"

base_dir = os.path.dirname(os.path.abspath(__file__))
csm_path = os.path.join(base_dir, "geometry", "hsct.csm")

# F2F MODEL and SHAPE MODELS
# ----------------------------------------

f2f_model = FUNtoFEMmodel(model_name)
# tacs_model = caps2tacs.TacsModel.build(
#    csm_file=csm_path,
#    comm=comm,
#    problem_name="capsStruct",
#    active_procs=[0],
#    verbosity=1,
# )
# tacs_model.mesh_aim.set_mesh(  # need a refined-enough mesh for the derivative test to pass
#    edge_pt_min=2,
#    edge_pt_max=20,
#    mesh_elements="Mixed",
#    global_mesh_size=0.05,
#    max_surf_offset=0.2,
#    max_dihedral_angle=15,
# ).register_to(
#    tacs_model
# )
# f2f_model.structural = tacs_model

# tacs_aim = tacs_model.tacs_aim
# tacs_aim.set_config_parameter("mode:flow", 0)
# tacs_aim.set_config_parameter("mode:struct", 1)
# tacs_aim.set_config_parameter("wing:allOMLgroups", 1)
# tacs_aim.set_config_parameter("wing:includeLE", 0)
# tacs_aim.set_config_parameter("wing:includeTE", 0)
# tacs_aim.set_config_parameter("wing:nspars", 40) # same # as concorde

# for proc in tacs_aim.active_procs:
#    if comm.rank == proc:
#        aim = tacs_model.mesh_aim.aim
#        aim.input.Mesh_Sizing = {
#            "chord": {"numEdgePoints": 20},
#            "span": {"numEdgePoints": 8},
#            "vert": {"numEdgePoints": 4},
#        }
# "LEribFace": {"tessParams": [0.03, 0.1, 3]},
# "LEribEdge": {"numEdgePoints": 20},

# add tacs constraints in
# caps2tacs.PinConstraint("root").register_to(tacs_model)
# caps2tacs.PinConstraint("station2").register_to(tacs_model)
# caps2tacs.TemperatureConstraint("midplane", temperature=0).register_to(tacs_model)

# BODIES AND STRUCT DVs
# -------------------------------------------------

wing = Body.aeroelastic("wing", boundary=5)
# aerothermoelastic

# setup the material and shell properties
# null_material = caps2tacs.Orthotropic.null().register_to(tacs_model)

nribs = 20
nspars = 40
# nribs = int(tacs_model.get_config_parameter("wing:nribs"))
# nspars = int(tacs_model.get_config_parameter("wing:nspars"))
nOML = nribs - 1

# NOTE : the feature in ESP/CAPS that gives you the names of all capsGroups
# failed to list all of them since it hit the character limit in the textbox
# so I basically had to count the ranges of all capsGroups myself..
component_groups = []
for prefix in ["OMLtop", "OMLbot"]:
    component_groups += [f"{prefix}1-{ispar}" for ispar in range(1, 41 + 1)]
    component_groups += [f"{prefix}2-{ispar}" for ispar in range(3, 41 + 1)]
    component_groups += [f"{prefix}3-{ispar}" for ispar in range(6, 41 + 1)]
    component_groups += [f"{prefix}4-{ispar}" for ispar in range(9, 41 + 1)]
    component_groups += [f"{prefix}5-{ispar}" for ispar in range(12, 41 + 1)]
    component_groups += [f"{prefix}6-{ispar}" for ispar in range(15, 41 + 1)]
    component_groups += [f"{prefix}7-{ispar}" for ispar in range(18, 41 + 1)]
    component_groups += [f"{prefix}8-{ispar}" for ispar in range(20, 41 + 1)]
    component_groups += [f"{prefix}9-{ispar}" for ispar in range(23, 41 + 1)]
    component_groups += [f"{prefix}10-{ispar}" for ispar in range(24, 41 + 1)]
    component_groups += [f"{prefix}11-{ispar}" for ispar in range(26, 41 + 1)]
    component_groups += [f"{prefix}12-{ispar}" for ispar in range(27, 41 + 1)]
    component_groups += [f"{prefix}13-{ispar}" for ispar in range(28, 41 + 1)]
    component_groups += [f"{prefix}14-{ispar}" for ispar in range(29, 41 + 1)]
    component_groups += [f"{prefix}15-{ispar}" for ispar in range(30, 41 + 1)]
    component_groups += [f"{prefix}16-{ispar}" for ispar in range(31, 41 + 1)]
    component_groups += [f"{prefix}17-{ispar}" for ispar in range(32, 41 + 1)]
    component_groups += [f"{prefix}18-{ispar}" for ispar in range(33, 41 + 1)]
    component_groups += [f"{prefix}19-{ispar}" for ispar in range(34, 41 + 1)]

# add rib component groups based on OML ones
rib_groups = ["rib" + comp[6:] for comp in component_groups if "OMLtop" in comp]
rib_groups += [f"rib20-{ispar}" for ispar in range(35, 41 + 1)]
component_groups += rib_groups

# add spar component groups
component_groups += [f"LEspar-{iOML}" for iOML in range(1, 19 + 1)]
component_groups += [f"TEspar-{iOML}" for iOML in range(1, 19 + 1)]
component_groups += [f"spar1-{iOML}" for iOML in range(1, 1 + 1)]
component_groups += [f"spar2-{iOML}" for iOML in range(1, 1 + 1)]
component_groups += [f"spar3-{iOML}" for iOML in range(1, 2 + 1)]
component_groups += [f"spar4-{iOML}" for iOML in range(1, 2 + 1)]
component_groups += [f"spar5-{iOML}" for iOML in range(1, 2 + 1)]
component_groups += [f"spar6-{iOML}" for iOML in range(1, 3 + 1)]
component_groups += [f"spar7-{iOML}" for iOML in range(1, 3 + 1)]
component_groups += [f"spar8-{iOML}" for iOML in range(1, 3 + 1)]
component_groups += [f"spar9-{iOML}" for iOML in range(1, 4 + 1)]
component_groups += [f"spar10-{iOML}" for iOML in range(1, 4 + 1)]
component_groups += [f"spar11-{iOML}" for iOML in range(1, 4 + 1)]
component_groups += [f"spar12-{iOML}" for iOML in range(1, 5 + 1)]
component_groups += [f"spar13-{iOML}" for iOML in range(1, 5 + 1)]
component_groups += [f"spar14-{iOML}" for iOML in range(1, 5 + 1)]
component_groups += [f"spar15-{iOML}" for iOML in range(1, 6 + 1)]
component_groups += [f"spar16-{iOML}" for iOML in range(1, 6 + 1)]
component_groups += [f"spar17-{iOML}" for iOML in range(1, 6 + 1)]
component_groups += [f"spar18-{iOML}" for iOML in range(1, 7 + 1)]
component_groups += [f"spar19-{iOML}" for iOML in range(1, 7 + 1)]
component_groups += [f"spar20-{iOML}" for iOML in range(1, 8 + 1)]
component_groups += [f"spar21-{iOML}" for iOML in range(1, 8 + 1)]
component_groups += [f"spar22-{iOML}" for iOML in range(1, 8 + 1)]
component_groups += [f"spar23-{iOML}" for iOML in range(1, 9 + 1)]
component_groups += [f"spar24-{iOML}" for iOML in range(1, 10 + 1)]
component_groups += [f"spar25-{iOML}" for iOML in range(1, 10 + 1)]
component_groups += [f"spar26-{iOML}" for iOML in range(1, 11 + 1)]
component_groups += [f"spar27-{iOML}" for iOML in range(1, 12 + 1)]
component_groups += [f"spar28-{iOML}" for iOML in range(1, 13 + 1)]
component_groups += [f"spar29-{iOML}" for iOML in range(1, 14 + 1)]
component_groups += [f"spar30-{iOML}" for iOML in range(1, 15 + 1)]
component_groups += [f"spar31-{iOML}" for iOML in range(1, 16 + 1)]
component_groups += [f"spar32-{iOML}" for iOML in range(1, 17 + 1)]
component_groups += [f"spar33-{iOML}" for iOML in range(1, 18 + 1)]
component_groups += [f"spar34-{iOML}" for iOML in range(1, 19 + 1)]
component_groups += [f"spar35-{iOML}" for iOML in range(1, 19 + 1)]
component_groups += [f"spar36-{iOML}" for iOML in range(1, 19 + 1)]
component_groups += [f"spar37-{iOML}" for iOML in range(1, 19 + 1)]
component_groups += [f"spar38-{iOML}" for iOML in range(1, 19 + 1)]
component_groups += [f"spar39-{iOML}" for iOML in range(1, 19 + 1)]
component_groups += [f"spar40-{iOML}" for iOML in range(1, 19 + 1)]

component_groups = sorted(component_groups)

# print(f"component group 89 = {component_groups[89]}")
# exit()

if args.useML:
    callback = gp_callback_generator(component_groups)

for icomp, comp in enumerate(component_groups):
    # caps2tacs.CompositeProperty.null(comp, null_material).register_to(tacs_model)

    # NOTE : need to make the struct DVs in TACS in the same order as the blade callback
    # which is done by components and then a local order

    # panel length variable
    Variable.structural(
        f"{comp}-" + TacsSteadyInterface.LENGTH_VAR, value=0.1
    ).set_bounds(
        lower=0.0,
        scale=1.0,
        state=True,  # need the length & width to be state variables
    ).register_to(
        wing
    )

    # stiffener pitch variable
    Variable.structural(f"{comp}-spitch", value=0.20).set_bounds(
        lower=0.05, upper=0.5, scale=1.0
    ).register_to(wing)

    # panel thickness variable, shortened DV name for ESP/CAPS, nastran requirement here
    Variable.structural(f"{comp}-pthick", value=0.01).set_bounds(
        lower=0.002, upper=0.1, scale=100.0
    ).register_to(wing)

    # stiffener height
    Variable.structural(f"{comp}-sheight", value=0.05).set_bounds(
        lower=0.002, upper=0.1, scale=10.0
    ).register_to(wing)

    # stiffener thickness
    Variable.structural(f"{comp}-sthick", value=0.02).set_bounds(
        lower=0.002, upper=0.1, scale=100.0
    ).register_to(wing)

    Variable.structural(
        f"{comp}-" + TacsSteadyInterface.WIDTH_VAR, value=0.1
    ).set_bounds(
        lower=0.0,
        scale=1.0,
        state=True,  # need the length & width to be state variables
    ).register_to(
        wing
    )


# register the wing body to the model
wing.register_to(f2f_model)

# INITIAL STRUCTURE MESH, SINCE NO STRUCT SHAPE VARS
# --------------------------------------------------

# tacs_aim.setup_aim()
# if args.newMesh:
#    tacs_aim.pre_analysis()

# SCENARIOS
# ----------------------------------------------------

# make a funtofem scenario
climb = Scenario.steady("climb_turb", steps=350, uncoupled_steps=200)  # 2000
Function.ksfailure(ks_weight=20.0, safety_factor=1.5).optimize(
    scale=1.0, upper=1.0, objective=False, plot=True, plot_name="ks-climb"
).register_to(climb)
Function.mass().optimize(
    scale=1.0e-4, objective=True, plot=True, plot_name="mass"
).register_to(climb)
climb.set_temperature(T_ref=216, T_inf=216)
climb.set_flow_ref_vals(qinf=3.16e4)
climb.register_to(f2f_model)

# DISCIPLINE INTERFACES AND DRIVERS
# -----------------------------------------------------

solvers = SolverManager(comm)
# solvers.flow = Fun3dInterface(comm, f2f_model, fun3d_dir="meshes")
solvers.structural = TacsSteadyInterface.create_from_bdf(
    model=f2f_model,
    comm=comm,
    nprocs=args.procs,
    # bdf_file=tacs_aim.root_dat_file if args.newMesh else "struct/tacs.dat",
    # prefix=tacs_aim.root_analysis_dir if args.newMesh else "struct",
    bdf_file="struct/tacs.dat",
    prefix="struct",
    callback=callback,
    panel_length_dv_index=0,
    panel_width_dv_index=5,
)

# read in aero loads
aero_loads_file = os.path.join(os.getcwd(), "cfd", "loads", "uncoupled_turb_loads.txt")

transfer_settings = TransferSettings(npts=200)

# build the shape driver from the file
tacs_driver = OnewayStructDriver.prime_loads_from_file(
    filename=aero_loads_file,
    solvers=solvers,
    model=f2f_model,
    nprocs=args.procs,
    transfer_settings=transfer_settings,
    init_transfer=True,
)

f2f_model.read_design_variables_file(comm, "design/ML-sizing.txt" if args.useML else "design/CF-sizing.txt")

tacs_driver.solve_forward()

# print out the function values
if comm.rank == 0:
    for func in f2f_model.get_functions(optim=True):
        print(f"func {func.name} = {func.value.real}")
