#!/usr/bin/env python3
import argparse
import json
import random
import os
from collections import defaultdict, abc
from typing import Dict
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout

try:
    from natsort import natsorted
except ImportError:
    natsorted = sorted

DEBUG = True

if DEBUG:
    import matplotlib.pyplot as plt


def grid_network(n, m):
    G = nx.grid_2d_graph(n, m)
    for n in G.nodes:
        G.nodes[n]['is_switch'] = True

    label_map = dict(zip(G.nodes, range(len(G.nodes))))
    G = nx.relabel_nodes(G, label_map)
    all_switches = set(G.nodes())

    for edge_node in all_switches:
        node_id = len(G.nodes)
        G.add_node(node_id)
        G.add_edge(node_id, edge_node)
        G.nodes[node_id]['is_switch'] = False

    return G


def calculate_positions(G):
    positions = graphviz_layout(G)

    min_x = min([positions[v][0] for v in positions.keys()])
    min_y = min([positions[v][1] for v in positions.keys()])
    max_x = max([positions[v][0] for v in positions.keys()])
    max_y = max([positions[v][1] for v in positions.keys()])
    preferred_min_x = 300
    preferred_min_y = 300
    preferred_max_x = 1000
    preferred_max_y = 1000
    scale_x = (preferred_max_x - preferred_min_x) / (max_x - min_x)
    scale_y = (preferred_max_y - preferred_min_y) / (max_y - min_y)
    normalized_positions = {}
    for v in positions.keys():
        normalized_positions[v] = (positions[v][0] * scale_x + preferred_min_x,
                                   positions[v][1] * scale_y + preferred_min_y)

    for v in G.nodes:
        G.nodes[v]['_ipvs_position'] = "{},{}".format(normalized_positions[v][0], normalized_positions[v][1])


def prepare_vertices_for_json_export(G, processing_delay_ns):
    vertices = {}
    for v0, v1 in G.edges():
        if v0 not in vertices.keys():
            vertices[v0] = create_dict_entry_for_vertex(G, v0, processing_delay_ns)
        if v1 not in vertices.keys():
            vertices[v1] = create_dict_entry_for_vertex(G, v1, processing_delay_ns)

    for node in G.nodes:
        if 'is_wireless' in G.nodes[node] and G.nodes[node]['is_wireless']:
            vertices[node] = create_dict_entry_for_vertex(G, node, processing_delay_ns)
    return vertices


def create_dict_entry_for_vertex(G, vertex, processing_delay_ns):
    is_switch: bool = ('is_switch' in G.nodes[vertex] and G.nodes[vertex]['is_switch'])
    entry = {
        'id': int(vertex),
        'name': 'n{}'.format(int(vertex)),
        'processing_delay_ns': processing_delay_ns if is_switch else 0,
        'is_switch': is_switch,
        'queues_per_port': 8,
        'position': G.nodes[vertex]['_ipvs_position']
    }
    return entry


def prepare_edges_for_json_export(G, propagation_delay_ns):
    edges = {}
    for v0, v1 in G.edges():
        # Set link speed depending on the type of the link

        link_speed_mbps = 100
        edges['_'.join([str(v0), str(v1)])] = {
            'id': len(edges),
            'name': '{}-{}'.format(v0, v1),
            'source': v0,
            'target': v1,
            'link_speed_mbps': link_speed_mbps,
            'propagation_delay_ns': propagation_delay_ns,
        }
        edges['_'.join([str(v1), str(v0)])] = {
            'id': len(edges),
            'name': '{}-{}'.format(v1, v0),
            'source': v1,
            'target': v0,
            'link_speed_mbps': link_speed_mbps,
            'propagation_delay_ns': propagation_delay_ns,
        }
    return edges


