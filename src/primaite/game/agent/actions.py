from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
import itertools


from primaite.simulator.sim_container import Simulation

from gym import spaces

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
    def __init__(self, manager:"ActionManager", **kwargs) -> None:
        """
        Init method for action.

        All action init functions should accept **kwargs as a way of ignoring extra arguments.

        Since many parameters are defined for the action space as a whole (such as max files per folder, max services
        per node), we need to pass those options to every action that gets created. To pervent verbosity, these
        parameters are just broadcasted to all actions and the actions can pay attention to the ones that apply.
        """
        self.name:str = ""
        """Human-readable action identifier used for printing, logging, and reporting."""
        self.shape = (0,)
        """Tuple describing number of options for each parameter of this action. Can be passed to
        gym.spaces.MultiDiscrete to form a valid space."""
        self.manager:ActionManager = manager


    @abstractmethod
    def form_request(self) -> List[str]:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return []


class DoNothingAction(AbstractAction):
    def __init__(self, manager:"ActionManager", **kwargs) -> None:
        super().__init__(manager=manager)
        self.name = "DONOTHING"
        self.shape = (1,)

    def form_request(self) -> List[str]:
        return ["do_nothing"]

class NodeServiceAbstractAction(AbstractAction):
    """
    Base class for service actions.

    Any action which applies to a service and uses node_id and service_id as its only two parameters can inherit from
    this base class.
    """
    @abstractmethod
    def __init__(self, manager:"ActionManager", num_nodes, num_services, **kwargs) -> None:
        super().__init__(manager=manager)
        self.shape: Tuple[int] = (num_nodes, num_services)
        self.verb:str

    def form_request(self, node_id:int, service_id:int) -> List[str]:
        node_uuid = self.manager.get_node_uuid_by_idx(node_id)
        service_uuid = self.manager.get_service_uuid_by_idx(node_id, service_id)
        if node_uuid is None or service_uuid is None:
            return ["do_nothing"]
        return ['network', 'node', node_uuid, 'services', service_uuid, self.verb]

class NodeServiceScanAction(NodeServiceAbstractAction):
    def __init__(self, manager:"ActionManager", num_nodes, num_services, **kwargs) -> None:
        super().__init__(manager=manager)
        self.verb = "scan"

class NodeServiceStopAction(NodeServiceAbstractAction):
    def __init__(self, manager:"ActionManager", num_nodes, num_services, **kwargs) -> None:
        super().__init__(manager=manager)
        self.verb = "stop"

class NodeServiceStartAction(NodeServiceAbstractAction):
    def __init__(self, manager:"ActionManager", num_nodes, num_services, **kwargs) -> None:
        super().__init__(manager=manager)
        self.verb = "start"

class NodeServicePauseAction(NodeServiceAbstractAction):
    def __init__(self, manager:"ActionManager", num_nodes, num_services, **kwargs) -> None:
        super().__init__(manager=manager)
        self.verb = "pause"

class NodeServiceResumeAction(NodeServiceAbstractAction):
    def __init__(self, manager:"ActionManager", num_nodes, num_services, **kwargs) -> None:
        super().__init__(manager=manager)
        self.verb = "resume"

class NodeServiceRestartAction(NodeServiceAbstractAction):
    def __init__(self, manager:"ActionManager", num_nodes, num_services, **kwargs) -> None:
        super().__init__(manager=manager)
        self.verb = "restart"

class NodeServiceDisableAction(NodeServiceAbstractAction):
    def __init__(self, manager:"ActionManager", num_nodes, num_services, **kwargs) -> None:
        super().__init__(manager=manager)
        self.verb = "disable"

class NodeServiceEnableAction(NodeServiceAbstractAction):
    def __init__(self, manager:"ActionManager", num_nodes, num_services, **kwargs) -> None:
        super().__init__(manager=manager)
        self.verb = "enable"



class NodeFolderAbstractAction(AbstractAction):
    @abstractmethod
    def __init__(self, manager:"ActionManager", num_nodes, num_folders, **kwargs) -> None:
        super().__init__(manager=manager)
        self.shape = (num_nodes, num_folders)
        self.verb: str

    def form_request(self, node_id:int, folder_id:int) -> List[str]:
        node_uuid = self.manager.get_node_uuid_by_idx(node_id)
        folder_uuid = self.manager.get_folder_uuid_by_idx(node_idx=node_id, folder_idx=folder_id)
        if node_uuid is None or folder_uuid is None:
            return ["do_nothing"]
        return ['network', 'node', node_uuid, 'file_system', 'folder', folder_uuid, self.verb]

