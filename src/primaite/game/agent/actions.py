# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
"""
This module contains the ActionManager class which belongs to the Agent class.

An agent's action space is made up of a collection of actions. Each action is an instance of a subclass of
AbstractAction. The ActionManager is responsible for:
    1. Creating the action space from a list of action types.
    2. Converting an integer action choice into a specific action and parameter choice.
    3. Converting an action and parameter choice into a request which can be ingested by the PrimAITE simulation. This
        ensures that requests conform to the simulator's request format.
"""
from abc import abstractmethod
from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, ValidationInfo

from primaite import getLogger
from primaite.game.agent.actions.manager import AbstractAction, ActionManager
from primaite.game.agent.actions.service import NodeServiceAbstractAction
from primaite.interface.request import RequestFormat

_LOGGER = getLogger(__name__)


class NodeServiceScanAction(NodeServiceAbstractAction):
    """Action which scans a service."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_services: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes, num_services=num_services)
        self.verb: str = "scan"


class NodeServiceStopAction(NodeServiceAbstractAction):
    """Action which stops a service."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_services: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes, num_services=num_services)
        self.verb: str = "stop"


class NodeServiceStartAction(NodeServiceAbstractAction):
    """Action which starts a service."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_services: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes, num_services=num_services)
        self.verb: str = "start"


class NodeServicePauseAction(NodeServiceAbstractAction):
    """Action which pauses a service."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_services: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes, num_services=num_services)
        self.verb: str = "pause"


class NodeServiceResumeAction(NodeServiceAbstractAction):
    """Action which resumes a service."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_services: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes, num_services=num_services)
        self.verb: str = "resume"


class NodeServiceRestartAction(NodeServiceAbstractAction):
    """Action which restarts a service."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_services: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes, num_services=num_services)
        self.verb: str = "restart"


class NodeServiceDisableAction(NodeServiceAbstractAction):
    """Action which disables a service."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_services: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes, num_services=num_services)
        self.verb: str = "disable"


class NodeServiceEnableAction(NodeServiceAbstractAction):
    """Action which enables a service."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_services: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes, num_services=num_services)
        self.verb: str = "enable"


class NodeServiceFixAction(NodeServiceAbstractAction):
    """Action which fixes a service."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_services: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes, num_services=num_services)
        self.verb: str = "fix"


class NodeApplicationAbstractAction(AbstractAction):
    """
    Base class for application actions.

    Any action which applies to an application and uses node_id and application_id as its only two parameters can
    inherit from this base class.
    """

    @abstractmethod
    def __init__(self, manager: "ActionManager", num_nodes: int, num_applications: int, **kwargs) -> None:
        super().__init__(manager=manager)
        self.shape: Dict[str, int] = {"node_id": num_nodes, "application_id": num_applications}
        self.verb: str  # define but don't initialise: defends against children classes not defining this

    def form_request(self, node_id: int, application_id: int) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        node_name = self.manager.get_node_name_by_idx(node_id)
        application_name = self.manager.get_application_name_by_idx(node_id, application_id)
        if node_name is None or application_name is None:
            return ["do_nothing"]
        return ["network", "node", node_name, "application", application_name, self.verb]


class NodeApplicationExecuteAction(NodeApplicationAbstractAction):
    """Action which executes an application."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_applications: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes, num_applications=num_applications)
        self.verb: str = "execute"


class NodeApplicationScanAction(NodeApplicationAbstractAction):
    """Action which scans an application."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_applications: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes, num_applications=num_applications)
        self.verb: str = "scan"


class NodeApplicationCloseAction(NodeApplicationAbstractAction):
    """Action which closes an application."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_applications: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes, num_applications=num_applications)
        self.verb: str = "close"


