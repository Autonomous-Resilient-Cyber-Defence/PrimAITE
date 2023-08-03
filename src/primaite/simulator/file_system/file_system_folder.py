from typing import Dict, List

from pydantic import PrivateAttr

from primaite.simulator.core import SimComponent
from primaite.simulator.file_system.file_system_file import FileSystemFile


class FileSystemFolder(SimComponent):
    """Simulation FileSystemFolder."""

    _files: List[FileSystemFile] = PrivateAttr([])
    """List of files stored in the folder."""

    _folder_size: float = PrivateAttr(0)
    """The current size of the folder"""

    _is_quarantined: bool = PrivateAttr(False)
    """Flag that marks the folder as quarantined if true."""

    def get_files(self) -> List[FileSystemFile]:
        """Returns the list of files the folder contains."""
        return self._files

    def get_file(self, file_id: str) -> FileSystemFile:
        """Return a FileSystemFile with the matching id."""
        return next((f for f in self._files if f.uuid == file_id), None)

    def add_file(self, file: FileSystemFile):
        """Adds a file to the folder list."""
        self._folder_size += file.get_file_size()

        # add to list
        self._files.append(file)

    def remove_file(self, file_id: str):
        """Removes a file from the folder list."""
        file = next((f for f in self._files if f.uuid == file_id), None)
        self._files.remove(file)

        # remove folder size from folder
        self._folder_size -= file.get_file_size()

    def get_folder_size(self) -> float:
        """Returns a sum of all file sizes in the files list."""
        return sum([file.get_file_size() for file in self._files])

    def quarantine(self):
        """Quarantines the File System Folder."""
        self._is_quarantined = True

    def end_quarantine(self):
        """Ends the quarantine of the File System Folder."""
        self._is_quarantined = False

    def quarantine_status(self) -> bool:
        """Returns true if the folder is being quarantined."""
        return self._is_quarantined

    def describe_state(self) -> Dict:
        """
        Get the current state of the FileSystemFolder as a dict.

        :return: A dict containing the current state of the FileSystemFile.
        """
        pass
