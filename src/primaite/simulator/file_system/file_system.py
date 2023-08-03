from typing import Dict, List, Optional

from primaite.simulator.core import SimComponent
from primaite.simulator.file_system.file_system_file import FileSystemFile
from primaite.simulator.file_system.file_system_file_type import FileSystemFileType
from primaite.simulator.file_system.file_system_folder import FileSystemFolder


class FileSystem(SimComponent):
    """Class that contains all the simulation File System."""

    folders: List[FileSystemFolder] = []
    """List containing all the folders in the file system."""

    def describe_state(self) -> Dict:
        """
        Get the current state of the FileSystem as a dict.

        :return: A dict containing the current state of the FileSystemFile.
        """
        pass

    def get_folders(self) -> List[FileSystemFolder]:
        """Returns the list of folders."""
        return self.folders

    def create_file(self, file_size: float, folder_uuid: Optional[str] = None) -> FileSystemFile:
        """
        Creates a FileSystemFile and adds it to the list of files.

        :param: folder_uuid: The uuid of the folder to add the file to
        :type: folder_uuid: str
        """
        file = None
        # if no folder uuid provided, create a folder and add file to it
        if folder_uuid is None:
            folder = FileSystemFolder()

            file = FileSystemFile(item_parent=folder.uuid, file_size=file_size, file_type=FileSystemFileType.TBD)
            folder.add_file(file)
            self.folders.append(folder)
        else:
            # otherwise check for existence and add file
            folder = self.get_folder_by_id(folder_uuid)
            if folder is not None:
                file = FileSystemFile(file_size=file_size, file_type=FileSystemFileType.TBD)
                folder.add_file(file=file)
        return file

    def create_folder(self) -> FileSystemFolder:
        """Creates a FileSystemFolder and adds it to the list of folders."""
        folder = FileSystemFolder(item_parent=None)
        self.folders.append(folder)
        return folder

    def delete_file(self, file_id: str):
        """
        Deletes a file and removes it from the files list.

        :param file_id: The UUID of the file item to delete
        :type file_id: str
        """
        # iterate through folders to delete the item with the matching uuid
        for folder in self.folders:
            folder.remove_file(file_id)

    def delete_folder(self, folder_id: str):
        """
        Deletes a folder, removes it from the folders list and removes any child folders and files.

        :param folder_id: The UUID of the file item to delete
        :type folder_id: str
        """
        self.folders = list(filter(lambda f: (f.uuid != folder_id), self.folders))

    def move_file(self, src_folder_id: str, target_folder_id: str, file_id: str):
        """Moves a file from one folder to another."""
        # check that both folders and the file exists
        src = self.get_folder_by_id(src_folder_id)
        target = self.get_folder_by_id(target_folder_id)

        if src is None:
            raise Exception(f"src folder with UUID {src_folder_id} could not be found")

        if target is None:
            raise Exception(f"src folder with UUID {target_folder_id} could not be found")

        file = src.get_file(file_id=file_id)
        if file is None:
            raise Exception(f"file with UUID {file_id} could not be found")

        # remove file from src
        src.remove_file(file_id)

        # add file to target
        target.add_file(file)

    def copy_file(self, src_folder_id: str, target_folder_id: str, file_id: str):
        """Copies a file from one folder to another."""
        # check that both folders and the file exists
        src = self.get_folder_by_id(src_folder_id)
        target = self.get_folder_by_id(target_folder_id)

        if src is None:
            raise Exception(f"src folder with UUID {src_folder_id} could not be found")

        if target is None:
            raise Exception(f"src folder with UUID {target_folder_id} could not be found")

        file = src.get_file(file_id=file_id)
        if file is None:
            raise Exception(f"file with UUID {file_id} could not be found")

        # add file to target
        target.add_file(file)

    def get_file_by_id(self, file_id: str) -> FileSystemFile:
        """Checks if the file exists in any file system folders."""
        for folder in self.folders:
            file = folder.get_file(file_id=file_id)
            if file is not None:
                return file

    def get_folder_by_id(self, folder_id: str) -> FileSystemFolder:
        """Checks if the folder exists."""
        return next((f for f in self.folders if f.uuid == folder_id), None)
