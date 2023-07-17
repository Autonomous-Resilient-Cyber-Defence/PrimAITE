# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
import pytest

from primaite import getLogger
from primaite.config.lay_down_config import dos_very_basic_config_path
from tests import TEST_CONFIG_ROOT

_LOGGER = getLogger(__name__)


@pytest.mark.parametrize(
    "temp_primaite_session",
    [[TEST_CONFIG_ROOT / "training_config_main_rllib.yaml", dos_very_basic_config_path()]],
    indirect=True,
)
def test_primaite_session(temp_primaite_session):
    """Test the training_config_main_rllib.yaml training config file."""
    with temp_primaite_session as session:
        session_path = session.session_path
        assert session_path.exists()
        session.learn()

        assert len(session.learn_av_reward_per_episode_dict().keys()) == 10
        assert len(session.learn_all_transactions_dict().keys()) == 10 * 256