class NodeApplicationFixAction(NodeApplicationAbstractAction):
    """Action which fixes an application."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_applications: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes, num_applications=num_applications)
        self.verb: str = "fix"


class NodeApplicationInstallAction(AbstractAction):
    """Action which installs an application."""

    def __init__(self, manager: "ActionManager", num_nodes: int, **kwargs) -> None:
        super().__init__(manager=manager)
        self.shape: Dict[str, int] = {"node_id": num_nodes}

    def form_request(self, node_id: int, application_name: str) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        node_name = self.manager.get_node_name_by_idx(node_id)
        if node_name is None:
            return ["do_nothing"]
        return [
            "network",
            "node",
            node_name,
            "software_manager",
            "application",
            "install",
            application_name,
        ]


class ConfigureDatabaseClientAction(AbstractAction):
    """Action which sets config parameters for a database client on a node."""

    class _Opts(BaseModel):
        """Schema for options that can be passed to this action."""

        model_config = ConfigDict(extra="forbid")
        server_ip_address: Optional[str] = None
        server_password: Optional[str] = None

    def __init__(self, manager: "ActionManager", **kwargs) -> None:
        super().__init__(manager=manager)

    def form_request(self, node_id: int, config: Dict) -> RequestFormat:
        """Return the action formatted as a request that can be ingested by the simulation."""
        node_name = self.manager.get_node_name_by_idx(node_id)
        if node_name is None:
            return ["do_nothing"]
        ConfigureDatabaseClientAction._Opts.model_validate(config)  # check that options adhere to schema
        return ["network", "node", node_name, "application", "DatabaseClient", "configure", config]


class ConfigureRansomwareScriptAction(AbstractAction):
    """Action which sets config parameters for a ransomware script on a node."""

    class _Opts(BaseModel):
        """Schema for options that can be passed to this option."""

        model_config = ConfigDict(extra="forbid")
        server_ip_address: Optional[str] = None
        server_password: Optional[str] = None
        payload: Optional[str] = None

    def __init__(self, manager: "ActionManager", **kwargs) -> None:
        super().__init__(manager=manager)

    def form_request(self, node_id: int, config: Dict) -> RequestFormat:
        """Return the action formatted as a request that can be ingested by the simulation."""
        node_name = self.manager.get_node_name_by_idx(node_id)
        if node_name is None:
            return ["do_nothing"]
        ConfigureRansomwareScriptAction._Opts.model_validate(config)  # check that options adhere to schema
        return ["network", "node", node_name, "application", "RansomwareScript", "configure", config]


class ConfigureDoSBotAction(AbstractAction):
    """Action which sets config parameters for a DoS bot on a node."""

    class _Opts(BaseModel):
        """Schema for options that can be passed to this action."""

        model_config = ConfigDict(extra="forbid")
        target_ip_address: Optional[str] = None
        target_port: Optional[str] = None
        payload: Optional[str] = None
        repeat: Optional[bool] = None
        port_scan_p_of_success: Optional[float] = None
        dos_intensity: Optional[float] = None
        max_sessions: Optional[int] = None

    def __init__(self, manager: "ActionManager", **kwargs) -> None:
        super().__init__(manager=manager)

    def form_request(self, node_id: int, config: Dict) -> RequestFormat:
        """Return the action formatted as a request that can be ingested by the simulation."""
        node_name = self.manager.get_node_name_by_idx(node_id)
        if node_name is None:
            return ["do_nothing"]
        self._Opts.model_validate(config)  # check that options adhere to schema
        return ["network", "node", node_name, "application", "DoSBot", "configure", config]


class NodeApplicationRemoveAction(AbstractAction):
    """Action which removes/uninstalls an application."""

    def __init__(self, manager: "ActionManager", num_nodes: int, **kwargs) -> None:
        super().__init__(manager=manager)
        self.shape: Dict[str, int] = {"node_id": num_nodes}

    def form_request(self, node_id: int, application_name: str) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        node_name = self.manager.get_node_name_by_idx(node_id)
        if node_name is None:
            return ["do_nothing"]
        return ["network", "node", node_name, "software_manager", "application", "uninstall", application_name]


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
        self.verb: str  # define but don't initialise: defends against children classes not defining this

    def form_request(self, node_id: int, folder_id: int) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        node_name = self.manager.get_node_name_by_idx(node_id)
        folder_name = self.manager.get_folder_name_by_idx(node_idx=node_id, folder_idx=folder_id)
        if node_name is None or folder_name is None:
            return ["do_nothing"]
        return ["network", "node", node_name, "file_system", "folder", folder_name, self.verb]


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


class NodeFileCreateAction(AbstractAction):
    """Action which creates a new file in a given folder."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_folders: int, **kwargs) -> None:
        super().__init__(manager, num_nodes=num_nodes, num_folders=num_folders, **kwargs)
        self.verb: str = "create"

    def form_request(
        self, node_id: int, folder_name: str, file_name: str, force: Optional[bool] = False
    ) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        node_name = self.manager.get_node_name_by_idx(node_id)
        if node_name is None or folder_name is None or file_name is None:
            return ["do_nothing"]
        return ["network", "node", node_name, "file_system", "create", "file", folder_name, file_name, force]


