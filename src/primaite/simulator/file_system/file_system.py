from __future__ import annotations

import math
import os.path
import shutil
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

from prettytable import MARKDOWN, PrettyTable

from primaite import getLogger
from primaite.simulator.core import Action, ActionManager, SimComponent
from primaite.simulator.file_system.file_type import FileType, get_file_type_from_extension
from primaite.simulator.system.core.sys_log import SysLog

_LOGGER = getLogger(__name__)


def convert_size(size_bytes: int) -> str:
    """
    Convert a file size from bytes to a string with a more human-readable format.

    This function takes the size of a file in bytes and converts it to a string representation with appropriate size
    units (B, KB, MB, GB, etc.).

    :param size_bytes: The size of the file in bytes.
    :return: The human-readable string representation of the file size.
    """
    if size_bytes == 0:
        return "0 B"

    # Tuple of size units starting from Bytes up to Yottabytes
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")

    # Calculate the index (i) that will be used to select the appropriate size unit from size_name
    i = int(math.floor(math.log(size_bytes, 1024)))

    # Calculate the adjusted size value (s) in terms of the new size unit
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)

    return f"{s} {size_name[i]}"


class FileSystemItemHealthStatus(Enum):
    GOOD = 1
    COMPROMISED = 2
    CORRUPT = 3
    RESTORING = 4
    REPAIRING = 5


