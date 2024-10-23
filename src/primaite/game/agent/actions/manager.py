# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
"""yaml example.

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
from typing import Dict, List, Literal, Optional, Tuple

from gymnasium import spaces

# from primaite.game.game import PrimaiteGame # TODO: Breaks things
from primaite.game.agent.actions.abstract import AbstractAction
from primaite.interface.request import RequestFormat

# TODO: Make sure that actions are backwards compatible where the old YAML format is used.


class DoNothingAction(AbstractAction, identifier="do_nothing"):
    """Do Nothing Action."""

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Configuration Schema for DoNothingAction."""

        type: Literal["do_nothing"] = "do_nothing"

    def form_request(self, options: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
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
        *args,
        **kwargs,
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
        # self.node_names: List[str] = [n["node_name"] for n in nodes]
        """List of node names in this action space. The list order is the mapping between node index and node name."""
        # self.application_names: List[List[str]] = []
        """
        List of applications per node. The list order gives the two-index mapping between (node_id, app_id) to app name.
        The first index corresponds to node id, the second index is the app id on that particular node.
        For instance, self.application_names[0][2] is the name of the third application on the first node.
        """
        # self.service_names: List[List[str]] = []
        """
        List of services per node. The list order gives the two-index mapping between (node_id, svc_id) to svc name.
        The first index corresponds to node id, the second index is the service id on that particular node.
        For instance, self.service_names[0][2] is the name of the third service on the first node.
        """
        # self.folder_names: List[List[str]] = []
        """
        List of folders per node. The list order gives the two-index mapping between (node_id, folder_id) to folder
        name. The first index corresponds to node id, the second index is the folder id on that particular node.
        For instance, self.folder_names[0][2] is the name of the third folder on the first node.
        """
        # self.file_names: List[List[List[str]]] = []
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
            # act_options = act_spec.get("options", {}) # Don't need this anymore I think?
            self.actions[act_type] = AbstractAction._registry[act_type]

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
            {0: ("do_nothing", {'dummy': 0}),
            1: ("node_os_scan", {'node_name': computer}),
            2: ("node_os_scan", {'node_name': server}),
            3: ("node_folder_scan", {'node_name:computer, folder_name:downloads}),
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
        return act_obj.form_request(action_options)

    @property
    def space(self) -> spaces.Space:
        """Return the gymnasium action space for this agent."""
        return spaces.Discrete(len(self.action_map))

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
