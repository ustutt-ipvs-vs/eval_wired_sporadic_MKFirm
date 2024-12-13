import os
from run_simulation import run_simulation, extract_data, eval_results
from generate_omnetpp_scenario import generate_scenario


def prepare_and_run_sim(top_folder, stream_folder, sim_file):
    if not sim_file.startswith("etsn") and not sim_file.startswith("libtsndgm") or os.path.isdir(f"{stream_folder}/{sim_file}"):
        return

    et_run = sim_file.split("_")[-1]
    et_run = ".".join(et_run.split(".")[:-1])
    print(f"Generating simulation for {stream_folder}/{sim_file}")
    if sim_file.startswith("etsn"):
        out_folder = f"{stream_folder}/etsn_{et_run}"
        generate_scenario(f"{top_folder}/topology.json", f"{stream_folder}/streams.json",
                          f"{stream_folder}/streams_et_{et_run}.json",
                          f"{stream_folder}/{sim_file}",
                          None,
                          out_folder)

    if sim_file.startswith("libtsndgm"):
        out_folder = f"{stream_folder}/libtsndgm_{et_run}"
        generate_scenario(f"{top_folder}/topology.json", f"{stream_folder}/streams.json",
                          f"{stream_folder}/streams_et_{et_run}.json",
                          f"{stream_folder}/cp_out.json",
                          f"{stream_folder}/{sim_file}",
                          out_folder)

    run_simulation(out_folder, "/home/haugls/workspaces/emergency/inet", out_folder, "omnetpp.ini")
    extract_data(out_folder)
    eval_results(out_folder, f"{out_folder}/stream_meta.json")


if __name__ == "__main__":
    # Beautiful code <3
    for top_folder in os.listdir("."):
        if top_folder.startswith("t_"):
            for stream_folder in os.listdir(top_folder):
                if stream_folder.startswith("s_"):
                    for sim_file in os.listdir(f"{top_folder}/{stream_folder}"):
                        prepare_and_run_sim(top_folder, f"{top_folder}/{stream_folder}", sim_file)
