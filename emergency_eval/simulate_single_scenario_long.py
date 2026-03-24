import os.path
import shlex
import subprocess
from concurrent.futures import ThreadPoolExecutor

from emergency_eval import settings
from emergency_eval.settings import num_workers, EVAL_PATH_SIM, EVAL_PATH_SCHED, num_sim_workers
from generate_omnetpp_scenario import generate_scenario

def run_simulation(input_dir, inet_dir, result_dir, ini_filename, num_run=None):
    input_dir = os.path.abspath(input_dir)
    inet_dir = os.path.abspath(inet_dir)
    result_dir = os.path.abspath(result_dir)
    ini_file = os.path.join(input_dir, 'omnetpp.ini')
    log_file = os.path.join(result_dir, 'simulation.log')
    if num_run is not None:
        log_file = os.path.join(result_dir, f'simulation_{num_run}.log')

    if os.path.exists(log_file):
        print("Skipping as simulation seems to be already done or ongoing.")
        return
    elif not os.path.exists(f'{result_dir}'):
        os.makedirs(f'{result_dir}')

    num_run_text = ""
    if num_run is not None:
        num_run_text = f'-r {num_run}'
    exec_command = f'opp_run -u Cmdenv -m {num_run_text} -c General -n {input_dir}:{inet_dir}/src --image-path={inet_dir}/images -l {inet_dir}/src/INET {ini_file} --result-dir={result_dir} {ini_filename}'

    f = open(log_file, "w+")

    print(f"Running simulation with command: {exec_command}")
    p = subprocess.Popen(shlex.split(exec_command), stdout=f, stderr=f, cwd=result_dir)
    p.communicate()

    # Check if the process completed successfully
    if p.returncode == 0:
        print("Simulation completed successfully.")
    else:
        print(f"Simulation encountered an error, see {log_file} for details.")

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
                      settings.sim_time_seconds,
                      ignore_highest_pcp=True)

    lib_out = f"{EVAL_PATH_SIM}/{top_name}/{run_name}/{et_name}/libtsndgm"
    generate_scenario(f"{top_folder}/topology.json", f"{run_folder}/streams.json",
                      f"{scenario_folder}/streams_et.json",
                      f"{run_folder}/cp_out.json",
                      f"{scenario_folder}/libtsndgm_out.json",
                      lib_out,
                      settings.num_runs,
                      settings.sim_time_seconds)

    with ThreadPoolExecutor(max_workers=num_sim_workers) as executor:
        for i in range(settings.num_runs):
            executor.submit(run_simulation, et_out, settings.INET_PATH, et_out, "omnetpp.ini", i)
            executor.submit(run_simulation, lib_out, settings.INET_PATH, lib_out, "omnetpp.ini", i)
