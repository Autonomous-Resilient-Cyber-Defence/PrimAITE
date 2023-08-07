from random import choice, randint
from typing import Dict

from primaite.simulator.file_system.file_system_file_type import file_type_sizes_KB, FileSystemFileType
from primaite.simulator.file_system.file_system_item_abc import FileSystemItem


class FileSystemFile(FileSystemItem):
    """Class that represents a file in the simulation."""

    file_type: FileSystemFileType = None
    """The type of the FileSystemFile"""

    def __init__(self, **kwargs):
        """
        Initialise FileSystemFile class.

        :param item_name: The name of the file.
        :type item_name: str

        :param file_type: The FileSystemFileType of the file
        :type file_type: Optional[FileSystemFileType]

        :param item_size: The size of the FileSystemItem
        :type item_size: Optional[float]
        """
        # set random file type if none provided
        if kwargs.get("item_name") is None:
            raise Exception("File name not provided.")

        # set random file type if none provided
        if kwargs.get("file_type") is None:
            kwargs["file_type"] = choice(list(FileSystemFileType))

        # set random file size if none provided
        if kwargs.get("item_size") is None:
            kwargs["item_size"] = float(randint(1, file_type_sizes_KB[kwargs["file_type"]]))

        super().__init__(**kwargs)

    def get_file_name(self) -> str:
        """Returns the name of the file."""
        return self.item_name

    def get_file_size(self) -> float:
        """Returns the size of the file system item."""
        return self.item_size

    def get_file_type(self) -> FileSystemFileType:
        """Returns the FileSystemFileType of the file."""
        return self.file_type

    def describe_state(self) -> Dict:
        """
        Get the current state of the FileSystemFile as a dict.

        :return: A dict containing the current state of the FileSystemFile.
        """
        pass
