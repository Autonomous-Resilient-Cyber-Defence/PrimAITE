from ipaddress import IPv4Address

from primaite.simulator.network.hardware.nodes.computer import Computer
from primaite.simulator.network.networks import arcd_uc2_network
from primaite.simulator.network.transmission.data_link_layer import EthernetHeader, Frame
from primaite.simulator.network.transmission.network_layer import IPPacket, Precedence
from primaite.simulator.network.transmission.transport_layer import Port, TCPHeader


def test_database_query_across_the_network():
    """Tests DB query across the network returns HTTP status 200 and date."""
    network = arcd_uc2_network()

    client_1: Computer = network.get_node_by_hostname("client_1")

    client_1.arp.send_arp_request(IPv4Address("192.168.1.14"))

    dst_mac_address = client_1.arp.get_arp_cache_mac_address(IPv4Address("192.168.1.14"))

    outbound_nic = client_1.arp.get_arp_cache_nic(IPv4Address("192.168.1.14"))
    client_1.ping("192.168.1.14")

    frame = Frame(
        ethernet=EthernetHeader(src_mac_addr=client_1.ethernet_port[1].mac_address, dst_mac_addr=dst_mac_address),
        ip=IPPacket(
            src_ip_address=client_1.ethernet_port[1].ip_address,
            dst_ip_address=IPv4Address("192.168.1.14"),
            precedence=Precedence.FLASH,
        ),
        tcp=TCPHeader(src_port=Port.POSTGRES_SERVER, dst_port=Port.POSTGRES_SERVER),
        payload="SELECT * FROM user;",
    )

    outbound_nic.send_frame(frame)

    client_1_last_payload = outbound_nic.pcap.read()[-1]["payload"]

    assert client_1_last_payload["status_code"] == 200
    assert client_1_last_payload["data"]
