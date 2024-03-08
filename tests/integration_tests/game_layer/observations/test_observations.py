import pytest

from primaite.game.agent.observations.observations import NicObservation
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.host_node import NIC
from primaite.simulator.sim_container import Simulation


@pytest.fixture(scope="function")
def simulation(example_network) -> Simulation:
    sim = Simulation()

    # set simulation network as example network
    sim.network = example_network

    return sim


def test_nic(simulation):
    """Test the NIC observation."""
    pc: Computer = simulation.network.get_node_by_hostname("client_1")

    nic: NIC = pc.network_interface[1]

    nic_obs = NicObservation(where=["network", "nodes", pc.hostname, "NICs", 1])

    observation_state = nic_obs.observe(simulation.describe_state())
    assert observation_state.get("nic_status") == 1  # enabled
    assert observation_state.get("nmne") is not None
    assert observation_state["nmne"].get("inbound") == 0
    assert observation_state["nmne"].get("outbound") == 0

    nic.disable()
    observation_state = nic_obs.observe(simulation.describe_state())
    assert observation_state.get("nic_status") == 2  # disabled
