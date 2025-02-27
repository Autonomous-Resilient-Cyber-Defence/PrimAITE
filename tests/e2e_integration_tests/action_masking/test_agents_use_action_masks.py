# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from typing import Dict

import pytest
import yaml
from ray.rllib.algorithms.ppo import PPOConfig
from ray.rllib.core.rl_module.marl_module import MultiAgentRLModuleSpec
from ray.rllib.core.rl_module.rl_module import SingleAgentRLModuleSpec
from ray.rllib.examples.rl_modules.classes.action_masking_rlm import ActionMaskingTorchRLModule
from sb3_contrib import MaskablePPO

from primaite.game.game import PrimaiteGame
from primaite.session.environment import PrimaiteGymEnv
from primaite.session.ray_envs import PrimaiteRayEnv, PrimaiteRayMARLEnv
from primaite.simulator.network.hardware.nodes.network.wireless_router import WirelessRouter
from tests import TEST_ASSETS_ROOT

CFG_PATH = TEST_ASSETS_ROOT / "configs/test_primaite_session.yaml"
MARL_PATH = TEST_ASSETS_ROOT / "configs/multi_agent_session.yaml"


def test_sb3_action_masking(monkeypatch):
    # There's no simple way of capturing what the action mask was at every step, therefore we are mocking the action
    # mask function here to save the output of the action mask method and pass through the result back to the agent.
    old_action_mask_method = PrimaiteGame.action_mask
    mask_history = []

    def cache_action_mask(obj, agent_name):
        mask = old_action_mask_method(obj, agent_name)
        mask_history.append(mask)
        return mask

    # Even though it's easy to know which CAOS action the agent took by looking at agent history, we don't know which
    # action map action integer that was, therefore we cache it by using monkeypatch
    action_num_history = []

    def cache_step(env, action: int):
        action_num_history.append(action)
        return PrimaiteGymEnv.step(env, action)

    monkeypatch.setattr(PrimaiteGame, "action_mask", cache_action_mask)
    env = PrimaiteGymEnv(CFG_PATH)
    monkeypatch.setattr(env, "step", lambda action: cache_step(env, action))

    model = MaskablePPO("MlpPolicy", env, gamma=0.4, seed=32, batch_size=32)
    model.learn(256)

    assert len(action_num_history) == len(mask_history) > 0
    # Make sure the masks had at least some False entries, if it was all True then the mask was disabled
    assert any([not all(x) for x in mask_history])
    # When the agent takes action N from its action map, we need to have a look at the action mask and make sure that
    # the N-th entry was True, meaning that it was a valid action at that step.
    # This plucks out the mask history at step i, and at action entry a and checks that it's set to True, and this
    # happens for all steps i in the episode
    assert all(mask_history[i][a] for i, a in enumerate(action_num_history))
    monkeypatch.undo()


def test_ray_single_agent_action_masking(monkeypatch):
    """Check that a Ray agent uses the action mask and never chooses invalid actions."""
    with open(CFG_PATH, "r") as f:
        cfg = yaml.safe_load(f)
    for agent in cfg["agents"]:
        if agent["ref"] == "defender":
            agent["agent_settings"]["flatten_obs"] = True

    # There's no simple way of capturing what the action mask was at every step, therefore we are mocking the step
    # function to save the action mask and the agent's chosen action to a local variable.
    old_step_method = PrimaiteRayEnv.step
    action_num_history = []
    mask_history = []

    def cache_step(self, action: int):
        action_num_history.append(action)
        obs, *_ = old_step_method(self, action)
        action_mask = obs["action_mask"]
        mask_history.append(action_mask)
        return obs, *_

    monkeypatch.setattr(PrimaiteRayEnv, "step", lambda *args, **kwargs: cache_step(*args, **kwargs))

    # Configure Ray PPO to use action masking by using the ActionMaskingTorchRLModule
    config = (
        PPOConfig()
        .api_stack(enable_rl_module_and_learner=True, enable_env_runner_and_connector_v2=True)
        .environment(env=PrimaiteRayEnv, env_config=cfg, action_mask_key="action_mask")
        .rl_module(rl_module_spec=SingleAgentRLModuleSpec(module_class=ActionMaskingTorchRLModule))
        .env_runners(num_env_runners=0)
        .training(train_batch_size=128)
    )
    algo = config.build()
    algo.train()

    assert len(action_num_history) == len(mask_history) > 0
    # Make sure the masks had at least some False entries, if it was all True then the mask was disabled
    assert any([not all(x) for x in mask_history])
    # When the agent takes action N from its action map, we need to have a look at the action mask and make sure that
    # the N-th action was valid.
    # The first step uses the action mask provided by the reset method, so we are only checking from the second step
    # onward, that's why we need to use mask_history[:-1] and action_num_history[1:]
    assert all(mask_history[:-1][i][a] for i, a in enumerate(action_num_history[1:]))
    monkeypatch.undo()


@pytest.mark.xfail(reason="Fails due to being flaky when run in CI.")
def test_ray_multi_agent_action_masking(monkeypatch):
    """Check that Ray agents never take invalid actions when using MARL."""
    with open(MARL_PATH, "r") as f:
        cfg = yaml.safe_load(f)

    old_step_method = PrimaiteRayMARLEnv.step
    action_num_history = {"defender_1": [], "defender_2": []}
    mask_history = {"defender_1": [], "defender_2": []}

    def cache_step(self, actions: Dict[str, int]):
        for agent_name, action in actions.items():
            action_num_history[agent_name].append(action)
        obs, *_ = old_step_method(self, actions)
        for (
            agent_name,
            o,
        ) in obs.items():
            mask_history[agent_name].append(o["action_mask"])
        return obs, *_

    monkeypatch.setattr(PrimaiteRayMARLEnv, "step", lambda *args, **kwargs: cache_step(*args, **kwargs))

    config = (
        PPOConfig()
        .multi_agent(
            policies={
                "defender_1",
                "defender_2",
            },  # These names are the same as the agents defined in the example config.
            policy_mapping_fn=lambda agent_id, *args, **kwargs: agent_id,
        )
        .api_stack(enable_rl_module_and_learner=True, enable_env_runner_and_connector_v2=True)
        .environment(env=PrimaiteRayMARLEnv, env_config=cfg, action_mask_key="action_mask")
        .rl_module(
            rl_module_spec=MultiAgentRLModuleSpec(
                module_specs={
                    "defender_1": SingleAgentRLModuleSpec(module_class=ActionMaskingTorchRLModule),
                    "defender_2": SingleAgentRLModuleSpec(module_class=ActionMaskingTorchRLModule),
                }
            )
        )
        .env_runners(num_env_runners=0)
        .training(train_batch_size=128)
    )
    algo = config.build()
    algo.train()

    for agent_name in ["defender_1", "defender_2"]:
        act_hist = action_num_history[agent_name]
        mask_hist = mask_history[agent_name]
        assert len(act_hist) == len(mask_hist) > 0
        assert any([not all(x) for x in mask_hist])
        assert all(mask_hist[:-1][i][a] for i, a in enumerate(act_hist[1:]))
    monkeypatch.undo()
