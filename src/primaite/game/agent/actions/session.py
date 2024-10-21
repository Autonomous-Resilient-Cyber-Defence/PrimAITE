# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from abc import abstractmethod

from primaite.game.agent.actions.manager import AbstractAction
from primaite.interface.request import RequestFormat

__all__ = ("NodeSessionsRemoteLoginAction", "NodeSessionsRemoteLogoutAction")


class NodeSessionAbstractAction(AbstractAction, identifier="node_session_abstract"):
    """Base class for NodeSession actions."""

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Base configuration schema for NodeSessionAbstractActions."""

        node_name: str
        remote_ip: str

    @classmethod
    @abstractmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Abstract method. Should return the action formatted as a request which 
            can be ingested by the PrimAITE simulation."""
        pass


class NodeSessionsRemoteLoginAction(NodeSessionAbstractAction, identifier="node_session_remote_login"):
    """Action which performs a remote session login."""

    class ConfigSchema(NodeSessionAbstractAction.ConfigSchema):
        """Configuration schema for NodeSessionsRemoteLoginAction."""

        username: str
        password: str

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        if config.node_name is None or config.remote_ip is None:
            return ["do_nothing"]
        return [
            "network",
            "node",
            config.node_name,
            "service",
            "Terminal",
            "ssh_to_remote",
            config.username,
            config.password,
            config.remote_ip,
        ]


class NodeSessionsRemoteLogoutAction(NodeSessionAbstractAction, identifier="node_session_remote_logout"):
    """Action which performs a remote session logout."""

    class ConfigSchema(NodeSessionAbstractAction.ConfigSchema):
        """Configuration schema for NodeSessionsRemoteLogoutAction."""

        pass

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        if config.node_name is None or config.remote_ip is None:
            return ["do_nothing"]
        return ["network", "node", config.node_name, "service", "Terminal", "remote_logoff", config.remote_ip]