class NodeFolderScanAction(NodeFolderAbstractAction):
    def __init__(self, manager:"ActionManager", num_nodes, num_folders, **kwargs) -> None:
        super().__init__(manager, num_nodes, num_folders, **kwargs)
        self.verb:str = "scan"

class NodeFolderCheckhashAction(NodeFolderAbstractAction):
    def __init__(self, manager:"ActionManager", num_nodes, num_folders, **kwargs) -> None:
        super().__init__(manager, num_nodes, num_folders, **kwargs)
        self.verb:str = "checkhash"

class NodeFolderRepairAction(NodeFolderAbstractAction):
    def __init__(self, manager:"ActionManager", num_nodes, num_folders, **kwargs) -> None:
        super().__init__(manager, num_nodes, num_folders, **kwargs)
        self.verb:str = "repair"

class NodeFolderRestoreAction(NodeFolderAbstractAction):
    def __init__(self, manager: "ActionManager", num_nodes, num_folders, **kwargs) -> None:
        super().__init__(manager, num_nodes, num_folders, **kwargs)
        self.verb:str = "restore"


class NodeFileAbstractAction(AbstractAction):
    @abstractmethod
    def __init__(self, manager:"ActionManager", num_nodes:int, num_folders:int, num_files:int, **kwargs) -> None:
        super().__init__(manager=manager)
        self.shape:Tuple[int] = (num_nodes, num_folders, num_files)
        self.verb:str

    def form_request(self, node_id:int, folder_id:int, file_id:int) -> List[str]:
        node_uuid = self.manager.get_node_uuid_by_idx(node_id)
        folder_uuid = self.manager.get_folder_uuid_by_idx(node_idx=node_id, folder_idx=folder_id)
        file_uuid = self.manager.get_file_uuid_by_idx(node_idx=node_id, folder_idx=folder_id, file_idx=file_id)
        if node_uuid is None or folder_uuid is None or file_uuid is None:
            return ["do_nothing"]
        return ['network', 'node', node_uuid, 'file_system', 'folder', folder_uuid, 'files', file_uuid, self.verb]

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
        self.shape: Tuple[int] = (num_nodes,)
        self.verb: str

    def form_request(self, node_id:int) -> List[str]:
        node_uuid = self.manager.get_node_uuid_by_idx(node_id)
        return ["network", "node", node_uuid, self.verb]

class NodeOSScanAction(NodeAbstractAction):
    def __init__(self, manager: "ActionManager", num_nodes: int, **kwargs) -> None:
        super().__init__(manager=manager)
        self.verb = 'scan'

class NodeShutdownAction(NodeAbstractAction):
    def __init__(self, manager: "ActionManager", num_nodes: int, **kwargs) -> None:
        super().__init__(manager=manager)
        self.verb = 'shutdown'

class NodeStartupAction(NodeAbstractAction):
    def __init__(self, manager: "ActionManager", num_nodes: int, **kwargs) -> None:
        super().__init__(manager=manager)
        self.verb = 'start'

class NodeResetAction(NodeAbstractAction):
    def __init__(self, manager: "ActionManager", num_nodes: int, **kwargs) -> None:
        super().__init__(manager=manager)
        self.verb = 'reset'

