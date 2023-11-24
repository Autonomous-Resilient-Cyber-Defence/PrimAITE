"""
This module contains the ActionManager class which belongs to the Agent class.

An agent's action space is made up of a collection of actions. Each action is an instance of a subclass of
AbstractAction. The ActionManager is responsible for:
    1. Creating the action space from a list of action types.
    2. Converting an integer action choice into a specific action and parameter choice.
    3. Converting an action and parameter choice into a request which can be ingested by the PrimAITE simulation. This
        ensures that requests conform to the simulator's request format.
"""
import itertools
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from gymnasium import spaces

from primaite import getLogger
from primaite.simulator.sim_container import Simulation

_LOGGER = getLogger(__name__)

if TYPE_CHECKING:
    from primaite.game.game import PrimaiteGame


class AbstractAction(ABC):
    """Base class for actions."""

    @abstractmethod
    def __init__(self, manager: "ActionManager", **kwargs) -> None:
        """
        Init method for action.

        All action init functions should accept **kwargs as a way of ignoring extra arguments.

        Since many parameters are defined for the action space as a whole (such as max files per folder, max services
        per node), we need to pass those options to every action that gets created. To pervent verbosity, these
        parameters are just broadcasted to all actions and the actions can pay attention to the ones that apply.
        """
        self.name: str = ""
        """Human-readable action identifier used for printing, logging, and reporting."""
        self.shape: Dict[str, int] = {}
        """Dictionary describing the number of options for each parameter of this action. The keys of this dict must
        align with the keyword args of the form_request method."""
        self.manager: ActionManager = manager
        """Reference to the ActionManager which created this action. This is used to access the game and simulation
        objects."""

    @abstractmethod
    def form_request(self) -> List[str]:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return []


class DoNothingAction(AbstractAction):
    """Action which does nothing. This is here to allow agents to be idle if they choose to."""

    def __init__(self, manager: "ActionManager", **kwargs) -> None:
        super().__init__(manager=manager)
        self.name = "DONOTHING"
        self.shape: Dict[str, int] = {
            "dummy": 1,
        }
        # This action does not accept any parameters, therefore it technically has a gymnasium shape of Discrete(1),
        # i.e. a choice between one option. To make enumerating this action easier, we are adding a 'dummy' paramter
        # with one option. This just aids the Action Manager to enumerate all possibilities.

    def form_request(self, **kwargs) -> List[str]:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return ["do_nothing"]


class NodeServiceAbstractAction(AbstractAction):
    """
    Base class for service actions.

    Any action which applies to a service and uses node_id and service_id as its only two parameters can inherit from
    this base class.
    """

    @abstractmethod
    def __init__(self, manager: "ActionManager", num_nodes: int, num_services: int, **kwargs) -> None:
        super().__init__(manager=manager)
        self.shape: Dict[str, int] = {"node_id": num_nodes, "service_id": num_services}
        self.verb: str

    def form_request(self, node_id: int, service_id: int) -> List[str]:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        node_uuid = self.manager.get_node_uuid_by_idx(node_id)
        service_uuid = self.manager.get_service_uuid_by_idx(node_id, service_id)
        if node_uuid is None or service_uuid is None:
            return ["do_nothing"]
        return ["network", "node", node_uuid, "services", service_uuid, self.verb]


class NodeServiceScanAction(NodeServiceAbstractAction):
    """Action which scans a service."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_services: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes, num_services=num_services)
        self.verb = "scan"


class NodeServiceStopAction(NodeServiceAbstractAction):
    """Action which stops a service."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_services: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes, num_services=num_services)
        self.verb = "stop"


class NodeServiceStartAction(NodeServiceAbstractAction):
    """Action which starts a service."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_services: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes, num_services=num_services)
        self.verb = "start"


class NodeServicePauseAction(NodeServiceAbstractAction):
    """Action which pauses a service."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_services: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes, num_services=num_services)
        self.verb = "pause"


