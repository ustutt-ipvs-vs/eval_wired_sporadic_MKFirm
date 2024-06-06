import json

import graph_tool.all as gt
import networkx as nx

DEBUG = False

def parse_topology(topology_path):
    topology = gt.Graph(directed=True)

    with open(topology_path, 'r') as topology_fd:
        topology_data = json.load(topology_fd)

        e_id = topology.new_edge_property('int')
        topology.edge_properties['id'] = e_id
        link_speed = topology.new_edge_property('int')
        topology.edge_properties['link_speed_mbps'] = link_speed
        propagation_delay = topology.new_edge_property('int')
        topology.edge_properties['propagation_delay_ns'] = propagation_delay
        egw_cluster_id = topology.new_edge_property('string')
        topology.edge_properties['name'] = egw_cluster_id

        v_id = topology.new_vertex_property('string')
        topology.vertex_properties['v_id'] = v_id
        vertices = topology.add_vertex(len(topology_data['nodes']))
        vertex_dict = {}
        for vertex, name in zip(vertices, map(lambda curr: curr['id'], topology_data['nodes'])):
            v_id[vertex] = name
            vertex_dict[name] = vertex

        # Add edges: source -> target
        topology.add_edge_list(
            [(vertex_dict[edge['source']], vertex_dict[edge['target']], edge['id'], edge['link_speed_mbps'],
              edge['propagation_delay_ns'], edge['name'])
             for edge in topology_data['links']],
            eprops=[e_id, link_speed, propagation_delay])

        # Add edges: target -> source
        # topology.add_edge_list(
        #     [(vertex_dict[edge['target']], vertex_dict[edge['source']], edge['link_speed_mbps'],
        #       edge['propagation_delay_ns'], edge['_ipvs_gw_cluster_id'])
        #      for edge in topology_data['links']],
        #     eprops=[link_speed, propagation_delay, egw_cluster_id])

        processing_delay = topology.new_vertex_property('int')
        is_switch = topology.new_vertex_property('bool')
        queues_per_port = topology.new_vertex_property('int')
        fwd_header_b = topology.new_vertex_property('int')
        position = topology.new_vertex_property('string')

        if '_ipvs_gw_cluster_id' in topology_data['nodes'][0]:
            # Set cluster id of vertices
            vgw_cluster_id = topology.new_vertex_property('int')
            topology.vertex_properties['vgw_cluster_id'] = vgw_cluster_id

        if '_ipvs_segment_id' in topology_data['nodes'][0]:
            segment_id = topology.new_vertex_property('int')
            topology.vertex_properties['segment_id'] = segment_id

        topology.vertex_properties['is_switch'] = is_switch
        topology.vertex_properties['processing_delay_ns'] = processing_delay
        topology.vertex_properties['queues_per_port'] = queues_per_port
        topology.vertex_properties['fwd_header_b'] = fwd_header_b
        topology.vertex_properties['position'] = position

        for vertex in topology_data['nodes']:
            v = gt.find_vertex(topology, topology.vp['v_id'], vertex['id'])[0]
            processing_delay[v] = vertex['processing_delay_ns']
            is_switch[v] = vertex['is_switch']
            queues_per_port[v] = vertex['queues_per_port']

    return topology


def parse_topology_networkx(topology_path):
    with open(topology_path, 'r') as topology_fd:
        topology_data = json.load(topology_fd)

        topology = nx.readwrite.json_graph.node_link_graph(topology_data)

        return topology


def get_topology_subset(topology, streams):
    '''

    :param topology:
    :param streams:
    :return: topology as subset of original topology that is used by streams

    NOTE: the operation remove_vertex(vertex) may invalidate vertex descriptors. Vertices are always indexed
    contiguously in the range, hence vertex descriptors with an index higher than vertex will be invalidated after
    removal (if fast == False, otherwise only descriptors pointing to vertices with the largest index will be
    invalidated).
    Because of this, the only safe way to remove more than one vertex at once is to sort them in decreasing index order:
    see:https://graph-tool.skewed.de/static/doc/graph_tool.html?highlight=remove%20vertex#graph_tool.Graph.remove_vertex
    '''

    stream_paths = []
    used_nodes = []
    removable_vertices = []
    topo_subset = topology.copy()

    # take all shortest paths from all streams and add them to stream_paths list
    for s_id, stream in streams.items():
        stream_paths.append(list(gt.all_shortest_paths(topology, stream.source, stream.target)))

    # flatten it to a single list
    for s in stream_paths:
        for a in s:
            used_nodes.extend(a.tolist())

    if DEBUG:
        for t in set(used_nodes):
            print("DEBUG", topology.vp['v_id'][t], t)

    # get list of all vertex that needed to be removed
    for v in topology.vertices():
        if v not in sorted(set(used_nodes)):
            removable_vertices.append(v)

    # remove all vertices from topology that are not in this list
    for v in reversed(removable_vertices):
        topo_subset.remove_vertex(v)
        if DEBUG:
            print("REMOVED:", topology.vp['v_id'][v], v)

    return topo_subset
