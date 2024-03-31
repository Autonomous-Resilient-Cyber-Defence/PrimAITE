from pathlib import Path
from typing import Union

import pytest
import yaml
from gymnasium import spaces

from primaite.game.agent.observations.nic_observations import NICObservation
from primaite.game.game import PrimaiteGame
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.host_node import NIC
from primaite.simulator.network.nmne import CAPTURE_NMNE
from primaite.simulator.sim_container import Simulation
from tests import TEST_ASSETS_ROOT

BASIC_CONFIG = TEST_ASSETS_ROOT / "configs/basic_switched_network.yaml"


def load_config(config_path: Union[str, Path]) -> PrimaiteGame:
    """Returns a PrimaiteGame object which loads the contents of a given yaml path."""
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    return PrimaiteGame.from_config(cfg)


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

    nic_obs = NICObservation(where=["network", "nodes", pc.hostname, "NICs", 1])

    assert nic_obs.space["nic_status"] == spaces.Discrete(3)
    assert nic_obs.space["NMNE"]["inbound"] == spaces.Discrete(4)
    assert nic_obs.space["NMNE"]["outbound"] == spaces.Discrete(4)

    observation_state = nic_obs.observe(simulation.describe_state())
    assert observation_state.get("nic_status") == 1  # enabled
    assert observation_state.get("NMNE") is not None
    assert observation_state["NMNE"].get("inbound") == 0
    assert observation_state["NMNE"].get("outbound") == 0

    nic.disable()
    observation_state = nic_obs.observe(simulation.describe_state())
    assert observation_state.get("nic_status") == 2  # disabled


def test_nic_categories(simulation):
    """Test the NIC observation nmne count categories."""
    pc: Computer = simulation.network.get_node_by_hostname("client_1")

    nic_obs = NICObservation(where=["network", "nodes", pc.hostname, "NICs", 1])

    assert nic_obs.high_nmne_threshold == 10  # default
    assert nic_obs.med_nmne_threshold == 5  # default
    assert nic_obs.low_nmne_threshold == 0  # default

    nic_obs = NICObservation(
        where=["network", "nodes", pc.hostname, "NICs", 1],
        low_nmne_threshold=3,
        med_nmne_threshold=6,
        high_nmne_threshold=9,
    )

    assert nic_obs.high_nmne_threshold == 9
    assert nic_obs.med_nmne_threshold == 6
    assert nic_obs.low_nmne_threshold == 3

    with pytest.raises(Exception):
        # should throw an error
        NICObservation(
            where=["network", "nodes", pc.hostname, "NICs", 1],
            low_nmne_threshold=9,
            med_nmne_threshold=6,
            high_nmne_threshold=9,
        )

    with pytest.raises(Exception):
        # should throw an error
        NICObservation(
            where=["network", "nodes", pc.hostname, "NICs", 1],
            low_nmne_threshold=3,
            med_nmne_threshold=9,
            high_nmne_threshold=9,
        )
