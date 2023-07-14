import pytest as pytest

from primaite.config.lay_down_config import dos_very_basic_config_path
from tests import TEST_CONFIG_ROOT


@pytest.mark.parametrize(
    "temp_primaite_session",
    [[TEST_CONFIG_ROOT / "ppo_seeded_training_config.yaml", dos_very_basic_config_path()]],
    indirect=True,
)
def test_seeded_learning(temp_primaite_session):
    """
    Test running seeded learning produces the same output when ran twice.

    .. note::

        If this is failing, the hard-coded expected_mean_reward_per_episode
        from a pre-trained agent will probably need to be updated. If the
        env changes and those changed how this agent is trained, chances are
        the mean rewards are going to be different.

        Run the test, but print out the session.learn_av_reward_per_episode()
        before comparing it. Then copy the printed dict and replace the
        expected_mean_reward_per_episode with those values. The test should
        now work. If not, then you've got a bug :).
    """
    expected_mean_reward_per_episode = {
        1: -33.90625,
        2: -32.32421875,
        3: -25.234375,
        4: -30.15625,
        5: -27.1484375,
        6: -29.609375,
        7: -29.921875,
        8: -29.3359375,
        9: -28.046875,
        10: -27.24609375,
    }

    with temp_primaite_session as session:
        assert (
            session._training_config.seed == 67890
        ), "Expected output is based upon a agent that was trained with seed 67890"
        session.learn()

        assert expected_mean_reward_per_episode == session.learn_av_reward_per_episode()


@pytest.mark.skip(reason="Inconsistent results. Needs someone with RL knowledge to investigate further.")
@pytest.mark.parametrize(
    "temp_primaite_session",
    [[TEST_CONFIG_ROOT / "ppo_seeded_training_config.yaml", dos_very_basic_config_path()]],
    indirect=True,
)
def test_deterministic_evaluation(temp_primaite_session):
    """Test running deterministic evaluation gives same av eward per episode."""
    with temp_primaite_session as session:
        # do stuff
        session.learn()
        session.evaluate()
        eval_mean_reward = session.eval_av_reward_per_episode_csv()
        assert len(set(eval_mean_reward.values())) == 1