class FileSystemItemABC(SimComponent):
    """
    Abstract base class for file system items used in the file system simulation.

    :ivar name: The name of the FileSystemItemABC.
    """

    name: str
    "The name of the FileSystemItemABC."
    health_status: FileSystemItemHealthStatus = FileSystemItemHealthStatus.GOOD

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        :return: Current state of this object and child objects.
        """
        state = super().describe_state()
        state.update({"name": self.name, "health_status": self.health_status.value})
        return state

    @property
    def size_str(self) -> str:
        """
        Get the file size in a human-readable string format.

        This property makes use of the :func:`convert_size` function to convert the `self.size` attribute to a string
        that is easier to read and understand.

        :return: The human-readable string representation of the file size.
        """
        return convert_size(self.size)


class FileSystem(SimComponent):
    """Class that contains all the simulation File System."""

    folders: Dict[str, Folder] = {}
    "List containing all the folders in the file system."
    _folders_by_name: Dict[str, Folder] = {}
    sys_log: SysLog
    sim_root: Path

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure a default root folder
        if not self.folders:
            self.create_folder("root")

    def _init_action_manager(self) -> ActionManager:
        am = super()._init_action_manager()

        self._folder_action_manager = ActionManager()
        am.add_action("folder", Action(func=self._folder_action_manager))

        self._file_action_manager = ActionManager()
        am.add_action("file", Action(func=self._file_action_manager))

        return am

    @property
    def size(self) -> int:
        """
        Calculate and return the total size of all folders in the file system.

        :return: The sum of the sizes of all folders in the file system.
        """
        return sum(folder.size for folder in self.folders.values())

    def show(self, markdown: bool = False, full: bool = False):
        """
        Prints a table of the FileSystem, displaying either just folders or full files.

        :param markdown: Flag indicating if output should be in markdown format.
        :param full: Flag indicating if to show full files.
        """
        headers = ["Folder", "Size"]
        if full:
            headers[0] = "File Path"
        table = PrettyTable(headers)
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"{self.sys_log.hostname} File System"
        for folder in self.folders.values():
            if not full:
                table.add_row([folder.name, folder.size_str])
            else:
                for file in folder.files.values():
                    table.add_row([file.path, file.size_str])
        if full:
            print(table.get_string(sortby="File Path"))
        else:
            print(table.get_string(sortby="Folder"))

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        :return: Current state of this object and child objects.
        """
        state = super().describe_state()
        state["folders"] = {folder.name: folder.describe_state() for folder in self.folders.values()}
        return state

    def create_folder(self, folder_name: str) -> Folder:
        """
        Creates a Folder and adds it to the list of folders.

        :param folder_name: The name of the folder.
        """
        # check if folder with name already exists
        if self.get_folder(folder_name):
            raise Exception(f"Cannot create folder as it already exists: {folder_name}")

        folder = Folder(name=folder_name, fs=self)

        self.folders[folder.uuid] = folder
        self._folders_by_name[folder.name] = folder
        self.sys_log.info(f"Created folder /{folder.name}")
        self._folder_action_manager.add_action(folder.uuid, Action(func=folder._action_manager))
        return folder

    def delete_folder(self, folder_name: str):
        """
        Deletes a folder, removes it from the folders list and removes any child folders and files.

        :param folder_name: The name of the folder.
        """
        if folder_name == "root":
            self.sys_log.warning("Cannot delete the root folder.")
            return
        folder = self._folders_by_name.get(folder_name)
        if folder:
            for file in folder.files.values():
                self.delete_file(file)
            self.folders.pop(folder.uuid)
            self._folders_by_name.pop(folder.name)
            self.sys_log.info(f"Deleted folder /{folder.name} and its contents")
            self._folder_action_manager.remove_action(folder.uuid)
        else:
            _LOGGER.debug(f"Cannot delete folder as it does not exist: {folder_name}")

    def create_file(
        self,
        file_name: str,
        size: Optional[int] = None,
        file_type: Optional[FileType] = None,
        folder_name: Optional[str] = None,
        real: bool = False,
    ) -> File:
        """
        Creates a File and adds it to the list of files.

        :param file_name: The file name.
        :param size: The size the file takes on disk in bytes.
        :param file_type: The type of the file.
        :param folder_name: The folder to add the file to.
        :param real: "Indicates whether the File is actually a real file in the Node sim fs output."
        """
        if folder_name:
            # check if file with name already exists
            folder = self._folders_by_name.get(folder_name)
            # If not then create it
            if not folder:
                folder = self.create_folder(folder_name)
        else:
            # Use root folder if folder_name not supplied
            folder = self._folders_by_name["root"]

        # Create the file and add it to the folder
        file = File(
            name=file_name,
            sim_size=size,
            file_type=file_type,
            folder=folder,
            real=real,
            sim_path=self.sim_root if real else None,
        )
        folder.add_file(file)
        self.sys_log.info(f"Created file /{file.path}")
        self._file_action_manager.add_action(file.uuid, Action(func=file._action_manager))
        return file

    def get_file(self, folder_name: str, file_name: str) -> Optional[File]:
        """
        Retrieve a file by its name from a specific folder.

        :param folder_name: The name of the folder where the file resides.
        :param file_name: The name of the file to be retrieved, including its extension.
        :return: An instance of File if it exists, otherwise `None`.
        """
        folder = self.get_folder(folder_name)
        if folder:
            return folder.get_file(file_name)
        self.fs.sys_log.info(f"file not found /{folder_name}/{file_name}")

    def delete_file(self, folder_name: str, file_name: str):
        """
        Delete a file by its name from a specific folder.

        :param folder_name: The name of the folder containing the file.
        :param file_name: The name of the file to be deleted, including its extension.
        """
        folder = self.get_folder(folder_name)
        if folder:
            file = folder.get_file(file_name)
            if file:
                folder.remove_file(file)
                self._file_action_manager.remove_action(file.uuid)
                self.sys_log.info(f"Deleted file /{file.path}")

    def move_file(self, src_folder_name: str, src_file_name: str, dst_folder_name: str):
        """
        Move a file from one folder to another.

        :param src_folder_name: The name of the source folder containing the file.
        :param src_file_name: The name of the file to be moved.
        :param dst_folder_name: The name of the destination folder.
        """
        file = self.get_file(folder_name=src_folder_name, file_name=src_file_name)
        if file:
            src_folder = file.folder

            # remove file from src
            src_folder.remove_file(file)
            dst_folder = self.get_folder(folder_name=dst_folder_name)
            if not dst_folder:
                dst_folder = self.create_folder(dst_folder_name)
            # add file to dst
            dst_folder.add_file(file)
            if file.real:
                old_sim_path = file.sim_path
                file.sim_path = file.folder.fs.sim_root / file.path
                file.sim_path.parent.mkdir(exist_ok=True)
                shutil.move(old_sim_path, file.sim_path)

    def copy_file(self, src_folder_name: str, src_file_name: str, dst_folder_name: str):
        """
        Copy a file from one folder to another.

        :param src_folder_name: The name of the source folder containing the file.
        :param src_file_name: The name of the file to be copied.
        :param dst_folder_name: The name of the destination folder.
        """
        file = self.get_file(folder_name=src_folder_name, file_name=src_file_name)
        if file:
            dst_folder = self.get_folder(folder_name=dst_folder_name)
            if not dst_folder:
                dst_folder = self.create_folder(dst_folder_name)
            new_file = file.make_copy(dst_folder=dst_folder)
            dst_folder.add_file(new_file)
            if file.real:
                new_file.sim_path.parent.mkdir(exist_ok=True)
                shutil.copy2(file.sim_path, new_file.sim_path)

    def get_folder(self, folder_name: str) -> Optional[Folder]:
        """
        Get a folder by its name if it exists.

        :param folder_name: The folder name.
        :return: The matching Folder.
        """
        return self._folders_by_name.get(folder_name)

    def get_folder_by_id(self, folder_uuid: str) -> Optional[Folder]:
        """
        Get a folder by its uuid if it exists.

        :param folder_uuid: The folder uuid.
        :return: The matching Folder.
        """
        return self.folders.get(folder_uuid)


