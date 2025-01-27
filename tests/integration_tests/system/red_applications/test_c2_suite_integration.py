# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from ipaddress import IPv4Address
from typing import Tuple

import pytest
import yaml

from primaite.game.agent.interface import ProxyAgent
from primaite.game.game import PrimaiteGame
from primaite.simulator.file_system.file_system_item_abc import FileSystemItemHealthStatus
from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.hardware.nodes.network.router import AccessControlList, ACLAction, Router
from primaite.simulator.network.hardware.nodes.network.switch import Switch
from primaite.simulator.system.applications.application import ApplicationOperatingState
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.applications.red_applications.c2.c2_beacon import C2Beacon
from primaite.simulator.system.applications.red_applications.c2.c2_server import C2Command, C2Server
from primaite.simulator.system.applications.red_applications.ransomware_script import RansomwareScript
from primaite.simulator.system.services.database.database_service import DatabaseService
from primaite.simulator.system.services.dns.dns_server import DNSServer
from primaite.simulator.system.services.ftp.ftp_client import FTPClient
from primaite.simulator.system.services.ftp.ftp_server import FTPServer
from primaite.simulator.system.services.web_server.web_server import WebServer
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.port import PORT_LOOKUP
from tests import TEST_ASSETS_ROOT


@pytest.fixture(scope="function")
def basic_network() -> Network:
    network = Network()

    # Creating two generic nodes for the C2 Server and the C2 Beacon.

    node_a_cfg = {
        "type": "computer",
        "hostname": "node_a",
        "ip_address": "192.168.0.2",
        "subnet_mask": "255.255.255.252",
        "default_gateway": "192.168.0.1",
        "start_up_duration": 0,
    }

    node_a: Computer = Computer.from_config(config=node_a_cfg)
    node_a.power_on()
    node_a.software_manager.get_open_ports()
    node_a.software_manager.install(software_class=C2Server)

    node_b_cfg = {
        "type": "computer",
        "hostname": "node_b",
        "ip_address": "192.168.255.2",
        "subnet_mask": "255.255.255.248",
        "default_gateway": "192.168.255.1",
        "start_up_duration": 0,
    }

    node_b: Computer = Computer.from_config(config=node_b_cfg)
    node_b.power_on()
    node_b.software_manager.install(software_class=C2Beacon)

    # Creating a generic computer for testing remote terminal connections.
    node_c_cfg = {
        "type": "computer",
        "hostname": "node_c",
        "ip_address": "192.168.255.3",
        "subnet_mask": "255.255.255.248",
        "default_gateway": "192.168.255.1",
        "start_up_duration": 0,
    }

    node_c: Computer = Computer.from_config(config=node_c_cfg)
    node_c.power_on()

    # Creating a router to sit between node 1 and node 2.
    router = Router.from_config(config={"type": "router", "hostname": "router", "num_ports": 3, "start_up_duration": 0})
    # Default allow all.
    router.acl.add_rule(action=ACLAction.PERMIT)
    router.power_on()
    # Creating switches for each client.
    switch_1 = Switch.from_config(
        config={"type": "switch", "hostname": "switch_1", "num_ports": 6, "start_up_duration": 0}
    )
    switch_1.power_on()

    # Connecting the switches to the router.
    router.configure_port(port=1, ip_address="192.168.0.1", subnet_mask="255.255.255.252")
    network.connect(endpoint_a=router.network_interface[1], endpoint_b=switch_1.network_interface[6])

    switch_2 = Switch.from_config(
        config={"type": "switch", "hostname": "switch_2", "num_ports": 6, "start_up_duration": 0}
    )
    switch_2.power_on()

    network.connect(endpoint_a=router.network_interface[2], endpoint_b=switch_2.network_interface[6])
    router.configure_port(port=2, ip_address="192.168.255.1", subnet_mask="255.255.255.248")

    router.enable_port(1)
    router.enable_port(2)

    # Connecting the node to each switch
    network.connect(node_a.network_interface[1], switch_1.network_interface[1])
    network.connect(node_b.network_interface[1], switch_2.network_interface[1])
    network.connect(node_c.network_interface[1], switch_2.network_interface[2])

    return network


