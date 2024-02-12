import pytest

from primaite.simulator.network.airspace import AIR_SPACE, AirSpaceFrequency
from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.network.router import ACLAction
from primaite.simulator.network.hardware.nodes.network.wireless_router import WirelessRouter
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port


@pytest.fixture(scope="function")
def setup_network():
    network = Network()

    # Configure PC A
    pc_a = Computer(
        hostname="pc_a",
        ip_address="192.168.0.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.0.1",
        start_up_duration=0,
    )
    pc_a.power_on()
    network.add_node(pc_a)

    # Configure Router 1
    router_1 = WirelessRouter(hostname="router_1", start_up_duration=0)
    router_1.power_on()
    network.add_node(router_1)

    # Configure the connection between PC A and Router 1 port 2
    router_1.configure_router_interface("192.168.0.1", "255.255.255.0")
    network.connect(pc_a.network_interface[1], router_1.network_interface[2])

    # Configure Router 1 ACLs
    router_1.acl.add_rule(action=ACLAction.PERMIT, src_port=Port.ARP, dst_port=Port.ARP, position=22)
    router_1.acl.add_rule(action=ACLAction.PERMIT, protocol=IPProtocol.ICMP, position=23)

    # Configure PC B
    pc_b = Computer(
        hostname="pc_b",
        ip_address="192.168.2.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.2.1",
        start_up_duration=0,
    )
    pc_b.power_on()
    network.add_node(pc_b)

    # Configure Router 2
    router_2 = WirelessRouter(hostname="router_2", start_up_duration=0)
    router_2.power_on()
    network.add_node(router_2)

    # Configure the connection between PC B and Router 2 port 2
    router_2.configure_router_interface("192.168.2.1", "255.255.255.0")
    network.connect(pc_b.network_interface[1], router_2.network_interface[2])

    # Configure Router 2 ACLs

    # Configure the wireless connection between Router 1 port 1 and Router 2 port 1
    router_1.configure_wireless_access_point("192.168.1.1", "255.255.255.0")
    router_2.configure_wireless_access_point("192.168.1.2", "255.255.255.0")

    AIR_SPACE.show()

    router_1.route_table.add_route(
        address="192.168.2.0", subnet_mask="255.255.255.0", next_hop_ip_address="192.168.1.2"
    )

    # Configure Route from Router 2 to PC A subnet
    router_2.route_table.add_route(
        address="192.168.0.2", subnet_mask="255.255.255.0", next_hop_ip_address="192.168.1.1"
    )

    # Configure PC C
    pc_c = Computer(
        hostname="pc_c",
        ip_address="192.168.3.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.3.1",
        start_up_duration=0,
    )
    pc_c.power_on()
    network.add_node(pc_c)

    # Configure Router 3
    router_3 = WirelessRouter(hostname="router_3", start_up_duration=0)
    router_3.power_on()
    network.add_node(router_3)

    # Configure the connection between PC C and Router 3 port 2
    router_3.configure_router_interface("192.168.3.1", "255.255.255.0")
    network.connect(pc_c.network_interface[1], router_3.network_interface[2])

    # Configure the wireless connection between Router 2 port 1 and Router 3 port 1
    router_3.configure_wireless_access_point("192.168.1.3", "255.255.255.0")

    # Configure Route from Router 1 to PC C subnet
    router_1.route_table.add_route(
        address="192.168.3.0", subnet_mask="255.255.255.0", next_hop_ip_address="192.168.1.3"
    )

    # Configure Route from Router 2 to PC C subnet
    router_2.route_table.add_route(
        address="192.168.3.0", subnet_mask="255.255.255.0", next_hop_ip_address="192.168.1.3"
    )

    # Configure Route from Router 3 to PC A and PC B subnets
    router_3.route_table.add_route(
        address="192.168.0.0", subnet_mask="255.255.255.0", next_hop_ip_address="192.168.1.1"
    )
    router_3.route_table.add_route(
        address="192.168.2.0", subnet_mask="255.255.255.0", next_hop_ip_address="192.168.1.2"
    )

    return pc_a, pc_b, pc_c, router_1, router_2, router_3


def test_ping_default_gateways(setup_network):
    pc_a, pc_b, pc_c, router_1, router_2, router_3 = setup_network
    # Check if each PC can ping its default gateway
    assert pc_a.ping(pc_a.default_gateway), "PC A should ping its default gateway successfully."
    assert pc_b.ping(pc_b.default_gateway), "PC B should ping its default gateway successfully."
    assert pc_c.ping(pc_c.default_gateway), "PC C should ping its default gateway successfully."


def test_cross_router_connectivity_pre_frequency_change(setup_network):
    pc_a, pc_b, pc_c, router_1, router_2, router_3 = setup_network
    # Ensure that PCs can ping across routers before any frequency change
    assert pc_a.ping(pc_b.network_interface[1].ip_address), "PC A should ping PC B across routers successfully."
    assert pc_a.ping(pc_c.network_interface[1].ip_address), "PC A should ping PC C across routers successfully."
    assert pc_b.ping(pc_c.network_interface[1].ip_address), "PC B should ping PC C across routers successfully."