class NodeFolderCreateAction(AbstractAction):
    """Action which creates a new folder."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_folders: int, **kwargs) -> None:
        super().__init__(manager, num_nodes=num_nodes, num_folders=num_folders, **kwargs)
        self.verb: str = "create"

    def form_request(self, node_id: int, folder_name: str) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        node_name = self.manager.get_node_name_by_idx(node_id)
        if node_name is None or folder_name is None:
            return ["do_nothing"]
        return ["network", "node", node_name, "file_system", "create", "folder", folder_name]


class NodeFileAbstractAction(AbstractAction):
    """Abstract base class for file actions.

    Any action which applies to a file and uses node_id, folder_id, and file_id as its only three parameters can inherit
    from this base class.
    """

    @abstractmethod
    def __init__(self, manager: "ActionManager", num_nodes: int, num_folders: int, num_files: int, **kwargs) -> None:
        super().__init__(manager=manager)
        self.shape: Dict[str, int] = {"node_id": num_nodes, "folder_id": num_folders, "file_id": num_files}
        self.verb: str  # define but don't initialise: defends against children classes not defining this

    def form_request(self, node_id: int, folder_id: int, file_id: int) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        node_name = self.manager.get_node_name_by_idx(node_id)
        folder_name = self.manager.get_folder_name_by_idx(node_idx=node_id, folder_idx=folder_id)
        file_name = self.manager.get_file_name_by_idx(node_idx=node_id, folder_idx=folder_id, file_idx=file_id)
        if node_name is None or folder_name is None or file_name is None:
            return ["do_nothing"]
        return ["network", "node", node_name, "file_system", "folder", folder_name, "file", file_name, self.verb]


class NodeFileScanAction(NodeFileAbstractAction):
    """Action which scans a file."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_folders: int, num_files: int, **kwargs) -> None:
        super().__init__(manager, num_nodes=num_nodes, num_folders=num_folders, num_files=num_files, **kwargs)
        self.verb: str = "scan"


class NodeFileCheckhashAction(NodeFileAbstractAction):
    """Action which checks the hash of a file."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_folders: int, num_files: int, **kwargs) -> None:
        super().__init__(manager, num_nodes=num_nodes, num_folders=num_folders, num_files=num_files, **kwargs)
        self.verb: str = "checkhash"


class NodeFileDeleteAction(NodeFileAbstractAction):
    """Action which deletes a file."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_folders: int, num_files: int, **kwargs) -> None:
        super().__init__(manager, num_nodes=num_nodes, num_folders=num_folders, num_files=num_files, **kwargs)
        self.verb: str = "delete"

    def form_request(self, node_id: int, folder_id: int, file_id: int) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        node_name = self.manager.get_node_name_by_idx(node_id)
        folder_name = self.manager.get_folder_name_by_idx(node_idx=node_id, folder_idx=folder_id)
        file_name = self.manager.get_file_name_by_idx(node_idx=node_id, folder_idx=folder_id, file_idx=file_id)
        if node_name is None or folder_name is None or file_name is None:
            return ["do_nothing"]
        return ["network", "node", node_name, "file_system", "delete", "file", folder_name, file_name]


class NodeFileRepairAction(NodeFileAbstractAction):
    """Action which repairs a file."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_folders: int, num_files: int, **kwargs) -> None:
        super().__init__(manager, num_nodes=num_nodes, num_folders=num_folders, num_files=num_files, **kwargs)
        self.verb: str = "repair"


class NodeFileRestoreAction(NodeFileAbstractAction):
    """Action which restores a file."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_folders: int, num_files: int, **kwargs) -> None:
        super().__init__(manager, num_nodes=num_nodes, num_folders=num_folders, num_files=num_files, **kwargs)
        self.verb: str = "restore"


class NodeFileCorruptAction(NodeFileAbstractAction):
    """Action which corrupts a file."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_folders: int, num_files: int, **kwargs) -> None:
        super().__init__(manager, num_nodes=num_nodes, num_folders=num_folders, num_files=num_files, **kwargs)
        self.verb: str = "corrupt"


class NodeFileAccessAction(AbstractAction):
    """Action which increases a file's access count."""

    def __init__(self, manager: "ActionManager", num_nodes: int, num_folders: int, **kwargs) -> None:
        super().__init__(manager, num_nodes=num_nodes, num_folders=num_folders, **kwargs)
        self.verb: str = "access"

    def form_request(self, node_id: int, folder_name: str, file_name: str) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        node_name = self.manager.get_node_name_by_idx(node_id)
        if node_name is None or folder_name is None or file_name is None:
            return ["do_nothing"]
        return ["network", "node", node_name, "file_system", "access", folder_name, file_name]


class NodeAbstractAction(AbstractAction):
    """
    Abstract base class for node actions.

    Any action which applies to a node and uses node_id as its only parameter can inherit from this base class.
    """

    @abstractmethod
    def __init__(self, manager: "ActionManager", num_nodes: int, **kwargs) -> None:
        super().__init__(manager=manager)
        self.shape: Dict[str, int] = {"node_id": num_nodes}
        self.verb: str  # define but don't initialise: defends against children classes not defining this

    def form_request(self, node_id: int) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        node_name = self.manager.get_node_name_by_idx(node_id)
        return ["network", "node", node_name, self.verb]


class NodeOSScanAction(NodeAbstractAction):
    """Action which scans a node's OS."""

    def __init__(self, manager: "ActionManager", num_nodes: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes)
        self.verb: str = "scan"


