import itertools
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from gym import spaces

from primaite.game.session import PrimaiteSession
from primaite.simulator.sim_container import Simulation


class ExecutionDefiniton(ABC):
    """
    Converter from actions to simulator requests.

    Allows adding extra data/context that defines in more detail what an action means.
    """

    """
    Examples:
    ('node', 'service', 'scan', 2, 0) means scan the first service on node index 2
        -> ['network', 'nodes', <node-idx-2-uuid>, 'services', <svc-idx-0-uuid>, 'scan'w]
    """
    ...


class AbstractAction(ABC):
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

    @abstractmethod
    def form_request(self) -> List[str]:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return []


class DoNothingAction(AbstractAction):
    def __init__(self, manager: "ActionManager", **kwargs) -> None:
        super().__init__(manager=manager)
        self.name = "DONOTHING"
        self.shape: Dict[str, int] = {
            "dummy": 1,
        }
        # This action does not accept any parameters, therefore it technically has a gymnasium shape of Discrete(1),
        # i.e. a choice between one option. To make enumerating this action easier, we are adding a 'dummy' paramter
        # with one option. This just aids the Action Manager to enumerate all possibilities.

    def form_request(self) -> List[str]:
        return ["do_nothing"]


class NodeServiceAbstractAction(AbstractAction):
    """
    Base class for service actions.

    Any action which applies to a service and uses node_id and service_id as its only two parameters can inherit from
    this base class.
    """

    @abstractmethod
    def __init__(self, manager: "ActionManager", num_nodes, num_services, **kwargs) -> None:
        super().__init__(manager=manager)
        self.shape: Dict[str, int] = {"node_id": num_nodes, "service_id": num_services}
        self.verb: str

    def form_request(self, node_id: int, service_id: int) -> List[str]:
        node_uuid = self.manager.get_node_uuid_by_idx(node_id)
        service_uuid = self.manager.get_service_uuid_by_idx(node_id, service_id)
        if node_uuid is None or service_uuid is None:
            return ["do_nothing"]
        return ["network", "node", node_uuid, "services", service_uuid, self.verb]


class NodeServiceScanAction(NodeServiceAbstractAction):
    def __init__(self, manager: "ActionManager", num_nodes, num_services, **kwargs) -> None:
        super().__init__(manager=manager)
        self.verb = "scan"


class NodeServiceStopAction(NodeServiceAbstractAction):
    def __init__(self, manager: "ActionManager", num_nodes, num_services, **kwargs) -> None:
        super().__init__(manager=manager)
        self.verb = "stop"


class NodeServiceStartAction(NodeServiceAbstractAction):
    def __init__(self, manager: "ActionManager", num_nodes, num_services, **kwargs) -> None:
        super().__init__(manager=manager)
        self.verb = "start"


class NodeServicePauseAction(NodeServiceAbstractAction):
    def __init__(self, manager: "ActionManager", num_nodes, num_services, **kwargs) -> None:
        super().__init__(manager=manager)
        self.verb = "pause"


class NodeServiceResumeAction(NodeServiceAbstractAction):
    def __init__(self, manager: "ActionManager", num_nodes, num_services, **kwargs) -> None:
        super().__init__(manager=manager)
        self.verb = "resume"


class NodeServiceRestartAction(NodeServiceAbstractAction):
    def __init__(self, manager: "ActionManager", num_nodes, num_services, **kwargs) -> None:
        super().__init__(manager=manager)
        self.verb = "restart"


class NodeServiceDisableAction(NodeServiceAbstractAction):
    def __init__(self, manager: "ActionManager", num_nodes, num_services, **kwargs) -> None:
        super().__init__(manager=manager)
        self.verb = "disable"


class NodeServiceEnableAction(NodeServiceAbstractAction):
    def __init__(self, manager: "ActionManager", num_nodes, num_services, **kwargs) -> None:
        super().__init__(manager=manager)
        self.verb = "enable"


class NodeFolderAbstractAction(AbstractAction):
    @abstractmethod
    def __init__(self, manager: "ActionManager", num_nodes, num_folders, **kwargs) -> None:
        super().__init__(manager=manager)
        self.shape: Dict[str, int] = {"node_id": num_nodes, "folder_id": num_folders}
        self.verb: str

    def form_request(self, node_id: int, folder_id: int) -> List[str]:
        node_uuid = self.manager.get_node_uuid_by_idx(node_id)
        folder_uuid = self.manager.get_folder_uuid_by_idx(node_idx=node_id, folder_idx=folder_id)
        if node_uuid is None or folder_uuid is None:
            return ["do_nothing"]
        return ["network", "node", node_uuid, "file_system", "folder", folder_uuid, self.verb]


