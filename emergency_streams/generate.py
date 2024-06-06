import argparse
import json
import random
import configparser
import numpy as np

from typing import List

import network.network_graph
import network.Routing

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--topology', help='path to the topology file', type=str, required=True)
parser.add_argument('-i', '--ini', help='path to the ini file with the stream parameters', type=str, required=True)
parser.add_argument('-o', '--output', help='path to the output file', type=str, default='emergency_streams.json')

args = parser.parse_args()
##########
# topology
##########
topology = network.network_graph.NetworkGraph(args.topology)
device_ids: List[int] = topology.get_node_ids()

########
# config
########
config = configparser.ConfigParser()
config.read(args.ini)

number_of_streams: int = int(config.get('generic', 'number_of_emergency_streams'))

buffer_sizes = np.arange(int(config.get('buffer size', 'min_buffer_size')),
                         int(config.get('buffer size', 'max_buffer_size')),
                         int(config.get('buffer size', 'buffer_size_step')))
data_rate = np.arange(int(config.get('rate', 'min_rate')),
                      int(config.get('rate', 'max_rate')),
                      int(config.get('rate', 'rate_step')))


def get_random_source_and_destination() -> (int, int):
    source = random.choice(device_ids)
    destination = random.choice([d_id for d_id in device_ids if d_id != source])
    return source, destination


def create_random_emergency_stream(stream_id: int):
    source, destination = get_random_source_and_destination()
    rate = random.choice(data_rate)
    buffer_size = random.choice(buffer_sizes)

    route = network.Routing.get_dijkstra_shortest_path(source, destination, topology)

    return {'streamID': stream_id, 'source': source, 'destination': destination, 'data rate': rate,
            'buffer size': buffer_size, 'route': network.Routing.route_to_json_ready(route)}


################
# create streams
################
emergency_streams = []
for i in range(0, number_of_streams):
    emergency_streams.append(create_random_emergency_stream(i))

with open(args.output, 'w') as output_file:
    output_file.write(json.dumps(emergency_streams, indent=4))
