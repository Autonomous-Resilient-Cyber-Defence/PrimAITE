import pytest

from tests import TEST_CONFIG_ROOT


@pytest.mark.parametrize(
    "temp_primaite_session",
    [
        [
            TEST_CONFIG_ROOT / "one_node_states_on_off_main_config.yaml",
            TEST_CONFIG_ROOT / "one_node_states_on_off_lay_down_config.yaml",
        ]
    ],
    indirect=True,
)
def test_rewards_are_being_penalised_at_each_step_function(
    temp_primaite_session,
):
    """
    Test that hardware state is penalised at each step.

    When the initial state is OFF compared to reference state which is ON.

    On different steps (of the 13 in total) these are the following rewards
    for config_6 which are activated:
        File System State: goodShouldBeCorrupt = 5 (between Steps 1 & 3)
        Hardware State: onShouldBeOff = -2 (between Steps 4 & 6)
        Service State: goodShouldBeCompromised = 5 (between Steps 7 & 9)
        Software State (Software State): goodShouldBeCompromised = 5 (between
        Steps 10 & 12)

    Total Reward: -2 - 2 + 5 + 5 + 5 + 5 + 5 + 5 = 26
    Step Count: 13

    For the 4 steps where this occurs the average reward is:
        Average Reward: 2 (26 / 13)
    """
    with temp_primaite_session as session:
        session.evaluate()
        session.close()
        ev_rewards = session.eval_av_reward_per_episode_csv()
        assert ev_rewards[1] == -8.0
