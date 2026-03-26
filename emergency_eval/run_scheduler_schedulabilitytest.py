import argparse
import json
import os
import shlex
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

from fontTools.misc.cython import returns
from networkx.algorithms.coloring.greedy_coloring import strategy_largest_first

from emergency_eval.settings import EVAL_PATH_SCHED, estn_scheduler_path, cplex_path, libtsndgm_path, cp_based_scheduling_path, \
    cplex_timelimit, cplex_threads, num_workers

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

def run_scheduler_for_et_streams(top_folder, stream_folder, et_folder):
    tt_stream_file = f"{top_folder}/{stream_folder}/streams.json"
    et_stream_file = f"{top_folder}/{stream_folder}/{et_folder}/streams_et.json"

    out_dir = f"{top_folder}/{stream_folder}/{et_folder}"

    etsn_out_basename = "etsn_out"
    etsn_out_file = f"{out_dir}/{etsn_out_basename}.json"
    exec_command_etsn = f'python3 {estn_scheduler_path} -n {top_folder}/topology.json -t {tt_stream_file} -e {et_stream_file} --cplex {cplex_path} -o {etsn_out_file} --timelimit {cplex_timelimit} --threads {cplex_threads}'
    run_scheduler(exec_command_etsn, out_dir, etsn_out_basename)

    cp_file = f"{top_folder}/{stream_folder}/cp_out.json"
    libtsndgm_out_basename = "libtsndgm_out"
    libtsndgm_out_file = f"{out_dir}/{libtsndgm_out_basename}.json"
    exec_command_libtsndgm = f'{libtsndgm_path} -t {top_folder}/topology.json -s {tt_stream_file} -z {cp_file} --e_streams {et_stream_file} -o {libtsndgm_out_file}'
    run_scheduler(exec_command_libtsndgm, out_dir, libtsndgm_out_basename)


def run_scheduler_for_tt_streams(top_folder, stream_folder):
    tt_stream_file = f"{top_folder}/{stream_folder}/streams.json"
    out_folder = f"{top_folder}/{stream_folder}/"
    out_file_base = "cp_out"
    out_file = f"{out_folder}/{out_file_base}.json"

    exec_command = f'python3 {cp_based_scheduling_path} -n {top_folder}/topology.json -s {tt_stream_file} --cplex {cplex_path} --out {out_file} --timelimit {cplex_timelimit} --threads {cplex_threads}'
    run_scheduler(exec_command, out_folder, out_file_base)


def run_scheduler_for_topology(top_folder):
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for stream_folder in os.listdir(top_folder):
            if stream_folder.startswith("p_"):
                for run_folder in os.listdir(f"{top_folder}/{stream_folder}"):
                    if run_folder.startswith("r_"):
                        executor.submit(run_for_runfolder, top_folder, stream_folder, run_folder)

        for future in futures:
            future.result()


def run_for_runfolder(top_folder, stream_folder, run_folder):
    print(top_folder, stream_folder, run_folder)
    run_scheduler_for_tt_streams(f"{top_folder}", f"{stream_folder}/{run_folder}")
    for et_folder in os.listdir(f"{top_folder}/{stream_folder}/{run_folder}"):
        if et_folder.startswith("et_"):
            run_scheduler_for_et_streams(top_folder, f"{stream_folder}/{run_folder}/", et_folder)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--folder", "-f", required=False, default=None, help="Run only for specific run folder")
    args = parser.parse_args()

    if args.folder:
        et_folder = os.path.abspath(args.folder)
        run_folder = os.path.abspath(os.path.join(et_folder, os.pardir))
        stream_folder = os.path.abspath(os.path.join(run_folder, os.pardir))
        top_folder = os.path.abspath(os.path.join(stream_folder, os.pardir))

        stream_folder_name = os.path.basename(stream_folder)
        run_folder_name = os.path.basename(run_folder)
        et_folder_name = os.path.basename(et_folder)

        run_scheduler_for_tt_streams(f"{top_folder}", f"{stream_folder_name}/{run_folder_name}")
        run_scheduler_for_et_streams(top_folder, f"{stream_folder_name}/{run_folder_name}/", et_folder_name)

    else:
        for folder in os.listdir(EVAL_PATH_SCHED):
            if folder.startswith("t_"):
                folder = f"{EVAL_PATH_SCHED}/{folder}"
                run_scheduler_for_topology(folder)