class NodeShutdownAction(NodeAbstractAction):
    """Action which shuts down a node."""

    def __init__(self, manager: "ActionManager", num_nodes: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes)
        self.verb: str = "shutdown"


class NodeStartupAction(NodeAbstractAction):
    """Action which starts up a node."""

    def __init__(self, manager: "ActionManager", num_nodes: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes)
        self.verb: str = "startup"


class NodeResetAction(NodeAbstractAction):
    """Action which resets a node."""

    def __init__(self, manager: "ActionManager", num_nodes: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes)
        self.verb: str = "reset"


class RouterACLAddRuleAction(AbstractAction):
    """Action which adds a rule to a router's ACL."""

    class ACLRuleOptions(BaseModel):
        """Validator for ACL_ADD_RULE options."""

        target_router: str
        """On which router to add the rule, must be specified."""
        position: int
        """At what position to add the rule, must be specified."""
        permission: Literal[1, 2]
        """Whether to allow or deny traffic, must be specified. 1 = PERMIT, 2 = DENY."""
        source_ip_id: int = Field(default=1, ge=1)
        """Rule source IP address. By default, all ip addresses."""
        source_wildcard_id: int = Field(default=0, ge=0)
        """Rule source IP wildcard. By default, use the wildcard at index 0 from action manager."""
        source_port_id: int = Field(default=1, ge=1)
        """Rule source port. By default, all source ports."""
        dest_ip_id: int = Field(default=1, ge=1)
        """Rule destination IP address. By default, all ip addresses."""
        dest_wildcard_id: int = Field(default=0, ge=0)
        """Rule destination IP wildcard. By default, use the wildcard at index 0 from action manager."""
        dest_port_id: int = Field(default=1, ge=1)
        """Rule destination port. By default, all destination ports."""
        protocol_id: int = Field(default=1, ge=1)
        """Rule protocol. By default, all protocols."""

        @field_validator(
            "source_ip_id",
            "source_port_id",
            "source_wildcard_id",
            "dest_ip_id",
            "dest_port_id",
            "dest_wildcard_id",
            "protocol_id",
            mode="before",
        )
        @classmethod
        def not_none(cls, v: str, info: ValidationInfo) -> int:
            """If None is passed, use the default value instead."""
            if v is None:
                return cls.model_fields[info.field_name].default
            return v

    def __init__(
        self,
        manager: "ActionManager",
        max_acl_rules: int,
        num_ips: int,
        num_ports: int,
        num_protocols: int,
        **kwargs,
    ) -> None:
        """Init method for RouterACLAddRuleAction.

        :param manager: Reference to the ActionManager which created this action.
        :type manager: ActionManager
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

    def form_request(
        self,
        target_router: str,
        position: int,
        permission: int,
        source_ip_id: int,
        source_wildcard_id: int,
        dest_ip_id: int,
        dest_wildcard_id: int,
        source_port_id: int,
        dest_port_id: int,
        protocol_id: int,
    ) -> List[str]:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        # Validate incoming data.
        parsed_options = RouterACLAddRuleAction.ACLRuleOptions(
            target_router=target_router,
            position=position,
            permission=permission,
            source_ip_id=source_ip_id,
            source_wildcard_id=source_wildcard_id,
            dest_ip_id=dest_ip_id,
            dest_wildcard_id=dest_wildcard_id,
            source_port_id=source_port_id,
            dest_port_id=dest_port_id,
            protocol_id=protocol_id,
        )
        if parsed_options.permission == 1:
            permission_str = "PERMIT"
        elif parsed_options.permission == 2:
            permission_str = "DENY"
        else:
            _LOGGER.warning(f"{self.__class__} received permission {permission}, expected 0 or 1.")

        if parsed_options.protocol_id == 1:
            protocol = "ALL"
        else:
            protocol = self.manager.get_internet_protocol_by_idx(parsed_options.protocol_id - 2)
            # subtract 2 to account for UNUSED=0 and ALL=1.

        if parsed_options.source_ip_id == 1:
            src_ip = "ALL"
        else:
            src_ip = self.manager.get_ip_address_by_idx(parsed_options.source_ip_id - 2)
            # subtract 2 to account for UNUSED=0, and ALL=1

        src_wildcard = self.manager.get_wildcard_by_idx(parsed_options.source_wildcard_id)

        if parsed_options.source_port_id == 1:
            src_port = "ALL"
        else:
            src_port = self.manager.get_port_by_idx(parsed_options.source_port_id - 2)
            # subtract 2 to account for UNUSED=0, and ALL=1

        if parsed_options.dest_ip_id == 1:
            dst_ip = "ALL"
        else:
            dst_ip = self.manager.get_ip_address_by_idx(parsed_options.dest_ip_id - 2)
            # subtract 2 to account for UNUSED=0, and ALL=1
        dst_wildcard = self.manager.get_wildcard_by_idx(parsed_options.dest_wildcard_id)

        if parsed_options.dest_port_id == 1:
            dst_port = "ALL"
        else:
            dst_port = self.manager.get_port_by_idx(parsed_options.dest_port_id - 2)
            # subtract 2 to account for UNUSED=0, and ALL=1

        return [
            "network",
            "node",
            target_router,
            "acl",
            "add_rule",
            permission_str,
            protocol,
            str(src_ip),
            src_wildcard,
            src_port,
            str(dst_ip),
            dst_wildcard,
            dst_port,
            position,
        ]


class RouterACLRemoveRuleAction(AbstractAction):
    """Action which removes a rule from a router's ACL."""

    def __init__(self, manager: "ActionManager", max_acl_rules: int, **kwargs) -> None:
        """Init method for RouterACLRemoveRuleAction.

        :param manager: Reference to the ActionManager which created this action.
        :type manager: ActionManager
        :param max_acl_rules: Maximum number of ACL rules that can be added to the router.
        :type max_acl_rules: int
        """
        super().__init__(manager=manager)
        self.shape: Dict[str, int] = {"position": max_acl_rules}

    def form_request(self, target_router: str, position: int) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return ["network", "node", target_router, "acl", "remove_rule", position]