class NodeServiceResumeAction(NodeServiceAbstractAction):
    """Action which resumes a service."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_services: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes, num_services=num_services)
        self.verb = "resume"


class NodeServiceRestartAction(NodeServiceAbstractAction):
    """Action which restarts a service."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_services: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes, num_services=num_services)
        self.verb = "restart"


class NodeServiceDisableAction(NodeServiceAbstractAction):
    """Action which disables a service."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_services: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes, num_services=num_services)
        self.verb = "disable"


class NodeServiceEnableAction(NodeServiceAbstractAction):
    """Action which enables a service."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_services: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes, num_services=num_services)
        self.verb = "enable"


class NodeFolderAbstractAction(AbstractAction):
    """
    Base class for folder actions.

    Any action which applies to a folder and uses node_id and folder_id as its only two parameters can inherit from
    this base class.
    """

    @abstractmethod
    def __init__(self, manager: "ActionManager", num_nodes: int, num_folders: int, **kwargs) -> None:
        super().__init__(manager=manager)
        self.shape: Dict[str, int] = {"node_id": num_nodes, "folder_id": num_folders}
        self.verb: str

    def form_request(self, node_id: int, folder_id: int) -> List[str]:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        node_uuid = self.manager.get_node_uuid_by_idx(node_id)
        folder_uuid = self.manager.get_folder_uuid_by_idx(node_idx=node_id, folder_idx=folder_id)
        if node_uuid is None or folder_uuid is None:
            return ["do_nothing"]
        return ["network", "node", node_uuid, "file_system", "folder", folder_uuid, self.verb]


class NodeFolderScanAction(NodeFolderAbstractAction):
    """Action which scans a folder."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_folders: int, **kwargs) -> None:
        super().__init__(manager, num_nodes=num_nodes, num_folders=num_folders, **kwargs)
        self.verb: str = "scan"


class NodeFolderCheckhashAction(NodeFolderAbstractAction):
    """Action which checks the hash of a folder."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_folders: int, **kwargs) -> None:
        super().__init__(manager, num_nodes=num_nodes, num_folders=num_folders, **kwargs)
        self.verb: str = "checkhash"


class NodeFolderRepairAction(NodeFolderAbstractAction):
    """Action which repairs a folder."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_folders: int, **kwargs) -> None:
        super().__init__(manager, num_nodes=num_nodes, num_folders=num_folders, **kwargs)
        self.verb: str = "repair"


class NodeFolderRestoreAction(NodeFolderAbstractAction):
    """Action which restores a folder."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_folders: int, **kwargs) -> None:
        super().__init__(manager, num_nodes=num_nodes, num_folders=num_folders, **kwargs)
        self.verb: str = "restore"


class NodeFileAbstractAction(AbstractAction):
    """Abstract base class for file actions.

    Any action which applies to a file and uses node_id, folder_id, and file_id as its only three parameters can inherit
    from this base class.
    """

    @abstractmethod
    def __init__(self, manager: "ActionManager", num_nodes: int, num_folders: int, num_files: int, **kwargs) -> None:
        super().__init__(manager=manager)
        self.shape: Dict[str, int] = {"node_id": num_nodes, "folder_id": num_folders, "file_id": num_files}
        self.verb: str

    def form_request(self, node_id: int, folder_id: int, file_id: int) -> List[str]:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        node_uuid = self.manager.get_node_uuid_by_idx(node_id)
        folder_uuid = self.manager.get_folder_uuid_by_idx(node_idx=node_id, folder_idx=folder_id)
        file_uuid = self.manager.get_file_uuid_by_idx(node_idx=node_id, folder_idx=folder_id, file_idx=file_id)
        if node_uuid is None or folder_uuid is None or file_uuid is None:
            return ["do_nothing"]
        return ["network", "node", node_uuid, "file_system", "folder", folder_uuid, "files", file_uuid, self.verb]


class NodeFileScanAction(NodeFileAbstractAction):
    """Action which scans a file."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_folders: int, num_files: int, **kwargs) -> None:
        super().__init__(manager, num_nodes=num_nodes, num_folders=num_folders, num_files=num_files, **kwargs)
        self.verb = "scan"


class NodeFileCheckhashAction(NodeFileAbstractAction):
    """Action which checks the hash of a file."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_folders: int, num_files: int, **kwargs) -> None:
        super().__init__(manager, num_nodes=num_nodes, num_folders=num_folders, num_files=num_files, **kwargs)
        self.verb = "checkhash"


