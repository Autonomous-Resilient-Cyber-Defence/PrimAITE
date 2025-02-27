# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
import copy
from uuid import uuid4

import pytest
from gymnasium import spaces

from primaite.game.agent.observations.host_observations import HostObservation
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.sim_container import Simulation


@pytest.fixture(scope="function")
def simulation(example_network) -> Simulation:
    sim = Simulation()

    # set simulation network as example network
    sim.network = example_network

    return sim


def test_host_observation(simulation):
    """Test a Host observation."""
    pc: Computer = simulation.network.get_node_by_hostname("client_1")

    host_obs = HostObservation(
        where=["network", "nodes", pc.config.hostname],
        num_applications=0,
        num_files=1,
        num_folders=1,
        num_nics=2,
        num_services=1,
        include_num_access=False,
        include_nmne=False,
        monitored_traffic=None,
        services=[],
        applications=[],
        folders=[],
        network_interfaces=[],
        file_system_requires_scan=True,
        services_requires_scan=True,
        applications_requires_scan=True,
        include_users=False,
    )

    assert host_obs.space["operating_status"] == spaces.Discrete(5)

    observation_state = host_obs.observe(simulation.describe_state())
    assert observation_state.get("operating_status") == 1  # computer is on

    assert observation_state.get("SERVICES") is not None
    assert observation_state.get("FOLDERS") is not None
    assert observation_state.get("NICS") is not None

    # turn off computer
    pc.power_off()
    observation_state = host_obs.observe(simulation.describe_state())
    assert observation_state.get("operating_status") == 4  # shutting down

    for i in range(pc.config.shut_down_duration + 1):
        pc.apply_timestep(i)

    observation_state = host_obs.observe(simulation.describe_state())
    assert observation_state.get("operating_status") == 2
