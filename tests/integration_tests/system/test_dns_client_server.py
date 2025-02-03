# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from ipaddress import IPv4Address
from typing import Tuple

import pytest

from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.system.services.dns.dns_client import DNSClient
from primaite.simulator.system.services.dns.dns_server import DNSServer
from primaite.simulator.system.services.service import ServiceOperatingState


@pytest.fixture(scope="function")
def dns_client_and_dns_server(client_server) -> Tuple[DNSClient, Computer, DNSServer, Server]:
    computer, server = client_server

    # Install DNS Client on computer
    computer.software_manager.install(DNSClient)
    dns_client: DNSClient = computer.software_manager.software.get("dns-client")
    dns_client.start()
    # set server as DNS Server
    dns_client.dns_server = IPv4Address(server.network_interfaces.get(next(iter(server.network_interfaces))).ip_address)

    # Install DNS Server on server
    server.software_manager.install(DNSServer)
    dns_server: DNSServer = server.software_manager.software.get("dns-server")
    dns_server.start()
    # register arcd.com as a domain
    dns_server.dns_register(
        domain_name="arcd.com",
        domain_ip_address=IPv4Address(server.network_interface[1].ip_address),
    )

    return dns_client, computer, dns_server, server


def test_dns_client_server(dns_client_and_dns_server):
    dns_client, computer, dns_server, server = dns_client_and_dns_server

    assert dns_client.operating_state == ServiceOperatingState.RUNNING
    assert dns_server.operating_state == ServiceOperatingState.RUNNING

    dns_server.show()

    # fake domain should not be added to dns cache
    assert not dns_client.check_domain_exists(target_domain="fake-domain.com")
    assert dns_client.dns_cache.get("fake-domain.com", None) is None

    # arcd.com is registered in dns server and should be saved to cache
    assert dns_client.check_domain_exists(target_domain="arcd.com")
    assert dns_client.dns_cache.get("arcd.com", None) is not None

    assert len(dns_client.dns_cache) == 1


def test_dns_client_requests_offline_dns_server(dns_client_and_dns_server):
    dns_client, computer, dns_server, server = dns_client_and_dns_server

    assert dns_client.operating_state == ServiceOperatingState.RUNNING
    assert dns_server.operating_state == ServiceOperatingState.RUNNING

    dns_server.show()

    # arcd.com is registered in dns server
    assert dns_client.check_domain_exists(target_domain="arcd.com")
    assert dns_client.dns_cache.get("arcd.com", None) is not None

    assert len(dns_client.dns_cache) == 1
    dns_client.dns_cache = {}

    server.power_off()

    for i in range(server.shut_down_duration + 1):
        server.apply_timestep(timestep=i)

    assert server.operating_state == NodeOperatingState.OFF
    assert dns_server.operating_state == ServiceOperatingState.STOPPED

    # this time it should not cache because dns server is not online
    assert dns_client.check_domain_exists(target_domain="arcd.com") is False
    assert dns_client.dns_cache.get("arcd.com", None) is None

    assert len(dns_client.dns_cache) == 0
