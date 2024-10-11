from typing import ClassVar
from primaite.game.agent.actions.manager import AbstractAction
from primaite.interface.request import RequestFormat

class NodeServiceAbstractAction(AbstractAction):
    class ConfigSchema(AbstractAction.ConfigSchema):
        node_name: str
        service_name: str

    verb: ClassVar[str]

    @classmethod
    def form_request(cls, config:ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return ["network", "node", config.node_name, "service", config.service_name, cls.verb]

class NodeServiceScanAction(NodeServiceAbstractAction, identifier="node_service_scan"):
    verb: str = "scan"

class NodeServiceStopAction(NodeServiceAbstractAction, identifier=...):
    verb: str = "stop"

class NodeServiceStartAction(NodeServiceAbstractAction):
    verb: str = "start"

class NodeServicePauseAction(NodeServiceAbstractAction):
    verb: str = "pause"

class NodeServiceResumeAction(NodeServiceAbstractAction):
    verb: str = "resume"

class NodeServiceRestartAction(NodeServiceAbstractAction):
    verb: str = "restart"

class NodeServiceDisableAction(NodeServiceAbstractAction):
    verb: str = "disable"

class NodeServiceEnableAction(NodeServiceAbstractAction):
    verb: str = "enable"

class NodeServiceFixAction(NodeServiceAbstractAction):
    verb: str = "fix"
