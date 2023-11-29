from ipaddress import IPv4Address
from typing import Tuple

import pytest

from primaite.simulator.network.hardware.base import Link
from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.computer import Computer
from primaite.simulator.network.hardware.nodes.server import Server
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.applications.web_browser import WebBrowser
from primaite.simulator.system.services.database.database_service import DatabaseService
from primaite.simulator.system.services.dns.dns_client import DNSClient
from primaite.simulator.system.services.dns.dns_server import DNSServer
from primaite.simulator.system.services.web_server.web_server import WebServer


@pytest.fixture(scope="function")
def web_client_web_server_database() -> Tuple[Computer, Server, Server]:
    # Create Computer
    computer: Computer = Computer(
        hostname="test_computer",
        ip_address="192.168.0.1",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        operating_state=NodeOperatingState.ON,
    )

    # Create Web Server
    web_server = Server(
        hostname="web_server",
        ip_address="192.168.0.2",
        subnet_mask="255.255.255.0",
        operating_state=NodeOperatingState.ON,
    )

    # Create Database Server
    db_server = Server(
        hostname="db_server",
        ip_address="192.168.0.3",
        subnet_mask="255.255.255.0",
        operating_state=NodeOperatingState.ON,
    )

    # Get the NICs
    computer_nic = computer.nics[next(iter(computer.nics))]
    server_nic = web_server.nics[next(iter(web_server.nics))]
    db_server_nic = db_server.nics[next(iter(db_server.nics))]

    # Connect Computer and Server
    link_computer_server = Link(endpoint_a=computer_nic, endpoint_b=server_nic)
    # Should be linked
    assert link_computer_server.is_up

    # Connect database server and web server
    link_server_db = Link(endpoint_a=server_nic, endpoint_b=db_server_nic)
    # Should be linked
    assert link_computer_server.is_up
    assert link_server_db.is_up

    # Install DatabaseService on db server
    db_server.software_manager.install(DatabaseService)
    db_service: DatabaseService = db_server.software_manager.software["DatabaseService"]
    db_service.start()

    # Install Web Browser on computer
    computer.software_manager.install(WebBrowser)
    web_browser: WebBrowser = computer.software_manager.software["WebBrowser"]
    web_browser.run()

    # Install DNS Client service on computer
    computer.software_manager.install(DNSClient)
    dns_client: DNSClient = computer.software_manager.software["DNSClient"]
    # set dns server
    dns_client.dns_server = web_server.nics[next(iter(web_server.nics))].ip_address

    # Install Web Server service on web server
    web_server.software_manager.install(WebServer)
    web_server_service: WebServer = web_server.software_manager.software["WebServer"]
    web_server_service.start()

    # Install DNS Server service on web server
    web_server.software_manager.install(DNSServer)
    dns_server: DNSServer = web_server.software_manager.software["DNSServer"]
    # register arcd.com to DNS
    dns_server.dns_register(
        domain_name="arcd.com", domain_ip_address=web_server.nics[next(iter(web_server.nics))].ip_address
    )

    # Install DatabaseClient service on web server
    web_server.software_manager.install(DatabaseClient)
    db_client: DatabaseClient = web_server.software_manager.software["DatabaseClient"]
    db_client.server_ip_address = IPv4Address(db_server_nic.ip_address)  # set IP address of Database Server
    db_client.run()
    assert db_client.connect()

    return computer, web_server, db_server


@pytest.mark.skip(reason="waiting for a way to set this up correctly")
def test_web_client_requests_users(web_client_web_server_database):
    computer, web_server, db_server = web_client_web_server_database

    web_browser: WebBrowser = computer.software_manager.software["WebBrowser"]

    web_browser.get_webpage()
