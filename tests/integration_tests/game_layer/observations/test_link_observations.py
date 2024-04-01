import pytest
from gymnasium import spaces

from primaite.game.agent.observations.link_observation import LinkObservation
from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.base import Link, Node
from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.hardware.nodes.network.switch import Switch
from primaite.simulator.sim_container import Simulation


@pytest.fixture(scope="function")
def simulation() -> Simulation:
    sim = Simulation()

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

    # Should be linked
    assert next(iter(network.links.values())).is_up

    assert computer.ping(server.network_interface.get(1).ip_address)

    # set simulation network as example network
    sim.network = network

    return sim


def test_link_observation():
    """Check the shape and contents of the link observation."""
    net = Network()
    sim = Simulation(network=net)
    switch = Switch(hostname="switch", num_ports=5, operating_state=NodeOperatingState.ON)
    computer_1 = Computer(
        hostname="computer_1", ip_address="10.0.0.1", subnet_mask="255.255.255.0", start_up_duration=0
    )
    computer_2 = Computer(
        hostname="computer_2", ip_address="10.0.0.2", subnet_mask="255.255.255.0", start_up_duration=0
    )
    computer_1.power_on()
    computer_2.power_on()
    link_1 = net.connect(switch.network_interface[1], computer_1.network_interface[1])
    link_2 = net.connect(switch.network_interface[2], computer_2.network_interface[1])
    assert link_1 is not None
    assert link_2 is not None

    link_1_observation = LinkObservation(where=["network", "links", link_1.uuid])
    link_2_observation = LinkObservation(where=["network", "links", link_2.uuid])

    state = sim.describe_state()
    link_1_obs = link_1_observation.observe(state)
    link_2_obs = link_2_observation.observe(state)
    assert "PROTOCOLS" in link_1_obs
    assert "PROTOCOLS" in link_2_obs
    assert "ALL" in link_1_obs["PROTOCOLS"]
    assert "ALL" in link_2_obs["PROTOCOLS"]
    assert link_1_observation.space["PROTOCOLS"]["ALL"] == spaces.Discrete(11)
    assert link_2_observation.space["PROTOCOLS"]["ALL"] == spaces.Discrete(11)
    assert link_1_obs["PROTOCOLS"]["ALL"] == 0
    assert link_2_obs["PROTOCOLS"]["ALL"] == 0

    # Test that the link observation is updated when a packet is sent
    computer_1.ping("10.0.0.2")
    computer_2.ping("10.0.0.1")
    state = sim.describe_state()
    link_1_obs = link_1_observation.observe(state)
    link_2_obs = link_2_observation.observe(state)
    assert link_1_obs["PROTOCOLS"]["ALL"] > 0
    assert link_2_obs["PROTOCOLS"]["ALL"] > 0
