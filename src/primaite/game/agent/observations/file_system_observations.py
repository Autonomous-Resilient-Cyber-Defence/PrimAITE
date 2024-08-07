# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from gymnasium import spaces
from gymnasium.core import ObsType

from primaite import getLogger
from primaite.game.agent.observations.observations import AbstractObservation, WhereType
from primaite.game.agent.utils import access_from_nested_dict, NOT_PRESENT_IN_STATE

_LOGGER = getLogger(__name__)


class FileObservation(AbstractObservation, identifier="FILE"):
    """File observation, provides status information about a file within the simulation environment."""

    class ConfigSchema(AbstractObservation.ConfigSchema):
        """Configuration schema for FileObservation."""

        file_name: str
        """Name of the file, used for querying simulation state dictionary."""
        include_num_access: Optional[bool] = None
        """Whether to include the number of accesses to the file in the observation."""
        file_system_requires_scan: Optional[bool] = None
        """If True, the file must be scanned to update the health state. Tf False, the true state is always shown."""

    def __init__(self, where: WhereType, include_num_access: bool, file_system_requires_scan: bool) -> None:
        """
        Initialise a file observation instance.

        :param where: Where in the simulation state dictionary to find the relevant information for this file.
            A typical location for a file might be
            ['network', 'nodes', <node_hostname>, 'file_system', 'folder', <folder_name>, 'files', <file_name>].
        :type where: WhereType
        :param include_num_access: Whether to include the number of accesses to the file in the observation.
        :type include_num_access: bool
        :param file_system_requires_scan: If True, the file must be scanned to update the health state. Tf False,
            the true state is always shown.
        :type file_system_requires_scan: bool
        """
        self.where: WhereType = where
        self.include_num_access: bool = include_num_access
        self.file_system_requires_scan: bool = file_system_requires_scan

        self.default_observation: ObsType = {"health_status": 0}
        if self.include_num_access:
            self.default_observation["num_access"] = 0

        # TODO: allow these to be configured in yaml
        self.high_threshold = 10
        self.med_threshold = 5
        self.low_threshold = 0

    def _categorise_num_access(self, num_access: int) -> int:
        """
        Represent number of file accesses as a categorical variable.

        :param num_access: Number of file accesses.
        :return: Bin number corresponding to the number of accesses.
        """
        if num_access > self.high_threshold:
            return 3
        elif num_access > self.med_threshold:
            return 2
        elif num_access > self.low_threshold:
            return 1
        return 0

    def observe(self, state: Dict) -> ObsType:
        """
        Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary.
        :type state: Dict
        :return: Observation containing the health status of the file and optionally the number of accesses.
        :rtype: ObsType
        """
        file_state = access_from_nested_dict(state, self.where)
        if file_state is NOT_PRESENT_IN_STATE:
            return self.default_observation
        if self.file_system_requires_scan:
            health_status = file_state["visible_status"]
        else:
            health_status = file_state["health_status"]
        obs = {"health_status": health_status}
        if self.include_num_access:
            obs["num_access"] = self._categorise_num_access(file_state["num_access"])
        return obs

    @property
    def space(self) -> spaces.Space:
        """
        Gymnasium space object describing the observation space shape.

        :return: Gymnasium space representing the observation space for file status.
        :rtype: spaces.Space
        """
        space = {"health_status": spaces.Discrete(6)}
        if self.include_num_access:
            space["num_access"] = spaces.Discrete(4)
        return spaces.Dict(space)

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = []) -> FileObservation:
        """
        Create a file observation from a configuration schema.

        :param config: Configuration schema containing the necessary information for the file observation.
        :type config: ConfigSchema
        :param parent_where: Where in the simulation state dictionary to find the information about this file's
            parent node. A typical location for a node might be ['network', 'nodes', <node_hostname>].
        :type parent_where: WhereType, optional
        :return: Constructed file observation instance.
        :rtype: FileObservation
        :param file_system_requires_scan: If True, the folder must be scanned to update the health state. Tf False,
            the true state is always shown.
        :type file_system_requires_scan: bool
        """
        return cls(
            where=parent_where + ["files", config.file_name],
            include_num_access=config.include_num_access,
            file_system_requires_scan=config.file_system_requires_scan,
        )


