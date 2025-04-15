from dataclasses import dataclass
from typing import List

import streams.tt_stream
from network import Routing
from network.network_graph import NetworkGraph
from network.network_elements import EgressPort


@dataclass
class EtStream:
    stream_id: int
    tt_stream_id: int
    name: str
    source: int
    target: int
    rate_mbps: float
    bucket_size_byte: int
    route: List[EgressPort]
    frame_size_byte: int
    min_inter_event_time_ns: int

    def __init__(self, stream_id: int):
        self.stream_id = stream_id
        self.name = "stream_{}".format(stream_id)
        self.tt_stream_id = -1

    def to_json(self):
        return {'id': int(self.stream_id),
                'ttStreamID': int(self.tt_stream_id),
                'name': 'emergency_stream_{}'.format(self.stream_id),
                'source': int(self.source),
                'target': int(self.target),
                'rate_mbps': float(self.rate_mbps),
                'bucket_size_byte': int(self.bucket_size_byte),
                'frame_size_byte': int(self.frame_size_byte),
                'min_inter_event_time_ns': int(self.min_inter_event_time_ns),
                'route': Routing.route_to_json_ready(self.route)}

    def set_and_calculate_bucket_attributes(self, frame_size_byte: int, min_inter_event_time_ns):
        self.frame_size_byte = frame_size_byte
        self.min_inter_event_time_ns = min_inter_event_time_ns
        self.bucket_size_byte = self.frame_size_byte
        # byte/ns = kByte/us = MByte/ms -> /1000 for MByte/s
        self.rate_mbps = self.bucket_size_byte / (1000 * self.min_inter_event_time_ns)

    def set_and_calculate_route(self, source: int, target: int, topology: NetworkGraph):
        self.source = source
        self.target = target
        self.route = Routing.get_dijkstra_shortest_path(self.source, self.target, topology)


def from_tt_stream(tt_stream: streams.tt_stream.TtStream, stream_id: int, topology: NetworkGraph) -> EtStream:
    et_stream = EtStream(stream_id)
    et_stream.tt_stream_id = tt_stream.id

    et_stream.set_and_calculate_route(tt_stream.source, tt_stream.target, topology)
    et_stream.set_and_calculate_bucket_attributes(tt_stream.frame_size_byte, tt_stream.cycle_time_ns * 3)

    return et_stream