def setup_c2(given_network: Network):
    """Installs the C2 Beacon & Server, configures and then returns."""
    computer_a: Computer = given_network.get_node_by_hostname("node_a")
    c2_server: C2Server = computer_a.software_manager.software.get("C2Server")
    computer_a.software_manager.install(DatabaseService)
    computer_a.software_manager.software["DatabaseService"].start()

    computer_b: Computer = given_network.get_node_by_hostname("node_b")
    c2_beacon: C2Beacon = computer_b.software_manager.software.get("C2Beacon")
    computer_b.software_manager.install(DatabaseClient)
    computer_b.software_manager.software["DatabaseClient"].configure(server_ip_address=IPv4Address("192.168.0.2"))
    computer_b.software_manager.software["DatabaseClient"].run()

    c2_beacon.configure(c2_server_ip_address="192.168.0.2", keep_alive_frequency=2)
    c2_server.run()
    c2_beacon.establish()

    return given_network, computer_a, c2_server, computer_b, c2_beacon


def test_c2_suite_setup_receive(basic_network):
    """Test that C2 Beacon can successfully establish connection with the C2 Server."""
    network: Network = basic_network
    network, computer_a, c2_server, computer_b, c2_beacon = setup_c2(network)
    # Asserting that the c2 beacon has established a c2 connection
    assert c2_beacon.c2_connection_active is True

    # Asserting that the c2 server has established a c2 connection.
    assert c2_server.c2_connection_active is True
    assert c2_server.c2_remote_connection == IPv4Address("192.168.255.2")

    for i in range(50):
        network.apply_timestep(i)

    assert c2_beacon.c2_connection_active is True
    assert c2_server.c2_connection_active is True


def test_c2_suite_keep_alive_inactivity(basic_network):
    """Tests that C2 Beacon disconnects from the C2 Server after inactivity."""
    network: Network = basic_network
    network, computer_a, c2_server, computer_b, c2_beacon = setup_c2(network)

    c2_beacon.apply_timestep(0)
    assert c2_beacon.keep_alive_inactivity == 1

    # Keep Alive successfully sent and received upon the 2nd timestep.
    c2_beacon.apply_timestep(1)
    assert c2_beacon.keep_alive_inactivity == 0
    assert c2_beacon.c2_connection_active == True

    # Now we turn off the c2 server (Thus preventing a keep alive)
    c2_server.close()
    c2_beacon.apply_timestep(2)

    assert c2_beacon.keep_alive_inactivity == 1

    c2_beacon.apply_timestep(3)

    # C2 Beacon resets it's connections back to default.
    assert c2_beacon.keep_alive_inactivity == 0
    assert c2_beacon.c2_connection_active == False
    assert c2_beacon.operating_state == ApplicationOperatingState.CLOSED


def test_c2_suite_configure_request(basic_network):
    """Tests that the request system can be used to successfully setup a c2 suite."""
    network: Network = basic_network
    network, computer_a, c2_server, computer_b, c2_beacon = setup_c2(network)

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
    network, computer_a, c2_server, computer_b, c2_beacon = setup_c2(network)

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
    network, computer_a, c2_server, computer_b, c2_beacon = setup_c2(network)
    computer_b.software_manager.install(software_class=RansomwareScript)
    ransomware_config = {"server_ip_address": "192.168.0.2"}

    router: Router = network.get_node_by_hostname("router")

    c2_beacon.apply_timestep(0)
    assert c2_beacon.keep_alive_inactivity == 1

    # Keep Alive successfully sent and received upon the 2nd timestep.
    c2_beacon.apply_timestep(1)
    assert c2_beacon.keep_alive_inactivity == 0
    assert c2_beacon.c2_connection_active == True

    # Now we add a HTTP blocking acl (Thus preventing a keep alive)
    router.acl.add_rule(action=ACLAction.DENY, src_port=PORT_LOOKUP["HTTP"], dst_port=PORT_LOOKUP["HTTP"], position=0)

    c2_beacon.apply_timestep(2)
    c2_beacon.apply_timestep(3)

    # C2 Beacon resets after unable to maintain contact.

    assert c2_beacon.keep_alive_inactivity == 0
    assert c2_beacon.c2_connection_active == False
    assert c2_beacon.operating_state == ApplicationOperatingState.CLOSED