class FirewallACLAddRuleAction(AbstractAction):
    """Action which adds a rule to a firewall port's ACL."""

    def __init__(
        self,
        manager: "ActionManager",
        max_acl_rules: int,
        num_ips: int,
        num_ports: int,
        num_protocols: int,
        **kwargs,
    ) -> None:
        """Init method for FirewallACLAddRuleAction.

        :param manager: Reference to the ActionManager which created this action.
        :type manager: ActionManager
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

    def form_request(
        self,
        target_firewall_nodename: str,
        firewall_port_name: str,
        firewall_port_direction: str,
        position: int,
        permission: int,
        source_ip_id: int,
        source_wildcard_id: int,
        dest_ip_id: int,
        dest_wildcard_id: int,
        source_port_id: int,
        dest_port_id: int,
        protocol_id: int,
    ) -> List[str]:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        if permission == 0:
            permission_str = "UNUSED"
            return ["do_nothing"]  # NOT SUPPORTED, JUST DO NOTHING IF WE COME ACROSS THIS
        elif permission == 1:
            permission_str = "PERMIT"
        elif permission == 2:
            permission_str = "DENY"
        else:
            _LOGGER.warning(f"{self.__class__} received permission {permission}, expected 0 or 1.")

        if protocol_id == 0:
            return ["do_nothing"]  # NOT SUPPORTED, JUST DO NOTHING IF WE COME ACROSS THIS

        if protocol_id == 1:
            protocol = "ALL"
        else:
            protocol = self.manager.get_internet_protocol_by_idx(protocol_id - 2)
            # subtract 2 to account for UNUSED=0 and ALL=1.

        if source_ip_id == 0:
            return ["do_nothing"]  # invalid formulation
        elif source_ip_id == 1:
            src_ip = "ALL"
        else:
            src_ip = self.manager.get_ip_address_by_idx(source_ip_id - 2)
            # subtract 2 to account for UNUSED=0, and ALL=1

        if source_port_id == 0:
            return ["do_nothing"]  # invalid formulation
        elif source_port_id == 1:
            src_port = "ALL"
        else:
            src_port = self.manager.get_port_by_idx(source_port_id - 2)
            # subtract 2 to account for UNUSED=0, and ALL=1

        if dest_ip_id == 0:
            return ["do_nothing"]  # invalid formulation
        elif dest_ip_id == 1:
            dst_ip = "ALL"
        else:
            dst_ip = self.manager.get_ip_address_by_idx(dest_ip_id - 2)
            # subtract 2 to account for UNUSED=0, and ALL=1

        if dest_port_id == 0:
            return ["do_nothing"]  # invalid formulation
        elif dest_port_id == 1:
            dst_port = "ALL"
        else:
            dst_port = self.manager.get_port_by_idx(dest_port_id - 2)
            # subtract 2 to account for UNUSED=0, and ALL=1
        src_wildcard = self.manager.get_wildcard_by_idx(source_wildcard_id)
        dst_wildcard = self.manager.get_wildcard_by_idx(dest_wildcard_id)

        return [
            "network",
            "node",
            target_firewall_nodename,
            firewall_port_name,
            firewall_port_direction,
            "acl",
            "add_rule",
            permission_str,
            protocol,
            str(src_ip),
            src_wildcard,
            src_port,
            str(dst_ip),
            dst_wildcard,
            dst_port,
            position,
        ]


class FirewallACLRemoveRuleAction(AbstractAction):
    """Action which removes a rule from a firewall port's ACL."""

    def __init__(self, manager: "ActionManager", max_acl_rules: int, **kwargs) -> None:
        """Init method for RouterACLRemoveRuleAction.

        :param manager: Reference to the ActionManager which created this action.
        :type manager: ActionManager
        :param max_acl_rules: Maximum number of ACL rules that can be added to the router.
        :type max_acl_rules: int
        """
        super().__init__(manager=manager)
        self.shape: Dict[str, int] = {"position": max_acl_rules}

    def form_request(
        self, target_firewall_nodename: str, firewall_port_name: str, firewall_port_direction: str, position: int
    ) -> List[str]:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return [
            "network",
            "node",
            target_firewall_nodename,
            firewall_port_name,
            firewall_port_direction,
            "acl",
            "remove_rule",
            position,
        ]


