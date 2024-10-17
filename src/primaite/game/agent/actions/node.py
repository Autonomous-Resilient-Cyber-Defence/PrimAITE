# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from abc import abstractmethod
from typing import ClassVar, Dict

from primaite.game.agent.actions.manager import AbstractAction
from primaite.interface.request import RequestFormat


class NodeAbstractAction(AbstractAction):
    """
    Abstract base class for node actions.

    Any action which applies to a node and uses node_name as its only parameter can inherit from this base class.
    """

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Base Configuration schema for Node actions."""

        node_name: str

    verb: ClassVar[str]

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return ["network", "node", config.node_name, cls.verb]


class NodeOSScanAction(NodeAbstractAction, identifier="node_os_scan"):
    """Action which scans a node's OS."""

    class ConfigSchema(NodeAbstractAction.ConfigSchema):
        """Configuration schema for NodeOSScanAction."""

        verb: str = "scan"


class NodeShutdownAction(NodeAbstractAction, identifier="node_shutdown"):
    """Action which shuts down a node."""

    class ConfigSchema(NodeAbstractAction.ConfigSchema):
        """Configuration schema for NodeShutdownAction."""

        verb: str = "shutdown"


class NodeStartupAction(NodeAbstractAction, identifier="node_startup"):
    """Action which starts up a node."""

    class ConfigSchema(NodeAbstractAction.ConfigSchema):
        """Configuration schema for NodeStartupAction."""

        verb: str = "startup"


class NodeResetAction(NodeAbstractAction, identifier="node_reset"):
    """Action which resets a node."""

    class ConfigSchema(NodeAbstractAction.ConfigSchema):
        """Configuration schema for NodeResetAction."""

        verb: str = "reset"
