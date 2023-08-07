from random import choice
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

    def create_file(
        self,
        file_name: str,
        file_size: Optional[float] = None,
        file_type: Optional[FileSystemFileType] = None,
        folder: Optional[FileSystemFolder] = None,
        folder_uuid: Optional[str] = None,
    ) -> FileSystemFile:
        """
        Creates a FileSystemFile and adds it to the list of files.

        If no file_size or file_type are provided, one will be chosen randomly.
        If no folder_uuid or folder is provided, a new folder will be created.

        :param: file_name: The file name
        :type: file_name: str

        :param: file_size: The size the file takes on disk.
        :type: file_size: Optional[float]

        :param: file_type: The type of the file
        :type: Optional[FileSystemFileType]

        :param: folder_uuid: The uuid of the folder to add the file to
        :type: folder_uuid: Optional[str]
        """
        file = None
        folder = None

        if file_type is None:
            file_type = self.get_random_file_type()

        # if no folder uuid provided, create a folder and add file to it
        if folder_uuid is not None:
            # otherwise check for existence and add file
            folder = self.get_folder_by_id(folder_uuid)

        if folder is not None:
            file = FileSystemFile(item_name=file_name, item_size=file_size, file_type=file_type)
            folder.add_file(file=file)
        else:
            # check if a "root" folder exists
            folder = self.get_folder_by_name("root")
            if folder is None:
                # create a root folder
                folder = FileSystemFolder(item_name="root")

            # add file to root folder
            file = FileSystemFile(item_name=file_name, item_size=file_size, file_type=file_type)
            folder.add_file(file)
            self.folders.append(folder)
        return file

    def create_folder(
        self,
        folder_name: str,
    ) -> FileSystemFolder:
        """Creates a FileSystemFolder and adds it to the list of folders."""
        folder = FileSystemFolder(item_name=folder_name)
        self.folders.append(folder)
        return folder

    def delete_file(self, file: Optional[FileSystemFile] = None):
        """
        Deletes a file and removes it from the files list.

        :param file: The file to delete
        :type file: Optional[FileSystemFile]

        :param file_id: The UUID of the file item to delete
        :type file_id: Optional[str]
        """
        # iterate through folders to delete the item with the matching uuid
        for folder in self.folders:
            folder.remove_file(file=file)

    def delete_folder(self, folder: FileSystemFolder):
        """
        Deletes a folder, removes it from the folders list and removes any child folders and files.

        :param folder: The folder to remove
        :type folder: FileSystemFolder
        """
        self.folders.remove(folder)

    def move_file(self, file: FileSystemFile, src_folder: FileSystemFolder, target_folder: FileSystemFolder):
        """
        Moves a file from one folder to another.

        can provide

        :param: file: The file to move
        :type: file: FileSystemFile

        :param: src_folder: The folder where the file is located
        :type: FileSystemFolder

        :param: target_folder: The folder where the file should be moved to
        :type: FileSystemFolder
        """
        # check that the folders exist
        if src_folder is None:
            raise Exception("Source folder not provided")

        if target_folder is None:
            raise Exception("Target folder not provided")

        if file is None:
            raise Exception("File to be moved is None")

        # remove file from src
        src_folder.remove_file(file)

        # add file to target
        target_folder.add_file(file)

    def copy_file(self, file: FileSystemFile, src_folder: FileSystemFolder, target_folder: FileSystemFolder):
        """
        Copies a file from one folder to another.

        can provide

        :param: file: The file to move
        :type: file: FileSystemFile

        :param: src_folder: The folder where the file is located
        :type: FileSystemFolder

        :param: target_folder: The folder where the file should be moved to
        :type: FileSystemFolder
        """
        if src_folder is None:
            raise Exception("Source folder not provided")

        if target_folder is None:
            raise Exception("Target folder not provided")

        if file is None:
            raise Exception("File to be moved is None")

        # add file to target
        target_folder.add_file(file)

    def get_file_by_id(self, file_id: str) -> FileSystemFile:
        """Checks if the file exists in any file system folders."""
        for folder in self.folders:
            file = folder.get_file(file_id=file_id)
            if file is not None:
                return file

    def get_folder_by_name(self, folder_name: str) -> FileSystemFolder:
        """
        Returns a the first folder with a matching name.

        :return: Returns the first FileSydtemFolder with a matching name
        """
        return next((f for f in self.folders if f.get_folder_name() == folder_name), None)

    def get_folder_by_id(self, folder_id: str) -> FileSystemFolder:
        """Checks if the folder exists."""
        return next((f for f in self.folders if f.uuid == folder_id), None)

    def get_random_file_type(self) -> FileSystemFileType:
        """Returns a random FileSystemFileTypeEnum."""
        return choice(list(FileSystemFileType))