class NodeFolderScanAction(NodeFolderAbstractAction):
    def __init__(self, manager: "ActionManager", num_nodes, num_folders, **kwargs) -> None:
        super().__init__(manager, num_nodes, num_folders, **kwargs)
        self.verb: str = "scan"


class NodeFolderCheckhashAction(NodeFolderAbstractAction):
    def __init__(self, manager: "ActionManager", num_nodes, num_folders, **kwargs) -> None:
        super().__init__(manager, num_nodes, num_folders, **kwargs)
        self.verb: str = "checkhash"


class NodeFolderRepairAction(NodeFolderAbstractAction):
    def __init__(self, manager: "ActionManager", num_nodes, num_folders, **kwargs) -> None:
        super().__init__(manager, num_nodes, num_folders, **kwargs)
        self.verb: str = "repair"


class NodeFolderRestoreAction(NodeFolderAbstractAction):
    def __init__(self, manager: "ActionManager", num_nodes, num_folders, **kwargs) -> None:
        super().__init__(manager, num_nodes, num_folders, **kwargs)
        self.verb: str = "restore"


class NodeFileAbstractAction(AbstractAction):
    @abstractmethod
    def __init__(self, manager: "ActionManager", num_nodes: int, num_folders: int, num_files: int, **kwargs) -> None:
        super().__init__(manager=manager)
        self.shape: Dict[str, int] = {"node_id": num_nodes, "folder_id": num_folders, "file_id": num_files}
        self.verb: str

    def form_request(self, node_id: int, folder_id: int, file_id: int) -> List[str]:
        node_uuid = self.manager.get_node_uuid_by_idx(node_id)
        folder_uuid = self.manager.get_folder_uuid_by_idx(node_idx=node_id, folder_idx=folder_id)
        file_uuid = self.manager.get_file_uuid_by_idx(node_idx=node_id, folder_idx=folder_id, file_idx=file_id)
        if node_uuid is None or folder_uuid is None or file_uuid is None:
            return ["do_nothing"]
        return ["network", "node", node_uuid, "file_system", "folder", folder_uuid, "files", file_uuid, self.verb]


class NodeFileScanAction(NodeFileAbstractAction):
    def __init__(self, manager: "ActionManager", num_nodes: int, num_folders: int, num_files: int, **kwargs) -> None:
        super().__init__(manager, num_nodes, num_folders, num_files, **kwargs)
        self.verb = "scan"


class NodeFileCheckhashAction(NodeFileAbstractAction):
    def __init__(self, manager: "ActionManager", num_nodes: int, num_folders: int, num_files: int, **kwargs) -> None:
        super().__init__(manager, num_nodes, num_folders, num_files, **kwargs)
        self.verb = "checkhash"


class NodeFileDeleteAction(NodeFileAbstractAction):
    def __init__(self, manager: "ActionManager", num_nodes: int, num_folders: int, num_files: int, **kwargs) -> None:
        super().__init__(manager, num_nodes, num_folders, num_files, **kwargs)
        self.verb = "delete"


class NodeFileRepairAction(NodeFileAbstractAction):
    def __init__(self, manager: "ActionManager", num_nodes: int, num_folders: int, num_files: int, **kwargs) -> None:
        super().__init__(manager, num_nodes, num_folders, num_files, **kwargs)
        self.verb = "repair"


class NodeFileRestoreAction(NodeFileAbstractAction):
    def __init__(self, manager: "ActionManager", num_nodes: int, num_folders: int, num_files: int, **kwargs) -> None:
        super().__init__(manager, num_nodes, num_folders, num_files, **kwargs)
        self.verb = "restore"


class NodeAbstractAction(AbstractAction):
    @abstractmethod
    def __init__(self, manager: "ActionManager", num_nodes: int, **kwargs) -> None:
        super().__init__(manager=manager)
        self.shape: Dict[str, int] = {"node_id": num_nodes}
        self.verb: str

    def form_request(self, node_id: int) -> List[str]:
        node_uuid = self.manager.get_node_uuid_by_idx(node_id)
        return ["network", "node", node_uuid, self.verb]


class NodeOSScanAction(NodeAbstractAction):
    def __init__(self, manager: "ActionManager", num_nodes: int, **kwargs) -> None:
        super().__init__(manager=manager)
        self.verb = "scan"


