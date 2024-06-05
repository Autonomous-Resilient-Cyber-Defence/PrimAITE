# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from ipaddress import IPv4Address

import pytest

from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.hardware.nodes.network.firewall import Firewall
from primaite.simulator.network.hardware.nodes.network.router import ACLAction
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from tests.integration_tests.configuration_file_parsing import BASIC_FIREWALL, DMZ_NETWORK, load_config


@pytest.fixture(scope="function")
def dmz_config() -> Network:
    game = load_config(DMZ_NETWORK)
    return game.simulation.network


@pytest.fixture(scope="function")
def basic_firewall_config() -> Network:
    game = load_config(BASIC_FIREWALL)
    return game.simulation.network


def test_firewall_is_in_configuration(dmz_config):
    """Test that the firewall exists in the configuration file."""
    network: Network = dmz_config

    firewall: Firewall = network.get_node_by_hostname("firewall")

    assert firewall
    assert firewall.operating_state == NodeOperatingState.ON


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

    # client_1 should be able to ping other nodes
    assert client_1.ping(dmz_server.network_interface[1].ip_address)
    assert client_1.ping(external_computer.network_interface[1].ip_address)
    assert client_1.ping(external_server.network_interface[1].ip_address)


def test_firewall_acl_rules_correctly_added(dmz_config):
    """
    Test that makes sure that the firewall ACLs have been configured onto the firewall
    node via configuration file.
    """
    firewall: Firewall = dmz_config.get_node_by_hostname("firewall")

    # ICMP and ARP should be allowed internal_inbound
    assert firewall.internal_inbound_acl.num_rules == 2
    assert firewall.internal_inbound_acl.acl[22].action == ACLAction.PERMIT
    assert firewall.internal_inbound_acl.acl[22].src_port == Port.ARP
    assert firewall.internal_inbound_acl.acl[22].dst_port == Port.ARP
    assert firewall.internal_inbound_acl.acl[23].action == ACLAction.PERMIT
    assert firewall.internal_inbound_acl.acl[23].protocol == IPProtocol.ICMP
    assert firewall.internal_inbound_acl.implicit_action == ACLAction.DENY

    # ICMP and ARP should be allowed internal_outbound
    assert firewall.internal_outbound_acl.num_rules == 2
    assert firewall.internal_outbound_acl.acl[22].action == ACLAction.PERMIT
    assert firewall.internal_outbound_acl.acl[22].src_port == Port.ARP
    assert firewall.internal_outbound_acl.acl[22].dst_port == Port.ARP
    assert firewall.internal_outbound_acl.acl[23].action == ACLAction.PERMIT
    assert firewall.internal_outbound_acl.acl[23].protocol == IPProtocol.ICMP
    assert firewall.internal_outbound_acl.implicit_action == ACLAction.DENY

    # ICMP and ARP should be allowed dmz_inbound
    assert firewall.dmz_inbound_acl.num_rules == 2
    assert firewall.dmz_inbound_acl.acl[22].action == ACLAction.PERMIT
    assert firewall.dmz_inbound_acl.acl[22].src_port == Port.ARP
    assert firewall.dmz_inbound_acl.acl[22].dst_port == Port.ARP
    assert firewall.dmz_inbound_acl.acl[23].action == ACLAction.PERMIT
    assert firewall.dmz_inbound_acl.acl[23].protocol == IPProtocol.ICMP
    assert firewall.dmz_inbound_acl.implicit_action == ACLAction.DENY

    # ICMP and ARP should be allowed dmz_outbound
    assert firewall.dmz_outbound_acl.num_rules == 2
    assert firewall.dmz_outbound_acl.acl[22].action == ACLAction.PERMIT
    assert firewall.dmz_outbound_acl.acl[22].src_port == Port.ARP
    assert firewall.dmz_outbound_acl.acl[22].dst_port == Port.ARP
    assert firewall.dmz_outbound_acl.acl[23].action == ACLAction.PERMIT
    assert firewall.dmz_outbound_acl.acl[23].protocol == IPProtocol.ICMP
    assert firewall.dmz_outbound_acl.implicit_action == ACLAction.DENY

    # ICMP and ARP should be allowed external_inbound
    assert firewall.external_inbound_acl.num_rules == 1
    assert firewall.external_inbound_acl.acl[22].action == ACLAction.PERMIT
    assert firewall.external_inbound_acl.acl[22].src_port == Port.ARP
    assert firewall.external_inbound_acl.acl[22].dst_port == Port.ARP
    # external_inbound should have implicit action PERMIT
    # ICMP does not have a provided ACL Rule but implicit action should allow anything
    assert firewall.external_inbound_acl.implicit_action == ACLAction.PERMIT

    # ICMP and ARP should be allowed external_outbound
    assert firewall.external_outbound_acl.num_rules == 1
    assert firewall.external_outbound_acl.acl[22].action == ACLAction.PERMIT
    assert firewall.external_outbound_acl.acl[22].src_port == Port.ARP
    assert firewall.external_outbound_acl.acl[22].dst_port == Port.ARP
    # external_outbound should have implicit action PERMIT
    # ICMP does not have a provided ACL Rule but implicit action should allow anything
    assert firewall.external_outbound_acl.implicit_action == ACLAction.PERMIT


def test_firewall_with_no_dmz_port(basic_firewall_config):
    """
    Test to check that:
     - the DMZ port can be ignored i.e. is optional.
     - the external_outbound_acl and external_inbound_acl are optional
    """
    network: Network = basic_firewall_config

    firewall: Firewall = network.get_node_by_hostname("firewall")

    assert firewall.dmz_port.ip_address == IPv4Address("127.0.0.1")

    assert firewall.external_outbound_acl.num_rules == 0
    assert firewall.external_inbound_acl.num_rules == 0
