from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from gymnasium import spaces

from primaite import getLogger
from primaite.game.agent.observations.file_system_observations import FolderObservation
from primaite.game.agent.observations.observations import AbstractObservation, NicObservation
from primaite.game.agent.observations.software_observation import ServiceObservation
from primaite.game.agent.utils import access_from_nested_dict, NOT_PRESENT_IN_STATE

_LOGGER = getLogger(__name__)

if TYPE_CHECKING:
    from primaite.game.game import PrimaiteGame


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
