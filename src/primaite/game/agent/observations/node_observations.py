from __future__ import annotations
from typing import Any, Dict, Iterable, List, Literal, Optional, Tuple, TYPE_CHECKING, Union

from gymnasium import spaces
from gymnasium.core import ObsType
from pydantic import BaseModel, ConfigDict

from primaite import getLogger
from primaite.game.agent.observations.observations import AbstractObservation
# from primaite.game.agent.observations.file_system_observations import FolderObservation
# from primaite.game.agent.observations.nic_observations import NicObservation
# from primaite.game.agent.observations.software_observation import ServiceObservation
from primaite.game.agent.utils import access_from_nested_dict, NOT_PRESENT_IN_STATE

_LOGGER = getLogger(__name__)

WhereType = Iterable[str | int] | None


class ServiceObservation(AbstractObservation, identifier="SERVICE"):
    class ConfigSchema(AbstractObservation.ConfigSchema):
        service_name: str

    def __init__(self, where: WhereType)->None:
        self.where = where
        self.default_observation = {"operating_status": 0, "health_status": 0}

    def observe(self, state: Dict) -> Any:
        service_state = access_from_nested_dict(state, self.where)
        if service_state is NOT_PRESENT_IN_STATE:
            return self.default_observation
        return {
            "operating_status": service_state["operating_state"],
            "health_status": service_state["health_state_visible"],
        }

    @property
    def space(self) -> spaces.Space:
        """Gymnasium space object describing the observation space shape."""
        return spaces.Dict({"operating_status": spaces.Discrete(7), "health_status": spaces.Discrete(5)})

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = [] ) -> ServiceObservation:
        return cls(where=parent_where+["services", config.service_name])


class ApplicationObservation(AbstractObservation, identifier="APPLICATION"):
    class ConfigSchema(AbstractObservation.ConfigSchema):
        application_name: str

    def __init__(self, where: WhereType)->None:
        self.where = where
        self.default_observation = {"operating_status": 0, "health_status": 0, "num_executions": 0}

    def observe(self, state: Dict) -> Any:
        # raise NotImplementedError("TODO NUM EXECUTIONS NEEDS TO BE CONVERTED TO A CATEGORICAL")
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
        """Gymnasium space object describing the observation space shape."""
        return spaces.Dict({
            "operating_status": spaces.Discrete(7),
            "health_status": spaces.Discrete(5),
            "num_executions": spaces.Discrete(4)
            })

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = [] ) -> ApplicationObservation:
        return cls(where=parent_where+["applications", config.application_name])


class FileObservation(AbstractObservation, identifier="FILE"):
    class ConfigSchema(AbstractObservation.ConfigSchema):
        file_name: str
        include_num_access : bool = False

    def __init__(self, where: WhereType, include_num_access: bool)->None:
        self.where: WhereType = where
        self.include_num_access :bool = include_num_access

        self.default_observation: ObsType = {"health_status": 0}
        if self.include_num_access:
            self.default_observation["num_access"] = 0

    def observe(self, state: Dict) -> Any:
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
        space = {"health_status": spaces.Discrete(6)}
        if self.include_num_access:
            space["num_access"] = spaces.Discrete(4)
        return spaces.Dict(space)

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = [] ) -> FileObservation:
        return cls(where=parent_where+["files", config.file_name], include_num_access=config.include_num_access)


class FolderObservation(AbstractObservation, identifier="FOLDER"):
    class ConfigSchema(AbstractObservation.ConfigSchema):
        folder_name: str
        files: List[FileObservation.ConfigSchema] = []
        num_files : int = 0
        include_num_access : bool = False

    def __init__(self, where: WhereType, files: Iterable[FileObservation], num_files: int, include_num_access: bool)->None:
        self.where: WhereType = where

        self.files: List[FileObservation] = files
        while len(self.files) < num_files:
            self.files.append(FileObservation(where=None,include_num_access=include_num_access))
        while len(self.files) > num_files:
            truncated_file = self.files.pop()
            msg = f"Too many files in folder observation. Truncating file {truncated_file}"
            _LOGGER.warning(msg)

        self.default_observation = {
            "health_status": 0,
            "FILES": {i + 1: f.default_observation for i, f in enumerate(self.files)},
        }

    def observe(self, state: Dict) -> Any:
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
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = [] ) -> FileObservation:
        where = parent_where + ["folders", config.folder_name]

        #pass down shared/common config items
        for file_config in config.files:
            file_config.include_num_access = config.include_num_access

        files = [FileObservation.from_config(config=f, parent_where = where) for f in config.files]
        return cls(where=where, files=files, num_files=config.num_files, include_num_access=config.include_num_access)


