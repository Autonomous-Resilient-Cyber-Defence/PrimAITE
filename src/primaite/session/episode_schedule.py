# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
import copy
from abc import ABC, abstractmethod
from itertools import chain
from pathlib import Path
from typing import Dict, List, Mapping, Sequence, Union

import pydantic
import yaml

from primaite import getLogger

_LOGGER = getLogger(__name__)


class EpisodeScheduler(pydantic.BaseModel, ABC):
    """
    Episode schedulers provide functionality to select different scenarios and game setups for each episode.

    This is useful when implementing advanced RL concepts like curriculum learning and domain randomisation.
    """

    @abstractmethod
    def __call__(self, episode_num: int) -> Dict:
        """Return the config that should be used during this episode."""
        ...


class ConstantEpisodeScheduler(EpisodeScheduler):
    """The constant episode schedule simply provides the same game setup every time."""

    config: Dict

    def __call__(self, episode_num: int) -> Dict:
        """Return the same config every time."""
        return copy.deepcopy(self.config)


class EpisodeListScheduler(EpisodeScheduler):
    """Cycle through a list of different game setups for each episode."""

    schedule: Mapping[int, List[str]]
    """Mapping from episode number to list of filenames"""
    episode_data: Mapping[str, str]
    """Mapping from filename to yaml string."""
    base_scenario: str
    """yaml string containing the base scenario."""

    _exceeded_episode_list: bool = False
    """
    Flag that's set to true when attempting to keep generating episodes after schedule runs out.

    When this happens, we loop back to the beginning, but a warning is raised.
    """

    def __call__(self, episode_num: int) -> Dict:
        """Return the config for the given episode number."""
        if episode_num >= len(self.schedule):
            if not self._exceeded_episode_list:
                self._exceeded_episode_list = True
                _LOGGER.warning(
                    f"Running episode {episode_num} but the schedule only defines "
                    f"{len(self.schedule)} episodes. Looping back to the beginning"
                )
                # not sure if we should be using a traditional warning, or a _LOGGER.warning
            episode_num = episode_num % len(self.schedule)

        filenames_to_join = self.schedule[episode_num]
        yaml_data_to_join = [self.episode_data[fn] for fn in filenames_to_join] + [self.base_scenario]
        joined_yaml = "\n".join(yaml_data_to_join)
        parsed_cfg = yaml.safe_load(joined_yaml)

        # Unfortunately, using placeholders like this is slightly hacky, so we have to flatten the list of agents
        flat_agents_list = []
        for a in parsed_cfg["agents"]:
            if isinstance(a, Sequence):
                flat_agents_list.extend(a)
            else:
                flat_agents_list.append(a)
        parsed_cfg["agents"] = flat_agents_list

        return parsed_cfg


def build_scheduler(config: Union[str, Path, Dict]) -> EpisodeScheduler:
    """
    Convenience method to build an EpisodeScheduler with a dict, file path, or folder path.

    If a path to a folder is provided, it will be treated as a list of game scenarios.
    Otherwise, if a dict or a single file is provided, it will be treated as a constant game scenario.
    """
    # If we get a dict, return a constant episode schedule that repeats that one config forever
    if isinstance(config, Dict):
        return ConstantEpisodeScheduler(config=config)

    # Cast string to Path
    if isinstance(config, str):
        config = Path(config)

    if not config.exists():
        raise FileNotFoundError(f"Provided config path {config} could not be found.")

    if config.is_file():
        with open(config, "r") as f:
            cfg_data = yaml.safe_load(f)
        return ConstantEpisodeScheduler(config=cfg_data)

    if not config.is_dir():
        raise RuntimeError("Something went wrong while building Primaite config.")

    root = config
    schedule_path = root / "schedule.yaml"

    with open(schedule_path, "r") as f:
        schedule = yaml.safe_load(f)

    base_scenario_path = root / schedule["base_scenario"]
    files_to_load = set(chain.from_iterable(schedule["schedule"].values()))

    episode_data = {fp: (root / fp).read_text() for fp in files_to_load}

    return EpisodeListScheduler(
        schedule=schedule["schedule"], episode_data=episode_data, base_scenario=base_scenario_path.read_text()
    )
