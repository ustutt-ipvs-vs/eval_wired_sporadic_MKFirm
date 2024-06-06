from math import ceil

import graph_tool.all as gt

from stream import Stream


# TODO: this might need an update to consider each node's fwd_header_b instead stream.size and header_size (Eike)
def calc_nowait_e2e_delay(topology: gt.Graph, stream: Stream, route, round=False) -> int:
    """
    Calculates the e2e delay for a stream.
    """
    path_v = [stream.source] + [edge.target() for edge in route]
    time = 0
    for v in path_v:
        time += topology.vertex_properties['processing_delay_ns'][v]
    for e in route:
        time += topology.edge_properties['propagation_delay_ns'][e]
        time += int(ceil(stream.frame_size_byte * 8 / (topology.edge_properties['link_speed_mbps'][e] * 1e-3)))
    if round:
        return int(ceil(time / 1000) * 1000)
    else:
        return int(time)


def edge_to_unique_string(edge: gt.Edge):
    return str(edge.source()) + "-" + str(edge.target())


def unique_string_to_edge(g: gt.Graph, unique_string: str):
    split_parts = unique_string.split("-")
    edge = g.edge(split_parts[0], split_parts[1])
    return edge
