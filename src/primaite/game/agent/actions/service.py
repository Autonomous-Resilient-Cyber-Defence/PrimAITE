# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from typing import ClassVar

from primaite.game.agent.actions.manager import AbstractAction
from primaite.interface.request import RequestFormat


class NodeServiceAbstractAction(AbstractAction):
    class ConfigSchema(AbstractAction.ConfigSchema):
        node_name: str
        service_name: str

    verb: ClassVar[str]

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return ["network", "node", config.node_name, "service", config.service_name, cls.verb]


class NodeServiceScanAction(NodeServiceAbstractAction, identifier="node_service_scan"):
    """Action which scans a service."""

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        verb: str = "scan"


class NodeServiceStopAction(NodeServiceAbstractAction, identifier="node_service_stop"):
    """Action which stops a service."""

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        verb: str = "stop"


class NodeServiceStartAction(NodeServiceAbstractAction, identifier="node_service_start"):
    """Action which starts a service."""

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        verb: str = "start"


class NodeServicePauseAction(NodeServiceAbstractAction, identifier="node_service_pause"):
    """Action which pauses a service."""

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        verb: str = "pause"


class NodeServiceResumeAction(NodeServiceAbstractAction, identifier="node_service_resume"):
    """Action which resumes a service."""

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        verb: str = "resume"


class NodeServiceRestartAction(NodeServiceAbstractAction, identifier="node_service_restart"):
    """Action which restarts a service."""

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        verb: str = "restart"


class NodeServiceDisableAction(NodeServiceAbstractAction, identifier="node_service_disable"):
    """Action which disables a service."""

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        verb: str = "disable"


class NodeServiceEnableAction(NodeServiceAbstractAction, identifier="node_service_enable"):
    """Action which enables a service."""

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        verb: str = "enable"


class NodeServiceFixAction(NodeServiceAbstractAction, identifier="node_service_fix"):
    """Action which fixes a service."""

    class ConfigSchema(NodeServiceAbstractAction.ConfigSchema):
        verb: str = "fix"
