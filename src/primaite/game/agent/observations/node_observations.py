from __future__ import annotations

from ipaddress import IPv4Address
from typing import Any, Dict, Iterable, List, Optional

from gymnasium import spaces
from gymnasium.core import ObsType

from primaite import getLogger
from primaite.game.agent.observations.observations import AbstractObservation
from primaite.game.agent.utils import access_from_nested_dict, NOT_PRESENT_IN_STATE

_LOGGER = getLogger(__name__)

WhereType = Iterable[str | int] | None


class ServiceObservation(AbstractObservation, identifier="SERVICE"):
    """Service observation, shows status of a service in the simulation environment."""

    class ConfigSchema(AbstractObservation.ConfigSchema):
        """Configuration schema for ServiceObservation."""

        service_name: str
        """Name of the service, used for querying simulation state dictionary"""

    def __init__(self, where: WhereType) -> None:
        """
        Initialize a service observation instance.

        :param where: Where in the simulation state dictionary to find the relevant information for this service.
            A typical location for a service might be ['network', 'nodes', <node_hostname>, 'services', <service_name>].
        :type where: WhereType
        """
        self.where = where
        self.default_observation = {"operating_status": 0, "health_status": 0}

    def observe(self, state: Dict) -> ObsType:
        """
        Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary.
        :type state: Dict
        :return: Observation containing the operating status and health status of the service.
        :rtype: Any
        """
        service_state = access_from_nested_dict(state, self.where)
        if service_state is NOT_PRESENT_IN_STATE:
            return self.default_observation
        return {
            "operating_status": service_state["operating_state"],
            "health_status": service_state["health_state_visible"],
        }

    @property
    def space(self) -> spaces.Space:
        """
        Gymnasium space object describing the observation space shape.

        :return: Gymnasium space representing the observation space for service status.
        :rtype: spaces.Space
        """
        return spaces.Dict({"operating_status": spaces.Discrete(7), "health_status": spaces.Discrete(5)})

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = []) -> ServiceObservation:
        """
        Create a service observation from a configuration schema.

        :param config: Configuration schema containing the necessary information for the service observation.
        :type config: ConfigSchema
        :param parent_where: Where in the simulation state dictionary to find the information about this service's
            parent node. A typical location for a node might be ['network', 'nodes', <node_hostname>].
        :type parent_where: WhereType, optional
        :return: Constructed service observation instance.
        :rtype: ServiceObservation
        """
        return cls(where=parent_where + ["services", config.service_name])


class ApplicationObservation(AbstractObservation, identifier="APPLICATION"):
    """Application observation, shows the status of an application within the simulation environment."""

    class ConfigSchema(AbstractObservation.ConfigSchema):
        """Configuration schema for ApplicationObservation."""

        application_name: str
        """Name of the application, used for querying simulation state dictionary"""

    def __init__(self, where: WhereType) -> None:
        """
        Initialise an application observation instance.

        :param where: Where in the simulation state dictionary to find the relevant information for this application.
            A typical location for an application might be
            ['network', 'nodes', <node_hostname>, 'applications', <application_name>].
        :type where: WhereType
        """
        self.where = where
        self.default_observation = {"operating_status": 0, "health_status": 0, "num_executions": 0}

    def observe(self, state: Dict) -> Any:
        """
        Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary.
        :type state: Dict
        :return: Obs containing the operating status, health status, and number of executions of the application.
        :rtype: Any
        """
        application_state = access_from_nested_dict(state, self.where)
        if application_state is NOT_PRESENT_IN_STATE:
            return self.default_observation
        return {
            "operating_status": application_state["operating_state"],
            "health_status": application_state["health_state_visible"],
            "num_executions": application_state["num_executions"],
        }

    @property
    def space(self) -> spaces.Space:
        """
        Gymnasium space object describing the observation space shape.

        :return: Gymnasium space representing the observation space for application status.
        :rtype: spaces.Space
        """
        return spaces.Dict(
            {
                "operating_status": spaces.Discrete(7),
                "health_status": spaces.Discrete(5),
                "num_executions": spaces.Discrete(4),
            }
        )

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = []) -> ApplicationObservation:
        """
        Create an application observation from a configuration schema.

        :param config: Configuration schema containing the necessary information for the application observation.
        :type config: ConfigSchema
        :param parent_where: Where in the simulation state dictionary to find the information about this application's
            parent node. A typical location for a node might be ['network', 'nodes', <node_hostname>].
        :type parent_where: WhereType, optional
        :return: Constructed application observation instance.
        :rtype: ApplicationObservation
        """
        return cls(where=parent_where + ["applications", config.application_name])


