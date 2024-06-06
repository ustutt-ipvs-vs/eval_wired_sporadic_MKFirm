#!/usr/bin/env python3
import argparse
import json
import math
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


def edge_core_graph(n=50, p_add_edge=0.33, add_edge_node_degree=2, add_edge_path_len=4):
    G = nx.random_tree(n)

    non_leaf_nodes = set(node for node, degree in G.degree() if add_edge_node_degree <= degree)

    for node in non_leaf_nodes:
        if random.random() > p_add_edge:
            rewiring_candidates = non_leaf_nodes.copy().difference({node})
            path_len_root = len(nx.shortest_path(G, 0, node))
            rewiring_candidates = set(filter(
                lambda candidate: abs(len(nx.shortest_path(G, 0, candidate)) - path_len_root) < add_edge_path_len,
                rewiring_candidates))

            G.add_edge(node, random.sample(rewiring_candidates, 1)[0])

    return G


def mesh_topology(rows, cols, r_conn=1, c_conn=1):
    # rows: number of horizontal lines
    # cols: number of vertical lines
    # r_conn: horizontal connection every r_conn rows
    # c_conn: vertical connection every c_conn cols
    # r_conn/c_conn can be iterables to define the rows/cols with connectivity

    # switches are usually placed with a distance of 1
    hs_dist = 0.8  # desired host - switch distance
    s_fmt = '{}'
    h_fmt = '{}'

    if not isinstance(r_conn, abc.Iterable):
        r_conn = range(0, rows, r_conn)
    if not isinstance(c_conn, abc.Iterable):
        c_conn = range(0, cols, c_conn)
    r_conn = set(int(x) for x in r_conn if x >= 0 and x < rows)
    c_conn = set(int(x) for x in c_conn if x >= 0 and x < cols)

    a = hs_dist / 1.41  # x/y shift for the desired host - switch distance
    h = rows * cols

    g = nx.Graph()
    for row in range(rows):
        r_nodes = range(cols) if row in r_conn else c_conn
        r_switches = [s_fmt.format(i + row * cols) for i in r_nodes]
        r_hosts = [h_fmt.format(h + i + row * cols) for i in r_nodes]
        for i, switch, host in zip(r_nodes, r_switches, r_hosts):
            g.add_node(switch, is_switch=True, pos=[i, -row])
            g.add_node(host, is_switch=False, pos=[round(i - a, 2), round(-row + a, 2)])
            g.add_edge(switch, host)
        if row in r_conn:
            nx.add_path(g, r_switches)

    for col in c_conn:
        nx.add_path(g, (s_fmt.format(i) for i in range(col, h, cols)))

    g.graph['path_length_cutoff_abs'] = 2 * (rows - 1) + 2 * (cols - 1)
    g.graph['path_length_cutoff_rel'] = 3

    return g


def two_porter_ring(n):
    """
    Creates a ring of switches with one host at every switch.
    :param n: Number of switches
    :return:
    """
    # add switches
    G = nx.cycle_graph(n)
    for n in G.nodes:
        G.nodes[n]['is_switch'] = True
    # add hosts
    nodes = list(G.nodes)
    for ring_node in nodes:
        node_id = len(G.nodes)
        G.add_node(node_id)
        G.nodes[node_id]['is_switch'] = False
        G.add_edge(ring_node, node_id)
    return G


def ring(n, global_no_switches):
    """
    Creates a ring of switches
    :param n: Number of switches
    :param global_no_switches: Number of switches in whole topology (needed for globally unique names)
    """
    G = nx.cycle_graph(n)
    for n in G.nodes:
        G.nodes[n]['is_switch'] = True
    G = nx.relabel_nodes(G, lambda label: label + global_no_switches)
    return G


def two_porter_line(n):
    G = nx.Graph()
    # add switches on line
    G.add_node(0)
    G.nodes[0]['is_switch'] = True
    for n in range(1, n):
        G.add_node(n)
        G.nodes[n]['is_switch'] = True
        G.add_edge(n - 1, n)
    # add hosts
    nodes = list(G.nodes)
    for line_node in nodes:
        node_id = len(G.nodes)
        G.add_node(node_id)
        G.nodes[node_id]['is_switch'] = False
        G.add_edge(line_node, node_id)
    return G


