import argparse
import json
import math
import os.path
from typing import Dict

from PIL.ImageChops import offset

from streams.tt_stream import parse_streams, TtStream
from topology.topology import parse_topology

network_base = '''
import inet.networks.base.TsnNetworkBase;
import inet.node.contract.IEthernetNetworkNode;
import inet.node.ethernet.EthernetLink;
import inet.node.tsn.TsnDevice;
import inet.node.tsn.TsnSwitch;

network EmergencyNetwork extends TsnNetworkBase
{{
    submodules:
{submodules}
    connections:
{connections}
}}
'''

tsn_device_base = '''
        {name}: TsnDevice {{
            @display("p={xpos},{ypos}");
            numEthInterfaces = {num_interfaces};
            hasOutgoingStreams = true;
            eth[*].macLayer.queue.numTrafficClasses = {num_queues};{bitrates}
        }}
'''

tsn_switch_base = '''
        {name}: TsnSwitch {{
            @display("p={xpos},{ypos}");
            numEthInterfaces = {num_interfaces};
            hasOutgoingStreams = true;
            bridging.directionReverser.delayer.typename = "PacketDelayer";
            bridging.directionReverser.delayer.delay = {proc_delay_ns}ns;
            eth[*].macLayer.queue.numTrafficClasses = {num_queues};{bitrates}
        }}
'''

bitrate_base = '''
            eth[{port}].bitrate = {bitrate}Mbps;'''

connection_base = '''
        {src}.ethg[{src_port}] <--> EthernetLink {{ length = {length}m; datarate = {datarate}Mbps; }} <--> {tgt}.ethg[{tgt_port}];'''


def generate_network(topology, output):
    devices = {}

    for vertex in topology.vertices():
        pos = topology.vp.position[vertex].split(',')
        device = {
            "name": f'n{topology.vp.v_id[vertex]}',
            "num_queues": topology.vp.queues_per_port[vertex],
            "xpos": pos[0],
            "ypos": pos[1],
            "is_switch": topology.vp.is_switch[vertex],
            "datarates": {},
            "connections": {},
            "apps": [],
            "mactable": []
        }

        if device["is_switch"]:
            device["proc_delay_ns"] = topology.vp.processing_delay_ns[vertex]
        devices[topology.vp.v_id[vertex]] = device

    for edge in topology.edges():
        src = topology.vp.v_id[edge.source()]
        tgt = topology.vp.v_id[edge.target()]
        propagation_delay = topology.ep.propagation_delay_ns[edge]
        length = propagation_delay * 2e8 * 1e-9
        datarate = topology.ep.link_speed_mbps[edge]
        if tgt in devices[src]["connections"]:
            if length != devices[src]["connections"][tgt]["length"]:
                print(f"Warning: Inconsistent link length between {src} and {tgt}")
            if datarate != devices[src]["connections"][tgt]["datarate"]:
                print(f"Warning: Inconsistent link speed between {src} and {tgt}")
            continue

        connection = {
            "src": devices[src]["name"],
            "tgt": devices[tgt]["name"],
            "src_id": src,
            "tgt_id": tgt,
            "propagation_delay": propagation_delay,
            "length": length,
            "datarate": datarate,
            "src_port": len(devices[src]["connections"]),
            "tgt_port": len(devices[tgt]["connections"]),
            "done": False,
        }
        devices[src]["connections"][tgt] = connection
        devices[src]["datarates"][connection["src_port"]] = connection["datarate"]

        if src not in devices[tgt]["connections"]:
            devices[tgt]["connections"][src] = {
                "src": connection["tgt"],
                "tgt": connection["src"],
                "src_id": connection["tgt_id"],
                "tgt_id": connection["src_id"],
                "length": length,
                "datarate": datarate,
                "propagation_delay": propagation_delay,
                "src_port": connection["tgt_port"],
                "tgt_port": connection["src_port"],
                "done": False,
            }
            devices[tgt]["datarates"][connection["tgt_port"]] = connection["datarate"]

    # Build string of all devices
    submodules = ""
    connections = ""
    for device in devices.values():
        device["num_interfaces"] = len(device["connections"])
        bitrates = ""
        for port, bitrate in device["datarates"].items():
            bitrates += bitrate_base.format(port=port, bitrate=bitrate)
        if device["is_switch"]:
            submodules += tsn_switch_base.format(bitrates=bitrates, **device)
        else:
            submodules += tsn_device_base.format(bitrates=bitrates, **device)

        for connection in device["connections"].values():
            if connection["done"]:
                continue
            connections += connection_base.format(**connection)
            connection["done"] = True
            devices[connection["tgt_id"]]["connections"][connection["src_id"]]["done"] = True

    # Write to file
    with open(os.path.join(output, "Scenario.ned"), "w") as f:
        f.write(network_base.format(submodules=submodules, connections=connections))
    return devices


