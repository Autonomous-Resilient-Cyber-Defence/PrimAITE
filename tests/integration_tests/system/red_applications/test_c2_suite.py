# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from ipaddress import IPv4Address
from typing import Tuple

import pytest

from primaite.game.agent.interface import ProxyAgent
from primaite.game.game import PrimaiteGame
from primaite.simulator.file_system.file_system_item_abc import FileSystemItemHealthStatus
from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.hardware.nodes.network.router import ACLAction, Router
from primaite.simulator.network.hardware.nodes.network.switch import Switch
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.application import ApplicationOperatingState
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.applications.red_applications.c2.c2_beacon import C2Beacon
from primaite.simulator.system.applications.red_applications.c2.c2_server import C2Server
from primaite.simulator.system.applications.red_applications.ransomware_script import RansomwareScript
from primaite.simulator.system.services.database.database_service import DatabaseService
from primaite.simulator.system.services.dns.dns_server import DNSServer
from primaite.simulator.system.services.web_server.web_server import WebServer


@pytest.fixture(scope="function")
def basic_network() -> Network:
    network = Network()

    # Creating two generic nodes for the C2 Server and the C2 Beacon.
    node_a = Computer(
        hostname="node_a",
        ip_address="192.168.0.2",
        subnet_mask="255.255.255.252",
        default_gateway="192.168.0.1",
        start_up_duration=0,
    )
    node_a.power_on()
    node_a.software_manager.get_open_ports()
    node_a.software_manager.install(software_class=C2Server)

    node_b = Computer(
        hostname="node_b",
        ip_address="192.168.255.2",
        subnet_mask="255.255.255.252",
        default_gateway="192.168.255.1",
        start_up_duration=0,
    )
    node_b.power_on()
    node_b.software_manager.install(software_class=C2Beacon)
    # Creating a router to sit between node 1 and node 2.
    router = Router(hostname="router", num_ports=3, start_up_duration=0)
    # Default allow all.
    router.acl.add_rule(action=ACLAction.PERMIT)
    router.power_on()
    # Creating switches for each client.
    switch_1 = Switch(hostname="switch_1", num_ports=6, start_up_duration=0)
    switch_1.power_on()

    # Connecting the switches to the router.
    router.configure_port(port=1, ip_address="192.168.0.1", subnet_mask="255.255.255.252")
    network.connect(endpoint_a=router.network_interface[1], endpoint_b=switch_1.network_interface[6])

    switch_2 = Switch(hostname="switch_2", num_ports=6, start_up_duration=0)
    switch_2.power_on()

    network.connect(endpoint_a=router.network_interface[2], endpoint_b=switch_2.network_interface[6])
    router.configure_port(port=2, ip_address="192.168.255.1", subnet_mask="255.255.255.252")

    router.enable_port(1)
    router.enable_port(2)

    # Connecting the node to each switch
    network.connect(node_a.network_interface[1], switch_1.network_interface[1])

    network.connect(node_b.network_interface[1], switch_2.network_interface[1])

    return network


def test_c2_suite_setup_receive(basic_network):
    """Test that C2 Beacon can successfully establish connection with the C2 Server."""
    network: Network = basic_network
    computer_a: Computer = network.get_node_by_hostname("node_a")
    c2_server: C2Server = computer_a.software_manager.software.get("C2Server")

    computer_b: Computer = network.get_node_by_hostname("node_b")
    c2_beacon: C2Beacon = computer_b.software_manager.software.get("C2Beacon")

    # Assert that the c2 beacon configure correctly.
    c2_beacon.configure(c2_server_ip_address="192.168.0.2")
    assert c2_beacon.c2_remote_connection == IPv4Address("192.168.0.2")

    c2_server.run()
    c2_beacon.establish()

    # Asserting that the c2 beacon has established a c2 connection
    assert c2_beacon.c2_connection_active is True

    # Asserting that the c2 server has established a c2 connection.
    assert c2_server.c2_connection_active is True
    assert c2_server.c2_remote_connection == IPv4Address("192.168.255.2")


def test_c2_suite_keep_alive_inactivity(basic_network):
    """Tests that C2 Beacon disconnects from the C2 Server after inactivity."""
    network: Network = basic_network
    computer_a: Computer = network.get_node_by_hostname("node_a")
    c2_server: C2Server = computer_a.software_manager.software.get("C2Server")

    computer_b: Computer = network.get_node_by_hostname("node_b")
    c2_beacon: C2Beacon = computer_b.software_manager.software.get("C2Beacon")

    c2_beacon.configure(c2_server_ip_address="192.168.0.2", keep_alive_frequency=2)
    c2_server.run()
    c2_beacon.establish()

    c2_beacon.apply_timestep(0)
    assert c2_beacon.keep_alive_inactivity == 1

    # Keep Alive successfully sent and received upon the 2nd timestep.
    c2_beacon.apply_timestep(1)
    assert c2_beacon.keep_alive_inactivity == 0
    assert c2_beacon.c2_connection_active == True

    # Now we turn off the c2 server (Thus preventing a keep alive)
    c2_server.close()
    c2_beacon.apply_timestep(2)
    c2_beacon.apply_timestep(3)
    assert c2_beacon.keep_alive_inactivity == 2
    assert c2_beacon.c2_connection_active == False
    assert c2_beacon.operating_state == ApplicationOperatingState.CLOSED