def build_hierarchical_ring_struct_from_node_no(no_nodes):
    ratio_of_backbone_switches = random.randrange(10, 30, step=5) / 100
    no_of_backbone_switches = int(ratio_of_backbone_switches * no_nodes)
    no_nodes -= no_of_backbone_switches
    no_of_switches_per_ring = 0
    while no_of_backbone_switches * no_of_switches_per_ring <= no_nodes:
        no_of_switches_per_ring += 1
    no_of_switches_per_ring -= 1
    return [(1, no_of_backbone_switches), (no_of_backbone_switches, no_of_switches_per_ring)]


def hierarchical_rings_rec(no_switch_nodes, n=0, level_rings=[(1, 4), (4, 3)], level=0, no=0):
    print(level_rings)
    amount, nodes = level_rings[0]
    # don't know what amount does
    # nodes = number of nodes for current ring
    level_rings.remove((amount, nodes))

    G = ring(nodes, n)
    # increment global number of switches to name nodes globally uniquely
    n += nodes
    # ring id to distinguish nodes from different rings
    for node in G.nodes:
        G.nodes[node]['gw_cluster_id'] = no
    no += 1
    # G = nx.relabel_nodes(G, lambda label: '{}_{}_{}_{}'.format(random.randrange(0, 1000), level, no, label))

    if len(level_rings) > 0:
        # number of lower rings
        no_lower_nodes = level_rings[0][0]
        # number of nodes in lower rings
        no_lower_nodes_nodes = level_rings[0][1]

        # number of lower rings can't be higher than number of nodes in current ring
        if nodes < no_lower_nodes:
            print('Error not enough higher levels gateways!', nodes, no_lower_nodes)
            return -1

        # current ring nodes
        higher_level_gw = list(G.nodes)[-no_lower_nodes:]

        lower_rings = []

        for i in range(no_lower_nodes):
            lower_rings.append(
                hierarchical_rings_rec(no_switch_nodes, n=n, level_rings=level_rings.copy(), level=level + 1, no=no))
            # increment global number of nodes
            n += no_lower_nodes_nodes
            no += 1

        for lower_ring in lower_rings:
            if lower_ring != -1:
                print(lower_ring.nodes)
                G = nx.union(G, lower_ring)
                # need to connect via switch to higher ring, ot via host
                lower_ring_node = random.choice(list(lower_ring.nodes))
                while lower_ring.degree[lower_ring_node] <= 1:
                    lower_ring_node = random.choice(list(lower_ring.nodes))
                # Remove host on gateway node
                for n in G.neighbors(lower_ring_node):
                    if not G.nodes[n]['is_switch']:
                        G.remove_node(n)
                        break
                G.add_edge(higher_level_gw.pop(), lower_ring_node)

    else:
        no = no - 1
        # if this is lowest ring add host nodes
        nodes = list(G.nodes)
        for ring_node in nodes:
            h_name = no_switch_nodes + ring_node
            G.add_node(h_name)
            G.nodes[h_name]['is_switch'] = False
            G.add_edge(ring_node, h_name)
            G.nodes[h_name]['gw_cluster_id'] = no
    return G


def grid(n, m):
    G = nx.grid_2d_graph(n, m)

    label_map = dict(zip(G.nodes, range(len(G.nodes))))
    G = nx.relabel_nodes(G, label_map)
    edge_nodes = set(node for node, degree in G.degree() if degree <= 3)

    for edge_node in edge_nodes:
        node_id = len(G.nodes)
        G.add_node(node_id)
        G.add_edge(node_id, edge_node)

    return G


def star_topology(n):
    G = nx.Graph()

    G.add_node(0)
    G.nodes[0]['is_switch'] = True

    for node_id in range(1, n):
        G.add_node(node_id)
        G.nodes[node_id]['is_switch'] = False
        G.add_edge(node_id, 0)

    return G


