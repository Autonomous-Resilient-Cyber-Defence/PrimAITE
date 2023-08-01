from typing import Dict, List, Union

from primaite.simulator.core import SimComponent
from primaite.simulator.file_system.file_system_file import FileSystemFile
from primaite.simulator.file_system.file_system_folder import FileSystemFolder


class FileSystem(SimComponent):
    """Class that contains all the simulation File System."""

    files: List[FileSystemFile]
    """List containing all the files in the file system."""

    folders: List[FileSystemFolder]
    """List containing all the folders in the file system."""

    def describe_state(self) -> Dict:
        """
        Get the current state of the FileSystem as a dict.

        :return: A dict containing the current state of the FileSystemFile.
        """
        pass

    def create_file(self):
        """Creates a FileSystemFile and adds it to the list of files."""
        pass

    def create_folder(self):
        """Creates a FileSystemFolder and adds it to the list of folders."""
        pass

    def delete_file(self, file_item: str):
        """
        Deletes a file and removes it from the files list.

        :param file_item: The UUID of the file item to delete
        :type file_item: str
        """
        self.files = list(filter(lambda x: (x.get_item_uuid() != file_item), self.files))

    def delete_folder(self, file_item: str):
        """
        Deletes a folder, removes it frdom the folders list and removes any child folders and files.

        :param file_item: The UUID of the file item to delete
        :type file_item: str
        """
        self.files = list(filter(lambda x: (x.get_item_parent() != file_item), self.files))
        self.folders = list(filter(lambda x: (x.get_item_uuid() != file_item), self.folders))

    def move_file_item(self, file_item: str, target_directory: str):
        """
        Check to see if the file_item and target_directory exists then moves the item by changing its parent item uuid.

        :param file_item: The UUID of the file item to move
        :type file_item: str

        :param target_directory: The UUID of the directory the item should be moved into
        :type target_directory: str
        """
        item = self._file_item_exists(file_item)
        if item and any(f for f in self.folders if f.get_item_uuid() == target_directory):
            item.move(target_directory)

    def _file_item_exists(self, file_item_uuid: str) -> Union[FileSystemFile, FileSystemFolder, None]:
        """Returns true if the file or folder UUID exists."""
        item = next((x for x in self.files if x.get_item_uuid() == file_item_uuid), None)
        if item:
            return item

        next((x for x in self.folders if x.get_item_uuid() == file_item_uuid), None)

        if item:
            return item

        raise Exception(f"No file or folder found with id: {file_item_uuid}")
