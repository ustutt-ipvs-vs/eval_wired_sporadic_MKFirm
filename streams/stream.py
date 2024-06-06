from dataclasses import dataclass


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
