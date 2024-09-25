# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from ipaddress import IPv4Address

import pytest

from primaite.simulator.network.hardware.base import generate_mac_address
from primaite.simulator.network.hardware.nodes.network.router import ACLAction, Router
from primaite.simulator.network.protocols.icmp import ICMPPacket
from primaite.simulator.network.transmission.data_link_layer import EthernetHeader, Frame
from primaite.simulator.network.transmission.network_layer import IPPacket
from primaite.simulator.network.transmission.transport_layer import TCPHeader, UDPHeader
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.port import PORT_LOOKUP


@pytest.fixture(scope="function")
def router_with_acl_rules():
    """
    Provides a router instance with predefined ACL rules for testing.

    :Setup:
        1. Creates a Router object named "Router".
        2. Adds a PERMIT rule for TCP traffic from 192.168.1.1:HTTPS to 192.168.1.2:HTTP.
        3. Adds a DENY rule for TCP traffic from 192.168.1.3:8080 to 192.168.1.4:80.

    :return: A configured Router object with ACL rules.
    """
    router = Router("Router")
    acl = router.acl
    # Add rules here as needed
    acl.add_rule(
        action=ACLAction.PERMIT,
        protocol=PROTOCOL_LOOKUP["TCP"],
        src_ip_address="192.168.1.1",
        src_port=PORT_LOOKUP["HTTPS"],
        dst_ip_address="192.168.1.2",
        dst_port=PORT_LOOKUP["HTTP"],
        position=1,
    )
    acl.add_rule(
        action=ACLAction.DENY,
        protocol=PROTOCOL_LOOKUP["TCP"],
        src_ip_address="192.168.1.3",
        src_port=8080,
        dst_ip_address="192.168.1.4",
        dst_port=80,
        position=2,
    )
    return router


@pytest.fixture(scope="function")
def router_with_wildcard_acl():
    """
    Provides a router instance with ACL rules that include wildcard masking for testing.

    :Setup:
        1. Creates a Router object named "Router".
        2. Adds a PERMIT rule for TCP traffic from 192.168.1.1:8080 to 10.1.1.2:80.
        3. Adds a DENY rule with a wildcard mask for TCP traffic from the 192.168.1.0/24 network to 10.1.1.3:443.
        4. Adds a PERMIT rule for any traffic to the 10.2.0.0/16 network.

    :return: A Router object with configured ACL rules, including rules with wildcard masking.
    """
    router = Router("Router")
    acl = router.acl
    # Rule to permit traffic from a specific source IP and port to a specific destination IP and port
    acl.add_rule(
        action=ACLAction.PERMIT,
        protocol=PROTOCOL_LOOKUP["TCP"],
        src_ip_address="192.168.1.1",
        src_port=8080,
        dst_ip_address="10.1.1.2",
        dst_port=80,
        position=1,
    )
    # Rule to deny traffic from an IP range to a specific destination IP and port
    acl.add_rule(
        action=ACLAction.DENY,
        protocol=PROTOCOL_LOOKUP["TCP"],
        src_ip_address="192.168.1.0",
        src_wildcard_mask="0.0.0.255",
        dst_ip_address="10.1.1.3",
        dst_port=443,
        position=2,
    )
    # Rule to permit any traffic to a range of destination IPs
    acl.add_rule(
        action=ACLAction.PERMIT,
        protocol=None,
        src_ip_address=None,
        dst_ip_address="10.2.0.0",
        dst_wildcard_mask="0.0.255.255",
        position=3,
    )
    return router


def test_add_rule(router_with_acl_rules):
    """
    Tests that an ACL rule is added correctly to the router's ACL.

    Asserts:
        - The action of the added rule is PERMIT.
        - The protocol of the added rule is TCP.
        - The source IP address matches "192.168.1.1".
        - The source port is HTTPS.
        - The destination IP address matches "192.168.1.2".
        - The destination port is HTTP.
    """
    acl = router_with_acl_rules.acl

    assert acl.acl[1].action == ACLAction.PERMIT
    assert acl.acl[1].protocol == PROTOCOL_LOOKUP["TCP"]
    assert acl.acl[1].src_ip_address == IPv4Address("192.168.1.1")
    assert acl.acl[1].src_port == PORT_LOOKUP["HTTPS"]
    assert acl.acl[1].dst_ip_address == IPv4Address("192.168.1.2")
    assert acl.acl[1].dst_port == PORT_LOOKUP["HTTP"]


