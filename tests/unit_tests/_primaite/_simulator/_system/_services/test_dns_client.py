# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from ipaddress import IPv4Address

import pytest

from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.protocols.dns import DNSPacket, DNSReply, DNSRequest
from primaite.simulator.system.services.dns.dns_client import DNSClient
from primaite.simulator.system.services.service import ServiceOperatingState
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.port import PORT_LOOKUP


@pytest.fixture(scope="function")
def dns_client() -> Computer:
    node = Computer(
        hostname="dns_client",
        ip_address="192.168.1.11",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        dns_server=IPv4Address("192.168.1.10"),
    )
    return node


def test_create_dns_client(dns_client):
    assert dns_client is not None
    dns_client_service: DNSClient = dns_client.software_manager.software.get("dns-client")
    assert dns_client_service.name is "dns-client"
    assert dns_client_service.port is PORT_LOOKUP["DNS"]
    assert dns_client_service.protocol is PROTOCOL_LOOKUP["TCP"]


def test_dns_client_add_domain_to_cache_when_not_running(dns_client):
    dns_client_service: DNSClient = dns_client.software_manager.software.get("dns-client")
    assert dns_client.operating_state is NodeOperatingState.OFF
    assert dns_client_service.operating_state is ServiceOperatingState.STOPPED

    assert (
        dns_client_service.add_domain_to_cache(domain_name="test.com", ip_address=IPv4Address("192.168.1.100")) is False
    )

    assert dns_client_service.dns_cache.get("test.com") is None


def test_dns_client_check_domain_exists_when_not_running(dns_client):
    dns_client.operating_state = NodeOperatingState.ON
    dns_client_service: DNSClient = dns_client.software_manager.software.get("dns-client")
    dns_client_service.start()

    assert dns_client.operating_state is NodeOperatingState.ON
    assert dns_client_service.operating_state is ServiceOperatingState.RUNNING

    assert (
        dns_client_service.add_domain_to_cache(domain_name="test.com", ip_address=IPv4Address("192.168.1.100"))
        is not False
    )

    assert dns_client_service.check_domain_exists("test.com") is True

    dns_client.power_off()

    for i in range(dns_client.shut_down_duration + 1):
        dns_client.apply_timestep(timestep=i)

    assert dns_client.operating_state is NodeOperatingState.OFF
    assert dns_client_service.operating_state is ServiceOperatingState.STOPPED

    assert dns_client_service.check_domain_exists("test.com") is False


def test_dns_client_check_domain_in_cache(dns_client):
    """Test to make sure that the check_domain_in_cache returns the correct values."""
    dns_client.operating_state = NodeOperatingState.ON
    dns_client_service: DNSClient = dns_client.software_manager.software.get("dns-client")
    dns_client_service.start()

    # add a domain to the dns client cache
    dns_client_service.add_domain_to_cache("real-domain.com", IPv4Address("192.168.1.12"))

    assert dns_client_service.check_domain_exists("fake-domain.com") is False
    assert dns_client_service.check_domain_exists("real-domain.com") is True


def test_dns_client_receive(dns_client):
    """Test to make sure the DNS Client knows how to deal with request responses."""
    dns_client_service: DNSClient = dns_client.software_manager.software.get("dns-client")

    dns_client_service.receive(
        payload=DNSPacket(
            dns_request=DNSRequest(domain_name_request="real-domain.com"),
            dns_reply=DNSReply(domain_name_ip_address=IPv4Address("192.168.1.12")),
        )
    )

    # domain name should be saved to cache
    assert dns_client_service.dns_cache["real-domain.com"] == IPv4Address("192.168.1.12")


def test_dns_client_receive_non_dns_payload(dns_client):
    dns_client_service: DNSClient = dns_client.software_manager.software.get("dns-client")

    assert dns_client_service.receive(payload=None) is False
