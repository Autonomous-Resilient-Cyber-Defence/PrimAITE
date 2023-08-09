from typing import Dict, Optional

from primaite import getLogger
from primaite.simulator.file_system.file_system_file import FileSystemFile
from primaite.simulator.file_system.file_system_item_abc import FileSystemItem

_LOGGER = getLogger(__name__)


class FileSystemFolder(FileSystemItem):
    """Simulation FileSystemFolder."""

    files: Dict = {}
    """List of files stored in the folder."""

    is_quarantined: bool = False
    """Flag that marks the folder as quarantined if true."""

    def get_file_by_id(self, file_id: str) -> FileSystemFile:
        """Return a FileSystemFile with the matching id."""
        return self.files.get(file_id)

    def add_file(self, file: FileSystemFile):
        """Adds a file to the folder list."""
        if file is None or not isinstance(file, FileSystemFile):
            raise Exception(f"Invalid file: {file}")

        # check if file with id already exists in folder
        if self.get_file_by_id(file.uuid) is not None:
            _LOGGER.debug(f"File with id {file.uuid} already exists in folder")
        else:
            # add to list
            self.files[file.uuid] = file
            self.size += file.size

    def remove_file(self, file: Optional[FileSystemFile]):
        """
        Removes a file from the folder list.

        The method can take a FileSystemFile object or a file id.

        :param: file: The file to remove
        :type: Optional[FileSystemFile]
        """
        if file is None or not isinstance(file, FileSystemFile):
            raise Exception(f"Invalid file: {file}")

        if self.files.get(file.uuid):
            del self.files[file.uuid]

            self.size -= file.size
        else:
            _LOGGER.debug(f"File with UUID {file.uuid} was not found.")

    def quarantine(self):
        """Quarantines the File System Folder."""
        self.is_quarantined = True

    def end_quarantine(self):
        """Ends the quarantine of the File System Folder."""
        self.is_quarantined = False

    def quarantine_status(self) -> bool:
        """Returns true if the folder is being quarantined."""
        return self.is_quarantined

    def describe_state(self) -> Dict:
        """
        Get the current state of the FileSystemFolder as a dict.

        :return: A dict containing the current state of the FileSystemFile.
        """
        pass
