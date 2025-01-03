# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
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


class NodeServiceAbstractAction(AbstractAction, identifier="node_service_abstract"):
    """Abstract Action for Node Service related actions.

    Any actions which use node_name and service_name can inherit from this class.
    """

    config: "NodeServiceAbstractAction.ConfigSchema"

    class ConfigSchema(AbstractAction.ConfigSchema):
        node_name: str
        service_name: str
        verb: ClassVar[str]

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return ["network", "node", config.node_name, "service", config.service_name, config.verb]


class NodeServiceScanAction(NodeServiceAbstractAction, identifier="node_service_scan"):
    """Action which scans a service."""

    config: "NodeServiceScanAction.ConfigSchema"

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        """Configuration Schema for NodeServiceScanAction."""

        verb: str = "scan"


class NodeServiceStopAction(NodeServiceAbstractAction, identifier="node_service_stop"):
    """Action which stops a service."""

    config: "NodeServiceStopAction.ConfigSchema"

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        """Configuration Schema for NodeServiceStopAction."""

        verb: str = "stop"


class NodeServiceStartAction(NodeServiceAbstractAction, identifier="node_service_start"):
    """Action which starts a service."""

    config: "NodeServiceStartAction.ConfigSchema"

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        """Configuration Schema for NodeServiceStartAction."""

        verb: str = "start"


class NodeServicePauseAction(NodeServiceAbstractAction, identifier="node_service_pause"):
    """Action which pauses a service."""

    config: "NodeServicePauseAction.ConfigSchema"

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        """Configuration Schema for NodeServicePauseAction."""

        verb: str = "pause"


class NodeServiceResumeAction(NodeServiceAbstractAction, identifier="node_service_resume"):
    """Action which resumes a service."""

    config: "NodeServiceResumeAction.ConfigSchema"

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        """Configuration Schema for NodeServiceResumeAction."""

        verb: str = "resume"


class NodeServiceRestartAction(NodeServiceAbstractAction, identifier="node_service_restart"):
    """Action which restarts a service."""

    config: "NodeServiceRestartAction.ConfigSchema"

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        """Configuration Schema for NodeServiceRestartAction."""

        verb: str = "restart"


class NodeServiceDisableAction(NodeServiceAbstractAction, identifier="node_service_disable"):
    """Action which disables a service."""

    config: "NodeServiceDisableAction.ConfigSchema"

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        """Configuration Schema for NodeServiceDisableAction."""

        verb: str = "disable"


class NodeServiceEnableAction(NodeServiceAbstractAction, identifier="node_service_enable"):
    """Action which enables a service."""

    config: "NodeServiceEnableAction.ConfigSchema"

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        """Configuration Schema for NodeServiceEnableAction."""

        verb: str = "enable"


class NodeServiceFixAction(NodeServiceAbstractAction, identifier="node_service_fix"):
    """Action which fixes a service."""

    config: "NodeServiceFixAction.ConfigSchema"

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        """Configuration Schema for NodeServiceFixAction."""

        verb: str = "fix"
