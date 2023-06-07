# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Union, Final

import yaml

from primaite import getLogger, USERS_CONFIG_DIR
from primaite.common.enums import ActionType

_LOGGER = getLogger(__name__)

_EXAMPLE_TRAINING: Final[
    Path] = USERS_CONFIG_DIR / "example_config" / "training"


@dataclass()
class TrainingConfig:
    """The Training Config class."""

    # Generic
    agent_identifier: str  # The Red Agent algo/class to be used
    action_type: ActionType  # type of action to use (NODE/ACL/ANY)
    num_episodes: int  # number of episodes to train over
    num_steps: int  # number of steps in an episode
    time_delay: int  # delay between steps (ms) - applies to generic agents only
    # file
    session_type: str  # the session type to run (TRAINING or EVALUATION)
    load_agent: str  # Determine whether to load an agent from file
    agent_load_file: str  # File path and file name of agent if you're loading one in

    # Environment
    observation_space_high_value: int  # The high value for the observation space

    # Reward values
    # Generic
    all_ok: int
    # Node Hardware State
    off_should_be_on: int
    off_should_be_resetting: int
    on_should_be_off: int
    on_should_be_resetting: int
    resetting_should_be_on: int
    resetting_should_be_off: int
    resetting: int
    # Node Software or Service State
    good_should_be_patching: int
    good_should_be_compromised: int
    good_should_be_overwhelmed: int
    patching_should_be_good: int
    patching_should_be_compromised: int
    patching_should_be_overwhelmed: int
    patching: int
    compromised_should_be_good: int
    compromised_should_be_patching: int
    compromised_should_be_overwhelmed: int
    compromised: int
    overwhelmed_should_be_good: int
    overwhelmed_should_be_patching: int
    overwhelmed_should_be_compromised: int
    overwhelmed: int
    # Node File System State
    good_should_be_repairing: int
    good_should_be_restoring: int
    good_should_be_corrupt: int
    good_should_be_destroyed: int
    repairing_should_be_good: int
    repairing_should_be_restoring: int
    repairing_should_be_corrupt: int
    repairing_should_be_destroyed: int  # Repairing does not fix destroyed state - you need to restore

    repairing: int
    restoring_should_be_good: int
    restoring_should_be_repairing: int
    restoring_should_be_corrupt: int  # Not the optimal method (as repair will fix corruption)

    restoring_should_be_destroyed: int
    restoring: int
    corrupt_should_be_good: int
    corrupt_should_be_repairing: int
    corrupt_should_be_restoring: int
    corrupt_should_be_destroyed: int
    corrupt: int
    destroyed_should_be_good: int
    destroyed_should_be_repairing: int
    destroyed_should_be_restoring: int
    destroyed_should_be_corrupt: int
    destroyed: int
    scanning: int
    # IER status
    red_ier_running: int
    green_ier_blocked: int

    # Patching / Reset
    os_patching_duration: int  # The time taken to patch the OS
    node_reset_duration: int  # The time taken to reset a node (hardware)
    service_patching_duration: int  # The time taken to patch a service
    file_system_repairing_limit: int  # The time take to repair a file
    file_system_restoring_limit: int  # The time take to restore a file
    file_system_scanning_limit: int  # The time taken to scan the file system


def main_training_config_path() -> Path:
    """
    The path to the example training_config_main.yaml file

    :return: The file path.
    """

    path = _EXAMPLE_TRAINING / "training_config_main.yaml"
    if not path.exists():
        msg = f"Example config not found. Please run 'primaite setup'"
        _LOGGER.critical(msg)
        raise FileNotFoundError(msg)

    return path


def load(file_path: Union[str, Path],
         legacy_file: bool = False) -> TrainingConfig:
    """
    Read in a training config yaml file.

    :param file_path: The config file path.
    :param legacy_file: True if the config file is legacy format, otherwise
        False.
    :return: An instance of
        :class:`~primaite.config.training_config.TrainingConfig`.
    :raises ValueError: If the file_path does not exist.
    :raises TypeError: When the TrainingConfig object cannot be created
        using the values from the config file read from ``file_path``.
    """
    if not isinstance(file_path, Path):
        file_path = Path(file_path)
    if file_path.exists():
        with open(file_path, "r") as file:
            config = yaml.safe_load(file)
            _LOGGER.debug(f"Loading training config file: {file_path}")
        if legacy_file:
            try:
                config = convert_legacy_training_config_dict(config)
            except KeyError:
                msg = (
                    f"Failed to convert training config file {file_path} "
                    f"from legacy format. Attempting to use file as is."
                )
                _LOGGER.error(msg)
        # Convert values to Enums
        config["action_type"] = ActionType[config["action_type"]]
        try:
            return TrainingConfig(**config)
        except TypeError as e:
            msg = (
                f"Error when creating an instance of {TrainingConfig} "
                f"from the training config file {file_path}"
            )
            _LOGGER.critical(msg, exc_info=True)
            raise e
    msg = f"Cannot load the training config as it does not exist: {file_path}"
    _LOGGER.error(msg)
    raise ValueError(msg)