class FileObservation(AbstractObservation, identifier="FILE"):
    """File observation, provides status information about a file within the simulation environment."""

    class ConfigSchema(AbstractObservation.ConfigSchema):
        """Configuration schema for FileObservation."""

        file_name: str
        """Name of the file, used for querying simulation state dictionary."""
        include_num_access: Optional[bool] = None
        """Whether to include the number of accesses to the file in the observation."""

    def __init__(self, where: WhereType, include_num_access: bool) -> None:
        """
        Initialize a file observation instance.

        :param where: Where in the simulation state dictionary to find the relevant information for this file.
            A typical location for a file might be
            ['network', 'nodes', <node_hostname>, 'file_system', 'folder', <folder_name>, 'files', <file_name>].
        :type where: WhereType
        :param include_num_access: Whether to include the number of accesses to the file in the observation.
        :type include_num_access: bool
        """
        self.where: WhereType = where
        self.include_num_access: bool = include_num_access

        self.default_observation: ObsType = {"health_status": 0}
        if self.include_num_access:
            self.default_observation["num_access"] = 0

    def observe(self, state: Dict) -> Any:
        """
        Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary.
        :type state: Dict
        :return: Observation containing the health status of the file and optionally the number of accesses.
        :rtype: Any
        """
        file_state = access_from_nested_dict(state, self.where)
        if file_state is NOT_PRESENT_IN_STATE:
            return self.default_observation
        obs = {"health_status": file_state["visible_status"]}
        if self.include_num_access:
            obs["num_access"] = file_state["num_access"]
            # raise NotImplementedError("TODO: need to fix num_access to use thresholds instead of raw value.")
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
        """
        return cls(where=parent_where + ["files", config.file_name], include_num_access=config.include_num_access)


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

    def __init__(
        self, where: WhereType, files: Iterable[FileObservation], num_files: int, include_num_access: bool
    ) -> None:
        """
        Initialize a folder observation instance.

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

        self.files: List[FileObservation] = files
        while len(self.files) < num_files:
            self.files.append(FileObservation(where=None, include_num_access=include_num_access))
        while len(self.files) > num_files:
            truncated_file = self.files.pop()
            msg = f"Too many files in folder observation. Truncating file {truncated_file}"
            _LOGGER.warning(msg)

        self.default_observation = {
            "health_status": 0,
            "FILES": {i + 1: f.default_observation for i, f in enumerate(self.files)},
        }

    def observe(self, state: Dict) -> Any:
        """
        Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary.
        :type state: Dict
        :return: Observation containing the health status of the folder and status of files within the folder.
        :rtype: Any
        """
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
        """
        Gymnasium space object describing the observation space shape.

        :return: Gymnasium space representing the observation space for folder status.
        :rtype: spaces.Space
        """
        return spaces.Dict(
            {
                "health_status": spaces.Discrete(6),
                "FILES": spaces.Dict({i + 1: f.space for i, f in enumerate(self.files)}),
            }
        )

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
        where = parent_where + ["folders", config.folder_name]

        # pass down shared/common config items
        for file_config in config.files:
            file_config.include_num_access = config.include_num_access

        files = [FileObservation.from_config(config=f, parent_where=where) for f in config.files]
        return cls(where=where, files=files, num_files=config.num_files, include_num_access=config.include_num_access)


