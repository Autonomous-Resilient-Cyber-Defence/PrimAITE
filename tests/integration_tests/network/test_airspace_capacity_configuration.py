# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
import yaml

from primaite.game.game import PrimaiteGame
from primaite.simulator.network.airspace import (
    AirspaceEnvironmentType,
    AirSpaceFrequency,
    calculate_total_channel_capacity,
    ChannelWidth,
)
from primaite.simulator.network.hardware.nodes.network.wireless_router import WirelessRouter
from tests import TEST_ASSETS_ROOT


def test_wireless_wan_wifi_5_80_channel_width_urban():
    config_path = TEST_ASSETS_ROOT / "configs" / "wireless_wan_wifi_5_80_channel_width_urban.yaml"

    with open(config_path, "r") as f:
        config_dict = yaml.safe_load(f)
    network = PrimaiteGame.from_config(cfg=config_dict).simulation.network

    airspace = network.airspace

    assert airspace.airspace_environment_type == AirspaceEnvironmentType.URBAN

    router_1: WirelessRouter = network.get_node_by_hostname("router_1")
    router_2: WirelessRouter = network.get_node_by_hostname("router_2")

    expected_speed = calculate_total_channel_capacity(
        channel_width=ChannelWidth.WIDTH_80_MHZ,
        frequency=AirSpaceFrequency.WIFI_5,
        environment_type=AirspaceEnvironmentType.URBAN,
    )

    assert router_1.wireless_access_point.speed == expected_speed
    assert router_2.wireless_access_point.speed == expected_speed

    pc_a = network.get_node_by_hostname("pc_a")
    pc_b = network.get_node_by_hostname("pc_b")

    assert pc_a.ping(pc_a.default_gateway), "PC A should ping its default gateway successfully."
    assert pc_b.ping(pc_b.default_gateway), "PC B should ping its default gateway successfully."

    assert pc_a.ping(pc_b.network_interface[1].ip_address), "PC A should ping PC B across routers successfully."
    assert pc_b.ping(pc_a.network_interface[1].ip_address), "PC B should ping PC A across routers successfully."


def test_wireless_wan_wifi_5_80_channel_width_blocked():
    config_path = TEST_ASSETS_ROOT / "configs" / "wireless_wan_wifi_5_80_channel_width_blocked.yaml"

    with open(config_path, "r") as f:
        config_dict = yaml.safe_load(f)
    network = PrimaiteGame.from_config(cfg=config_dict).simulation.network

    airspace = network.airspace

    assert airspace.airspace_environment_type == AirspaceEnvironmentType.BLOCKED

    router_1: WirelessRouter = network.get_node_by_hostname("router_1")
    router_2: WirelessRouter = network.get_node_by_hostname("router_2")

    expected_speed = calculate_total_channel_capacity(
        channel_width=ChannelWidth.WIDTH_80_MHZ,
        frequency=AirSpaceFrequency.WIFI_5,
        environment_type=AirspaceEnvironmentType.BLOCKED,
    )

    assert router_1.wireless_access_point.speed == expected_speed
    assert router_2.wireless_access_point.speed == expected_speed

    pc_a = network.get_node_by_hostname("pc_a")
    pc_b = network.get_node_by_hostname("pc_b")

    assert pc_a.ping(pc_a.default_gateway), "PC A should ping its default gateway successfully."
    assert pc_b.ping(pc_b.default_gateway), "PC B should ping its default gateway successfully."

    assert not pc_a.ping(pc_b.network_interface[1].ip_address), "PC A should ping PC B across routers unsuccessfully."
    assert not pc_b.ping(pc_a.network_interface[1].ip_address), "PC B should ping PC A across routers unsuccessfully."


def test_wireless_wan_blocking_and_unblocking_airspace():
    config_path = TEST_ASSETS_ROOT / "configs" / "wireless_wan_wifi_5_80_channel_width_urban.yaml"

    with open(config_path, "r") as f:
        config_dict = yaml.safe_load(f)
    network = PrimaiteGame.from_config(cfg=config_dict).simulation.network

    airspace = network.airspace

    assert airspace.airspace_environment_type == AirspaceEnvironmentType.URBAN

    pc_a = network.get_node_by_hostname("pc_a")
    pc_b = network.get_node_by_hostname("pc_b")

    assert pc_a.ping(pc_b.network_interface[1].ip_address), "PC A should ping PC B across routers successfully."
    assert pc_b.ping(pc_a.network_interface[1].ip_address), "PC B should ping PC A across routers successfully."

    airspace.airspace_environment_type = AirspaceEnvironmentType.BLOCKED

    assert not pc_a.ping(pc_b.network_interface[1].ip_address), "PC A should ping PC B across routers unsuccessfully."
    assert not pc_b.ping(pc_a.network_interface[1].ip_address), "PC B should ping PC A across routers unsuccessfully."

    airspace.airspace_environment_type = AirspaceEnvironmentType.URBAN

    assert pc_a.ping(pc_b.network_interface[1].ip_address), "PC A should ping PC B across routers successfully."
    assert pc_b.ping(pc_a.network_interface[1].ip_address), "PC B should ping PC A across routers successfully."