ini_base = '''[General]
network = "EmergencyNetwork"
sim-time-limit = 10s

**.hasEgressTrafficShaping = true

**.multicastForwarding = true
**.defaultMulticastLoop = false
**.igmp.enabled = false
*.*.ethernet.macHeaderChecker.promiscuous=true

{apps}

**.bridging.streamIdentifier.identifier.mapping = [{identifier_mapping}]

**.bridging.streamCoder.encoder.mapping = [{pcp_mapping}]

{gcls}

# Catch all for all other gates
**.macLayer.queue.transmissionGate[*].initiallyOpen = false
'''

identifier_mapping_base = '''{{stream: "{name}", packetFilter: expr(udp.destPort == {port})}}'''
identifier_mapping_spacing = ",\n" + (51 * " ")
pcp_mapping_base = '''{{stream: "{name}", pcp: {pcp}}}'''
pcp_mapping_spacing = ",\n" + (43 * " ")

omnet_device_base = '''
*.{name}.numApps = {numApps}
*.{name}.macTable.forwardingTable = [{macTable}]
{apps}
'''

mac_config_base = '''{{"address": "{address}", "interface": "eth{port}"}}'''

src_app_base_tt = '''
*.{device}.app[{index}].typename = "UdpSourceApp"
*.{device}.app[{index}].display-name = "{name}"
*.{device}.app[{index}].io.destAddress = "{ip}" # {tgt}
*.{device}.app[{index}].io.destPort = {port}
*.{device}.app[{index}].source.packetLength = {size}B - 58B # 58B = 4B (VLAN Tag) + 8B (UDP) + 20B (IP) + 14B (ETH MAC) + 4B (ETH FCS) + 8B (ETH PHY)
*.{device}.app[{index}].source.productionInterval = {prod_interval}
*.{device}.app[{index}].source.initialProductionOffset = {offset}ns
*.{device}.app[{index}].io.interfaceTableModule = "^.^.interfaceTable"
'''

src_app_base_et = '''
*.{device}.app[{index}].typename = "UdpBasicBurst"
*.{device}.app[{index}].display-name = "{name}"
*.{device}.app[{index}].destAddresses = "{ip}" # {tgt}
*.{device}.app[{index}].destPort = {port}
*.{device}.app[{index}].chooseDestAddrMode = "once"
*.{device}.app[{index}].burstDuration = {burst_duration}ms
*.{device}.app[{index}].messageLength = {size}B - 58B # 58B = 4B (VLAN Tag) + 8B (UDP) + 20B (IP) + 14B (ETH MAC) + 4B (ETH FCS) + 8B (ETH PHY)
*.{device}.app[{index}].startTime = {interevent_time}ms + exponential({exp_param}ms)
*.{device}.app[{index}].sleepDuration = {interevent_time}ms + exponential({exp_param}ms)
*.{device}.app[{index}].sendInterval = 9999s # burst consists of a single packet
*.{device}.app[{index}].io.interfaceTableModule = "^.^.interfaceTable"
'''

sink_app_base = '''
*.{device}.app[{index}].typename = "UdpSinkApp"
*.{device}.app[{index}].display-name = "{name}"
*.{device}.app[{index}].io.localPort = {port}
*.{device}.app[{index}].io.multicastAddresses = ["{ip}"]
'''