class NICObservation(AbstractObservation, identifier="NETWORK_INTERFACE"):
    """Status information about a network interface within the simulation environment."""

    class ConfigSchema(AbstractObservation.ConfigSchema):
        """Configuration schema for NICObservation."""

        nic_num: int
        """Number of the network interface."""
        include_nmne: Optional[bool] = None
        """Whether to include number of malicious network events (NMNE) in the observation."""

    def __init__(self, where: WhereType, include_nmne: bool) -> None:
        """
        Initialize a network interface observation instance.

        :param where: Where in the simulation state dictionary to find the relevant information for this interface.
            A typical location for a network interface might be
            ['network', 'nodes', <node_hostname>, 'NICs', <nic_num>].
        :type where: WhereType
        :param include_nmne: Flag to determine whether to include NMNE information in the observation.
        :type include_nmne: bool
        """
        self.where = where
        self.include_nmne: bool = include_nmne

        self.default_observation: ObsType = {"nic_status": 0}
        if self.include_nmne:
            self.default_observation.update({"NMNE": {"inbound": 0, "outbound": 0}})

    def observe(self, state: Dict) -> Any:
        """
        Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary.
        :type state: Dict
        :return: Observation containing the status of the network interface and optionally NMNE information.
        :rtype: Any
        """
        nic_state = access_from_nested_dict(state, self.where)

        if nic_state is NOT_PRESENT_IN_STATE:
            return self.default_observation

        obs = {"nic_status": 1 if nic_state["enabled"] else 2}
        if self.include_nmne:
            obs.update({"NMNE": {}})
            direction_dict = nic_state["nmne"].get("direction", {})
            inbound_keywords = direction_dict.get("inbound", {}).get("keywords", {})
            inbound_count = inbound_keywords.get("*", 0)
            outbound_keywords = direction_dict.get("outbound", {}).get("keywords", {})
            outbound_count = outbound_keywords.get("*", 0)
            obs["NMNE"]["inbound"] = self._categorise_mne_count(inbound_count - self.nmne_inbound_last_step)
            obs["NMNE"]["outbound"] = self._categorise_mne_count(outbound_count - self.nmne_outbound_last_step)
            self.nmne_inbound_last_step = inbound_count
            self.nmne_outbound_last_step = outbound_count
        return obs

    @property
    def space(self) -> spaces.Space:
        """
        Gymnasium space object describing the observation space shape.

        :return: Gymnasium space representing the observation space for network interface status and NMNE information.
        :rtype: spaces.Space
        """
        space = spaces.Dict({"nic_status": spaces.Discrete(3)})

        if self.include_nmne:
            space["NMNE"] = spaces.Dict({"inbound": spaces.Discrete(4), "outbound": spaces.Discrete(4)})

        return space

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = []) -> NICObservation:
        """
        Create a network interface observation from a configuration schema.

        :param config: Configuration schema containing the necessary information for the network interface observation.
        :type config: ConfigSchema
        :param parent_where: Where in the simulation state dictionary to find the information about this NIC's
            parent node. A typical location for a node might be ['network', 'nodes', <node_hostname>].
        :type parent_where: WhereType, optional
        :return: Constructed network interface observation instance.
        :rtype: NICObservation
        """
        return cls(where=parent_where + ["NICs", config.nic_num], include_nmne=config.include_nmne)


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
        Initialize a host observation instance.

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

        self.network_interfaces: List[NICObservation] = network_interfaces
        while len(self.network_interfaces) < num_nics:
            self.network_interfaces.append(NICObservation(where=None, include_nmne=include_nmne))
        while len(self.network_interfaces) > num_nics:
            truncated_nic = self.network_interfaces.pop()
            msg = f"Too many network_interfaces in Node observation space for node. Truncating {truncated_nic.where}"
            _LOGGER.warning(msg)

        self.default_observation: ObsType = {
            "SERVICES": {i + 1: s.default_observation for i, s in enumerate(self.services)},
            "APPLICATIONS": {i + 1: a.default_observation for i, a in enumerate(self.applications)},
            "FOLDERS": {i + 1: f.default_observation for i, f in enumerate(self.folders)},
            "NICS": {i + 1: n.default_observation for i, n in enumerate(self.network_interfaces)},
            "operating_status": 0,
            "num_file_creations": 0,
            "num_file_deletions": 0,
        }

    def observe(self, state: Dict) -> Any:
        """
        Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary.
        :type state: Dict
        :return: Observation containing the status information about the host.
        :rtype: Any
        """
        node_state = access_from_nested_dict(state, self.where)
        if node_state is NOT_PRESENT_IN_STATE:
            return self.default_observation

        obs = {}
        obs["SERVICES"] = {i + 1: service.observe(state) for i, service in enumerate(self.services)}
        obs["APPLICATIONS"] = {i + 1: app.observe(state) for i, app in enumerate(self.applications)}
        obs["FOLDERS"] = {i + 1: folder.observe(state) for i, folder in enumerate(self.folders)}
        obs["operating_status"] = node_state["operating_state"]
        obs["NICS"] = {
            i + 1: network_interface.observe(state) for i, network_interface in enumerate(self.network_interfaces)
        }
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
            "SERVICES": spaces.Dict({i + 1: service.space for i, service in enumerate(self.services)}),
            "APPLICATIONS": spaces.Dict({i + 1: app.space for i, app in enumerate(self.applications)}),
            "FOLDERS": spaces.Dict({i + 1: folder.space for i, folder in enumerate(self.folders)}),
            "operating_status": spaces.Discrete(5),
            "NICS": spaces.Dict(
                {i + 1: network_interface.space for i, network_interface in enumerate(self.network_interfaces)}
            ),
            "num_file_creations": spaces.Discrete(4),
            "num_file_deletions": spaces.Discrete(4),
        }
        return spaces.Dict(shape)

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = None) -> HostObservation:
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
        if parent_where is None:
            where = ["network", "nodes", config.hostname]
        else:
            where = parent_where + ["nodes", config.hostname]

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


