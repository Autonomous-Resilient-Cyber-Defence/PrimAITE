# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from abc import abstractmethod
from typing import ClassVar, Dict

from primaite.game.agent.actions.manager import AbstractAction
from primaite.interface.request import RequestFormat


class NodeApplicationAbstractAction(AbstractAction):
    """
    Base class for application actions.

    Any action which applies to an application and uses node_id and application_id as its only two parameters can
    inherit from this base class.
    """

    class ConfigSchema(AbstractAction.ConfigSchema):
        node_name: str
        application_name: str

    verb: ClassVar[str]

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        if config.node_name is None or config.application_name is None:
            return ["do_nothing"]
        return ["network", "node", config.node_name, "application", config.application_name, cls.verb]


class NodeApplicationExecuteAction(NodeApplicationAbstractAction, identifier="node_application_execute"):
    """Action which executes an application."""

    class ConfigSchema(NodeApplicationAbstractAction.ConfigSchema):
        verb: str = "execute"


class NodeApplicationScanAction(NodeApplicationAbstractAction, identifier="node_application_scan"):
    """Action which scans an application."""

    class ConfigSchema(NodeApplicationAbstractAction.ConfigSchema):
        verb: str = "scan"


class NodeApplicationCloseAction(NodeApplicationAbstractAction, identifier="node_application_close"):
    """Action which closes an application."""

    class ConfigSchema(NodeApplicationAbstractAction.ConfigSchema):
        verb: str = "close"


class NodeApplicationFixAction(NodeApplicationAbstractAction, identifier="node_application_fix"):
    """Action which fixes an application."""

    class ConfigSchema(NodeApplicationAbstractAction.ConfigSchema):
        verb: str = "fix"


class NodeApplicationInstallAction(AbstractAction):
    """Action which installs an application."""

    class ConfigSchema(NodeApplicationAbstractAction.ConfigSchema):
        verb: str = "install"
