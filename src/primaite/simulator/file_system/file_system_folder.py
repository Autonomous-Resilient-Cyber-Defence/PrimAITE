from typing import Dict

from primaite.simulator.file_system.file_system_item_abc import FileSystemItemABC


class FileSystemFolder(FileSystemItemABC):
    """Simulation FileSystemFolder."""

    _is_quarantined: bool
    """Flag that marks the folder as quarantined if true."""

    def quarantine(self):
        """Quarantines the File System Folder."""
        self._is_quarantined = True

    def end_quarantine(self):
        """Ends the quarantine of the File System Folder."""
        self._is_quarantined = False

    def quarantine_status(self) -> bool:
        """Returns true if the folder is being quarantined."""
        return self._is_quarantined

    def move(self, target_directory: str):
        """
        Changes the parent_item of the file system item.

        Essentially simulates the file system item being moved from folder to folder

        :param target_directory: The UUID of the directory the file system item should be moved to
        :type target_directory: str
        """
        super().move(target_directory)

    def describe_state(self) -> Dict:
        """
        Get the current state of the FileSystemFolder as a dict.

        :return: A dict containing the current state of the FileSystemFile.
        """
        pass
