from typing import Dict

from pydantic import PrivateAttr

from primaite.simulator.core import SimComponent
from primaite.simulator.file_system.file_system_file_type import FileSystemFileType


class FileSystemFile(SimComponent):
    """Class that represents a file in the simulation."""

    _file_type: FileSystemFileType = PrivateAttr()
    """The type of the FileSystemFile"""

    _file_size: float = PrivateAttr()
    """Disk size of the FileSystemItem"""

    def __init__(self, file_type: FileSystemFileType, file_size: float, **kwargs):
        """
        Initialise FileSystemFile class.

        :param item_parent: The UUID of the FileSystemItem parent
        :type item_parent: str

        :param file_size: The size of the FileSystemItem
        :type file_size: float
        """
        super().__init__(**kwargs)

        self._file_type = file_type
        self._file_size = file_size

    def get_file_size(self) -> float:
        """Returns the size of the file system item."""
        return self._file_size

    def get_file_type(self) -> FileSystemFileType:
        """Returns the FileSystemFileType of the file."""
        return self._file_type

    def describe_state(self) -> Dict:
        """
        Get the current state of the FileSystemFile as a dict.

        :return: A dict containing the current state of the FileSystemFile.
        """
        pass