class NodeShutdownAction(NodeAbstractAction):
    def __init__(self, manager: "ActionManager", num_nodes: int, **kwargs) -> None:
        super().__init__(manager=manager)
        self.verb = "shutdown"


class NodeStartupAction(NodeAbstractAction):
    def __init__(self, manager: "ActionManager", num_nodes: int, **kwargs) -> None:
        super().__init__(manager=manager)
        self.verb = "start"


class NodeResetAction(NodeAbstractAction):
    def __init__(self, manager: "ActionManager", num_nodes: int, **kwargs) -> None:
        super().__init__(manager=manager)
        self.verb = "reset"


class NetworkACLAddRuleAction(AbstractAction):
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
        super().__init__(manager=manager)
        num_permissions = 2
        self.shape: Dict[str, int] = {
            "position": max_acl_rules,
            "permission": num_permissions,
            "source_ip_idx": num_ips,
            "dest_ip_idx": num_ips,
            "source_port_idx": num_ports,
            "dest_port_idx": num_ports,
            "protocol_idx": num_protocols,
        }
        self.target_router_uuid: str = target_router_uuid

    def form_request(
        self, position, permission, source_ip_idx, dest_ip_idx, source_port_idx, dest_port_idx, protocol_idx
    ) -> List[str]:
        protocol = self.manager.get_internet_protocol_by_idx(protocol_idx)
        src_ip = self.manager.get_ip_address_by_idx(source_ip_idx)
        src_port = self.manager.get_port_by_idx(source_port_idx)
        dst_ip = self.manager.get_ip_address_by_idx(dest_ip_idx)
        dst_port = self.manager.get_port_by_idx(dest_port_idx)
        return [
            "network",
            "node",
            self.target_router_uuid,
            "acl",
            "add_rule",
            permission,
            protocol,
            src_ip,
            src_port,
            dst_ip,
            dst_port,
            position,
        ]


class NetworkACLRemoveRuleAction(AbstractAction):
    def __init__(self, manager: "ActionManager", target_router_uuid: str, max_acl_rules: int, **kwargs) -> None:
        super().__init__(manager=manager)
        self.shape: Dict[str, int] = {"position": max_acl_rules}
        self.target_router_uuid: str = target_router_uuid

    def form_request(self, position: int) -> List[str]:
        return ["network", "node", self.target_router_uuid, "acl", "remove_rule", position]


class NetworkNICEnableAction(AbstractAction):
    def __init__(self, manager: "ActionManager", num_nodes: int, max_nics_per_node: int, **kwargs) -> None:
        super().__init__(manager=manager)
        self.shape: Dict[str, int] = {"node_id": num_nodes, "nic_id": max_nics_per_node}

    def form_request(self, node_id: int, nic_id: int) -> List[str]:
        return [
            "network",
            "node",
            self.manager.get_node_uuid_by_idx(node_idx=node_id),
            "nic",
            self.manager.get_nic_uuid_by_idx(node_idx=node_id, nic_idx=nic_id),
            "enable",
        ]


class NetworkNICDisableAction(AbstractAction):
    def __init__(self, manager: "ActionManager", num_nodes: int, max_nics_per_node: int, **kwargs) -> None:
        super().__init__(manager=manager)
        self.shape: Dict[str, int] = {"node_id": num_nodes, "nic_id": max_nics_per_node}

    def form_request(self, node_id: int, nic_id: int) -> List[str]:
        return [
            "network",
            "node",
            self.manager.get_node_uuid_by_idx(node_idx=node_id),
            "nic",
            self.manager.get_nic_uuid_by_idx(node_idx=node_id, nic_idx=nic_id),
            "disable",
        ]