class HostNICAbstractAction(AbstractAction):
    """
    Abstract base class for NIC actions.

    Any action which applies to a NIC and uses node_id and nic_id as its only two parameters can inherit from this base
    class.
    """

    def __init__(self, manager: "ActionManager", num_nodes: int, max_nics_per_node: int, **kwargs) -> None:
        """Init method for HostNICAbstractAction.

        :param manager: Reference to the ActionManager which created this action.
        :type manager: ActionManager
        :param num_nodes: Number of nodes in the simulation.
        :type num_nodes: int
        :param max_nics_per_node: Maximum number of NICs per node.
        :type max_nics_per_node: int
        """
        super().__init__(manager=manager)
        self.shape: Dict[str, int] = {"node_id": num_nodes, "nic_id": max_nics_per_node}
        self.verb: str  # define but don't initialise: defends against children classes not defining this

    def form_request(self, node_id: int, nic_id: int) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        node_name = self.manager.get_node_name_by_idx(node_idx=node_id)
        nic_num = self.manager.get_nic_num_by_idx(node_idx=node_id, nic_idx=nic_id)
        if node_name is None or nic_num is None:
            return ["do_nothing"]
        return ["network", "node", node_name, "network_interface", nic_num, self.verb]


class HostNICEnableAction(HostNICAbstractAction):
    """Action which enables a NIC."""

    def __init__(self, manager: "ActionManager", num_nodes: int, max_nics_per_node: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes, max_nics_per_node=max_nics_per_node, **kwargs)
        self.verb: str = "enable"


class HostNICDisableAction(HostNICAbstractAction):
    """Action which disables a NIC."""

    def __init__(self, manager: "ActionManager", num_nodes: int, max_nics_per_node: int, **kwargs) -> None:
        super().__init__(manager=manager, num_nodes=num_nodes, max_nics_per_node=max_nics_per_node, **kwargs)
        self.verb: str = "disable"


class NetworkPortEnableAction(AbstractAction):
    """Action which enables are port on a router or a firewall."""

    def __init__(self, manager: "ActionManager", max_nics_per_node: int, **kwargs) -> None:
        """Init method for NetworkPortEnableAction.

        :param max_nics_per_node: Maximum number of NICs per node.
        :type max_nics_per_node: int
        """
        super().__init__(manager=manager)
        self.shape: Dict[str, int] = {"port_id": max_nics_per_node}

    def form_request(self, target_nodename: str, port_id: int) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        if target_nodename is None or port_id is None:
            return ["do_nothing"]
        return ["network", "node", target_nodename, "network_interface", port_id, "enable"]


class NetworkPortDisableAction(AbstractAction):
    """Action which disables are port on a router or a firewall."""

    def __init__(self, manager: "ActionManager", max_nics_per_node: int, **kwargs) -> None:
        """Init method for NetworkPortDisableAction.

        :param max_nics_per_node: Maximum number of NICs per node.
        :type max_nics_per_node: int
        """
        super().__init__(manager=manager)
        self.shape: Dict[str, int] = {"port_id": max_nics_per_node}

    def form_request(self, target_nodename: str, port_id: int) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        if target_nodename is None or port_id is None:
            return ["do_nothing"]
        return ["network", "node", target_nodename, "network_interface", port_id, "disable"]


class NodeNMAPPingScanAction(AbstractAction):
    """Action which performs an NMAP ping scan."""

    def __init__(self, manager: "ActionManager", **kwargs) -> None:
        super().__init__(manager=manager)

    def form_request(
        self, source_node: str, target_ip_address: Union[str, List[str]], show: Optional[bool] = False
    ) -> List[str]:  # noqa
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return [
            "network",
            "node",
            source_node,
            "application",
            "NMAP",
            "ping_scan",
            {"target_ip_address": target_ip_address, "show": show},
        ]


