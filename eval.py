import argparse
import json
import os
import shlex
import subprocess

import numpy as np
import pandas as pd


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def load_csv(output, run_number=None):
    csv_filename = os.path.join(output, 'output.csv')
    if run_number is not None:
        csv_filename = os.path.join(output, f'output-{run_number}.csv')
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

        if not delay_df['vectime'].any():
            stream["delay"] = [[], []]
        else:
            stream["delay"] = [
                list(map(float, delay_df['vectime'].item().split(" "))),
                list(map(float, delay_df['vecvalue'].item().split(" "))),
            ]

    for port, stream in emergency_streams.items():
        delay_df = df[
            (df['module'] == stream['sink']) & (df['name'] == 'meanBitLifeTimePerPacket:vector') & (
                    df['type'] == 'vector')]

        if not delay_df['vectime'].any():
            stream["delay"] = [[], []]
        else:
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


def calc_metrics(streams, streams_meta, debug=True):
    total_sum = 0
    total_len = 0
    all_delays = []
    for port, stream in streams.items():
        stream["min_delay"] = min(stream["delay"][1])
        stream["max_delay"] = max(stream["delay"][1])
        sum_now = sum(stream["delay"][1])
        stream["mean_delay"] = sum_now / len(stream["delay"][1])
        total_sum += sum_now
        total_len += len(stream["delay"][1])
        all_delays.extend(stream["delay"][1])
        stream["stddev_delay"] = np.std(stream["delay"][1])
        if debug:
            print(f"Stream {streams_meta[port]['id']} has "
                  f"min: {stream['min_delay']} "
                  f"max: {stream['max_delay']} "
                  f"mean: {stream['mean_delay']} "
                  f"stddev: {stream['stddev_delay']} ")

    result = {
        "total_min": min([stream["min_delay"] for stream in streams.values()]),
        "total_max": max([stream["max_delay"] for stream in streams.values()]),
        "total_mean": total_sum / total_len,
        "total_median": np.median(all_delays),
        "total_stddev": np.std(all_delays)
    }
    if debug:
        print(f"Total min: {result['total_min']} "
              f"max: {result['total_max']} "
              f"mean: {result['total_mean']} "
              f"median: {result['total_median']} "
              f"stddev: {result['total_stddev']} ")

    return result


def calc_offset_to_expected(streams, streams_meta):
    for port, stream in streams.items():
        stream_meta = streams_meta[port]
        num_frames_per_cycle = len(stream_meta["expected_arrivals"])
        delayed = 0
        too_late = 0
        too_early = 0

        stream["offset_to_expected"] = []
        for i in range(len(stream["delay"][0])):
            frame = i % num_frames_per_cycle
            arrival_time = round(stream["delay"][0][i] * 1e9)
            expected_arrival_time = round(
                stream_meta["expected_arrivals"][str(frame)] + (i - frame) * stream_meta["cycle_time"])
            latest_arrival_time = round(
                stream_meta["expected_latest_arrivals"][str(frame)] + (i - frame) * stream_meta["cycle_time"])
            if arrival_time > latest_arrival_time:
                too_late += 1
            if arrival_time != expected_arrival_time:
                delayed += 1
            if arrival_time < expected_arrival_time:
                too_early += 1
            stream["offset_to_expected"].append(arrival_time - expected_arrival_time)

        stream["too_early"] = too_early
        stream["too_late"] = too_late
        stream["delayed"] = delayed


def check_arrival_times(streams):
    for port, stream in streams.items():
        total = len(stream["delay"][0])
        print_str = f"Stream {port} has {stream['delayed']} of {total} delayed frames (due to emergency frames). ({stream['too_late']} too late, {stream['too_early']} too early)"
        if stream['too_late'] > 0:
            print(bcolors.FAIL + print_str + bcolors.ENDC)
        elif stream['too_early'] > 0:
            print(bcolors.OKCYAN + print_str + bcolors.ENDC)
        elif total == 0:
            print(bcolors.WARNING + print_str + bcolors.ENDC)
        else:
            pass
            print(bcolors.OKGREEN + print_str + bcolors.ENDC)


def load_eval_files(output, stream_meta_file, run_number=None):
    streams, emergency_streams = load_csv(output, run_number)
    streams_meta = load_stream_meta(stream_meta_file)
    return streams, emergency_streams, streams_meta


def extract_data(output_dir, run_number=0):
    filter = "meanBitLifeTimePerPacket:vector OR localPort OR destPort"
    vec_file = os.path.join(output_dir, f'General-#{run_number}.vec')
    sca_file = os.path.join(output_dir, f'General-#{run_number}.sca')
    output_file = os.path.join(output_dir, f'output-{run_number}.csv')
    log_file = os.path.join(output_dir, f'extract-{run_number}.log')

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
