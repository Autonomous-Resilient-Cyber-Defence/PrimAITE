# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
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

    class ConfigSchema(AbstractAction.ConfigSchema):
        node_name: str
        service_name: str

    verb: ClassVar[str]

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return ["network", "node", config.node_name, "service", config.service_name, cls.model_fields["verb"].default]


class NodeServiceScanAction(NodeServiceAbstractAction, identifier="node_service_scan"):
    """Action which scans a service."""

    verb: str = "scan"

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        """Configuration Schema for NodeServiceScanAction."""

        verb: str = "scan"


class NodeServiceStopAction(NodeServiceAbstractAction, identifier="node_service_stop"):
    """Action which stops a service."""

    verb: str = "stop"

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        """Configuration Schema for NodeServiceStopAction."""

        verb: str = "stop"


class NodeServiceStartAction(NodeServiceAbstractAction, identifier="node_service_start"):
    """Action which starts a service."""

    verb: str = "start"

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        """Configuration Schema for NodeServiceStartAction."""

        verb: str = "start"


class NodeServicePauseAction(NodeServiceAbstractAction, identifier="node_service_pause"):
    """Action which pauses a service."""

    verb: str = "pause"

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        """Configuration Schema for NodeServicePauseAction."""

        verb: str = "pause"


class NodeServiceResumeAction(NodeServiceAbstractAction, identifier="node_service_resume"):
    """Action which resumes a service."""

    verb: str = "resume"

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        """Configuration Schema for NodeServiceResumeAction."""

        verb: str = "resume"


class NodeServiceRestartAction(NodeServiceAbstractAction, identifier="node_service_restart"):
    """Action which restarts a service."""

    verb: str = "restart"

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        """Configuration Schema for NodeServiceRestartAction."""

        verb: str = "restart"


class NodeServiceDisableAction(NodeServiceAbstractAction, identifier="node_service_disable"):
    """Action which disables a service."""

    verb: str = "disable"

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        """Configuration Schema for NodeServiceDisableAction."""

        verb: str = "disable"


class NodeServiceEnableAction(NodeServiceAbstractAction, identifier="node_service_enable"):
    """Action which enables a service."""

    verb: str = "enable"

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        """Configuration Schema for NodeServiceEnableAction."""

        verb: str = "enable"


class NodeServiceFixAction(NodeServiceAbstractAction, identifier="node_service_fix"):
    """Action which fixes a service."""

    verb: str = "fix"

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        """Configuration Schema for NodeServiceFixAction."""

        verb: str = "fix"
