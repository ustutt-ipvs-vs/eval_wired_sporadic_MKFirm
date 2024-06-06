from dataclasses import dataclass
import json


@dataclass
class Stream:
    id: int
    name: str
    source: int
    target: int
    frame_size_byte: int
    cycle_time_ns: int
    deadline_ns: int

    def __init__(self, stream_id: int):
        self.id = stream_id
        self.name = "stream_{}".format(stream_id)
        
    def toJSON(self):
        return {"id": self.id,
                "name": self.name,
                "source": int(self.source),
                "target": int(self.target),
                "frame_size_byte": self.frame_size_byte,
                "cycle_time_ns": self.cycle_time_ns,
                "deadline_ns": self.deadline_ns}