#!/usr/bin/python3

import argparse
import json
import random
import configparser
import os.path
from typing import List

from streams.tt_stream import TtStream
from network.Routing import calc_nowait_e2e_delay, get_dijkstra_shortest_path
from network.network_graph import NetworkGraph

##############
# data loading
##############
# program arguments
parser = argparse.ArgumentParser()
parser.add_argument('-t', '--topology', type=str, required=True, help='Path to topology file')
parser.add_argument('-i', '--ini', type=str, required=True, help='Path to the ini file with the stream parameters')
parser.add_argument('-o', '--output', help='Output file', default='examples/streams.json')

args = parser.parse_args()

# read config file
config = configparser.ConfigParser()
if not os.path.isfile(args.ini):
    raise FileNotFoundError
config.read(args.ini)

number_of_streams: int = int(config.get('generic', 'number_of_tt_streams'))
periods_ns: List[int] = [period_us * 1000 for period_us in json.loads(config.get('generic', 'periods_in_us'))]
frame_sizes_in_byte: List[int] = json.loads(config.get('generic', 'frame_sizes_in_byte'))
max_delay_percentages: List[float] = json.loads(config.get('generic', 'max_delay_percentage'))

et_capable_portion: float = float(config.get('generic', 'et_capable_portion'))
first_stream_id: int = int(config.get('generic', 'first_stream_id'))

# read topology
if not os.path.isfile(args.topology):
    raise FileNotFoundError
topology = NetworkGraph(args.topology)
hosts: List[int] = topology.get_end_device_ids()


def generate_stream(stream_id):
    stream = TtStream(stream_id)
    # todo consider enforcing a maximum frame size (i.e. MTU)
    stream.frame_size_byte = max(64, random.choice(frame_sizes_in_byte))
    stream.cycle_time_ns = random.choice(periods_ns)

    stream.source = random.choice(hosts)
    stream.target = random.choice([n for n in hosts if n != stream.source])

    stream.et_capable = random.random() < et_capable_portion

    route = get_dijkstra_shortest_path(stream.source, stream.target, topology)
    if not route:
        print(
            f'Warning: For source {stream.source} -> {stream.target}, there is no route')
        stream = None

    no_wait_e2e_delay = calc_nowait_e2e_delay(topology, stream, route, round=True)
    # enforce max delay = cycle time
    delay_percentage = min(1.0, random.choice(max_delay_percentages))
    max_slack = stream.cycle_time_ns - no_wait_e2e_delay
    stream.deadline_ns = int(max_slack * delay_percentage + no_wait_e2e_delay)

    # prevent rounding issues
    if delay_percentage == 0.0:
        stream.deadline_ns = no_wait_e2e_delay
    elif delay_percentage == 1.0:
        stream.deadline_ns = stream.cycle_time_ns

    return stream


#############
# actual work
#############
streams = []
for new_stream_id in range(first_stream_id, first_stream_id + number_of_streams):
    streams.append(generate_stream(new_stream_id))

with open(args.output, 'w') as output:
    json.dump([s.to_json() for s in streams], output, indent=4)
