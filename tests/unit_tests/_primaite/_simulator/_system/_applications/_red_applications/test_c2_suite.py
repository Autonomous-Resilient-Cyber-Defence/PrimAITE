# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
import pytest

from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.system.applications.application import ApplicationOperatingState
from primaite.simulator.system.applications.red_applications.c2.c2_beacon import C2Beacon
from primaite.simulator.system.applications.red_applications.c2.c2_server import C2Command, C2Server
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.port import PORT_LOOKUP


@pytest.fixture(scope="function")
def basic_c2_network() -> Network:
    network = Network()

    # Creating two generic nodes for the C2 Server and the C2 Beacon.

    computer_a = Computer(
        hostname="computer_a",
        ip_address="192.168.0.1",
        subnet_mask="255.255.255.252",
        start_up_duration=0,
    )
    computer_a.power_on()
    computer_a.software_manager.install(software_class=C2Server)

    computer_b = Computer(
        hostname="computer_b", ip_address="192.168.0.2", subnet_mask="255.255.255.252", start_up_duration=0
    )

    computer_b.power_on()
    computer_b.software_manager.install(software_class=C2Beacon)

    network.connect(endpoint_a=computer_a.network_interface[1], endpoint_b=computer_b.network_interface[1])
    return network


def setup_c2(given_network: Network):
    """Installs the C2 Beacon & Server, configures and then returns."""
    network: Network = given_network

    computer_a: Computer = network.get_node_by_hostname("computer_a")
    computer_b: Computer = network.get_node_by_hostname("computer_b")

    c2_beacon: C2Beacon = computer_b.software_manager.software.get("C2Beacon")
    c2_server: C2Server = computer_a.software_manager.software.get("C2Server")

    c2_beacon.configure(c2_server_ip_address="192.168.0.1", keep_alive_frequency=2)
    c2_server.run()
    c2_beacon.establish()

    return network, computer_a, c2_server, computer_b, c2_beacon


def test_c2_handle_server_disconnect(basic_c2_network):
    """Tests that the C2 suite will be able handle the c2 server application closing."""
    network: Network = basic_c2_network
    network, computer_a, c2_server, computer_b, c2_beacon = setup_c2(network)

    assert c2_beacon.c2_connection_active is True

    ##### C2 Server disconnecting.

    # Closing the C2 Server
    c2_server.close()

    # Applying 10 timesteps to trigger C2 beacon keep alive

    for i in range(10):
        network.apply_timestep(i)

    assert c2_beacon.c2_connection_active is False
    assert c2_beacon.operating_state is ApplicationOperatingState.CLOSED

    # C2 Beacon disconnected.

    network: Network = basic_c2_network

    network, computer_a, c2_server, computer_b, c2_beacon = setup_c2(network)


def test_c2_handle_beacon_disconnect(basic_c2_network):
    """Tests that the C2 suite will be able handle the c2 beacon application closing."""
    network: Network = basic_c2_network
    network, computer_a, c2_server, computer_b, c2_beacon = setup_c2(network)

    assert c2_server.c2_connection_active is True

    # Closing the C2 beacon

    c2_beacon.close()

    assert c2_beacon.operating_state is ApplicationOperatingState.CLOSED

    # Attempting a simple C2 Server command:
    file_create_command = {
        "commands": [["file_system", "create", "folder", "test_folder"]],
        "username": "admin",
        "password": "admin",
        "ip_address": None,
    }

    command_request_response = c2_server.send_command(C2Command.TERMINAL, command_options=file_create_command)

    assert command_request_response.status == "failure"

    # Despite the command failing - The C2 Server will still consider the beacon alive
    # Until it does not respond within the keep alive frequency set in the last keep_alive.
    assert c2_server.c2_connection_active is True

    # Stepping 6 timesteps in order for the C2 server to consider the beacon dead.
    for i in range(6):
        network.apply_timestep(i)

    assert c2_server.c2_connection_active is False