def test_c2_suite_terminal_command_file_creation(basic_network):
    """Tests the C2 Terminal command can be used on local and remote."""
    network: Network = basic_network
    network, computer_a, c2_server, computer_b, c2_beacon = setup_c2(network)
    computer_c: Computer = network.get_node_by_hostname("node_c")

    # Asserting to demonstrate that the test files don't exist:
    assert (
        computer_c.software_manager.file_system.access_file(folder_name="test_folder", file_name="test_file") == False
    )

    assert (
        computer_b.software_manager.file_system.access_file(folder_name="test_folder", file_name="test_file") == False
    )

    # Testing that we can create the test file and folders via the terminal command (Local C2 Terminal).

    # Local file/folder creation commands.
    folder_create_command = {
        "commands": ["file_system", "create", "folder", "test_folder"],
        "username": "admin",
        "password": "admin",
        "ip_address": None,
    }
    c2_server.send_command(C2Command.TERMINAL, command_options=folder_create_command)

    file_create_command = {
        "commands": ["file_system", "create", "file", "test_folder", "test_file", "True"],
        "username": "admin",
        "password": "admin",
        "ip_address": None,
    }
    c2_server.send_command(C2Command.TERMINAL, command_options=file_create_command)

    assert computer_b.software_manager.file_system.access_file(folder_name="test_folder", file_name="test_file") == True
    assert c2_beacon.terminal_session is not None

    # Testing that we can create the same test file/folders via on node 3 via a remote terminal.
    file_remote_create_command = {
        "commands": [
            ["file_system", "create", "folder", "test_folder"],
            ["file_system", "create", "file", "test_folder", "test_file", "True"],
        ],
        "username": "admin",
        "password": "admin",
        "ip_address": "192.168.255.3",
    }

    c2_server.send_command(C2Command.TERMINAL, command_options=file_remote_create_command)

    assert computer_c.software_manager.file_system.access_file(folder_name="test_folder", file_name="test_file") == True
    assert c2_beacon.terminal_session is not None


