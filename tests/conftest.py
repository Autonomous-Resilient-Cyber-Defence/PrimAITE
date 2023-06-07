# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
import time
from pathlib import Path
from typing import Union

import yaml

from primaite.common.config_values_main import ConfigValuesMain
from primaite.environment.primaite_env import Primaite

ACTION_SPACE_NODE_VALUES = 1
ACTION_SPACE_NODE_ACTION_VALUES = 1


def _get_primaite_env_from_config(
    main_config_path: Union[str, Path], lay_down_config_path: Union[str, Path]
):
    """Takes a config path and returns the created instance of Primaite."""

    def load_config_values():
        config_values.agent_identifier = config_data["agentIdentifier"]
        if "observationSpace" in config_data:
            config_values.observation_config = config_data["observationSpace"]
        else:
            config_values.observation_config = None
        config_values.num_episodes = int(config_data["numEpisodes"])
        config_values.time_delay = int(config_data["timeDelay"])
        config_values.config_filename_use_case = lay_down_config_path
        config_values.session_type = config_data["sessionType"]
        config_values.load_agent = bool(config_data["loadAgent"])
        config_values.agent_load_file = config_data["agentLoadFile"]
        # Environment
        config_values.observation_space_high_value = int(
            config_data["observationSpaceHighValue"]
        )
        # Reward values
        # Generic
        config_values.all_ok = int(config_data["allOk"])
        # Node Hardware State
        config_values.off_should_be_on = int(config_data["offShouldBeOn"])
        config_values.off_should_be_resetting = int(config_data["offShouldBeResetting"])
        config_values.on_should_be_off = int(config_data["onShouldBeOff"])
        config_values.on_should_be_resetting = int(config_data["onShouldBeResetting"])
        config_values.resetting_should_be_on = int(config_data["resettingShouldBeOn"])
        config_values.resetting_should_be_off = int(config_data["resettingShouldBeOff"])
        config_values.resetting = int(config_data["resetting"])
        # Node Software or Service State
        config_values.good_should_be_patching = int(config_data["goodShouldBePatching"])
        config_values.good_should_be_compromised = int(
            config_data["goodShouldBeCompromised"]
        )
        config_values.good_should_be_overwhelmed = int(
            config_data["goodShouldBeOverwhelmed"]
        )
        config_values.patching_should_be_good = int(config_data["patchingShouldBeGood"])
        config_values.patching_should_be_compromised = int(
            config_data["patchingShouldBeCompromised"]
        )
        config_values.patching_should_be_overwhelmed = int(
            config_data["patchingShouldBeOverwhelmed"]
        )
        config_values.patching = int(config_data["patching"])
        config_values.compromised_should_be_good = int(
            config_data["compromisedShouldBeGood"]
        )
        config_values.compromised_should_be_patching = int(
            config_data["compromisedShouldBePatching"]
        )
        config_values.compromised_should_be_overwhelmed = int(
            config_data["compromisedShouldBeOverwhelmed"]
        )
        config_values.compromised = int(config_data["compromised"])
        config_values.overwhelmed_should_be_good = int(
            config_data["overwhelmedShouldBeGood"]
        )
        config_values.overwhelmed_should_be_patching = int(
            config_data["overwhelmedShouldBePatching"]
        )
        config_values.overwhelmed_should_be_compromised = int(
            config_data["overwhelmedShouldBeCompromised"]
        )
        config_values.overwhelmed = int(config_data["overwhelmed"])
        # Node File System State
        config_values.good_should_be_repairing = int(
            config_data["goodShouldBeRepairing"]
        )
        config_values.good_should_be_restoring = int(
            config_data["goodShouldBeRestoring"]
        )
        config_values.good_should_be_corrupt = int(config_data["goodShouldBeCorrupt"])
        config_values.good_should_be_destroyed = int(
            config_data["goodShouldBeDestroyed"]
        )
        config_values.repairing_should_be_good = int(
            config_data["repairingShouldBeGood"]
        )
        config_values.repairing_should_be_restoring = int(
            config_data["repairingShouldBeRestoring"]
        )
        config_values.repairing_should_be_corrupt = int(
            config_data["repairingShouldBeCorrupt"]
        )
        config_values.repairing_should_be_destroyed = int(
            config_data["repairingShouldBeDestroyed"]
        )
        config_values.repairing = int(config_data["repairing"])
        config_values.restoring_should_be_good = int(
            config_data["restoringShouldBeGood"]
        )
        config_values.restoring_should_be_repairing = int(
            config_data["restoringShouldBeRepairing"]
        )
        config_values.restoring_should_be_corrupt = int(
            config_data["restoringShouldBeCorrupt"]
        )
        config_values.restoring_should_be_destroyed = int(
            config_data["restoringShouldBeDestroyed"]
        )
        config_values.restoring = int(config_data["restoring"])
        config_values.corrupt_should_be_good = int(config_data["corruptShouldBeGood"])
        config_values.corrupt_should_be_repairing = int(
            config_data["corruptShouldBeRepairing"]
        )
        config_values.corrupt_should_be_restoring = int(
            config_data["corruptShouldBeRestoring"]
        )
        config_values.corrupt_should_be_destroyed = int(
            config_data["corruptShouldBeDestroyed"]
        )
        config_values.corrupt = int(config_data["corrupt"])
        config_values.destroyed_should_be_good = int(
            config_data["destroyedShouldBeGood"]
        )
        config_values.destroyed_should_be_repairing = int(
            config_data["destroyedShouldBeRepairing"]
        )
        config_values.destroyed_should_be_restoring = int(
            config_data["destroyedShouldBeRestoring"]
        )
        config_values.destroyed_should_be_corrupt = int(
            config_data["destroyedShouldBeCorrupt"]
        )
        config_values.destroyed = int(config_data["destroyed"])
        config_values.scanning = int(config_data["scanning"])
        # IER status
        config_values.red_ier_running = int(config_data["redIerRunning"])
        config_values.green_ier_blocked = int(config_data["greenIerBlocked"])
        # Patching / Reset durations
        config_values.os_patching_duration = int(config_data["osPatchingDuration"])
        config_values.node_reset_duration = int(config_data["nodeResetDuration"])
        config_values.service_patching_duration = int(
            config_data["servicePatchingDuration"]
        )
        config_values.file_system_repairing_limit = int(
            config_data["fileSystemRepairingLimit"]
        )
        config_values.file_system_restoring_limit = int(
            config_data["fileSystemRestoringLimit"]
        )
        config_values.file_system_scanning_limit = int(
            config_data["fileSystemScanningLimit"]
        )

    config_file_main = open(main_config_path, "r")
    config_data = yaml.safe_load(config_file_main)
    # Create a config class
    config_values = ConfigValuesMain()
    # Load in config data
    load_config_values()
    env = Primaite(config_values, [])
    config_values.num_steps = env.episode_steps

    if env.config_values.agent_identifier == "GENERIC":
        run_generic(env, config_values)

    return env


def run_generic(env, config_values):
    """Run against a generic agent."""
    # Reset the environment at the start of the episode
    # env.reset()
    for episode in range(0, config_values.num_episodes):
        for step in range(0, config_values.num_steps):
            # Send the observation space to the agent to get an action
            # TEMP - random action for now
            # action = env.blue_agent_action(obs)
            action = env.action_space.sample()

            # Run the simulation step on the live environment
            obs, reward, done, info = env.step(action)

            # Break if done is True
            if done:
                break

            # Introduce a delay between steps
            time.sleep(config_values.time_delay / 1000)

        # Reset the environment at the end of the episode
        # env.reset()

    # env.close()