class NetworkACLAddRuleAction(AbstractAction):
    def __init__(self, manager: "ActionManager", **kwargs) -> None:
        super().__init__(manager=manager)
        num_permissions = 2
        self.shape: Tuple[int] = (max_acl_rules, num_permissions, num_nics, num_nics, num_ports, num_ports, num_protocols)






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
    __act_class_identifiers:Dict[str,type] = {
        "DONOTHING": DoNothingAction,
        "NODE_SERVICE_SCAN": NodeServiceScanAction,
        "NODE_SERVICE_STOP": NodeServiceStopAction,
        # "NODE_SERVICE_START": NodeServiceStartAction,
        # "NODE_SERVICE_PAUSE": NodeServicePauseAction,
        # "NODE_SERVICE_RESUME": NodeServiceResumeAction,
        # "NODE_SERVICE_RESTART": NodeServiceRestartAction,
        # "NODE_SERVICE_DISABLE": NodeServiceDisableAction,
        # "NODE_SERVICE_ENABLE": NodeServiceEnableAction,
        # "NODE_FILE_SCAN": NodeFileScanAction,
        # "NODE_FILE_CHECKHASH": NodeFileCheckhashAction,
        # "NODE_FILE_DELETE": NodeFileDeleteAction,
        # "NODE_FILE_REPAIR": NodeFileRepairAction,
        # "NODE_FILE_RESTORE": NodeFileRestoreAction,
        "NODE_FOLDER_SCAN": NodeFolderScanAction,
        # "NODE_FOLDER_CHECKHASH": NodeFolderCheckhashAction,
        # "NODE_FOLDER_REPAIR": NodeFolderRepairAction,
        # "NODE_FOLDER_RESTORE": NodeFolderRestoreAction,
        # "NODE_OS_SCAN": NodeOSScanAction,
        # "NODE_SHUTDOWN": NodeShutdownAction,
        # "NODE_STARTUP": NodeStartupAction,
        # "NODE_RESET": NodeResetAction,
        # "NETWORK_ACL_ADDRULE": NetworkACLAddRuleAction,
        # "NETWORK_ACL_REMOVERULE": NetworkACLRemoveRuleAction,
        # "NETWORK_NIC_ENABLE": NetworkNICEnable,
        # "NETWORK_NIC_DISABLE": NetworkNICDisable,
    }


    def __init__(self,
                 sim:Simulation,
                 actions:List[str],
                 node_uuids:List[str],
                 max_folders_per_node:int = 2,
                 max_files_per_folder:int = 2,
                 max_services_per_node:int = 2,
                 max_nics_per_node:int=8,
                 max_acl_rules:int=10,
                 act_map:Optional[Dict[int, Dict]]=None) -> None:
        self.sim: Simulation = sim
        self.node_uuids:List[str] = node_uuids

        action_args = {
            "num_nodes": len(node_uuids),
            "num_folders":max_folders_per_node,
            "num_files": max_files_per_folder,
            "num_services": max_services_per_node,
            "num_nics": max_nics_per_node,
            "num_acl_rules": max_acl_rules}
        self.actions: Dict[str, AbstractAction] = {}
        for act_type in actions:
            self.actions[act_type] = self.__act_class_identifiers[act_type](self, **action_args)

        self.action_map:Dict[int, Tuple[str, Dict]] = {}
        """
        Action mapping that converts an integer to a specific action and parameter choice.

        For example :
        {0: ("NODE_SERVICE_SCAN", {node_id:0, service_id:2})}
        """
        if act_map is None:
            self.action_map = self._enumerate_actions()
        else:
            self.action_map = {i:(a['action'], a['options']) for i,a in act_map.items()}
        # make sure all numbers between 0 and N are represented as dict keys in action map
        assert all([i in self.action_map.keys() for i in range(len(self.action_map))])

    def _enumerate_actions(self,) -> Dict[int, Tuple[AbstractAction, Dict]]:
        ...

    def get_action(self, action: int) -> Tuple[str,Dict]:
        """Produce action in CAOS format"""
        """the agent chooses an action (as an integer), this is converted into an action in CAOS format"""
        """The caos format is basically a action identifier, followed by parameters stored in a dictionary"""
        act_identifier, act_options = self.action_map[action]
        return act_identifier, act_options

    def form_request(self, action_identifier:str, action_options:Dict):
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
        return folder_uuids[folder_idx] if len(folder_uuids)>folder_idx else None

    def get_file_uuid_by_idx(self, node_idx, folder_idx, file_idx) -> Optional[str]:
        node_uuid = self.get_node_uuid_by_idx(node_idx)
        node = self.sim.network.nodes[node_uuid]
        folder_uuids = list(node.file_system.folders.keys())
        if len(folder_uuids)<=folder_idx:
            return None
        folder = node.file_system.folders[folder_uuids[folder_idx]]
        file_uuids = list(folder.files.keys())
        return file_uuids[file_idx] if len(file_uuids)>file_idx else None

    def get_service_uuid_by_idx(self, node_idx, service_idx) -> Optional[str]:
        node_uuid = self.get_node_uuid_by_idx(node_idx)
        node = self.sim.network.nodes[node_uuid]
        service_uuids = list(node.services.keys())
        return service_uuids[service_idx] if len(service_uuids)>service_idx else None






class UC2RedActions(AbstractAction):
    ...

class UC2GreenActionSpace(ActionManager):
    ...
