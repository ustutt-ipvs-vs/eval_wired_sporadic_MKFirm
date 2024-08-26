from math import ceil

from emergency_streams.network.Routing import calculate_hop_delay_in_ns
from emergency_streams.network.network_elements import EgressPort

from emergency_streams.network.network_graph import NetworkGraph
from tt_stream import TtStream


# TODO: this might need an update to consider each node's fwd_header_b instead stream.size and header_size (Eike)
def calc_nowait_e2e_delay(topology: NetworkGraph, stream: TtStream, route, round=False) -> int:
    """
    Calculates the e2e delay for a stream.
    """
    time = 0
    link: EgressPort
    for link in route:
        time += calculate_hop_delay_in_ns(topology, link, stream.frame_size_byte)

    if round:
        return int(ceil(time / 1000) * 1000)
    else:
        return int(time)
