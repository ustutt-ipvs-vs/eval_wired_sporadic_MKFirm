#!/usr/bin/python3

import argparse
import json
import random
import configparser
from typing import List

import graph_tool.all as gt

from streams.stream import Stream
from streams.stream_utils import calc_nowait_e2e_delay
from topology.topology import parse_topology

##############
# data loading
##############
# program arguments
parser = argparse.ArgumentParser()
parser.add_argument('-t', '--topology', type=str, required=True, help='Path to topology file')
parser.add_argument('-i', '--ini', type=str, required=True, help='Path to the ini file with the stream parameters')
parser.add_argument('-o', '--output', help='Output file', default='./examples/streams.json')

args = parser.parse_args()

# read config file
config = configparser.ConfigParser()
config.read(args.ini)

number_of_streams: int = int(config.get('generic', 'number_of_tt_streams'))
periods_ns: List[int] = [period_us * 1000 for period_us in json.loads(config.get('generic', 'periods'))]
min_frame_size_byte: int = int(config.get('generic', 'min_frame_size_byte'))
max_frame_size_byte: int = int(config.get('generic', 'max_frame_size_byte'))
max_delay_percentages: List[float] = json.loads(config.get('generic', 'max_delay_multiples'))

# read topology
topology = parse_topology(args.topology)
hosts: List[gt.Vertex] = [v for v in topology.vertices() if not topology.vp.is_switch[v]]


def generate_stream(stream_id):
    stream = Stream(stream_id)
    # todo consider enforcing a maximum frame size (i.e. MTU)
    stream.frame_size_byte = max(64, random.randint(min_frame_size_byte, max_frame_size_byte))
    stream.cycle_time_ns = random.choice(periods_ns)

    source_vertex = random.choice(hosts)
    stream.source = topology.vp["v_id"][source_vertex]
    target_vertex = random.choice([n for n in hosts if n != stream.source])
    stream.target = topology.vp["v_id"][target_vertex]

    route = gt.shortest_path(topology, stream.source, stream.target)[1]
    if not route:
        print(
            f'Warning: For source {stream.source} -> {stream.target}, there is no route')
        stream = None

    no_wait_e2e_delay = calc_nowait_e2e_delay(topology, stream, route, round=True)
    # enforce max delay = cycle time
    delay_percentage = min(1.0, random.choice(max_delay_percentages))
    max_slack = stream.cycle_time_ns - no_wait_e2e_delay
    stream.deadline_ns = max_slack * delay_percentage + no_wait_e2e_delay

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
for new_stream_id in range(number_of_streams):
    streams.append(generate_stream(new_stream_id))

with open(args.output, 'w') as output:
    json.dump(streams, output)
