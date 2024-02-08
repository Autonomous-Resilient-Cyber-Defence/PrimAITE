"""Manages the observation space for the agent."""
from abc import ABC, abstractmethod
from ipaddress import IPv4Address
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from gymnasium import spaces
from gymnasium.core import ObsType

from primaite import getLogger
from primaite.game.agent.utils import access_from_nested_dict, NOT_PRESENT_IN_STATE

_LOGGER = getLogger(__name__)

if TYPE_CHECKING:
    from primaite.game.game import PrimaiteGame


class AbstractObservation(ABC):
    """Abstract class for an observation space component."""

    @abstractmethod
    def observe(self, state: Dict) -> Any:
        """
        Return an observation based on the current state of the simulation.

        :param state: Simulation state dictionary
        :type state: Dict
        :return: Observation
        :rtype: Any
        """
        pass

    @property
    @abstractmethod
    def space(self) -> spaces.Space:
        """Gymnasium space object describing the observation space."""
        pass

    @classmethod
    @abstractmethod
    def from_config(cls, config: Dict, game: "PrimaiteGame"):
        """Create this observation space component form a serialised format.

        The `game` parameter is for a the PrimaiteGame object that spawns this component.
        """
        pass


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


class ServiceObservation(AbstractObservation):
    """Observation of a service in the network."""

    default_observation: spaces.Space = {"operating_status": 0, "health_status": 0}
    "Default observation is what should be returned when the service doesn't exist."

    def __init__(self, where: Optional[Tuple[str]] = None) -> None:
        """Initialise service observation.

        :param where: Store information about where in the simulation state dictionary to find the relevant information.
            Optional. If None, this corresponds that the file does not exist and the observation will be populated with
            zeroes.

            A typical location for a service looks like this:
            `['network','nodes',<node_hostname>,'services', <service_name>]`
        :type where: Optional[List[str]]
        """
        super().__init__()
        self.where: Optional[Tuple[str]] = where

    def observe(self, state: Dict) -> Dict:
        """Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary
        :type state: Dict
        :return: Observation
        :rtype: Dict
        """
        if self.where is None:
            return self.default_observation

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
        return spaces.Dict({"operating_status": spaces.Discrete(7), "health_status": spaces.Discrete(6)})

    @classmethod
    def from_config(
        cls, config: Dict, game: "PrimaiteGame", parent_where: Optional[List[str]] = None
    ) -> "ServiceObservation":
        """Create service observation from a config.

        :param config: Dictionary containing the configuration for this service observation.
        :type config: Dict
        :param game: Reference to the PrimaiteGame object that spawned this observation.
        :type game: PrimaiteGame
        :param parent_where: Where in the simulation state dictionary this service's parent node is located. Optional.
        :type parent_where: Optional[List[str]], optional
        :return: Constructed service observation
        :rtype: ServiceObservation
        """
        return cls(where=parent_where + ["services", config["service_name"]])


class LinkObservation(AbstractObservation):
    """Observation of a link in the network."""

    default_observation: spaces.Space = {"PROTOCOLS": {"ALL": 0}}
    "Default observation is what should be returned when the link doesn't exist."

    def __init__(self, where: Optional[Tuple[str]] = None) -> None:
        """Initialise link observation.

        :param where: Store information about where in the simulation state dictionary to find the relevant information.
            Optional. If None, this corresponds that the file does not exist and the observation will be populated with
            zeroes.

            A typical location for a service looks like this:
            `['network','nodes',<node_hostname>,'servics', <service_name>]`
        :type where: Optional[List[str]]
        """
        super().__init__()
        self.where: Optional[Tuple[str]] = where

    def observe(self, state: Dict) -> Dict:
        """Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary
        :type state: Dict
        :return: Observation
        :rtype: Dict
        """
        if self.where is None:
            return self.default_observation

        link_state = access_from_nested_dict(state, self.where)
        if link_state is NOT_PRESENT_IN_STATE:
            return self.default_observation

        bandwidth = link_state["bandwidth"]
        load = link_state["current_load"]
        if load == 0:
            utilisation_category = 0
        else:
            utilisation_fraction = load / bandwidth
            # 0 is UNUSED, 1 is 0%-10%. 2 is 10%-20%. 3 is 20%-30%. And so on... 10 is exactly 100%
            utilisation_category = int(utilisation_fraction * 9) + 1

        # TODO: once the links support separte load per protocol, this needs amendment to reflect that.
        return {"PROTOCOLS": {"ALL": min(utilisation_category, 10)}}

    @property
    def space(self) -> spaces.Space:
        """Gymnasium space object describing the observation space shape.

        :return: Gymnasium space
        :rtype: spaces.Space
        """
        return spaces.Dict({"PROTOCOLS": spaces.Dict({"ALL": spaces.Discrete(11)})})

    @classmethod
    def from_config(cls, config: Dict, game: "PrimaiteGame") -> "LinkObservation":
        """Create link observation from a config.

        :param config: Dictionary containing the configuration for this link observation.
        :type config: Dict
        :param game: Reference to the PrimaiteGame object that spawned this observation.
        :type game: PrimaiteGame
        :return: Constructed link observation
        :rtype: LinkObservation
        """
        return cls(where=["network", "links", game.ref_map_links[config["link_ref"]]])


