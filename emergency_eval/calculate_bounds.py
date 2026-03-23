import os

from emergency_eval.settings import EVAL_PATH_SCHED
from topology.topology import parse_topology
from generate_omnetpp_scenario import parse_emergency_streams

def calculate_bucket_size_per_hop(topology, e_streams):
    bucket_per_hop = {}
    for stream in e_streams:
        for hop in stream['route']:
            link = (hop['from'], hop['to'])
            if link not in bucket_per_hop:
                bucket_per_hop[link] = 0
            bucket_per_hop[link] += stream['frame_size_byte']
    return bucket_per_hop

def calculate_max_delay_per_hop(bucket_per_hop, min_frame_size, max_frame_size):
    # In our scenario, the datarate is always 100Mbps
    datarate = 100 * 1e6  # 100 Mbps in bps
    MTU_BITS = 1500 * 8  # MTU in bits

    max_delay_per_hop = {}
    for link, bucket_size in bucket_per_hop.items():
        bucket_size_bits = bucket_size * 8  # Convert bytes to bits
        bucket_size_only_other_packets = bucket_size_bits
        max_delay_per_hop[link] = bucket_size_only_other_packets / datarate

    return max_delay_per_hop


def calculate_end_to_end_delays(queueing_delays, e_streams):
    processing_delay_s = 2000 * 1e-9  # 2000 ns in seconds
    propagation_delay_s = 200 * 1e-9
    datarate = 100 * 1e6  # 100 Mbps in bps

    delays = {}
    for stream in e_streams:
        delay = 0
        frame_size = stream['frame_size_byte'] * 8  # Convert bytes to bits
        for hop in stream['route']:
            link = (hop['from'], hop['to'])
            transmission_delay = frame_size / datarate
            delay += queueing_delays[link] + processing_delay_s + propagation_delay_s + transmission_delay
        delays[stream['id']] = delay
    return delays

if __name__ == "__main__":
    top_name = "t_3x4"
    run_name = "p_24/r_9"
    et_name = "et_24"

    top_folder = os.path.join(EVAL_PATH_SCHED, top_name)
    run_folder = os.path.join(top_folder, run_name)
    scenario_folder = os.path.join(run_folder, et_name)

    topology = parse_topology(top_folder + "/topology.json")
    e_streams = parse_emergency_streams(scenario_folder + "/streams_et.json")
    bucket_per_hop = calculate_bucket_size_per_hop(topology, e_streams)
    min_frame_size = min(stream['frame_size_byte'] for stream in e_streams)
    max_frame_size = max(stream['frame_size_byte'] for stream in e_streams)
    print(bucket_per_hop)
    queueing_delays = calculate_max_delay_per_hop(bucket_per_hop, min_frame_size, max_frame_size)
    print(queueing_delays)
    e2e_delays = calculate_end_to_end_delays(queueing_delays, e_streams)
    e2e_delays_us = {stream_id: delay * 1e6 for stream_id, delay in e2e_delays.items()}
    # Sort
    sorted_e2e_delays = dict(sorted(e2e_delays_us.items(), key=lambda item: item[1]))
    print(sorted_e2e_delays)
    pass