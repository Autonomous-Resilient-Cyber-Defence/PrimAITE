from __future__ import annotations

import shutil
from pathlib import Path
from typing import Dict, Optional

from prettytable import MARKDOWN, PrettyTable

from primaite import getLogger
from primaite.simulator.core import RequestManager, RequestType, SimComponent
from primaite.simulator.file_system.file import File
from primaite.simulator.file_system.file_type import FileType
from primaite.simulator.file_system.folder import Folder
from primaite.simulator.system.core.sys_log import SysLog

_LOGGER = getLogger(__name__)


class FileSystem(SimComponent):
    """Class that contains all the simulation File System."""

    folders: Dict[str, Folder] = {}
    "List containing all the folders in the file system."
    deleted_folders: Dict[str, Folder] = {}
    "List containing all the folders that have been deleted."
    _folders_by_name: Dict[str, Folder] = {}
    sys_log: SysLog
    "Instance of SysLog used to create system logs."
    sim_root: Path
    "Root path of the simulation."

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

    ###############################################################
    # Folder methods
    ###############################################################
    def create_folder(self, folder_name: str) -> Folder:
        """
        Creates a Folder and adds it to the list of folders.

        :param folder_name: The name of the folder.
        """
        # check if folder with name already exists
        if self.get_folder(folder_name):
            raise Exception(f"Cannot create folder as it already exists: {folder_name}")

        folder = Folder(name=folder_name, sys_log=self.sys_log)

        self.folders[folder.uuid] = folder
        self._folders_by_name[folder.name] = folder
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

            # add to deleted list
            folder.remove_all_files()

            self.deleted_folders[folder.uuid] = folder
        else:
            _LOGGER.debug(f"Cannot delete folder as it does not exist: {folder_name}")

    def delete_folder_by_id(self, folder_uuid: str):
        """
        Deletes a folder via its uuid.

        :param: folder_uuid: UUID of the folder to delete
        """
        folder = self.get_folder_by_id(folder_uuid=folder_uuid)
        self.delete_folder(folder_name=folder.name)

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

    ###############################################################
    # File methods
    ###############################################################

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
            folder_id=folder.uuid,
            folder_name=folder.name,
            real=real,
            sim_path=self.sim_root if real else None,
            sim_root=self.sim_root,
            sys_log=self.sys_log,
        )
        folder.add_file(file)
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
                file.sim_path = file.sim_root / file.path
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
            # check that dest folder exists
            dst_folder = self.get_folder(folder_name=dst_folder_name)
            if not dst_folder:
                # create dest folder
                dst_folder = self.create_folder(dst_folder_name)

            file_copy = File(
                folder_id=dst_folder.uuid,
                folder_name=dst_folder.name,
                **file.model_dump(exclude={"uuid", "folder_id", "folder_name", "sim_path"}),
            )
            dst_folder.add_file(file_copy)

            if file.real:
                file_copy.sim_path.parent.mkdir(exist_ok=True)
                shutil.copy2(file.sim_path, file_copy.sim_path)
        else:
            self.sys_log.error(f"Unable to copy file. {src_file_name} does not exist.")

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        :return: Current state of this object and child objects.
        """
        state = super().describe_state()
        state["folders"] = {folder.name: folder.describe_state() for folder in self.folders.values()}
        return state

    def apply_timestep(self, timestep: int) -> None:
        """Apply time step to FileSystem and its child folders and files."""
        super().apply_timestep(timestep=timestep)

        # apply timestep to folders
        for folder_id in self.folders:
            self.folders[folder_id].apply_timestep(timestep=timestep)

    def scan(self, instant_scan: bool = False):
        """
        Scan all the folders (and child files) in the file system.

        :param: instant_scan: If True, the scan is completed instantly and ignores scan duration. Default False.
        """
        for folder_id in self.folders:
            self.folders[folder_id].scan(instant_scan=instant_scan)

    def reveal_to_red(self, instant_scan: bool = False):
        """
        Reveals all the folders (and child files) in the file system to the red agent.

        :param: instant_scan: If True, the scan is completed instantly and ignores scan duration. Default False.
        """
        for folder_id in self.folders:
            self.folders[folder_id].reveal_to_red(instant_scan=instant_scan)

    def restore_folder(self, folder_id: str):
        """TODO."""
        pass

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
