import os.path
import shutil
import tempfile
from pathlib import Path
from typing import Union
from uuid import uuid4

from primaite import getLogger
from primaite.agents.sb3 import SB3Agent
from primaite.common.enums import AgentFramework, AgentIdentifier
from primaite.utils.session_output_reader import av_rewards_dict
from tests import TEST_ASSETS_ROOT

_LOGGER = getLogger(__name__)


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
    assert loaded_agent.uuid == "8c196c83-b77d-4ef7-af4b-0a3ada30221c"
    assert loaded_agent._training_config.agent_framework == AgentFramework.SB3.name
    assert loaded_agent._training_config.agent_identifier == AgentIdentifier.PPO.name
    assert loaded_agent._training_config.deterministic
    assert str(loaded_agent.session_path) == str(test_path)

    # run an evaluation
    loaded_agent.evaluate()

    # load the evaluation average reward csv file
    eval_mean_reward = av_rewards_dict(
        loaded_agent.evaluation_path / f"average_reward_per_episode_{loaded_agent.timestamp_str}.csv"
    )

    # the agent config ran the evaluation in deterministic mode, so should have the same reward value
    assert len(set(eval_mean_reward.values())) == 1

    # the evaluation should be the same as a previous run
    assert next(iter(set(eval_mean_reward.values()))) == -0.009857999999999992

    # delete the test directory
    shutil.rmtree(test_path)


def test_load_rllib_session():
    """Test that loading an RLlib agent works."""
    # test_path = copy_session_asset(TEST_ASSETS_ROOT)
    #
    # loaded_agent = RLlibAgent(session_path=test_path)
    #
    # # loaded agent should have the same UUID as the previous agent
    # assert loaded_agent.uuid == "58c7e648-c784-44e8-bec0-a1db95898270"
    # assert loaded_agent._training_config.agent_framework == AgentFramework.SB3.name
    # assert loaded_agent._training_config.agent_identifier == AgentIdentifier.PPO.name
    # assert loaded_agent._training_config.deterministic
    # assert str(loaded_agent.session_path) == str(test_path)
    #
    # # run an evaluation
    # loaded_agent.evaluate()
    #
    # # load the evaluation average reward csv file
    # eval_mean_reward = av_rewards_dict(
    #     loaded_agent.evaluation_path / f"average_reward_per_episode_{loaded_agent.timestamp_str}.csv"
    # )
    #
    # # the agent config ran the evaluation in deterministic mode, so should have the same reward value
    # assert len(set(eval_mean_reward.values())) == 1
    #
    # # the evaluation should be the same as a previous run
    # assert next(iter(set(eval_mean_reward.values()))) == -0.00011132812500000003
    #
    # # delete the test directory
    # shutil.rmtree(test_path)
