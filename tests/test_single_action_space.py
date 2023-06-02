from tests import TEST_CONFIG_ROOT
from tests.conftest import _get_primaite_env_from_config


def test_single_action_space():
    """Test to ensure the blue agent is using the ACL action space and is carrying out both kinds of operations."""
    env = _get_primaite_env_from_config(
        main_config_path=TEST_CONFIG_ROOT / "single_action_space_main_config.yaml",
        lay_down_config_path=TEST_CONFIG_ROOT
        / "single_action_space_lay_down_config.yaml",
    )
    """
    nv.action_space.n is the total number of actions in the Discrete action space
    This is the number of actions the agent has to choose from.

    The total number of actions that an agent can type when a NODE action type is selected is: 6
    The total number of actions that an agent can take when an ACL action type is selected is: 7

    These action spaces are combined and the total number of actions is: 12
    This is due to both actions containing the action to "Do nothing", so it needs to be removed from one of the spaces,
    to avoid duplicate actions.

    As a result, 12 is the total number of action spaces.
    """
    # e
    assert env.action_space.n == 12
