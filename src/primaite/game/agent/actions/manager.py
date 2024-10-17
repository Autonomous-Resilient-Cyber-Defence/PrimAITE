# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
"""yaml example

agents:
  - name: agent_1
    action_space:
      actions:
        - do_nothing
        - node_service_start
        - node_service_stop
      action_map:
"""

from __future__ import annotations

import itertools
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Dict, List, Literal, Optional, Tuple, Type

from gymnasium import spaces
from pydantic import BaseModel, ConfigDict

from primaite.game.game import _LOGGER, PrimaiteGame
from primaite.interface.request import RequestFormat


class AbstractAction(BaseModel):
    """Base class for actions."""

    # notes:
    # we actually don't need to hold any state in actions, so there's no need to define any __init__ logic.
    # all the init methods in the old actions are just used for holding a verb and shape, which are not really used.
    # the config schema should be used to the actual parameters for formatting the action itself.
    # (therefore there's no need for creating action instances, just the action class contains logic for converting
    # CAOS actions to requests for simulator. Similar to the network node adder, that class also doesn't need to be
    # instantiated.)
    class ConfigSchema(BaseModel, ABC):  # TODO: not sure if this better named something like `Options`
        model_config = ConfigDict(extra="forbid")
        type: str

    _registry: ClassVar[Dict[str, Type[AbstractAction]]] = {}

    def __init_subclass__(cls, identifier: str, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if identifier in cls._registry:
            raise ValueError(f"Cannot create new action under reserved name {identifier}")
        cls._registry[identifier] = cls

    @classmethod
    def form_request(self, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return []


class DoNothingAction(AbstractAction):
    class ConfigSchema(AbstractAction.ConfigSchema):
        type: Literal["do_nothing"] = "do_nothing"

    def form_request(self, options: ConfigSchema) -> RequestFormat:
        return ["do_nothing"]


class ActionManager:
    """Class which manages the action space for an agent."""

    def __init__(
        self,
        actions: List[Dict],  # stores list of actions available to agent
        # nodes: List[Dict],  # extra configuration for each node
        # max_folders_per_node: int = 2,  # allows calculating shape
        # max_files_per_folder: int = 2,  # allows calculating shape
        # max_services_per_node: int = 2,  # allows calculating shape
        # max_applications_per_node: int = 2,  # allows calculating shape
        # max_nics_per_node: int = 8,  # allows calculating shape
        # max_acl_rules: int = 10,  # allows calculating shape
        # protocols: List[str] = ["TCP", "UDP", "ICMP"],  # allow mapping index to protocol
        # ports: List[str] = ["HTTP", "DNS", "ARP", "FTP", "NTP"],  # allow mapping index to port
        # ip_list: List[str] = [],  # to allow us to map an index to an ip address.
        # wildcard_list: List[str] = [],  # to allow mapping from wildcard index to
        act_map: Optional[Dict[int, Dict]] = None,  # allows restricting set of possible actions
    ) -> None:
        """Init method for ActionManager.

        :param game: Reference to the game to which the agent belongs.
        :type game: PrimaiteGame
        :param actions: List of action specs which should be made available to the agent. The keys of each spec are:
            'type' and 'options' for passing any options to the action class's init method
        :type actions: List[dict]
        :param nodes: Extra configuration for each node.
        :type nodes: List[Dict]
        :param max_folders_per_node: Maximum number of folders per node. Used for calculating action shape.
        :type max_folders_per_node: int
        :param max_files_per_folder: Maximum number of files per folder. Used for calculating action shape.
        :type max_files_per_folder: int
        :param max_services_per_node: Maximum number of services per node. Used for calculating action shape.
        :type max_services_per_node: int
        :param max_nics_per_node: Maximum number of NICs per node. Used for calculating action shape.
        :type max_nics_per_node: int
        :param max_acl_rules: Maximum number of ACL rules per router. Used for calculating action shape.
        :type max_acl_rules: int
        :param protocols: List of protocols that are available in the simulation. Used for calculating action shape.
        :type protocols: List[str]
        :param ports: List of ports that are available in the simulation. Used for calculating action shape.
        :type ports: List[str]
        :param ip_list: List of IP addresses that known to this agent. Used for calculating action shape.
        :type ip_list: Optional[List[str]]
        :param act_map: Action map which maps integers to actions. Used for restricting the set of possible actions.
        :type act_map: Optional[Dict[int, Dict]]
        """
        self.node_names: List[str] = [n["node_name"] for n in nodes]
        """List of node names in this action space. The list order is the mapping between node index and node name."""
        self.application_names: List[List[str]] = []
        """
        List of applications per node. The list order gives the two-index mapping between (node_id, app_id) to app name.
        The first index corresponds to node id, the second index is the app id on that particular node.
        For instance, self.application_names[0][2] is the name of the third application on the first node.
        """
        self.service_names: List[List[str]] = []
        """
        List of services per node. The list order gives the two-index mapping between (node_id, svc_id) to svc name.
        The first index corresponds to node id, the second index is the service id on that particular node.
        For instance, self.service_names[0][2] is the name of the third service on the first node.
        """
        self.folder_names: List[List[str]] = []
        """
        List of folders per node. The list order gives the two-index mapping between (node_id, folder_id) to folder
        name. The first index corresponds to node id, the second index is the folder id on that particular node.
        For instance, self.folder_names[0][2] is the name of the third folder on the first node.
        """
        self.file_names: List[List[List[str]]] = []
        """
        List of files per folder per node. The list order gives the three-index mapping between
        (node_id, folder_id, file_id) to file name. The first index corresponds to node id, the second index is the
        folder id on that particular node, and the third index is the file id in that particular folder.
        For instance, self.file_names[0][2][1] is the name of the second file in the third folder on the first node.
        """

        # Populate lists of apps, services, files, folders, etc on nodes.
        # for node in nodes:
        #     app_list = [a["application_name"] for a in node.get("applications", [])]
        #     while len(app_list) < max_applications_per_node:
        #         app_list.append(None)
        #     self.application_names.append(app_list)

        #     svc_list = [s["service_name"] for s in node.get("services", [])]
        #     while len(svc_list) < max_services_per_node:
        #         svc_list.append(None)
        #     self.service_names.append(svc_list)

        #     folder_list = [f["folder_name"] for f in node.get("folders", [])]
        #     while len(folder_list) < max_folders_per_node:
        #         folder_list.append(None)
        #     self.folder_names.append(folder_list)

        #     file_sublist = []
        #     for folder in node.get("folders", [{"files": []}]):
        #         file_list = [f["file_name"] for f in folder.get("files", [])]
        #         while len(file_list) < max_files_per_folder:
        #             file_list.append(None)
        #         file_sublist.append(file_list)
        #     while len(file_sublist) < max_folders_per_node:
        #         file_sublist.append([None] * max_files_per_folder)
        #     self.file_names.append(file_sublist)
        # self.protocols: List[str] = protocols
        # self.ports: List[str] = ports

        # self.ip_address_list: List[str] = ip_list
        # self.wildcard_list: List[str] = wildcard_list
        # if self.wildcard_list == []:
        #     self.wildcard_list = ["NONE"]
        # # action_args are settings which are applied to the action space as a whole.
        # global_action_args = {
        #     "num_nodes": len(self.node_names),
        #     "num_folders": max_folders_per_node,
        #     "num_files": max_files_per_folder,
        #     "num_services": max_services_per_node,
        #     "num_applications": max_applications_per_node,
        #     "num_nics": max_nics_per_node,
        #     "num_acl_rules": max_acl_rules,
        #     "num_protocols": len(self.protocols),
        #     "num_ports": len(self.protocols),
        #     "num_ips": len(self.ip_address_list),
        #     "max_acl_rules": max_acl_rules,
        #     "max_nics_per_node": max_nics_per_node,
        # }
        self.actions: Dict[str, AbstractAction] = {}
        for act_spec in actions:
            # each action is provided into the action space config like this:
            # - type: ACTION_TYPE
            #   options:
            #     option_1: value1
            #     option_2: value2
            # where `type` decides which AbstractAction subclass should be used
            # and `options` is an optional dict of options to pass to the init method of the action class
            act_type = act_spec.get("type")
            act_options = act_spec.get("options", {})
            self.actions[act_type] = self.act_class_identifiers[act_type](self, **global_action_args, **act_options)

        self.action_map: Dict[int, Tuple[str, Dict]] = {}
        """
        Action mapping that converts an integer to a specific action and parameter choice.

        For example :
        {0: ("NODE_SERVICE_SCAN", {node_id:0, service_id:2})}
        """
        if act_map is None:
            # raise RuntimeError("Action map must be specified in the config file.")
            pass
        else:
            self.action_map = {i: (a["action"], a["options"]) for i, a in act_map.items()}
        # make sure all numbers between 0 and N are represented as dict keys in action map
        assert all([i in self.action_map.keys() for i in range(len(self.action_map))])

    def _enumerate_actions(
        self,
    ) -> Dict[int, Tuple[str, Dict]]:
        """Generate a list of all the possible actions that could be taken.

        This enumerates all actions all combinations of parameters you could choose for those actions. The output
        of this function is intended to populate the self.action_map parameter in the situation where the user provides
        a list of action types, but doesn't specify any subset of actions that should be made available to the agent.

        The enumeration relies on the Actions' `shape` attribute.

        :return: An action map maps consecutive integers to a combination of Action type and parameter choices.
            An example output could be:
            {0: ("DONOTHING", {'dummy': 0}),
            1: ("NODE_OS_SCAN", {'node_id': 0}),
            2: ("NODE_OS_SCAN", {'node_id': 1}),
            3: ("NODE_FOLDER_SCAN", {'node_id:0, folder_id:0}),
            ... #etc...
            }
        :rtype: Dict[int, Tuple[AbstractAction, Dict]]
        """
        all_action_possibilities = []
        for act_name, action in self.actions.items():
            param_names = list(action.shape.keys())
            num_possibilities = list(action.shape.values())
            possibilities = [range(n) for n in num_possibilities]

            param_combinations = list(itertools.product(*possibilities))
            all_action_possibilities.extend(
                [
                    (act_name, {param_names[i]: param_combinations[j][i] for i in range(len(param_names))})
                    for j in range(len(param_combinations))
                ]
            )

        return {i: p for i, p in enumerate(all_action_possibilities)}

    def get_action(self, action: int) -> Tuple[str, Dict]:
        """Produce action in CAOS format."""
        """the agent chooses an action (as an integer), this is converted into an action in CAOS format"""
        """The CAOS format is basically a action identifier, followed by parameters stored in a dictionary"""
        act_identifier, act_options = self.action_map[action]
        return act_identifier, act_options

    def form_request(self, action_identifier: str, action_options: Dict) -> RequestFormat:
        """Take action in CAOS format and use the execution definition to change it into PrimAITE request format."""
        act_obj = self.actions[action_identifier]
        return act_obj.form_request(**action_options)

    @property
    def space(self) -> spaces.Space:
        """Return the gymnasium action space for this agent."""
        return spaces.Discrete(len(self.action_map))

    # def get_node_name_by_idx(self, node_idx: int) -> str:
    #     """
    #     Get the node name corresponding to the given index.

    #     :param node_idx: The index of the node to retrieve.
    #     :type node_idx: int
    #     :return: The node hostname.
    #     :rtype: str
    #     """
    #     if not node_idx < len(self.node_names):
    #         msg = (
    #             f"Error: agent attempted to perform an action on node {node_idx}, but its action space only"
    #             f"has {len(self.node_names)} nodes."
    #         )
    #         _LOGGER.error(msg)
    #         raise RuntimeError(msg)
    #     return self.node_names[node_idx]

    # def get_folder_name_by_idx(self, node_idx: int, folder_idx: int) -> Optional[str]:
    #     """
    #     Get the folder name corresponding to the given node and folder indices.

    #     :param node_idx: The index of the node.
    #     :type node_idx: int
    #     :param folder_idx: The index of the folder on the node.
    #     :type folder_idx: int
    #     :return: The name of the folder. Or None if the node has fewer folders than the given index.
    #     :rtype: Optional[str]
    #     """
    #     if node_idx >= len(self.folder_names) or folder_idx >= len(self.folder_names[node_idx]):
    #         msg = (
    #             f"Error: agent attempted to perform an action on node {node_idx} and folder {folder_idx}, but this"
    #             f" is out of range for its action space.   Folder on each node:  {self.folder_names}"
    #         )
    #         _LOGGER.error(msg)
    #         raise RuntimeError(msg)
    #     return self.folder_names[node_idx][folder_idx]

    # def get_file_name_by_idx(self, node_idx: int, folder_idx: int, file_idx: int) -> Optional[str]:
    #     """Get the file name corresponding to the given node, folder, and file indices.

    #     :param node_idx: The index of the node.
    #     :type node_idx: int
    #     :param folder_idx: The index of the folder on the node.
    #     :type folder_idx: int
    #     :param file_idx: The index of the file in the folder.
    #     :type file_idx: int
    #     :return: The name of the file. Or None if the node has fewer folders than the given index, or the folder has
    #         fewer files than the given index.
    #     :rtype: Optional[str]
    #     """
    #     if (
    #         node_idx >= len(self.file_names)
    #         or folder_idx >= len(self.file_names[node_idx])
    #         or file_idx >= len(self.file_names[node_idx][folder_idx])
    #     ):
    #         msg = (
    #             f"Error: agent attempted to perform an action on node {node_idx} folder {folder_idx} file {file_idx}"
    #             f" but this is out of range for its action space.   Files on each node:  {self.file_names}"
    #         )
    #         _LOGGER.error(msg)
    #         raise RuntimeError(msg)
    #     return self.file_names[node_idx][folder_idx][file_idx]

    # def get_service_name_by_idx(self, node_idx: int, service_idx: int) -> Optional[str]:
    #     """Get the service name corresponding to the given node and service indices.

    #     :param node_idx: The index of the node.
    #     :type node_idx: int
    #     :param service_idx: The index of the service on the node.
    #     :type service_idx: int
    #     :return: The name of the service. Or None if the node has fewer services than the given index.
    #     :rtype: Optional[str]
    #     """
    #     if node_idx >= len(self.service_names) or service_idx >= len(self.service_names[node_idx]):
    #         msg = (
    #             f"Error: agent attempted to perform an action on node {node_idx} and service {service_idx}, but this"
    #             f" is out of range for its action space.   Services on each node:  {self.service_names}"
    #         )
    #         _LOGGER.error(msg)
    #         raise RuntimeError(msg)
    #     return self.service_names[node_idx][service_idx]

    # def get_application_name_by_idx(self, node_idx: int, application_idx: int) -> Optional[str]:
    #     """Get the application name corresponding to the given node and service indices.

    #     :param node_idx: The index of the node.
    #     :type node_idx: int
    #     :param application_idx: The index of the service on the node.
    #     :type application_idx: int
    #     :return: The name of the service. Or None if the node has fewer services than the given index.
    #     :rtype: Optional[str]
    #     """
    #     if node_idx >= len(self.application_names) or application_idx >= len(self.application_names[node_idx]):
    #         msg = (
    #             f"Error: agent attempted to perform an action on node {node_idx} and app {application_idx}, but "
    #             f"this is out of range for its action space.   Applications on each node:  {self.application_names}"
    #         )
    #         _LOGGER.error(msg)
    #         raise RuntimeError(msg)
    #     return self.application_names[node_idx][application_idx]

    # def get_internet_protocol_by_idx(self, protocol_idx: int) -> str:
    #     """Get the internet protocol corresponding to the given index.

    #     :param protocol_idx: The index of the protocol to retrieve.
    #     :type protocol_idx: int
    #     :return: The protocol.
    #     :rtype: str
    #     """
    #     if protocol_idx >= len(self.protocols):
    #         msg = (
    #             f"Error: agent attempted to perform an action on protocol {protocol_idx} but this"
    #             f" is out of range for its action space.   Protocols:  {self.protocols}"
    #         )
    #         _LOGGER.error(msg)
    #         raise RuntimeError(msg)
    #     return self.protocols[protocol_idx]

    # def get_ip_address_by_idx(self, ip_idx: int) -> str:
    #     """
    #     Get the IP address corresponding to the given index.

    #     :param ip_idx: The index of the IP address to retrieve.
    #     :type ip_idx: int
    #     :return: The IP address.
    #     :rtype: str
    #     """
    #     if ip_idx >= len(self.ip_address_list):
    #         msg = (
    #             f"Error: agent attempted to perform an action on ip address {ip_idx} but this"
    #             f" is out of range for its action space.   IP address list:  {self.ip_address_list}"
    #         )
    #         _LOGGER.error(msg)
    #         raise RuntimeError(msg)
    #     return self.ip_address_list[ip_idx]

    # def get_wildcard_by_idx(self, wildcard_idx: int) -> str:
    #     """
    #     Get the IP wildcard corresponding to the given index.

    #     :param ip_idx: The index of the IP wildcard to retrieve.
    #     :type ip_idx: int
    #     :return: The wildcard address.
    #     :rtype: str
    #     """
    #     if wildcard_idx >= len(self.wildcard_list):
    #         msg = (
    #             f"Error: agent attempted to perform an action on ip wildcard {wildcard_idx} but this"
    #             f" is out of range for its action space.   Wildcard list:  {self.wildcard_list}"
    #         )
    #         _LOGGER.error(msg)
    #         raise RuntimeError(msg)
    #     return self.wildcard_list[wildcard_idx]

    # def get_port_by_idx(self, port_idx: int) -> str:
    #     """
    #     Get the port corresponding to the given index.

    #     :param port_idx: The index of the port to retrieve.
    #     :type port_idx: int
    #     :return: The port.
    #     :rtype: str
    #     """
    #     if port_idx >= len(self.ports):
    #         msg = (
    #             f"Error: agent attempted to perform an action on port {port_idx} but this"
    #             f" is out of range for its action space.   Port list:  {self.ip_address_list}"
    #         )
    #         _LOGGER.error(msg)
    #         raise RuntimeError(msg)
    #     return self.ports[port_idx]

    # def get_nic_num_by_idx(self, node_idx: int, nic_idx: int) -> int:
    #     """
    #     Get the NIC number corresponding to the given node and NIC indices.

    #     :param node_idx: The index of the node.
    #     :type node_idx: int
    #     :param nic_idx: The index of the NIC on the node.
    #     :type nic_idx: int
    #     :return: The NIC number.
    #     :rtype: int
    #     """
    #     return nic_idx + 1

    @classmethod
    def from_config(cls, game: "PrimaiteGame", cfg: Dict) -> "ActionManager":
        """
        Construct an ActionManager from a config definition.

        The action space config supports the following three sections:
            1. ``action_list``
                ``action_list`` contains a list action components which need to be included in the action space.
                Each action component has a ``type`` which maps to a subclass of AbstractAction, and additional options
                which will be passed to the action class's __init__ method during initialisation.
            2. ``action_map``
                Since the agent uses a discrete action space which acts as a flattened version of the component-based
                action space, action_map provides a mapping between an integer (chosen by the agent) and a meaningful
                action and values of parameters. For example action 0 can correspond to do nothing, action 1 can
                correspond to "NODE_SERVICE_SCAN" with ``node_id=1`` and ``service_id=1``, action 2 can be "
            3. ``options``
                ``options`` contains a dictionary of options which are passed to the ActionManager's __init__ method.
                These options are used to calculate the shape of the action space, and to provide additional information
                to the ActionManager which is required to convert the agent's action choice into a CAOS request.

        :param game: The Primaite Game to which the agent belongs.
        :type game: PrimaiteGame
        :param cfg: The action space config.
        :type cfg: Dict
        :return: The constructed ActionManager.
        :rtype: ActionManager
        """
        if "ip_list" not in cfg["options"]:
            cfg["options"]["ip_list"] = []

        obj = cls(
            actions=cfg["action_list"],
            **cfg["options"],
            protocols=game.options.protocols,
            ports=game.options.ports,
            act_map=cfg.get("action_map"),
        )

        return obj