class PortObservation(AbstractObservation, identifier="PORT"):
    """Port observation, provides status information about a network port within the simulation environment."""

    class ConfigSchema(AbstractObservation.ConfigSchema):
        """Configuration schema for PortObservation."""

        port_id: int
        """Identifier of the port, used for querying simulation state dictionary."""

    def __init__(self, where: WhereType) -> None:
        """
        Initialize a port observation instance.

        :param where: Where in the simulation state dictionary to find the relevant information for this port.
            A typical location for a port might be ['network', 'nodes', <node_hostname>, 'NICs', <port_id>].
        :type where: WhereType
        """
        self.where = where
        self.default_observation: ObsType = {"operating_status": 0}

    def observe(self, state: Dict) -> Any:
        """
        Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary.
        :type state: Dict
        :return: Observation containing the operating status of the port.
        :rtype: Any
        """
        port_state = access_from_nested_dict(state, self.where)
        if port_state is NOT_PRESENT_IN_STATE:
            return self.default_observation
        return {"operating_status": 1 if port_state["enabled"] else 2}

    @property
    def space(self) -> spaces.Space:
        """
        Gymnasium space object describing the observation space shape.

        :return: Gymnasium space representing the observation space for port status.
        :rtype: spaces.Space
        """
        return spaces.Dict({"operating_status": spaces.Discrete(3)})

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = []) -> PortObservation:
        """
        Create a port observation from a configuration schema.

        :param config: Configuration schema containing the necessary information for the port observation.
        :type config: ConfigSchema
        :param parent_where: Where in the simulation state dictionary to find the information about this port's
            parent node. A typical location for a node might be ['network', 'nodes', <node_hostname>].
        :type parent_where: WhereType, optional
        :return: Constructed port observation instance.
        :rtype: PortObservation
        """
        return cls(where=parent_where + ["NICs", config.port_id])


class ACLObservation(AbstractObservation, identifier="ACL"):
    """ACL observation, provides information about access control lists within the simulation environment."""

    class ConfigSchema(AbstractObservation.ConfigSchema):
        """Configuration schema for ACLObservation."""

        ip_list: Optional[List[IPv4Address]] = None
        """List of IP addresses."""
        wildcard_list: Optional[List[str]] = None
        """List of wildcard strings."""
        port_list: Optional[List[int]] = None
        """List of port numbers."""
        protocol_list: Optional[List[str]] = None
        """List of protocol names."""
        num_rules: Optional[int] = None
        """Number of ACL rules."""

    def __init__(
        self,
        where: WhereType,
        num_rules: int,
        ip_list: List[IPv4Address],
        wildcard_list: List[str],
        port_list: List[int],
        protocol_list: List[str],
    ) -> None:
        """
        Initialize an ACL observation instance.

        :param where: Where in the simulation state dictionary to find the relevant information for this ACL.
        :type where: WhereType
        :param num_rules: Number of ACL rules.
        :type num_rules: int
        :param ip_list: List of IP addresses.
        :type ip_list: List[IPv4Address]
        :param wildcard_list: List of wildcard strings.
        :type wildcard_list: List[str]
        :param port_list: List of port numbers.
        :type port_list: List[int]
        :param protocol_list: List of protocol names.
        :type protocol_list: List[str]
        """
        self.where = where
        self.num_rules: int = num_rules
        self.ip_to_id: Dict[str, int] = {i + 2: p for i, p in enumerate(ip_list)}
        self.wildcard_to_id: Dict[str, int] = {i + 2: p for i, p in enumerate(wildcard_list)}
        self.port_to_id: Dict[int, int] = {i + 2: p for i, p in enumerate(port_list)}
        self.protocol_to_id: Dict[str, int] = {i + 2: p for i, p in enumerate(protocol_list)}
        self.default_observation: Dict = {
            i
            + 1: {
                "position": i,
                "permission": 0,
                "source_ip_id": 0,
                "source_wildcard_id": 0,
                "source_port_id": 0,
                "dest_ip_id": 0,
                "dest_wildcard_id": 0,
                "dest_port_id": 0,
                "protocol_id": 0,
            }
            for i in range(self.num_rules)
        }

    def observe(self, state: Dict) -> Any:
        """
        Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary.
        :type state: Dict
        :return: Observation containing ACL rules.
        :rtype: Any
        """
        acl_state: Dict = access_from_nested_dict(state, self.where)
        if acl_state is NOT_PRESENT_IN_STATE:
            return self.default_observation
        obs = {}
        acl_items = dict(acl_state.items())
        i = 1  # don't show rule 0 for compatibility reasons.
        while i < self.num_rules + 1:
            rule_state = acl_items[i]
            if rule_state is None:
                obs[i] = {
                    "position": i - 1,
                    "permission": 0,
                    "source_ip_id": 0,
                    "source_wildcard_id": 0,
                    "source_port_id": 0,
                    "dest_ip_id": 0,
                    "dest_wildcard_id": 0,
                    "dest_port_id": 0,
                    "protocol_id": 0,
                }
            else:
                src_ip = rule_state["src_ip_address"]
                src_node_id = self.ip_to_id.get(src_ip, 1)
                dst_ip = rule_state["dst_ip_address"]
                dst_node_ip = self.ip_to_id.get(dst_ip, 1)
                src_wildcard = rule_state["source_wildcard_id"]
                src_wildcard_id = self.wildcard_to_id.get(src_wildcard, 1)
                dst_wildcard = rule_state["dest_wildcard_id"]
                dst_wildcard_id = self.wildcard_to_id.get(dst_wildcard, 1)
                src_port = rule_state["source_port_id"]
                src_port_id = self.port_to_id.get(src_port, 1)
                dst_port = rule_state["dest_port_id"]
                dst_port_id = self.port_to_id.get(dst_port, 1)
                protocol = rule_state["protocol"]
                protocol_id = self.protocol_to_id.get(protocol, 1)
                obs[i] = {
                    "position": i - 1,
                    "permission": rule_state["action"],
                    "source_ip_id": src_node_id,
                    "source_wildcard_id": src_wildcard_id,
                    "source_port_id": src_port_id,
                    "dest_ip_id": dst_node_ip,
                    "dest_wildcard_id": dst_wildcard_id,
                    "dest_port_id": dst_port_id,
                    "protocol_id": protocol_id,
                }
            i += 1
        return obs

    @property
    def space(self) -> spaces.Space:
        """
        Gymnasium space object describing the observation space shape.

        :return: Gymnasium space representing the observation space for ACL rules.
        :rtype: spaces.Space
        """
        return spaces.Dict(
            {
                i
                + 1: spaces.Dict(
                    {
                        "position": spaces.Discrete(self.num_rules),
                        "permission": spaces.Discrete(3),
                        # adding two to lengths is to account for reserved values 0 (unused) and 1 (any)
                        "source_ip_id": spaces.Discrete(len(self.ip_to_id) + 2),
                        "source_wildcard_id": spaces.Discrete(len(self.wildcard_to_id) + 2),
                        "source_port_id": spaces.Discrete(len(self.port_to_id) + 2),
                        "dest_ip_id": spaces.Discrete(len(self.ip_to_id) + 2),
                        "dest_wildcard_id": spaces.Discrete(len(self.wildcard_to_id) + 2),
                        "dest_port_id": spaces.Discrete(len(self.port_to_id) + 2),
                        "protocol_id": spaces.Discrete(len(self.protocol_to_id) + 2),
                    }
                )
                for i in range(self.num_rules)
            }
        )

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = []) -> ACLObservation:
        """
        Create an ACL observation from a configuration schema.

        :param config: Configuration schema containing the necessary information for the ACL observation.
        :type config: ConfigSchema
        :param parent_where: Where in the simulation state dictionary to find the information about this ACL's
            parent node. A typical location for a node might be ['network', 'nodes', <node_hostname>].
        :type parent_where: WhereType, optional
        :return: Constructed ACL observation instance.
        :rtype: ACLObservation
        """
        return cls(
            where=parent_where + ["acl", "acl"],
            num_rules=config.num_rules,
            ip_list=config.ip_list,
            wildcard_list=config.wildcard_list,
            port_list=config.port_list,
            protocol_list=config.protocol_list,
        )


