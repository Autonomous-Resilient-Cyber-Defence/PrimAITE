from ipaddress import IPv4Address

from primaite.simulator.network.hardware.nodes.network.router import ACLAction
from primaite.simulator.network.hardware.nodes.network.wireless_router import WirelessRouter
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port


def test_wireless_router_from_config():
    cfg = {
        "ref": "router_2",
        "type": "wireless_router",
        "hostname": "router_2",
        "router_interface": {
            "ip_address": "192.168.1.1",
            "subnet_mask": "255.255.255.0",
        },
        "wireless_access_point": {
            "ip_address": "192.170.1.1",
            "subnet_mask": "255.255.255.0",
            "frequency": "WIFI_2_4",
        },
        "acl": {
            0: {
                "action": "PERMIT",
                "src_port": "POSTGRES_SERVER",
                "dst_port": "POSTGRES_SERVER",
            },
            1: {
                "action": "PERMIT",
                "protocol": "ICMP",
            },
            2: {
                "action": "PERMIT",
                "src_ip": "100.100.100.1",
                "dst_ip": "100.100.101.1",
            },
            3: {
                "action": "PERMIT",
                "src_ip": "100.100.102.0",
                "dst_ip": "100.100.103.0",
                "src_wildcard_mask": "0.0.0.255",
                "dst_wildcard_mask": "0.0.0.255",
            },
            20: {
                "action": "DENY",
            },
        },
    }

    rt = WirelessRouter.from_config(cfg=cfg)

    r0 = rt.acl.acl[0]
    assert r0.action == ACLAction.PERMIT
    assert r0.src_port == r0.dst_port == Port.POSTGRES_SERVER
    assert r0.src_ip_address == r0.dst_ip_address == r0.dst_wildcard_mask == r0.src_wildcard_mask == r0.protocol == None

    r1 = rt.acl.acl[1]
    assert r1.action == ACLAction.PERMIT
    assert r1.protocol == IPProtocol.ICMP
    assert (
        r1.src_ip_address
        == r1.dst_ip_address
        == r1.dst_wildcard_mask
        == r1.src_wildcard_mask
        == r1.src_port
        == r1.dst_port
        == None
    )

    r2 = rt.acl.acl[2]
    assert r2.action == ACLAction.PERMIT
    assert r2.src_ip_address == IPv4Address("100.100.100.1")
    assert r2.dst_ip_address == IPv4Address("100.100.101.1")
    assert r2.src_wildcard_mask == r2.dst_wildcard_mask == None
    assert r2.src_port == r2.dst_port == r2.protocol == None

    r3 = rt.acl.acl[3]
    assert r3.action == ACLAction.PERMIT
    assert r3.src_ip_address == IPv4Address("100.100.102.0")
    assert r3.dst_ip_address == IPv4Address("100.100.103.0")
    assert r3.src_wildcard_mask == IPv4Address("0.0.0.255")
    assert r3.dst_wildcard_mask == IPv4Address("0.0.0.255")
    assert r3.src_port == r3.dst_port == r3.protocol == None

    r20 = rt.acl.acl[20]
    assert r20.action == ACLAction.DENY
    assert (
        r20.src_ip_address
        == r20.dst_ip_address
        == r20.src_wildcard_mask
        == r20.dst_wildcard_mask
        == r20.src_port
        == r20.dst_port
        == r20.protocol
        == None
    )