class Folder(FileSystemItemABC):
    """Simulation Folder."""

    fs: FileSystem
    "The FileSystem the Folder is in."
    files: Dict[str, File] = {}
    "Files stored in the folder."
    _files_by_name: Dict[str, File] = {}
    "Files by their name as <file name>.<file type>."
    is_quarantined: bool = False
    "Flag that marks the folder as quarantined if true."

    def _init_action_manager(sekf) -> ActionManager:
        am = super()._init_action_manager()

        am.add_action("scan", Action(func=lambda request, context: ...))  # TODO implement action
        am.add_action("checkhash", Action(func=lambda request, context: ...))  # TODO implement action
        am.add_action("repair", Action(func=lambda request, context: ...))  # TODO implement action
        am.add_action("restore", Action(func=lambda request, context: ...))  # TODO implement action
        am.add_action("delete", Action(func=lambda request, context: ...))  # TODO implement action
        am.add_action("corrupt", Action(func=lambda request, context: ...))  # TODO implement action

        return am

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        :return: Current state of this object and child objects.
        """
        state = super().describe_state()
        state["files"] = {file.name: file.describe_state() for uuid, file in self.files.items()}
        state["is_quarantined"] = self.is_quarantined
        return state

    def show(self, markdown: bool = False):
        """
        Display the contents of the Folder in tabular format.

        :param markdown: Whether to display the table in Markdown format or not. Default is `False`.
        """
        table = PrettyTable(["File", "Size"])
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"{self.fs.sys_log.hostname} File System Folder ({self.name})"
        for file in self.files.values():
            table.add_row([file.name, file.size_str])
        print(table.get_string(sortby="File"))

    @property
    def size(self) -> int:
        """
        Calculate and return the total size of all files in the folder.

        :return: The total size of all files in the folder. If no files exist or all have `None`
            size, returns 0.
        """
        return sum(file.size for file in self.files.values() if file.size is not None)

    def get_file(self, file_name: str) -> Optional[File]:
        """
        Get a file by its name.

        File name must be the filename and prefix, like 'memo.docx'.

        :param file_name: The file name.
        :return: The matching File.
        """
        # TODO: Increment read count?
        return self._files_by_name.get(file_name)

    def get_file_by_id(self, file_uuid: str) -> File:
        """
        Get a file by its uuid.

        :param file_uuid: The file uuid.
        :return: The matching File.
        """
        return self.files.get(file_uuid)

    def add_file(self, file: File):
        """
        Adds a file to the folder.

        :param File file: The File object to be added to the folder.
        :raises Exception: If the provided `file` parameter is None or not an instance of the
            `File` class.
        """
        if file is None or not isinstance(file, File):
            raise Exception(f"Invalid file: {file}")

        # check if file with id already exists in folder
        if file.uuid in self.files:
            _LOGGER.debug(f"File with id {file.uuid} already exists in folder")
        else:
            # add to list
            self.files[file.uuid] = file
            self._files_by_name[file.name] = file
            file.folder = self

    def remove_file(self, file: Optional[File]):
        """
        Removes a file from the folder list.

        The method can take a File object or a file id.

        :param file: The file to remove
        """
        if file is None or not isinstance(file, File):
            raise Exception(f"Invalid file: {file}")

        if self.files.get(file.uuid):
            self.files.pop(file.uuid)
            self._files_by_name.pop(file.name)
        else:
            _LOGGER.debug(f"File with UUID {file.uuid} was not found.")

    def quarantine(self):
        """Quarantines the File System Folder."""
        if not self.is_quarantined:
            self.is_quarantined = True
            self.fs.sys_log.info(f"Quarantined folder ./{self.name}")

    def unquarantine(self):
        """Unquarantine of the File System Folder."""
        if self.is_quarantined:
            self.is_quarantined = False
            self.fs.sys_log.info(f"Quarantined folder ./{self.name}")

    def quarantine_status(self) -> bool:
        """Returns true if the folder is being quarantined."""
        return self.is_quarantined


class File(FileSystemItemABC):
    """
    Class representing a file in the simulation.

    :ivar Folder folder: The folder in which the file resides.
    :ivar FileType file_type: The type of the file.
    :ivar Optional[int] sim_size: The simulated file size.
    :ivar bool real: Indicates if the file is actually a real file in the Node sim fs output.
    :ivar Optional[Path] sim_path: The path if the file is real.
    """

    folder: Folder
    "The Folder the File is in."
    file_type: FileType
    "The type of File."
    sim_size: Optional[int] = None
    "The simulated file size."
    real: bool = False
    "Indicates whether the File is actually a real file in the Node sim fs output."
    sim_path: Optional[Path] = None
    "The Path if real is True."

    def __init__(self, **kwargs):
        """
        Initialise File class.

        :param name: The name of the file.
        :param file_type: The FileType of the file
        :param size: The size of the FileSystemItemABC
        """
        has_extension = "." in kwargs["name"]

        # Attempt to use the file type extension to set/override the FileType
        if has_extension:
            extension = kwargs["name"].split(".")[-1]
            kwargs["file_type"] = get_file_type_from_extension(extension)
        else:
            # If the file name does not have a extension, override file type to FileType.UNKNOWN
            if not kwargs["file_type"]:
                kwargs["file_type"] = FileType.UNKNOWN
            if kwargs["file_type"] != FileType.UNKNOWN:
                kwargs["name"] = f"{kwargs['name']}.{kwargs['file_type'].name.lower()}"

        # set random file size if none provided
        if not kwargs.get("sim_size"):
            kwargs["sim_size"] = kwargs["file_type"].default_size
        super().__init__(**kwargs)
        if self.real:
            self.sim_path = self.folder.fs.sim_root / self.path
            if not self.sim_path.exists():
                self.sim_path.parent.mkdir(exist_ok=True, parents=True)
                with open(self.sim_path, mode="a"):
                    pass

    def _init_action_manager(self) -> ActionManager:
        am = super()._init_action_manager()

        am.add_action("scan", Action(func=lambda request, context: ...))  # TODO implement action
        am.add_action("checkhash", Action(func=lambda request, context: ...))  # TODO implement action
        am.add_action("delete", Action(func=lambda request, context: ...))  # TODO implement action
        am.add_action("repair", Action(func=lambda request, context: ...))  # TODO implement action
        am.add_action("restore", Action(func=lambda request, context: ...))  # TODO implement action
        am.add_action("corrupt", Action(func=lambda request, context: ...))  # TODO implement action

        return am

    def make_copy(self, dst_folder: Folder) -> File:
        """
        Create a copy of the current File object in the given destination folder.

        :param Folder dst_folder: The destination folder for the copied file.
        :return: A new File object that is a copy of the current file.
        """
        return File(folder=dst_folder, **self.model_dump(exclude={"uuid", "folder", "sim_path"}))

    @property
    def path(self) -> str:
        """
        Get the path of the file in the file system.

        :return: The full path of the file.
        """
        return f"{self.folder.name}/{self.name}"

    @property
    def size(self) -> int:
        """
        Get the size of the file in bytes.

        :return: The size of the file in bytes.
        """
        if self.real:
            return os.path.getsize(self.sim_path)
        return self.sim_size

    def describe_state(self) -> Dict:
        """Produce a dictionary describing the current state of this object."""
        state = super().describe_state()
        state["size"] = self.size
        state["file_type"] = self.file_type.name
        return state
