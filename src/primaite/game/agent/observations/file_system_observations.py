from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from gymnasium import spaces

from primaite import getLogger
from primaite.game.agent.observations.observations import AbstractObservation
from primaite.game.agent.utils import access_from_nested_dict, NOT_PRESENT_IN_STATE

_LOGGER = getLogger(__name__)

if TYPE_CHECKING:
    from primaite.game.game import PrimaiteGame


class FileObservation(AbstractObservation):
    """Observation of a file on a node in the network."""

    def __init__(self, where: Optional[Tuple[str]] = None) -> None:
        """
        Initialise file observation.

        :param where: Store information about where in the simulation state dictionary to find the relevant information.
            Optional. If None, this corresponds that the file does not exist and the observation will be populated with
            zeroes.

            A typical location for a file looks like this:
            ['network','nodes',<node_hostname>,'file_system', 'folders',<folder_name>,'files',<file_name>]
        :type where: Optional[List[str]]
        """
        super().__init__()
        self.where: Optional[Tuple[str]] = where
        self.default_observation: spaces.Space = {"health_status": 0}
        "Default observation is what should be returned when the file doesn't exist, e.g. after it has been deleted."

    def observe(self, state: Dict) -> Dict:
        """Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary
        :type state: Dict
        :return: Observation
        :rtype: Dict
        """
        if self.where is None:
            return self.default_observation
        file_state = access_from_nested_dict(state, self.where)
        if file_state is NOT_PRESENT_IN_STATE:
            return self.default_observation
        return {"health_status": file_state["visible_status"]}

    @property
    def space(self) -> spaces.Space:
        """Gymnasium space object describing the observation space shape.

        :return: Gymnasium space
        :rtype: spaces.Space
        """
        return spaces.Dict({"health_status": spaces.Discrete(6)})

    @classmethod
    def from_config(cls, config: Dict, game: "PrimaiteGame", parent_where: List[str] = None) -> "FileObservation":
        """Create file observation from a config.

        :param config: Dictionary containing the configuration for this file observation.
        :type config: Dict
        :param game: _description_
        :type game: PrimaiteGame
        :param parent_where: _description_, defaults to None
        :type parent_where: _type_, optional
        :return: _description_
        :rtype: _type_
        """
        return cls(where=parent_where + ["files", config["file_name"]])


class FolderObservation(AbstractObservation):
    """Folder observation, including files inside of the folder."""

    def __init__(
        self, where: Optional[Tuple[str]] = None, files: List[FileObservation] = [], num_files_per_folder: int = 2
    ) -> None:
        """Initialise folder Observation, including files inside the folder.

        :param where: Where in the simulation state dictionary to find the relevant information for this folder.
            A typical location for a file looks like this:
            ['network','nodes',<node_hostname>,'file_system', 'folders',<folder_name>]
        :type where: Optional[List[str]]
        :param max_files: As size of the space must remain static, define max files that can be in this folder
            , defaults to 5
        :type max_files: int, optional
        :param file_positions: Defines the positioning within the observation space of particular files. This ensures
            that even if new files are created, the existing files will always occupy the same space in the observation
            space. The keys must be between 1 and max_files. Providing file_positions will reserve a spot in the
            observation space for a file with that name, even if it's temporarily deleted, if it reappears with the same
            name, it will take the position defined in this dict. Defaults to {}
        :type file_positions: Dict[int, str], optional
        """
        super().__init__()

        self.where: Optional[Tuple[str]] = where

        self.files: List[FileObservation] = files
        while len(self.files) < num_files_per_folder:
            self.files.append(FileObservation())
        while len(self.files) > num_files_per_folder:
            truncated_file = self.files.pop()
            msg = f"Too many files in folder observation. Truncating file {truncated_file}"
            _LOGGER.warning(msg)

        self.default_observation = {
            "health_status": 0,
            "FILES": {i + 1: f.default_observation for i, f in enumerate(self.files)},
        }

    def observe(self, state: Dict) -> Dict:
        """Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary
        :type state: Dict
        :return: Observation
        :rtype: Dict
        """
        if self.where is None:
            return self.default_observation
        folder_state = access_from_nested_dict(state, self.where)
        if folder_state is NOT_PRESENT_IN_STATE:
            return self.default_observation

        health_status = folder_state["health_status"]

        obs = {}

        obs["health_status"] = health_status
        obs["FILES"] = {i + 1: file.observe(state) for i, file in enumerate(self.files)}

        return obs

    @property
    def space(self) -> spaces.Space:
        """Gymnasium space object describing the observation space shape.

        :return: Gymnasium space
        :rtype: spaces.Space
        """
        return spaces.Dict(
            {
                "health_status": spaces.Discrete(6),
                "FILES": spaces.Dict({i + 1: f.space for i, f in enumerate(self.files)}),
            }
        )

    @classmethod
    def from_config(
        cls, config: Dict, game: "PrimaiteGame", parent_where: Optional[List[str]], num_files_per_folder: int = 2
    ) -> "FolderObservation":
        """Create folder observation from a config. Also creates child file observations.

        :param config: Dictionary containing the configuration for this folder observation. Includes the name of the
            folder and the files inside of it.
        :type config: Dict
        :param game: Reference to the PrimaiteGame object that spawned this observation.
        :type game: PrimaiteGame
        :param parent_where: Where in the simulation state dictionary to find the information about this folder's
            parent node. A typical location for a node ``where`` can be:
            ['network','nodes',<node_hostname>,'file_system']
        :type parent_where: Optional[List[str]]
        :param num_files_per_folder: How many spaces for files are in this folder observation (to preserve static
            observation size) , defaults to 2
        :type num_files_per_folder: int, optional
        :return: Constructed folder observation
        :rtype: FolderObservation
        """
        where = parent_where + ["folders", config["folder_name"]]

        file_configs = config["files"]
        files = [FileObservation.from_config(config=f, game=game, parent_where=where) for f in file_configs]

        return cls(where=where, files=files, num_files_per_folder=num_files_per_folder)
