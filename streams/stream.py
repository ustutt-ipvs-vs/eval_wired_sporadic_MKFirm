import json
from typing import List, Dict, Any

import networkx as nx
from graph_tool import Vertex, Edge


class Stream:
    id: int
    name: str
    source: int
    target: int
    frame_size_byte: int
    cycle_time: int
    max_delay_ns: int

    def __init__(self, stream_id: int):
        self.id = stream_id
        self.name = "stream_{}".format(stream_id)

    @staticmethod
    def export_streams_to_json(streams, topology):

        stream_dict = {}
        for stream_id, stream in streams.items():
            stream_dict[stream_id] = {}

            if not isinstance(topology, nx.MultiDiGraph):
                # Graph-tool to dict
                stream_dict[stream_id]['source'] = int(topology.vp['v_id'][stream.source])
                stream_dict[stream_id]['target'] = int(topology.vp['v_id'][stream.target])
                # graph-tool: Convert edge object to triple (source, target, edge key


            # Relabelling
            stream_dict[stream_id]['cycle_time_ns'] = stream_dict[stream_id].pop('cycle_time')
            stream_dict[stream_id]['frame_size_b'] = stream_dict[stream_id].pop('size')
            stream_dict[stream_id]['max_delay_ns'] = stream_dict[stream_id].pop('max_delay')

        return json.dumps(stream_dict)