class NICObservation(AbstractObservation, identifier="NETWORK_INTERFACE"):
    class ConfigSchema(AbstractObservation.ConfigSchema):
        nic_num: int
        include_nmne: bool = False


    def __init__(self, where: WhereType, include_nmne: bool)->None:
        self.where = where
        self.include_nmne : bool = include_nmne

        self.default_observation: ObsType = {"nic_status": 0}
        if self.include_nmne:
            self.default_observation.update({"NMNE":{"inbound":0, "outbound":0}})

    def observe(self, state: Dict) -> Any:
        # raise NotImplementedError("TODO: CATEGORISATION")
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
        space = spaces.Dict({"nic_status": spaces.Discrete(3)})

        if self.include_nmne:
            space["NMNE"] = spaces.Dict({"inbound": spaces.Discrete(4), "outbound": spaces.Discrete(4)})

        return space

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = [] ) -> ServiceObservation:
        return cls(where = parent_where+["NICs", config.nic_num], include_nmne=config.include_nmne)


class HostObservation(AbstractObservation, identifier="HOST"):
    class ConfigSchema(AbstractObservation.ConfigSchema):
        hostname: str
        services: List[ServiceObservation.ConfigSchema] = []
        applications: List[ApplicationObservation.ConfigSchema] = []
        folders: List[FolderObservation.ConfigSchema] = []
        network_interfaces: List[NICObservation.ConfigSchema] = []
        num_services: int
        num_applications: int
        num_folders: int
        num_files: int
        num_nics: int
        include_nmne: bool
        include_num_access: bool

    def __init__(self,
                 where: WhereType,
                 services:List[ServiceObservation],
                 applications:List[ApplicationObservation],
                 folders:List[FolderObservation],
                 network_interfaces:List[NICObservation],
                 num_services: int,
                 num_applications: int,
                 num_folders: int,
                 num_files: int,
                 num_nics: int,
                 include_nmne: bool,
                 include_num_access: bool
                 )->None:

        self.where : WhereType = where

        # ensure service list has length equal to num_services by truncating or padding
        self.services: List[ServiceObservation] = services
        while len(self.services) < num_services:
            self.services.append(ServiceObservation(where=None))
        while len(self.services) > num_services:
            truncated_service = self.services.pop()
            msg = f"Too many services in Node observation space for node. Truncating service {truncated_service.where}"
            _LOGGER.warning(msg)

        # ensure application list has length equal to num_applications by truncating or padding
        self.applications: List[ApplicationObservation] = applications
        while len(self.applications) < num_applications:
            self.applications.append(ApplicationObservation(where=None))
        while len(self.applications) > num_applications:
            truncated_application = self.applications.pop()
            msg = f"Too many applications in Node observation space for node. Truncating application {truncated_application.where}"
            _LOGGER.warning(msg)

        # ensure folder list has length equal to num_folders by truncating or padding
        self.folders: List[FolderObservation] = folders
        while len(self.folders) < num_folders:
            self.folders.append(FolderObservation(where = None, files= [], num_files=num_files, include_num_access=include_num_access))
        while len(self.folders) > num_folders:
            truncated_folder = self.folders.pop()
            msg = f"Too many folders in Node observation space for node. Truncating folder {truncated_folder.where}"
            _LOGGER.warning(msg)

        # ensure network_interface list has length equal to num_network_interfaces by truncating or padding
        self.network_interfaces: List[NICObservation] = network_interfaces
        while len(self.network_interfaces) < num_nics:
            self.network_interfaces.append(NICObservation(where = None, include_nmne=include_nmne))
        while len(self.network_interfaces) > num_nics:
            truncated_nic = self.network_interfaces.pop()
            msg = f"Too many network_interfaces in Node observation space for node. Truncating {truncated_folder.where}"
            _LOGGER.warning(msg)

        self.default_observation: ObsType = {
            "SERVICES": {i + 1: s.default_observation for i, s in enumerate(self.services)},
            "FOLDERS": {i + 1: f.default_observation for i, f in enumerate(self.folders)},
            "NICS": {i + 1: n.default_observation for i, n in enumerate(self.network_interfaces)},
            "operating_status": 0,
            "num_file_creations": 0,
            "num_file_deletions": 0,
        }


    def observe(self, state: Dict) -> Any:
        node_state = access_from_nested_dict(state, self.where)
        if node_state is NOT_PRESENT_IN_STATE:
            return self.default_observation

        obs = {}
        obs["SERVICES"] = {i + 1: service.observe(state) for i, service in enumerate(self.services)}
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
        shape = {
            "SERVICES": spaces.Dict({i + 1: service.space for i, service in enumerate(self.services)}),
            "FOLDERS": spaces.Dict({i + 1: folder.space for i, folder in enumerate(self.folders)}),
            "operating_status": spaces.Discrete(5),
            "NICS": spaces.Dict(
                {i + 1: network_interface.space for i, network_interface in enumerate(self.network_interfaces)}
            ),
            "num_file_creations" : spaces.Discrete(4),
            "num_file_deletions" : spaces.Discrete(4),
        }
        return spaces.Dict(shape)

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = None ) -> ServiceObservation:
        if parent_where is None:
            where = ["network", "nodes", config.hostname]
        else:
            where = parent_where + ["nodes", config.hostname]

        #pass down shared/common config items
        for folder_config in config.folders:
            folder_config.include_num_access = config.include_num_access
            folder_config.num_files = config.num_files
        for nic_config in config.network_interfaces:
            nic_config.include_nmne = config.include_nmne

        services = [ServiceObservation.from_config(config=c,parent_where=where) for c in config.services]
        applications = [ApplicationObservation.from_config(config=c, parent_where=where) for c in config.applications]
        folders = [FolderObservation.from_config(config=c, parent_where=where) for c in config.folders]
        nics = [NICObservation.from_config(config=c, parent_where=where) for c in config.network_interfaces]

        return cls(
            where = where,
            services = services,
            applications = applications,
            folders = folders,
            network_interfaces = nics,
            num_services = config.num_services,
            num_applications = config.num_applications,
            num_folders = config.num_folders,
            num_files = config.num_files,
            num_nics = config.num_nics,
            include_nmne = config.include_nmne,
            include_num_access = config.include_num_access,
        )


