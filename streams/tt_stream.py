from dataclasses import dataclass
import json
from typing import Dict

try:
    import graph_tool.all as gt

    hasGt = True
except:
    hasGt = False

@dataclass
class TtStream:
    id: int
    name: str
    source: int
    target: int
    frame_size_byte: int
    cycle_time_ns: int
    deadline_ns: int
    properties: dict
    et_capable: bool = False

    def __init__(self, stream_id: int):
        self.id = stream_id
        self.name = "stream_{}".format(stream_id)

    def to_json(self):
        return {"id": self.id,
                "name": self.name,
                "source": int(self.source),
                "target": int(self.target),
                "frame_size_byte": self.frame_size_byte,
                "cycle_time_ns": self.cycle_time_ns,
                "deadline_ns": self.deadline_ns,
                "et_capable": self.et_capable}


def from_json(json_object) -> TtStream:
    stream = TtStream(json_object['id'])
    stream.source = json_object['source']
    stream.target = json_object['target']
    stream.frame_size_byte = json_object['frame_size_byte']
    stream.cycle_time_ns = json_object['cycle_time_ns']
    stream.deadline_ns = json_object['deadline_ns']
    stream.et_capable = json_object['et_capable']
    stream.properties = {}
    return stream

def parse_streams(topology, stream_path: str) -> Dict[int, TtStream]:
    streams = {}

    with open(stream_path) as stream_fd:
        stream_data = json.load(stream_fd)

        for stream_json in stream_data:
            stream = TtStream(stream_json['id'])
            stream.name = stream_json['name']
            stream.source = stream_json['source']
            stream.target = stream_json['target']
            stream.frame_size_byte = stream_json['frame_size_byte']
            stream.cycle_time_ns = stream_json['cycle_time_ns']
            stream.deadline_ns = stream_json['deadline_ns']
            stream.properties = {}
            if hasGt:
                stream.properties["source"] = topology.vertex(stream.source)
                stream.properties["target"] = topology.vertex(stream.target)
            streams[stream.id] = stream

    return streams
