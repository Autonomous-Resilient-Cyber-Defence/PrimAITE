from typing import Dict

from primaite.simulator.core import SimComponent


class FileSystemItem(SimComponent):
    """Abstract base class for FileSystemItems used in the file system simulation."""

    name: str
    """The name of the FileSystemItem."""

    size: float = 0
    """The size the item takes up on disk."""

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        Please see :py:meth:`primaite.simulator.core.SimComponent.describe_state` for a more detailed explanation.

        :return: Current state of this object and child objects.
        :rtype: Dict
        """
        state = super().describe_state()
        state.update(
            {
                "name": self.name,
                "size": self.size,
            }
        )
        return state
