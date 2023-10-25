# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
import pytest
import yaml

# from primaite.config.lay_down_config import (
#     convert_legacy_lay_down_config,
#     data_manipulation_config_path,
#     ddos_basic_one_config_path,
#     ddos_basic_two_config_path,
#     dos_very_basic_config_path,
# )
from tests import TEST_CONFIG_ROOT


@pytest.skip("Deprecated")  # TODO: implement a similar test for primaite v3
@pytest.mark.parametrize(
    "legacy_file, new_path",
    [
        ("legacy_config_1_DDOS_BASIC.yaml", ddos_basic_one_config_path()),
        ("legacy_config_2_DDOS_BASIC.yaml", ddos_basic_two_config_path()),
        ("legacy_config_3_DOS_VERY_BASIC.yaml", dos_very_basic_config_path()),
        ("legacy_config_5_DATA_MANIPULATION.yaml", data_manipulation_config_path()),
    ],
)
def test_legacy_lay_down_config_load(legacy_file, new_path):
    """Tests converting legacy lay down files into the new format."""
    with open(TEST_CONFIG_ROOT / "legacy_conversion" / legacy_file, "r") as file:
        legacy_lay_down_config = yaml.safe_load(file)

    with open(new_path, "r") as file:
        new_lay_down_config = yaml.safe_load(file)

    converted_lay_down_config = convert_legacy_lay_down_config(legacy_lay_down_config)

    assert len(converted_lay_down_config) == len(new_lay_down_config)

    for i, new_item in enumerate(new_lay_down_config):
        converted_item = converted_lay_down_config[i]

        for key, val in new_item.items():
            if key == "position":
                continue
            assert key in converted_item

            assert val == converted_item[key]
