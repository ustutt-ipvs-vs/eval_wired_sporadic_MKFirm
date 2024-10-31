import argparse
import json
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


def extract_data(output_dir):
    filter = "meanBitLifeTimePerPacket:vector OR localPort OR destPort"
    vec_file = os.path.join(output_dir, 'General-#0.vec')
    sca_file = os.path.join(output_dir, 'General-#0.sca')
    output_file = os.path.join(output_dir, 'output.csv')
    log_file = os.path.join(output_dir, 'extract.log')

    exec_command = f'opp_scavetool x {vec_file} {sca_file} -F CSV-R -f \'{filter}\' -o {output_file}'

    if os.path.exists(output_file):
        print("Skipping, already exists", output_file)
        return

    print(f"Extracting data with command: {exec_command}")
    f = open(log_file, "w+")

    p = subprocess.Popen(shlex.split(exec_command), stdout=f, stderr=f)
    p.communicate()

    # Check if the process completed successfully
    if p.returncode == 0:
        print("Data extraction completed successfully.")
    else:
        print("Data extraction encountered an error, see {log_file} for details.")


def load_csv(output):
    csv_filename = os.path.join(output, 'output.csv')
    df = pd.read_csv(csv_filename)

    streams = {}
    emergency_streams = {}

    stream_types = df.loc[df['name'].str.contains('', na=False)]

    ports = df.loc[df['name'].str.contains('localPort|destPort', na=False)]
    # print(ports)
    for index, row in ports.iterrows():
        module_name = row['module'].split('.')[1]
        port = row['value']
        port_type = row['name']
        if port < 0:
            continue
        port = int(port)
        streams_now = streams
        if port >= 10000:
            streams_now = emergency_streams

        if port not in streams_now:
            streams_now[port] = {}
        if port_type == 'destPort':
            streams_now[port]['source'] = module_name
        else:
            streams_now[port]['sink'] = '.'.join(row['module'].split('.')[0:-1]) + ".sink"

    for port, stream in streams.items():
        delay_df = df[
            (df['module'] == stream['sink']) & (df['name'] == 'meanBitLifeTimePerPacket:vector') & (
                    df['type'] == 'vector')]

        stream["delay"] = [
            list(map(float, delay_df['vectime'].item().split(" "))),
            list(map(float, delay_df['vecvalue'].item().split(" "))),
        ]
    return streams, emergency_streams


def load_stream_meta(stream_meta_file):
    with open(stream_meta_file, 'r') as file:
        stream_meta = json.load(file)

    stream_meta_by_port = {}
    for sid, stream in stream_meta.items():
        port = stream['port']
        stream["id"] = sid
        stream_meta_by_port[port] = stream

    return stream_meta_by_port


def check_arrival_delays(streams, streams_meta):
    for port, stream in streams.items():
        stream_meta = streams_meta[port]
        num_frames_per_cycle = len(stream_meta["expected_arrivals"])
        delayed = 0
        too_late = 0
        for i in range(len(stream["delay"][0])):
            frame = i % num_frames_per_cycle
            arrival_time = round(stream["delay"][0][i] * 1e9)
            expected_arrival_time = round(stream_meta["expected_arrivals"][str(frame)] + (i-frame) * stream_meta["cycle_time"])
            latest_arrival_time = round(stream_meta["expected_latest_arrivals"][str(frame)] + (i-frame) * stream_meta["cycle_time"])
            if arrival_time > latest_arrival_time:
                print(f"Arrival time too late for stream {stream_meta['id']}, frame {i}: Expected at most {latest_arrival_time}, got {arrival_time}")
                too_late += 1
            if arrival_time != expected_arrival_time:
                delayed += 1
        print(f"Stream {stream_meta['id']} has {delayed} delayed frames (due to emergency frames). ({too_late} too late)")




def eval_results(output, stream_meta_file):
    streams, emergency_streams = load_csv(output)
    streams_meta = load_stream_meta(stream_meta_file)
    check_arrival_delays(streams, streams_meta)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', help="Input directory containing .ini and .ned for simulation", type=str, required=True)
    parser.add_argument('--inet', '-n', help="Directory to installed INET library", type=str, required=True)
    parser.add_argument('--output', '-o', help="Output directory", type=str, required=True)
    parser.add_argument('--ini-filename', '-f', help="Name of .ini file (if not omnetpp.ini)", default="omnetpp.ini", type=str)
    parser.add_argument('--streams-meta', '-m', help="Path to streams meta file", type=str, required=False)
    parser.add_argument('--steps', '-s', help="Only perform a specific step of simulation (0=All (default), 1=Simulate, 2=Extract data, 3=Evaluate results)", default=0, type=int)
    args = parser.parse_args()

    if (args.steps == 0) or (args.steps == 1):
        run_simulation(args.input, args.inet, args.output, args.ini_filename)

    if (args.steps == 0) or (args.steps == 2):
        extract_data(args.output)

    if (args.steps == 0) or (args.steps == 3):
        # Check streams meta argument given
        if args.streams_meta is None:
            raise ValueError("Streams meta file is required for evaluation of results.")
        eval_results(args.output, args.streams_meta)