gcl_base = '''
*.{name}.eth[{port}].macLayer.queue.transmissionGate[{pcp}].offset = {offset}ns
*.{name}.eth[{port}].macLayer.queue.transmissionGate[{pcp}].initiallyOpen = {initially_open}
# {info}
*.{name}.eth[{port}].macLayer.queue.transmissionGate[{pcp}].durations = [{durations}]
'''


def multicast_ip_to_mac(ip):
    ip = ip.split(".")
    return f"01-00-5E-{int(ip[1]) & 0x7F:02X}-{int(ip[2]):02X}-{int(ip[3]):02X}"


def add_mac_entries(devices, stream_properties):
    mac = multicast_ip_to_mac(stream_properties["ip"])
    for route_element in stream_properties["route"]:
        devices[route_element["device"]]["mactable"].append({
            "address": mac,
            "port": route_element["port"]
        })


def generate_omnetpp_ini(topology, streams: Dict[int, TtStream], emergency_streams, devices, gcls, output):
    identifier_mapping = []
    pcp_mappings = []
    generate_apps(devices, identifier_mapping, pcp_mappings, streams, topology)
    generate_emergency_apps(devices, identifier_mapping, pcp_mappings, emergency_streams, topology)

    device_str = ""
    for device in devices.values():
        app_str = ""
        for app in device["apps"]:
            if app["type"] == "UdpSourceApp":
                app_str += src_app_base_tt.format(**app)
            elif app["type"] == "UdpBasicBurst":
                app_str += src_app_base_et.format(**app)
            else:
                app_str += sink_app_base.format(**app)

        mac_table_str = ",".join(mac_config_base.format(**entry) for entry in device["mactable"])

        device_str += omnet_device_base.format(name=device["name"], numApps=len(device["apps"]), apps=app_str,
                                               macTable=mac_table_str)

    gcl_str = ""
    for device_id, gcl in gcls.items():
        for target, gcl_per_pcp in gcl.items():
            port = devices[device_id]["connections"][str(target)]["src_port"]
            for pcp, gcl_entry in gcl_per_pcp.items():
                gcl_entry["initially_open"] = str(gcl_entry["initially_open"]).lower()
                gcl_entry["durations"] = ", ".join(str(d) + "ns" for d in gcl_entry["durations"])
                gcl_str += gcl_base.format(name=devices[device_id]["name"], port=port, pcp=pcp, **gcl_entry)

    with open(os.path.join(output, "omnetpp.ini"), "w") as f:
        f.write(ini_base.format(apps=device_str,
                                identifier_mapping=identifier_mapping_spacing.join(identifier_mapping),
                                pcp_mapping=pcp_mapping_spacing.join(pcp_mappings), gcls=gcl_str))


def generate_apps(devices, identifier_mapping, pcp_mappings, streams, topology):
    port = 5000
    for stream in streams.values():
        device = devices[topology.vp.v_id[stream.source]]
        tgt_device = devices[topology.vp.v_id[stream.target]]
        offsets = stream.properties["offsets"]
        cycle_time = stream.cycle_time_ns * len(offsets)
        for frame_number, offset in offsets.items():
            src_app = {
                "type": "UdpSourceApp",
                "device": device["name"],
                "tgt": tgt_device["name"],
                "ip": stream.properties["ip"],
                "name": f"{stream.name}_{frame_number}",
                "port": port,
                "size": stream.frame_size_byte,
                "prod_interval": f"{cycle_time}ns",
                "index": len(device["apps"]),
                "offset": offset,
            }
            devices[topology.vp.v_id[stream.source]]["apps"].append(src_app)

        sink_app = {
            "type": "UdpSinkApp",
            "name": stream.name,
            "device": tgt_device["name"],
            "port": port,
            "index": len(tgt_device["apps"]),
            "ip": stream.properties["ip"],
        }
        stream.properties["port"] = port
        devices[topology.vp.v_id[stream.target]]["apps"].append(sink_app)
        identifier_mapping.append(identifier_mapping_base.format(name=stream.name, port=port))
        pcp_mappings.append(pcp_mapping_base.format(name=stream.name, pcp=stream.properties["pcp"]))
        add_mac_entries(devices, stream.properties)

        port += 1


