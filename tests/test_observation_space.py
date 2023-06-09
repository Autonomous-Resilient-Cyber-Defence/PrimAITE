"""Test env creation and behaviour with different observation spaces."""

from tests import TEST_CONFIG_ROOT
from tests.conftest import _get_primaite_env_from_config


def test_creating_env_with_box_obs():
    """Try creating env with box observation space."""
    env, config_values = _get_primaite_env_from_config(
        main_config_path=TEST_CONFIG_ROOT / "one_node_states_on_off_main_config.yaml",
        lay_down_config_path=TEST_CONFIG_ROOT / "box_obs_space_laydown_config.yaml",
    )
    env.update_environent_obs()

    # we have three nodes and two links, with one service
    # therefore the box observation space will have:
    #   * 5 columns (four fixed and one for the service)
    #   * 5 rows (3 nodes + 2 links)
    assert env.env_obs.shape == (5, 5)


def test_creating_env_with_multidiscrete_obs():
    """Try creating env with MultiDiscrete observation space."""
    env, config_values = _get_primaite_env_from_config(
        main_config_path=TEST_CONFIG_ROOT / "one_node_states_on_off_main_config.yaml",
        lay_down_config_path=TEST_CONFIG_ROOT
        / "multidiscrete_obs_space_laydown_config.yaml",
    )
    env.update_environent_obs()

    # we have three nodes and two links, with one service
    # the nodes have hardware, OS, FS, and service, the links just have bandwidth,
    # therefore we need 3*4 + 2 observations
    assert env.env_obs.shape == (3 * 4 + 2,)