class FolderObservation(AbstractObservation):
    """Folder observation, including files inside of the folder."""

    def __init__(
        self, where: Optional[Tuple[str]] = None, files: List[FileObservation] = [], num_files_per_folder: int = 2
    ) -> None:
        """Initialise folder Observation, including files inside of the folder.

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


class NicObservation(AbstractObservation):
    """Observation of a Network Interface Card (NIC) in the network."""

    default_observation: spaces.Space = {"nic_status": 0}

    def __init__(self, where: Optional[Tuple[str]] = None) -> None:
        """Initialise NIC observation.

        :param where: Where in the simulation state dictionary to find the relevant information for this NIC. A typical
            example may look like this:
            ['network','nodes',<node_hostname>,'NICs',<nic_number>]
            If None, this denotes that the NIC does not exist and the observation will be populated with zeroes.
        :type where: Optional[Tuple[str]], optional
        """
        super().__init__()
        self.where: Optional[Tuple[str]] = where

    def observe(self, state: Dict) -> Dict:
        """Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary
        :type state: Dict
        :return: Observation
        :rtype: Dict
        """
        if self.where is None:
            return self.default_observation
        nic_state = access_from_nested_dict(state, self.where)
        if nic_state is NOT_PRESENT_IN_STATE:
            return self.default_observation
        else:
            return {"nic_status": 1 if nic_state["enabled"] else 2}

    @property
    def space(self) -> spaces.Space:
        """Gymnasium space object describing the observation space shape."""
        return spaces.Dict({"nic_status": spaces.Discrete(3)})

    @classmethod
    def from_config(cls, config: Dict, game: "PrimaiteGame", parent_where: Optional[List[str]]) -> "NicObservation":
        """Create NIC observation from a config.

        :param config: Dictionary containing the configuration for this NIC observation.
        :type config: Dict
        :param game: Reference to the PrimaiteGame object that spawned this observation.
        :type game: PrimaiteGame
        :param parent_where: Where in the simulation state dictionary to find the information about this NIC's parent
            node. A typical location for a node ``where`` can be: ['network','nodes',<node_hostname>]
        :type parent_where: Optional[List[str]]
        :return: Constructed NIC observation
        :rtype: NicObservation
        """
        return cls(where=parent_where + ["NICs", config["nic_num"]])


class NodeObservation(AbstractObservation):
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
            "NETWORK_INTERFACES": {i + 1: n.default_observation for i, n in enumerate(self.network_interfaces)},
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
        obs["NETWORK_INTERFACES"] = {
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
            "NETWORK_INTERFACES": spaces.Dict(
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


class AclObservation(AbstractObservation):
    """Observation of an Access Control List (ACL) in the network."""

    # TODO: should where be optional, and we can use where=None to pad the observation space?
    # definitely the current approach does not support tracking files that aren't specified by name, for example
    # if a file is created at runtime, we have currently got no way of telling the observation space to track it.
    # this needs adding, but not for the MVP.
    def __init__(
        self,
        node_ip_to_id: Dict[str, int],
        ports: List[int],
        protocols: List[str],
        where: Optional[Tuple[str]] = None,
        num_rules: int = 10,
    ) -> None:
        """Initialise ACL observation.

        :param node_ip_to_id: Mapping between IP address and ID.
        :type node_ip_to_id: Dict[str, int]
        :param ports: List of ports which are part of the game that define the ordering when converting to an ID
        :type ports: List[int]
        :param protocols: List of protocols which are part of the game, defines ordering when converting to an ID
        :type protocols: list[str]
        :param where: Where in the simulation state dictionary to find the relevant information for this ACL. A typical
            example may look like this:
            ['network','nodes',<router_hostname>,'acl','acl']
        :type where: Optional[Tuple[str]], optional
        :param num_rules: , defaults to 10
        :type num_rules: int, optional
        """
        super().__init__()
        self.where: Optional[Tuple[str]] = where
        self.num_rules: int = num_rules
        self.node_to_id: Dict[str, int] = node_ip_to_id
        "List of node IP addresses, order in this list determines how they are converted to an ID"
        self.port_to_id: Dict[int, int] = {port: i + 2 for i, port in enumerate(ports)}
        "List of ports which are part of the game that define the ordering when converting to an ID"
        self.protocol_to_id: Dict[str, int] = {protocol: i + 2 for i, protocol in enumerate(protocols)}
        "List of protocols which are part of the game, defines ordering when converting to an ID"
        self.default_observation: Dict = {
            i
            + 1: {
                "position": i,
                "permission": 0,
                "source_node_id": 0,
                "source_port": 0,
                "dest_node_id": 0,
                "dest_port": 0,
                "protocol": 0,
            }
            for i in range(self.num_rules)
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
        acl_state: Dict = access_from_nested_dict(state, self.where)
        if acl_state is NOT_PRESENT_IN_STATE:
            return self.default_observation

        # TODO: what if the ACL has more rules than num of max rules for obs space
        obs = {}
        acl_items = dict(acl_state.items())
        i = 1  # don't show rule 0 for compatibility reasons.
        while i < self.num_rules + 1:
            rule_state = acl_items[i]
            if rule_state is None:
                obs[i] = {
                    "position": i - 1,
                    "permission": 0,
                    "source_node_id": 0,
                    "source_port": 0,
                    "dest_node_id": 0,
                    "dest_port": 0,
                    "protocol": 0,
                }
            else:
                src_ip = rule_state["src_ip_address"]
                src_node_id = 1 if src_ip is None else self.node_to_id[IPv4Address(src_ip)]
                dst_ip = rule_state["dst_ip_address"]
                dst_node_ip = 1 if dst_ip is None else self.node_to_id[IPv4Address(dst_ip)]
                src_port = rule_state["src_port"]
                src_port_id = 1 if src_port is None else self.port_to_id[src_port]
                dst_port = rule_state["dst_port"]
                dst_port_id = 1 if dst_port is None else self.port_to_id[dst_port]
                protocol = rule_state["protocol"]
                protocol_id = 1 if protocol is None else self.protocol_to_id[protocol]
                obs[i] = {
                    "position": i - 1,
                    "permission": rule_state["action"],
                    "source_node_id": src_node_id,
                    "source_port": src_port_id,
                    "dest_node_id": dst_node_ip,
                    "dest_port": dst_port_id,
                    "protocol": protocol_id,
                }
            i += 1
        return obs

    @property
    def space(self) -> spaces.Space:
        """Gymnasium space object describing the observation space shape.

        :return: Gymnasium space
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
                        "source_node_id": spaces.Discrete(len(set(self.node_to_id.values())) + 2),
                        "source_port": spaces.Discrete(len(self.port_to_id) + 2),
                        "dest_node_id": spaces.Discrete(len(set(self.node_to_id.values())) + 2),
                        "dest_port": spaces.Discrete(len(self.port_to_id) + 2),
                        "protocol": spaces.Discrete(len(self.protocol_to_id) + 2),
                    }
                )
                for i in range(self.num_rules)
            }
        )

    @classmethod
    def from_config(cls, config: Dict, game: "PrimaiteGame") -> "AclObservation":
        """Generate ACL observation from a config.

        :param config: Dictionary containing the configuration for this ACL observation.
        :type config: Dict
        :param game: Reference to the PrimaiteGame object that spawned this observation.
        :type game: PrimaiteGame
        :return: Observation object
        :rtype: AclObservation
        """
        max_acl_rules = config["options"]["max_acl_rules"]
        node_ip_to_idx = {}
        for ip_idx, ip_map_config in enumerate(config["ip_address_order"]):
            node_ref = ip_map_config["node_hostname"]
            nic_num = ip_map_config["nic_num"]
            node_obj = game.simulation.network.nodes[game.ref_map_nodes[node_ref]]
            nic_obj = node_obj.network_interface[nic_num]
            node_ip_to_idx[nic_obj.ip_address] = ip_idx + 2

        router_hostname = config["router_hostname"]
        return cls(
            node_ip_to_id=node_ip_to_idx,
            ports=game.options.ports,
            protocols=game.options.protocols,
            where=["network", "nodes", router_hostname, "acl", "acl"],
            num_rules=max_acl_rules,
        )


