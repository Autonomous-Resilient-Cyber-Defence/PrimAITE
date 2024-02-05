from ipaddress import IPv4Address

import pytest

from primaite.simulator.network.hardware.base import Node
from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.protocols.dns import DNSPacket, DNSRequest
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.services.dns.dns_server import DNSServer


@pytest.fixture(scope="function")
def dns_server() -> Node:
    node = Server(
        hostname="dns_server",
        ip_address="192.168.1.10",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        operating_state=NodeOperatingState.ON,
    )
    node.software_manager.install(software_class=DNSServer)
    return node


def test_create_dns_server(dns_server):
    assert dns_server is not None
    dns_server_service: DNSServer = dns_server.software_manager.software.get("DNSServer")
    assert dns_server_service.name is "DNSServer"
    assert dns_server_service.port is Port.DNS
    assert dns_server_service.protocol is IPProtocol.TCP


def test_dns_server_domain_name_registration(dns_server):
    """Test to check if the domain name registration works."""
    dns_server_service: DNSServer = dns_server.software_manager.software.get("DNSServer")

    # register the web server in the domain controller
    dns_server_service.dns_register(domain_name="real-domain.com", domain_ip_address=IPv4Address("192.168.1.12"))

    # return none for an unknown domain
    assert dns_server_service.dns_lookup("fake-domain.com") is None
    assert dns_server_service.dns_lookup("real-domain.com") is not None


def test_dns_server_receive(dns_server):
    """Test to make sure that the DNS Server correctly responds to a DNS Client request."""
    dns_server_service: DNSServer = dns_server.software_manager.software.get("DNSServer")

    # register the web server in the domain controller
    dns_server_service.dns_register(domain_name="real-domain.com", domain_ip_address=IPv4Address("192.168.1.12"))

    assert (
        dns_server_service.receive(payload=DNSPacket(dns_request=DNSRequest(domain_name_request="fake-domain.com")))
        is False
    )

    assert (
        dns_server_service.receive(payload=DNSPacket(dns_request=DNSRequest(domain_name_request="real-domain.com")))
        is True
    )

    dns_server_service.show()