def dumbbell_topology(n):
    # two stars with link between both switches
    #   n/2 -2 nodes in every star
    n = 2 if n < 2 else n

    G = nx.Graph()

    G.add_node(0)
    G.nodes[0]['is_switch'] = True

    G.add_node(1)
    G.nodes[1]['is_switch'] = True
    G.add_edge(0, 1)
    n_half_hosts = int((n - 2) / 2)

    for node_id in range(2, n_half_hosts + 2):
        G.add_node(node_id)
        G.nodes[node_id]['is_switch'] = False
        G.add_edge(node_id, 0)

    for node_id in range(n_half_hosts + 2, n):
        G.add_node(node_id)
        G.nodes[node_id]['is_switch'] = False
        G.add_edge(node_id, 1)

    return G


def fat_tree_topology(n, k=None):
    '''
    :param n: nodes ~ hosts
    :param k: number of ports each switch contains; if not set it is automatically set depending on node size
    :return: NetworkX graph
    '''
    G = nx.Graph()
    # max hosts = k^3 / 4 --> cubic root(n * 4) = k
    k_calc = (n * 4) ** (1. / 3.)
    # if e.g. k is 3.4 we increment
    k_calc = int(k_calc) if int(k_calc) == k_calc else int(k_calc) + 1

    # if k not set or to small take calculated k
    k = k_calc if not k or k < k_calc else k
    # for simplicity take only even values for nr of ports
    k = k if k % 2 == 0 else k + 1

    # number core switches is (k/2)^2 core switches
    core_switches = int((k / 2) * (k / 2))

    # number of pods  = k ; half of them aggregation switches and edge_switches
    pods = k
    agg_edge_switches = k / 2
    agg_edge_switches = int(agg_edge_switches) if int(agg_edge_switches) == agg_edge_switches else int(
        agg_edge_switches) + 1

    # each agg_switch within pod is connected to k/2 core_switches and k/2 edge_switches
    # each edge_switch is connected to max k/2 nodes

    # create switches
    for c in range(0, core_switches):
        t = "c" + str(c)
        G.add_node(t)
        G.nodes[t]['is_switch'] = True

    for p in range(0, pods):
        # add agg switches for current pod
        for a in range(0, agg_edge_switches):
            t = "p" + str(p) + "a" + str(a)
            G.add_node(t)
            G.nodes[t]['is_switch'] = True

        # add edge switches for current pod
        for e in range(0, agg_edge_switches):
            t = "p" + str(p) + "e" + str(e)
            G.add_node(t)
            G.nodes[t]['is_switch'] = True

            # add edges between edge and agg switches
            for a in range(0, agg_edge_switches):
                G.add_edge(t, "p" + str(p) + "a" + str(a))

        # core switches have the first node ids
        for i in range(0, core_switches):
            G.add_edge("c" + str(i), "p" + str(p) + "a" + str(i // agg_edge_switches))

    # nodes
    i = 0
    for a in range(0, int(k / 2)):  # hosts at every edge switch
        for e in range(0, agg_edge_switches):  # edge switches
            for p in range(0, pods):  # pods
                if i < n:
                    G.add_node(i)
                    G.nodes[i]['is_switch'] = False
                    G.add_edge(i, "p" + str(p) + "e" + str(e))
                    i += 1

    G.graph['path_length_cutoff_rel'] = 1

    return _relabel_nodes(G)


def get_hybrid_graph_input_from_node_no(no_switches):
    """
    Generates the input for hierarchical_hybrid_graph() from a given number of switches.
    """
    ratio_no_of_subtop_nodes = 0.05
    tree_n = 2
    no_nodes = (tree_n + int(0.25 * tree_n ** 2)) * int(ratio_no_of_subtop_nodes * no_switches) + tree_n * 2
    while no_nodes < no_switches:
        cut_off = 1.5 / tree_n
        if no_nodes < cut_off * no_switches:
            tree_n += 1
        else:
            ratio_no_of_subtop_nodes += 0.005
        no_nodes = (tree_n + int(0.25 * tree_n ** 2)) * int(ratio_no_of_subtop_nodes * no_switches) + tree_n * 2
    return tree_n, int(ratio_no_of_subtop_nodes * no_switches), (tree_n + int(0.25 * tree_n ** 2)) * int(
        ratio_no_of_subtop_nodes * no_switches) + tree_n * 2


def test_input():
    for i in range(50, 3000, 50):
        _, _, no_nodes = get_hybrid_graph_input_from_node_no(i)
        if abs(no_nodes - i) > 0.025 * i:
            print(f"F - target: {i} actual: {no_nodes}")
        else:
            print(f"T - target: {i} actual: {no_nodes}")


def hierarchical_hybrid_graph(tree_n, backbone_n, min_size, max_size, thin_random=True):
    # Create balanced tree, nodes in tree will be replaced by lines or rings
    base_graph = nx.balanced_tree(tree_n, 2)
    total_subrings = 0
    total_sublines = 0

    # get first level nodes (needed later), first level nodes have degree tree_n + 1
    first_level_nodes = [node for node, degree in base_graph.degree() if degree == tree_n + 1]
    # Select nodes for thinning out balanced tree (only leaf nodes are thinned, keep 25% of leaf nodes)
    number_of_leaf_nodes = tree_n ** 2
    leaf_nodes = [node for node, degree in base_graph.degree() if degree == 1]
    if not thin_random:
        while len(leaf_nodes) > number_of_leaf_nodes * 0.25:
            to_remove = random.choice(leaf_nodes)
            leaf_nodes.remove(to_remove)
            base_graph.remove_node(to_remove)
    # keep legacy thinning
    else:
        to_remove = [node for node in leaf_nodes if random.random() < 0.75]
        base_graph.remove_nodes_from(to_remove)
        leaf_nodes = list(set(leaf_nodes) - set(to_remove))
    # replace nodes in base_graph with subtopologies (lines and rings)
    graphs = {}
    # do root
    root_node = 0
    # every subtopology is connected redudandly, therefore take maximum
    graphs[root_node] = ('ring', nx.cycle_graph(max(backbone_n, 2 * len(list(base_graph.neighbors(root_node))))))
    # do first level nodes
    for node in first_level_nodes:
        total_subrings += 1
        no_neighbors = len(list(base_graph.neighbors(node)))
        subring_min_size = max(min_size, 2 * no_neighbors)
        subring_max_size = max(max_size, 2 * no_neighbors + 1)  # +1 because of range function
        subring_size = random.choice(range(subring_min_size, subring_max_size)) if max_size != min_size else max(
            max_size, 2 * no_neighbors)
        graphs[node] = ('ring', nx.cycle_graph(subring_size))
    # do leaf nodes, leafs can be either ring or line
    for node in leaf_nodes:
        # Ring
        if random.getrandbits(1):
            total_subrings += 1
            subring_size = random.choice(range(min_size, max_size)) if max_size != min_size else max_size
            graphs[node] = ('ring', nx.cycle_graph(subring_size))
        # Line
        else:
            total_sublines += 1
            subline_size = random.choice(range(min_size, max_size)) if max_size != min_size else max_size
            graphs[node] = ('line', nx.path_graph(subline_size))
    # rename nodes to avoid duplicate names for merging later
    for node, type_graph_tupel in graphs.items():
        type = type_graph_tupel[0]
        graph = type_graph_tupel[1]
        graphs[node] = (type, nx.relabel_nodes(graph, lambda old: '{}-{}'.format(node, old)))

    # Create new graph for final network
    G = nx.Graph()

    # Gateway Cluster-ID
    nx.set_edge_attributes(G, -1, 'gw_cluster_id')
    nx.set_node_attributes(G, -1, 'gw_cluster_id')
    nx.set_node_attributes(G, -1, 'segment_id')
    nx.set_node_attributes(G, -1, '_ipvs_position')
    gw_cluster_id = 0
    segment_id = 0
    total_gateways = 0

    # Iterate base graph to create connections and gateways
    dfs_predecessors = nx.dfs_predecessors(base_graph)
    for dfs_node in nx.dfs_preorder_nodes(base_graph):

        tmp_graph = graphs[dfs_node][1]
        if dfs_node in dfs_predecessors.keys():
            predecessor = dfs_predecessors[dfs_node]
            # Merge subtopology into final graph
            G = nx.union(G, tmp_graph)
            for node in tmp_graph.nodes:
                G.nodes[node]['segment_id'] = segment_id
            segment_id = segment_id + 1

            # Select gateways
            gateways = [node for node in graphs[predecessor][1] if G.degree(node) <= 2]
            if graphs[dfs_node][0] == 'ring':
                gws0 = list(gateways)[:2]
                gws1 = list(tmp_graph.nodes())[-2:]

                for gw0, gw1 in zip(gws0, gws1):
                    G.nodes[gw0]['gw_cluster_id'] = gw_cluster_id
                    G.nodes[gw1]['gw_cluster_id'] = gw_cluster_id
                    total_gateways += 2
                    G.add_edge(gw0, gw1, gw_cluster_id=gw_cluster_id)
                    break
                gw_cluster_id += 1

            else:
                gw0 = list(gateways)[:1][0]
                G.nodes[gw0]['gw_cluster_id'] = gw_cluster_id
                total_gateways += 1
                gw1 = list(tmp_graph.nodes())[-1:][0]

                G.add_edge(gw0, gw1, gw_cluster_id=gw_cluster_id)
                gw_cluster_id += 1

        else:
            G = tmp_graph
            for node in G.nodes:
                G.nodes[node]['segment_id'] = segment_id
            segment_id = segment_id + 1

    nx.set_node_attributes(G, True, 'is_switch')

    total_switches = G.number_of_nodes()

    for node in [node for node, degree in G.degree() if degree <= 2]:
        leaf = len(G.nodes())
        G.add_node(leaf)
        G.add_edge(node, leaf, is_switch=False)
        G.nodes[leaf]['segment_id'] = G.nodes[node]['segment_id']
        G.nodes[leaf]['is_switch'] = False

    G = _relabel_nodes(G)
    total_nodes = G.number_of_nodes()
    total_edges = G.number_of_edges()
    summary_report = {"nodes": total_nodes, "edges": total_edges, "switches": total_switches,
                      "gateways": total_gateways, "subrings": total_subrings, "sublines": total_sublines,
                      "segments": segment_id, "max_height": 2, "type": "factory_backbone"}

    return G, base_graph, summary_report


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
    entry = {
        'id': 'n{}'.format(int(vertex)),
        'processing_delay_ns': processing_delay_ns,
        'is_switch': ('is_switch' in G.nodes[vertex] and G.nodes[vertex]['is_switch']),
        'fwd_header_b': 24,  # Preamble + Ethernet header
        'queues_per_port': 8,
        '_ipvs_gw_cluster_id': G.nodes[vertex]['gw_cluster_id'] if 'gw_cluster_id' in G.nodes[vertex] else -1,
        '_ipvs_segment_id': G.nodes[vertex]['segment_id'] if 'segment_id' in G.nodes[vertex] else -1,
        '_ipvs_position': G.nodes[vertex]['_ipvs_position'],
    }
    if 'pos' in G.nodes[vertex]: entry['_imd_pos'] = G.nodes[vertex]['pos']
    return entry


def prepare_edges_for_json_export(G, propagation_delay_ns):
    edges = {}
    for v0, v1 in G.edges():
        # Set link speed depending on the type of the link

        link_speed_mbps = 1000
        edges['_'.join([str(v0), str(v1)])] = {
            'key': 'e{}'.format(len(edges)),
            'source': 'n{}'.format(v0),
            'target': 'n{}'.format(v1),
            'link_speed_mbps': link_speed_mbps,
            'propagation_delay_ns': propagation_delay_ns,
            '_ipvs_gw_cluster_id': G.edges[(v0, v1)]['gw_cluster_id'] if 'gw_cluster_id' in G.edges[(v0, v1)] else -1,
            '_ipvs_out_port': G.edges[(v0, v1)]['out_port'],
            '_ipvs_in_port': G.edges[(v0, v1)]['in_port']
        }
        edges['_'.join([str(v1), str(v0)])] = {
            'key': 'e{}'.format(len(edges)),
            'source': 'n{}'.format(v1),
            'target': 'n{}'.format(v0),
            'link_speed_mbps': link_speed_mbps,
            'propagation_delay_ns': propagation_delay_ns,
            '_ipvs_gw_cluster_id': G.edges[(v0, v1)]['gw_cluster_id'] if 'gw_cluster_id' in G.edges[(v0, v1)] else -1,
            # As only one directed edge exists in our graph G, inverting our selector
            #  from (v0, v1) to (v1, v0) does not invert our edge attributes
            #  out_port and in_port. This is why we manually invert out_port
            #  and in_port here.
            # The edge selector is not inverted. Otherwise this code would break if
            #  the generation algorithm is changed to contain both directed edges.
            '_ipvs_out_port': G.edges[(v0, v1)]['in_port'],
            '_ipvs_in_port': G.edges[(v0, v1)]['out_port']
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

    json_output = {'directed': True,
                   'multigraph': True,
                   'graph': G.graph,
                   'nodes': natsorted(vertices.values(), key=lambda k: k['id']),
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
         hierarchical_rings=False, export_summary=False, output_path="testdir", output_is_dir=True,
         output_graphml=True, processing_delay_ns=2000,
         propagation_delay_ns=200, seed=None, seed_state=None):
    if seed_state:
        random.setstate(seed_state)
    elif seed:
        random.seed(seed)

    summary = None
    if edge_core:
        if nodes:
            G = edge_core_graph(n=nodes)
        else:
            G = edge_core_graph()
    elif factory_backbone:
        if nodes:
            tree_n, subtop_size, _ = get_hybrid_graph_input_from_node_no(nodes)
            G, base_graph, summary = hierarchical_hybrid_graph(tree_n, 0, subtop_size, subtop_size, thin_random=False)
        else:
            G, base_graph, summary = hierarchical_hybrid_graph(5, 15, 5, 10)
    elif minimal_backbone:
        if nodes:
            tree_n, subtop_size, _ = get_hybrid_graph_input_from_node_no(nodes)
            G, base_graph, summary = hierarchical_hybrid_graph(tree_n, 0, subtop_size, subtop_size, thin_random=False)
        else:
            G, base_graph, summary = hierarchical_hybrid_graph(3, 10, 5, 5)
    elif ring:
        G = two_porter_ring(nodes)
    elif mesh:
        G = mesh_topology(*nodes)
    elif hierarchical_rings:
        hier_struct = build_hierarchical_ring_struct_from_node_no(nodes)
        G = hierarchical_rings_rec(nodes, level_rings=hier_struct)
    elif line:
        G = two_porter_line(nodes)
    elif star:
        G = star_topology(nodes)
    elif dumbbell:
        G = dumbbell_topology(nodes)
    elif fat_tree:
        G = fat_tree_topology(nodes)

    calculate_positions(G)

    if DEBUG:
        debug_draw(G)

    switches = list(filter(lambda node: G.nodes[node]['is_switch'] is True, G.nodes))

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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--nodes', type=int, required=False, help="Number of switches in topology", default=500)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--star', action='store_true', default=False)
    group.add_argument('--dumbbell', action='store_true', default=False)
    group.add_argument('--fat_tree', action='store_true', default=False)

    group.add_argument('--edge_core', action='store_true', default=False)
    group.add_argument('--factory_backbone', action='store_true', default=False)
    group.add_argument('--minimal_backbone', action='store_true', default=False)
    group.add_argument('--hierarchical_rings_rec', action='store_true', default=False)
    group.add_argument('--ring', action='store_true', default=False)
    group.add_argument('--line', action='store_true', default=False)
    parser.add_argument('--output_path', default='./examples')
    parser.add_argument('--export_summary', help='set if summary json is to be exported (only for factory_backbone)',
                        action='store_true', default=False)
    parser.add_argument('--processing-delay-ns', default=2000, help="Processing delay in nano seconds", type=int)
    parser.add_argument('--propagation-delay-ns', default=200, help="Propagation delay in nano seconds", type=int)

    args = parser.parse_args()

    main(nodes=args.nodes,
         line=args.line,
         ring=args.ring,
         star=args.star,
         dumbbell=args.dumbbell,
         fat_tree=args.fat_tree,
         edge_core=args.edge_core,
         minimal_backbone=args.minimal_backbone,
         factory_backbone=args.factory_backbone,
         hierarchical_rings=args.hierarchical_rings_rec,
         export_summary=args.export_summary,
         output_path=args.output_path,
         processing_delay_ns=args.processing_delay_ns,
         propagation_delay_ns=args.propagation_delay_ns,
         )
