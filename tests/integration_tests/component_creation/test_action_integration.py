# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from primaite.simulator.core import RequestType
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.hardware.nodes.network.switch import Switch
from primaite.simulator.sim_container import Simulation
from primaite.simulator.system.services.database.database_service import DatabaseService


def test_passing_actions_down(monkeypatch) -> None:
    """Check that an action is passed down correctly to the child component."""

    sim = Simulation()

    pc1 = Computer(hostname="PC-1", ip_address="10.10.1.1", subnet_mask="255.255.255.0")
    pc1.start_up_duration = 0
    pc1.power_on()
    pc2 = Computer(hostname="PC-2", ip_address="10.10.1.2", subnet_mask="255.255.255.0")
    srv = Server(hostname="WEBSERVER", ip_address="10.10.1.100", subnet_mask="255.255.255.0")
    s1 = Switch(hostname="switch1")

    for n in [pc1, pc2, srv, s1]:
        sim.network.add_node(n)

    database_service = DatabaseService(file_system=srv.file_system)
    srv.install_service(database_service)

    downloads_folder = pc1.file_system.create_folder("downloads")
    pc1.file_system.create_file("bermuda_triangle.png", folder_name="downloads")

    sim.network.connect(pc1.network_interface[1], s1.network_interface[1])
    sim.network.connect(pc2.network_interface[1], s1.network_interface[2])
    sim.network.connect(s1.network_interface[3], srv.network_interface[1])

    # call this method to make sure no errors occur.
    sim._request_manager.get_request_types_recursively()

    # patch the action to do something which we can check the result of.
    action_invoked = False

    def succeed():
        nonlocal action_invoked
        action_invoked = True

    monkeypatch.setitem(
        downloads_folder._request_manager.request_types, "repair", RequestType(func=lambda request, context: succeed())
    )

    assert not action_invoked

    # call the patched method
    sim.apply_request(["network", "node", pc1.hostname, "file_system", "folder", "downloads", "repair"])

    assert action_invoked
