from ipaddress import IPv4Address
from time import sleep

import pytest

from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.computer import Computer
from primaite.simulator.network.hardware.nodes.server import Server
from primaite.simulator.network.protocols.ntp import NTPPacket, NTPRequest
from primaite.simulator.system.services.ntp.ntp_client import NTPClient
from primaite.simulator.system.services.ntp.ntp_server import NTPServer
from primaite.simulator.system.services.service import ServiceOperatingState

# Create simple network for testing


def create_ntp_network() -> Network:
    """
    +------------+            +------------+
    |    ntp     |            |     ntp    |
    |  client_1  +------------+  server_1  |
    |            |            |            |
    +------------+            +------------+

    """

    network = Network()
    ntp_server = Server(
        hostname="ntp_server", ip_address="192.168.1.2", subnet_mask="255.255.255.0", default_gateway="192.168.1.1"
    )
    ntp_server.power_on()
    ntp_server.software_manager.install(NTPServer)

    ntp_client = Computer(
        hostname="ntp_client", ip_address="192.168.1.3", subnet_mask="255.255.255.0", default_gateway="192.168.1.1"
    )
    ntp_client.power_on()
    ntp_client.software_manager.install(NTPClient)
    network.connect(endpoint_b=ntp_server.ethernet_port[1], endpoint_a=ntp_client.ethernet_port[1])

    return network


# Define one node to be an NTP server and another node to be a NTP Client.


def test_ntp_client_server():
    network = create_ntp_network()
    server: Server = network.get_node_by_hostname("ntp_server")
    client: Computer = network.get_node_by_hostname("ntp_client")

    ntp_server: NTPServer = server.software_manager.software["NTPServer"]
    ntp_client: NTPClient = client.software_manager.software["NTPClient"]

    assert ntp_server.operating_state == ServiceOperatingState.RUNNING
    assert ntp_client.operating_state == ServiceOperatingState.RUNNING
    assert ntp_client.time is None

    ntp_request = NTPRequest(ntp_client="192.168.1.3")
    ntp_packet = NTPPacket(ntp_request=ntp_request)
    # ntp_client.send(payload=ntp_packet)
    ntp_client.request_time("192.168.1.3")

    assert ntp_server.receive(payload=ntp_packet) is True
    assert ntp_client.receive(payload=ntp_packet) is True
    assert ntp_client.time is not None
    first_time = ntp_client.time
    sleep(0.1)
    ntp_client.apply_timestep(1)  # Check time advances
    ntp_server.receive(payload=ntp_packet)
    ntp_client.receive(payload=ntp_packet)
    second_time = ntp_client.time
    assert first_time != second_time


# Test ntp client behaviour when ntp server is unavailable.
@pytest.mark.skip(reason="NTP needs to know if underlying node is RUNNING")
def test_ntp_server_failure():
    network = create_ntp_network()
    server: Server = network.get_node_by_hostname("ntp_server")
    client: Computer = network.get_node_by_hostname("ntp_client")

    ntp_server: NTPServer = server.software_manager.software["NTPServer"]
    ntp_client: NTPClient = client.software_manager.software["NTPClient"]

    assert ntp_client.operating_state == ServiceOperatingState.RUNNING

    # Turn off ntp server.
    ntp_server.stop()
    assert ntp_server.operating_state == ServiceOperatingState.STOPPED
    # And request a time update.
    ntp_request = NTPRequest(ntp_client="192.168.1.3")
    ntp_packet = NTPPacket(ntp_request=ntp_request)
    ntp_client.send(payload=ntp_packet)
    assert ntp_server.receive(payload=ntp_packet) is False
    assert ntp_client.receive(payload=ntp_packet) is False

    # Restart ntp server.
    ntp_server.start()
    assert ntp_server.operating_state == ServiceOperatingState.RUNNING