def generate_emergency_apps(devices, identifier_mapping, pcp_mappings, emergency_streams, topology):
    port = 10000
    for stream in emergency_streams:
        device = devices[topology.vp.v_id[stream["source"]]]
        tgt_device = devices[topology.vp.v_id[stream["target"]]]
        drate = device["datarates"][stream["properties"]["route"][0]["port"]]
        burst_duration = stream["bucket_size_byte"] / (drate - stream["rate_mbps"]) * 8 / 1e3

        src_app = {
            "type": "UdpBasicBurst",
            "device": device["name"],
            "tgt": tgt_device["name"],
            "ip": stream["properties"]["ip"],
            "name": stream["name"],
            "port": port,
            "size": stream["frame_size_byte"],
            "index": len(device["apps"]),
            "exp_param": 10,
            "burst_duration": burst_duration,
            "interevent_time": stream["min_inter_event_time_ns"] / 1e6,
        }
        devices[topology.vp.v_id[stream["source"]]]["apps"].append(src_app)

        sink_app = {
            "type": "UdpSinkApp",
            "name": stream["name"],
            "device": tgt_device["name"],
            "port": port,
            "index": len(tgt_device["apps"]),
            "ip": stream["properties"]["ip"],
        }
        devices[topology.vp.v_id[stream["target"]]]["apps"].append(sink_app)
        identifier_mapping.append(identifier_mapping_base.format(name=stream["name"], port=port))
        pcp_mappings.append(pcp_mapping_base.format(name=stream["name"], pcp=7))
        add_mac_entries(devices, stream["properties"])

        port += 1


def calc_cycle_time(streams):
    periods = set()
    for stream in streams.values():
        periods.add(stream.cycle_time_ns)
    return math.lcm(*periods)


def parse_transmission_output(transmission_path, devices, streams, gclcalc):
    # Read json
    with open(transmission_path, "r") as f:
        transmission_array = json.load(f)

    gcls_in = {}

    for transmission_stream in transmission_array:
        stream = streams[transmission_stream["stream_id"]]
        pcp = transmission_stream["pcp"]
        stream.properties["pcp"] = pcp
        stream.properties["route"] = []
        last_src_str = None
        for transmission in transmission_stream["frames"][0]["transmissions"]:
            src_str = str(transmission["source"])
            if src_str != last_src_str:
                port = devices[src_str]["connections"][str(transmission["target"])]["src_port"]
                stream.properties["route"].append({
                    "device": src_str,
                    "port": port
                })
            last_src_str = src_str


    if gclcalc:
        cycle_time = calc_cycle_time(streams)
        for transmission_stream in transmission_array:
            pcp = transmission_stream["pcp"]
            stream = streams[transmission_stream["stream_id"]]
            for frame in transmission_stream["frames"]:
                for transmission in frame["transmissions"]:
                    src_str = str(transmission["source"])
                    if src_str not in gcls_in:
                        gcls_in[src_str] = {}

                    target = transmission["target"]
                    if target not in gcls_in[src_str]:
                        gcls_in[src_str][target] = {}

                    entry = {
                            "open_time_ns": transmission["start"],
                            "close_time_ns": transmission["end"],
                            "streams": [{"stream_id": stream.id, "frame_number": frame["frame_number"]}]
                        }

                    if pcp not in gcls_in[src_str][target]:
                        gcls_in[src_str][target][pcp] = [entry]
                    else:
                        gcls_in[src_str][target][pcp].append(entry)

        gcls = {}
        for device, ports in gcls_in.items():
            gcls[device] = {}
            num_queues = devices[device]["num_queues"]
            highest_queue = max(num_queues - 1, 0)
            for target, pcps in ports.items():
                gcls[device][target] = {
                    highest_queue: {
                        "initially_open": True,
                        "offset": 0,
                        "durations": [],
                        "info": "ET port, open all the time"
                    }
                }
                for pcp, gcl in pcps.items():
                    calc_gcl(gcls[device][target], gcl, pcp, cycle_time, streams, device, target)
        return gcls
    return None


