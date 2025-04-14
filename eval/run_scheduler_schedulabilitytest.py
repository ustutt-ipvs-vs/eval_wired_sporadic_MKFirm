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

def run_scheduler_for_et_streams(top_folder, stream_folder, et_folder):
    tt_stream_file = f"{top_folder}/{stream_folder}/streams.json"
    et_stream_file = f"{top_folder}/{stream_folder}/{et_folder}/streams_et.json"

    # Check if executed file exists
    if os.path.exists(f"{top_folder}/{stream_folder}/{et_folder}/executed"):
        print("Skipping, already executed")
        return

    etsn_out_file = f"{top_folder}/{stream_folder}/{et_folder}/etsn_out.json"
    exec_command_etsn = f'python3 {estn_scheduler_path} -n {top_folder}/topology.json -t {tt_stream_file} -e {et_stream_file} --cplex {cplex_path} -o {etsn_out_file}'
    run_scheduler(exec_command_etsn, etsn_out_file)

    cp_file = f"{top_folder}/{stream_folder}/cp_out.json"
    libtsndgm_out_file = f"{top_folder}/{stream_folder}/{et_folder}/libtsndgm_out.json"
    exec_command_libtsndgm = f'{libtsndgm_path} -t {top_folder}/topology.json -s {tt_stream_file} -z {cp_file} --e_streams {et_stream_file} -o {libtsndgm_out_file}'
    run_scheduler(exec_command_libtsndgm, libtsndgm_out_file)

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


def run_scheduler_for_topology(top_folder):
    for stream_folder in os.listdir(top_folder):
        if stream_folder.startswith("p_"):
            for run_folder in os.listdir(f"{top_folder}/{stream_folder}"):
                if run_folder.startswith("r_"):
                    run_scheduler_for_tt_streams(f"{top_folder}", f"{stream_folder}/{run_folder}")
                    for et_folder in os.listdir(f"{top_folder}/{stream_folder}/{run_folder}"):
                        if et_folder.startswith("et_"):
                            run_scheduler_for_et_streams(top_folder, f"{stream_folder}/{run_folder}/", et_folder)


if __name__ == "__main__":
    for folder in os.listdir("."):
        if folder.startswith("t_"):
            run_scheduler_for_topology(folder)