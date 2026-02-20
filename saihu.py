import argparse
import json
import os
import math
from statistics import median_low

DATA_RATE = 100  # in Mbps
PROPAGATION_DELAY = 0.2  # in us
PROCESSING_DELAY = 2  # in us


def parse_json_file(filename):
    with open(filename) as f:
        return json.load(f)


def generate_saihu_input(streams):
    network = {
        "name": "mkfirm",
        "packetizer": False,
        "multiplexing": "FIFO",
        "analysis_option": ["IS"],
        "time_unit": "us",
        "data_unit": "B",
        "rate_unit": "Mbps",
        "min_packet_length": 60,
    }

    flows = []
    servers = {}
    for i, stream in enumerate(streams):
        for hop in stream["route"]:
            data_rate = DATA_RATE
            max_interference = (
                8 * 100
            ) / data_rate  # 1534 = 1500B (payload) + 18B (Ethernet header) + 4B (Dot1Q header) + 12B (IFG)
            servers[hop["name"]] = {
                "name": hop["name"],
                "service_curve": {
                    "latencies": [
                        f"{max_interference + PROPAGATION_DELAY + PROCESSING_DELAY}us"
                    ],
                    "rates": [f"{data_rate}Mbps"],
                },
                "capacity": 100,
            }

        arrival_curve = {
            "bursts": [f"{stream['bucket_size_byte']}B"],
            "rates": [f"{1000*stream['rate_mbps']}kbps"],
        }

        path = [hop["name"] for hop in stream["route"]]
        flows.append(
            {
                "name": stream["name"],
                "path": path,
                "path_name": f"p{i}",
                "arrival_curve": arrival_curve,
                "max_packet_length": stream["frame_size_byte"],
                "min_packet_length": stream["frame_size_byte"],
                "rate_unit": "kbps",
            }
        )

    servers = [v for _, v in servers.items()]

    return {"network": network, "flows": flows, "servers": servers}


def main():
    parser = argparse.ArgumentParser(
        prog="python scripts/emergency_e2e_delay.py",
        description=""" Converts the scheduler output to JSON files,
        readable by Saihu (https://github.com/adfeel220/Saihu-TSN-Analysis-Tool-Integration).
        With their end-to-end delay results of emergency traffic, we derive an upper bound for 
        the maximum 5G packet delay budget to ensure the survival of each stream.""",
    )

    parser.add_argument("-s", "--streams_input", default="streams.json")
    parser.add_argument("-out", "--output", default="saihu_input.json")

    args = parser.parse_args()
    streams = parse_json_file(args.streams_input)

    saihu_data = generate_saihu_input(streams)
    with open(args.output, "w") as f:
        json.dump(saihu_data, f, indent=4)


if __name__ == "__main__":
    main()
