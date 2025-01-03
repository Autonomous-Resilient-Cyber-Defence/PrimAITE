# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from typing import ClassVar

from primaite.game.agent.actions.manager import AbstractAction
from primaite.interface.request import RequestFormat

__all__ = (
    "NodeFileCreateAction",
    "NodeFileScanAction",
    "NodeFileDeleteAction",
    "NodeFileRestoreAction",
    "NodeFileCorruptAction",
    "NodeFileAccessAction",
    "NodeFileCheckhashAction",
    "NodeFileRepairAction",
)


class NodeFileAbstractAction(AbstractAction, identifier="node_file_abstract_action"):
    """Abstract base class for file actions.

    Any action which applies to a file and uses node_name, folder_name, and file_name as its
    only three parameters can inherit from this base class.
    """

    config: "NodeFileAbstractAction.ConfigSchema"

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Configuration Schema for NodeFileAbstractAction."""

        node_name: str
        folder_name: str
        file_name: str
        verb: ClassVar[str]

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        if config.node_name is None or config.folder_name is None or config.file_name is None:
            return ["do_nothing"]
        return [
            "network",
            "node",
            config.node_name,
            "file_system",
            "folder",
            config.folder_name,
            "file",
            config.file_name,
            config.verb,
        ]


class NodeFileCreateAction(NodeFileAbstractAction, identifier="node_file_create"):
    """Action which creates a new file in a given folder."""

    config: "NodeFileCreateAction.ConfigSchema"

    class ConfigSchema(NodeFileAbstractAction.ConfigSchema):
        """Configuration schema for NodeFileCreateAction."""

        verb: str = "create"
        force: bool = False

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        if config.node_name is None or config.folder_name is None or config.file_name is None:
            return ["do_nothing"]
        return [
            "network",
            "node",
            config.node_name,
            "file_system",
            config.verb,
            "file",
            config.folder_name,
            config.file_name,
            config.verb,
        ]


class NodeFileScanAction(NodeFileAbstractAction, identifier="node_file_scan"):
    """Action which scans a file."""

    config: "NodeFileScanAction.ConfigSchema"

    class ConfigSchema(NodeFileAbstractAction.ConfigSchema):
        """Configuration schema for NodeFileScanAction."""

        verb: str = "scan"


class NodeFileDeleteAction(NodeFileAbstractAction, identifier="node_file_delete"):
    """Action which deletes a file."""

    config: "NodeFileDeleteAction.ConfigSchema"

    class ConfigSchema(NodeFileAbstractAction.ConfigSchema):
        """Configuration schema for NodeFileDeleteAction."""

        verb: str = "delete"

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        if config.node_name is None or config.folder_name is None or config.file_name is None:
            return ["do_nothing"]
        return [
            "network",
            "node",
            config.node_name,
            "file_system",
            config.verb,
            "file",
            config.folder_name,
            config.file_name,
        ]


class NodeFileRestoreAction(NodeFileAbstractAction, identifier="node_file_restore"):
    """Action which restores a file."""

    config: "NodeFileRestoreAction.ConfigSchema"

    class ConfigSchema(NodeFileAbstractAction.ConfigSchema):
        """Configuration schema for NodeFileRestoreAction."""

        verb: str = "restore"


class NodeFileCorruptAction(NodeFileAbstractAction, identifier="node_file_corrupt"):
    """Action which corrupts a file."""

    config: "NodeFileCorruptAction.ConfigSchema"

    class ConfigSchema(NodeFileAbstractAction.ConfigSchema):
        """Configuration schema for NodeFileCorruptAction."""

        verb: str = "corrupt"


class NodeFileAccessAction(NodeFileAbstractAction, identifier="node_file_access"):
    """Action which increases a file's access count."""

    config: "NodeFileAccessAction.ConfigSchema"

    class ConfigSchema(NodeFileAbstractAction.ConfigSchema):
        """Configuration schema for NodeFileAccessAction."""

        verb: str = "access"

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        if config.node_name is None or config.folder_name is None or config.file_name is None:
            return ["do_nothing"]
        return [
            "network",
            "node",
            config.node_name,
            "file_system",
            config.verb,
            config.folder_name,
            config.file_name,
        ]


class NodeFileCheckhashAction(NodeFileAbstractAction, identifier="node_file_checkhash"):
    """Action which checks the hash of a file."""

    config: "NodeFileCheckhashAction.ConfigSchema"

    class ConfigSchema(NodeFileAbstractAction.ConfigSchema):
        """Configuration schema for NodeFileCheckhashAction."""

        verb: str = "checkhash"


class NodeFileRepairAction(NodeFileAbstractAction, identifier="node_file_repair"):
    """Action which repairs a file."""

    config: "NodeFileRepairAction.ConfigSchema"

    class ConfigSchema(NodeFileAbstractAction.ConfigSchema):
        """Configuration Schema for NodeFileRepairAction."""

        verb: str = "repair"