class NodeFileDeleteAction(NodeFileAbstractAction):
    """Action which deletes a file."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_folders: int, num_files: int, **kwargs) -> None:
        super().__init__(manager, num_nodes=num_nodes, num_folders=num_folders, num_files=num_files, **kwargs)
        self.verb = "delete"


class NodeFileRepairAction(NodeFileAbstractAction):
    """Action which repairs a file."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_folders: int, num_files: int, **kwargs) -> None:
        super().__init__(manager, num_nodes=num_nodes, num_folders=num_folders, num_files=num_files, **kwargs)
        self.verb = "repair"


class NodeFileRestoreAction(NodeFileAbstractAction):
    """Action which restores a file."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_folders: int, num_files: int, **kwargs) -> None:
        super().__init__(manager, num_nodes=num_nodes, num_folders=num_folders, num_files=num_files, **kwargs)
        self.verb = "restore"


class NodeFileCorruptAction(NodeFileAbstractAction):
    """Action which corrupts a file."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_folders: int, num_files: int, **kwargs) -> None:
        super().__init__(manager, num_nodes=num_nodes, num_folders=num_folders, num_files=num_files, **kwargs)
        self.verb = "corrupt"


class NodeAbstractAction(AbstractAction):
    """
    Abstract base class for node actions.

    Any action which applies to a node and uses node_id as its only parameter can inherit from this base class.
    """

    @abstractmethod
    def __init__(self, manager: "ActionManager", num_nodes: int, **kwargs) -> None:
        super().__init__(manager=manager)
        self.shape: Dict[str, int] = {"node_id": num_nodes}
        self.verb: str

    def form_request(self, node_id: int) -> List[str]:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        node_uuid = self.manager.get_node_uuid_by_idx(node_id)
        return ["network", "node", node_uuid, self.verb]


class NodeOSScanAction(NodeAbstractAction):
    """Action which scans a node's OS."""

    def __init__(self, manager: "ActionManager", num_nodes: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes)
        self.verb = "scan"


class NodeShutdownAction(NodeAbstractAction):
    """Action which shuts down a node."""

    def __init__(self, manager: "ActionManager", num_nodes: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes)
        self.verb = "shutdown"


class NodeStartupAction(NodeAbstractAction):
    """Action which starts up a node."""

    def __init__(self, manager: "ActionManager", num_nodes: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes)
        self.verb = "startup"


class NodeResetAction(NodeAbstractAction):
    """Action which resets a node."""

    def __init__(self, manager: "ActionManager", num_nodes: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes)
        self.verb = "reset"


