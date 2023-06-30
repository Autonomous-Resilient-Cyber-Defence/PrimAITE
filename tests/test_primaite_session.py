import os

import pytest

from primaite import getLogger
from primaite.config.lay_down_config import dos_very_basic_config_path
from primaite.config.training_config import main_training_config_path

_LOGGER = getLogger(__name__)


@pytest.mark.parametrize(
    "temp_primaite_session",
    [[main_training_config_path(), dos_very_basic_config_path()]],
    indirect=True,
)
def test_primaite_session(temp_primaite_session):
    """Tests the PrimaiteSession class and its outputs."""
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

        # Check that both the transactions and av reward csv files exist
        for file in session.learning_path.iterdir():
            if file.suffix == ".csv":
                assert (
                    "all_transactions" in file.name
                    or "average_reward_per_episode" in file.name
                )

        # Check that both the transactions and av reward csv files exist
        for file in session.evaluation_path.iterdir():
            if file.suffix == ".csv":
                assert (
                    "all_transactions" in file.name
                    or "average_reward_per_episode" in file.name
                )

        _LOGGER.debug("Inspecting files in temp session path...")
        for dir_path, dir_names, file_names in os.walk(session_path):
            for file in file_names:
                path = os.path.join(dir_path, file)
                file_str = path.split(str(session_path))[-1]
                _LOGGER.debug(f"  {file_str}")

    # Now that we've exited the context manager, the session.session_path
    # directory and its contents are deleted
    assert not session_path.exists()
