#!/usr/bin/python3

import argparse
import json
# xml parser
import xml.etree.ElementTree as ET
# grouping the streams
import random

import graph_tool.all as gt
import networkx as nx
import xml.dom.minidom

from streams.stream import Stream
from streams.stream_utils import calc_e2e_delay
from topology.topology import parse_topology
from topology.topology_utils import get_header_size


def find_route(src, dst, g):
    route = nx.dijkstra_path(g, src, dst)

    return route[1:-1]


def write_to_xml(input_xml, output_name):
    with open(output_name + '_flow.xml', 'w') as output:
        # prettify the output routing
        pretty_xml = xml.dom.minidom.parseString(ET.tostring(input_xml)).toprettyxml()
        output.write(pretty_xml)


def generate_stream(stream_id, hosts, cycle_time_ns, calculate_route=False, topology=None, delay_alpha=None, pcp=7,
                    size=None, stream_type='scheduled_cyclic_traffic', properties={}):
    stream = None
    if delay_alpha is None:
        delay_alpha = 1.5  # default value
    # Max delay must be smaller than the cycle time
    while not stream or (not calculate_route and stream.max_delay < cycle_time_ns):
        source = random.choice(hosts)
        target = random.choice([n for n in hosts if n != source])

        if size is None:
            size = random.randint(16, 512) + get_header_size(udp_header=True, ipv4_header=True, ieee8021q_header=True,
                                                             mac_header=True, ethernet_header=True)

        stream = Stream(id=stream_id,
                        source=source,
                        target=target,
                        cycle_time=cycle_time_ns,
                        size=size,
                        max_delay=cycle_time_ns,
                        redundancy=1,
                        route=[],
                        pcp=pcp,
                        type=stream_type,
                        properties=properties)

        if calculate_route:
            stream.route = gt.shortest_path(topology, stream.source, stream.target)[1]
            # Stream route as list of triples containing source, target, and key
            # stream.route = [(edge.source(), edge.target(), topology.ep['e_id'][edge])
            #                  for edge in gt.shortest_path(topology, stream.source, stream.target)[1]]

            if not stream.route:
                print(
                    f'Warning: For source {topology.vp["v_id"][stream.source]} -> {topology.vp["v_id"][stream.target]}, there is no route')
                stream = None
                continue

            stream.max_delay = calc_e2e_delay(topology, stream, delay_alpha, False, round=True)

    return stream


def generate_streams(streams_no, cycle_time_ns, topology_path=None, output=None, seed=None, seed_state=None,
                     is_xml=False, topology=None, pcp=7, size=None, delay_alpha=None):
    if not topology:
        topology = parse_topology(topology_path)
    hosts = [v for v in topology.vertices() if not topology.vp.is_switch[v]]

    if seed_state:
        random.setstate(seed_state)
    elif seed:
        random.seed(seed)

    streams = {}
    while len(streams) < streams_no:

        streams[len(streams)] = generate_stream(len(streams), hosts, cycle_time_ns, calculate_route=True,
                                                topology=topology, pcp=pcp, size=size)

    if is_xml:
        is_xml = Stream.export_streams_to_xml(streams, topology)
        write_to_xml(is_xml, output)

    # print("Streams:", len(streams))

    if output:
        with open(output, 'w') as output:
            output.write(Stream.export_streams_to_json(streams, topology))

    return streams, random.getstate()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--ns', type=int, help='Number of streams', default=50)
    parser.add_argument('--cycle', type=int, help='Cycle time of hosts in ns', default=1000)
    parser.add_argument('--topology', type=str, required=True, help='Path to topology file')
    parser.add_argument('--framesize', type=str, default=None, help='Frame size (Default: random(64,300)')
    parser.add_argument('--output', help='Output file', default='./examples/streams.json')
    parser.add_argument('--x', help='Use if output format should be xml', action='store_true', default=False)

    args = parser.parse_args()

    generate_streams(args.ns, args.cycle, args.topology, args.output, args.x, size=args.framesize)

    # main('test_topology.json', 100, 'test_s.xml', True)
