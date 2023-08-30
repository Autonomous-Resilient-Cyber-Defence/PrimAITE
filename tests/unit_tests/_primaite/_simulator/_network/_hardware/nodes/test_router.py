from ipaddress import IPv4Address

from primaite.simulator.network.hardware.nodes.router import AccessControlList, ACLAction, ACLRule
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port


def test_add_rule():
    acl = AccessControlList()
    acl.add_rule(
        action=ACLAction.PERMIT,
        protocol=IPProtocol.TCP,
        src_ip=IPv4Address("192.168.1.1"),
        src_port=Port(8080),
        dst_ip=IPv4Address("192.168.1.2"),
        dst_port=Port(80),
        position=1,
    )
    assert acl.acl[1].action == ACLAction.PERMIT
    assert acl.acl[1].protocol == IPProtocol.TCP
    assert acl.acl[1].src_ip == IPv4Address("192.168.1.1")
    assert acl.acl[1].src_port == Port(8080)
    assert acl.acl[1].dst_ip == IPv4Address("192.168.1.2")
    assert acl.acl[1].dst_port == Port(80)


def test_remove_rule():
    acl = AccessControlList()
    acl.add_rule(
        action=ACLAction.PERMIT,
        protocol=IPProtocol.TCP,
        src_ip=IPv4Address("192.168.1.1"),
        src_port=Port(8080),
        dst_ip=IPv4Address("192.168.1.2"),
        dst_port=Port(80),
        position=1,
    )
    acl.remove_rule(1)
    assert not acl.acl[1]


def test_rules():
    acl = AccessControlList()
    acl.add_rule(
        action=ACLAction.PERMIT,
        protocol=IPProtocol.TCP,
        src_ip=IPv4Address("192.168.1.1"),
        src_port=Port(8080),
        dst_ip=IPv4Address("192.168.1.2"),
        dst_port=Port(80),
        position=1,
    )
    acl.add_rule(
        action=ACLAction.DENY,
        protocol=IPProtocol.TCP,
        src_ip=IPv4Address("192.168.1.3"),
        src_port=Port(8080),
        dst_ip=IPv4Address("192.168.1.4"),
        dst_port=Port(80),
        position=2,
    )
    assert acl.is_permitted(
        protocol=IPProtocol.TCP,
        src_ip=IPv4Address("192.168.1.1"),
        src_port=Port(8080),
        dst_ip=IPv4Address("192.168.1.2"),
        dst_port=Port(80),
    )
    assert not acl.is_permitted(
        protocol=IPProtocol.TCP,
        src_ip=IPv4Address("192.168.1.3"),
        src_port=Port(8080),
        dst_ip=IPv4Address("192.168.1.4"),
        dst_port=Port(80),
    )


def test_default_rule():
    acl = AccessControlList()
    acl.add_rule(
        action=ACLAction.PERMIT,
        protocol=IPProtocol.TCP,
        src_ip=IPv4Address("192.168.1.1"),
        src_port=Port(8080),
        dst_ip=IPv4Address("192.168.1.2"),
        dst_port=Port(80),
        position=1,
    )
    acl.add_rule(
        action=ACLAction.DENY,
        protocol=IPProtocol.TCP,
        src_ip=IPv4Address("192.168.1.3"),
        src_port=Port(8080),
        dst_ip=IPv4Address("192.168.1.4"),
        dst_port=Port(80),
        position=2,
    )
    assert not acl.is_permitted(
        protocol=IPProtocol.UDP,
        src_ip=IPv4Address("192.168.1.5"),
        src_port=Port(8080),
        dst_ip=IPv4Address("192.168.1.12"),
        dst_port=Port(80),
    )
