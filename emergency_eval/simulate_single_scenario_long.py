import os.path
from concurrent.futures import ThreadPoolExecutor

from emergency_eval import settings
from emergency_eval.settings import num_workers, EVAL_PATH_SIM, EVAL_PATH_SCHED, num_sim_workers
from generate_omnetpp_scenario import generate_scenario
from run_simulation import run_simulation

if __name__ == "__main__":
    top_name = "t_3x4"
    run_name = "p_24/r_9"
    et_name = "et_24"

    top_folder = os.path.join(EVAL_PATH_SCHED, top_name)
    run_folder = os.path.join(top_folder, run_name)
    scenario_folder = os.path.join(run_folder, et_name)

    et_out = f"{EVAL_PATH_SIM}/{top_name}/{run_name}/{et_name}/etsn"
    generate_scenario(f"{top_folder}/topology.json", f"{run_folder}/streams.json",
                      f"{scenario_folder}/streams_et.json",
                      f"{scenario_folder}/etsn_out.json",
                      None,
                      et_out,
                      settings.num_runs,
                      ignore_highest_pcp=True)

    lib_out = f"{EVAL_PATH_SIM}/{top_name}/{run_name}/{et_name}/libtsndgm"
    generate_scenario(f"{top_folder}/topology.json", f"{run_folder}/streams.json",
                      f"{scenario_folder}/streams_et.json",
                      f"{run_folder}/cp_out.json",
                      f"{scenario_folder}/libtsndgm_out.json",
                      lib_out,
                      settings.num_runs)

    with ThreadPoolExecutor(max_workers=num_sim_workers) as executor:
        for i in range(settings.num_runs):
            executor.submit(run_simulation, et_out, settings.INET_PATH, et_out, "omnetpp.ini", i)
            executor.submit(run_simulation, lib_out, settings.INET_PATH, lib_out, "omnetpp.ini", i)