def test_remove_rule(router_with_acl_rules):
    """
    Tests the removal of an ACL rule from the router's ACL.

    Asserts that accessing the removed rule index in the ACL returns None.
    """
    acl = router_with_acl_rules.acl
    acl.remove_rule(1)
    assert acl.acl[1] is None


def test_traffic_permitted_by_specific_rule(router_with_acl_rules):
    """
    Verifies that traffic matching a specific ACL rule is correctly permitted.

    Asserts traffic that matches a permit rule is allowed through the ACL.
    """
    acl = router_with_acl_rules.acl
    permitted_frame = Frame(
        ethernet=EthernetHeader(src_mac_addr=generate_mac_address(), dst_mac_addr=generate_mac_address()),
        ip=IPPacket(src_ip_address="192.168.1.1", dst_ip_address="192.168.1.2", protocol=PROTOCOL_LOOKUP["TCP"]),
        tcp=TCPHeader(src_port=PORT_LOOKUP["HTTPS"], dst_port=PORT_LOOKUP["HTTP"]),
    )
    is_permitted, _ = acl.is_permitted(permitted_frame)
    assert is_permitted


def test_traffic_denied_by_specific_rule(router_with_acl_rules):
    """
    Verifies that traffic matching a specific ACL rule is correctly denied.

    Asserts traffic that matches a deny rule is blocked by the ACL.
    """

    acl = router_with_acl_rules.acl
    not_permitted_frame = Frame(
        ethernet=EthernetHeader(src_mac_addr=generate_mac_address(), dst_mac_addr=generate_mac_address()),
        ip=IPPacket(src_ip_address="192.168.1.3", dst_ip_address="192.168.1.4", protocol=PROTOCOL_LOOKUP["TCP"]),
        tcp=TCPHeader(src_port=8080, dst_port=80),
    )
    is_permitted, _ = acl.is_permitted(not_permitted_frame)
    assert not is_permitted


def test_default_rule(router_with_acl_rules):
    """
    Tests the default deny rule of the ACL.

    This test verifies that traffic which does not match any explicit permit rule in the ACL
    is correctly denied, as per the common "default deny" security stance that ACLs implement.

    Asserts the frame does not match any of the predefined ACL rules and is therefore not permitted by the ACL,
    illustrating the default deny behavior when no explicit permit rule is matched.
    """
    acl = router_with_acl_rules.acl
    not_permitted_frame = Frame(
        ethernet=EthernetHeader(src_mac_addr=generate_mac_address(), dst_mac_addr=generate_mac_address()),
        ip=IPPacket(src_ip_address="192.168.1.5", dst_ip_address="192.168.1.12", protocol=PROTOCOL_LOOKUP["UDP"]),
        udp=UDPHeader(src_port=PORT_LOOKUP["HTTPS"], dst_port=PORT_LOOKUP["HTTP"]),
    )
    is_permitted, rule = acl.is_permitted(not_permitted_frame)
    assert not is_permitted


def test_direct_ip_match_with_acl(router_with_wildcard_acl):
    """
    Tests ACL functionality for a direct IP address match.

    Asserts direct IP address match traffic is permitted by the ACL rule.
    """
    acl = router_with_wildcard_acl.acl
    frame = Frame(
        ethernet=EthernetHeader(src_mac_addr=generate_mac_address(), dst_mac_addr=generate_mac_address()),
        ip=IPPacket(src_ip_address="192.168.1.1", dst_ip_address="10.1.1.2", protocol=PROTOCOL_LOOKUP["TCP"]),
        tcp=TCPHeader(src_port=8080, dst_port=80),
    )
    assert acl.is_permitted(frame)[0], "Direct IP match should be permitted."


def test_ip_range_match_denied_with_acl(router_with_wildcard_acl):
    """
    Tests ACL functionality for denying traffic from an IP range using wildcard masking.

    Asserts traffic from the specified IP range is correctly denied by the ACL rule.
    """
    acl = router_with_wildcard_acl.acl
    frame = Frame(
        ethernet=EthernetHeader(src_mac_addr=generate_mac_address(), dst_mac_addr=generate_mac_address()),
        ip=IPPacket(src_ip_address="192.168.1.100", dst_ip_address="10.1.1.3", protocol=PROTOCOL_LOOKUP["TCP"]),
        tcp=TCPHeader(src_port=8080, dst_port=443),
    )
    assert not acl.is_permitted(frame)[0], "IP range match with wildcard mask should be denied."


