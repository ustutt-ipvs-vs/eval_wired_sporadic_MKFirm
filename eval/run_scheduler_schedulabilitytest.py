import os
from concurrent.futures import ThreadPoolExecutor

from eval.run_scheduler import run_scheduler
from eval.settings import EVAL_PATH, estn_scheduler_path, cplex_path, libtsndgm_path, cp_based_scheduling_path, \
    cplex_timelimit, cplex_threads


def run_scheduler_for_et_streams(top_folder, stream_folder, et_folder):
    tt_stream_file = f"{top_folder}/{stream_folder}/streams.json"
    et_stream_file = f"{top_folder}/{stream_folder}/{et_folder}/streams_et.json"

    out_dir = f"{top_folder}/{stream_folder}/{et_folder}"

    etsn_out_basename = "etsn_out"
    etsn_out_file = f"{out_dir}/{etsn_out_basename}.json"
    exec_command_etsn = f'python3 {estn_scheduler_path} -n {top_folder}/topology.json -t {tt_stream_file} -e {et_stream_file} --cplex {cplex_path} -o {etsn_out_file} --timelimit {cplex_timelimit} --threads {cplex_threads}'
    run_scheduler(exec_command_etsn, out_dir, etsn_out_basename)

    etsn2_out_basename = "etsn2_out"
    etsn2_out_file = f"{out_dir}/{etsn2_out_basename}.json"
    exec_command_etsn2 = f'python3 {estn_scheduler_path} -N 2 -n {top_folder}/topology.json -t {tt_stream_file} -e {et_stream_file} --cplex {cplex_path} -o {etsn2_out_file} --timelimit {cplex_timelimit} --threads {cplex_threads}'
    run_scheduler(exec_command_etsn2, out_dir, etsn2_out_basename)

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
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = []
        for stream_folder in os.listdir(top_folder):
            if stream_folder.startswith("p_"):
                for run_folder in os.listdir(f"{top_folder}/{stream_folder}"):
                    if run_folder.startswith("r_"):
                        # run_for_runfolder(top_folder, stream_folder, run_folder)
                        executor.submit(run_for_runfolder, top_folder, stream_folder, run_folder)

        for future in futures:
            future.result()


def run_for_runfolder(top_folder, stream_folder, run_folder):
    run_scheduler_for_tt_streams(f"{top_folder}", f"{stream_folder}/{run_folder}")
    for et_folder in os.listdir(f"{top_folder}/{stream_folder}/{run_folder}"):
        if et_folder.startswith("et_"):
            run_scheduler_for_et_streams(top_folder, f"{stream_folder}/{run_folder}/", et_folder)


if __name__ == "__main__":
    for folder in os.listdir(EVAL_PATH):
        if folder.startswith("t_"):
            folder = f"{EVAL_PATH}/{folder}"
            run_scheduler_for_topology(folder)
