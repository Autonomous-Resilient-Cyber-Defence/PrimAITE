# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
import os

import pytest

from primaite import getLogger

# from primaite.config.lay_down_config import dos_very_basic_config_path
from tests import TEST_CONFIG_ROOT

_LOGGER = getLogger(__name__)


@pytest.skip("Deprecated")  # TODO: implement a similar test for primaite v3
@pytest.mark.parametrize(
    "temp_primaite_session",
    [
        # [TEST_CONFIG_ROOT / "session_test/training_config_main_rllib.yaml", dos_very_basic_config_path()],
        [TEST_CONFIG_ROOT / "session_test/training_config_main_sb3.yaml", dos_very_basic_config_path()],
    ],
    indirect=True,
)
def test_primaite_session(temp_primaite_session):
    """
    Tests the PrimaiteSession class and all of its outputs.

    This test runs for both a Stable Baselines3 agent, and a Ray RLlib agent.
    """
    with temp_primaite_session as session:
        session_path = session.session_path
        assert session_path.exists()
        session.learn()
        # Learning outputs are saved in session.learning_path
        session.evaluate()
        # Evaluation outputs are saved in session.evaluation_path

        # If you need to inspect any session outputs, it must be done inside
        # the context manager

        # Check that the metadata json file exists
        assert (session_path / "session_metadata.json").exists()

        # Check that the network png file exists
        assert (session_path / f"network_{session.timestamp_str}.png").exists()

        # Check that the saved agent exists
        assert session._agent_session._saved_agent_path.exists()

        # Check that both the transactions and av reward csv files exist
        for file in session.learning_path.iterdir():
            if file.suffix == ".csv":
                assert "all_transactions" in file.name or "average_reward_per_episode" in file.name

        # Check that both the transactions and av reward csv files exist
        for file in session.evaluation_path.iterdir():
            if file.suffix == ".csv":
                assert "all_transactions" in file.name or "average_reward_per_episode" in file.name

        # Check that the average reward per episode plots exist
        assert (session.learning_path / f"average_reward_per_episode_{session.timestamp_str}.png").exists()
        assert (session.evaluation_path / f"average_reward_per_episode_{session.timestamp_str}.png").exists()

        # Check that the metadata has captured the correct number of learning and eval episodes and steps
        assert len(session.learn_av_reward_per_episode_dict().keys()) == 10
        assert len(session.learn_all_transactions_dict().keys()) == 10 * 256

        assert len(session.eval_av_reward_per_episode_dict().keys()) == 3
        assert len(session.eval_all_transactions_dict().keys()) == 3 * 256

        _LOGGER.debug("Inspecting files in temp session path...")
        for dir_path, dir_names, file_names in os.walk(session_path):
            for file in file_names:
                path = os.path.join(dir_path, file)
                file_str = path.split(str(session_path))[-1]
                _LOGGER.debug(f"  {file_str}")

    # Now that we've exited the context manager, the session.session_path
    # directory and its contents are deleted
    assert not session_path.exists()
