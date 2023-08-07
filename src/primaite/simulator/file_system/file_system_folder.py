from typing import Dict, List, Optional

from primaite.simulator.file_system.file_system_file import FileSystemFile
from primaite.simulator.file_system.file_system_item_abc import FileSystemItemABC


class FileSystemFolder(FileSystemItemABC):
    """Simulation FileSystemFolder."""

    files: List[FileSystemFile] = []
    """List of files stored in the folder."""

    is_quarantined: bool = False
    """Flag that marks the folder as quarantined if true."""

    def get_folder_name(self) -> str:
        """Returns the item_name of the folder."""
        return self.item_name

    def get_folder_size(self) -> float:
        """Returns the item_size of the folder."""
        return self.item_size

    def get_files(self) -> List[FileSystemFile]:
        """Returns the list of files the folder contains."""
        return self.files

    def get_file(self, file_id: str) -> FileSystemFile:
        """Return a FileSystemFile with the matching id."""
        return next((f for f in self.files if f.uuid == file_id), None)

    def add_file(self, file: FileSystemFile):
        """Adds a file to the folder list."""
        self.item_size += file.get_file_size()

        # add to list
        self.files.append(file)

    def remove_file(self, file: Optional[FileSystemFile]):
        """
        Removes a file from the folder list.

        The method can take a FileSystemFile object or a file id.

        :param: file: The file to remove
        :type: Optional[FileSystemFile]
        """
        self.files.remove(file)

        # remove folder size from folder
        self.item_size -= file.get_file_size()

    def get_folder_size(self) -> float:
        """Returns a sum of all file sizes in the files list."""
        return sum([file.get_file_size() for file in self.files])

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
