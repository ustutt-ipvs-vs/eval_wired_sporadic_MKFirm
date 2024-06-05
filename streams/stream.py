import json
import xml.etree.cElementTree as ET
from copy import deepcopy
from typing import List, Dict

import graph_tool.all as gt
import networkx as nx
from graph_tool import Vertex, Edge
from lxml import etree


class Stream:
    def __init__(self, id: str, source: Vertex, target: Vertex, size: int, cycle_time: int,
                 max_delay: int, redundancy: int, route: List[Edge], type='scheduled_cyclic_traffic', cycle_offset=0,
                 state=None, pcp=7, feasible=None, properties=None):
        if properties is None:
            properties = {}
        self.id = id
        self.source = source
        self.target = target
        self.size = size
        self.cycle_time = cycle_time
        self.cycle_offset = cycle_offset
        self.max_delay = max_delay
        self.redundancy = redundancy
        self.route = route
        self.type = type
        self.state = state
        self.pcp = pcp
        self.properties = properties

        if not state:
            self.state = {}

        if not feasible:
            self.feasible = {}

    # def __init__(self, id: int, source: Vertex, target: Vertex, paths_v: List[ndarray], paths_e: ndarray,
    #              edges: Set[Edge], vertices: Set[Vertex], size: int):
    #     self.__init__(id, source, target, size)
    #     self.paths_e = paths_e
    #     self.paths_v = paths_v
    #     self.edges = edges
    #     self.vertices = vertices

    id: str
    source: Vertex
    target: Vertex
    size: int
    cycle_time: int
    max_delay: int
    redundancy: int
    route: List[Edge]
    pcp: int
    state: dict()
    feasible: dict()
    properties: dict()

    def __deepcopy__(self, memo):
        copy = type(self)(**self.__dict__)
        copy.__dict__.update(self.__dict__)
        copy.state = deepcopy(self.state)

        print('[WARNING] Only stream.state gets deepcopied!')
        return copy

    def export_to_xml(self, topology):
        if not isinstance(topology, nx.MultiDiGraph):
            # graph-tool
            source = str(topology.vp['v_id'][self.source])
            target = str(topology.vp['v_id'][self.target])
        else:
            # networkx
            source = self.source
            target = self.target

        stream_element = ET.Element('stream')
        stream_element.set('id', str(self.id))
        sources = ET.SubElement(stream_element, 'sources')
        host = ET.SubElement(sources, 'host')
        host.set('id', source)
        targets = ET.SubElement(stream_element, 'targets')
        host = ET.SubElement(targets, 'host')
        host.set('id', target)
        route = ET.SubElement(stream_element, 'route')
        route.set('routing_method', 'precomputed')
        for e in self.route:
            edge = ET.SubElement(route, 'edge')

            if not isinstance(topology, nx.MultiDiGraph):
                # graph-tool
                edge.set('key', topology.ep['e_id'][e])
                edge.set('source', topology.vp['v_id'][e.source()])
                edge.set('target', topology.vp['v_id'][e.target()])
            else:
                # networkx
                edge.set('key', e[2])
                edge.set('source', e[0])
                edge.set('target', e[1])

        cyle_time = ET.SubElement(stream_element, 'cycle_time_ns')
        cyle_time.set('value', str(self.cycle_time))
        traffic_type = ET.SubElement(stream_element, 'traffic_type')
        traffic_type.set('type', self.type)
        frame_size = ET.SubElement(stream_element, 'frame_size_b')
        frame_size.set('value', str(self.size))
        transmit_offset = ET.SubElement(stream_element, 'cycle_offset_ns')
        transmit_offset.set('value', str(self.cycle_offset))
        vlan_settings = ET.SubElement(stream_element, 'vlan_settings')
        vlan_settings.set('pcp', str(self.pcp))
        properties = ET.SubElement(stream_element, 'properties')
        for key, value in self.properties.items():
            properties.set(key, value)

        return stream_element

    @staticmethod
    def export_streams_to_xml(streams, topology):
        streams_element = ET.Element('streams')

        for stream in streams.values():
            stream_element = stream.export_to_xml(topology)
            streams_element.append(stream_element)

        return streams_element

    @staticmethod
    def export_streams_to_json(streams, topology):

        stream_dict = {}
        for stream_id, stream in streams.items():
            stream_dict[stream_id] = {}

            if not isinstance(topology, nx.MultiDiGraph):
                # Graph-tool to dict
                stream_dict[stream_id]['source'] = [topology.vp['v_id'][stream.source]]
                stream_dict[stream_id]['target'] = [topology.vp['v_id'][stream.target]]
                # graph-tool: Convert edge object to triple (source, target, edge key
                stream_dict[stream_id]['route'] = [
                    (topology.vp['v_id'][edge.source()], topology.vp['v_id'][edge.target()],
                     topology.ep['e_id'][edge]) for edge in stream.route]

            for key, item in vars(stream).items():
                if key not in stream_dict[stream_id]:
                    stream_dict[stream_id][key] = deepcopy(item)

            # Relabelling
            stream_dict[stream_id]['cycle_time_ns'] = stream_dict[stream_id].pop('cycle_time')
            stream_dict[stream_id]['frame_size_b'] = stream_dict[stream_id].pop('size')
            stream_dict[stream_id]['max_delay_ns'] = stream_dict[stream_id].pop('max_delay')
            stream_dict[stream_id]['_ipvs_state'] = stream_dict[stream_id].pop('state')
            stream_dict[stream_id]['_ipvs_feasible'] = stream_dict[stream_id].pop('feasible')

        return json.dumps(stream_dict)


def parse_streams(g: gt.Graph, stream_path: str) -> Dict[str, Stream]:
    streams = {}

    with open(stream_path) as stream_fd:
        stream_data = json.load(stream_fd)

        for i, stream in map(lambda x: (x[0], x[1]), stream_data.items()):
            if 'source' in stream and 'target' in stream:
                source, target = (gt.find_vertex(g, g.vp['v_id'], stream['source'][0])[0],
                                  gt.find_vertex(g, g.vp['v_id'], stream['target'][0])[0])
            elif 'sources' in stream and 'destinations' in stream:
                source, target = (gt.find_vertex(g, g.vp['v_id'], stream['sources'][0])[0],
                                  gt.find_vertex(g, g.vp['v_id'], stream['destinations'][0])[0])
            else:
                raise NotImplemented('Format not supported')

            streams[i] = Stream(id=i, source=source, target=target, size=stream['frame_size_b'],
                                cycle_time=stream['cycle_time_ns'], max_delay=stream['max_delay_ns'],
                                redundancy=stream['redundancy'], pcp=stream['pcp'] if 'pcp' in stream else 7,
                                type=stream['type'],
                                route=[gt.find_edge(g, g.ep['e_id'], edge[2])[0] for edge in stream['route']])

    return streams
