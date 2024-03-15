import yaml

from primaite.game.game import PrimaiteGame
from tests import TEST_ASSETS_ROOT

CONFIG_FILE = TEST_ASSETS_ROOT / "configs" / "no_nodes_links_agents_network.yaml"


def test_no_nodes_links_agents_config():
    """Tests PrimaiteGame can be created from config file where there are no nodes, links, agents in the config file."""
    with open(CONFIG_FILE, "r") as f:
        cfg = yaml.safe_load(f)

    game = PrimaiteGame.from_config(cfg)

    network = game.simulation.network

    assert len(network.nodes) == 0
    assert len(network.links) == 0
