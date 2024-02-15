from primaite.config.load import example_config_path
from primaite.simulator.network.container import Network
from tests.integration_tests.configuration_file_parsing import DMZ_NETWORK, load_config


def test_example_config():
    """Test that the example config can be parsed properly."""
    game = load_config(example_config_path())
    network: Network = game.simulation.network

    assert len(network.nodes) == 10  # 10 nodes in example network
    assert len(network.routers) == 1  # 1 router in network
    assert len(network.switches) == 2  # 2 switches in network
    assert len(network.servers) == 5  # 5 servers in network


def test_dmz_config():
    """Test that the DMZ network config can be parsed properly."""
    game = load_config(DMZ_NETWORK)

    network: Network = game.simulation.network

    assert len(network.nodes) == 9  # 9 nodes in network
    assert len(network.routers) == 2  # 2 routers in network
    assert len(network.switches) == 3  # 3 switches in network
    assert len(network.servers) == 2  # 2 servers in network
