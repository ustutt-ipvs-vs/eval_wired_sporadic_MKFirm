import sys
from math import ceil
from queue import PriorityQueue
from typing import Dict, List, Set

from network.network_graph import NetworkGraph
from network.network_elements import EgressPort
from streams.tt_stream import TtStream


def calculate_hop_delay_in_ns(network: NetworkGraph, egress_port: EgressPort, frame_size: int) -> int:
    return (egress_port.propagation_delay_ns +
            egress_port.calculate_transmission_delay_in_ns_of(frame_size) +
            network.get_node(egress_port.destination_node).processing_delay_ns)


def get_dijkstra_shortest_path(source: int, destination: int, network: NetworkGraph, frame_size: int = 1) \
        -> List[EgressPort]:
    egress_port_from_predecessor: Dict[int, EgressPort] = {}

    # holds distance, node tuples. This ordering, since it is ordered by the first entry first
    frontier_queue = PriorityQueue()

    frontier_distances: Dict[int, int] = {}
    for node_id in network.get_node_ids():
        frontier_distances[node_id] = sys.maxsize

    frontier_distances[source] = 0
    frontier_queue.put((0, source))

    checked_nodes: Set[int] = set()
    # expand nodes
    while not frontier_queue.empty():
        current_distance, current_node = frontier_queue.get()

        if frontier_distances[destination] < current_distance:
            # useless path
            continue

        # this filters already expanded nodes, since we add duplicates in emplace
        if not checked_nodes.__contains__(current_node):

            egress_port: EgressPort
            for egress_port in network.get_node(current_node).ports:
                next_hop: int = egress_port.destination_node
                edge_cost: int = calculate_hop_delay_in_ns(network, egress_port, frame_size)
                distance_to_next_hop: int = frontier_distances[current_node] + edge_cost

                if distance_to_next_hop < frontier_distances[next_hop]:
                    frontier_distances[next_hop] = distance_to_next_hop
                    egress_port_from_predecessor[next_hop] = egress_port
                    # update frontier_queue, note that this can add duplicates with lower frontier_distances
                    frontier_queue.put((distance_to_next_hop, next_hop))

            # end of egress_port loop
            checked_nodes.add(current_node)
    # end of frontier_queue loop

    if frontier_distances[destination] == sys.maxsize:
        raise Exception("No path found from " + str(source) + " to " + str(destination))

    # extract path
    path: List[EgressPort] = []
    current_node: int = destination
    while current_node != source:
        current_port = egress_port_from_predecessor[current_node]
        path.append(current_port)
        current_node = current_port.host_node

    path.reverse()
    return path


def route_to_json_ready(route: List[EgressPort]):
    output = []
    for egress_port in route:
        output.append({'id': int(egress_port.id),
                       'name': str(egress_port.name),
                       'from': int(egress_port.host_node),
                       'to': int(egress_port.destination_node)})
    return output


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