class RouterObservation(AbstractObservation, identifier="ROUTER"):
    """Router observation, provides status information about a router within the simulation environment."""

    class ConfigSchema(AbstractObservation.ConfigSchema):
        """Configuration schema for RouterObservation."""

        hostname: str
        """Hostname of the router, used for querying simulation state dictionary."""
        ports: Optional[List[PortObservation.ConfigSchema]] = None
        """Configuration of port observations for this router."""
        num_ports: Optional[int] = None
        """Number of port observations configured for this router."""
        acl: Optional[ACLObservation.ConfigSchema] = None
        """Configuration of ACL observation on this router."""
        ip_list: Optional[List[str]] = None
        """List of IP addresses for encoding ACLs."""
        wildcard_list: Optional[List[str]] = None
        """List of IP wildcards for encoding ACLs."""
        port_list: Optional[List[int]] = None
        """List of ports for encoding ACLs."""
        protocol_list: Optional[List[str]] = None
        """List of protocols for encoding ACLs."""
        num_rules: Optional[int] = None
        """Number of rules ACL rules to show."""

    def __init__(
        self,
        where: WhereType,
        ports: List[PortObservation],
        num_ports: int,
        acl: ACLObservation,
    ) -> None:
        """
        Initialize a router observation instance.

        :param where: Where in the simulation state dictionary to find the relevant information for this router.
            A typical location for a router might be ['network', 'nodes', <node_hostname>].
        :type where: WhereType
        :param ports: List of port observations representing the ports of the router.
        :type ports: List[PortObservation]
        :param num_ports: Number of ports for the router.
        :type num_ports: int
        :param acl: ACL observation representing the access control list of the router.
        :type acl: ACLObservation
        """
        self.where: WhereType = where
        self.ports: List[PortObservation] = ports
        self.acl: ACLObservation = acl
        self.num_ports: int = num_ports

        while len(self.ports) < num_ports:
            self.ports.append(PortObservation(where=None))
        while len(self.ports) > num_ports:
            self.ports.pop()
            msg = "Too many ports in router observation. Truncating."
            _LOGGER.warning(msg)

        self.default_observation = {
            "PORTS": {i + 1: p.default_observation for i, p in enumerate(self.ports)},
            "ACL": self.acl.default_observation,
        }

    def observe(self, state: Dict) -> Any:
        """
        Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary.
        :type state: Dict
        :return: Observation containing the status of ports and ACL configuration of the router.
        :rtype: Any
        """
        router_state = access_from_nested_dict(state, self.where)
        if router_state is NOT_PRESENT_IN_STATE:
            return self.default_observation

        obs = {}
        obs["PORTS"] = {i + 1: p.observe(state) for i, p in enumerate(self.ports)}
        obs["ACL"] = self.acl.observe(state)
        return obs

    @property
    def space(self) -> spaces.Space:
        """
        Gymnasium space object describing the observation space shape.

        :return: Gymnasium space representing the observation space for router status.
        :rtype: spaces.Space
        """
        return spaces.Dict(
            {"PORTS": spaces.Dict({i + 1: p.space for i, p in enumerate(self.ports)}), "ACL": self.acl.space}
        )

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = []) -> RouterObservation:
        """
        Create a router observation from a configuration schema.

        :param config: Configuration schema containing the necessary information for the router observation.
        :type config: ConfigSchema
        :param parent_where: Where in the simulation state dictionary to find the information about this router's
            parent node. A typical location for a node might be ['network', 'nodes', <node_hostname>].
        :type parent_where: WhereType, optional
        :return: Constructed router observation instance.
        :rtype: RouterObservation
        """
        where = parent_where + ["nodes", config.hostname]

        if config.acl is None:
            config.acl = ACLObservation.ConfigSchema()
        if config.acl.num_rules is None:
            config.acl.num_rules = config.num_rules
        if config.acl.ip_list is None:
            config.acl.ip_list = config.ip_list
        if config.acl.wildcard_list is None:
            config.acl.wildcard_list = config.wildcard_list
        if config.acl.port_list is None:
            config.acl.port_list = config.port_list
        if config.acl.protocol_list is None:
            config.acl.protocol_list = config.protocol_list

        if config.ports is None:
            config.ports = [PortObservation.ConfigSchema(port_id=i + 1) for i in range(config.num_ports)]

        ports = [PortObservation.from_config(config=c, parent_where=where) for c in config.ports]
        acl = ACLObservation.from_config(config=config.acl, parent_where=where)
        return cls(where=where, ports=ports, num_ports=config.num_ports, acl=acl)