def test_c2_handle_switching_port(basic_c2_network):
    """Tests that the C2 suite will be able handle switching destination/src port."""
    network: Network = basic_c2_network

    network, computer_a, c2_server, computer_b, c2_beacon = setup_c2(network)

    # Asserting that the c2 applications have established a c2 connection
    assert c2_beacon.c2_connection_active is True
    assert c2_server.c2_connection_active is True

    # Assert to confirm that both the C2 server and the C2 beacon are configured correctly.
    assert c2_beacon.c2_config.keep_alive_frequency is 2
    assert c2_beacon.c2_config.masquerade_port is PORT_LOOKUP["HTTP"]
    assert c2_beacon.c2_config.masquerade_protocol is PROTOCOL_LOOKUP["TCP"]

    assert c2_server.c2_config.keep_alive_frequency is 2
    assert c2_server.c2_config.masquerade_port is PORT_LOOKUP["HTTP"]
    assert c2_server.c2_config.masquerade_protocol is PROTOCOL_LOOKUP["TCP"]

    # Configuring the C2 Beacon.
    c2_beacon.configure(
        c2_server_ip_address="192.168.0.1",
        keep_alive_frequency=2,
        masquerade_port=PORT_LOOKUP["FTP"],
        masquerade_protocol=PROTOCOL_LOOKUP["TCP"],
    )

    # Asserting that the c2 applications have established a c2 connection
    assert c2_beacon.c2_connection_active is True
    assert c2_server.c2_connection_active is True

    # Assert to confirm that both the C2 server and the C2 beacon
    # Have reconfigured their C2 settings.
    assert c2_beacon.c2_config.masquerade_port is PORT_LOOKUP["FTP"]
    assert c2_beacon.c2_config.masquerade_protocol is PROTOCOL_LOOKUP["TCP"]

    assert c2_server.c2_config.masquerade_port is PORT_LOOKUP["FTP"]
    assert c2_server.c2_config.masquerade_protocol is PROTOCOL_LOOKUP["TCP"]


def test_c2_handle_switching_frequency(basic_c2_network):
    """Tests that the C2 suite will be able handle switching keep alive frequency."""
    network: Network = basic_c2_network

    network, computer_a, c2_server, computer_b, c2_beacon = setup_c2(network)

    # Asserting that the c2 beacon has established a c2 connection
    assert c2_beacon.c2_connection_active is True
    network: Network = basic_c2_network

    network, computer_a, c2_server, computer_b, c2_beacon = setup_c2(network)

    # Asserting that the c2 applications have established a c2 connection
    assert c2_beacon.c2_connection_active is True
    assert c2_server.c2_connection_active is True

    # Assert to confirm that both the C2 server and the C2 beacon are configured correctly.
    assert c2_beacon.c2_config.keep_alive_frequency is 2
    assert c2_server.c2_config.keep_alive_frequency is 2

    # Configuring the C2 Beacon.
    c2_beacon.configure(c2_server_ip_address="192.168.0.1", keep_alive_frequency=10)

    # Asserting that the c2 applications have established a c2 connection
    assert c2_beacon.c2_connection_active is True
    assert c2_server.c2_connection_active is True

    # Assert to confirm that both the C2 server and the C2 beacon
    # Have reconfigured their C2 settings.
    assert c2_beacon.c2_config.keep_alive_frequency is 10
    assert c2_server.c2_config.keep_alive_frequency is 10

    # Now skipping 9 time steps to confirm keep alive inactivity
    for i in range(9):
        network.apply_timestep(i)

    # If the keep alive reconfiguration failed then the keep alive inactivity could never reach 9
    # As another keep alive would have already been sent.
    assert c2_beacon.keep_alive_inactivity is 9
    assert c2_server.keep_alive_inactivity is 9

    network.apply_timestep(10)

    assert c2_beacon.keep_alive_inactivity is 0
    assert c2_server.keep_alive_inactivity is 0


def test_c2_handles_1_timestep_keep_alive(basic_c2_network):
    """Tests that the C2 suite will be able handle a C2 Beacon will a keep alive of 1 timestep."""
    network: Network = basic_c2_network

    network, computer_a, c2_server, computer_b, c2_beacon = setup_c2(network)

    c2_beacon.configure(c2_server_ip_address="192.168.0.1", keep_alive_frequency=1)
    c2_server.run()
    c2_beacon.establish()

    for i in range(50):
        network.apply_timestep(i)

    assert c2_beacon.c2_connection_active is True
    assert c2_server.c2_connection_active is True


def test_c2_exfil_folder(basic_c2_network):
    """Tests that the C2 suite correctly default and setup their exfiltration_folders."""
    network: Network = basic_c2_network

    network, computer_a, c2_server, computer_b, c2_beacon = setup_c2(network)

    c2_beacon.get_exfiltration_folder()
    c2_server.get_exfiltration_folder()
    assert c2_beacon.file_system.get_folder("exfiltration_folder")
    assert c2_server.file_system.get_folder("exfiltration_folder")

    c2_server.file_system.create_file(folder_name="test_folder", file_name="test_file")

    # asserting to check that by default the c2 exfil will use "exfiltration_folder"
    exfil_options = {
        "username": "admin",
        "password": "admin",
        "target_ip_address": "192.168.0.1",
        "target_folder_name": "test_folder",
        "exfiltration_folder_name": None,
        "target_file_name": "test_file",
    }
    c2_server.send_command(given_command=C2Command.DATA_EXFILTRATION, command_options=exfil_options)

    assert c2_beacon.file_system.get_file(folder_name="exfiltration_folder", file_name="test_file")
