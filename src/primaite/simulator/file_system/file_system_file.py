from typing import Dict

from primaite.simulator.file_system.file_system_file_type import FileSystemFileType
from primaite.simulator.file_system.file_system_item_abc import FileSystemItemABC


class FileSystemFile(FileSystemItemABC):
    """Class that represents a file in the simulation."""

    _file_type: FileSystemFileType
    """The type of the FileSystemFile"""

    def get_file_type(self) -> FileSystemFileType:
        """Returns the FileSystemFileType of the file."""
        return self._file_type

    def move(self, target_directory: str):
        """
        Changes the parent_item of the FileSystemFile.

        Essentially simulates the file system item being moved from folder to folder

        :param target_directory: The UUID of the directory the file system item should be moved to
        :type target_directory: str
        """
        super().move(target_directory)

    def describe_state(self) -> Dict:
        """
        Get the current state of the FileSystemFile as a dict.

        :return: A dict containing the current state of the FileSystemFile.
        """
        pass