def test_c2_suite_acl_bypass(basic_network):
    """Tests that C2 Beacon can be reconfigured to connect C2 Server to bypass blocking ACL rules.

    1. This Test first configures a router to block HTTP traffic and asserts the following:
        1. C2 Beacon and C2 Server are unable to maintain connection
        2. Traffic is confirmed to be blocked by the ACL rule.

    2. Next the C2 Beacon is re-configured to use FTP which is permitted by the ACL and asserts the following;
        1. The C2 Beacon and C2 Server re-establish connection
        2. The ACL rule has not prevent any further traffic.
        3. A test file create command is sent & it's output confirmed

    3. The ACL is then re-configured to block FTP traffic and asserts the following:
        1. C2 Beacon and C2 Server are unable to maintain connection
        2. Traffic is confirmed to be blocked by the ACL rule.

    4. Next the C2 Beacon is re-configured to use HTTP which is permitted by the ACL and asserts the following;
        1. The C2 Beacon and C2 Server re-establish connection
        2. The ACL rule has not prevent any further traffic.
        3. A test file create command is sent & it's output confirmed
    """

    network: Network = basic_network
    network, computer_a, c2_server, computer_b, c2_beacon = setup_c2(network)
    router: Router = network.get_node_by_hostname("router")

    ################ Confirm Default Setup #########################

    # Permitting all HTTP & FTP traffic
    router.acl.add_rule(action=ACLAction.PERMIT, src_port=PORT_LOOKUP["HTTP"], dst_port=PORT_LOOKUP["HTTP"], position=0)
    router.acl.add_rule(action=ACLAction.PERMIT, src_port=PORT_LOOKUP["FTP"], dst_port=PORT_LOOKUP["FTP"], position=1)

    c2_beacon.apply_timestep(0)
    assert c2_beacon.keep_alive_inactivity == 1

    # Keep Alive successfully sent and received upon the 2nd timestep.
    c2_beacon.apply_timestep(1)

    assert c2_beacon.keep_alive_inactivity == 0
    assert c2_beacon.c2_connection_active == True

    ################ Denying HTTP Traffic #########################

    # Now we add a HTTP blocking acl (Thus preventing a keep alive)
    router.acl.add_rule(action=ACLAction.DENY, src_port=PORT_LOOKUP["HTTP"], dst_port=PORT_LOOKUP["HTTP"], position=0)
    blocking_acl: AccessControlList = router.acl.acl[0]

    # Asserts to show the C2 Suite is unable to maintain connection:

    network.apply_timestep(2)
    network.apply_timestep(3)

    c2_packets_blocked = blocking_acl.match_count
    assert c2_packets_blocked != 0
    assert c2_beacon.c2_connection_active is False

    # Stepping one more time to confirm that the C2 server drops its connection
    network.apply_timestep(4)
    assert c2_server.c2_connection_active is False

    ################ Configuring C2 to use FTP #####################

    # Reconfiguring the c2 beacon to now use FTP
    c2_beacon.configure(
        c2_server_ip_address="192.168.0.2",
        keep_alive_frequency=2,
        masquerade_port=PORT_LOOKUP["FTP"],
        masquerade_protocol=PROTOCOL_LOOKUP["TCP"],
    )

    c2_beacon.establish()

    ################ Confirming connection via FTP #####################

    # Confirming we've re-established connection

    assert c2_beacon.c2_connection_active is True
    assert c2_server.c2_connection_active is True

    # Confirming that we can send commands:

    ftp_file_create_command = {
        "commands": [
            ["file_system", "create", "folder", "test_folder"],
            ["file_system", "create", "file", "test_folder", "ftp_test_file", "True"],
        ],
        "username": "admin",
        "password": "admin",
        "ip_address": None,
    }
    c2_server.send_command(C2Command.TERMINAL, command_options=ftp_file_create_command)
    assert (
        computer_b.software_manager.file_system.access_file(folder_name="test_folder", file_name="ftp_test_file")
        == True
    )

    # Confirming we can maintain connection

    # Stepping twenty timesteps in the network
    i = 4  # We're already at the 4th timestep (starting at timestep 4)

    for i in range(20):
        network.apply_timestep(i)

    # Confirming HTTP ACL ineffectiveness (C2 Bypass)

    # Asserting that the ACL hasn't caught more traffic and the c2 connection is still active
    assert c2_packets_blocked == blocking_acl.match_count
    assert c2_server.c2_connection_active is True
    assert c2_beacon.c2_connection_active is True

    ################ Denying FTP Traffic & Enable HTTP #########################

    # Blocking FTP and re-permitting HTTP:
    router.acl.add_rule(action=ACLAction.PERMIT, src_port=PORT_LOOKUP["HTTP"], dst_port=PORT_LOOKUP["HTTP"], position=0)
    router.acl.add_rule(action=ACLAction.DENY, src_port=PORT_LOOKUP["FTP"], dst_port=PORT_LOOKUP["FTP"], position=1)
    blocking_acl: AccessControlList = router.acl.acl[1]

    # Asserts to show the C2 Suite is unable to maintain connection:

    network.apply_timestep(25)
    network.apply_timestep(26)

    c2_packets_blocked = blocking_acl.match_count
    assert c2_packets_blocked != 0
    assert c2_beacon.c2_connection_active is False

    # Stepping one more time to confirm that the C2 server drops its connection
    network.apply_timestep(27)
    assert c2_server.c2_connection_active is False

    ################ Configuring C2 to use HTTP #####################

    # Reconfiguring the c2 beacon to now use HTTP Again
    c2_beacon.configure(
        c2_server_ip_address="192.168.0.2",
        keep_alive_frequency=2,
        masquerade_port=PORT_LOOKUP["HTTP"],
        masquerade_protocol=PROTOCOL_LOOKUP["TCP"],
    )

    c2_beacon.establish()

    ################ Confirming connection via HTTP #####################

    # Confirming we've re-established connection

    assert c2_beacon.c2_connection_active is True
    assert c2_server.c2_connection_active is True

    # Confirming that we can send commands

    http_folder_create_command = {
        "commands": ["file_system", "create", "folder", "test_folder"],
        "username": "admin",
        "password": "admin",
        "ip_address": None,
    }
    c2_server.send_command(C2Command.TERMINAL, command_options=http_folder_create_command)
    http_file_create_command = {
        "commands": ["file_system", "create", "file", "test_folder", "http_test_file", "true"],
        "username": "admin",
        "password": "admin",
        "ip_address": None,
    }
    c2_server.send_command(C2Command.TERMINAL, command_options=http_file_create_command)
    assert (
        computer_b.software_manager.file_system.access_file(folder_name="test_folder", file_name="http_test_file")
        == True
    )

    assert c2_beacon.c2_connection_active is True
    assert c2_server.c2_connection_active is True

    # Confirming we can maintain connection

    # Stepping twenty timesteps in the network
    i = 28  # We're already at the 28th timestep

    for i in range(20):
        network.apply_timestep(i)

    # Confirming FTP ACL ineffectiveness (C2 Bypass)

    # Asserting that the ACL hasn't caught more traffic and the c2 connection is still active
    assert c2_packets_blocked == blocking_acl.match_count
    assert c2_server.c2_connection_active is True
    assert c2_beacon.c2_connection_active is True


