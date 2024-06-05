from math import ceil
from typing import List
from collections import defaultdict

import graph_tool.all as gt

from streams.stream import Stream


# TODO: this might need an update to consider each node's fwd_header_b instead stream.size and header_size (Eike)
def calc_e2e_delay(topology: gt.Graph, stream, alpha: [float, int], cut_through, header_size=30, round=False) -> int:
    """
    Calculates the e2e delay for a stream.
    """
    # simulator = PacketSimulator(topology, is_cut_trough=cut_through, verbose=False)
    # simulator.add_packets([stream])
    # simulator.execute_simulation()
    # with open("packet_history_list.bin", 'rb') as pickle_file:
    #     packet_history_list = pickle.load(pickle_file)
    # # e2e is timestamp of last event of simulation
    # time = packet_history_list[0][-1][0]
    path_v = [stream.route[0].source()] + [edge.target() for edge in stream.route]
    time = 0
    for v in path_v:
        time += topology.vertex_properties['processing_delay_ns'][v]
    for e in stream.route:
        time += topology.edge_properties['propagation_delay_ns'][e]
        # header is 41 B
        time += int(ceil((stream.size + header_size) * 8 / (topology.edge_properties['link_speed_mbps'][e] * 1e-3)))
    if round:
        return int(ceil(time * alpha / 1000) * 1000)
    else:
        return time * alpha


def calculate_potential_shortest_path(g: gt.Graph, stream: Stream):
    """

    :param g:               Topology graph
    :param stream:          Stream to calculate potential path for
    :param s_settings:      Scheduler settings
    :param shortest_path:   If true only returns the shortest path (Requires all_paths to be false)
    :param all_paths:       If true calculates all possible paths matching other given requirements (@see use_cutoff)
                                Requires shortest_path to be false
    :param use_cutoff:      Cutoff all possible paths to a maximum length of the graphs diameter

    :return: Tuple[Set[gt.Vertex], Set[gt.Edge]]
                            Returns a tuple containing a set of all possible vertices and edges
    """
    paths_v, path_edges = list(gt.shortest_path(g, stream.source, stream.target))
    paths_v = [paths_v]
    stream.state["path_to_schedule"] = path_edges

    # Sort paths by len
    paths_v.sort(key=len)
    # Compute set of potential edges
    edges = {g.edge(source, target) for path_vertices in paths_v
             for source, target in zip(path_vertices, path_vertices[1:])}
    # Compute set of potential vertices
    vertices = {g.vertex(path_vertex) for path_vertices in paths_v for path_vertex in path_vertices}

    return vertices, edges


def calculate_all_potential_paths(g: gt.Graph, stream: Stream, use_cutoff=False):
    """

    :param g:               Topology graph
    :param stream:          Stream to calculate potential path for
    :param shortest_path:   If true only returns the shortest path (Requires all_paths to be false)
    :param all_paths:       If true calculates all possible paths matching other given requirements (@see use_cutoff)
                                Requires shortest_path to be false
    :param use_cutoff:      Cutoff all possible paths to a maximum length of the graphs diameter

    :return: Tuple[Set[gt.Vertex], Set[gt.Edge]]
                            Returns a tuple containing a set of all possible vertices and edges
    """
    paths_v: List = []
    if use_cutoff:
        global_cutoff = gt.pseudo_diameter(g)[0] * 2
        # Compute all paths < global_cutoff
        paths_v = list(gt.all_paths(g, stream.source, stream.target, cutoff=global_cutoff))
    else:
        paths_v = list(gt.all_paths(g, stream.source, stream.target))

    # Sort paths by len
    paths_v.sort(key=len)
    # Compute set of potential edges
    edges = {g.edge(source, target) for path_vertices in paths_v
             for source, target in zip(path_vertices, path_vertices[1:])}
    # Compute set of potential vertices
    vertices = {g.vertex(path_vertex) for path_vertices in paths_v for path_vertex in path_vertices}

    return (vertices, edges)


def edge_to_unique_string(edge: gt.Edge):
    return str(edge.source()) + "-" + str(edge.target())


def unique_string_to_edge(g: gt.Graph, unique_string: str):
    split_parts = unique_string.split("-")
    edge = g.edge(split_parts[0], split_parts[1])
    return edge