class NetworkACLAddRuleAction(AbstractAction):
    """Action which adds a rule to a router's ACL."""

    def __init__(
        self,
        manager: "ActionManager",
        target_router_uuid: str,
        max_acl_rules: int,
        num_ips: int,
        num_ports: int,
        num_protocols: int,
        **kwargs,
    ) -> None:
        """Init method for NetworkACLAddRuleAction.

        :param manager: Reference to the ActionManager which created this action.
        :type manager: ActionManager
        :param target_router_uuid: UUID of the router to which the ACL rule should be added.
        :type target_router_uuid: str
        :param max_acl_rules: Maximum number of ACL rules that can be added to the router.
        :type max_acl_rules: int
        :param num_ips: Number of IP addresses in the simulation.
        :type num_ips: int
        :param num_ports: Number of ports in the simulation.
        :type num_ports: int
        :param num_protocols: Number of protocols in the simulation.
        :type num_protocols: int
        """
        super().__init__(manager=manager)
        num_permissions = 3
        self.shape: Dict[str, int] = {
            "position": max_acl_rules,
            "permission": num_permissions,
            "source_ip_id": num_ips,
            "dest_ip_id": num_ips,
            "source_port_id": num_ports,
            "dest_port_id": num_ports,
            "protocol_id": num_protocols,
        }
        self.target_router_uuid: str = target_router_uuid

    def form_request(
        self,
        position: int,
        permission: int,
        source_ip_id: int,
        dest_ip_id: int,
        source_port_id: int,
        dest_port_id: int,
        protocol_id: int,
    ) -> List[str]:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        if permission == 0:
            permission_str = "UNUSED"
            return ["do_nothing"]  # NOT SUPPORTED, JUST DO NOTHING IF WE COME ACROSS THIS
        elif permission == 1:
            permission_str = "ALLOW"
        elif permission == 2:
            permission_str = "DENY"
        else:
            _LOGGER.warn(f"{self.__class__} received permission {permission}, expected 0 or 1.")

        if protocol_id == 0:
            return ["do_nothing"]  # NOT SUPPORTED, JUST DO NOTHING IF WE COME ACROSS THIS

        if protocol_id == 1:
            protocol = "ALL"
        else:
            protocol = self.manager.get_internet_protocol_by_idx(protocol_id - 2)
            # subtract 2 to account for UNUSED=0 and ALL=1.

        if source_ip_id in [0, 1]:
            src_ip = "ALL"
            return ["do_nothing"]  # NOT SUPPORTED, JUST DO NOTHING IF WE COME ACROSS THIS
        else:
            src_ip = self.manager.get_ip_address_by_idx(source_ip_id - 2)
            # subtract 2 to account for UNUSED=0, and ALL=1

        if source_port_id == 1:
            src_port = "ALL"
        else:
            src_port = self.manager.get_port_by_idx(source_port_id - 2)
            # subtract 2 to account for UNUSED=0, and ALL=1

        if dest_ip_id in (0, 1):
            dst_ip = "ALL"
            return ["do_nothing"]  # NOT SUPPORTED, JUST DO NOTHING IF WE COME ACROSS THIS
        else:
            dst_ip = self.manager.get_ip_address_by_idx(dest_ip_id)
            # subtract 2 to account for UNUSED=0, and ALL=1

        if dest_port_id == 1:
            dst_port = "ALL"
        else:
            dst_port = self.manager.get_port_by_idx(dest_port_id)
            # subtract 2 to account for UNUSED=0, and ALL=1

        return [
            "network",
            "node",
            self.target_router_uuid,
            "acl",
            "add_rule",
            permission_str,
            protocol,
            src_ip,
            src_port,
            dst_ip,
            dst_port,
            position,
        ]


class NetworkACLRemoveRuleAction(AbstractAction):
    """Action which removes a rule from a router's ACL."""

    def __init__(self, manager: "ActionManager", target_router_uuid: str, max_acl_rules: int, **kwargs) -> None:
        """Init method for NetworkACLRemoveRuleAction.

        :param manager: Reference to the ActionManager which created this action.
        :type manager: ActionManager
        :param target_router_uuid: UUID of the router from which the ACL rule should be removed.
        :type target_router_uuid: str
        :param max_acl_rules: Maximum number of ACL rules that can be added to the router.
        :type max_acl_rules: int
        """
        super().__init__(manager=manager)
        self.shape: Dict[str, int] = {"position": max_acl_rules}
        self.target_router_uuid: str = target_router_uuid

    def form_request(self, position: int) -> List[str]:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return ["network", "node", self.target_router_uuid, "acl", "remove_rule", position]


class NetworkNICAbstractAction(AbstractAction):
    """
    Abstract base class for NIC actions.

    Any action which applies to a NIC and uses node_id and nic_id as its only two parameters can inherit from this base
    class.
    """

    def __init__(self, manager: "ActionManager", num_nodes: int, max_nics_per_node: int, **kwargs) -> None:
        """Init method for NetworkNICAbstractAction.

        :param manager: Reference to the ActionManager which created this action.
        :type manager: ActionManager
        :param num_nodes: Number of nodes in the simulation.
        :type num_nodes: int
        :param max_nics_per_node: Maximum number of NICs per node.
        :type max_nics_per_node: int
        """
        super().__init__(manager=manager)
        self.shape: Dict[str, int] = {"node_id": num_nodes, "nic_id": max_nics_per_node}
        self.verb: str

    def form_request(self, node_id: int, nic_id: int) -> List[str]:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        node_uuid = self.manager.get_node_uuid_by_idx(node_idx=node_id)
        nic_uuid = self.manager.get_nic_uuid_by_idx(node_idx=node_id, nic_idx=nic_id)
        if node_uuid is None or nic_uuid is None:
            return ["do_nothing"]
        return [
            "network",
            "node",
            node_uuid,
            "nic",
            nic_uuid,
            self.verb,
        ]