def convert_legacy_training_config_dict(
        legacy_config_dict: Dict[str, Any],
        num_steps: int = 256,
        action_type: str = "ANY"
) -> Dict[str, Any]:
    """
    Convert a legacy training config dict to the new format.

    :param legacy_config_dict: A legacy training config dict.
    :param num_steps: The number of steps to set as legacy training configs
        don't have num_steps values.
    :param action_type: The action space type to set as legacy training configs
        don't have action_type values.
    :return: The converted training config dict.
    """
    config_dict = {"num_steps": num_steps, "action_type": action_type}
    for legacy_key, value in legacy_config_dict.items():
        new_key = _get_new_key_from_legacy(legacy_key)
        if new_key:
            config_dict[new_key] = value
    return config_dict


def _get_new_key_from_legacy(legacy_key: str) -> str:
    """
    Maps legacy training config keys to the new format keys.

    :param legacy_key: A legacy training config key.
    :return: The mapped key.
    """
    key_mapping = {
        "agentIdentifier": "agent_identifier",
        "numEpisodes": "num_episodes",
        "timeDelay": "time_delay",
        "configFilename": None,
        "sessionType": "session_type",
        "loadAgent": "load_agent",
        "agentLoadFile": "agent_load_file",
        "observationSpaceHighValue": "observation_space_high_value",
        "allOk": "all_ok",
        "offShouldBeOn": "off_should_be_on",
        "offShouldBeResetting": "off_should_be_resetting",
        "onShouldBeOff": "on_should_be_off",
        "onShouldBeResetting": "on_should_be_resetting",
        "resettingShouldBeOn": "resetting_should_be_on",
        "resettingShouldBeOff": "resetting_should_be_off",
        "resetting": "resetting",
        "goodShouldBePatching": "good_should_be_patching",
        "goodShouldBeCompromised": "good_should_be_compromised",
        "goodShouldBeOverwhelmed": "good_should_be_overwhelmed",
        "patchingShouldBeGood": "patching_should_be_good",
        "patchingShouldBeCompromised": "patching_should_be_compromised",
        "patchingShouldBeOverwhelmed": "patching_should_be_overwhelmed",
        "patching": "patching",
        "compromisedShouldBeGood": "compromised_should_be_good",
        "compromisedShouldBePatching": "compromised_should_be_patching",
        "compromisedShouldBeOverwhelmed": "compromised_should_be_overwhelmed",
        "compromised": "compromised",
        "overwhelmedShouldBeGood": "overwhelmed_should_be_good",
        "overwhelmedShouldBePatching": "overwhelmed_should_be_patching",
        "overwhelmedShouldBeCompromised": "overwhelmed_should_be_compromised",
        "overwhelmed": "overwhelmed",
        "goodShouldBeRepairing": "good_should_be_repairing",
        "goodShouldBeRestoring": "good_should_be_restoring",
        "goodShouldBeCorrupt": "good_should_be_corrupt",
        "goodShouldBeDestroyed": "good_should_be_destroyed",
        "repairingShouldBeGood": "repairing_should_be_good",
        "repairingShouldBeRestoring": "repairing_should_be_restoring",
        "repairingShouldBeCorrupt": "repairing_should_be_corrupt",
        "repairingShouldBeDestroyed": "repairing_should_be_destroyed",
        "repairing": "repairing",
        "restoringShouldBeGood": "restoring_should_be_good",
        "restoringShouldBeRepairing": "restoring_should_be_repairing",
        "restoringShouldBeCorrupt": "restoring_should_be_corrupt",
        "restoringShouldBeDestroyed": "restoring_should_be_destroyed",
        "restoring": "restoring",
        "corruptShouldBeGood": "corrupt_should_be_good",
        "corruptShouldBeRepairing": "corrupt_should_be_repairing",
        "corruptShouldBeRestoring": "corrupt_should_be_restoring",
        "corruptShouldBeDestroyed": "corrupt_should_be_destroyed",
        "corrupt": "corrupt",
        "destroyedShouldBeGood": "destroyed_should_be_good",
        "destroyedShouldBeRepairing": "destroyed_should_be_repairing",
        "destroyedShouldBeRestoring": "destroyed_should_be_restoring",
        "destroyedShouldBeCorrupt": "destroyed_should_be_corrupt",
        "destroyed": "destroyed",
        "scanning": "scanning",
        "redIerRunning": "red_ier_running",
        "greenIerBlocked": "green_ier_blocked",
        "osPatchingDuration": "os_patching_duration",
        "nodeResetDuration": "node_reset_duration",
        "servicePatchingDuration": "service_patching_duration",
        "fileSystemRepairingLimit": "file_system_repairing_limit",
        "fileSystemRestoringLimit": "file_system_restoring_limit",
        "fileSystemScanningLimit": "file_system_scanning_limit",
    }
    return key_mapping[legacy_key]
