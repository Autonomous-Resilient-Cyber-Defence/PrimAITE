import pytest

from primaite.simulator.core import Action
from primaite.simulator.network.hardware.nodes.computer import Computer
from primaite.simulator.network.hardware.nodes.server import Server
from primaite.simulator.network.hardware.nodes.switch import Switch
from primaite.simulator.sim_container import Simulation
from primaite.simulator.system.services.database_service import DatabaseService


def test_passing_actions_down(monkeypatch) -> None:
    """Check that an action is passed down correctly to the child component."""

    sim = Simulation()

    pc1 = Computer(hostname="PC-1", ip_address="10.10.1.1", subnet_mask="255.255.255.0")
    pc2 = Computer(hostname="PC-2", ip_address="10.10.1.2", subnet_mask="255.255.255.0")
    srv = Server(hostname="WEBSERVER", ip_address="10.10.1.100", subnet_mask="255.255.255.0")
    s1 = Switch(hostname="switch1")

    for n in [pc1, pc2, srv, s1]:
        sim.network.add_node(n)

    database_service = DatabaseService(file_system=srv.file_system)
    srv.install_service(database_service)

    downloads_folder = pc1.file_system.create_folder("downloads")
    pc1.file_system.create_file("bermuda_triangle.png", folder_name="downloads")

    sim.network.connect(pc1.ethernet_port[1], s1.switch_ports[1])
    sim.network.connect(pc2.ethernet_port[1], s1.switch_ports[2])
    sim.network.connect(s1.switch_ports[3], srv.ethernet_port[1])

    # call this method to make sure no errors occur.
    sim._action_manager.get_action_tree()

    # patch the action to do something which we can check the result of.
    action_invoked = False

    def succeed():
        nonlocal action_invoked
        action_invoked = True

    monkeypatch.setitem(
        downloads_folder._action_manager.actions, "repair", Action(func=lambda request, context: succeed())
    )

    assert not action_invoked

    # call the patched method
    sim.apply_action(
        ["network", "node", pc1.uuid, "file_system", "folder", pc1.file_system.get_folder("downloads").uuid, "repair"]
    )

    assert action_invoked
