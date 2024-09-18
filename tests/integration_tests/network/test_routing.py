# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from typing import Tuple

import pytest

from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.network.router import ACLAction, Router
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.services.ntp.ntp_client import NTPClient
from primaite.simulator.system.services.ntp.ntp_server import NTPServer


@pytest.fixture(scope="function")
def pc_a_pc_b_router_1() -> Tuple[Computer, Computer, Router]:
    network = Network()
    pc_a = Computer(
        hostname="pc_a",
        ip_address="192.168.0.10",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.0.1",
        start_up_duration=0,
    )
    pc_a.power_on()

    pc_b = Computer(
        hostname="pc_b",
        ip_address="192.168.1.10",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    pc_b.power_on()

    router_1 = Router(hostname="router_1", start_up_duration=0)
    router_1.power_on()

    router_1.configure_port(1, "192.168.0.1", "255.255.255.0")
    router_1.configure_port(2, "192.168.1.1", "255.255.255.0")

    network.connect(endpoint_a=pc_a.network_interface[1], endpoint_b=router_1.network_interface[1])
    network.connect(endpoint_a=pc_b.network_interface[1], endpoint_b=router_1.network_interface[2])
    router_1.enable_port(1)
    router_1.enable_port(2)

    return pc_a, pc_b, router_1


@pytest.fixture(scope="function")
def multi_hop_network() -> Network:
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
    router_1 = Router(hostname="router_1", start_up_duration=0)
    router_1.power_on()
    network.add_node(router_1)

    # Configure the connection between PC A and Router 1 port 2
    router_1.configure_port(2, "192.168.0.1", "255.255.255.0")
    network.connect(pc_a.network_interface[1], router_1.network_interface[2])
    router_1.enable_port(2)

    # Configure Router 1 ACLs
    router_1.acl.add_rule(action=ACLAction.PERMIT, src_port=Port["ARP"], dst_port=Port["ARP"], position=22)
    router_1.acl.add_rule(action=ACLAction.PERMIT, protocol=IPProtocol["ICMP"], position=23)

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
    router_2 = Router(hostname="router_2", start_up_duration=0)
    router_2.power_on()
    network.add_node(router_2)

    # Configure the connection between PC B and Router 2 port 2
    router_2.configure_port(2, "192.168.2.1", "255.255.255.0")
    network.connect(pc_b.network_interface[1], router_2.network_interface[2])
    router_2.enable_port(2)

    # Configure Router 2 ACLs

    # Configure the connection between Router 1 port 1 and Router 2 port 1
    router_2.configure_port(1, "192.168.1.2", "255.255.255.252")
    router_1.configure_port(1, "192.168.1.1", "255.255.255.252")
    network.connect(router_1.network_interface[1], router_2.network_interface[1])
    router_1.enable_port(1)
    router_2.enable_port(1)
    return network


def test_ping_default_gateway(pc_a_pc_b_router_1):
    pc_a, pc_b, router_1 = pc_a_pc_b_router_1

    assert pc_a.ping(pc_a.default_gateway)


def test_ping_other_router_port(pc_a_pc_b_router_1):
    pc_a, pc_b, router_1 = pc_a_pc_b_router_1

    assert pc_a.ping(pc_b.default_gateway)


def test_host_on_other_subnet(pc_a_pc_b_router_1):
    pc_a, pc_b, router_1 = pc_a_pc_b_router_1

    assert pc_a.ping(pc_b.network_interface[1].ip_address)


def test_no_route_no_ping(multi_hop_network):
    pc_a = multi_hop_network.get_node_by_hostname("pc_a")
    pc_b = multi_hop_network.get_node_by_hostname("pc_b")

    assert not pc_a.ping(pc_b.network_interface[1].ip_address)


def test_with_routes_can_ping(multi_hop_network):
    pc_a = multi_hop_network.get_node_by_hostname("pc_a")
    pc_b = multi_hop_network.get_node_by_hostname("pc_b")

    router_1: Router = multi_hop_network.get_node_by_hostname("router_1")  # noqa
    router_2: Router = multi_hop_network.get_node_by_hostname("router_2")  # noqa

    # Configure Route from Router 1 to PC B subnet
    router_1.route_table.add_route(
        address="192.168.2.0", subnet_mask="255.255.255.0", next_hop_ip_address="192.168.1.2"
    )

    # Configure Route from Router 2 to PC A subnet
    router_2.route_table.add_route(
        address="192.168.0.2", subnet_mask="255.255.255.0", next_hop_ip_address="192.168.1.1"
    )

    assert pc_a.ping(pc_b.network_interface[1].ip_address)


def test_with_default_routes_can_ping(multi_hop_network):
    pc_a = multi_hop_network.get_node_by_hostname("pc_a")
    pc_b = multi_hop_network.get_node_by_hostname("pc_b")

    router_1: Router = multi_hop_network.get_node_by_hostname("router_1")  # noqa
    router_2: Router = multi_hop_network.get_node_by_hostname("router_2")  # noqa

    # Configure Route from Router 1 to PC B subnet
    router_1.route_table.set_default_route_next_hop_ip_address("192.168.1.2")

    # Configure Route from Router 2 to PC A subnet
    router_2.route_table.set_default_route_next_hop_ip_address("192.168.1.1")

    assert pc_a.ping(pc_b.network_interface[1].ip_address)


def test_ping_router_port_multi_hop(multi_hop_network):
    pc_a = multi_hop_network.get_node_by_hostname("pc_a")
    router_2 = multi_hop_network.get_node_by_hostname("router_2")

    router_2.route_table.add_route(
        address="192.168.0.0", subnet_mask="255.255.255.0", next_hop_ip_address="192.168.1.1"
    )

    assert pc_a.ping(router_2.network_interface[1].ip_address)


def test_routing_services(multi_hop_network):
    pc_a = multi_hop_network.get_node_by_hostname("pc_a")

    pc_b = multi_hop_network.get_node_by_hostname("pc_b")

    pc_a.software_manager.install(NTPClient)
    ntp_client = pc_a.software_manager.software["NTPClient"]
    ntp_client.start()

    pc_b.software_manager.install(NTPServer)
    pc_b.software_manager.software["NTPServer"].start()

    ntp_client.configure(ntp_server_ip_address=pc_b.network_interface[1].ip_address)

    router_1: Router = multi_hop_network.get_node_by_hostname("router_1")  # noqa
    router_2: Router = multi_hop_network.get_node_by_hostname("router_2")  # noqa

    router_1.acl.add_rule(action=ACLAction.PERMIT, src_port=Port["NTP"], dst_port=Port["NTP"], position=21)
    router_2.acl.add_rule(action=ACLAction.PERMIT, src_port=Port["NTP"], dst_port=Port["NTP"], position=21)

    assert ntp_client.time is None
    ntp_client.request_time()
    assert ntp_client.time is None

    # Configure Route from Router 1 to PC B subnet
    router_1.route_table.add_route(
        address="192.168.2.0", subnet_mask="255.255.255.0", next_hop_ip_address="192.168.1.2"
    )

    # Configure Route from Router 2 to PC A subnet
    router_2.route_table.add_route(
        address="192.168.0.2", subnet_mask="255.255.255.0", next_hop_ip_address="192.168.1.1"
    )

    ntp_client.request_time()
    assert ntp_client.time is not None