class FirewallObservation(AbstractObservation, identifier="FIREWALL"):
    """Firewall observation, provides status information about a firewall within the simulation environment."""

    class ConfigSchema(AbstractObservation.ConfigSchema):
        """Configuration schema for FirewallObservation."""

        hostname: str
        """Hostname of the firewall node, used for querying simulation state dictionary."""
        ip_list: Optional[List[str]] = None
        """List of IP addresses for encoding ACLs."""
        wildcard_list: Optional[List[str]] = None
        """List of IP wildcards for encoding ACLs."""
        port_list: Optional[List[int]] = None
        """List of ports for encoding ACLs."""
        protocol_list: Optional[List[str]] = None
        """List of protocols for encoding ACLs."""
        num_rules: Optional[int] = None
        """Number of rules ACL rules to show."""

    def __init__(
        self,
        where: WhereType,
        ip_list: List[str],
        wildcard_list: List[str],
        port_list: List[int],
        protocol_list: List[str],
        num_rules: int,
    ) -> None:
        """
        Initialize a firewall observation instance.

        :param where: Where in the simulation state dictionary to find the relevant information for this firewall.
            A typical location for a firewall might be ['network', 'nodes', <firewall_hostname>].
        :type where: WhereType
        :param ip_list: List of IP addresses.
        :type ip_list: List[str]
        :param wildcard_list: List of wildcard rules.
        :type wildcard_list: List[str]
        :param port_list: List of port numbers.
        :type port_list: List[int]
        :param protocol_list: List of protocol types.
        :type protocol_list: List[str]
        :param num_rules: Number of rules configured in the firewall.
        :type num_rules: int
        """
        self.where: WhereType = where

        self.ports: List[PortObservation] = [
            PortObservation(where=self.where + ["port", port_num]) for port_num in (1, 2, 3)
        ]
        # TODO: check what the port nums are for firewall.

        self.internal_inbound_acl = ACLObservation(
            where=self.where + ["acl", "internal", "inbound"],
            num_rules=num_rules,
            ip_list=ip_list,
            wildcard_list=wildcard_list,
            port_list=port_list,
            protocol_list=protocol_list,
        )
        self.internal_outbound_acl = ACLObservation(
            where=self.where + ["acl", "internal", "outbound"],
            num_rules=num_rules,
            ip_list=ip_list,
            wildcard_list=wildcard_list,
            port_list=port_list,
            protocol_list=protocol_list,
        )
        self.dmz_inbound_acl = ACLObservation(
            where=self.where + ["acl", "dmz", "inbound"],
            num_rules=num_rules,
            ip_list=ip_list,
            wildcard_list=wildcard_list,
            port_list=port_list,
            protocol_list=protocol_list,
        )
        self.dmz_outbound_acl = ACLObservation(
            where=self.where + ["acl", "dmz", "outbound"],
            num_rules=num_rules,
            ip_list=ip_list,
            wildcard_list=wildcard_list,
            port_list=port_list,
            protocol_list=protocol_list,
        )
        self.external_inbound_acl = ACLObservation(
            where=self.where + ["acl", "external", "inbound"],
            num_rules=num_rules,
            ip_list=ip_list,
            wildcard_list=wildcard_list,
            port_list=port_list,
            protocol_list=protocol_list,
        )
        self.external_outbound_acl = ACLObservation(
            where=self.where + ["acl", "external", "outbound"],
            num_rules=num_rules,
            ip_list=ip_list,
            wildcard_list=wildcard_list,
            port_list=port_list,
            protocol_list=protocol_list,
        )

        self.default_observation = {
            "PORTS": {i + 1: p.default_observation for i, p in enumerate(self.ports)},
            "INTERNAL": {
                "INBOUND": self.internal_inbound_acl.default_observation,
                "OUTBOUND": self.internal_outbound_acl.default_observation,
            },
            "DMZ": {
                "INBOUND": self.dmz_inbound_acl.default_observation,
                "OUTBOUND": self.dmz_outbound_acl.default_observation,
            },
            "EXTERNAL": {
                "INBOUND": self.external_inbound_acl.default_observation,
                "OUTBOUND": self.external_outbound_acl.default_observation,
            },
        }

    def observe(self, state: Dict) -> Any:
        """
        Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary.
        :type state: Dict
        :return: Observation containing the status of ports and ACLs for internal, DMZ, and external traffic.
        :rtype: Any
        """
        obs = {
            "PORTS": {i + 1: p.observe(state) for i, p in enumerate(self.ports)},
            "INTERNAL": {
                "INBOUND": self.internal_inbound_acl.observe(state),
                "OUTBOUND": self.internal_outbound_acl.observe(state),
            },
            "DMZ": {
                "INBOUND": self.dmz_inbound_acl.observe(state),
                "OUTBOUND": self.dmz_outbound_acl.observe(state),
            },
            "EXTERNAL": {
                "INBOUND": self.external_inbound_acl.observe(state),
                "OUTBOUND": self.external_outbound_acl.observe(state),
            },
        }
        return obs

    @property
    def space(self) -> spaces.Space:
        """
        Gymnasium space object describing the observation space shape.

        :return: Gymnasium space representing the observation space for firewall status.
        :rtype: spaces.Space
        """
        space = spaces.Dict(
            {
                "PORTS": spaces.Dict({i + 1: p.space for i, p in enumerate(self.ports)}),
                "INTERNAL": spaces.Dict(
                    {
                        "INBOUND": self.internal_inbound_acl.space,
                        "OUTBOUND": self.internal_outbound_acl.space,
                    }
                ),
                "DMZ": spaces.Dict(
                    {
                        "INBOUND": self.dmz_inbound_acl.space,
                        "OUTBOUND": self.dmz_outbound_acl.space,
                    }
                ),
                "EXTERNAL": spaces.Dict(
                    {
                        "INBOUND": self.external_inbound_acl.space,
                        "OUTBOUND": self.external_outbound_acl.space,
                    }
                ),
            }
        )
        return space

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = []) -> FirewallObservation:
        """
        Create a firewall observation from a configuration schema.

        :param config: Configuration schema containing the necessary information for the firewall observation.
        :type config: ConfigSchema
        :param parent_where: Where in the simulation state dictionary to find the information about this firewall's
            parent node. A typical location for a node might be ['network', 'nodes', <firewall_hostname>].
        :type parent_where: WhereType, optional
        :return: Constructed firewall observation instance.
        :rtype: FirewallObservation
        """
        where = parent_where + ["nodes", config.hostname]
        return cls(
            where=where,
            ip_list=config.ip_list,
            wildcard_list=config.wildcard_list,
            port_list=config.port_list,
            protocol_list=config.protocol_list,
            num_rules=config.num_rules,
        )


