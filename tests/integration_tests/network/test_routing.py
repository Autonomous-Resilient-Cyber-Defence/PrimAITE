from typing import Tuple

import pytest

from src.primaite.simulator.network.hardware.base import Link, NIC, Node, NodeOperatingState
from src.primaite.simulator.network.hardware.nodes.router import ACLAction, Router
from src.primaite.simulator.network.transmission.network_layer import IPProtocol
from src.primaite.simulator.network.transmission.transport_layer import Port


@pytest.fixture(scope="function")
def pc_a_pc_b_router_1() -> Tuple[Node, Node, Router]:
    pc_a = Node(hostname="pc_a", default_gateway="192.168.0.1", operating_state=NodeOperatingState.ON)
    nic_a = NIC(ip_address="192.168.0.10", subnet_mask="255.255.255.0")
    pc_a.connect_nic(nic_a)

    pc_b = Node(hostname="pc_b", default_gateway="192.168.1.1", operating_state=NodeOperatingState.ON)
    nic_b = NIC(ip_address="192.168.1.10", subnet_mask="255.255.255.0")
    pc_b.connect_nic(nic_b)

    router_1 = Router(hostname="router_1", operating_state=NodeOperatingState.ON)

    router_1.configure_port(1, "192.168.0.1", "255.255.255.0")
    router_1.configure_port(2, "192.168.1.1", "255.255.255.0")

    Link(endpoint_a=nic_a, endpoint_b=router_1.ethernet_ports[1])
    Link(endpoint_a=nic_b, endpoint_b=router_1.ethernet_ports[2])
    router_1.enable_port(1)
    router_1.enable_port(2)

    router_1.acl.add_rule(action=ACLAction.PERMIT, src_port=Port.ARP, dst_port=Port.ARP, position=22)

    router_1.acl.add_rule(action=ACLAction.PERMIT, protocol=IPProtocol.ICMP, position=23)
    return pc_a, pc_b, router_1


def test_ping_default_gateway(pc_a_pc_b_router_1):
    pc_a, pc_b, router_1 = pc_a_pc_b_router_1

    assert pc_a.ping(pc_a.default_gateway)


def test_ping_other_router_port(pc_a_pc_b_router_1):
    pc_a, pc_b, router_1 = pc_a_pc_b_router_1

    assert pc_a.ping(pc_b.default_gateway)


def test_host_on_other_subnet(pc_a_pc_b_router_1):
    pc_a, pc_b, router_1 = pc_a_pc_b_router_1

    assert pc_a.ping("192.168.1.10")
