from abc import ABC, abstractmethod
from uuid import uuid4

from primaite.simulator.core import SimComponent


class FileSystemItemABC(SimComponent, ABC):
    """Abstract Base class for any file system items e.g. files and folders."""

    _uuid: str
    """Unique identifier for the FileSystemItem"""

    _parent_item: str
    """UUID of the parent FileSystemItem"""

    _item_size: float
    """Disk size of the FileSystemItem"""

    def __init__(self, parent_item: str, item_size: float):
        """
        Abstract base class used by FileSystem items.

        :param parent_item: The UUID of the FileSystemItem parent
        :type parent_item: str

        :param item_size: The size of the FileSystemItem
        :type item_size: float
        """
        super().__init__()

        # generate random uuid for file system item
        self._uuid = str(uuid4())

        self._parent_item = parent_item

        self._item_size = item_size

    def get_item_uuid(self) -> str:
        """Returns the file system item UUID."""
        return self._uuid

    def get_item_parent(self) -> str:
        """Returns the UUID of the item's parent."""
        return self._parent_item

    def get_item_size(self) -> float:
        """Returns the item size."""
        return self._item_size

    @abstractmethod
    def move(self, target_directory: str):
        """
        Changes the parent_item of the file system item.

        Essentially simulates the file system item being moved from folder to folder

        :param target_directory: The UUID of the directory the file system item should be moved to
        :type target_directory: str
        """
        self._parent_item = target_directory