class NullObservation(AbstractObservation):
    """Null observation, returns a single 0 value for the observation space."""

    def __init__(self, where: Optional[List[str]] = None):
        """Initialise null observation."""
        self.default_observation: Dict = {}

    def observe(self, state: Dict) -> Dict:
        """Generate observation based on the current state of the simulation."""
        return 0

    @property
    def space(self) -> spaces.Space:
        """Gymnasium space object describing the observation space shape."""
        return spaces.Discrete(1)

    @classmethod
    def from_config(cls, config: Dict, game: Optional["PrimaiteGame"] = None) -> "NullObservation":
        """
        Create null observation from a config.

        The parameters are ignored, they are here to match the signature of the other observation classes.
        """
        return cls()


class ICSObservation(NullObservation):
    """ICS observation placeholder, currently not implemented so always returns a single 0."""

    pass


class UC2BlueObservation(AbstractObservation):
    """Container for all observations used by the blue agent in UC2.

    TODO: there's no real need for a UC2 blue container class, we should be able to simply use the observation handler
        for the purpose of compiling several observation components.
    """

    def __init__(
        self,
        nodes: List[NodeObservation],
        links: List[LinkObservation],
        acl: AclObservation,
        ics: ICSObservation,
        where: Optional[List[str]] = None,
    ) -> None:
        """Initialise UC2 blue observation.

        :param nodes: List of node observations
        :type nodes: List[NodeObservation]
        :param links: List of link observations
        :type links: List[LinkObservation]
        :param acl: The Access Control List observation
        :type acl: AclObservation
        :param ics: The ICS observation
        :type ics: ICSObservation
        :param where: Where in the simulation state dict to find information. Not used in this particular observation
            because it only compiles other observations and doesn't contribute any new information, defaults to None
        :type where: Optional[List[str]], optional
        """
        super().__init__()
        self.where: Optional[Tuple[str]] = where

        self.nodes: List[NodeObservation] = nodes
        self.links: List[LinkObservation] = links
        self.acl: AclObservation = acl
        self.ics: ICSObservation = ics

        self.default_observation: Dict = {
            "NODES": {i + 1: n.default_observation for i, n in enumerate(self.nodes)},
            "LINKS": {i + 1: l.default_observation for i, l in enumerate(self.links)},
            "ACL": self.acl.default_observation,
            "ICS": self.ics.default_observation,
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

        obs = {}
        obs["NODES"] = {i + 1: node.observe(state) for i, node in enumerate(self.nodes)}
        obs["LINKS"] = {i + 1: link.observe(state) for i, link in enumerate(self.links)}
        obs["ACL"] = self.acl.observe(state)
        obs["ICS"] = self.ics.observe(state)

        return obs

    @property
    def space(self) -> spaces.Space:
        """
        Gymnasium space object describing the observation space shape.

        :return: Space
        :rtype: spaces.Space
        """
        return spaces.Dict(
            {
                "NODES": spaces.Dict({i + 1: node.space for i, node in enumerate(self.nodes)}),
                "LINKS": spaces.Dict({i + 1: link.space for i, link in enumerate(self.links)}),
                "ACL": self.acl.space,
                "ICS": self.ics.space,
            }
        )

    @classmethod
    def from_config(cls, config: Dict, game: "PrimaiteGame") -> "UC2BlueObservation":
        """Create UC2 blue observation from a config.

        :param config: Dictionary containing the configuration for this UC2 blue observation. This includes the nodes,
            links, ACL and ICS observations.
        :type config: Dict
        :param game: Reference to the PrimaiteGame object that spawned this observation.
        :type game: PrimaiteGame
        :return: Constructed UC2 blue observation
        :rtype: UC2BlueObservation
        """
        node_configs = config["nodes"]

        num_services_per_node = config["num_services_per_node"]
        num_folders_per_node = config["num_folders_per_node"]
        num_files_per_folder = config["num_files_per_folder"]
        num_nics_per_node = config["num_nics_per_node"]
        nodes = [
            NodeObservation.from_config(
                config=n,
                game=game,
                num_services_per_node=num_services_per_node,
                num_folders_per_node=num_folders_per_node,
                num_files_per_folder=num_files_per_folder,
                num_nics_per_node=num_nics_per_node,
            )
            for n in node_configs
        ]

        link_configs = config["links"]
        links = [LinkObservation.from_config(config=link, game=game) for link in link_configs]

        acl_config = config["acl"]
        acl = AclObservation.from_config(config=acl_config, game=game)

        ics_config = config["ics"]
        ics = ICSObservation.from_config(config=ics_config, game=game)
        new = cls(nodes=nodes, links=links, acl=acl, ics=ics, where=["network"])
        return new


class UC2RedObservation(AbstractObservation):
    """Container for all observations used by the red agent in UC2."""

    def __init__(self, nodes: List[NodeObservation], where: Optional[List[str]] = None) -> None:
        super().__init__()
        self.where: Optional[List[str]] = where
        self.nodes: List[NodeObservation] = nodes

        self.default_observation: Dict = {
            "NODES": {i + 1: n.default_observation for i, n in enumerate(self.nodes)},
        }

    def observe(self, state: Dict) -> Dict:
        """Generate observation based on the current state of the simulation."""
        if self.where is None:
            return self.default_observation

        obs = {}
        obs["NODES"] = {i + 1: node.observe(state) for i, node in enumerate(self.nodes)}
        return obs

    @property
    def space(self) -> spaces.Space:
        """Gymnasium space object describing the observation space shape."""
        return spaces.Dict(
            {
                "NODES": spaces.Dict({i + 1: node.space for i, node in enumerate(self.nodes)}),
            }
        )

    @classmethod
    def from_config(cls, config: Dict, game: "PrimaiteGame") -> "UC2RedObservation":
        """
        Create UC2 red observation from a config.

        :param config: Dictionary containing the configuration for this UC2 red observation.
        :type config: Dict
        :param game: Reference to the PrimaiteGame object that spawned this observation.
        :type game: PrimaiteGame
        """
        node_configs = config["nodes"]
        nodes = [NodeObservation.from_config(config=cfg, game=game) for cfg in node_configs]
        return cls(nodes=nodes, where=["network"])


class UC2GreenObservation(NullObservation):
    """Green agent observation. As the green agent's actions don't depend on the observation, this is empty."""

    pass


class ObservationManager:
    """
    Manage the observations of an Agent.

    The observation space has the purpose of:
      1. Reading the outputted state from the PrimAITE Simulation.
      2. Selecting parts of the simulation state that are requested by the simulation config
      3. Formatting this information so an agent can use it to make decisions.
    """

    # TODO: Dear code reader: This class currently doesn't do much except hold an observation object. It will be changed
    # to have more of it's own behaviour, and it will replace UC2BlueObservation and UC2RedObservation during the next
    # refactor.

    def __init__(self, observation: AbstractObservation) -> None:
        """Initialise observation space.

        :param observation: Observation object
        :type observation: AbstractObservation
        """
        self.obs: AbstractObservation = observation
        self.current_observation: ObsType

    def update(self, state: Dict) -> Dict:
        """
        Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary
        :type state: Dict
        """
        self.current_observation = self.obs.observe(state)
        return self.current_observation

    @property
    def space(self) -> None:
        """Gymnasium space object describing the observation space shape."""
        return self.obs.space

    @classmethod
    def from_config(cls, config: Dict, game: "PrimaiteGame") -> "ObservationManager":
        """Create observation space from a config.

        :param config: Dictionary containing the configuration for this observation space.
            It should contain the key 'type' which selects which observation class to use (from a choice of:
            UC2BlueObservation, UC2RedObservation, UC2GreenObservation)
            The other key is 'options' which are passed to the constructor of the selected observation class.
        :type config: Dict
        :param game: Reference to the PrimaiteGame object that spawned this observation.
        :type game: PrimaiteGame
        """
        if config["type"] == "UC2BlueObservation":
            return cls(UC2BlueObservation.from_config(config.get("options", {}), game=game))
        elif config["type"] == "UC2RedObservation":
            return cls(UC2RedObservation.from_config(config.get("options", {}), game=game))
        elif config["type"] == "UC2GreenObservation":
            return cls(UC2GreenObservation.from_config(config.get("options", {}), game=game))
        else:
            raise ValueError("Observation space type invalid")
