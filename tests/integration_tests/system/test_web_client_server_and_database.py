from ipaddress import IPv4Address
from typing import Tuple

import pytest

from primaite.simulator.network.hardware.base import Link
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.network.router import ACLAction, Router
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.applications.web_browser import WebBrowser
from primaite.simulator.system.services.database.database_service import DatabaseService
from primaite.simulator.system.services.dns.dns_client import DNSClient
from primaite.simulator.system.services.dns.dns_server import DNSServer
from primaite.simulator.system.services.web_server.web_server import WebServer


@pytest.fixture(scope="function")
def web_client_web_server_database(example_network) -> Tuple[Computer, Server, Server]:
    # add rules to network router
    router_1: Router = example_network.get_node_by_hostname("router_1")
    router_1.acl.add_rule(
        action=ACLAction.PERMIT, src_port=Port.POSTGRES_SERVER, dst_port=Port.POSTGRES_SERVER, position=0
    )

    # Allow DNS requests
    router_1.acl.add_rule(action=ACLAction.PERMIT, src_port=Port.DNS, dst_port=Port.DNS, position=1)

    # Allow FTP requests
    router_1.acl.add_rule(action=ACLAction.PERMIT, src_port=Port.FTP, dst_port=Port.FTP, position=2)

    # Open port 80 for web server
    router_1.acl.add_rule(action=ACLAction.PERMIT, src_port=Port.HTTP, dst_port=Port.HTTP, position=3)

    # Create Computer
    computer: Computer = example_network.get_node_by_hostname("client_1")

    # Create Web Server
    web_server: Server = example_network.get_node_by_hostname("server_1")

    # Create Database Server
    db_server = example_network.get_node_by_hostname("server_2")

    # Get the NICs
    computer_nic = computer.network_interfaces[next(iter(computer.network_interfaces))]
    server_nic = web_server.network_interfaces[next(iter(web_server.network_interfaces))]
    db_server_nic = db_server.network_interfaces[next(iter(db_server.network_interfaces))]

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
    db_service: DatabaseService = db_server.software_manager.software.get("DatabaseService")
    db_service.start()

    # Install Web Browser on computer
    computer.software_manager.install(WebBrowser)
    web_browser: WebBrowser = computer.software_manager.software.get("WebBrowser")
    web_browser.target_url = "http://arcd.com/users/"
    web_browser.run()

    # Install DNS Client service on computer
    computer.software_manager.install(DNSClient)
    dns_client: DNSClient = computer.software_manager.software.get("DNSClient")
    # set dns server
    dns_client.dns_server = web_server.network_interfaces[next(iter(web_server.network_interfaces))].ip_address

    # Install Web Server service on web server
    web_server.software_manager.install(WebServer)
    web_server_service: WebServer = web_server.software_manager.software.get("WebServer")
    web_server_service.start()

    # Install DNS Server service on web server
    web_server.software_manager.install(DNSServer)
    dns_server: DNSServer = web_server.software_manager.software.get("DNSServer")
    # register arcd.com to DNS
    dns_server.dns_register(
        domain_name="arcd.com", domain_ip_address=web_server.network_interfaces[next(iter(web_server.network_interfaces))].ip_address
    )

    # Install DatabaseClient service on web server
    web_server.software_manager.install(DatabaseClient)
    db_client: DatabaseClient = web_server.software_manager.software.get("DatabaseClient")
    db_client.server_ip_address = IPv4Address(db_server_nic.ip_address)  # set IP address of Database Server
    db_client.run()
    assert dns_client.check_domain_exists("arcd.com")
    assert db_client.connect()

    return computer, web_server, db_server


def test_web_client_requests_users(web_client_web_server_database):
    computer, web_server, db_server = web_client_web_server_database

    web_browser: WebBrowser = computer.software_manager.software.get("WebBrowser")

    assert web_browser.get_webpage()
