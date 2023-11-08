from ipaddress import IPv4Address

from src.primaite.simulator.network.hardware.nodes.router import ACLAction, Router
from src.primaite.simulator.network.transmission.network_layer import IPProtocol
from src.primaite.simulator.network.transmission.transport_layer import Port


def test_add_rule():
    router = Router("Router")
    acl = router.acl
    acl.add_rule(
        action=ACLAction.PERMIT,
        protocol=IPProtocol.TCP,
        src_ip_address=IPv4Address("192.168.1.1"),
        src_port=Port(8080),
        dst_ip_address=IPv4Address("192.168.1.2"),
        dst_port=Port(80),
        position=1,
    )
    assert acl.acl[1].action == ACLAction.PERMIT
    assert acl.acl[1].protocol == IPProtocol.TCP
    assert acl.acl[1].src_ip_address == IPv4Address("192.168.1.1")
    assert acl.acl[1].src_port == Port(8080)
    assert acl.acl[1].dst_ip_address == IPv4Address("192.168.1.2")
    assert acl.acl[1].dst_port == Port(80)


def test_remove_rule():
    router = Router("Router")
    acl = router.acl
    acl.add_rule(
        action=ACLAction.PERMIT,
        protocol=IPProtocol.TCP,
        src_ip_address=IPv4Address("192.168.1.1"),
        src_port=Port(8080),
        dst_ip_address=IPv4Address("192.168.1.2"),
        dst_port=Port(80),
        position=1,
    )
    acl.remove_rule(1)
    assert not acl.acl[1]


def test_rules():
    router = Router("Router")
    acl = router.acl
    acl.add_rule(
        action=ACLAction.PERMIT,
        protocol=IPProtocol.TCP,
        src_ip_address=IPv4Address("192.168.1.1"),
        src_port=Port(8080),
        dst_ip_address=IPv4Address("192.168.1.2"),
        dst_port=Port(80),
        position=1,
    )
    acl.add_rule(
        action=ACLAction.DENY,
        protocol=IPProtocol.TCP,
        src_ip_address=IPv4Address("192.168.1.3"),
        src_port=Port(8080),
        dst_ip_address=IPv4Address("192.168.1.4"),
        dst_port=Port(80),
        position=2,
    )
    is_permitted, rule = acl.is_permitted(
        protocol=IPProtocol.TCP,
        src_ip_address=IPv4Address("192.168.1.1"),
        src_port=Port(8080),
        dst_ip_address=IPv4Address("192.168.1.2"),
        dst_port=Port(80),
    )
    assert is_permitted
    is_permitted, rule = acl.is_permitted(
        protocol=IPProtocol.TCP,
        src_ip_address=IPv4Address("192.168.1.3"),
        src_port=Port(8080),
        dst_ip_address=IPv4Address("192.168.1.4"),
        dst_port=Port(80),
    )
    assert not is_permitted


def test_default_rule():
    router = Router("Router")
    acl = router.acl
    acl.add_rule(
        action=ACLAction.PERMIT,
        protocol=IPProtocol.TCP,
        src_ip_address=IPv4Address("192.168.1.1"),
        src_port=Port(8080),
        dst_ip_address=IPv4Address("192.168.1.2"),
        dst_port=Port(80),
        position=1,
    )
    acl.add_rule(
        action=ACLAction.DENY,
        protocol=IPProtocol.TCP,
        src_ip_address=IPv4Address("192.168.1.3"),
        src_port=Port(8080),
        dst_ip_address=IPv4Address("192.168.1.4"),
        dst_port=Port(80),
        position=2,
    )
    is_permitted, rule = acl.is_permitted(
        protocol=IPProtocol.UDP,
        src_ip_address=IPv4Address("192.168.1.5"),
        src_port=Port(8080),
        dst_ip_address=IPv4Address("192.168.1.12"),
        dst_port=Port(80),
    )
    assert not is_permitted
