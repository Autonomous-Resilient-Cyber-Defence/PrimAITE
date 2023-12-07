from ipaddress import IPv4Address
from time import sleep
from typing import Tuple

import pytest

from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.computer import Computer
from primaite.simulator.network.hardware.nodes.server import Server
from primaite.simulator.network.protocols.ntp import NTPPacket, NTPRequest
from primaite.simulator.system.services.ntp.ntp_client import NTPClient
from primaite.simulator.system.services.ntp.ntp_server import NTPServer
from primaite.simulator.system.services.service import ServiceOperatingState

# Create simple network for testing


@pytest.fixture(scope="function")
def create_ntp_network(client_server) -> Tuple[NTPClient, Computer, NTPServer, Server]:
    """
    +------------+            +------------+
    |    ntp     |            |     ntp    |
    |  client_1  +------------+  server_1  |
    |            |            |            |
    +------------+            +------------+

    """
    client, server = client_server

    server.power_on()
    server.software_manager.install(NTPServer)
    ntp_server: NTPServer = server.software_manager.software.get("NTPServer")
    ntp_server.start()

    client.power_on()
    client.software_manager.install(NTPClient)
    ntp_client: NTPClient = client.software_manager.software.get("NTPClient")
    ntp_client.start()

    return ntp_client, client, ntp_server, server


# Define one node to be an NTP server and another node to be a NTP Client.


def test_ntp_client_server(create_ntp_network):
    ntp_client, client, ntp_server, server = create_ntp_network

    ntp_server: NTPServer = server.software_manager.software["NTPServer"]
    ntp_client: NTPClient = client.software_manager.software["NTPClient"]

    assert ntp_server.operating_state == ServiceOperatingState.RUNNING
    assert ntp_client.operating_state == ServiceOperatingState.RUNNING
    ntp_client.configure(
        ntp_server_ip_address=IPv4Address("192.168.0.2"), ntp_client_ip_address=IPv4Address("192.168.0.1")
    )

    assert ntp_client.time is None
    ntp_client.request_time()
    assert ntp_client.time is not None
    first_time = ntp_client.time
    sleep(0.1)
    ntp_client.apply_timestep(1)  # Check time advances
    second_time = ntp_client.time
    assert first_time != second_time


# Test ntp client behaviour when ntp server is unavailable.
def test_ntp_server_failure(create_ntp_network):
    ntp_client, client, ntp_server, server = create_ntp_network

    ntp_server: NTPServer = server.software_manager.software["NTPServer"]
    ntp_client: NTPClient = client.software_manager.software["NTPClient"]

    assert ntp_client.operating_state == ServiceOperatingState.RUNNING
    assert ntp_client.operating_state == ServiceOperatingState.RUNNING
    ntp_client.configure(
        ntp_server_ip_address=IPv4Address("192.168.0.2"), ntp_client_ip_address=IPv4Address("192.168.0.1")
    )

    # Turn off ntp server.
    ntp_server.stop()
    assert ntp_server.operating_state == ServiceOperatingState.STOPPED
    # And request a time update.
    ntp_client.request_time()
    assert ntp_client.time is None

    # Restart ntp server.
    ntp_server.start()
    assert ntp_server.operating_state == ServiceOperatingState.RUNNING
    ntp_client.request_time()
    assert ntp_client.time is not None
