import sys
from ipaddress import IPv4Address

import pytest

from primaite.simulator.network.hardware.base import Node
from primaite.simulator.network.networks import arcd_uc2_network
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.services.dns_client import DNSClient
from primaite.simulator.system.services.dns_server import DNSServer


@pytest.fixture(scope="function")
def dns_server() -> Node:
    node = Node(hostname="dns_server")
    node.software_manager.add_service(service_class=DNSServer)
    node.software_manager.services["DNSServer"].start()
    return node


@pytest.fixture(scope="function")
def dns_client() -> Node:
    node = Node(hostname="dns_client")
    node.software_manager.add_service(service_class=DNSClient)
    node.software_manager.services["DNSClient"].start()
    return node


def test_create_dns_server(dns_server):
    assert dns_server is not None
    dns_server_service: DNSServer = dns_server.software_manager.services["DNSServer"]
    assert dns_server_service.name is "DNSServer"
    assert dns_server_service.port is Port.DNS
    assert dns_server_service.protocol is IPProtocol.UDP


def test_create_dns_client(dns_client):
    assert dns_client is not None
    dns_client_service: DNSClient = dns_client.software_manager.services["DNSClient"]
    assert dns_client_service.name is "DNSClient"
    assert dns_client_service.port is Port.DNS
    assert dns_client_service.protocol is IPProtocol.UDP


def test_dns_server_domain_name_registration(dns_server):
    """Test to check if the domain name registration works."""
    dns_server_service: DNSServer = dns_server.software_manager.services["DNSServer"]

    # register the web server in the domain controller
    dns_server_service.dns_register(domain_name="real-domain.com", domain_ip_address=IPv4Address("192.168.1.12"))

    # return none for an unknown domain
    assert dns_server_service.dns_lookup("fake-domain.com") is None
    assert dns_server_service.dns_lookup("real-domain.com") is not None


def test_dns_client_check_domain_in_cache(dns_client):
    """Test to make sure that the check_domain_in_cache returns the correct values."""
    dns_client_service: DNSClient = dns_client.software_manager.services["DNSClient"]

    # add a domain to the dns client cache
    dns_client_service.add_domain_to_cache("real-domain.com", IPv4Address("192.168.1.12"))

    assert dns_client_service.check_domain_in_cache("fake-domain.com") is False
    assert dns_client_service.check_domain_in_cache("real-domain.com") is True
