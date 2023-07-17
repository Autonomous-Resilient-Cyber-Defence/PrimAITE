# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
import pytest

from primaite import getLogger
from primaite.config.lay_down_config import dos_very_basic_config_path
from tests import TEST_CONFIG_ROOT

_LOGGER = getLogger(__name__)


@pytest.mark.parametrize(
    "temp_primaite_session",
    [[TEST_CONFIG_ROOT / "train_episode_step.yaml", dos_very_basic_config_path()]],
    indirect=True,
)
def test_eval_steps_differ_from_training(temp_primaite_session):
    """Uses PrimaiteSession class to compare number of episodes used for training and evaluation.

    Train_episode_step.yaml main config:
        num_train_steps = 25
        num_train_episodes = 3
        num_eval_steps = 17
        num_eval_episodes = 1
    """
    expected_learning_metadata = {"total_episodes": 3, "total_time_steps": 75}
    expected_evaluation_metadata = {"total_episodes": 1, "total_time_steps": 17}

    with temp_primaite_session as session:
        # Run learning and check episode and step counts
        session.learn()
        assert session.env.actual_episode_count == expected_learning_metadata["total_episodes"]
        assert session.env.total_step_count == expected_learning_metadata["total_time_steps"]

        # Run evaluation and check episode and step counts
        session.evaluate()
        assert session.env.actual_episode_count == expected_evaluation_metadata["total_episodes"]
        assert session.env.total_step_count == expected_evaluation_metadata["total_time_steps"]

        # Load the session_metadata.json file and check that the both the
        # learning and evaluation match what is expected above
        metadata = session.metadata_file_as_dict()
        assert metadata["learning"] == expected_learning_metadata
        assert metadata["evaluation"] == expected_evaluation_metadata
