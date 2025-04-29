import json
import os
import shlex
import subprocess
import time

from emergency_eval.settings import estn_scheduler_path, libtsndgm_path, cplex_path, cp_based_scheduling_path


def run_scheduler(exec_command, out_dir, out_file_basename):
    log_file = f"{out_dir}/{out_file_basename}.log"
    meta_file = f"{out_dir}/{out_file_basename}_meta.json"

    if os.path.exists(log_file):
        print("Skipping, already exists", log_file)
        return

    print(f"Running scheduler with command: {exec_command}")
    start_time = time.time()
    p = subprocess.Popen(shlex.split(exec_command), stdout=open(log_file, "w"), stderr=subprocess.STDOUT)
    p.communicate()
    end_time = time.time()

    # Write meta information to the meta file
    elapsed_time = end_time - start_time
    meta = {
        "command": exec_command,
        "start_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)),
        "end_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time)),
        "elapsed_time": elapsed_time,
        "return_code": p.returncode
    }
    with open(meta_file, "w") as meta_f:
        json.dump(meta, meta_f, indent=4)

    # Check if the process completed successfully
    if p.returncode == 0:
        print("Scheduler completed successfully.")
    else:
        print("Scheduler encountered an error.")

def run_scheduler_for_et_streams(top_folder, stream_folder):
    tt_stream_file = f"{top_folder}/{stream_folder}/streams.json"
    et_stream_file = f"{top_folder}/{stream_folder}/streams_et.json"
    out_folder = f"{top_folder}/{stream_folder}"

    # Check if executed file exists
    if os.path.exists(f"{top_folder}/{stream_folder}/executed"):
        print("Skipping, already executed")
        return

    etsn_out_basename = f"etsn_out"
    etsn_out_file = f"{out_folder}/{etsn_out_basename}.json"
    exec_command_etsn = f'python3 {estn_scheduler_path} -n {top_folder}/topology.json -t {tt_stream_file} -e {et_stream_file} --cplex {cplex_path} -o {etsn_out_file}'
    run_scheduler(exec_command_etsn, out_folder, etsn_out_basename)

    cp_file = f"{top_folder}/{stream_folder}/cp_out.json"
    libtsn_out_basename = f"libtsndgm_out"
    libtsndgm_out_file = f"{out_folder}/{libtsn_out_basename}.json"
    exec_command_libtsndgm = f'{libtsndgm_path} -t {top_folder}/topology.json -s {tt_stream_file} -z {cp_file} --e_streams {et_stream_file} -o {libtsndgm_out_file}'
    run_scheduler(exec_command_libtsndgm, out_folder, libtsn_out_basename)

    # Generate a "executed" file
    open(f"{top_folder}/{stream_folder}/executed", "w").close()


def run_scheduler_for_tt_streams(top_folder, stream_folder):
    tt_stream_file = f"{top_folder}/{stream_folder}/streams.json"
    out_file = f"{top_folder}/{stream_folder}/cp_out.json"

    if os.path.exists(out_file):
        print("Skipping, already exists", out_file)
        return

    exec_command = f'python3 {cp_based_scheduling_path} -n {top_folder}/topology.json -s {tt_stream_file} --cplex {cplex_path} --out {out_file}'
    print(f"Running scheduler with command: {exec_command}")
    p = subprocess.Popen(shlex.split(exec_command))
    p.communicate()

    # Check if the process completed successfully
    if p.returncode == 0:
        print("Scheduler completed successfully.")
    else:
        print("Scheduler encountered an error.")

def run_scheduler_for_streams(top_folder, stream_folder):
    run_scheduler_for_tt_streams(top_folder, stream_folder)
    run_scheduler_for_et_streams(top_folder, stream_folder)



def run_scheduler_for_topology(top_folder):
    for stream_folder in os.listdir(top_folder):
        if stream_folder.startswith("s_"):
            for run_folder in os.listdir(f"{top_folder}/{stream_folder}"):
                if run_folder.startswith("r_"):
                    run_scheduler_for_streams(top_folder, f"{stream_folder}/{run_folder}")


if __name__ == "__main__":
    for folder in os.listdir("."):
        if folder.startswith("t_"):
            run_scheduler_for_topology(folder)