def test_c2_suite_configure_request(basic_network):
    """Tests that the request system can be used to successfully setup a c2 suite."""
    # Setting up the network:
    network: Network = basic_network
    computer_a: Computer = network.get_node_by_hostname("node_a")
    c2_server: C2Server = computer_a.software_manager.software.get("C2Server")

    computer_b: Computer = network.get_node_by_hostname("node_b")
    c2_beacon: C2Beacon = computer_b.software_manager.software.get("C2Beacon")

    # Testing Via Requests:
    c2_server.run()
    network.apply_timestep(0)

    c2_beacon_config = {
        "c2_server_ip_address": "192.168.0.2",
        "keep_alive_frequency": 5,
        "masquerade_protocol": "TCP",
        "masquerade_port": "HTTP",
    }

    network.apply_request(["node", "node_b", "application", "C2Beacon", "configure", c2_beacon_config])
    network.apply_timestep(0)
    network.apply_request(["node", "node_b", "application", "C2Beacon", "execute"])

    assert c2_beacon.c2_connection_active is True
    assert c2_server.c2_connection_active is True
    assert c2_server.c2_remote_connection == IPv4Address("192.168.255.2")


def test_c2_suite_ransomware_commands(basic_network):
    """Tests the Ransomware commands can be used to configure & launch ransomware via Requests."""
    # Setting up the network:
    network: Network = basic_network
    computer_a: Computer = network.get_node_by_hostname("node_a")
    c2_server: C2Server = computer_a.software_manager.software.get("C2Server")
    computer_a.software_manager.install(DatabaseService)
    computer_a.software_manager.software["DatabaseService"].start()

    computer_b: Computer = network.get_node_by_hostname("node_b")
    c2_beacon: C2Beacon = computer_b.software_manager.software.get("C2Beacon")
    computer_b.software_manager.install(DatabaseClient)
    computer_b.software_manager.software["DatabaseClient"].configure(server_ip_address=IPv4Address("192.168.0.2"))
    computer_b.software_manager.software["DatabaseClient"].run()

    c2_beacon.configure(c2_server_ip_address="192.168.0.2", keep_alive_frequency=2)
    c2_server.run()
    c2_beacon.establish()

    # Testing Via Requests:
    computer_b.software_manager.install(software_class=RansomwareScript)
    ransomware_config = {"server_ip_address": "192.168.0.2"}
    network.apply_request(["node", "node_a", "application", "C2Server", "ransomware_configure", ransomware_config])

    ransomware_script: RansomwareScript = computer_b.software_manager.software["RansomwareScript"]

    assert ransomware_script.server_ip_address == "192.168.0.2"

    network.apply_request(["node", "node_a", "application", "C2Server", "ransomware_launch"])

    database_file = computer_a.software_manager.file_system.get_file("database", "database.db")

    assert database_file.health_status == FileSystemItemHealthStatus.CORRUPT


def test_c2_suite_acl_block(basic_network):
    """Tests that C2 Beacon disconnects from the C2 Server after blocking ACL rules."""

    network: Network = basic_network
    computer_a: Computer = network.get_node_by_hostname("node_a")
    c2_server: C2Server = computer_a.software_manager.software.get("C2Server")

    computer_b: Computer = network.get_node_by_hostname("node_b")
    c2_beacon: C2Beacon = computer_b.software_manager.software.get("C2Beacon")

    router: Router = network.get_node_by_hostname("router")

    c2_beacon.configure(c2_server_ip_address="192.168.0.2", keep_alive_frequency=2)
    c2_server.run()
    c2_beacon.establish()

    c2_beacon.apply_timestep(0)
    assert c2_beacon.keep_alive_inactivity == 1

    # Keep Alive successfully sent and received upon the 2nd timestep.
    c2_beacon.apply_timestep(1)
    assert c2_beacon.keep_alive_inactivity == 0
    assert c2_beacon.c2_connection_active == True

    # Now we add a HTTP blocking acl (Thus preventing a keep alive)
    router.acl.add_rule(action=ACLAction.DENY, src_port=Port.HTTP, dst_port=Port.HTTP, position=0)

    c2_beacon.apply_timestep(2)
    c2_beacon.apply_timestep(3)
    assert c2_beacon.keep_alive_inactivity == 2
    assert c2_beacon.c2_connection_active == False
    assert c2_beacon.operating_state == ApplicationOperatingState.CLOSED


def test_c2_suite_terminal(basic_network):
    """Tests the Ransomware commands can be used to configure & launch ransomware via Requests."""