def test_c2_suite_yaml():
    """Tests that the C2 Suite is can be configured correctly via the Yaml."""
    with open(TEST_ASSETS_ROOT / "configs" / "basic_c2_setup.yaml") as f:
        cfg = yaml.safe_load(f)
    game = PrimaiteGame.from_config(cfg)

    yaml_network = game.simulation.network
    computer_a: Computer = yaml_network.get_node_by_hostname("node_a")
    c2_server: C2Server = computer_a.software_manager.software.get("C2Server")

    computer_b: Computer = yaml_network.get_node_by_hostname("node_b")
    c2_beacon: C2Beacon = computer_b.software_manager.software.get("C2Beacon")
    c2_beacon.configure(
        c2_server_ip_address=c2_beacon.config.c2_server_ip_address,
        keep_alive_frequency=c2_beacon.config.keep_alive_frequency,
        masquerade_port=c2_beacon.config.masquerade_port,
        masquerade_protocol=c2_beacon.config.masquerade_protocol,
    )

    assert c2_server.operating_state == ApplicationOperatingState.RUNNING

    assert c2_beacon.c2_remote_connection == IPv4Address("192.168.10.21")

    c2_beacon.establish()

    # Asserting that the c2 beacon has established a c2 connection
    assert c2_beacon.c2_connection_active is True
    # Asserting that the c2 server has established a c2 connection.
    assert c2_server.c2_connection_active is True
    assert c2_server.c2_remote_connection == IPv4Address("192.168.10.22")

    for i in range(50):
        yaml_network.apply_timestep(i)

    assert c2_beacon.c2_connection_active is True
    assert c2_server.c2_connection_active is True


def test_c2_suite_file_extraction(basic_network):
    """Test that C2 Beacon can successfully exfiltrate a target file."""
    network: Network = basic_network
    network, computer_a, c2_server, computer_b, c2_beacon = setup_c2(network)
    # Asserting that the c2 beacon has established a c2 connection
    assert c2_beacon.c2_connection_active is True

    # Asserting that the c2 server has established a c2 connection.
    assert c2_server.c2_connection_active is True
    assert c2_server.c2_remote_connection == IPv4Address("192.168.255.2")

    # Creating the target file on computer_c
    computer_c: Computer = network.get_node_by_hostname("node_c")
    computer_c.file_system.create_folder("important_files")
    computer_c.file_system.create_file(file_name="secret.txt", folder_name="important_files")
    assert computer_c.file_system.access_file(folder_name="important_files", file_name="secret.txt")

    # Installing an FTP Server on the same node as C2 Beacon via the terminal:

    # Attempting to exfiltrate secret.txt from computer c to the C2 Server
    c2_server.send_command(
        given_command=C2Command.DATA_EXFILTRATION,
        command_options={
            "username": "admin",
            "password": "admin",
            "target_ip_address": "192.168.255.3",
            "target_folder_name": "important_files",
            "exfiltration_folder_name": "yoinked_files",
            "target_file_name": "secret.txt",
        },
    )

    # Asserting that C2 Beacon has managed to get the file
    assert c2_beacon._host_file_system.access_file(folder_name="yoinked_files", file_name="secret.txt")

    # Asserting that the C2 Beacon can relay it back to the C2 Server
    assert c2_server._host_file_system.access_file(folder_name="yoinked_files", file_name="secret.txt")
