# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

import pytest

from primaite.main import run
from tests import TEST_CONFIG_ROOT


@pytest.skip("Deprecated")  # TODO: implement a similar test for primaite v3
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
    legacy_training_config_path = TEST_CONFIG_ROOT / "legacy_conversion" / "legacy_training_config.yaml"
    legacy_lay_down_config_path = TEST_CONFIG_ROOT / "legacy_conversion" / legacy_file

    # Run a PrimAITE session using legacy training and lay down config file paths
    run(
        legacy_training_config_path,
        legacy_lay_down_config_path,
        legacy_training_config=True,
        legacy_lay_down_config=True,
    )
