# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
from __future__ import annotations

from dataclasses import dataclass, field
from logging import Logger
from pathlib import Path
from typing import Any, Dict, Final, Optional, Union

import yaml

from primaite import getLogger, PRIMAITE_PATHS
from primaite.common.enums import (
    ActionType,
    AgentFramework,
    AgentIdentifier,
    DeepLearningFramework,
    HardCodedAgentView,
    RulePermissionType,
    SB3OutputVerboseLevel,
    SessionType,
)

_LOGGER: Logger = getLogger(__name__)

_EXAMPLE_TRAINING: Final[Path] = PRIMAITE_PATHS.user_config_path / "example_config" / "training"


def main_training_config_path() -> Path:
    """
    The path to the example training_config_main.yaml file.

    :return: The file path.
    """
    path = _EXAMPLE_TRAINING / "training_config_main.yaml"
    if not path.exists():
        msg = "Example config not found. Please run 'primaite setup'"
        _LOGGER.critical(msg)
        raise FileNotFoundError(msg)

    return path


@dataclass()
class TrainingConfig:
    """The Training Config class."""

    agent_framework: AgentFramework = AgentFramework.SB3
    "The AgentFramework"

    deep_learning_framework: DeepLearningFramework = DeepLearningFramework.TF
    "The DeepLearningFramework"

    agent_identifier: AgentIdentifier = AgentIdentifier.PPO
    "The AgentIdentifier"

    hard_coded_agent_view: HardCodedAgentView = HardCodedAgentView.FULL
    "The view the deterministic hard-coded agent has of the environment"

    random_red_agent: bool = False
    "Creates Random Red Agent Attacks"

    action_type: ActionType = ActionType.ANY
    "The ActionType to use"

    num_train_episodes: int = 10
    "The number of episodes to train over during an training session"

    num_train_steps: int = 256
    "The number of steps in an episode during an training session"

    num_eval_episodes: int = 1
    "The number of episodes to train over during an evaluation session"

    num_eval_steps: int = 256
    "The number of steps in an episode during an evaluation session"

    checkpoint_every_n_episodes: int = 5
    "The agent will save a checkpoint every n episodes"

    observation_space: dict = field(default_factory=lambda: {"components": [{"name": "NODE_LINK_TABLE"}]})
    "The observation space config dict"

    time_delay: int = 10
    "The delay between steps (ms). Applies to generic agents only"

    # file
    session_type: SessionType = SessionType.TRAIN
    "The type of PrimAITE session to run"

    load_agent: bool = False
    "Determine whether to load an agent from file"

    agent_load_file: Optional[str] = None
    "File path and file name of agent if you're loading one in"

    # Environment
    observation_space_high_value: int = 1000000000
    "The high value for the observation space"

    sb3_output_verbose_level: SB3OutputVerboseLevel = SB3OutputVerboseLevel.NONE
    "Stable Baselines3 learn/eval output verbosity level"

    implicit_acl_rule: RulePermissionType = RulePermissionType.DENY
    "ALLOW or DENY implicit firewall rule to go at the end of list of ACL list."

    max_number_acl_rules: int = 30
    "Sets a limit for number of acl rules allowed in the list and environment."

    # Reward values
    # Generic
    all_ok: float = 0

    # Node Hardware State
    off_should_be_on: float = -0.001
    off_should_be_resetting: float = -0.0005
    on_should_be_off: float = -0.0002
    on_should_be_resetting: float = -0.0005
    resetting_should_be_on: float = -0.0005
    resetting_should_be_off: float = -0.0002
    resetting: float = -0.0003

    # Node Software or Service State
    good_should_be_patching: float = 0.0002
    good_should_be_compromised: float = 0.0005
    good_should_be_overwhelmed: float = 0.0005
    patching_should_be_good: float = -0.0005
    patching_should_be_compromised: float = 0.0002
    patching_should_be_overwhelmed: float = 0.0002
    patching: float = -0.0003
    compromised_should_be_good: float = -0.002
    compromised_should_be_patching: float = -0.002
    compromised_should_be_overwhelmed: float = -0.002
    compromised: float = -0.002
    overwhelmed_should_be_good: float = -0.002
    overwhelmed_should_be_patching: float = -0.002
    overwhelmed_should_be_compromised: float = -0.002
    overwhelmed: float = -0.002

    # Node File System State
    good_should_be_repairing: float = 0.0002
    good_should_be_restoring: float = 0.0002
    good_should_be_corrupt: float = 0.0005
    good_should_be_destroyed: float = 0.001
    repairing_should_be_good: float = -0.0005
    repairing_should_be_restoring: float = 0.0002
    repairing_should_be_corrupt: float = 0.0002
    repairing_should_be_destroyed: float = 0.0000
    repairing: float = -0.0003
    restoring_should_be_good: float = -0.001
    restoring_should_be_repairing: float = -0.0002
    restoring_should_be_corrupt: float = 0.0001
    restoring_should_be_destroyed: float = 0.0002
    restoring: float = -0.0006
    corrupt_should_be_good: float = -0.001
    corrupt_should_be_repairing: float = -0.001
    corrupt_should_be_restoring: float = -0.001
    corrupt_should_be_destroyed: float = 0.0002
    corrupt: float = -0.001
    destroyed_should_be_good: float = -0.002
    destroyed_should_be_repairing: float = -0.002
    destroyed_should_be_restoring: float = -0.002
    destroyed_should_be_corrupt: float = -0.002
    destroyed: float = -0.002
    scanning: float = -0.0002

    # IER status
    red_ier_running: float = -0.0005
    green_ier_blocked: float = -0.001

    # Patching / Reset durations
    os_patching_duration: int = 5
    "The time taken to patch the OS"

    node_reset_duration: int = 5
    "The time taken to reset a node (hardware)"

    node_booting_duration: int = 3
    "The Time taken to turn on the node"

    node_shutdown_duration: int = 2
    "The time taken to turn off the node"

    service_patching_duration: int = 5
    "The time taken to patch a service"

    file_system_repairing_limit: int = 5
    "The time take to repair the file system"

    file_system_restoring_limit: int = 5
    "The time take to restore the file system"

    file_system_scanning_limit: int = 5
    "The time taken to scan the file system"

    deterministic: bool = False
    "If true, the training will be deterministic"

    seed: Optional[int] = None
    "The random number generator seed to be used while training the agent"

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> TrainingConfig:
        """
        Create an instance of TrainingConfig from a dict.

        :param config_dict: The training config dict.
        :return: The instance of TrainingConfig.
        """
        field_enum_map = {
            "agent_framework": AgentFramework,
            "deep_learning_framework": DeepLearningFramework,
            "agent_identifier": AgentIdentifier,
            "action_type": ActionType,
            "session_type": SessionType,
            "sb3_output_verbose_level": SB3OutputVerboseLevel,
            "hard_coded_agent_view": HardCodedAgentView,
            "implicit_acl_rule": RulePermissionType,
        }

        # convert the string representation of enums into the actual enum values themselves?
        for key, value in field_enum_map.items():
            if key in config_dict:
                config_dict[key] = value[config_dict[key]]

        return TrainingConfig(**config_dict)

    def to_dict(self, json_serializable: bool = True) -> Dict:
        """
        Serialise the ``TrainingConfig`` as dict.

        :param json_serializable: If True, Enums are converted to their
            string name.
        :return: The ``TrainingConfig`` as a dict.
        """
        data = self.__dict__
        if json_serializable:
            data["agent_framework"] = self.agent_framework.name
            data["deep_learning_framework"] = self.deep_learning_framework.name
            data["agent_identifier"] = self.agent_identifier.name
            data["action_type"] = self.action_type.name
            data["sb3_output_verbose_level"] = self.sb3_output_verbose_level.name
            data["session_type"] = self.session_type.name
            data["hard_coded_agent_view"] = self.hard_coded_agent_view.name
            data["implicit_acl_rule"] = self.implicit_acl_rule.name

        return data

    def __str__(self) -> str:
        obs_str = ",".join([c["name"] for c in self.observation_space["components"]])
        tc = f"{self.agent_framework}, "
        if self.agent_framework is AgentFramework.RLLIB:
            tc += f"{self.deep_learning_framework}, "
        tc += f"{self.agent_identifier}, "
        if self.agent_identifier is AgentIdentifier.HARDCODED:
            tc += f"{self.hard_coded_agent_view}, "
        tc += f"{self.action_type}, "
        tc += f"observation_space={obs_str}, "
        if self.session_type is SessionType.TRAIN:
            tc += f"{self.num_train_episodes} episodes @ "
            tc += f"{self.num_train_steps} steps"
        elif self.session_type is SessionType.EVAL:
            tc += f"{self.num_eval_episodes} episodes @ "
            tc += f"{self.num_eval_steps} steps"
        else:
            tc += f"Training: {self.num_eval_episodes} episodes @ "
            tc += f"{self.num_eval_steps} steps"
            tc += f"Evaluation: {self.num_eval_episodes} episodes @ "
            tc += f"{self.num_eval_steps} steps"
        return tc


