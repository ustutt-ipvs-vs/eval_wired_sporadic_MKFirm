import string

# Convert Mbit/S to nS/byte
MBITS_TO_NSBYTE = (1e6) / 8 / 1e9


def calc_propagation_delay(cable_length: int):
    # Propagation speed: 2/3 * speed_of_light [m/s]
    # [m/s] -> [m/ns] * 1e9
    return ((2 / 3) * (2.99792 * 1e8)) / 1e9 * cable_length


def calc_cable_length(propagation_delay_ns: int):
    # According to INET specification:
    # propagation_delay_seconds = length / 2e8
    return propagation_delay_ns * 2e8 * 1e-9


def calc_distance(pos1: string, pos2: string) -> float:
    x1, y1 = pos1.split(',')
    x2, y2 = pos2.split(',')
    return ((float(x1) - float(x2)) ** 2 + (float(y1) - float(y2)) ** 2) ** 0.5


def calc_transmission_delay(size: int, link_speed: int) -> int:
    if link_speed == 0:
        return 0

    return int(size / (link_speed * MBITS_TO_NSBYTE))


def calc_ifg_delay(link_speed: int) -> int:
    if link_speed == 0:
        return 0
    return int(get_header_size(inter_packet_gap=True) / (link_speed * MBITS_TO_NSBYTE))


def calc_ifg_delay_wifi() -> int:
    sifs = 16_000  # 16 us
    slot_time = 9_000  # 9 us
    return sifs + 2 * slot_time


def calc_port_blocking_time(size: int, link_speed: int) -> float:
    return int(calc_transmission_delay(size, link_speed) + calc_ifg_delay(link_speed))


def hop_list_to_edge_list(hop_list, topology):
    return list(topology.edge(source, target)
                for source, target in zip(hop_list[:-1], hop_list[1:]))


def get_header_size(udp_header=False, ipv4_header=False, ieee8021q_header=False, mac_header=False,
                    ethernet_header=False, inter_packet_gap=False, ieee80211_mac_trailer=False,
                    ieee80211_mac_header=False, ieee80211_llc_snap_header=False):
    """Return the overhead in bytes for the given headers

    :param inter_packet_gap: Inter packet gap
    :param ethernet_header: Include Ethernet header (physical layer)
    :param mac_header: Include the MAC header (link layer)
    :param ieee8021q_header: Include the IEEE 802.1q header
    :param udp_header: UDP header
    :param ipv4_header: IPv4 header
    :return: Overhead in bytes
    """
    overhead = 0
    if udp_header:
        overhead += 8
    if ipv4_header:
        overhead += 20
    if ieee8021q_header:
        overhead += 4
    if mac_header:
        overhead += 18
    if ethernet_header:
        overhead += 8
    if inter_packet_gap:
        overhead += 12
    if ieee80211_mac_trailer:
        overhead += 4
    if ieee80211_mac_header:
        overhead += 26
    if ieee80211_llc_snap_header:
        overhead += 8
    return overhead
