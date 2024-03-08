import pytest

from primaite.game.agent.observations.nic_observations import NicObservation
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


def test_nic_categories(simulation):
    """Test the NIC observation nmne count categories."""
    pc: Computer = simulation.network.get_node_by_hostname("client_1")

    nic_obs = NicObservation(where=["network", "nodes", pc.hostname, "NICs", 1])

    assert nic_obs.high_nmne_threshold == 10  # default
    assert nic_obs.med_nmne_threshold == 5  # default
    assert nic_obs.low_nmne_threshold == 0  # default

    nic_obs = NicObservation(
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
        NicObservation(
            where=["network", "nodes", pc.hostname, "NICs", 1],
            low_nmne_threshold=9,
            med_nmne_threshold=6,
            high_nmne_threshold=9,
        )

    with pytest.raises(Exception):
        # should throw an error
        NicObservation(
            where=["network", "nodes", pc.hostname, "NICs", 1],
            low_nmne_threshold=3,
            med_nmne_threshold=9,
            high_nmne_threshold=9,
        )
