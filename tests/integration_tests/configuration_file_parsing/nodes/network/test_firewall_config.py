import pytest

from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.hardware.nodes.network.firewall import Firewall
from tests.integration_tests.configuration_file_parsing import DMZ_NETWORK, load_config


@pytest.fixture(scope="function")
def dmz_config() -> Network:
    game = load_config(DMZ_NETWORK)
    return game.simulation.network


def test_firewall_is_in_configuration(dmz_config):
    """Test that the firewall exists in the configuration file."""
    network: Network = dmz_config

    assert network.get_node_by_hostname("firewall")


def test_firewall_routes_are_correctly_added(dmz_config):
    """Test that the firewall routes have been correctly added to and configured in the network."""
    network: Network = dmz_config

    firewall: Firewall = network.get_node_by_hostname("firewall")
    client_1: Computer = network.get_node_by_hostname("client_1")
    dmz_server: Server = network.get_node_by_hostname("dmz_server")
    external_computer: Computer = network.get_node_by_hostname("external_computer")
    external_server: Server = network.get_node_by_hostname("external_server")

    # there should be a route to client_1
    assert firewall.route_table.find_best_route(client_1.network_interface[1].ip_address)
    assert dmz_server.ping(client_1.network_interface[1].ip_address)
    assert external_computer.ping(client_1.network_interface[1].ip_address)
    assert external_server.ping(client_1.network_interface[1].ip_address)


def test_firewall_acl_rules_correctly_added():
    """
    Test that makes sure that the firewall ACLs have been configured onto the firewall
    node via configuration file.
    """
    pass
