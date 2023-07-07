import pytest

from primaite import getLogger
from primaite.config.lay_down_config import dos_very_basic_config_path
from tests import TEST_CONFIG_ROOT
from tests.conftest import run_generic

_LOGGER = getLogger(__name__)


@pytest.mark.parametrize(
    "temp_primaite_session",
    [[TEST_CONFIG_ROOT / "train_episode_step.yaml", dos_very_basic_config_path()]],
    indirect=True,
)
def test_eval_steps_differ_from_training(temp_primaite_session):
    """Uses PrimaiteSession class to compare number of episodes used for training and evaluation."""
    with temp_primaite_session as train_session:
        env = train_session.env
        train_session.learn()

    """
    Train_episode_step.yaml main config:
    num_train_steps = 1
    num_eval_steps = 10

    When the YAML file changes from TRAIN to EVAL the episode step changes and uses the other config value.

    The test is showing that 10 steps are running for evaluation and NOT 1 step as EVAL has been selected in the config.
    """
    assert env.episode_steps == 10  # 30
    # assert env.actual_episode_count == 10 # should be 10


@pytest.mark.parametrize(
    "temp_primaite_session",
    [[TEST_CONFIG_ROOT / "train_episode_step.yaml", dos_very_basic_config_path()]],
    indirect=True,
)
def test_train_eval_config_option(temp_primaite_session):
    """Uses PrimaiteSession class to test number of episodes and steps used for TRAIN and EVAL option."""
    with temp_primaite_session as train_session:
        env = train_session.env
        run_generic(env, env.training_config)

    print(env.actual_episode_count, env.step_count, env.total_step_count)
