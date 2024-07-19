# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server


def test_local_accounts_ping_temp():
    network = Network()

    # Create Computer
    computer = Computer(
        hostname="computer",
        ip_address="192.168.1.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    computer.power_on()

    # Create Server
    server = Server(
        hostname="server",
        ip_address="192.168.1.3",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    server.power_on()

    # Connect Computer and Server
    network.connect(computer.network_interface[1], server.network_interface[1])

    assert not computer.ping(server.network_interface[1].ip_address)

    computer.user_session_manager.login(username="admin", password="admin")

    assert computer.ping(server.network_interface[1].ip_address)
