"""Test env creation and behaviour with different observation spaces."""

from tests import TEST_CONFIG_ROOT
from tests.conftest import _get_primaite_env_from_config


def test_creating_env_with_box_obs():
    """Try creating env with box observation space."""
    env = _get_primaite_env_from_config(
        main_config_path=TEST_CONFIG_ROOT / "one_node_states_on_off_main_config.yaml",
        lay_down_config_path=TEST_CONFIG_ROOT / "box_obs_space_laydown_config.yaml",
    )
    env.update_environent_obs()


def test_creating_env_with_multidiscrete_obs():
    """Try creating env with MultiDiscrete observation space."""
    env = _get_primaite_env_from_config(
        main_config_path=TEST_CONFIG_ROOT / "one_node_states_on_off_main_config.yaml",
        lay_down_config_path=TEST_CONFIG_ROOT
        / "multidiscrete_obs_space_laydown_config.yaml",
    )
    env.update_environent_obs()
