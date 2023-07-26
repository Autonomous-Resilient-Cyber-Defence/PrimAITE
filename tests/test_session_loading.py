# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
import os.path
import shutil
import tempfile
from pathlib import Path
from typing import Union
from uuid import uuid4

from typer.testing import CliRunner

from primaite import getLogger
from primaite.agents.sb3 import SB3Agent
from primaite.cli import app
from primaite.common.enums import AgentFramework, AgentIdentifier
from primaite.main import run
from primaite.primaite_session import PrimaiteSession
from primaite.utils.session_output_reader import av_rewards_dict
from tests import TEST_ASSETS_ROOT

_LOGGER = getLogger(__name__)

runner = CliRunner()

sb3_expected_avg_reward_per_episode = {
    10: 0.0,
    11: -0.0011074218750000008,
    12: -0.0010000000000000007,
    13: -0.0016601562500000013,
    14: -0.001400390625000001,
    15: -0.0009863281250000007,
    16: -0.0011855468750000008,
    17: -0.0009511718750000007,
    18: -0.0008789062500000007,
    19: -0.0012226562500000009,
    20: -0.0010292968750000007,
}

sb3_expected_eval_rewards = -0.0018515625000000014


def copy_session_asset(asset_path: Union[str, Path]) -> str:
    """Copies the asset into a temporary test folder."""
    if asset_path is None:
        raise Exception("No path provided")

    if isinstance(asset_path, Path):
        asset_path = str(os.path.normpath(asset_path))

    copy_path = str(Path(tempfile.gettempdir()) / "primaite" / str(uuid4()))

    # copy the asset into a temp path
    try:
        shutil.copytree(asset_path, copy_path)
    except Exception as e:
        msg = f"Unable to copy directory: {asset_path}"
        _LOGGER.error(msg, e)
        print(msg, e)

    _LOGGER.debug(f"Copied test asset to: {copy_path}")

    # return the copied assets path
    return copy_path


def test_load_sb3_session():
    """Test that loading an SB3 agent works."""
    test_path = copy_session_asset(TEST_ASSETS_ROOT / "example_sb3_agent_session")

    loaded_agent = SB3Agent(session_path=test_path)

    # loaded agent should have the same UUID as the previous agent
    assert loaded_agent.uuid == "301874d3-2e14-43c2-ba7f-e2b03ad05dde"
    assert loaded_agent._training_config.agent_framework == AgentFramework.SB3.name
    assert loaded_agent._training_config.agent_identifier == AgentIdentifier.PPO.name
    assert loaded_agent._training_config.deterministic
    assert loaded_agent._training_config.seed == 12345
    assert str(loaded_agent.session_path) == str(test_path)

    # run another learn session
    loaded_agent.learn()

    learn_mean_rewards = av_rewards_dict(
        loaded_agent.learning_path / f"average_reward_per_episode_{loaded_agent.timestamp_str}.csv"
    )

    # run is seeded so should have the expected learn value
    assert learn_mean_rewards == sb3_expected_avg_reward_per_episode

    # run an evaluation
    loaded_agent.evaluate()

    # load the evaluation average reward csv file
    eval_mean_reward = av_rewards_dict(
        loaded_agent.evaluation_path / f"average_reward_per_episode_{loaded_agent.timestamp_str}.csv"
    )

    # the agent config ran the evaluation in deterministic mode, so should have the same reward value
    assert len(set(eval_mean_reward.values())) == 1

    # the evaluation should be the same as a previous run
    assert next(iter(set(eval_mean_reward.values()))) == sb3_expected_eval_rewards

    # delete the test directory
    shutil.rmtree(test_path)


def test_load_primaite_session():
    """Test that loading a Primaite session works."""
    test_path = copy_session_asset(TEST_ASSETS_ROOT / "example_sb3_agent_session")

    # create loaded session
    session = PrimaiteSession(session_path=test_path)

    # run setup on session
    session.setup()

    # make sure that the session was loaded correctly
    assert session._agent_session.uuid == "301874d3-2e14-43c2-ba7f-e2b03ad05dde"
    assert session._agent_session._training_config.agent_framework == AgentFramework.SB3.name
    assert session._agent_session._training_config.agent_identifier == AgentIdentifier.PPO.name
    assert session._agent_session._training_config.deterministic
    assert session._agent_session._training_config.seed == 12345
    assert str(session._agent_session.session_path) == str(test_path)

    # run another learn session
    session.learn()

    learn_mean_rewards = av_rewards_dict(
        session.learning_path / f"average_reward_per_episode_{session.timestamp_str}.csv"
    )

    # run is seeded so should have the expected learn value
    assert learn_mean_rewards == sb3_expected_avg_reward_per_episode

    # run an evaluation
    session.evaluate()

    # load the evaluation average reward csv file
    eval_mean_reward = av_rewards_dict(
        session.evaluation_path / f"average_reward_per_episode_{session.timestamp_str}.csv"
    )

    # the agent config ran the evaluation in deterministic mode, so should have the same reward value
    assert len(set(eval_mean_reward.values())) == 1

    # the evaluation should be the same as a previous run
    assert next(iter(set(eval_mean_reward.values()))) == sb3_expected_eval_rewards

    # delete the test directory
    shutil.rmtree(test_path)


def test_run_loading():
    """Test loading session via main.run."""
    test_path = copy_session_asset(TEST_ASSETS_ROOT / "example_sb3_agent_session")

    # create loaded session
    run(session_path=test_path)

    learn_mean_rewards = av_rewards_dict(
        next(Path(test_path).rglob("**/learning/average_reward_per_episode_*.csv"), None)
    )

    # run is seeded so should have the expected learn value
    assert learn_mean_rewards == sb3_expected_avg_reward_per_episode

    # delete the test directory
    shutil.rmtree(test_path)


def test_cli():
    """Test loading session via CLI."""
    test_path = copy_session_asset(TEST_ASSETS_ROOT / "example_sb3_agent_session")
    result = runner.invoke(app, ["session", "--load", test_path])

    # cli should work
    assert result.exit_code == 0

    learn_mean_rewards = av_rewards_dict(
        next(Path(test_path).rglob("**/learning/average_reward_per_episode_*.csv"), None)
    )

    # run is seeded so should have the expected learn value
    assert learn_mean_rewards == sb3_expected_avg_reward_per_episode

    # delete the test directory
    shutil.rmtree(test_path)
