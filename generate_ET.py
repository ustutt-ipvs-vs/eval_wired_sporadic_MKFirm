import json
import os.path
import random
from typing import List, Tuple

import numpy as np

from network import network_graph
from streams.et_stream import EtStream


##########
# topology
##########
def main(topology, config, output, tt_streams=None, force_host=None):
    if not os.path.isfile(topology):
        raise FileNotFoundError
    topology = network_graph.NetworkGraph(topology)

    number_of_streams: int = int(config.get('generic', 'number_of_emergency_streams'))

    random_et_streams: bool = tt_streams is None
    if random_et_streams:
        min_bucket_size_byte = int(config.get('random ET values', 'min_bucket_size_byte'))
        max_bucket_size_byte = int(config.get('random ET values', 'max_bucket_size_byte'))
        step_bucket_size_byte = int(config.get('random ET values', 'step_bucket_size_byte'))
        bucket_sizes_byte = np.arange(min_bucket_size_byte, max_bucket_size_byte, step_bucket_size_byte)

        frame_sizes_byte: List[int] = json.loads(config.get('random ET values', 'frame_sizes_in_byte'))
        min_inter_event_times_us: List[int] = json.loads(config.get('random ET values', 'min_inter_event_time_us'))

    ################
    # create streams
    ################
    emergency_streams = []
    if random_et_streams:
        for i in range(0, number_of_streams):
            emergency_streams.append(create_random_emergency_stream(i, topology, frame_sizes_byte, min_inter_event_times_us, force_host))

    with open(output, 'w') as output_file:
        output_file.write(json.dumps(emergency_streams, indent=4))



def get_random_source_and_target(device_ids, force_host=None) -> Tuple[int, int]:
    if force_host is not None:
        source = force_host
    else:
        source = random.choice(device_ids)
    target = random.choice([d_id for d_id in device_ids if d_id != source])
    return source, target


def create_random_emergency_stream(stream_id: int, topology, frame_sizes_byte, min_inter_event_times_us, force_host=None) -> dict:
    et_stream = EtStream(stream_id)

    frame_size = random.choice(frame_sizes_byte)
    min_inter_event_time_ns = random.choice(min_inter_event_times_us) * 1000
    et_stream.set_and_calculate_bucket_attributes(frame_size, min_inter_event_time_ns)

    device_ids: List[int] = topology.get_end_device_ids()
    source, target = get_random_source_and_target(device_ids, force_host)
    et_stream.set_and_calculate_route(source, target, topology)

    return et_stream.to_json()
