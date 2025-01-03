# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from typing import ClassVar

from primaite.game.agent.actions.abstract import AbstractAction
from primaite.interface.request import RequestFormat

__all__ = (
    "NodeApplicationExecuteAction",
    "NodeApplicationScanAction",
    "NodeApplicationCloseAction",
    "NodeApplicationFixAction",
    "NodeApplicationInstallAction",
    "NodeApplicationRemoveAction",
)


class NodeApplicationAbstractAction(AbstractAction, identifier="node_application_abstract_action"):
    """
    Base class for application actions.

    Any action which applies to an application and uses node_id and application_id as its only two parameters can
    inherit from this base class.
    """

    config: "NodeApplicationAbstractAction.ConfigSchema"

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Base Configuration schema for Node Application actions."""

        node_name: str
        application_name: str
        verb: ClassVar[str]

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return [
            "network",
            "node",
            config.node_name,
            "application",
            config.application_name,
            config.verb,
        ]


class NodeApplicationExecuteAction(NodeApplicationAbstractAction, identifier="node_application_execute"):
    """Action which executes an application."""

    config: "NodeApplicationExecuteAction.ConfigSchema"

    class ConfigSchema(NodeApplicationAbstractAction.ConfigSchema):
        """Configuration schema for NodeApplicationExecuteAction."""

        verb: str = "execute"


class NodeApplicationScanAction(NodeApplicationAbstractAction, identifier="node_application_scan"):
    """Action which scans an application."""

    config: "NodeApplicationScanAction.ConfigSchema"

    class ConfigSchema(NodeApplicationAbstractAction.ConfigSchema):
        """Configuration schema for NodeApplicationScanAction."""

        verb: str = "scan"


class NodeApplicationCloseAction(NodeApplicationAbstractAction, identifier="node_application_close"):
    """Action which closes an application."""

    config: "NodeApplicationCloseAction.ConfigSchema"

    class ConfigSchema(NodeApplicationAbstractAction.ConfigSchema):
        """Configuration schema for NodeApplicationCloseAction."""

        verb: str = "close"


class NodeApplicationFixAction(NodeApplicationAbstractAction, identifier="node_application_fix"):
    """Action which fixes an application."""

    config: "NodeApplicationFixAction.ConfigSchema"

    class ConfigSchema(NodeApplicationAbstractAction.ConfigSchema):
        """Configuration schema for NodeApplicationFixAction."""

        verb: str = "fix"


class NodeApplicationInstallAction(NodeApplicationAbstractAction, identifier="node_application_install"):
    """Action which installs an application."""

    config: "NodeApplicationInstallAction.ConfigSchema"

    class ConfigSchema(NodeApplicationAbstractAction.ConfigSchema):
        """Configuration schema for NodeApplicationInstallAction."""

        verb: str = "install"

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return [
            "network",
            "node",
            config.node_name,
            "software_manager",
            "application",
            config.verb,
            config.application_name,
        ]


class NodeApplicationRemoveAction(NodeApplicationAbstractAction, identifier="node_application_remove"):
    """Action which removes/uninstalls an application."""

    config: "NodeApplicationRemoveAction.ConfigSchema"

    class ConfigSchema(NodeApplicationAbstractAction.ConfigSchema):
        """Configuration schema for NodeApplicationRemoveAction."""

        verb: str = "uninstall"

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return [
            "network",
            "node",
            config.node_name,
            "software_manager",
            "application",
            config.verb,
            config.application_name,
        ]
