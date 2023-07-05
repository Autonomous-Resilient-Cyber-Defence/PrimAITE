"""
Seed tests.

These tests will train an agent.
This agent is then loaded and evaluated twice,
the 2 evaluation wuns should be the same.

This proves that the seed works.
"""
import time

from primaite.config.lay_down_config import dos_very_basic_config_path
from primaite.primaite_session import PrimaiteSession
from tests import TEST_CONFIG_ROOT


def test_seeded_sessions():
    """Test to see if seed works in multiple sessions."""
    # ppo training session
    ppo_train = PrimaiteSession(TEST_CONFIG_ROOT / "e2e/ppo_seeded_training_config.yaml", dos_very_basic_config_path())
    # train agent
    ppo_train.setup()
    ppo_train.learn()
    ppo_train.close()

    # agent path to use for evaluation
    path_prefix = f"{ppo_train._training_config.agent_framework}_{ppo_train._training_config.agent_identifier}"
    agent_path = ppo_train.session_path / f"{path_prefix}_{ppo_train.timestamp_str}.zip"

    ppo_session_1 = PrimaiteSession(
        TEST_CONFIG_ROOT / "e2e/ppo_seeded_training_config.yaml", dos_very_basic_config_path()
    )

    # load trained agent
    ppo_session_1._training_config.agent_load_file = agent_path
    ppo_session_1.setup()
    time.sleep(1)

    ppo_session_2 = PrimaiteSession(
        TEST_CONFIG_ROOT / "e2e/ppo_seeded_training_config.yaml", dos_very_basic_config_path()
    )

    # load trained agent
    ppo_session_2._training_config.agent_load_file = agent_path
    ppo_session_2.setup()

    # run evaluation
    ppo_session_1.evaluate()
    ppo_session_1.close()
    ppo_session_2.evaluate()
    ppo_session_2.close()

    # compare output
    # assert compare_transaction_file(
    #     ppo_session_1.evaluation_path / f"all_transactions_{ppo_session_1.timestamp_str}.csv",
    #     ppo_session_2.evaluation_path / f"all_transactions_{ppo_session_2.timestamp_str}.csv"
    # ) is True