class NodeNMAPPortScanAction(AbstractAction):
    """Action which performs an NMAP port scan."""

    def __init__(self, manager: "ActionManager", **kwargs) -> None:
        super().__init__(manager=manager)

    def form_request(
        self,
        source_node: str,
        target_ip_address: Union[str, List[str]],
        target_protocol: Optional[Union[str, List[str]]] = None,
        target_port: Optional[Union[str, List[str]]] = None,
        show: Optional[bool] = False,
    ) -> List[str]:  # noqa
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return [
            "network",
            "node",
            source_node,
            "application",
            "NMAP",
            "port_scan",
            {
                "target_ip_address": target_ip_address,
                "target_port": target_port,
                "target_protocol": target_protocol,
                "show": show,
            },
        ]


class NodeNetworkServiceReconAction(AbstractAction):
    """Action which performs an NMAP network service recon (ping scan followed by port scan)."""

    def __init__(self, manager: "ActionManager", **kwargs) -> None:
        super().__init__(manager=manager)

    def form_request(
        self,
        source_node: str,
        target_ip_address: Union[str, List[str]],
        target_protocol: Optional[Union[str, List[str]]] = None,
        target_port: Optional[Union[str, List[str]]] = None,
        show: Optional[bool] = False,
    ) -> List[str]:  # noqa
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return [
            "network",
            "node",
            source_node,
            "application",
            "NMAP",
            "network_service_recon",
            {
                "target_ip_address": target_ip_address,
                "target_port": target_port,
                "target_protocol": target_protocol,
                "show": show,
            },
        ]


class ConfigureC2BeaconAction(AbstractAction):
    """Action which configures a C2 Beacon based on the parameters given."""

    class _Opts(BaseModel):
        """Schema for options that can be passed to this action."""

        c2_server_ip_address: str
        keep_alive_frequency: int = Field(default=5, ge=1)
        masquerade_protocol: str = Field(default="TCP")
        masquerade_port: str = Field(default="HTTP")

        @field_validator(
            "c2_server_ip_address",
            "keep_alive_frequency",
            "masquerade_protocol",
            "masquerade_port",
            mode="before",
        )
        @classmethod
        def not_none(cls, v: str, info: ValidationInfo) -> int:
            """If None is passed, use the default value instead."""
            if v is None:
                return cls.model_fields[info.field_name].default
            return v

    def __init__(self, manager: "ActionManager", **kwargs) -> None:
        super().__init__(manager=manager)

    def form_request(self, node_id: int, config: Dict) -> RequestFormat:
        """Return the action formatted as a request that can be ingested by the simulation."""
        node_name = self.manager.get_node_name_by_idx(node_id)
        if node_name is None:
            return ["do_nothing"]
        config = ConfigureC2BeaconAction._Opts(
            c2_server_ip_address=config["c2_server_ip_address"],
            keep_alive_frequency=config["keep_alive_frequency"],
            masquerade_port=config["masquerade_port"],
            masquerade_protocol=config["masquerade_protocol"],
        )

        ConfigureC2BeaconAction._Opts.model_validate(config)  # check that options adhere to schema

        return ["network", "node", node_name, "application", "C2Beacon", "configure", config.__dict__]


class NodeAccountsChangePasswordAction(AbstractAction):
    """Action which changes the password for a user."""

    def __init__(self, manager: "ActionManager", **kwargs) -> None:
        super().__init__(manager=manager)

    def form_request(self, node_id: str, username: str, current_password: str, new_password: str) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        node_name = self.manager.get_node_name_by_idx(node_id)
        return [
            "network",
            "node",
            node_name,
            "service",
            "UserManager",
            "change_password",
            username,
            current_password,
            new_password,
        ]


class NodeSessionsRemoteLoginAction(AbstractAction):
    """Action which performs a remote session login."""

    def __init__(self, manager: "ActionManager", **kwargs) -> None:
        super().__init__(manager=manager)

    def form_request(self, node_id: str, username: str, password: str, remote_ip: str) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        node_name = self.manager.get_node_name_by_idx(node_id)
        return [
            "network",
            "node",
            node_name,
            "service",
            "Terminal",
            "ssh_to_remote",
            username,
            password,
            remote_ip,
        ]


class NodeSessionsRemoteLogoutAction(AbstractAction):
    """Action which performs a remote session logout."""

    def __init__(self, manager: "ActionManager", **kwargs) -> None:
        super().__init__(manager=manager)

    def form_request(self, node_id: str, remote_ip: str) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        node_name = self.manager.get_node_name_by_idx(node_id)
        return ["network", "node", node_name, "service", "Terminal", "remote_logoff", remote_ip]