class PortObservation(AbstractObservation, identifier="PORT"):
    class ConfigSchema(AbstractObservation.ConfigSchema):
        pass

    def __init__(self, where: WhereType)->None:
        pass

    def observe(self, state: Dict) -> Any:
        pass

    @property
    def space(self) -> spaces.Space:
        pass

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = [] ) -> ServiceObservation:
        pass

class ACLObservation(AbstractObservation, identifier="ACL"):
    class ConfigSchema(AbstractObservation.ConfigSchema):
        pass

    def __init__(self, where: WhereType)->None:
        pass

    def observe(self, state: Dict) -> Any:
        pass

    @property
    def space(self) -> spaces.Space:
        pass

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = [] ) -> ServiceObservation:
        pass

class RouterObservation(AbstractObservation, identifier="ROUTER"):
    class ConfigSchema(AbstractObservation.ConfigSchema):
        hostname: str
        ports: List[PortObservation.ConfigSchema]


    def __init__(self, where: WhereType)->None:
        pass

    def observe(self, state: Dict) -> Any:
        pass

    @property
    def space(self) -> spaces.Space:
        pass

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = [] ) -> ServiceObservation:
        pass

class FirewallObservation(AbstractObservation, identifier="FIREWALL"):
    class ConfigSchema(AbstractObservation.ConfigSchema):
        hostname: str
        ports: List[PortObservation.ConfigSchema] = []

    def __init__(self, where: WhereType)->None:
        pass

    def observe(self, state: Dict) -> Any:
        pass

    @property
    def space(self) -> spaces.Space:
        pass

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = [] ) -> ServiceObservation:
        pass

