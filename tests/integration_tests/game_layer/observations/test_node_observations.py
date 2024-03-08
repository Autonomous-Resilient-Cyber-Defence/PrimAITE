import copy
from uuid import uuid4

import pytest

from primaite.game.agent.observations.node_observations import NodeObservation
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.sim_container import Simulation


@pytest.fixture(scope="function")
def simulation(example_network) -> Simulation:
    sim = Simulation()

    # set simulation network as example network
    sim.network = example_network

    return sim


def test_node_observation(simulation):
    """Test a Node observation."""
    pc: Computer = simulation.network.get_node_by_hostname("client_1")

    node_obs = NodeObservation(where=["network", "nodes", pc.hostname])

    observation_state = node_obs.observe(simulation.describe_state())
    assert observation_state.get("operating_status") == 1  # computer is on

    assert observation_state.get("SERVICES") is not None
    assert observation_state.get("FOLDERS") is not None
    assert observation_state.get("NETWORK_INTERFACES") is not None

    # turn off computer
    pc.power_off()
    observation_state = node_obs.observe(simulation.describe_state())
    assert observation_state.get("operating_status") == 4  # shutting down

    for i in range(pc.shut_down_duration + 1):
        pc.apply_timestep(i)

    observation_state = node_obs.observe(simulation.describe_state())
    assert observation_state.get("operating_status") == 2
