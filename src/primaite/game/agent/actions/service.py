# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
"""Actions for interacting with services on network hosts."""
from abc import ABC
from typing import ClassVar

from primaite.game.agent.actions.manager import AbstractAction
from primaite.interface.request import RequestFormat

__all__ = (
    "NodeServiceScanAction",
    "NodeServiceStopAction",
    "NodeServiceStartAction",
    "NodeServicePauseAction",
    "NodeServiceResumeAction",
    "NodeServiceRestartAction",
    "NodeServiceDisableAction",
    "NodeServiceEnableAction",
    "NodeServiceFixAction",
)


class NodeServiceAbstractAction(AbstractAction, ABC):
    """Abstract Action for Node Service related actions.

    Any actions which use node_name and service_name can inherit from this class.
    """

    class ConfigSchema(AbstractAction.ConfigSchema, ABC):
        node_name: str
        service_name: str
        verb: ClassVar[str]

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return ["network", "node", config.node_name, "service", config.service_name, config.verb]


class NodeServiceScanAction(NodeServiceAbstractAction, discriminator="node-service-scan"):
    """Action which scans a service."""

    config: "NodeServiceScanAction.ConfigSchema"

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        """Configuration Schema for NodeServiceScanAction."""

        verb: ClassVar[str] = "scan"


class NodeServiceStopAction(NodeServiceAbstractAction, discriminator="node-service-stop"):
    """Action which stops a service."""

    config: "NodeServiceStopAction.ConfigSchema"

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        """Configuration Schema for NodeServiceStopAction."""

        verb: ClassVar[str] = "stop"


class NodeServiceStartAction(NodeServiceAbstractAction, discriminator="node-service-start"):
    """Action which starts a service."""

    config: "NodeServiceStartAction.ConfigSchema"

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        """Configuration Schema for NodeServiceStartAction."""

        verb: ClassVar[str] = "start"


class NodeServicePauseAction(NodeServiceAbstractAction, discriminator="node-service-pause"):
    """Action which pauses a service."""

    config: "NodeServicePauseAction.ConfigSchema"

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        """Configuration Schema for NodeServicePauseAction."""

        verb: ClassVar[str] = "pause"


class NodeServiceResumeAction(NodeServiceAbstractAction, discriminator="node-service-resume"):
    """Action which resumes a service."""

    config: "NodeServiceResumeAction.ConfigSchema"

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        """Configuration Schema for NodeServiceResumeAction."""

        verb: ClassVar[str] = "resume"


class NodeServiceRestartAction(NodeServiceAbstractAction, discriminator="node-service-restart"):
    """Action which restarts a service."""

    config: "NodeServiceRestartAction.ConfigSchema"

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        """Configuration Schema for NodeServiceRestartAction."""

        verb: ClassVar[str] = "restart"


class NodeServiceDisableAction(NodeServiceAbstractAction, discriminator="node-service-disable"):
    """Action which disables a service."""

    config: "NodeServiceDisableAction.ConfigSchema"

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        """Configuration Schema for NodeServiceDisableAction."""

        verb: ClassVar[str] = "disable"


class NodeServiceEnableAction(NodeServiceAbstractAction, discriminator="node-service-enable"):
    """Action which enables a service."""

    config: "NodeServiceEnableAction.ConfigSchema"

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        """Configuration Schema for NodeServiceEnableAction."""

        verb: ClassVar[str] = "enable"


class NodeServiceFixAction(NodeServiceAbstractAction, discriminator="node-service-fix"):
    """Action which fixes a service."""

    config: "NodeServiceFixAction.ConfigSchema"

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        """Configuration Schema for NodeServiceFixAction."""

        verb: ClassVar[str] = "fix"
