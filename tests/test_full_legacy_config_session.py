# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
import tempfile
from pathlib import Path

import pytest
import yaml

from primaite.config import training_config
from primaite.config.lay_down_config import convert_legacy_lay_down_config
from primaite.main import run
from tests import TEST_CONFIG_ROOT


@pytest.mark.parametrize(
    "legacy_file",
    [
        ("legacy_config_1_DDOS_BASIC.yaml"),
        ("legacy_config_2_DDOS_BASIC.yaml"),
        ("legacy_config_3_DOS_VERY_BASIC.yaml"),
        ("legacy_config_5_DATA_MANIPULATION.yaml"),
    ],
)
def test_legacy_training_config_run_session(legacy_file):
    """Tests using legacy training and lay down config files in PrimAITE session end-to-end."""
    # Load the legacy lay down config yaml file
    with open(TEST_CONFIG_ROOT / "legacy_conversion" / legacy_file, "r") as file:
        legacy_lay_down_config = yaml.safe_load(file)

    # Convert the legacy lay down config to the new format
    converted_lay_down_config = convert_legacy_lay_down_config(legacy_lay_down_config)

    # Write the converted lay down config file to yaml file
    temp_dir = Path(tempfile.gettempdir())
    converted_legacy_lay_down_path = temp_dir / legacy_file.replace("legacy_", "")
    with open(converted_legacy_lay_down_path, "w") as file:
        yaml.dump(converted_lay_down_config, file)

    # Load the legacy training config yaml file and covvert it to the new format
    converted_legacy_training_config = training_config.load(
        TEST_CONFIG_ROOT / "legacy_conversion" / "legacy_training_config.yaml", legacy_file=True
    )

    # Write the converted training config file to yaml file
    converted_legacy_training_path = temp_dir / "training_config.yaml"
    with open(converted_legacy_training_path, "w") as file:
        yaml.dump(converted_legacy_training_config.to_dict(json_serializable=True), file)

    # Run a PrimAITE session using the paths of both the converted training and lay down config files
    run(converted_legacy_training_path, converted_legacy_lay_down_path)
