from tests import TEST_CONFIG_ROOT
from tests.conftest import _get_primaite_env_from_config


def test_rewards_are_being_penalised_at_each_step_function():
    """
    Test that hardware state is penalised at each step.

    When the initial state is OFF compared to reference state which is ON.
    """
    env, config_values = _get_primaite_env_from_config(
        main_config_path=TEST_CONFIG_ROOT / "one_node_states_on_off_main_config.yaml",
        lay_down_config_path=TEST_CONFIG_ROOT
        / "one_node_states_on_off_lay_down_config.yaml",
    )

    """
    On different steps (of the 13 in total) these are the following rewards for config_6 which are activated:
        File System State: goodShouldBeCorrupt = 5 (between Steps 1 & 3)
        Hardware State: onShouldBeOff = -2 (between Steps 4 & 6)
        Service State: goodShouldBeCompromised = 5 (between Steps 7 & 9)
        Software State (Software State): goodShouldBeCompromised = 5 (between Steps 10 & 12)

    Total Reward: -2 - 2 + 5 + 5 + 5 + 5 + 5 + 5 = 26
    Step Count: 13

    For the 4 steps where this occurs the average reward is:
        Average Reward: 2 (26 / 13)
    """
    print("average reward", env.average_reward)
    assert env.average_reward == -8.0