def test_traffic_permitted_to_destination_range_with_acl(router_with_wildcard_acl):
    """
    Tests ACL functionality for permitting traffic to a destination IP range using wildcard masking.

    Asserts traffic to the specified destination IP range is correctly permitted by the ACL rule.
    """
    acl = router_with_wildcard_acl.acl
    frame = Frame(
        ethernet=EthernetHeader(src_mac_addr=generate_mac_address(), dst_mac_addr=generate_mac_address()),
        ip=IPPacket(src_ip_address="192.168.1.50", dst_ip_address="10.2.200.200", protocol=PROTOCOL_LOOKUP["UDP"]),
        udp=UDPHeader(src_port=1433, dst_port=1433),
    )
    assert acl.is_permitted(frame)[0], "Traffic to destination IP range should be permitted."


def test_ip_traffic_from_specific_subnet():
    """
    Tests that the ACL permits or denies IP traffic from specific subnets, mimicking a Cisco ACL rule for IP traffic.

    This test verifies the ACL's ability to permit all IP traffic from a specific subnet (192.168.1.0/24) while denying
    traffic from other subnets. The test mimics a Cisco ACL rule that allows IP traffic from a specified range using
    wildcard masking.

    The test frames are constructed with varying protocols (TCP, UDP, ICMP) and source IP addresses, to demonstrate the
    rule's general applicability to all IP protocols and its enforcement based on source IP address range.

    Asserts
        - Traffic from within the 192.168.1.0/24 subnet is permitted.
        - Traffic from outside the 192.168.1.0/24 subnet is denied.
    """

    router = Router("Router")
    acl = router.acl
    # Add rules here as needed
    acl.add_rule(
        action=ACLAction.PERMIT,
        src_ip_address="192.168.1.0",
        src_wildcard_mask="0.0.0.255",
        position=1,
    )

    permitted_frame_1 = Frame(
        ethernet=EthernetHeader(src_mac_addr=generate_mac_address(), dst_mac_addr=generate_mac_address()),
        ip=IPPacket(src_ip_address="192.168.1.50", dst_ip_address="10.2.200.200", protocol=PROTOCOL_LOOKUP["TCP"]),
        tcp=TCPHeader(src_port=PORT_LOOKUP["POSTGRES_SERVER"], dst_port=PORT_LOOKUP["POSTGRES_SERVER"]),
    )

    assert acl.is_permitted(permitted_frame_1)[0]

    permitted_frame_2 = Frame(
        ethernet=EthernetHeader(src_mac_addr=generate_mac_address(), dst_mac_addr=generate_mac_address()),
        ip=IPPacket(src_ip_address="192.168.1.10", dst_ip_address="85.199.214.101", protocol=PROTOCOL_LOOKUP["UDP"]),
        udp=UDPHeader(src_port=PORT_LOOKUP["NTP"], dst_port=PORT_LOOKUP["NTP"]),
    )

    assert acl.is_permitted(permitted_frame_2)[0]

    permitted_frame_3 = Frame(
        ethernet=EthernetHeader(src_mac_addr=generate_mac_address(), dst_mac_addr=generate_mac_address()),
        ip=IPPacket(src_ip_address="192.168.1.200", dst_ip_address="192.168.1.1", protocol=PROTOCOL_LOOKUP["ICMP"]),
        icmp=ICMPPacket(identifier=1),
    )

    assert acl.is_permitted(permitted_frame_3)[0]

    not_permitted_frame_1 = Frame(
        ethernet=EthernetHeader(src_mac_addr=generate_mac_address(), dst_mac_addr=generate_mac_address()),
        ip=IPPacket(src_ip_address="192.168.0.50", dst_ip_address="10.2.200.200", protocol=PROTOCOL_LOOKUP["TCP"]),
        tcp=TCPHeader(src_port=PORT_LOOKUP["POSTGRES_SERVER"], dst_port=PORT_LOOKUP["POSTGRES_SERVER"]),
    )

    assert not acl.is_permitted(not_permitted_frame_1)[0]

    not_permitted_frame_2 = Frame(
        ethernet=EthernetHeader(src_mac_addr=generate_mac_address(), dst_mac_addr=generate_mac_address()),
        ip=IPPacket(src_ip_address="192.168.2.10", dst_ip_address="85.199.214.101", protocol=PROTOCOL_LOOKUP["UDP"]),
        udp=UDPHeader(src_port=PORT_LOOKUP["NTP"], dst_port=PORT_LOOKUP["NTP"]),
    )

    assert not acl.is_permitted(not_permitted_frame_2)[0]

    acl.show()
