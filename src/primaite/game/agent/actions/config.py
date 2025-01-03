# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

from typing import List, Optional, Union

from pydantic import ConfigDict, Field, field_validator, ValidationInfo

from primaite.game.agent.actions.manager import AbstractAction, ActionManager
from primaite.interface.request import RequestFormat

__all__ = (
    "ConfigureRansomwareScriptAction",
    "ConfigureDoSBotAction",
    "ConfigureC2BeaconAction",
    "NodeSendRemoteCommandAction",
    "TerminalC2ServerAction",
    "RansomwareLaunchC2ServerAction",
    "ExfiltrationC2ServerAction",
    "ConfigureDatabaseClientAction",
)


class ConfigureRansomwareScriptAction(AbstractAction, identifier="c2_server_ransomware_configure"):
    """Action which sets config parameters for a ransomware script on a node."""

    config: "ConfigureRansomwareScriptAction.ConfigSchema"

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Configuration schema for ConfigureRansomwareScriptAction."""

        node_name: str
        server_ip_address: Optional[str]
        server_password: Optional[str]
        payload: Optional[str]

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request that can be ingested by the simulation."""
        if config.node_name is None:
            return ["do_nothing"]
        return [
            "network",
            "node",
            config.node_name,
            "application",
            "RansomwareScript",
            "configure",
            config.model_config,
        ]


class ConfigureDoSBotAction(AbstractAction, identifier="configure_dos_bot"):
    """Action which sets config parameters for a DoS bot on a node."""

    config: "ConfigureDoSBotAction.ConfigSchema"

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Schema for options that can be passed to this action."""

        node_name: str
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

    def form_request(self, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request that can be ingested by the simulation."""
        if config.node_name is None:
            return ["do_nothing"]
        self.ConfigSchema.model_validate(config)  # check that options adhere to schema
        return ["network", "node", config.node_name, "application", "DoSBot", "configure", config]


class ConfigureC2BeaconAction(AbstractAction, identifier="configure_c2_beacon"):
    """Action which configures a C2 Beacon based on the parameters given."""

    config: "ConfigureC2BeaconAction.ConfigSchema"

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Configuration schema for ConfigureC2BeaconAction."""

        node_name: str
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
        return ["network", "node", config.node_name, "application", "C2Beacon", "configure", config]


class NodeSendRemoteCommandAction(AbstractAction, identifier="node_send_remote_command"):
    """Action which sends a terminal command to a remote node via SSH."""

    config: "NodeSendRemoteCommandAction.ConfigSchema"

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Configuration schema for NodeSendRemoteCommandAction."""

        node_name: str
        remote_ip: str
        command: RequestFormat

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return [
            "network",
            "node",
            config.node_name,
            "service",
            "Terminal",
            "send_remote_command",
            config.remote_ip,
            {"command": config.command},
        ]


class TerminalC2ServerAction(AbstractAction, identifier="c2_server_terminal_command"):
    """Action which causes the C2 Server to send a command to the C2 Beacon to execute the terminal command passed."""

    config: "TerminalC2ServerAction.ConfigSchema"

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Schema for options that can be passed to this action."""

        node_name: str
        commands: Union[List[RequestFormat], RequestFormat]
        ip_address: Optional[str]
        username: Optional[str]
        password: Optional[str]

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request that can be ingested by the simulation."""
        if config.node_name is None:
            return ["do_nothing"]

        command_model = {
            "commands": config.commands,
            "ip_address": config.ip_address,
            "username": config.username,
            "password": config.password,
        }
        return ["network", "node", config.node_name, "application", "C2Server", "terminal_command", command_model]


class RansomwareLaunchC2ServerAction(AbstractAction, identifier="c2_server_ransomware_launch"):
    """Action which causes the C2 Server to send a command to the C2 Beacon to launch the RansomwareScript."""

    config: "RansomwareLaunchC2ServerAction.ConfigSchema"

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Configuration schema for RansomwareLaunchC2ServerAction."""

        node_name: str

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request that can be ingested by the simulation."""
        if config.node_name is None:
            return ["do_nothing"]
        # This action currently doesn't require any further configuration options.
        return ["network", "node", config.node_name, "application", "C2Server", "ransomware_launch"]


class ExfiltrationC2ServerAction(AbstractAction, identifier="c2_server_data_exfiltrate"):
    """Action which exfiltrates a target file from a certain node onto the C2 beacon and then the C2 Server."""

    config: "ExfiltrationC2ServerAction.ConfigSchema"

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Schema for options that can be passed to this action."""

        node_name: str
        username: Optional[str]
        password: Optional[str]
        target_ip_address: str
        target_file_name: str
        target_folder_name: str
        exfiltration_folder_name: Optional[str]

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request that can be ingested by the simulation."""
        if config.node_name is None:
            return ["do_nothing"]

        command_model = {
            "target_file_name": config.target_file_name,
            "target_folder_name": config.target_folder_name,
            "exfiltration_folder_name": config.exfiltration_folder_name,
            "target_ip_address": config.target_ip_address,
            "username": config.username,
            "password": config.password,
        }
        return ["network", "node", config.node_name, "application", "C2Server", "exfiltrate", command_model]


class ConfigureDatabaseClientAction(AbstractAction, identifier="configure_database_client"):
    """Action which sets config parameters for a database client on a node."""

    config: "ConfigureDatabaseClientAction.ConfigSchema"

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Schema for options that can be passed to this action."""

        node_name: str
        model_config = ConfigDict(extra="forbid")

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request that can be ingested by the simulation."""
        if config.node_name is None:
            return ["do_nothing"]
        return ["network", "node", config.node_name, "application", "DatabaseClient", "configure", config.model_config]
