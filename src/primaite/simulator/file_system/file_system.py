from random import choice
from typing import Dict, Optional

from primaite import getLogger
from primaite.simulator.core import SimComponent
from primaite.simulator.file_system.file_system_file import FileSystemFile
from primaite.simulator.file_system.file_system_file_type import FileSystemFileType
from primaite.simulator.file_system.file_system_folder import FileSystemFolder

_LOGGER = getLogger(__name__)


class FileSystem(SimComponent):
    """Class that contains all the simulation File System."""

    folders: Dict[str, FileSystemFolder] = {}
    """List containing all the folders in the file system."""

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        Please see :py:meth:`primaite.simulator.core.SimComponent.describe_state` for a more detailed explanation.

        :return: Current state of this object and child objects.
        :rtype: Dict
        """
        state = super().describe_state()
        state.update({"folders": {uuid: folder.describe_state() for uuid, folder in self.folders.items()}})
        return state

    def get_folders(self) -> Dict:
        """Returns the list of folders."""
        return self.folders

    def create_file(
        self,
        file_name: str,
        size: Optional[float] = None,
        file_type: Optional[FileSystemFileType] = None,
        folder: Optional[FileSystemFolder] = None,
        folder_uuid: Optional[str] = None,
    ) -> FileSystemFile:
        """
        Creates a FileSystemFile and adds it to the list of files.

        If no size or file_type are provided, one will be chosen randomly.
        If no folder_uuid or folder is provided, a new folder will be created.

        :param: file_name: The file name
        :type: file_name: str

        :param: size: The size the file takes on disk.
        :type: size: Optional[float]

        :param: file_type: The type of the file
        :type: Optional[FileSystemFileType]

        :param: folder: The folder to add the file to
        :type: folder: Optional[FileSystemFolder]

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
            # check if file with name already exists
            if folder.get_file_by_name(file_name):
                raise Exception(f'File with name "{file_name}" already exists.')

            file = FileSystemFile(name=file_name, size=size, file_type=file_type)
            folder.add_file(file=file)
        else:
            # check if a "root" folder exists
            folder = self.get_folder_by_name("root")
            if folder is None:
                # create a root folder
                folder = FileSystemFolder(name="root")

            # add file to root folder
            file = FileSystemFile(name=file_name, size=size, file_type=file_type)
            folder.add_file(file)
            self.folders[folder.uuid] = folder
        return file

    def create_folder(
        self,
        folder_name: str,
    ) -> FileSystemFolder:
        """
        Creates a FileSystemFolder and adds it to the list of folders.

        :param: folder_name: The name of the folder
        :type: folder_name: str
        """
        # check if folder with name already exists
        if self.get_folder_by_name(folder_name):
            raise Exception(f'Folder with name "{folder_name}" already exists.')

        folder = FileSystemFolder(name=folder_name)

        self.folders[folder.uuid] = folder
        return folder

    def delete_file(self, file: Optional[FileSystemFile] = None):
        """
        Deletes a file and removes it from the files list.

        :param file: The file to delete
        :type file: Optional[FileSystemFile]
        """
        # iterate through folders to delete the item with the matching uuid
        for key in self.folders:
            self.get_folder_by_id(key).remove_file(file)

    def delete_folder(self, folder: FileSystemFolder):
        """
        Deletes a folder, removes it from the folders list and removes any child folders and files.

        :param folder: The folder to remove
        :type folder: FileSystemFolder
        """
        if folder is None or not isinstance(folder, FileSystemFolder):
            raise Exception(f"Invalid folder: {folder}")

        if self.folders.get(folder.uuid):
            del self.folders[folder.uuid]
        else:
            _LOGGER.debug(f"File with UUID {folder.uuid} was not found.")

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

        # check if file with name already exists
        if target_folder.get_file_by_name(file.name):
            raise Exception(f'Folder with name "{file.name}" already exists.')

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

        # check if file with name already exists
        if target_folder.get_file_by_name(file.name):
            raise Exception(f'Folder with name "{file.name}" already exists.')

        # add file to target
        target_folder.add_file(file)

    def get_file_by_id(self, file_id: str) -> FileSystemFile:
        """Checks if the file exists in any file system folders."""
        for key in self.folders:
            file = self.folders[key].get_file_by_id(file_id=file_id)
            if file is not None:
                return file

    def get_folder_by_name(self, folder_name: str) -> FileSystemFolder:
        """
        Returns a the first folder with a matching name.

        :return: Returns the first FileSydtemFolder with a matching name
        """
        matching_folder = None
        for key in self.folders:
            if self.folders[key].name == folder_name:
                matching_folder = self.folders[key]
                break
        return matching_folder

    def get_folder_by_id(self, folder_id: str) -> FileSystemFolder:
        """
        Checks if the folder exists.

        :param: folder_id: The id of the folder to find
        :type: folder_id: str
        """
        return self.folders[folder_id]

    def get_random_file_type(self) -> FileSystemFileType:
        """
        Returns a random FileSystemFileTypeEnum.

        :return: A random file type Enum
        """
        return choice(list(FileSystemFileType))
