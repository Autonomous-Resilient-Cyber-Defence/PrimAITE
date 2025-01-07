# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from ipaddress import IPv4Address
from typing import Tuple

import pytest

from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.base import Link
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.hardware.nodes.network.router import ACLAction, Router
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.applications.web_browser import WebBrowser
from primaite.simulator.system.services.database.database_service import DatabaseService
from primaite.simulator.system.services.dns.dns_client import DNSClient
from primaite.simulator.system.services.dns.dns_server import DNSServer
from primaite.simulator.system.services.web_server.web_server import WebServer
from primaite.simulator.system.software import SoftwareHealthState
from primaite.utils.validation.port import PORT_LOOKUP


@pytest.fixture(scope="function")
def web_client_web_server_database(example_network) -> Tuple[Network, Computer, Server, Server]:
    # add rules to network router
    router_1: Router = example_network.get_node_by_hostname("router_1")
    router_1.acl.add_rule(
        action=ACLAction.PERMIT,
        src_port=PORT_LOOKUP["POSTGRES_SERVER"],
        dst_port=PORT_LOOKUP["POSTGRES_SERVER"],
        position=0,
    )

    # Allow DNS requests
    router_1.acl.add_rule(action=ACLAction.PERMIT, src_port=PORT_LOOKUP["DNS"], dst_port=PORT_LOOKUP["DNS"], position=1)

    # Allow FTP requests
    router_1.acl.add_rule(action=ACLAction.PERMIT, src_port=PORT_LOOKUP["FTP"], dst_port=PORT_LOOKUP["FTP"], position=2)

    # Open port 80 for web server
    router_1.acl.add_rule(
        action=ACLAction.PERMIT, src_port=PORT_LOOKUP["HTTP"], dst_port=PORT_LOOKUP["HTTP"], position=3
    )

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
    link_computer_server = Link(endpoint_a=computer_nic, endpoint_b=server_nic, bandwidth=100)
    # Should be linked
    assert link_computer_server.is_up

    # Connect database server and web server
    link_server_db = Link(endpoint_a=server_nic, endpoint_b=db_server_nic, bandwidth=100)
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
        domain_name="arcd.com",
        domain_ip_address=web_server.network_interfaces[next(iter(web_server.network_interfaces))].ip_address,
    )

    # Install DatabaseClient service on web server
    web_server.software_manager.install(DatabaseClient)
    db_client: DatabaseClient = web_server.software_manager.software.get("DatabaseClient")
    db_client.server_ip_address = IPv4Address(db_server_nic.ip_address)  # set IP address of Database Server
    db_client.run()
    assert dns_client.check_domain_exists("arcd.com")
    assert db_client.connect()

    return example_network, computer, web_server, db_server


def test_web_client_requests_users(web_client_web_server_database):
    _, computer, _, _ = web_client_web_server_database

    web_browser: WebBrowser = computer.software_manager.software.get("WebBrowser")

    assert web_browser.get_webpage()


def test_database_fix_disrupts_web_client(uc2_network):
    """Tests that the database service being in fixed state disrupts the web client."""
    computer: Computer = uc2_network.get_node_by_hostname("client_1")
    db_server: Server = uc2_network.get_node_by_hostname("database_server")

    web_browser: WebBrowser = computer.software_manager.software.get("WebBrowser")
    database_service: DatabaseService = db_server.software_manager.software.get("DatabaseService")

    # fix the database service
    database_service.fix()

    assert database_service.health_state_actual == SoftwareHealthState.FIXING

    assert web_browser.get_webpage() is False

    for i in range(database_service.config.fixing_duration + 1):
        uc2_network.apply_timestep(i)

    assert database_service.health_state_actual == SoftwareHealthState.GOOD

    assert web_browser.get_webpage()


class TestWebBrowserHistory:
    def test_populating_history(self, web_client_web_server_database):
        network, computer, _, _ = web_client_web_server_database

        web_browser: WebBrowser = computer.software_manager.software.get("WebBrowser")
        assert web_browser.history == []
        web_browser.get_webpage()
        assert len(web_browser.history) == 1
        web_browser.get_webpage()
        assert len(web_browser.history) == 2
        assert web_browser.history[-1].status == WebBrowser.BrowserHistoryItem._HistoryItemStatus.LOADED
        assert web_browser.history[-1].response_code == 200

        router = network.get_node_by_hostname("router_1")
        router.acl.add_rule(
            action=ACLAction.DENY, src_port=PORT_LOOKUP["HTTP"], dst_port=PORT_LOOKUP["HTTP"], position=0
        )
        assert not web_browser.get_webpage()
        assert len(web_browser.history) == 3
        # with current NIC behaviour, even if you block communication, you won't get SERVER_UNREACHABLE because
        # application.send always returns true, even if communication fails. we should change what is returned from NICs
        assert web_browser.history[-1].status == WebBrowser.BrowserHistoryItem._HistoryItemStatus.LOADED
        assert web_browser.history[-1].response_code == 404

    def test_history_in_state(self, web_client_web_server_database):
        network, computer, _, _ = web_client_web_server_database
        web_browser: WebBrowser = computer.software_manager.software.get("WebBrowser")

        state = computer.describe_state()
        assert "history" in state["applications"]["WebBrowser"]
        assert len(state["applications"]["WebBrowser"]["history"]) == 0

        web_browser.get_webpage()
        router = network.get_node_by_hostname("router_1")
        router.acl.add_rule(
            action=ACLAction.DENY, src_port=PORT_LOOKUP["HTTP"], dst_port=PORT_LOOKUP["HTTP"], position=0
        )
        web_browser.get_webpage()

        state = computer.describe_state()
        assert state["applications"]["WebBrowser"]["history"][0]["outcome"] == 200
        assert state["applications"]["WebBrowser"]["history"][1]["outcome"] == 404