class NetworkNICEnableAction(NetworkNICAbstractAction):
    """Action which enables a NIC."""

    def __init__(self, manager: "ActionManager", num_nodes: int, max_nics_per_node: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes, max_nics_per_node=max_nics_per_node, **kwargs)
        self.verb = "enable"


class NetworkNICDisableAction(NetworkNICAbstractAction):
    """Action which disables a NIC."""

    def __init__(self, manager: "ActionManager", num_nodes: int, max_nics_per_node: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes, max_nics_per_node=max_nics_per_node, **kwargs)
        self.verb = "disable"


class ActionManager:
    """Class which manages the action space for an agent."""

    __act_class_identifiers: Dict[str, type] = {
        "DONOTHING": DoNothingAction,
        "NODE_SERVICE_SCAN": NodeServiceScanAction,
        "NODE_SERVICE_STOP": NodeServiceStopAction,
        "NODE_SERVICE_START": NodeServiceStartAction,
        "NODE_SERVICE_PAUSE": NodeServicePauseAction,
        "NODE_SERVICE_RESUME": NodeServiceResumeAction,
        "NODE_SERVICE_RESTART": NodeServiceRestartAction,
        "NODE_SERVICE_DISABLE": NodeServiceDisableAction,
        "NODE_SERVICE_ENABLE": NodeServiceEnableAction,
        "NODE_FILE_SCAN": NodeFileScanAction,
        "NODE_FILE_CHECKHASH": NodeFileCheckhashAction,
        "NODE_FILE_DELETE": NodeFileDeleteAction,
        "NODE_FILE_REPAIR": NodeFileRepairAction,
        "NODE_FILE_RESTORE": NodeFileRestoreAction,
        "NODE_FILE_CORRUPT": NodeFileCorruptAction,
        "NODE_FOLDER_SCAN": NodeFolderScanAction,
        "NODE_FOLDER_CHECKHASH": NodeFolderCheckhashAction,
        "NODE_FOLDER_REPAIR": NodeFolderRepairAction,
        "NODE_FOLDER_RESTORE": NodeFolderRestoreAction,
        "NODE_OS_SCAN": NodeOSScanAction,
        "NODE_SHUTDOWN": NodeShutdownAction,
        "NODE_STARTUP": NodeStartupAction,
        "NODE_RESET": NodeResetAction,
        "NETWORK_ACL_ADDRULE": NetworkACLAddRuleAction,
        "NETWORK_ACL_REMOVERULE": NetworkACLRemoveRuleAction,
        "NETWORK_NIC_ENABLE": NetworkNICEnableAction,
        "NETWORK_NIC_DISABLE": NetworkNICDisableAction,
    }
    """Dictionary which maps action type strings to the corresponding action class."""

    def __init__(
        self,
        game: "PrimaiteGame",  # reference to game for information lookup
        actions: List[str],  # stores list of actions available to agent
        node_uuids: List[str],  # allows mapping index to node
        max_folders_per_node: int = 2,  # allows calculating shape
        max_files_per_folder: int = 2,  # allows calculating shape
        max_services_per_node: int = 2,  # allows calculating shape
        max_nics_per_node: int = 8,  # allows calculating shape
        max_acl_rules: int = 10,  # allows calculating shape
        protocols: List[str] = ["TCP", "UDP", "ICMP"],  # allow mapping index to protocol
        ports: List[str] = ["HTTP", "DNS", "ARP", "FTP"],  # allow mapping index to port
        ip_address_list: Optional[List[str]] = None,  # to allow us to map an index to an ip address.
        act_map: Optional[Dict[int, Dict]] = None,  # allows restricting set of possible actions
    ) -> None:
        """Init method for ActionManager.

        :param game: Reference to the game to which the agent belongs.
        :type game: PrimaiteGame
        :param actions: List of action types which should be made available to the agent.
        :type actions: List[str]
        :param node_uuids: List of node UUIDs that this agent can act on.
        :type node_uuids: List[str]
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
        :param ip_address_list: List of IP addresses that known to this agent. Used for calculating action shape.
        :type ip_address_list: Optional[List[str]]
        :param act_map: Action map which maps integers to actions. Used for restricting the set of possible actions.
        :type act_map: Optional[Dict[int, Dict]]
        """
        self.game: "PrimaiteGame" = game
        self.sim: Simulation = self.game.simulation
        self.node_uuids: List[str] = node_uuids
        self.protocols: List[str] = protocols
        self.ports: List[str] = ports

        self.ip_address_list: List[str]
        if ip_address_list is not None:
            self.ip_address_list = ip_address_list
        else:
            self.ip_address_list = []
            for node_uuid in self.node_uuids:
                node_obj = self.sim.network.nodes[node_uuid]
                nics = node_obj.nics
                for nic_uuid, nic_obj in nics.items():
                    self.ip_address_list.append(nic_obj.ip_address)

        # action_args are settings which are applied to the action space as a whole.
        global_action_args = {
            "num_nodes": len(node_uuids),
            "num_folders": max_folders_per_node,
            "num_files": max_files_per_folder,
            "num_services": max_services_per_node,
            "num_nics": max_nics_per_node,
            "num_acl_rules": max_acl_rules,
            "num_protocols": len(self.protocols),
            "num_ports": len(self.protocols),
            "num_ips": len(self.ip_address_list),
            "max_acl_rules": max_acl_rules,
            "max_nics_per_node": max_nics_per_node,
        }
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
            self.actions[act_type] = self.__act_class_identifiers[act_type](self, **global_action_args, **act_options)

        self.action_map: Dict[int, Tuple[str, Dict]] = {}
        """
        Action mapping that converts an integer to a specific action and parameter choice.

        For example :
        {0: ("NODE_SERVICE_SCAN", {node_id:0, service_id:2})}
        """
        if act_map is None:
            self.action_map = self._enumerate_actions()
        else:
            self.action_map = {i: (a["action"], a["options"]) for i, a in act_map.items()}
        # make sure all numbers between 0 and N are represented as dict keys in action map
        assert all([i in self.action_map.keys() for i in range(len(self.action_map))])

    def _enumerate_actions(
        self,
    ) -> Dict[int, Tuple[str, Dict]]:
        """Generate a list of all the possible actions that could be taken.

        This enumerates all actions all combinations of parametes you could choose for those actions. The output
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

    def form_request(self, action_identifier: str, action_options: Dict) -> List[str]:
        """Take action in CAOS format and use the execution definition to change it into PrimAITE request format."""
        act_obj = self.actions[action_identifier]
        return act_obj.form_request(**action_options)

    @property
    def space(self) -> spaces.Space:
        """Return the gymnasium action space for this agent."""
        return spaces.Discrete(len(self.action_map))

    def get_node_uuid_by_idx(self, node_idx: int) -> str:
        """
        Get the node UUID corresponding to the given index.

        :param node_idx: The index of the node to retrieve.
        :type node_idx: int
        :return: The node UUID.
        :rtype: str
        """
        return self.node_uuids[node_idx]

    def get_folder_uuid_by_idx(self, node_idx: int, folder_idx: int) -> Optional[str]:
        """
        Get the folder UUID corresponding to the given node and folder indices.

        :param node_idx: The index of the node.
        :type node_idx: int
        :param folder_idx: The index of the folder on the node.
        :type folder_idx: int
        :return: The UUID of the folder. Or None if the node has fewer folders than the given index.
        :rtype: Optional[str]
        """
        node_uuid = self.get_node_uuid_by_idx(node_idx)
        node = self.sim.network.nodes[node_uuid]
        folder_uuids = list(node.file_system.folders.keys())
        return folder_uuids[folder_idx] if len(folder_uuids) > folder_idx else None

    def get_file_uuid_by_idx(self, node_idx: int, folder_idx: int, file_idx: int) -> Optional[str]:
        """Get the file UUID corresponding to the given node, folder, and file indices.

        :param node_idx: The index of the node.
        :type node_idx: int
        :param folder_idx: The index of the folder on the node.
        :type folder_idx: int
        :param file_idx: The index of the file in the folder.
        :type file_idx: int
        :return: The UUID of the file. Or None if the node has fewer folders than the given index, or the folder has
            fewer files than the given index.
        :rtype: Optional[str]
        """
        node_uuid = self.get_node_uuid_by_idx(node_idx)
        node = self.sim.network.nodes[node_uuid]
        folder_uuids = list(node.file_system.folders.keys())
        if len(folder_uuids) <= folder_idx:
            return None
        folder = node.file_system.folders[folder_uuids[folder_idx]]
        file_uuids = list(folder.files.keys())
        return file_uuids[file_idx] if len(file_uuids) > file_idx else None

    def get_service_uuid_by_idx(self, node_idx: int, service_idx: int) -> Optional[str]:
        """Get the service UUID corresponding to the given node and service indices.

        :param node_idx: The index of the node.
        :type node_idx: int
        :param service_idx: The index of the service on the node.
        :type service_idx: int
        :return: The UUID of the service. Or None if the node has fewer services than the given index.
        :rtype: Optional[str]
        """
        node_uuid = self.get_node_uuid_by_idx(node_idx)
        node = self.sim.network.nodes[node_uuid]
        service_uuids = list(node.services.keys())
        return service_uuids[service_idx] if len(service_uuids) > service_idx else None

    def get_internet_protocol_by_idx(self, protocol_idx: int) -> str:
        """Get the internet protocol corresponding to the given index.

        :param protocol_idx: The index of the protocol to retrieve.
        :type protocol_idx: int
        :return: The protocol.
        :rtype: str
        """
        return self.protocols[protocol_idx]

    def get_ip_address_by_idx(self, ip_idx: int) -> str:
        """
        Get the IP address corresponding to the given index.

        :param ip_idx: The index of the IP address to retrieve.
        :type ip_idx: int
        :return: The IP address.
        :rtype: str
        """
        return self.ip_address_list[ip_idx]

    def get_port_by_idx(self, port_idx: int) -> str:
        """
        Get the port corresponding to the given index.

        :param port_idx: The index of the port to retrieve.
        :type port_idx: int
        :return: The port.
        :rtype: str
        """
        return self.ports[port_idx]

    def get_nic_uuid_by_idx(self, node_idx: int, nic_idx: int) -> str:
        """
        Get the NIC UUID corresponding to the given node and NIC indices.

        :param node_idx: The index of the node.
        :type node_idx: int
        :param nic_idx: The index of the NIC on the node.
        :type nic_idx: int
        :return: The NIC UUID.
        :rtype: str
        """
        node_uuid = self.get_node_uuid_by_idx(node_idx)
        node_obj = self.sim.network.nodes[node_uuid]
        nics = list(node_obj.nics.keys())
        if len(nics) <= nic_idx:
            return None
        return nics[nic_idx]

    @classmethod
    def from_config(cls, game: "PrimaiteGame", cfg: Dict) -> "ActionManager":
        """
        Construct an ActionManager from a config definition.

        The action space config supports the following three sections:
            1. ``action_list``
                ``action_list`` contians a list action components which need to be included in the action space.
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
        obj = cls(
            game=game,
            actions=cfg["action_list"],
            # node_uuids=cfg["options"]["node_uuids"],
            **cfg["options"],
            protocols=game.options.protocols,
            ports=game.options.ports,
            ip_address_list=None,
            act_map=cfg.get("action_map"),
        )

        return obj
