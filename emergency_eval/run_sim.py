import os
from run_simulation import run_simulation
from generate_omnetpp_scenario import generate_scenario


def prepare_and_run_sim(top_folder, run_folder, sim_file):
    if not sim_file.startswith("etsn") and not sim_file.startswith("libtsndgm") or os.path.isdir(f"{run_folder}/{sim_file}"):
        return

    if not os.path.exists(f"{run_folder}/{sim_file}"):
        print(f"Simulation file {run_folder}/{sim_file} does not exist")
        return

    print(f"Generating simulation for {run_folder}/{sim_file}")
    if sim_file.startswith("etsn"):
        out_folder = f"{run_folder}/etsn"
        generate_scenario(f"{top_folder}/topology.json", f"{run_folder}/streams.json",
                          f"{run_folder}/streams_et.json",
                          f"{run_folder}/{sim_file}",
                          None,
                          out_folder)

    if sim_file.startswith("libtsndgm"):
        out_folder = f"{run_folder}/libtsndgm"
        generate_scenario(f"{top_folder}/topology.json", f"{run_folder}/streams.json",
                          f"{run_folder}/streams_et.json",
                          f"{run_folder}/cp_out.json",
                          f"{run_folder}/{sim_file}",
                          out_folder)


    print(f"Running simulation for {out_folder}")
    run_simulation(out_folder, "/home/haugls/workspaces/emergency/inet", out_folder, "omnetpp.ini")


if __name__ == "__main__":
    # Beautiful code <3
    for top_folder in os.listdir("."):
        if top_folder.startswith("t_"):
            for stream_folder in os.listdir(top_folder):
                if stream_folder.startswith("s_"):
                    for run_folder in os.listdir(f"{top_folder}/{stream_folder}"):
                        if run_folder.startswith("r_"):
                            prepare_and_run_sim(top_folder, f"{top_folder}/{stream_folder}/{run_folder}",
                                                "etsn_out.json")
                            prepare_and_run_sim(top_folder, f"{top_folder}/{stream_folder}/{run_folder}",
                                                "libtsndgm_out.json")
