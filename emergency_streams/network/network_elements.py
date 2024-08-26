from dataclasses import dataclass
from typing import List


@dataclass
class EgressPort:
    id: int
    name: str
    host_node: int
    destination_node: int

    # link properties
    link_speed_mbps: int
    propagation_delay_ns: int

    inter_frame_gap: int

    def __init__(self, json_link):
        if json_link is not None:
            self.id = int(json_link['id'])
            self.name = json_link['name']
            self.host_node = int(json_link['source'])
            self.destination_node = int(json_link['target'])
            self.link_speed_mbps = int(json_link['link_speed_mbps'])
            self.propagation_delay_ns = int(json_link['propagation_delay_ns'])

            self.inter_frame_gap = self.calculate_transmission_delay_in_ns_of(12)

    def calculate_transmission_delay_in_ns_of(self, frame_size: int) -> int:
        return int(frame_size * 8 / self.link_speed_mbps * 10 ** 3)

    def get_inter_frame_gap(self):
        return self.inter_frame_gap


class NetworkNode:
    id: str
    processing_delay_ns: int
    queues_per_port: int
    is_switch: bool
    ports: List[EgressPort]

    def __init__(self, name):
        self.id = name

    def get_neighbors(self):
        return [port.destination_node for port in self.ports]
