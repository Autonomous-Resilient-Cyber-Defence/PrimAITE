# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from ipaddress import IPv4Address

import pytest

from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.network.firewall import Firewall
from primaite.simulator.network.hardware.nodes.network.router import ACLAction
from primaite.simulator.system.services.ntp.ntp_client import NTPClient
from primaite.simulator.system.services.ntp.ntp_server import NTPServer
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.port import PORT_LOOKUP


@pytest.fixture(scope="function")
def dmz_external_internal_network() -> Network:
    """
    Fixture for setting up a simulated network with a firewall, external node, internal node, and DMZ node. This
    configuration is designed to test firewall rules and their impact on traffic between these network segments.

    --------------         --------------         --------------
    |  external  |---------|  firewall  |---------|  internal  |
    --------------         --------------         --------------
                                  |
                                  |
                              ---------
                              |  DMZ  |
                              ---------

    The network is set up as follows:
    - An external node simulates an entity outside the organization's network.
    - An internal node represents a device within the organization's LAN.
    - A DMZ (Demilitarized Zone) node acts as a server or service exposed to external traffic.
    - A firewall node controls traffic between these nodes based on ACL (Access Control List) rules.

    The firewall is configured to allow ICMP and ARP traffic across all interfaces to ensure basic connectivity
    for the tests. Specific tests will modify ACL rules to test various traffic filtering scenarios.

    :return: A `Network` instance with the described nodes and configurations.
    """
    network = Network()

    firewall_node: Firewall = Firewall(hostname="firewall_1", start_up_duration=0)
    firewall_node.power_on()
    # configure firewall ports
    firewall_node.configure_external_port(
        ip_address=IPv4Address("192.168.10.1"), subnet_mask=IPv4Address("255.255.255.0")
    )
    firewall_node.configure_dmz_port(ip_address=IPv4Address("192.168.1.1"), subnet_mask=IPv4Address("255.255.255.0"))
    firewall_node.configure_internal_port(
        ip_address=IPv4Address("192.168.0.1"), subnet_mask=IPv4Address("255.255.255.0")
    )

    # Allow ICMP
    firewall_node.internal_inbound_acl.add_rule(action=ACLAction.PERMIT, protocol=PROTOCOL_LOOKUP["ICMP"], position=23)
    firewall_node.internal_outbound_acl.add_rule(action=ACLAction.PERMIT, protocol=PROTOCOL_LOOKUP["ICMP"], position=23)
    firewall_node.external_inbound_acl.add_rule(action=ACLAction.PERMIT, protocol=PROTOCOL_LOOKUP["ICMP"], position=23)
    firewall_node.external_outbound_acl.add_rule(action=ACLAction.PERMIT, protocol=PROTOCOL_LOOKUP["ICMP"], position=23)
    firewall_node.dmz_inbound_acl.add_rule(action=ACLAction.PERMIT, protocol=PROTOCOL_LOOKUP["ICMP"], position=23)
    firewall_node.dmz_outbound_acl.add_rule(action=ACLAction.PERMIT, protocol=PROTOCOL_LOOKUP["ICMP"], position=23)

    # Allow ARP
    firewall_node.internal_inbound_acl.add_rule(
        action=ACLAction.PERMIT, src_port=PORT_LOOKUP["ARP"], dst_port=PORT_LOOKUP["ARP"], position=22
    )
    firewall_node.internal_outbound_acl.add_rule(
        action=ACLAction.PERMIT, src_port=PORT_LOOKUP["ARP"], dst_port=PORT_LOOKUP["ARP"], position=22
    )
    firewall_node.external_inbound_acl.add_rule(
        action=ACLAction.PERMIT, src_port=PORT_LOOKUP["ARP"], dst_port=PORT_LOOKUP["ARP"], position=22
    )
    firewall_node.external_outbound_acl.add_rule(
        action=ACLAction.PERMIT, src_port=PORT_LOOKUP["ARP"], dst_port=PORT_LOOKUP["ARP"], position=22
    )
    firewall_node.dmz_inbound_acl.add_rule(
        action=ACLAction.PERMIT, src_port=PORT_LOOKUP["ARP"], dst_port=PORT_LOOKUP["ARP"], position=22
    )
    firewall_node.dmz_outbound_acl.add_rule(
        action=ACLAction.PERMIT, src_port=PORT_LOOKUP["ARP"], dst_port=PORT_LOOKUP["ARP"], position=22
    )

    # external node
    external_node = Computer(
        hostname="external_node",
        ip_address="192.168.10.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.10.1",
        start_up_duration=0,
    )
    external_node.power_on()
    external_node.software_manager.install(NTPServer)
    ntp_service: NTPServer = external_node.software_manager.software["ntp-server"]
    ntp_service.start()
    # connect external node to firewall node
    network.connect(endpoint_b=external_node.network_interface[1], endpoint_a=firewall_node.external_port)

    # internal node
    internal_node = Computer(
        hostname="internal_node",
        ip_address="192.168.0.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.0.1",
        start_up_duration=0,
    )
    internal_node.power_on()
    internal_node.software_manager.install(NTPClient)
    internal_ntp_client: NTPClient = internal_node.software_manager.software["ntp-client"]
    internal_ntp_client.configure(external_node.network_interface[1].ip_address)
    internal_ntp_client.start()
    # connect external node to firewall node
    network.connect(endpoint_b=internal_node.network_interface[1], endpoint_a=firewall_node.internal_port)

    # dmz node
    dmz_node = Computer(
        hostname="dmz_node",
        ip_address="192.168.1.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    dmz_node.power_on()
    dmz_ntp_client: NTPClient = dmz_node.software_manager.software["ntp-client"]
    dmz_ntp_client.configure(external_node.network_interface[1].ip_address)
    dmz_ntp_client.start()
    # connect external node to firewall node
    network.connect(endpoint_b=dmz_node.network_interface[1], endpoint_a=firewall_node.dmz_port)

    return network


def test_firewall_can_ping_nodes(dmz_external_internal_network):
    """
    Tests the firewall's ability to ping the external, internal, and DMZ nodes in the network.

    Verifies that the firewall has connectivity to all nodes within the network by performing a ping operation.
    Successful pings indicate proper network setup and basic ICMP traffic passage through the firewall.
    """
    firewall = dmz_external_internal_network.get_node_by_hostname("firewall_1")

    # ping from the firewall
    assert firewall.ping("192.168.0.2")  # firewall to internal
    assert firewall.ping("192.168.1.2")  # firewall to dmz
    assert firewall.ping("192.168.10.2")  # firewall to external


def test_nodes_can_ping_default_gateway(dmz_external_internal_network):
    """
    Checks if the external, internal, and DMZ nodes can ping their respective default gateways.

    This test confirms that each node is correctly configured with a route to its default gateway and that the
    firewall permits ICMP traffic for these basic connectivity checks.
    """
    external_node = dmz_external_internal_network.get_node_by_hostname("external_node")
    internal_node = dmz_external_internal_network.get_node_by_hostname("internal_node")
    dmz_node = dmz_external_internal_network.get_node_by_hostname("dmz_node")

    assert internal_node.ping(internal_node.default_gateway)  # default gateway internal
    assert dmz_node.ping(dmz_node.default_gateway)  # default gateway dmz
    assert external_node.ping(external_node.default_gateway)  # default gateway external


def test_nodes_can_ping_default_gateway_on_another_subnet(dmz_external_internal_network):
    """
    Verifies that nodes can ping default gateways located in a different subnet, facilitated by the firewall.

    This test assesses the routing and firewall ACL configurations that allow ICMP traffic between different
    network segments, ensuring that nodes can reach default gateways outside their local subnet.
    """
    external_node = dmz_external_internal_network.get_node_by_hostname("external_node")
    internal_node = dmz_external_internal_network.get_node_by_hostname("internal_node")
    dmz_node = dmz_external_internal_network.get_node_by_hostname("dmz_node")

    assert internal_node.ping(external_node.default_gateway)  # internal node to external default gateway
    assert internal_node.ping(dmz_node.default_gateway)  # internal node to dmz default gateway

    assert dmz_node.ping(internal_node.default_gateway)  # dmz node to internal default gateway
    assert dmz_node.ping(external_node.default_gateway)  # dmz node to external default gateway

    assert external_node.ping(external_node.default_gateway)  # external node to internal default gateway
    assert external_node.ping(dmz_node.default_gateway)  # external node to dmz default gateway


def test_nodes_can_ping_each_other(dmz_external_internal_network):
    """
    Evaluates the ability of each node (external, internal, DMZ) to ping the other nodes within the network.

    This comprehensive connectivity test checks if the firewall's current ACL configuration allows for inter-node
    communication via ICMP pings, highlighting the effectiveness of the firewall rules in place.
    """
    external_node = dmz_external_internal_network.get_node_by_hostname("external_node")
    internal_node = dmz_external_internal_network.get_node_by_hostname("internal_node")
    dmz_node = dmz_external_internal_network.get_node_by_hostname("dmz_node")

    # test that nodes can ping each other
    assert internal_node.ping(external_node.network_interface[1].ip_address)
    assert internal_node.ping(dmz_node.network_interface[1].ip_address)

    assert external_node.ping(internal_node.network_interface[1].ip_address)
    assert external_node.ping(dmz_node.network_interface[1].ip_address)

    assert dmz_node.ping(internal_node.network_interface[1].ip_address)
    assert dmz_node.ping(external_node.network_interface[1].ip_address)


def test_service_blocked(dmz_external_internal_network):
    """
    Tests the firewall's default blocking stance on NTP service requests from internal and DMZ nodes.

    Initially, without specific ACL rules to allow NTP traffic, this test confirms that NTP clients on both the
    internal and DMZ nodes are unable to update their time, demonstrating the firewall's effective blocking of
    unspecified services.
    """
    firewall = dmz_external_internal_network.get_node_by_hostname("firewall_1")
    internal_node = dmz_external_internal_network.get_node_by_hostname("internal_node")
    dmz_node = dmz_external_internal_network.get_node_by_hostname("dmz_node")
    internal_ntp_client: NTPClient = internal_node.software_manager.software["ntp-client"]
    dmz_ntp_client: NTPClient = dmz_node.software_manager.software["ntp-client"]

    assert not internal_ntp_client.time

    internal_ntp_client.request_time()

    assert not internal_ntp_client.time

    assert not dmz_ntp_client.time

    dmz_ntp_client.request_time()

    assert not dmz_ntp_client.time

    firewall.show_rules()


def test_service_allowed_with_rule(dmz_external_internal_network):
    """
    Tests that NTP service requests are allowed through the firewall based on ACL rules.

    This test verifies the functionality of the firewall in a network scenario where both an internal node and
    a node in the DMZ attempt to access NTP services. Initially, no NTP traffic is allowed. The test then
    configures ACL rules on the firewall to permit NTP traffic and checks if the NTP clients on the internal
    node and DMZ node can successfully request and receive time updates.

    Procedure:
        1. Assert that the internal node's NTP client initially has no time information due to ACL restrictions.
        2. Add ACL rules to the firewall to permit outbound and inbound NTP traffic from the internal network.
        3. Trigger an NTP time request from the internal node and assert that it successfully receives time
           information.
        4. Assert that the DMZ node's NTP client initially has no time information.
        5. Add ACL rules to the firewall to permit outbound and inbound NTP traffic from the DMZ.
        6. Trigger an NTP time request from the DMZ node and assert that it successfully receives time information.

    Asserts:
        - The internal node's NTP client has no time information before ACL rules are applied.
        - The internal node's NTP client successfully receives time information after the appropriate ACL rules
          are applied.
        - The DMZ node's NTP client has no time information before ACL rules are applied for the DMZ.
        - The DMZ node's NTP client successfully receives time information after the appropriate ACL rules for
          the DMZ are applied.
    """
    firewall = dmz_external_internal_network.get_node_by_hostname("firewall_1")
    internal_node = dmz_external_internal_network.get_node_by_hostname("internal_node")
    dmz_node = dmz_external_internal_network.get_node_by_hostname("dmz_node")
    internal_ntp_client: NTPClient = internal_node.software_manager.software["ntp-client"]
    dmz_ntp_client: NTPClient = dmz_node.software_manager.software["ntp-client"]

    assert not internal_ntp_client.time

    firewall.internal_outbound_acl.add_rule(
        action=ACLAction.PERMIT, src_port=PORT_LOOKUP["NTP"], dst_port=PORT_LOOKUP["NTP"], position=1
    )
    firewall.internal_inbound_acl.add_rule(
        action=ACLAction.PERMIT, src_port=PORT_LOOKUP["NTP"], dst_port=PORT_LOOKUP["NTP"], position=1
    )

    internal_ntp_client.request_time()

    assert internal_ntp_client.time

    assert not dmz_ntp_client.time

    firewall.dmz_outbound_acl.add_rule(
        action=ACLAction.PERMIT, src_port=PORT_LOOKUP["NTP"], dst_port=PORT_LOOKUP["NTP"], position=1
    )
    firewall.dmz_inbound_acl.add_rule(
        action=ACLAction.PERMIT, src_port=PORT_LOOKUP["NTP"], dst_port=PORT_LOOKUP["NTP"], position=1
    )

    dmz_ntp_client.request_time()

    assert dmz_ntp_client.time

    firewall.show_rules()