class RansomwareConfigureC2ServerAction(AbstractAction):
    """Action which sends a command from the C2 Server to the C2 Beacon which configures a local RansomwareScript."""

    def __init__(self, manager: "ActionManager", **kwargs) -> None:
        super().__init__(manager=manager)

    def form_request(self, node_id: int, config: Dict) -> RequestFormat:
        """Return the action formatted as a request that can be ingested by the simulation."""
        node_name = self.manager.get_node_name_by_idx(node_id)
        if node_name is None:
            return ["do_nothing"]
        # Using the ransomware scripts model to validate.
        ConfigureRansomwareScriptAction._Opts.model_validate(config)  # check that options adhere to schema
        return ["network", "node", node_name, "application", "C2Server", "ransomware_configure", config]


class RansomwareLaunchC2ServerAction(AbstractAction):
    """Action which causes the C2 Server to send a command to the C2 Beacon to launch the RansomwareScript."""

    def __init__(self, manager: "ActionManager", **kwargs) -> None:
        super().__init__(manager=manager)

    def form_request(self, node_id: int) -> RequestFormat:
        """Return the action formatted as a request that can be ingested by the simulation."""
        node_name = self.manager.get_node_name_by_idx(node_id)
        if node_name is None:
            return ["do_nothing"]
        # This action currently doesn't require any further configuration options.
        return ["network", "node", node_name, "application", "C2Server", "ransomware_launch"]


class ExfiltrationC2ServerAction(AbstractAction):
    """Action which exfiltrates a target file from a certain node onto the C2 beacon and then the C2 Server."""

    class _Opts(BaseModel):
        """Schema for options that can be passed to this action."""

        username: Optional[str]
        password: Optional[str]
        target_ip_address: str
        target_file_name: str
        target_folder_name: str
        exfiltration_folder_name: Optional[str]

    def __init__(self, manager: "ActionManager", **kwargs) -> None:
        super().__init__(manager=manager)

    def form_request(
        self,
        node_id: int,
        account: dict,
        target_ip_address: str,
        target_file_name: str,
        target_folder_name: str,
        exfiltration_folder_name: Optional[str],
    ) -> RequestFormat:
        """Return the action formatted as a request that can be ingested by the simulation."""
        node_name = self.manager.get_node_name_by_idx(node_id)
        if node_name is None:
            return ["do_nothing"]

        command_model = {
            "target_file_name": target_file_name,
            "target_folder_name": target_folder_name,
            "exfiltration_folder_name": exfiltration_folder_name,
            "target_ip_address": target_ip_address,
            "username": account["username"],
            "password": account["password"],
        }
        ExfiltrationC2ServerAction._Opts.model_validate(command_model)
        return ["network", "node", node_name, "application", "C2Server", "exfiltrate", command_model]


class NodeSendRemoteCommandAction(AbstractAction):
    """Action which sends a terminal command to a remote node via SSH."""

    def __init__(self, manager: "ActionManager", **kwargs) -> None:
        super().__init__(manager=manager)

    def form_request(self, node_id: int, remote_ip: str, command: RequestFormat) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        node_name = self.manager.get_node_name_by_idx(node_id)
        return [
            "network",
            "node",
            node_name,
            "service",
            "Terminal",
            "send_remote_command",
            remote_ip,
            {"command": command},
        ]


class TerminalC2ServerAction(AbstractAction):
    """Action which causes the C2 Server to send a command to the C2 Beacon to execute the terminal command passed."""

    class _Opts(BaseModel):
        """Schema for options that can be passed to this action."""

        commands: Union[List[RequestFormat], RequestFormat]
        ip_address: Optional[str]
        username: Optional[str]
        password: Optional[str]

    def __init__(self, manager: "ActionManager", **kwargs) -> None:
        super().__init__(manager=manager)

    def form_request(self, node_id: int, commands: List, ip_address: Optional[str], account: dict) -> RequestFormat:
        """Return the action formatted as a request that can be ingested by the simulation."""
        node_name = self.manager.get_node_name_by_idx(node_id)
        if node_name is None:
            return ["do_nothing"]

        command_model = {
            "commands": commands,
            "ip_address": ip_address,
            "username": account["username"],
            "password": account["password"],
        }

        TerminalC2ServerAction._Opts.model_validate(command_model)
        return ["network", "node", node_name, "application", "C2Server", "terminal_command", command_model]


class RansomwareLaunchC2ServerAction(AbstractAction):
    """Action which causes the C2 Server to send a command to the C2 Beacon to launch the RansomwareScript."""

    def __init__(self, manager: "ActionManager", **kwargs) -> None:
        super().__init__(manager=manager)

    def form_request(self, node_id: int) -> RequestFormat:
        """Return the action formatted as a request that can be ingested by the simulation."""
        node_name = self.manager.get_node_name_by_idx(node_id)
        if node_name is None:
            return ["do_nothing"]
        # This action currently doesn't require any further configuration options.
        return ["network", "node", node_name, "application", "C2Server", "ransomware_launch"]
