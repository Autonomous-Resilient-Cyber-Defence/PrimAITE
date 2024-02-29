import pytest

from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.hardware.nodes.network.router import ACLAction, Router
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from tests.integration_tests.configuration_file_parsing import DMZ_NETWORK, load_config


@pytest.fixture(scope="function")
def dmz_config() -> Network:
    game = load_config(DMZ_NETWORK)
    return game.simulation.network


def test_router_is_in_configuration(dmz_config):
    """Test that the router exists in the configuration file."""
    network: Network = dmz_config

    router_1: Router = network.get_node_by_hostname("router_1")

    assert router_1
    assert router_1.operating_state == NodeOperatingState.ON


def test_router_routes_are_correctly_added(dmz_config):
    """Test that makes sure that router routes have been added from the configuration file."""
    network: Network = dmz_config

    router_1: Router = network.get_node_by_hostname("router_1")
    client_1: Computer = network.get_node_by_hostname("client_1")
    dmz_server: Server = network.get_node_by_hostname("dmz_server")
    external_computer: Computer = network.get_node_by_hostname("external_computer")
    external_server: Server = network.get_node_by_hostname("external_server")

    # there should be a route to dmz_server
    assert router_1.route_table.find_best_route(dmz_server.network_interface[1].ip_address)
    assert client_1.ping(dmz_server.network_interface[1].ip_address)
    assert external_computer.ping(dmz_server.network_interface[1].ip_address)
    assert external_server.ping(dmz_server.network_interface[1].ip_address)

    # there should be a route to external_computer
    assert router_1.route_table.find_best_route(external_computer.network_interface[1].ip_address)
    assert client_1.ping(external_computer.network_interface[1].ip_address)
    assert dmz_server.ping(external_computer.network_interface[1].ip_address)
    assert external_server.ping(external_computer.network_interface[1].ip_address)

    # there should be a route to external_server
    assert router_1.route_table.find_best_route(external_server.network_interface[1].ip_address)
    assert client_1.ping(external_server.network_interface[1].ip_address)
    assert dmz_server.ping(external_server.network_interface[1].ip_address)
    assert external_computer.ping(external_server.network_interface[1].ip_address)


def test_router_acl_rules_correctly_added(dmz_config):
    """Test that makes sure that the router ACLs have been configured onto the router node via configuration file."""
    router_1: Router = dmz_config.get_node_by_hostname("router_1")

    # ICMP and ARP should be allowed
    assert router_1.acl.num_rules == 2
    assert router_1.acl.acl[22].action == ACLAction.PERMIT
    assert router_1.acl.acl[22].src_port == Port.ARP
    assert router_1.acl.acl[22].dst_port == Port.ARP
    assert router_1.acl.acl[23].action == ACLAction.PERMIT
    assert router_1.acl.acl[23].protocol == IPProtocol.ICMP
    assert router_1.acl.implicit_action == ACLAction.DENY
