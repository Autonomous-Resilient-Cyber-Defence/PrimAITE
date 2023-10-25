from __future__ import annotations

import hashlib
import json
import math
import os.path
import shutil
from abc import abstractmethod
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

from prettytable import MARKDOWN, PrettyTable

from primaite import getLogger
from primaite.simulator.core import RequestManager, RequestType, SimComponent
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
    """Health status for folders and files."""

    GOOD = 1
    """File/Folder is OK."""

    COMPROMISED = 2
    """File/Folder is quarantined."""

    CORRUPT = 3
    """File/Folder is corrupted."""

    RESTORING = 4
    """File/Folder is in the process of being restored."""

    REPAIRING = 5
    """File/Folder is in the process of being repaired."""


class FileSystemItemABC(SimComponent):
    """
    Abstract base class for file system items used in the file system simulation.

    :ivar name: The name of the FileSystemItemABC.
    """

    name: str
    "The name of the FileSystemItemABC."

    health_status: FileSystemItemHealthStatus = FileSystemItemHealthStatus.GOOD
    "Actual status of the current FileSystemItem"

    visible_health_status: FileSystemItemHealthStatus = FileSystemItemHealthStatus.GOOD
    "Visible status of the current FileSystemItem"

    previous_hash: Optional[str] = None
    "Hash of the file contents or the description state"

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        :return: Current state of this object and child objects.
        """
        state = super().describe_state()
        state["name"] = self.name
        state["health_status"] = self.health_status.value
        state["visible_health_status"] = self.visible_health_status.value
        state["previous_hash"] = self.previous_hash
        return state

    def _init_request_manager(self) -> RequestManager:
        rm = super()._init_request_manager()

        rm.add_request(name="scan", request_type=RequestType(func=lambda request, context: self.scan()))
        rm.add_request(name="checkhash", request_type=RequestType(func=lambda request, context: self.check_hash()))
        rm.add_request(name="repair", request_type=RequestType(func=lambda request, context: self.repair()))
        rm.add_request(name="restore", request_type=RequestType(func=lambda request, context: self.restore()))

        rm.add_request(name="corrupt", request_type=RequestType(func=lambda request, context: self.corrupt()))

        return rm

    @property
    def size_str(self) -> str:
        """
        Get the file size in a human-readable string format.

        This property makes use of the :func:`convert_size` function to convert the `self.size` attribute to a string
        that is easier to read and understand.

        :return: The human-readable string representation of the file size.
        """
        return convert_size(self.size)

    @abstractmethod
    def check_hash(self) -> bool:
        """
        Checks the has of the file to detect any changes.

        For current implementation, any change in file hash means it is compromised.

        Return False if corruption is detected, otherwise True
        """
        pass

    @abstractmethod
    def repair(self) -> bool:
        """
        Repair the FileSystemItem.

        True if successfully repaired. False otherwise.
        """
        pass

    @abstractmethod
    def corrupt(self) -> bool:
        """
        Corrupt the FileSystemItem.

        True if successfully corrupted. False otherwise.
        """
        pass

    def restore(self) -> None:
        """Restore the file/folder to the state before it got ruined."""
        pass


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

    def _init_request_manager(self) -> RequestManager:
        rm = super()._init_request_manager()

        rm.add_request(
            name="delete",
            request_type=RequestType(func=lambda request, context: self.delete_folder_by_id(folder_uuid=request[0])),
        )

        self._folder_request_manager = RequestManager()
        rm.add_request("folder", RequestType(func=self._folder_request_manager))

        self._file_request_manager = RequestManager()
        rm.add_request("file", RequestType(func=self._file_request_manager))

        return rm

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
        self._folder_request_manager.add_request(
            name=folder.uuid, request_type=RequestType(func=folder._request_manager)
        )
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
            # remove from folder list
            self.folders.pop(folder.uuid)
            self._folders_by_name.pop(folder.name)
            self.sys_log.info(f"Deleted folder /{folder.name} and its contents")
            self._folder_request_manager.remove_request(folder.uuid)
            folder.remove_all_files()

        else:
            _LOGGER.debug(f"Cannot delete folder as it does not exist: {folder_name}")

    def delete_folder_by_id(self, folder_uuid: str):
        """
        Deletes a folder via its uuid.

        :param: folder_uuid: UUID of the folder to delete
        """
        folder = self.get_folder_by_id(folder_uuid=folder_uuid)
        self.delete_folder(folder_name=folder.name)

    def restore_folder(self, folder_id: str):
        """TODO."""
        pass

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
        self._file_request_manager.add_request(name=file.uuid, request_type=RequestType(func=file._request_manager))
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
        self.sys_log.info(f"file not found /{folder_name}/{file_name}")

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
                self._file_request_manager.remove_request(file.uuid)
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

    def restore_file(self, folder_id: str, file_id: str):
        """
        Restore a file.

        Checks the current file's status and applies the correct fix for the file.

        :param: folder_id: id of the folder where the file is stored
        :type: folder_id: str

        :param: folder_id: id of the file to restore
        :type: folder_id: str
        """
        pass

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

        :param: folder_uuid: The folder uuid.
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

    scan_duration: int = -1
    "How many timesteps to complete a scan."

    def _init_request_manager(self) -> RequestManager:
        rm = super()._init_request_manager()
        rm.add_request(
            name="delete",
            request_type=RequestType(func=lambda request, context: self.remove_file_by_id(file_uuid=request[0])),
        )
        return rm

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        :return: Current state of this object and child objects.
        """
        state = super().describe_state()
        state["files"] = {file.name: file.describe_state() for uuid, file in self.files.items()}
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

    def apply_timestep(self, timestep: int):
        """
        Apply a single timestep of simulation dynamics to this service.

        In this instance, if any multi-timestep processes are currently occurring (such as scanning),
        then they are brought one step closer to being finished.

        :param timestep: The current timestep number. (Amount of time since simulation episode began)
        :type timestep: int
        """
        super().apply_timestep(timestep=timestep)

        # scan files each timestep
        if self.scan_duration > -1:
            # scan one file per timestep
            file = self.get_file_by_id(file_uuid=list(self.files)[self.scan_duration - 1])
            file.scan()
            if file.visible_health_status == FileSystemItemHealthStatus.CORRUPT:
                self.visible_health_status = FileSystemItemHealthStatus.CORRUPT
            self.scan_duration -= 1

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

        :param: file_uuid: The file uuid.
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

    def remove_file_by_id(self, file_uuid: str):
        """
        Remove a file using id.

        :param: file_uuid: The UUID of the file to remove.
        """
        file = self.get_file_by_id(file_uuid=file_uuid)
        self.remove_file(file=file)

    def remove_all_files(self):
        """Removes all the files in the folder."""
        self.files = {}
        self._files_by_name = {}

    def restore_file(self, file: Optional[File]):
        """
        Restores a file.

        The method can take a File object or a file id.

        :param file: The file to remove
        """
        pass

    def quarantine(self):
        """Quarantines the File System Folder."""
        pass

    def unquarantine(self):
        """Unquarantine of the File System Folder."""
        pass

    def quarantine_status(self) -> bool:
        """Returns true if the folder is being quarantined."""
        pass

    def scan(self) -> None:
        """Update Folder visible status."""
        if self.scan_duration <= -1:
            # scan one file per timestep
            self.scan_duration = len(self.files)
            self.fs.sys_log.info(f"Scanning folder {self.name} (id: {self.uuid})")
        else:
            # scan already in progress
            self.fs.sys_log.info(f"Scan is already in progress {self.name} (id: {self.uuid})")

    def check_hash(self) -> bool:
        """
        Runs a :func:`check_hash` on all files in the folder.

        If a file under the folder is corrupted, the whole folder is considered corrupted.

        TODO: For now this will just iterate through the files and run :func:`check_hash` and ignores
        any other changes to the folder

        Return False if corruption is detected, otherwise True
        """
        super().check_hash()

        # iterate through the files and run a check hash
        no_corrupted_files = True

        for file_id in self.files:
            file = self.get_file_by_id(file_uuid=file_id)
            no_corrupted_files = file.check_hash()

        # if one file in the folder is corrupted, set the folder status to corrupted
        if not no_corrupted_files:
            self.corrupt()

        self.fs.sys_log.info(f"Checking hash of folder {self.name} (id: {self.uuid})")

        return no_corrupted_files

    def repair(self) -> bool:
        """Repair a corrupted Folder by setting the folder and containing files status to FileSystemItemStatus.GOOD."""
        super().repair()

        repaired = False

        # iterate through the files in the folder
        for file_id in self.files:
            file = self.get_file_by_id(file_uuid=file_id)
            repaired = file.repair()

        # set file status to good if corrupt
        if self.health_status == FileSystemItemHealthStatus.CORRUPT:
            self.health_status = FileSystemItemHealthStatus.GOOD
            repaired = True

        self.fs.sys_log.info(f"Repaired folder {self.name} (id: {self.uuid})")
        return repaired

    def restore(self) -> None:
        """TODO."""
        pass

    def corrupt(self) -> bool:
        """Corrupt a File by setting the folder and containing files status to FileSystemItemStatus.CORRUPT."""
        super().corrupt()

        corrupted = False

        # iterate through the files in the folder
        for file_id in self.files:
            file = self.get_file_by_id(file_uuid=file_id)
            corrupted = file.corrupt()

        # set file status to corrupt if good
        if self.health_status == FileSystemItemHealthStatus.GOOD:
            self.health_status = FileSystemItemHealthStatus.CORRUPT
            corrupted = True

        self.fs.sys_log.info(f"Corrupted folder {self.name} (id: {self.uuid})")
        return corrupted


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

    def scan(self) -> None:
        """Updates the visible statuses of the file."""
        path = self.folder.name + "/" + self.name
        self.folder.fs.sys_log.info(f"Scanning file {self.sim_path if self.sim_path else path}")
        self.visible_health_status = self.health_status

    def check_hash(self) -> bool:
        """
        Check if the file has been changed.

        If changed, the file is considered corrupted.

        Return False if corruption is detected, otherwise True
        """
        current_hash = None

        # if file is real, read the file contents
        if self.real:
            with open(self.sim_path, "rb") as f:
                file_hash = hashlib.blake2b()
                while chunk := f.read(8192):
                    file_hash.update(chunk)

            current_hash = file_hash.hexdigest()
        else:
            # otherwise get describe_state dict and hash that
            current_hash = hashlib.blake2b(json.dumps(self.describe_state(), sort_keys=True).encode()).hexdigest()

        # if the previous hash is None, set the current hash to previous
        if self.previous_hash is None:
            self.previous_hash = current_hash

        # if the previous hash and current hash do not match, mark file as corrupted
        if self.previous_hash is not current_hash:
            self.corrupt()
            return False

        return True

    def repair(self) -> bool:
        """Repair a corrupted File by setting the status to FileSystemItemStatus.GOOD."""
        super().repair()

        # set file status to good if corrupt
        if self.health_status == FileSystemItemHealthStatus.CORRUPT:
            self.health_status = FileSystemItemHealthStatus.GOOD

        path = self.folder.name + "/" + self.name
        self.folder.fs.sys_log.info(f"Repaired file {self.sim_path if self.sim_path else path}")
        return True

    def restore(self) -> None:
        """Restore a corrupted File by setting the status to FileSystemItemStatus.GOOD."""
        pass

    def corrupt(self) -> bool:
        """Corrupt a File by setting the status to FileSystemItemStatus.CORRUPT."""
        super().corrupt()

        corrupted = False

        # set file status to good if corrupt
        if self.health_status == FileSystemItemHealthStatus.GOOD:
            self.health_status = FileSystemItemHealthStatus.CORRUPT
            corrupted = True

        path = self.folder.name + "/" + self.name
        self.folder.fs.sys_log.info(f"Corrupted file {self.sim_path if self.sim_path else path}")
        return corrupted
