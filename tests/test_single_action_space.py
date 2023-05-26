from tests import TEST_CONFIG_ROOT
from tests.conftest import _get_primaite_env_from_config


def test_single_action_space():
    """Test to ensure the blue agent is using the ACL action space and is carrying out both kinds of operations."""
    env = _get_primaite_env_from_config(
        main_config_path=TEST_CONFIG_ROOT / "one_node_states_on_off_main_config.yaml",
        lay_down_config_path=TEST_CONFIG_ROOT
        / "one_node_states_on_off_lay_down_config.yaml",
    )
    print("Average Reward:", env.average_reward)