class FolderObservation(AbstractObservation, identifier="FOLDER"):
    """Folder observation, provides status information about a folder within the simulation environment."""

    class ConfigSchema(AbstractObservation.ConfigSchema):
        """Configuration schema for FolderObservation."""

        folder_name: str
        """Name of the folder, used for querying simulation state dictionary."""
        files: List[FileObservation.ConfigSchema] = []
        """List of file configurations within the folder."""
        num_files: Optional[int] = None
        """Number of spaces for file observations in this folder."""
        include_num_access: Optional[bool] = None
        """Whether files in this folder should include the number of accesses in their observation."""
        file_system_requires_scan: Optional[bool] = None
        """If True, the folder must be scanned to update the health state. Tf False, the true state is always shown."""

    def __init__(
        self,
        where: WhereType,
        files: Iterable[FileObservation],
        num_files: int,
        include_num_access: bool,
        file_system_requires_scan: bool,
    ) -> None:
        """
        Initialise a folder observation instance.

        :param where: Where in the simulation state dictionary to find the relevant information for this folder.
            A typical location for a folder might be ['network', 'nodes', <node_hostname>, 'folders', <folder_name>].
        :type where: WhereType
        :param files: List of file observation instances within the folder.
        :type files: Iterable[FileObservation]
        :param num_files: Number of files expected in the folder.
        :type num_files: int
        :param include_num_access: Whether to include the number of accesses to files in the observation.
        :type include_num_access: bool
        """
        self.where: WhereType = where

        self.file_system_requires_scan: bool = file_system_requires_scan

        self.files: List[FileObservation] = files
        while len(self.files) < num_files:
            self.files.append(
                FileObservation(
                    where=None,
                    include_num_access=include_num_access,
                    file_system_requires_scan=self.file_system_requires_scan,
                )
            )
        while len(self.files) > num_files:
            truncated_file = self.files.pop()
            msg = f"Too many files in folder observation. Truncating file {truncated_file}"
            _LOGGER.warning(msg)

        self.default_observation = {
            "health_status": 0,
        }
        if self.files:
            self.default_observation["FILES"] = {i + 1: f.default_observation for i, f in enumerate(self.files)}

    def observe(self, state: Dict) -> ObsType:
        """
        Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary.
        :type state: Dict
        :return: Observation containing the health status of the folder and status of files within the folder.
        :rtype: ObsType
        """
        folder_state = access_from_nested_dict(state, self.where)
        if folder_state is NOT_PRESENT_IN_STATE:
            return self.default_observation

        if self.file_system_requires_scan:
            health_status = folder_state["visible_status"]
        else:
            health_status = folder_state["health_status"]

        obs = {}

        obs["health_status"] = health_status
        if self.files:
            obs["FILES"] = {i + 1: file.observe(state) for i, file in enumerate(self.files)}

        return obs

    @property
    def space(self) -> spaces.Space:
        """
        Gymnasium space object describing the observation space shape.

        :return: Gymnasium space representing the observation space for folder status.
        :rtype: spaces.Space
        """
        shape = {"health_status": spaces.Discrete(6)}
        if self.files:
            shape["FILES"] = spaces.Dict({i + 1: f.space for i, f in enumerate(self.files)})
        return spaces.Dict(shape)

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = []) -> FolderObservation:
        """
        Create a folder observation from a configuration schema.

        :param config: Configuration schema containing the necessary information for the folder observation.
        :type config: ConfigSchema
        :param parent_where: Where in the simulation state dictionary to find the information about this folder's
            parent node. A typical location for a node might be ['network', 'nodes', <node_hostname>].
        :type parent_where: WhereType, optional
        :return: Constructed folder observation instance.
        :rtype: FolderObservation
        """
        where = parent_where + ["file_system", "folders", config.folder_name]

        # pass down shared/common config items
        for file_config in config.files:
            file_config.include_num_access = config.include_num_access
            file_config.file_system_requires_scan = config.file_system_requires_scan

        files = [FileObservation.from_config(config=f, parent_where=where) for f in config.files]
        return cls(
            where=where,
            files=files,
            num_files=config.num_files,
            include_num_access=config.include_num_access,
            file_system_requires_scan=config.file_system_requires_scan,
        )
