# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from primaite.simulator.sim_container import Simulation


def test_creating_empty_simulation():
    """Check that no errors occur when trying to setup a simulation without providing parameters"""
    empty_sim = Simulation()


def test_empty_sim_state():
    """Check that describe_state has the right subcomponents."""
    empty_sim = Simulation()
    sim_state = empty_sim.describe_state()
    network_state = empty_sim.network.describe_state()
    domain_state = empty_sim.domain.describe_state()
    assert sim_state["network"] == network_state
    assert sim_state["domain"] == domain_state
