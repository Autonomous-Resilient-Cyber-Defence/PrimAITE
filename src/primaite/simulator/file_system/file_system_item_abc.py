from typing import Dict

from primaite.simulator.core import SimComponent


class FileSystemItem(SimComponent):
    """Abstract base class for FileSystemItems used in the file system simulation."""

    name: str
    """The name of the FileSystemItem."""

    size: float = 0
    """The size the item takes up on disk."""

    def describe_state(self) -> Dict:
        """Returns the state of the FileSystemItem."""
        pass
