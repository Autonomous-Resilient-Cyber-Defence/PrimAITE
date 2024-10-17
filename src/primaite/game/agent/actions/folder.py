# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from abc import abstractmethod
from typing import ClassVar, Dict

from primaite.game.agent.actions.manager import AbstractAction
from primaite.interface.request import RequestFormat


class NodeFolderAbstractAction(AbstractAction):
    """
    Base class for folder actions.

    Any action which applies to a folder and uses node_id and folder_id as its only two parameters can inherit from
    this base class.
    """

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Base configuration schema for NodeFolder actions."""

        node_name: str
        folder_name: str

    verb: ClassVar[str]

    @classmethod
    def form_request(cls, node_id: int, folder_id: int) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        node_name = cls.manager.get_node_name_by_idx(node_id)
        folder_name = cls.manager.get_folder_name_by_idx(node_idx=node_id, folder_idx=folder_id)
        if node_name is None or folder_name is None:
            return ["do_nothing"]
        return ["network", "node", node_name, "file_system", "folder", folder_name, cls.verb]


class NodeFolderScanAction(NodeFolderAbstractAction, identifier="node_folder_scan"):
    """Action which scans a folder."""

    class ConfigSchema(NodeFolderAbstractAction.ConfigSchema):
        """Configuration schema for NodeFolderScanAction."""

        verb: str = "scan"


class NodeFolderCheckhashAction(NodeFolderAbstractAction, identifier="node_folder_checkhash"):
    """Action which checks the hash of a folder."""

    class ConfigSchema(NodeFolderAbstractAction.ConfigSchema):
        """Configuration schema for NodeFolderCheckhashAction."""

        verb: str = "checkhash"


class NodeFolderRepairAction(NodeFolderAbstractAction, identifier="node_folder_repair"):
    """Action which repairs a folder."""

    class ConfigSchema(NodeFolderAbstractAction.ConfigSchema):
        """Configuration schema for NodeFolderRepairAction."""

        verb: str = "repair"


class NodeFolderRestoreAction(NodeFolderAbstractAction, identifier="node_folder_restore"):
    """Action which restores a folder."""

    class ConfigSchema(NodeFolderAbstractAction.ConfigSchema):
        """Configuration schema for NodeFolderRestoreAction."""

        verb: str = "restore"


class NodeFolderCreateAction(AbstractAction, identifier="node_folder_create"):
    """Action which creates a new folder."""

    class ConfigSchema(NodeFolderAbstractAction.ConfigSchema):
        """Configuration schema for NodeFolderCreateAction."""

        verb: str = "create"
