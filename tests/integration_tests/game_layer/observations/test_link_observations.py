import pytest
from gymnasium import spaces

from primaite.game.agent.observations.link_observation import LinkObservation
from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.base import Link, Node
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
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


def test_link_observation(simulation):
    """Test the link observation."""
    # get a link
    link: Link = next(iter(simulation.network.links.values()))

    computer: Computer = simulation.network.get_node_by_hostname("computer")
    server: Server = simulation.network.get_node_by_hostname("server")

    simulation.apply_timestep(0)  # some pings when network was made - reset with apply timestep

    link_obs = LinkObservation(where=["network", "links", link.uuid])

    assert link_obs.space["PROTOCOLS"]["ALL"] == spaces.Discrete(11)  # test that the spaces are 0-10 including 0 and 10

    observation_state = link_obs.observe(simulation.describe_state())
    assert observation_state.get("PROTOCOLS") is not None
    assert observation_state["PROTOCOLS"]["ALL"] == 0

    computer.ping(server.network_interface.get(1).ip_address)

    observation_state = link_obs.observe(simulation.describe_state())
    assert observation_state["PROTOCOLS"]["ALL"] == 1
