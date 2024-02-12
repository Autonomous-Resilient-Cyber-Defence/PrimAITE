from pathlib import Path
from typing import Union

import yaml

from primaite.game.game import PrimaiteGame
from primaite.simulator.network.container import Network
from tests import TEST_ASSETS_ROOT

DMZ_NETWORK = TEST_ASSETS_ROOT / "configs/dmz_network.yaml"


def load_config(config_path: Union[str, Path]) -> PrimaiteGame:
    """Returns a PrimaiteGame object which loads the contents of a given yaml path."""
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    return PrimaiteGame.from_config(cfg)


def test_dmz_config():
    """Test that the DMZ network config can be parsed properly."""
    game = load_config(DMZ_NETWORK)

    network: Network = game.simulation.network

    assert len(network.nodes) == 9  # 9 nodes in network
    assert len(network.routers) == 2  # 2 routers in network
    assert len(network.switches) == 3  # 3 switches in network
    assert len(network.servers) == 1  # 1 server in network


def test_router_routes_are_correctly_added():
    """Test that makes sure that router routes have been added from the configuration file."""
    pass


def test_firewall_node_added_to_network():
    """Test that the firewall has been correctly added to and configured in the network."""
    pass


def test_router_acl_rules_correctly_added():
    """Test that makes sure that the router ACLs have been configured onto the router node via configuration file."""
    pass


def test_firewall_routes_are_correctly_added():
    """Test that the firewall routes have been correctly added to and configured in the network."""
    pass


def test_firewall_acl_rules_correctly_added():
    """
    Test that makes sure that the firewall ACLs have been configured onto the firewall
    node via configuration file.
    """
    pass
