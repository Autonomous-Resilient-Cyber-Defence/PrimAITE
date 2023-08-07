from typing import Dict

from primaite.simulator.core import SimComponent


class FileSystemItem(SimComponent):
    """Abstract base class for FileSystemItems used in the file system simulation."""

    item_size: float = 0
    """The size the item takes up on disk."""

    item_name: str
    """The name of the file system item."""

    def describe_state(self) -> Dict:
        """Returns the state of the FileSystemItem."""
        pass
