# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from ipaddress import IPv4Address

import pytest

from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.base import Node
from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.transmission.transport_layer import PORT_LOOKUP
from primaite.simulator.system.services.dns.dns_client import DNSClient
from primaite.simulator.system.services.dns.dns_server import DNSServer
from primaite.utils.validators import PROTOCOL_LOOKUP


@pytest.fixture(scope="function")
def dns_server() -> Node:
    node = Server(
        hostname="dns_server",
        ip_address="192.168.1.10",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    node.power_on()
    node.software_manager.install(software_class=DNSServer)
    return node


def test_create_dns_server(dns_server):
    assert dns_server is not None
    dns_server_service: DNSServer = dns_server.software_manager.software.get("DNSServer")
    assert dns_server_service.name is "DNSServer"
    assert dns_server_service.port is PORT_LOOKUP["DNS"]
    assert dns_server_service.protocol is PROTOCOL_LOOKUP["TCP"]


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

    client = Computer(hostname="client", ip_address="192.168.1.11", subnet_mask="255.255.255.0", start_up_duration=0)
    client.power_on()
    client.dns_server = IPv4Address("192.168.1.10")
    network = Network()
    network.connect(dns_server.network_interface[1], client.network_interface[1])
    dns_client: DNSClient = client.software_manager.software["DNSClient"]  # noqa
    dns_client.check_domain_exists("fake-domain.com")

    assert dns_client.check_domain_exists("fake-domain.com") is False

    assert dns_client.check_domain_exists("real-domain.com") is False

    dns_server_service.show()