def add_route_to_emergency_streams(e_streams, devices):
    for stream in e_streams:
        stream["properties"]["route"] = []
        for route_element in stream["route"]:
            src_str = str(route_element["from"])
            stream["properties"]["route"].append({
                "device": src_str,
                "port": devices[src_str]["connections"][str(route_element["to"])]["src_port"]
            })
    pass


def load_gcls(gcl_path, streams, devices):
    with open(gcl_path, "r") as f:
        gcl_input = json.load(f)

    gcls = {}
    for nid, node in gcl_input.items():
        num_queues = devices[nid]["num_queues"]
        highest_queue = max(num_queues - 1, 0)
        gcls[nid] = {}
        for port in node["ports"].values():
            gcls[nid][port["target"]] = {
                highest_queue: {
                    "initially_open": True,
                    "offset": 0,
                    "durations": [],
                    "info": "ET port, open all the time"
                }
            }
            for pcp, gcl in port["gcl_per_pcp"].items():
                calc_gcl(gcls[nid][port["target"]], gcl, pcp, port["gcl_cycle"], streams, nid, port["target"])

    return gcls


def calc_gcl(port_gcls, gcl, pcp, cycle_time, streams, nid, tgt_id):
    durations = []
    port_gcls[pcp] = {
        "initially_open": False,
        "offset": 0,
        "durations": durations,
    }
    info = []
    # What a beautiful for and if nesting
    last_open = 0
    last_close = 0
    for gcl_entry in gcl:
        for stream in streams.values():
            if nid == str(stream.source):
                for frame in gcl_entry["streams"]:
                    if stream.id == frame["stream_id"]:
                        if "offsets" not in stream.properties:
                            stream.properties["offsets"] = {}
                        stream.properties["offsets"][frame["frame_number"]] = gcl_entry["open_time_ns"]
            elif tgt_id == stream.target:
                for frame in gcl_entry["streams"]:
                    if stream.id == frame["stream_id"]:
                        if "arrivals" not in stream.properties:
                            stream.properties["arrivals"] = {}
                        stream.properties["arrivals"][frame["frame_number"]] = (
                            gcl_entry["open_time_ns"], gcl_entry["close_time_ns"])

        tclose = gcl_entry["close_time_ns"]
        topen = gcl_entry["open_time_ns"]
        name_build = []
        for frame in gcl_entry["streams"]:
            name_build.append(str(frame["stream_id"]) + "-" + str(frame["frame_number"]))
        name = ", ".join(name_build)
        open_duration = tclose - topen

        if topen < last_open:
            # Not supported
            raise ValueError(f"Open time {topen} is before previous open time {last_open}")
        elif topen <= last_close:
            # Need to extend last open duration
            if len(durations) == 0:
                # Initially open case
                port_gcls[pcp]["initially_open"] = True
                durations.append(open_duration)
                info.append([name])
                last_close = tclose
            elif tclose > last_close:
                # Extend last open duration if close time is after last close
                extend_by = tclose - last_close
                durations[-1] += extend_by
                info[-1].append(name)
                last_close = tclose
            # In the case tclose <= last_close, we don't need to do anything
        else:
            # Need to add a close time in between
            durations.append(topen - last_close)
            info.append(["close"])
            durations.append(open_duration)
            info.append([name])
            last_close = tclose

        last_open = topen

    durations_sum = sum(durations)
    if durations_sum > cycle_time:
        raise ValueError(f"Sum of durations {durations_sum} exceeds cycle time {cycle_time}")
    elif durations_sum < cycle_time:
        # Last element in list is always the last open duration
        # Add close duration until the end of the cycle
        durations.append(cycle_time - durations_sum)
        info.append(["close"])
        if len(durations) % 2 != 0:
            # Shift GCL (merge front and end) and calculate offset
            offset = durations.pop(0)
            info_pop = info.pop(0)
            durations[-1] += offset
            if info[-1][-1] != info_pop[-1]:
                info[-1] += info_pop
            port_gcls[pcp]["offset"] = cycle_time - offset  # Offset is the start time within the cycle
            # Toggle initially open
            port_gcls[pcp]["initially_open"] = not port_gcls[pcp]["initially_open"]
    port_gcls[pcp]["info"] = ", ".join([f"({', '.join(f for f in frame)})" for i, frame in enumerate(info)])


