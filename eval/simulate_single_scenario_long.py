import os.path

from eval.settings import EVAL_PATH
from generate_omnetpp_scenario import generate_scenario
from run_simulation import run_simulation

if __name__ == "__main__":
    top_folder = os.path.join(EVAL_PATH, "t_3x4")
    run_folder = os.path.join(top_folder, "p_24/r_16/")
    scenario_folder = os.path.join(run_folder, "et_24")

    et_out = f"{scenario_folder}/etsn"
    generate_scenario(f"{top_folder}/topology.json", f"{run_folder}/streams.json",
                      f"{scenario_folder}/streams_et.json",
                      f"{scenario_folder}/etsn_out.json",
                      None,
                      et_out)

    lib_out = f"{scenario_folder}/libtsndgm"
    generate_scenario(f"{top_folder}/topology.json", f"{run_folder}/streams.json",
                      f"{scenario_folder}/streams_et.json",
                      f"{run_folder}/cp_out.json",
                      f"{scenario_folder}/libtsndgm_out.json",
                      lib_out)


    run_simulation(et_out, "/home/haugls/workspaces/emergency/inet", et_out, "omnetpp.ini")
    run_simulation(lib_out, "/home/haugls/workspaces/emergency/inet", lib_out, "omnetpp.ini")