class NodesObservation(AbstractObservation, identifier="NODES"):
    """Nodes observation, provides status information about nodes within the simulation environment."""

    class ConfigSchema(AbstractObservation.ConfigSchema):
        """Configuration schema for NodesObservation."""

        hosts: List[HostObservation.ConfigSchema] = []
        """List of configurations for host observations."""
        routers: List[RouterObservation.ConfigSchema] = []
        """List of configurations for router observations."""
        firewalls: List[FirewallObservation.ConfigSchema] = []
        """List of configurations for firewall observations."""
        num_services: int
        """Number of services."""
        num_applications: int
        """Number of applications."""
        num_folders: int
        """Number of folders."""
        num_files: int
        """Number of files."""
        num_nics: int
        """Number of network interface cards (NICs)."""
        include_nmne: bool
        """Flag to include nmne."""
        include_num_access: bool
        """Flag to include the number of accesses."""
        num_ports: int
        """Number of ports."""
        ip_list: List[str]
        """List of IP addresses for encoding ACLs."""
        wildcard_list: List[str]
        """List of IP wildcards for encoding ACLs."""
        port_list: List[int]
        """List of ports for encoding ACLs."""
        protocol_list: List[str]
        """List of protocols for encoding ACLs."""
        num_rules: int
        """Number of rules ACL rules to show."""

    def __init__(
        self,
        where: WhereType,
        hosts: List[HostObservation],
        routers: List[RouterObservation],
        firewalls: List[FirewallObservation],
    ) -> None:
        """
        Initialize a nodes observation instance.

        :param where: Where in the simulation state dictionary to find the relevant information for nodes.
            A typical location for nodes might be ['network', 'nodes'].
        :type where: WhereType
        :param hosts: List of host observations.
        :type hosts: List[HostObservation]
        :param routers: List of router observations.
        :type routers: List[RouterObservation]
        :param firewalls: List of firewall observations.
        :type firewalls: List[FirewallObservation]
        """
        self.where: WhereType = where

        self.hosts: List[HostObservation] = hosts
        self.routers: List[RouterObservation] = routers
        self.firewalls: List[FirewallObservation] = firewalls

        self.default_observation = {
            **{f"HOST{i}": host.default_observation for i, host in enumerate(self.hosts)},
            **{f"ROUTER{i}": router.default_observation for i, router in enumerate(self.routers)},
            **{f"FIREWALL{i}": firewall.default_observation for i, firewall in enumerate(self.firewalls)},
        }

    def observe(self, state: Dict) -> Any:
        """
        Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary.
        :type state: Dict
        :return: Observation containing status information about nodes.
        :rtype: Any
        """
        obs = {
            **{f"HOST{i}": host.observe(state) for i, host in enumerate(self.hosts)},
            **{f"ROUTER{i}": router.observe(state) for i, router in enumerate(self.routers)},
            **{f"FIREWALL{i}": firewall.observe(state) for i, firewall in enumerate(self.firewalls)},
        }
        return obs

    @property
    def space(self) -> spaces.Space:
        """
        Gymnasium space object describing the observation space shape.

        :return: Gymnasium space representing the observation space for nodes.
        :rtype: spaces.Space
        """
        space = spaces.Dict(
            {
                **{f"HOST{i}": host.space for i, host in enumerate(self.hosts)},
                **{f"ROUTER{i}": router.space for i, router in enumerate(self.routers)},
                **{f"FIREWALL{i}": firewall.space for i, firewall in enumerate(self.firewalls)},
            }
        )
        return space

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = []) -> ServiceObservation:
        """
        Create a nodes observation from a configuration schema.

        :param config: Configuration schema containing the necessary information for nodes observation.
        :type config: ConfigSchema
        :param parent_where: Where in the simulation state dictionary to find the information about nodes.
            A typical location for nodes might be ['network', 'nodes'].
        :type parent_where: WhereType, optional
        :return: Constructed nodes observation instance.
        :rtype: NodesObservation
        """
        if parent_where is None:
            where = ["network", "nodes"]
        else:
            where = parent_where + ["nodes"]

        for host_config in config.hosts:
            if host_config.num_services is None:
                host_config.num_services = config.num_services
            if host_config.num_applications is None:
                host_config.num_applications = config.num_applications
            if host_config.num_folders is None:
                host_config.num_folders = config.num_folders
            if host_config.num_files is None:
                host_config.num_files = config.num_files
            if host_config.num_nics is None:
                host_config.num_nics = config.num_nics
            if host_config.include_nmne is None:
                host_config.include_nmne = config.include_nmne
            if host_config.include_num_access is None:
                host_config.include_num_access = config.include_num_access

        for router_config in config.routers:
            if router_config.num_ports is None:
                router_config.num_ports = config.num_ports
            if router_config.ip_list is None:
                router_config.ip_list = config.ip_list
            if router_config.wildcard_list is None:
                router_config.wildcard_list = config.wildcard_list
            if router_config.port_list is None:
                router_config.port_list = config.port_list
            if router_config.protocol_list is None:
                router_config.protocol_list = config.protocol_list
            if router_config.num_rules is None:
                router_config.num_rules = config.num_rules

        for firewall_config in config.firewalls:
            if firewall_config.ip_list is None:
                firewall_config.ip_list = config.ip_list
            if firewall_config.wildcard_list is None:
                firewall_config.wildcard_list = config.wildcard_list
            if firewall_config.port_list is None:
                firewall_config.port_list = config.port_list
            if firewall_config.protocol_list is None:
                firewall_config.protocol_list = config.protocol_list
            if firewall_config.num_rules is None:
                firewall_config.num_rules = config.num_rules

        hosts = [HostObservation.from_config(config=c, parent_where=where) for c in config.hosts]
        routers = [RouterObservation.from_config(config=c, parent_where=where) for c in config.routers]
        firewalls = [FirewallObservation.from_config(config=c, parent_where=where) for c in config.firewalls]

        return cls(where=where, hosts=hosts, routers=routers, firewalls=firewalls)