def write_to_json(G, output_file, processing_delay_ns, propagation_delay_ns, summary_report=None):
    if summary_report:
        if ('/') in output_file:
            summary_output = output_file.split("/")[:-1]
            summary_filename = output_file.split("/")[-1].split(".")[0]
            summary_output.append(f"{summary_filename}_summary.json")
            summary_file = "/".join(summary_output)
        else:
            summary_filename = output_file.split(".")[0]
            summary_file = f"{summary_filename}_summary.json"

        with open(summary_file, 'w') as sum_output_fd:
            json.dump(summary_report, sum_output_fd, indent=4, separators=(',', ': '))

    vertices = prepare_vertices_for_json_export(G, processing_delay_ns)
    edges = prepare_edges_for_json_export(G, propagation_delay_ns)

    json_output = {'nodes': natsorted(vertices.values(), key=lambda k: k['id']),
                   'links': [value for key, value in edges.items()]}

    with open(output_file, 'w') as output_fd:
        json.dump(json_output,
                  output_fd, indent=4, separators=(',', ': '))

    return json_output


def _relabel_nodes(G):
    return nx.relabel_nodes(G, dict(zip(list(G.nodes), range(G.number_of_nodes()))))


def assign_port_numbers(G):
    # port_mapping uses a node as the key
    # The value is another dict, where each key is the connected node and each value it the mapped port
    port_mapping: Dict[int, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
    for edge_source, edge_target in G.edges:
        # Find if mapped port already existing on edge_source.
        #   This automatically means, there is also a mapped port on edge_target
        # Otherwise map port
        if edge_target in port_mapping[edge_source]:
            port_at_source = port_mapping[edge_source][edge_target]
            port_at_target = port_mapping[edge_target][edge_source]
        else:
            port_at_source = len(port_mapping[edge_source])
            port_at_target = len(port_mapping[edge_target])
            port_mapping[edge_source][edge_target] = port_at_source
            port_mapping[edge_target][edge_source] = port_at_target

        G.edges[(edge_source, edge_target)]["out_port"] = port_at_source
        G.edges[(edge_source, edge_target)]["in_port"] = port_at_target


def debug_draw(G):
    pos = graphviz_layout(G)
    switches = list(filter(lambda node: G.nodes[node]['is_switch'] is True, G.nodes))
    remaining = set(G.nodes) - set(switches)
    nx.draw_networkx_nodes(G, pos, switches, node_color="tab:red")
    nx.draw_networkx_nodes(G, pos, remaining, node_color="tab:blue")

    nx.draw_networkx_labels(G, pos)
    nx.draw_networkx_edges(G, pos)
    plt.axis("off")
    plt.tight_layout()
    plt.show()


def main(nodes=500, line=False, ring=False, mesh=False, star=False, dumbbell=False, fat_tree=False, edge_core=False,
         minimal_backbone=False, factory_backbone=False,
         hierarchical_rings=False, grid=False, export_summary=False, output_path="testdir", output_is_dir=True,
         output_graphml=True, processing_delay_ns=2000,
         propagation_delay_ns=200, seed=None, seed_state=None):
    if seed_state:
        random.setstate(seed_state)
    elif seed:
        random.seed(seed)

    summary = None
    if grid:
        G = grid_network(nodes, nodes+1)

    calculate_positions(G)

    if DEBUG:
        debug_draw(G)

    assign_port_numbers(G)

    if not output_path:
        for edge in G.edges():
            print(edge[0], edge[1])
    else:
        if output_is_dir:
            if not os.path.exists(output_path):
                os.makedirs(output_path)
            output_path = os.path.join(output_path, 'topology')
        if export_summary:
            json_output = write_to_json(G, f'{output_path}.json', processing_delay_ns, propagation_delay_ns, summary)
        else:
            json_output = write_to_json(G, f'{output_path}.json', processing_delay_ns, propagation_delay_ns, None)
        G = nx.readwrite.json_graph.node_link_graph(json_output)
        if output_graphml:
            nx.write_graphml(G, f'{output_path}.graphml')

    return G
