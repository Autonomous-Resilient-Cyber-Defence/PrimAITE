# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
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


class NodeFolderAbstractAction(AbstractAction, identifier="node_folder_abstract"):
    """
    Base class for folder actions.

    Any action which applies to a folder and uses node_name and folder_name as its only two parameters can inherit from
    this base class.
    """

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Base configuration schema for NodeFolder actions."""

        node_name: str
        folder_name: str

    verb: ClassVar[str]

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        if config.node_name is None or config.folder_name is None:
            return ["do_nothing"]
        return [
            "network",
            "node",
            config.node_name,
            "file_system",
            "folder",
            config.folder_name,
            cls.model_fields["verb"].default,
        ]


class NodeFolderScanAction(NodeFolderAbstractAction, identifier="node_folder_scan"):
    """Action which scans a folder."""

    verb: str = "scan"

    class ConfigSchema(NodeFolderAbstractAction.ConfigSchema):
        """Configuration schema for NodeFolderScanAction."""

        verb: str = "scan"


class NodeFolderCheckhashAction(NodeFolderAbstractAction, identifier="node_folder_checkhash"):
    """Action which checks the hash of a folder."""

    verb: str = "checkhash"

    class ConfigSchema(NodeFolderAbstractAction.ConfigSchema):
        """Configuration schema for NodeFolderCheckhashAction."""

        verb: str = "checkhash"


class NodeFolderRepairAction(NodeFolderAbstractAction, identifier="node_folder_repair"):
    """Action which repairs a folder."""

    verb: str = "repair"

    class ConfigSchema(NodeFolderAbstractAction.ConfigSchema):
        """Configuration schema for NodeFolderRepairAction."""

        verb: str = "repair"


class NodeFolderRestoreAction(NodeFolderAbstractAction, identifier="node_folder_restore"):
    """Action which restores a folder."""

    verb: str = "restore"

    class ConfigSchema(NodeFolderAbstractAction.ConfigSchema):
        """Configuration schema for NodeFolderRestoreAction."""

        verb: str = "restore"


class NodeFolderCreateAction(NodeFolderAbstractAction, identifier="node_folder_create"):
    """Action which creates a new folder."""

    verb: str = "create"

    class ConfigSchema(NodeFolderAbstractAction.ConfigSchema):
        """Configuration schema for NodeFolderCreateAction."""

        verb: str = "create"

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        if config.node_name is None or config.folder_name is None:
            return ["do_nothing"]
        return [
            "network",
            "node",
            config.node_name,
            "file_system",
            cls.model_fields["verb"].default,
            "folder",
            config.folder_name,
        ]