class NodesObservation(AbstractObservation, identifier="NODES"):
    class ConfigSchema(AbstractObservation.ConfigSchema):
        """Config"""
        hosts: List[HostObservation.ConfigSchema] = []
        routers: List[RouterObservation.ConfigSchema] = []
        firewalls: List[FirewallObservation.ConfigSchema] = []
        num_services: int = 1


    def __init__(self, where: WhereType)->None:
        pass

    def observe(self, state: Dict) -> Any:
        pass

    @property
    def space(self) -> spaces.Space:
        pass

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = [] ) -> ServiceObservation:
        pass

############################ OLD

class NodeObservation(AbstractObservation, identifier= "OLD"):
    """Observation of a node in the network. Includes services, folders and NICs."""

    def __init__(
        self,
        where: Optional[Tuple[str]] = None,
        services: List[ServiceObservation] = [],
        folders: List[FolderObservation] = [],
        network_interfaces: List[NicObservation] = [],
        logon_status: bool = False,
        num_services_per_node: int = 2,
        num_folders_per_node: int = 2,
        num_files_per_folder: int = 2,
        num_nics_per_node: int = 2,
    ) -> None:
        """
        Configurable observation for a node in the simulation.

        :param where: Where in the simulation state dictionary for find relevant information for this observation.
            A typical location for a node looks like this:
            ['network','nodes',<hostname>]. If empty list, a default null observation will be output, defaults to []
        :type where: List[str], optional
        :param services: Mapping between position in observation space and service name, defaults to {}
        :type services: Dict[int,str], optional
        :param max_services: Max number of services that can be presented in observation space for this node
            , defaults to 2
        :type max_services: int, optional
        :param folders: Mapping between position in observation space and folder name, defaults to {}
        :type folders: Dict[int,str], optional
        :param max_folders: Max number of folders in this node's obs space, defaults to 2
        :type max_folders: int, optional
        :param network_interfaces: Mapping between position in observation space and NIC idx, defaults to {}
        :type network_interfaces: Dict[int,str], optional
        :param max_nics: Max number of network interfaces in this node's obs space, defaults to 5
        :type max_nics: int, optional
        """
        super().__init__()
        self.where: Optional[Tuple[str]] = where

        self.services: List[ServiceObservation] = services
        while len(self.services) < num_services_per_node:
            # add empty service observation without `where` parameter so it always returns default (blank) observation
            self.services.append(ServiceObservation())
        while len(self.services) > num_services_per_node:
            truncated_service = self.services.pop()
            msg = f"Too many services in Node observation space for node. Truncating service {truncated_service.where}"
            _LOGGER.warning(msg)
            # truncate service list

        self.folders: List[FolderObservation] = folders
        # add empty folder observation without `where` parameter that will always return default (blank) observations
        while len(self.folders) < num_folders_per_node:
            self.folders.append(FolderObservation(num_files_per_folder=num_files_per_folder))
        while len(self.folders) > num_folders_per_node:
            truncated_folder = self.folders.pop()
            msg = f"Too many folders in Node observation for node. Truncating service {truncated_folder.where[-1]}"
            _LOGGER.warning(msg)

        self.network_interfaces: List[NicObservation] = network_interfaces
        while len(self.network_interfaces) < num_nics_per_node:
            self.network_interfaces.append(NicObservation())
        while len(self.network_interfaces) > num_nics_per_node:
            truncated_nic = self.network_interfaces.pop()
            msg = f"Too many NICs in Node observation for node. Truncating service {truncated_nic.where[-1]}"
            _LOGGER.warning(msg)

        self.logon_status: bool = logon_status

        self.default_observation: Dict = {
            "SERVICES": {i + 1: s.default_observation for i, s in enumerate(self.services)},
            "FOLDERS": {i + 1: f.default_observation for i, f in enumerate(self.folders)},
            "NICS": {i + 1: n.default_observation for i, n in enumerate(self.network_interfaces)},
            "operating_status": 0,
        }
        if self.logon_status:
            self.default_observation["logon_status"] = 0

    def observe(self, state: Dict) -> Dict:
        """Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary
        :type state: Dict
        :return: Observation
        :rtype: Dict
        """
        if self.where is None:
            return self.default_observation

        node_state = access_from_nested_dict(state, self.where)
        if node_state is NOT_PRESENT_IN_STATE:
            return self.default_observation

        obs = {}
        obs["SERVICES"] = {i + 1: service.observe(state) for i, service in enumerate(self.services)}
        obs["FOLDERS"] = {i + 1: folder.observe(state) for i, folder in enumerate(self.folders)}
        obs["operating_status"] = node_state["operating_state"]
        obs["NICS"] = {
            i + 1: network_interface.observe(state) for i, network_interface in enumerate(self.network_interfaces)
        }

        if self.logon_status:
            obs["logon_status"] = 0

        return obs

    @property
    def space(self) -> spaces.Space:
        """Gymnasium space object describing the observation space shape."""
        space_shape = {
            "SERVICES": spaces.Dict({i + 1: service.space for i, service in enumerate(self.services)}),
            "FOLDERS": spaces.Dict({i + 1: folder.space for i, folder in enumerate(self.folders)}),
            "operating_status": spaces.Discrete(5),
            "NICS": spaces.Dict(
                {i + 1: network_interface.space for i, network_interface in enumerate(self.network_interfaces)}
            ),
        }
        if self.logon_status:
            space_shape["logon_status"] = spaces.Discrete(3)

        return spaces.Dict(space_shape)

    @classmethod
    def from_config(
        cls,
        config: Dict,
        game: "PrimaiteGame",
        parent_where: Optional[List[str]] = None,
        num_services_per_node: int = 2,
        num_folders_per_node: int = 2,
        num_files_per_folder: int = 2,
        num_nics_per_node: int = 2,
    ) -> "NodeObservation":
        """Create node observation from a config. Also creates child service, folder and NIC observations.

        :param config: Dictionary containing the configuration for this node observation.
        :type config: Dict
        :param game: Reference to the PrimaiteGame object that spawned this observation.
        :type game: PrimaiteGame
        :param parent_where: Where in the simulation state dictionary to find the information about this node's parent
            network. A typical location for it would be: ['network',]
        :type parent_where: Optional[List[str]]
        :param num_services_per_node: How many spaces for services are in this node observation (to preserve static
            observation size) , defaults to 2
        :type num_services_per_node: int, optional
        :param num_folders_per_node: How many spaces for folders are in this node observation (to preserve static
            observation size) , defaults to 2
        :type num_folders_per_node: int, optional
        :param num_files_per_folder: How many spaces for files are in the folder observations (to preserve static
            observation size) , defaults to 2
        :type num_files_per_folder: int, optional
        :return: Constructed node observation
        :rtype: NodeObservation
        """
        node_hostname = config["node_hostname"]
        if parent_where is None:
            where = ["network", "nodes", node_hostname]
        else:
            where = parent_where + ["nodes", node_hostname]

        svc_configs = config.get("services", {})
        services = [ServiceObservation.from_config(config=c, game=game, parent_where=where) for c in svc_configs]
        folder_configs = config.get("folders", {})
        folders = [
            FolderObservation.from_config(
                config=c, game=game, parent_where=where + ["file_system"], num_files_per_folder=num_files_per_folder
            )
            for c in folder_configs
        ]
        # create some configs for the NIC observation in the format {"nic_num":1}, {"nic_num":2}, {"nic_num":3}, etc.
        nic_configs = [{"nic_num": i for i in range(num_nics_per_node)}]
        network_interfaces = [NicObservation.from_config(config=c, game=game, parent_where=where) for c in nic_configs]
        logon_status = config.get("logon_status", False)
        return cls(
            where=where,
            services=services,
            folders=folders,
            network_interfaces=network_interfaces,
            logon_status=logon_status,
            num_services_per_node=num_services_per_node,
            num_folders_per_node=num_folders_per_node,
            num_files_per_folder=num_files_per_folder,
            num_nics_per_node=num_nics_per_node,
        )
