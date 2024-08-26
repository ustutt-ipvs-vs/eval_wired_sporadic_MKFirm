import argparse
import json
import random
import configparser
import os.path
import numpy as np

from typing import List

import streams.tt_stream
from streams.et_stream import EtStream, from_tt_stream
from network import network_graph

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--topology', help='path to the topology file', type=str, required=True)
parser.add_argument('-s', '--tt_streams',
                    help='path to the tt streams file. If set, the TT streams will be used as template (if they have the proper flag set). Otherwise ET streams are created randomly.',
                    type=str, required=False)
parser.add_argument('-i', '--ini', help='path to the ini file with the stream parameters', type=str, required=True)
parser.add_argument('-o', '--output', help='path to the output file', type=str,
                    default='examples/emergency_streams.json')

args = parser.parse_args()
##########
# topology
##########
if not os.path.isfile(args.topology):
    raise FileNotFoundError
topology = network_graph.NetworkGraph(args.topology)
device_ids: List[int] = topology.get_end_device_ids()

########
# config
########
config = configparser.ConfigParser()
if not os.path.isfile(args.ini):
    raise FileNotFoundError
config.read(args.ini)

number_of_streams: int = int(config.get('generic', 'number_of_emergency_streams'))

random_et_streams: bool = args.tt_streams is None
if random_et_streams:
    min_bucket_size_byte = int(config.get('random ET values', 'min_bucket_size_byte'))
    max_bucket_size_byte = int(config.get('random ET values', 'max_bucket_size_byte'))
    step_bucket_size_byte = int(config.get('random ET values', 'step_bucket_size_byte'))
    bucket_sizes_byte = np.arange(min_bucket_size_byte, max_bucket_size_byte, step_bucket_size_byte)

    frame_sizes_byte: List[int] = json.loads(config.get('random ET values', 'frame_sizes_in_byte'))
    survival_times_us: List[int] = json.loads(config.get('random ET values', 'survival_times_us'))


def get_random_source_and_target() -> (int, int):
    source = random.choice(device_ids)
    target = random.choice([d_id for d_id in device_ids if d_id != source])
    return source, target


def create_random_emergency_stream(stream_id: int):
    assert random_et_streams
    et_stream = EtStream(stream_id)

    frame_size = random.choice(frame_sizes_byte)
    survival_time_ns = random.choice(survival_times_us) * 1000
    et_stream.set_and_calculate_bucket_attributes(frame_size, survival_time_ns)

    source, target = get_random_source_and_target()
    et_stream.set_and_calculate_route(source, target, topology)

    return et_stream.to_json()


def create_emergency_streams_based_on_tt_streams():
    et_streams: List[EtStream] = []

    with open(args.tt_streams, 'r') as tt_stream_file:
        tt_streams = [streams.tt_stream.from_json(s) for s in json.load(tt_stream_file) if s['et_capable']]

    if len(tt_streams) < number_of_streams:
        raise ValueError('Not enough TT streams available to create the requested number of emergency streams.')
    for stream_id in range(0, number_of_streams):
        tt_stream = random.choice(tt_streams)
        tt_streams.remove(tt_stream)

        et_stream = from_tt_stream(tt_stream, stream_id, topology)
        et_streams.append(et_stream)

    return [et.to_json() for et in et_streams]


################
# create streams
################
emergency_streams = []
if random_et_streams:
    for i in range(0, number_of_streams):
        emergency_streams.append(create_random_emergency_stream(i))
else:
    emergency_streams = create_emergency_streams_based_on_tt_streams()

with open(args.output, 'w') as output_file:
    output_file.write(json.dumps(emergency_streams, indent=4))
