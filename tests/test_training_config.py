# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
import yaml

from primaite.config import training_config
from tests import TEST_CONFIG_ROOT


def test_legacy_lay_down_config_yaml_conversion():
    """Tests the conversion of legacy lay down config files."""
    legacy_path = TEST_CONFIG_ROOT / "legacy" / "legacy_training_config.yaml"
    new_path = TEST_CONFIG_ROOT / "legacy" / "new_training_config.yaml"

    with open(legacy_path, "r") as file:
        legacy_dict = yaml.safe_load(file)

    with open(new_path, "r") as file:
        new_dict = yaml.safe_load(file)

    converted_dict = training_config.convert_legacy_training_config_dict(legacy_dict)

    for key, value in new_dict.items():
        assert converted_dict[key] == value


def test_create_config_values_main_from_file():
    """Tests creating an instance of TrainingConfig from file."""
    new_path = TEST_CONFIG_ROOT / "legacy" / "new_training_config.yaml"

    training_config.load(new_path)


def test_create_config_values_main_from_legacy_file():
    """Tests creating an instance of TrainingConfig from legacy file."""
    new_path = TEST_CONFIG_ROOT / "legacy" / "legacy_training_config.yaml"

    training_config.load(new_path, legacy_file=True)
