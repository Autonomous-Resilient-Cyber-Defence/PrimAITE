from random import choice
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

        :param name: The name of the file.
        :type name: str

        :param file_type: The FileSystemFileType of the file
        :type file_type: Optional[FileSystemFileType]

        :param size: The size of the FileSystemItem
        :type size: Optional[float]
        """
        # set random file type if none provided

        # set random file type if none provided
        if kwargs.get("file_type") is None:
            kwargs["file_type"] = choice(list(FileSystemFileType))

        # set random file size if none provided
        if kwargs.get("size") is None:
            kwargs["size"] = file_type_sizes_KB[kwargs["file_type"]]

        super().__init__(**kwargs)

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
                "uuid": self.uuid,
                "file_type": self.file_type.name,
            }
        )
        return state