def load(file_path: Union[str, Path], legacy_file: bool = False) -> TrainingConfig:
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

            except KeyError as e:
                msg = (
                    f"Failed to convert training config file {file_path} "
                    f"from legacy format. Attempting to use file as is."
                )
                _LOGGER.error(msg)
                raise e
        try:
            return TrainingConfig.from_dict(config)
        except TypeError as e:
            msg = f"Error when creating an instance of {TrainingConfig} " f"from the training config file {file_path}"
            _LOGGER.critical(msg, exc_info=True)
            raise e
    msg = f"Cannot load the training config as it does not exist: {file_path}"
    _LOGGER.error(msg)
    raise ValueError(msg)


def convert_legacy_training_config_dict(
    legacy_config_dict: Dict[str, Any],
    agent_framework: AgentFramework = AgentFramework.SB3,
    agent_identifier: AgentIdentifier = AgentIdentifier.PPO,
    action_type: ActionType = ActionType.ANY,
    num_train_steps: int = 256,
    num_eval_steps: int = 256,
    num_train_episodes: int = 10,
    num_eval_episodes: int = 1,
) -> Dict[str, Any]:
    """
    Convert a legacy training config dict to the new format.

    :param legacy_config_dict: A legacy training config dict.
    :param agent_framework: The agent framework to use as legacy training
        configs don't have agent_framework values.
    :param agent_identifier: The red agent identifier to use as legacy
        training configs don't have agent_identifier values.
    :param action_type: The action space type to set as legacy training configs
        don't have action_type values.
    :param num_train_steps: The number of train steps to set as legacy training configs
        don't have num_train_steps values.
    :param num_eval_steps: The number of eval steps to set as legacy training configs
        don't have num_eval_steps values.
    :param num_train_episodes: The number of train episodes to set as legacy training configs
        don't have num_train_episodes values.
    :param num_eval_episodes: The number of eval episodes to set as legacy training configs
        don't have num_eval_episodes values.
    :return: The converted training config dict.
    """
    config_dict = {
        "agent_framework": agent_framework.name,
        "agent_identifier": agent_identifier.name,
        "action_type": action_type.name,
        "num_train_steps": num_train_steps,
        "num_eval_steps": num_eval_steps,
        "num_train_episodes": num_train_episodes,
        "num_eval_episodes": num_eval_episodes,
        "sb3_output_verbose_level": SB3OutputVerboseLevel.INFO.name,
    }
    session_type_map = {"TRAINING": "TRAIN", "EVALUATION": "EVAL"}
    legacy_config_dict["sessionType"] = session_type_map[legacy_config_dict["sessionType"]]
    for legacy_key, value in legacy_config_dict.items():
        new_key = _get_new_key_from_legacy(legacy_key)
        if new_key:
            config_dict[new_key] = value
    return config_dict


def _get_new_key_from_legacy(legacy_key: str) -> Optional[str]:
    """
    Maps legacy training config keys to the new format keys.

    :param legacy_key: A legacy training config key.
    :return: The mapped key.
    """
    key_mapping = {
        "agentIdentifier": None,
        "numEpisodes": "num_train_episodes",
        "numSteps": "num_train_steps",
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
        "nodeBootingDuration": "node_booting_duration",
        "nodeShutdownDuration": "node_shutdown_duration",
        "servicePatchingDuration": "service_patching_duration",
        "fileSystemRepairingLimit": "file_system_repairing_limit",
        "fileSystemRestoringLimit": "file_system_restoring_limit",
        "fileSystemScanningLimit": "file_system_scanning_limit",
    }
    return key_mapping[legacy_key]
