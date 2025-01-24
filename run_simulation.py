import argparse
import json
import math
import os
import shlex
import subprocess
import pandas as pd

from generate_omnetpp_scenario import parse_emergency_streams


def run_simulation(input_dir, inet_dir, result_dir, ini_filename):
    input_dir = os.path.abspath(input_dir)
    inet_dir = os.path.abspath(inet_dir)
    result_dir = os.path.abspath(result_dir)
    ini_file = os.path.join(input_dir, 'omnetpp.ini')
    log_file = os.path.join(result_dir, 'simulation.log')

    if os.path.exists(log_file):
        print("Skipping as simulation seems to be already done or ongoing.")
        return
    elif not os.path.exists(f'{result_dir}'):
        os.makedirs(f'{result_dir}')

    exec_command = f'opp_run -u Cmdenv -m -c General -n {input_dir}:{inet_dir}/src --image-path={inet_dir}/images -l {inet_dir}/src/INET {ini_file} --result-dir={result_dir}'

    f = open(log_file, "w+")

    print(f"Running simulation with command: {exec_command}")
    p = subprocess.Popen(shlex.split(exec_command), stdout=f, stderr=f, cwd=result_dir)
    p.communicate()

    # Check if the process completed successfully
    if p.returncode == 0:
        print("Simulation completed successfully.")
    else:
        print("Simulation encountered an error, see {log_file} for details.")





if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', help="Input directory containing .ini and .ned for simulation", type=str,
                        required=True)
    parser.add_argument('--inet', '-n', help="Directory to installed INET library", type=str, required=True)
    parser.add_argument('--output', '-o', help="Output directory", type=str, required=True)
    parser.add_argument('--ini-filename', '-f', help="Name of .ini file (if not omnetpp.ini)", default="omnetpp.ini",
                        type=str)
    parser.add_argument('--streams-meta', '-m', help="Path to streams meta file", type=str, required=False)
    args = parser.parse_args()

    run_simulation(args.input, args.inet, args.output, args.ini_filename)
