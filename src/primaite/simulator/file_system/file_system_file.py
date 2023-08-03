from random import choice, random
from typing import Dict

from primaite.simulator.core import SimComponent
from primaite.simulator.file_system.file_system_file_type import FileSystemFileType


class FileSystemFile(SimComponent):
    """Class that represents a file in the simulation."""

    file_type: FileSystemFileType = None
    """The type of the FileSystemFile"""

    file_size: float = 0
    """Disk size of the FileSystemItem"""

    def __init__(self, **kwargs):
        """
        Initialise FileSystemFile class.

        :param file_type: The FileSystemFileType of the file
        :type file_type: Optional[FileSystemFileType]

        :param file_size: The size of the FileSystemItem
        :type file_size: Optional[float]
        """
        super().__init__(**kwargs)

        self.file_type = choice(list(FileSystemFileType))
        self.file_size = random()

        # set random file size if non provided
        if kwargs.get("file_size") is not None:
            self.file_size = kwargs.get("file_size")

        # set random file type if none provided
        if kwargs.get("file_type") is None:
            self.file_type = kwargs.get("file_type")

    def get_file_size(self) -> float:
        """Returns the size of the file system item."""
        return self.file_size

    def get_file_type(self) -> FileSystemFileType:
        """Returns the FileSystemFileType of the file."""
        return self.file_type

    def describe_state(self) -> Dict:
        """
        Get the current state of the FileSystemFile as a dict.

        :return: A dict containing the current state of the FileSystemFile.
        """
        pass
