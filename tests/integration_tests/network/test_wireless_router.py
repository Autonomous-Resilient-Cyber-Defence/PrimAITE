# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
import pytest
import yaml

from primaite.game.game import PrimaiteGame
from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.network.router import ACLAction
from primaite.simulator.network.hardware.nodes.network.wireless_router import WirelessRouter
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.port import PORT_LOOKUP
from tests import TEST_ASSETS_ROOT


@pytest.fixture(scope="function")
def wireless_wan_network():
    network = Network()

    # Configure PC A
    pc_a = Computer.from_config(
        config={
            "type": "computer",
            "hostname": "pc_a",
            "ip_address": "192.168.0.2",
            "subnet_mask": "255.255.255.0",
            "default_gateway": "192.168.0.1",
            "start_up_duration": 0,
        }
    )
    pc_a.power_on()
    network.add_node(pc_a)

    # Configure Router 1
    router_1 = WirelessRouter.from_config(
        config={"type": "wireless-router", "hostname": "router_1", "start_up_duration": 0}, airspace=network.airspace
    )
    router_1.power_on()
    network.add_node(router_1)

    # Configure the connection between PC A and Router 1 port 2
    router_1.configure_router_interface("192.168.0.1", "255.255.255.0")
    network.connect(pc_a.network_interface[1], router_1.network_interface[2])

    # Configure Router 1 ACLs
    router_1.acl.add_rule(
        action=ACLAction.PERMIT, src_port=PORT_LOOKUP["ARP"], dst_port=PORT_LOOKUP["ARP"], position=22
    )
    router_1.acl.add_rule(action=ACLAction.PERMIT, protocol=PROTOCOL_LOOKUP["ICMP"], position=23)

    # Configure PC B
    pc_b: Computer = Computer.from_config(
        config={
            "type": "computer",
            "hostname": "pc_b",
            "ip_address": "192.168.2.2",
            "subnet_mask": "255.255.255.0",
            "default_gateway": "192.168.2.1",
            "start_up_duration": 0,
        }
    )
    pc_b.power_on()
    network.add_node(pc_b)

    # Configure Router 2
    router_2: WirelessRouter = WirelessRouter.from_config(
        config={"type": "wireless-router", "hostname": "router_2", "start_up_duration": 0}, airspace=network.airspace
    )
    router_2.power_on()
    network.add_node(router_2)

    # Configure the connection between PC B and Router 2 port 2
    router_2.configure_router_interface("192.168.2.1", "255.255.255.0")
    network.connect(pc_b.network_interface[1], router_2.network_interface[2])

    # Configure Router 2 ACLs

    # Configure the wireless connection between Router 1 port 1 and Router 2 port 1
    router_1.configure_wireless_access_point("192.168.1.1", "255.255.255.0")
    router_2.configure_wireless_access_point("192.168.1.2", "255.255.255.0")

    network.airspace.show()

    router_1.route_table.add_route(
        address="192.168.2.0", subnet_mask="255.255.255.0", next_hop_ip_address="192.168.1.2"
    )

    # Configure Route from Router 2 to PC A subnet
    router_2.route_table.add_route(
        address="192.168.0.2", subnet_mask="255.255.255.0", next_hop_ip_address="192.168.1.1"
    )

    return pc_a, pc_b, router_1, router_2


@pytest.fixture(scope="function")
def wireless_wan_network_from_config_yaml():
    config_path = TEST_ASSETS_ROOT / "configs" / "wireless_wan_network_config.yaml"

    with open(config_path, "r") as f:
        config_dict = yaml.safe_load(f)
    network = PrimaiteGame.from_config(cfg=config_dict).simulation.network

    network.airspace.show()

    return network


def test_cross_wireless_wan_connectivity(wireless_wan_network):
    pc_a, pc_b, router_1, router_2 = wireless_wan_network
    # Ensure that PCs can ping across routers before any frequency change
    assert pc_a.ping(pc_a.config.default_gateway), "PC A should ping its default gateway successfully."
    assert pc_b.ping(pc_b.config.default_gateway), "PC B should ping its default gateway successfully."

    assert pc_a.ping(pc_b.network_interface[1].ip_address), "PC A should ping PC B across routers successfully."
    assert pc_b.ping(pc_a.network_interface[1].ip_address), "PC B should ping PC A across routers successfully."


def test_cross_wireless_wan_connectivity_from_yaml(wireless_wan_network_from_config_yaml):
    pc_a = wireless_wan_network_from_config_yaml.get_node_by_hostname("pc_a")
    pc_b = wireless_wan_network_from_config_yaml.get_node_by_hostname("pc_b")

    assert pc_a.ping(pc_a.config.default_gateway), "PC A should ping its default gateway successfully."
    assert pc_b.ping(pc_b.config.default_gateway), "PC B should ping its default gateway successfully."

    assert pc_a.ping(pc_b.network_interface[1].ip_address), "PC A should ping PC B across routers successfully."
    assert pc_b.ping(pc_a.network_interface[1].ip_address), "PC B should ping PC A across routers successfully."
