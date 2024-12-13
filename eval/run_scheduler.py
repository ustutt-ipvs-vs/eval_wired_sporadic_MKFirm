import os
import shlex
import subprocess


cplex_path = "/home/haugls/cplex/cpoptimizer/bin/x86-64_linux/cpoptimizer"
cp_based_scheduling_path = "../../cp-based-tsn-scheduling/main.py"
estn_scheduler_path = "../../e-tsn/main.py"
libtsndgm_path = "../../libtsndgm/release/DgmExec"

def run_scheduler(exec_command, out_file):
    if os.path.exists(out_file):
        print("Skipping, already exists", out_file)
        return

    print(f"Running scheduler with command: {exec_command}")
    p = subprocess.Popen(shlex.split(exec_command))
    p.communicate()

    # Check if the process completed successfully
    if p.returncode == 0:
        print("Scheduler completed successfully.")
    else:
        print("Scheduler encountered an error.")

def run_scheduler_for_et_streams(top_folder, stream_folder, et_stream_file):
    tt_stream_file = f"{top_folder}/{stream_folder}/streams.json"

    et_run = et_stream_file.split("_")[-1]
    et_run = ".".join(et_run.split(".")[:-1])

    etsn_out_file = f"{top_folder}/{stream_folder}/etsn_out_{et_run}.json"
    exec_command_etsn = f'python3 {estn_scheduler_path} -n {top_folder}/topology.json -t {tt_stream_file} -e {et_stream_file} --cplex {cplex_path} -o {etsn_out_file}'
    run_scheduler(exec_command_etsn, etsn_out_file)

    cp_file = f"{top_folder}/{stream_folder}/cp_out.json"
    libtsndgm_out_file = f"{top_folder}/{stream_folder}/libtsndgm_out_{et_run}.json"
    exec_command_libtsndgm = f'{libtsndgm_path} -t {top_folder}/topology.json -s {tt_stream_file} -z {cp_file} --e_streams {et_stream_file} -o {libtsndgm_out_file}'
    run_scheduler(exec_command_libtsndgm, libtsndgm_out_file)

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

    for et_stream_filename in os.listdir(f"{top_folder}/{stream_folder}"):
        if et_stream_filename.startswith("streams_et"):
            et_stream_file = f"{top_folder}/{stream_folder}/{et_stream_filename}"
            run_scheduler_for_et_streams(top_folder, stream_folder, et_stream_file)


def run_scheduler_for_topology(top_folder):
    for stream_folder in os.listdir(top_folder):
        if stream_folder.startswith("s_"):
            run_scheduler_for_streams(top_folder, stream_folder)


if __name__ == "__main__":
    for folder in os.listdir("."):
        if folder.startswith("t_"):
            run_scheduler_for_topology(folder)