def extend_streams_with_multicast(streams, emergency_streams):
    ip = [224, 0, 0, 2]
    for stream in streams.values():
        stream.properties = {
            "ip": ".".join(str(i) for i in ip),
        }
        get_next_ip(ip)

    for stream in emergency_streams:
        stream["properties"] = {
            "ip": ".".join(str(i) for i in ip)
        }
        get_next_ip(ip)
    pass


def get_next_ip(ip):
    ip[3] += 1
    if ip[3] > 255:
        ip[3] = 1
        ip[2] += 1
    if ip[2] > 255:
        ip[2] = 1
        ip[1] += 1
    if ip[1] > 255:
        ip[1] = 1
        ip[0] += 1


def parse_emergency_streams(path):
    with open(path) as emergency_stream_fd:
        return json.load(emergency_stream_fd)


def generate_stream_meta(topology, streams, devices, output):
    stream_meta = {}
    for sid, stream in streams.items():
        stream_meta[sid] = {
            "offsets": stream.properties["offsets"],
            "port": stream.properties["port"],
            "cycle_time": stream.cycle_time_ns,
        }
        expected_arrivals = {}
        expected_latest_arrivals = {}
        last_hop = stream.properties["route"][-1]
        device = devices[last_hop["device"]]
        drate = device["datarates"][last_hop["port"]]
        prop_delay = device["connections"][str(stream.target)]["propagation_delay"]
        trans_delay = stream.frame_size_byte * 8 / drate * 1e3
        for frame_number, (open_time, close_time) in stream.properties["arrivals"].items():
            expected_arrivals[frame_number] = open_time + prop_delay + trans_delay
            expected_latest_arrivals[frame_number] = close_time + prop_delay
        stream_meta[sid]["expected_arrivals"] = expected_arrivals
        stream_meta[sid]["expected_latest_arrivals"] = expected_latest_arrivals

    with open(os.path.join(output, "stream_meta.json"), "w") as f:
        json.dump(stream_meta, f, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--topology', '-t', help="Topology path", type=str, required=True)
    parser.add_argument('--streams', '-s', help="Stream path", type=str, required=True)
    parser.add_argument('--emergency_streams', '-e', help="Emergency stream path", type=str, required=True)
    parser.add_argument('--transmission', '-m',
                        help="Path of Transmission Output (first scheduler, i.e. E-TSN/cp-based)", type=str,
                        required=True)
    parser.add_argument("--gcl", "-g",
                        help="Path to GCL output, i.e. libtsndgm (if not provided, GCL is calculated from the transmission parameter, this is required for E-TSN)",
                        type=str, required=False)
    parser.add_argument("--output", "-o", help="Output path", type=str, required=True)
    args = parser.parse_args()

    topology = parse_topology(args.topology)
    streams = parse_streams(topology, args.streams)
    e_streams = parse_emergency_streams(args.emergency_streams)
    extend_streams_with_multicast(streams, e_streams)
    devices = generate_network(topology, args.output)

    if args.gcl is not None:
        # Our ET approach (use output from libtsndgm)
        parse_transmission_output(args.transmission, devices, streams, False)
        gcls = load_gcls(args.gcl, streams, devices)
        pass
    else:
        # E-TSN approach (use transmission output from E-TSN scheduler)
        gcls = parse_transmission_output(args.transmission, devices, streams, True)
        pass

    add_route_to_emergency_streams(e_streams, devices)
    generate_omnetpp_ini(topology, streams, e_streams, devices, gcls, args.output)
    generate_stream_meta(topology, streams, devices, args.output)

    print(topology, streams)
