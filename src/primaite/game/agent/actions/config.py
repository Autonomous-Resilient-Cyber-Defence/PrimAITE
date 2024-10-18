# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

from typing import Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, ValidationInfo

from primaite.game.agent.actions.manager import AbstractAction
from primaite.interface.request import RequestFormat


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


class ConfigureC2BeaconAction(AbstractAction):
    """Action which configures a C2 Beacon based on the parameters given."""

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Configuration schema for ConfigureC2BeaconAction."""

        node_name: str
        c2_server_ip_address: str
        keep_alive_frequency: int = Field(default=5, ge=1)
        masquerade_protocol: str = Field(default="TCP")
        masquerade_port: str = Field(default="HTTP")

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

    @classmethod
    def form_request(self, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request that can be ingested by the simulation."""
        if config.node_name is None:
            return ["do_nothing"]
        config = ConfigureC2BeaconAction._Opts(
            c2_server_ip_address=config["c2_server_ip_address"],
            keep_alive_frequency=config["keep_alive_frequency"],
            masquerade_port=config["masquerade_port"],
            masquerade_protocol=config["masquerade_protocol"],
        )

        ConfigureC2BeaconAction._Opts.model_validate(config)  # check that options adhere to schema

        return ["network", "node", config.node_name, "application", "C2Beacon", "configure", config.__dict__]


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

    class ConfigSchema(AbstractAction):
        """Configuration schema for RansomwareLaunchC2ServerAction."""
        node_name: str

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request that can be ingested by the simulation."""
        if config.node_name is None:
            return ["do_nothing"]
        # This action currently doesn't require any further configuration options.
        return ["network", "node", config.node_name, "application", "C2Server", "ransomware_launch"]
    
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