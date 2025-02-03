# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from abc import ABC
from typing import ClassVar

from primaite.game.agent.actions.manager import AbstractAction
from primaite.interface.request import RequestFormat

__all__ = (
    "NodeFolderScanAction",
    "NodeFolderCheckhashAction",
    "NodeFolderRepairAction",
    "NodeFolderRestoreAction",
    "NodeFolderCreateAction",
)


class NodeFolderAbstractAction(AbstractAction, ABC):
    """
    Base class for folder actions.

    Any action which applies to a folder and uses node_name and folder_name as its only two parameters can inherit from
    this base class.
    """

    config: "NodeFolderAbstractAction.ConfigSchema"

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Base configuration schema for NodeFolder actions."""

        node_name: str
        folder_name: str
        verb: ClassVar[str]

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        if config.node_name is None or config.folder_name is None:
            return ["do-nothing"]
        return [
            "network",
            "node",
            config.node_name,
            "file_system",
            "folder",
            config.folder_name,
            config.verb,
        ]


class NodeFolderScanAction(NodeFolderAbstractAction, discriminator="node-folder-scan"):
    """Action which scans a folder."""

    config: "NodeFolderScanAction.ConfigSchema"

    class ConfigSchema(NodeFolderAbstractAction.ConfigSchema):
        """Configuration schema for NodeFolderScanAction."""

        verb: ClassVar[str] = "scan"


class NodeFolderCheckhashAction(NodeFolderAbstractAction, discriminator="node-folder-checkhash"):
    """Action which checks the hash of a folder."""

    config: "NodeFolderCheckhashAction.ConfigSchema"

    class ConfigSchema(NodeFolderAbstractAction.ConfigSchema):
        """Configuration schema for NodeFolderCheckhashAction."""

        verb: ClassVar[str] = "checkhash"


class NodeFolderRepairAction(NodeFolderAbstractAction, discriminator="node-folder-repair"):
    """Action which repairs a folder."""

    config: "NodeFolderRepairAction.ConfigSchema"

    class ConfigSchema(NodeFolderAbstractAction.ConfigSchema):
        """Configuration schema for NodeFolderRepairAction."""

        verb: ClassVar[str] = "repair"


class NodeFolderRestoreAction(NodeFolderAbstractAction, discriminator="node-folder-restore"):
    """Action which restores a folder."""

    config: "NodeFolderRestoreAction.ConfigSchema"

    class ConfigSchema(NodeFolderAbstractAction.ConfigSchema):
        """Configuration schema for NodeFolderRestoreAction."""

        verb: ClassVar[str] = "restore"


class NodeFolderCreateAction(NodeFolderAbstractAction, discriminator="node-folder-create"):
    """Action which creates a new folder."""

    config: "NodeFolderCreateAction.ConfigSchema"

    class ConfigSchema(NodeFolderAbstractAction.ConfigSchema):
        """Configuration schema for NodeFolderCreateAction."""

        verb: ClassVar[str] = "create"

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        if config.node_name is None or config.folder_name is None:
            return ["do-nothing"]
        return [
            "network",
            "node",
            config.node_name,
            "file_system",
            config.verb,
            "folder",
            config.folder_name,
        ]
