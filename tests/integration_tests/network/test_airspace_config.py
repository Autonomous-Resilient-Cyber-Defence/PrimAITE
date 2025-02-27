# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
import yaml

from primaite.game.game import PrimaiteGame
from primaite.simulator.network.hardware.nodes.network.wireless_router import WirelessRouter
from tests import TEST_ASSETS_ROOT


def test_override_freq_max_capacity_mbps():
    config_path = TEST_ASSETS_ROOT / "configs" / "wireless_wan_network_config_freq_max_override.yaml"

    with open(config_path, "r") as f:
        config_dict = yaml.safe_load(f)
    network = PrimaiteGame.from_config(cfg=config_dict).simulation.network

    assert network.airspace.get_frequency_max_capacity_mbps("WIFI_2_4") == 123.45
    assert network.airspace.get_frequency_max_capacity_mbps("WIFI_5") == 0.0

    pc_a = network.get_node_by_hostname("pc_a")
    pc_b = network.get_node_by_hostname("pc_b")

    assert pc_a.ping(pc_b.network_interface[1].ip_address), "PC A should be able to ping PC B"
    assert pc_b.ping(pc_a.network_interface[1].ip_address), "PC B should be able to ping PC A"

    network.airspace.show()


def test_override_freq_max_capacity_mbps_blocked():
    config_path = TEST_ASSETS_ROOT / "configs" / "wireless_wan_network_config_freq_max_override_blocked.yaml"

    with open(config_path, "r") as f:
        config_dict = yaml.safe_load(f)
    network = PrimaiteGame.from_config(cfg=config_dict).simulation.network

    assert network.airspace.get_frequency_max_capacity_mbps("WIFI_2_4") == 0.0
    assert network.airspace.get_frequency_max_capacity_mbps("WIFI_5") == 0.0

    pc_a = network.get_node_by_hostname("pc_a")
    pc_b = network.get_node_by_hostname("pc_b")

    assert not pc_a.ping(pc_b.network_interface[1].ip_address), "PC A should not be able to ping PC B"
    assert not pc_b.ping(pc_a.network_interface[1].ip_address), "PC B should not be able to ping PC A"

    network.airspace.show()
