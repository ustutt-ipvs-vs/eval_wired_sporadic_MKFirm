import argparse
import json
import random
import configparser
import os.path
import numpy as np

from typing import List

import network.network_graph
import network.Routing

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--topology', help='path to the topology file', type=str, required=True)
parser.add_argument('-i', '--ini', help='path to the ini file with the stream parameters', type=str, required=True)
parser.add_argument('-o', '--output', help='path to the output file', type=str, default='examples/emergency_streams.json')

args = parser.parse_args()
##########
# topology
##########
if not os.path.isfile(args.topology):
    raise FileNotFoundError
topology = network.network_graph.NetworkGraph(args.topology)
device_ids: List[int] = topology.get_end_device_ids()

########
# config
########
config = configparser.ConfigParser()
if not os.path.isfile(args.ini):
    raise FileNotFoundError
config.read(args.ini)

number_of_streams: int = int(config.get('generic', 'number_of_emergency_streams'))

buffer_sizes = np.arange(int(config.get('buffer size', 'min_buffer_size')),
                         int(config.get('buffer size', 'max_buffer_size')),
                         int(config.get('buffer size', 'step_buffer_size')))
data_rate = np.arange(int(config.get('rate', 'min_rate')),
                      int(config.get('rate', 'max_rate')),
                      int(config.get('rate', 'step_rate')))


def get_random_source_and_target() -> (int, int):
    source = random.choice(device_ids)
    target = random.choice([d_id for d_id in device_ids if d_id != source])
    return source, target


def create_random_emergency_stream(stream_id: int):
    source, target = get_random_source_and_target()
    rate = random.choice(data_rate)
    buffer_size = random.choice(buffer_sizes)

    route = network.Routing.get_dijkstra_shortest_path(source, target, topology)

    return {'streamID': int(stream_id), 'source': int(source), 'target': int(target), 'data_rate': int(rate),
            'buffer_size': int(buffer_size), 'route': network.Routing.route_to_json_ready(route)}


################
# create streams
################
emergency_streams = []
for i in range(0, number_of_streams):
    emergency_streams.append(create_random_emergency_stream(i))

with open(args.output, 'w') as output_file:
    output_file.write(json.dumps(emergency_streams, indent=4))
