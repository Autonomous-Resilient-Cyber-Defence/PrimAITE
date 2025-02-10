# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from abc import ABC, abstractmethod

from primaite.game.agent.actions.manager import AbstractAction
from primaite.interface.request import RequestFormat

__all__ = (
    "NodeSessionsRemoteLoginAction",
    "NodeSessionsRemoteLogoutAction",
    "NodeAccountChangePasswordAction",
)


class NodeSessionAbstractAction(AbstractAction, ABC):
    """Base class for NodeSession actions."""

    class ConfigSchema(AbstractAction.ConfigSchema, ABC):
        """Base configuration schema for NodeSessionAbstractActions."""

        node_name: str
        remote_ip: str

    @classmethod
    @abstractmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """
        Abstract method for request forming.

        Should return the action formatted as a request which can be ingested by the PrimAITE simulation.
        """
        pass


class NodeSessionsRemoteLoginAction(NodeSessionAbstractAction, discriminator="node-session-remote-login"):
    """Action which performs a remote session login."""

    config: "NodeSessionsRemoteLoginAction.ConfigSchema"

    class ConfigSchema(NodeSessionAbstractAction.ConfigSchema):
        """Configuration schema for NodeSessionsRemoteLoginAction."""

        username: str
        password: str

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        if config.node_name is None or config.remote_ip is None:
            return ["do-nothing"]
        return [
            "network",
            "node",
            config.node_name,
            "service",
            "terminal",
            "node-session-remote-login",
            config.username,
            config.password,
            config.remote_ip,
        ]


class NodeSessionsRemoteLogoutAction(NodeSessionAbstractAction, discriminator="node-session-remote-logoff"):
    """Action which performs a remote session logout."""

    class ConfigSchema(NodeSessionAbstractAction.ConfigSchema):
        """Configuration schema for NodeSessionsRemoteLogoutAction."""

        verb: str = "remote_logoff"

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        if config.node_name is None or config.remote_ip is None:
            return ["do-nothing"]
        return ["network", "node", config.node_name, "service", "terminal", config.verb, config.remote_ip]


class NodeAccountChangePasswordAction(AbstractAction, discriminator="node-account-change-password"):
    """Action which changes the password for a user."""

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Configuration schema for NodeAccountsChangePasswordAction."""

        node_name: str
        username: str
        current_password: str
        new_password: str

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return [
            "network",
            "node",
            config.node_name,
            "service",
            "user-manager",
            "change_password",
            config.username,
            config.current_password,
            config.new_password,
        ]