class ActionManager:
    # let the action manager handle the conversion of action spaces into a single discrete integer space.
    #

    # when action space is created, it will take subspaces and generate an action map by enumerating all possibilities,
    # BUT, the action map can be provided in the config, in which case it will use that.

    # action map is basically just a mapping between integer and CAOS action (incl. parameter values)
    # for example the action map can be:
    # 0: DONOTHING
    # 1: NODE, FILE, SCAN, NODEID=2, FOLDERID=1, FILEID=0
    # 2: ......
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

    def __init__(
        self,
        session: PrimaiteSession,  # reference to session for looking up stuff
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
        self.session: PrimaiteSession = session
        self.sim: Simulation = self.session.simulation
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

        action_args = {
            "num_nodes": len(node_uuids),
            "num_folders": max_folders_per_node,
            "num_files": max_files_per_folder,
            "num_services": max_services_per_node,
            "num_nics": max_nics_per_node,
            "num_acl_rules": max_acl_rules,
            "num_protocols": len(self.protocols),
            "num_ports": len(self.protocols),
            "num_ips": len(self.ip_address_list),
        }
        self.actions: Dict[str, AbstractAction] = {}
        for act_type in actions:
            self.actions[act_type] = self.__act_class_identifiers[act_type](self, **action_args)

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
    ) -> Dict[int, Tuple[AbstractAction, Dict]]:
        all_action_possibilities = []
        for action in self.actions.values():
            param_names = (list(action.shape.keys()),)
            num_possibilities = list(action.shape.values())
            possibilities = [range(n) for n in num_possibilities]

            itertools.product(action.shape.values())
            all_action_possibilities.append((action, {}))

    def get_action(self, action: int) -> Tuple[str, Dict]:
        """Produce action in CAOS format"""
        """the agent chooses an action (as an integer), this is converted into an action in CAOS format"""
        """The caos format is basically a action identifier, followed by parameters stored in a dictionary"""
        act_identifier, act_options = self.action_map[action]
        return act_identifier, act_options

    def form_request(self, action_identifier: str, action_options: Dict):
        """Take action in CAOS format and use the execution definition to change it into PrimAITE request format"""
        act_obj = self.actions[action_identifier]
        return act_obj.form_request(**action_options)

    @property
    def space(self) -> spaces.Space:
        return spaces.Discrete(len(self.action_map))

    def get_node_uuid_by_idx(self, node_idx):
        return self.node_uuids[node_idx]

    def get_folder_uuid_by_idx(self, node_idx, folder_idx) -> Optional[str]:
        node_uuid = self.get_node_uuid_by_idx(node_idx)
        node = self.sim.network.nodes[node_uuid]
        folder_uuids = list(node.file_system.folders.keys())
        return folder_uuids[folder_idx] if len(folder_uuids) > folder_idx else None

    def get_file_uuid_by_idx(self, node_idx, folder_idx, file_idx) -> Optional[str]:
        node_uuid = self.get_node_uuid_by_idx(node_idx)
        node = self.sim.network.nodes[node_uuid]
        folder_uuids = list(node.file_system.folders.keys())
        if len(folder_uuids) <= folder_idx:
            return None
        folder = node.file_system.folders[folder_uuids[folder_idx]]
        file_uuids = list(folder.files.keys())
        return file_uuids[file_idx] if len(file_uuids) > file_idx else None

    def get_service_uuid_by_idx(self, node_idx, service_idx) -> Optional[str]:
        node_uuid = self.get_node_uuid_by_idx(node_idx)
        node = self.sim.network.nodes[node_uuid]
        service_uuids = list(node.services.keys())
        return service_uuids[service_idx] if len(service_uuids) > service_idx else None

    def get_internet_protocol_by_idx(self, protocol_idx: int) -> str:
        return self.protocols[protocol_idx]

    def get_ip_address_by_idx(self, ip_idx: int) -> str:
        return self.ip_address_list[ip_idx]

    def get_port_by_idx(self, port_idx: int) -> str:
        return self.ports[port_idx]

    def get_nic_uuid_by_idx(self, node_idx: int, nic_idx: int) -> str:
        node_uuid = self.get_node_uuid_by_idx(node_idx)
        node_obj = self.sim.network.nodes[node_uuid]
        nics = list(node_obj.nics.keys())
        if len(nics) <= nic_idx:
            return None
        return nics[nic_idx]

    @classmethod
    def from_config(cls, session: PrimaiteSession, cfg: Dict) -> "ActionManager":
        obj = cls(
            session=session,
            actions=cfg["action_list"],
            node_uuids=cfg["options"]["nodes"],
            max_folders_per_node=cfg["options"]["max_folders_per_node"],
            max_files_per_folder=cfg["options"]["max_files_per_folder"],
            max_services_per_node=cfg["options"]["max_services_per_node"],
            max_nics_per_node=cfg["options"]["max_nics_per_node"],
            max_acl_rules=cfg["options"]["max_acl_rules"],
            max_X=cfg["options"]["max_X"],
            protocols=session.options.ports,
            ports=session.options.protocols,
            ip_address_list=None,
            act_map=cfg["action_map"],
        )

        return obj
