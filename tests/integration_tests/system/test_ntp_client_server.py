from primaite.simulator.network.hardware.nodes.computer import Computer
from primaite.simulator.network.hardware.nodes.server import Server
from primaite.simulator.network.protocols.ntp import NTPPacket
from primaite.simulator.system.services.ntp.ntp_client import NTPClient
from primaite.simulator.system.services.ntp.ntp_server import NTPServer
from primaite.simulator.system.services.service import ServiceOperatingState

# Define one node to be an NTP server and another node to be a NTP Client.


def test_ntp_client_server(network):
    server: Server = network.get_node_by_hostname("ntp_server")
    client: Computer = network.get_node_by_hostname("ntp_client")

    ntp_server: NTPServer = server.software_manager.software["NTP_Server"]
    ntp_client: NTPClient = client.software_manager.software["NTP_Client"]

    assert ntp_server.operating_state == ServiceOperatingState.RUNNING
    assert ntp_client.operating_state == ServiceOperatingState.RUNNING

    ntp_client.send(payload=NTPPacket())
    assert ntp_server.receive() is True
    assert ntp_client.receive() is True

    assert ntp_client.apply_timestep(1) is True
