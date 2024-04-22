from __future__ import annotations

from typing import Dict, List, Optional

from gymnasium import spaces
from gymnasium.core import ObsType

from primaite import getLogger
from primaite.game.agent.observations.file_system_observations import FolderObservation
from primaite.game.agent.observations.nic_observations import NICObservation
from primaite.game.agent.observations.observations import AbstractObservation, WhereType
from primaite.game.agent.observations.software_observation import ApplicationObservation, ServiceObservation
from primaite.game.agent.utils import access_from_nested_dict, NOT_PRESENT_IN_STATE

_LOGGER = getLogger(__name__)


class HostObservation(AbstractObservation, identifier="HOST"):
    """Host observation, provides status information about a host within the simulation environment."""

    class ConfigSchema(AbstractObservation.ConfigSchema):
        """Configuration schema for HostObservation."""

        hostname: str
        """Hostname of the host, used for querying simulation state dictionary."""
        services: List[ServiceObservation.ConfigSchema] = []
        """List of services to observe on the host."""
        applications: List[ApplicationObservation.ConfigSchema] = []
        """List of applications to observe on the host."""
        folders: List[FolderObservation.ConfigSchema] = []
        """List of folders to observe on the host."""
        network_interfaces: List[NICObservation.ConfigSchema] = []
        """List of network interfaces to observe on the host."""
        num_services: Optional[int] = None
        """Number of spaces for service observations on this host."""
        num_applications: Optional[int] = None
        """Number of spaces for application observations on this host."""
        num_folders: Optional[int] = None
        """Number of spaces for folder observations on this host."""
        num_files: Optional[int] = None
        """Number of spaces for file observations on this host."""
        num_nics: Optional[int] = None
        """Number of spaces for network interface observations on this host."""
        include_nmne: Optional[bool] = None
        """Whether network interface observations should include number of malicious network events."""
        include_num_access: Optional[bool] = None
        """Whether to include the number of accesses to files observations on this host."""

    def __init__(
        self,
        where: WhereType,
        services: List[ServiceObservation],
        applications: List[ApplicationObservation],
        folders: List[FolderObservation],
        network_interfaces: List[NICObservation],
        num_services: int,
        num_applications: int,
        num_folders: int,
        num_files: int,
        num_nics: int,
        include_nmne: bool,
        include_num_access: bool,
    ) -> None:
        """
        Initialise a host observation instance.

        :param where: Where in the simulation state dictionary to find the relevant information for this host.
            A typical location for a host might be ['network', 'nodes', <hostname>].
        :type where: WhereType
        :param services: List of service observations on the host.
        :type services: List[ServiceObservation]
        :param applications: List of application observations on the host.
        :type applications: List[ApplicationObservation]
        :param folders: List of folder observations on the host.
        :type folders: List[FolderObservation]
        :param network_interfaces: List of network interface observations on the host.
        :type network_interfaces: List[NICObservation]
        :param num_services: Number of services to observe.
        :type num_services: int
        :param num_applications: Number of applications to observe.
        :type num_applications: int
        :param num_folders: Number of folders to observe.
        :type num_folders: int
        :param num_files: Number of files.
        :type num_files: int
        :param num_nics: Number of network interfaces.
        :type num_nics: int
        :param include_nmne: Flag to include network metrics and errors.
        :type include_nmne: bool
        :param include_num_access: Flag to include the number of accesses to files.
        :type include_num_access: bool
        """
        self.where: WhereType = where

        self.include_num_access = include_num_access

        # Ensure lists have lengths equal to specified counts by truncating or padding
        self.services: List[ServiceObservation] = services
        while len(self.services) < num_services:
            self.services.append(ServiceObservation(where=None))
        while len(self.services) > num_services:
            truncated_service = self.services.pop()
            msg = f"Too many services in Node observation space for node. Truncating service {truncated_service.where}"
            _LOGGER.warning(msg)

        self.applications: List[ApplicationObservation] = applications
        while len(self.applications) < num_applications:
            self.applications.append(ApplicationObservation(where=None))
        while len(self.applications) > num_applications:
            truncated_application = self.applications.pop()
            msg = f"Too many applications in Node observation space for node. Truncating {truncated_application.where}"
            _LOGGER.warning(msg)

        self.folders: List[FolderObservation] = folders
        while len(self.folders) < num_folders:
            self.folders.append(
                FolderObservation(where=None, files=[], num_files=num_files, include_num_access=include_num_access)
            )
        while len(self.folders) > num_folders:
            truncated_folder = self.folders.pop()
            msg = f"Too many folders in Node observation space for node. Truncating folder {truncated_folder.where}"
            _LOGGER.warning(msg)

        self.nics: List[NICObservation] = network_interfaces
        while len(self.nics) < num_nics:
            self.nics.append(NICObservation(where=None, include_nmne=include_nmne))
        while len(self.nics) > num_nics:
            truncated_nic = self.nics.pop()
            msg = f"Too many network_interfaces in Node observation space for node. Truncating {truncated_nic.where}"
            _LOGGER.warning(msg)

        self.default_observation: ObsType = {
            "operating_status": 0,
        }
        if self.services:
            self.default_observation["SERVICES"] = {i + 1: s.default_observation for i, s in enumerate(self.services)}
        if self.applications:
            self.default_observation["APPLICATIONS"] = {
                i + 1: a.default_observation for i, a in enumerate(self.applications)
            }
        if self.folders:
            self.default_observation["FOLDERS"] = {i + 1: f.default_observation for i, f in enumerate(self.folders)}
        if self.nics:
            self.default_observation["NICS"] = {i + 1: n.default_observation for i, n in enumerate(self.nics)}
        if self.include_num_access:
            self.default_observation["num_file_creations"] = 0
            self.default_observation["num_file_deletions"] = 0

    def observe(self, state: Dict) -> ObsType:
        """
        Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary.
        :type state: Dict
        :return: Observation containing the status information about the host.
        :rtype: ObsType
        """
        node_state = access_from_nested_dict(state, self.where)
        if node_state is NOT_PRESENT_IN_STATE:
            return self.default_observation

        obs = {}
        obs["operating_status"] = node_state["operating_state"]
        if self.services:
            obs["SERVICES"] = {i + 1: service.observe(state) for i, service in enumerate(self.services)}
        if self.applications:
            obs["APPLICATIONS"] = {i + 1: app.observe(state) for i, app in enumerate(self.applications)}
        if self.folders:
            obs["FOLDERS"] = {i + 1: folder.observe(state) for i, folder in enumerate(self.folders)}
        if self.nics:
            obs["NICS"] = {i + 1: nic.observe(state) for i, nic in enumerate(self.nics)}
        if self.include_num_access:
            obs["num_file_creations"] = node_state["file_system"]["num_file_creations"]
            obs["num_file_deletions"] = node_state["file_system"]["num_file_deletions"]
        return obs

    @property
    def space(self) -> spaces.Space:
        """
        Gymnasium space object describing the observation space shape.

        :return: Gymnasium space representing the observation space for host status.
        :rtype: spaces.Space
        """
        shape = {
            "operating_status": spaces.Discrete(5),
        }
        if self.services:
            shape["SERVICES"] = spaces.Dict({i + 1: service.space for i, service in enumerate(self.services)})
        if self.applications:
            shape["APPLICATIONS"] = spaces.Dict({i + 1: app.space for i, app in enumerate(self.applications)})
        if self.folders:
            shape["FOLDERS"] = spaces.Dict({i + 1: folder.space for i, folder in enumerate(self.folders)})
        if self.nics:
            shape["NICS"] = spaces.Dict({i + 1: nic.space for i, nic in enumerate(self.nics)})
        if self.include_num_access:
            shape["num_file_creations"] = spaces.Discrete(4)
            shape["num_file_deletions"] = spaces.Discrete(4)
        return spaces.Dict(shape)

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = []) -> HostObservation:
        """
        Create a host observation from a configuration schema.

        :param config: Configuration schema containing the necessary information for the host observation.
        :type config: ConfigSchema
        :param parent_where: Where in the simulation state dictionary to find the information about this host.
            A typical location might be ['network', 'nodes', <hostname>].
        :type parent_where: WhereType, optional
        :return: Constructed host observation instance.
        :rtype: HostObservation
        """
        if parent_where == []:
            where = ["network", "nodes", config.hostname]
        else:
            where = parent_where + [config.hostname]

        # Pass down shared/common config items
        for folder_config in config.folders:
            folder_config.include_num_access = config.include_num_access
            folder_config.num_files = config.num_files
        for nic_config in config.network_interfaces:
            nic_config.include_nmne = config.include_nmne

        services = [ServiceObservation.from_config(config=c, parent_where=where) for c in config.services]
        applications = [ApplicationObservation.from_config(config=c, parent_where=where) for c in config.applications]
        folders = [FolderObservation.from_config(config=c, parent_where=where) for c in config.folders]
        nics = [NICObservation.from_config(config=c, parent_where=where) for c in config.network_interfaces]
        # If list of network interfaces is not defined, assume we want to
        # monitor the first N interfaces. Network interface numbering starts at 1.
        count = 1
        while len(nics) < config.num_nics:
            nic_config = NICObservation.ConfigSchema(nic_num=count, include_nmne=config.include_nmne)
            nics.append(NICObservation.from_config(config=nic_config, parent_where=where))
            count += 1

        return cls(
            where=where,
            services=services,
            applications=applications,
            folders=folders,
            network_interfaces=nics,
            num_services=config.num_services,
            num_applications=config.num_applications,
            num_folders=config.num_folders,
            num_files=config.num_files,
            num_nics=config.num_nics,
            include_nmne=config.include_nmne,
            include_num_access=config.include_num_access,
        )
