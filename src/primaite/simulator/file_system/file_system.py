# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from prettytable import MARKDOWN, PrettyTable

from primaite.interface.request import RequestFormat, RequestResponse
from primaite.simulator.core import RequestManager, RequestPermissionValidator, RequestType, SimComponent
from primaite.simulator.file_system.file import File
from primaite.simulator.file_system.file_type import FileType
from primaite.simulator.file_system.folder import Folder
from primaite.simulator.system.core.sys_log import SysLog


class FileSystem(SimComponent):
    """Class that contains all the simulation File System."""

    folders: Dict[str, Folder] = {}
    "List containing all the folders in the file system."
    deleted_folders: Dict[str, Folder] = {}
    "List containing all the folders that have been deleted."
    sys_log: SysLog
    "Instance of SysLog used to create system logs."
    sim_root: Path
    "Root path of the simulation."
    num_file_creations: int = 0
    "Number of file creations in the current step."
    num_file_deletions: int = 0
    "Number of file deletions in the current step."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure a default root folder
        if not self.folders:
            self.create_folder("root")

    def _init_request_manager(self) -> RequestManager:
        """
        Initialise the request manager.

        More information in user guide and docstring for SimComponent._init_request_manager.
        """
        self._folder_exists = FileSystem._FolderExistsValidator(file_system=self)
        self._folder_deleted = FileSystem._FolderNotDeletedValidator(file_system=self)
        self._file_exists = FileSystem._FileExistsValidator(file_system=self)

        rm = super()._init_request_manager()

        self._delete_manager = RequestManager()
        self._delete_manager.add_request(
            name="file",
            request_type=RequestType(
                func=lambda request, context: RequestResponse.from_bool(
                    self.delete_file(folder_name=request[0], file_name=request[1])
                ),
                validator=self._file_exists,
            ),
        )
        self._delete_manager.add_request(
            name="folder",
            request_type=RequestType(
                func=lambda request, context: RequestResponse.from_bool(self.delete_folder(folder_name=request[0])),
                validator=self._folder_exists,
            ),
        )
        rm.add_request(
            name="delete",
            request_type=RequestType(func=self._delete_manager),
        )

        self._create_manager = RequestManager()

        def _create_file_action(request: List[Any], context: Any) -> RequestResponse:
            file = self.create_file(folder_name=request[0], file_name=request[1], force=request[2])
            if not file:
                return RequestResponse.from_bool(False)
            return RequestResponse(
                status="success",
                data={
                    "file_name": file.name,
                    "folder_name": file.folder_name,
                    "file_type": file.file_type.name,
                    "file_size": file.size,
                },
            )

        self._create_manager.add_request(
            name="file",
            request_type=RequestType(func=_create_file_action),
        )

        def _create_folder_action(request: List[Any], context: Any) -> RequestResponse:
            folder = self.create_folder(folder_name=request[0])
            if not folder:
                return RequestResponse.from_bool(False)
            return RequestResponse(status="success", data={"folder_name": folder.name})

        self._create_manager.add_request(
            name="folder",
            request_type=RequestType(func=_create_folder_action),
        )
        rm.add_request(
            name="create",
            request_type=RequestType(func=self._create_manager),
        )

        def _access_file_action(request: List[Any], context: Any) -> RequestResponse:
            file = self.get_file(folder_name=request[0], file_name=request[1])
            if not file:
                return RequestResponse.from_bool(False)

            if self.access_file(folder_name=request[0], file_name=request[1]):
                return RequestResponse(
                    status="success",
                    data={
                        "file_name": file.name,
                        "folder_name": file.folder_name,
                        "file_type": file.file_type.name,
                        "file_size": file.size,
                        "file_status": file.health_status.name,
                    },
                )
            return RequestResponse.from_bool(False)

        rm.add_request(
            name="access",
            request_type=RequestType(func=_access_file_action),
        )

        self._restore_manager = RequestManager()
        self._restore_manager.add_request(
            name="file",
            request_type=RequestType(
                func=lambda request, context: RequestResponse.from_bool(
                    self.restore_file(folder_name=request[0], file_name=request[1])
                )
            ),
        )
        self._restore_manager.add_request(
            name="folder",
            request_type=RequestType(
                func=lambda request, context: RequestResponse.from_bool(self.restore_folder(folder_name=request[0]))
            ),
        )
        rm.add_request(
            name="restore",
            request_type=RequestType(func=self._restore_manager),
        )

        self._folder_request_manager = RequestManager()
        rm.add_request(
            "folder",
            RequestType(func=self._folder_request_manager, validator=self._folder_exists + self._folder_deleted),
        )

        self._file_request_manager = RequestManager()
        rm.add_request("file", RequestType(func=self._file_request_manager, validator=self._file_exists))

        return rm

    @property
    def size(self) -> int:
        """
        Calculate and return the total size of all folders in the file system.

        :return: The sum of the sizes of all folders in the file system.
        """
        return sum(folder.size for folder in self.folders.values())

    def show_num_files(self, markdown: bool = False):
        """
        Prints a table showing a host's number of file creations & deletions.

        :param markdown: Flag indicating if output should be in markdown format.
        """
        headers = ["File creations", "File deletions"]
        table = PrettyTable(headers)
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"{self.sys_log.hostname} Number of Creations & Deletions"
        table.add_row([self.num_file_creations, self.num_file_deletions])
        print(table)

    def show(self, markdown: bool = False, full: bool = False):
        """
        Prints a table of the FileSystem, displaying either just folders or full files.

        :param markdown: Flag indicating if output should be in markdown format.
        :param full: Flag indicating if to show full files.
        """
        headers = ["Folder", "Size", "Health status", "Visible health status", "Deleted"]
        if full:
            headers[0] = "File Path"
        table = PrettyTable(headers)
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"{self.sys_log.hostname} File System"
        folders = {**self.folders, **self.deleted_folders}
        for folder in folders.values():
            if not full:
                table.add_row(
                    [
                        folder.name,
                        folder.size_str,
                        folder.health_status.name,
                        folder.visible_health_status.name,
                        folder.deleted,
                    ]
                )
            else:
                files = {**folder.files, **folder.deleted_files}
                if not files:
                    table.add_row(
                        [
                            folder.name,
                            folder.size_str,
                            folder.health_status.name,
                            folder.visible_health_status.name,
                            folder.deleted,
                        ]
                    )
                else:
                    for file in files.values():
                        table.add_row(
                            [
                                file.path,
                                file.size_str,
                                file.health_status.name,
                                file.visible_health_status.name,
                                file.deleted,
                            ]
                        )
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
        folder = self.get_folder(folder_name)
        if folder:
            self.sys_log.info(f"Cannot create folder as it already exists: {folder_name}")
        else:
            folder = Folder(name=folder_name, sys_log=self.sys_log)
            self._folder_request_manager.add_request(
                name=folder.name, request_type=RequestType(func=folder._request_manager)
            )
        self.folders[folder.uuid] = folder
        return folder

    def delete_folder(self, folder_name: str) -> bool:
        """
        Deletes a folder, removes it from the folders list and removes any child folders and files.

        :param folder_name: The name of the folder.
        """
        if folder_name == "root":
            self.sys_log.error("Cannot delete the root folder.")
            return False
        folder = self.get_folder(folder_name)
        if not folder:
            self.sys_log.error(f"Cannot delete folder as it does not exist: {folder_name}")
            return False

        # set folder to deleted state
        folder.delete()

        # remove from folder list
        self.folders.pop(folder.uuid)

        # add to deleted list
        folder.remove_all_files()

        self.deleted_folders[folder.uuid] = folder
        self.sys_log.warning(f"Deleted folder /{folder.name} and its contents")
        return True

    def delete_folder_by_id(self, folder_uuid: str) -> None:
        """
        Deletes a folder via its uuid.

        :param: folder_uuid: UUID of the folder to delete
        """
        folder = self.get_folder_by_id(folder_uuid=folder_uuid)
        self.delete_folder(folder_name=folder.name)

    def get_folder(self, folder_name: str, include_deleted: bool = False) -> Optional[Folder]:
        """
        Get a folder by its name if it exists.

        :param folder_name: The folder name.
        :return: The matching Folder.
        """
        for folder in self.folders.values():
            if folder.name == folder_name:
                return folder
        if include_deleted:
            for folder in self.deleted_folders.values():
                if folder.name == folder_name:
                    return folder
        return None

    def get_folder_by_id(self, folder_uuid: str, include_deleted: Optional[bool] = False) -> Optional[Folder]:
        """
        Get a folder by its uuid if it exists.

        :param: folder_uuid: The folder uuid.
        :param: include_deleted: If true, the deleted folders will also be checked
        :return: The matching Folder.
        """
        if include_deleted:
            folder = self.deleted_folders.get(folder_uuid)
            if folder:
                return folder

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
        force: Optional[bool] = False,
    ) -> File:
        """
        Creates a File and adds it to the list of files.

        :param file_name: The file name.
        :param size: The size the file takes on disk in bytes.
        :param file_type: The type of the file.
        :param folder_name: The folder to add the file to.
        :param force: Replaces the file if it already exists.
        """
        if folder_name:
            # check if file with name already exists
            folder = self.get_folder(folder_name)
            # If not then create it
            if not folder:
                folder = self.create_folder(folder_name)
        else:
            # Use root folder if folder_name not supplied
            folder = self.get_folder("root")

        file = self.get_file(folder, file_name)
        if file:
            self.sys_log.info(f"Cannot create file {file_name} as it already exists.")
            if force:
                self.sys_log.info(f"Replacing {file_name}")
        else:
            # Create the file and add it to the folder
            file = File(
                name=file_name,
                sim_size=size,
                file_type=file_type,
                folder_id=folder.uuid,
                folder_name=folder.name,
                sim_root=self.sim_root,
                sys_log=self.sys_log,
            )
        folder.add_file(file, force=force)
        self._file_request_manager.add_request(name=file.name, request_type=RequestType(func=file._request_manager))
        # increment file creation
        self.num_file_creations += 1
        return file

    def get_file(self, folder_name: str, file_name: str, include_deleted: Optional[bool] = False) -> Optional[File]:
        """
        Retrieve a file by its name from a specific folder.

        :param folder_name: The name of the folder where the file resides.
        :param file_name: The name of the file to be retrieved, including its extension.
        :return: An instance of File if it exists, otherwise `None`.
        """
        folder = self.get_folder(folder_name, include_deleted=include_deleted)
        if folder:
            return folder.get_file(file_name, include_deleted=include_deleted)
        self.sys_log.warning(f"File not found /{folder_name}/{file_name}")

    def get_file_by_id(
        self, file_uuid: str, folder_uuid: Optional[str] = None, include_deleted: Optional[bool] = False
    ) -> Optional[File]:
        """
        Retrieve a file by its uuid from a specific folder.

        :param: file_uuid: The uuid of the folder where the file resides.
        :param: folder_uuid: The uuid of the file to be retrieved, including its extension.
        :param: include_deleted: If true, the deleted files will also be checked
        :return: An instance of File if it exists, otherwise `None`.
        """
        folder = self.get_folder_by_id(folder_uuid=folder_uuid, include_deleted=include_deleted)

        if folder:
            return folder.get_file_by_id(file_uuid=file_uuid, include_deleted=include_deleted)

        # iterate through every folder looking for file
        file = None

        for folder_id in self.folders:
            folder = self.folders.get(folder_id)
            res = folder.get_file_by_id(file_uuid=file_uuid, include_deleted=True)
            if res:
                file = res

        if include_deleted:
            for folder_id in self.deleted_folders:
                folder = self.deleted_folders.get(folder_id)
                res = folder.get_file_by_id(file_uuid=file_uuid, include_deleted=True)
                if res:
                    file = res

        return file

    def delete_file(self, folder_name: str, file_name: str) -> bool:
        """
        Delete a file by its name from a specific folder.

        :param folder_name: The name of the folder containing the file.
        :param file_name: The name of the file to be deleted, including its extension.
        """
        folder = self.get_folder(folder_name)
        if folder:
            file = folder.get_file(file_name)
            if file:
                # increment file creation
                self.num_file_deletions += 1
                folder.remove_file(file)
                return True
        return False

    def delete_file_by_id(self, folder_uuid: str, file_uuid: str) -> None:
        """
        Deletes a file via its uuid.

        :param: folder_uuid: UUID of the folder the file belongs to
        :param: file_uuid: UUID of the file to delete
        """
        folder = self.get_folder_by_id(folder_uuid=folder_uuid)

        if folder:
            file = folder.get_file_by_id(file_uuid=file_uuid)

            if file:
                self.delete_file(folder_name=folder.name, file_name=file.name)
            else:
                self.sys_log.error(f"Unable to delete file that does not exist. (id: {file_uuid})")

    def move_file(self, src_folder_name: str, src_file_name: str, dst_folder_name: str) -> None:
        """
        Move a file from one folder to another.

        :param src_folder_name: The name of the source folder containing the file.
        :param src_file_name: The name of the file to be moved.
        :param dst_folder_name: The name of the destination folder.
        """
        file = self.get_file(folder_name=src_folder_name, file_name=src_file_name)
        if file:
            # remove file from src
            self.delete_file(folder_name=file.folder_name, file_name=file.name)
            dst_folder = self.get_folder(folder_name=dst_folder_name)
            if not dst_folder:
                dst_folder = self.create_folder(dst_folder_name)
            # add file to dst
            dst_folder.add_file(file)
            self.num_file_creations += 1

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
            self.num_file_creations += 1
            # increment access counter
            file.num_access += 1

            dst_folder.add_file(file_copy, force=True)

        else:
            self.sys_log.error(f"Unable to copy file. {src_file_name} does not exist.")

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        :return: Current state of this object and child objects.
        """
        state = super().describe_state()
        state["folders"] = {folder.name: folder.describe_state() for folder in self.folders.values()}
        state["deleted_folders"] = {folder.name: folder.describe_state() for folder in self.deleted_folders.values()}
        state["num_file_creations"] = self.num_file_creations
        state["num_file_deletions"] = self.num_file_deletions
        return state

    def apply_timestep(self, timestep: int) -> None:
        """Apply time step to FileSystem and its child folders and files."""
        super().apply_timestep(timestep=timestep)

        # apply timestep to folders
        for folder_id in self.folders:
            self.folders[folder_id].apply_timestep(timestep=timestep)

    def pre_timestep(self, timestep: int) -> None:
        """Apply pre-timestep logic."""
        super().pre_timestep(timestep)
        # reset number of file creations
        self.num_file_creations = 0

        # reset number of file deletions
        self.num_file_deletions = 0

        for folder in self.folders.values():
            folder.pre_timestep(timestep)

    ###############################################################
    # Agent actions
    ###############################################################

    def scan(self, instant_scan: bool = False) -> None:
        """
        Scan all the folders (and child files) in the file system.

        :param: instant_scan: If True, the scan is completed instantly and ignores scan duration. Default False.
        """
        for folder_id in self.folders:
            self.folders[folder_id].scan(instant_scan=instant_scan)

    def reveal_to_red(self, instant_scan: bool = False) -> None:
        """
        Reveals all the folders (and child files) in the file system to the red agent.

        :param: instant_scan: If True, the scan is completed instantly and ignores scan duration. Default False.
        """
        for folder_id in self.folders:
            self.folders[folder_id].reveal_to_red(instant_scan=instant_scan)

    def restore_folder(self, folder_name: str) -> bool:
        """
        Restore a folder.

        Checks the current folder's status and applies the correct fix for the folder.

        :param: folder_name: name of the folder to restore
        :type: folder_uuid: str
        """
        folder = self.get_folder(folder_name=folder_name, include_deleted=True)

        if folder is None:
            self.sys_log.error(f"Unable to restore folder {folder_name}. Folder is not in deleted folder list.")
            return False

        self.deleted_folders.pop(folder.uuid, None)
        folder.restore()
        self.folders[folder.uuid] = folder
        return True

    def restore_file(self, folder_name: str, file_name: str) -> bool:
        """
        Restore a file.

        Checks the current file's status and applies the correct fix for the file.

        :param: folder_name: name of the folder where the file is stored
        :type: folder_name: str

        :param: file_name: name of the file to restore
        :type: file_name: str
        """
        folder = self.get_folder(folder_name=folder_name)
        if not folder:
            self.sys_log.error(f"Cannot restore file {file_name} in folder {folder_name} as the folder does not exist.")
            return False

        file = folder.get_file(file_name=file_name, include_deleted=True)

        if not file:
            msg = f"Unable to restore file {file_name}. File was not found."
            self.sys_log.error(msg)
            return False

        return folder.restore_file(file_name=file_name)

    def access_file(self, folder_name: str, file_name: str) -> bool:
        """
        Access a file.

        Used by agents to simulate a file being accessed.

        :param: folder_name: name of the folder where the file is stored
        :type: folder_name: str

        :param: file_name: name of the file to access
        :type: file_name: str
        """
        folder = self.get_folder(folder_name=folder_name)

        if folder:
            file = folder.get_file(file_name=file_name)

            if file:
                file.num_access += 1
                return True
            else:
                self.sys_log.error(f"Unable to access file that does not exist. (file name: {file_name})")

        return False

    class _FolderExistsValidator(RequestPermissionValidator):
        """
        When requests come in, this validator will only let them through if the Folder exists.

        Actions cannot be performed on a non-existent folder.
        """

        file_system: FileSystem
        """Save a reference to the FileSystem instance."""

        def __call__(self, request: RequestFormat, context: Dict) -> bool:
            """Returns True if folder exists."""
            return self.file_system.get_folder(folder_name=request[0]) is not None

        @property
        def fail_message(self) -> str:
            """Message that is reported when a request is rejected by this validator."""
            return "Cannot perform request on folder because it does not exist"

    class _FolderNotDeletedValidator(RequestPermissionValidator):
        """
        When requests come in, this validator will only let them through if the Folder has not been deleted.

        Actions cannot be performed on a deleted folder.
        """

        file_system: FileSystem
        """Save a reference to the FileSystem instance."""

        def __call__(self, request: RequestFormat, context: Dict) -> bool:
            """Returns True if folder exists and is not deleted."""
            # get folder
            folder = self.file_system.get_folder(folder_name=request[0], include_deleted=True)
            return folder is not None and not folder.deleted

        @property
        def fail_message(self) -> str:
            """Message that is reported when a request is rejected by this validator."""
            return "Cannot perform request on folder because it is deleted."

    class _FileExistsValidator(RequestPermissionValidator):
        """
        When requests come in, this validator will only let them through if the File exists.

        Actions cannot be performed on a non-existent file.
        """

        file_system: FileSystem
        """Save a reference to the FileSystem instance."""

        def __call__(self, request: RequestFormat, context: Dict) -> bool:
            """Returns True if file exists."""
            return self.file_system.get_file(folder_name=request[0], file_name=request[1]) is not None

        @property
        def fail_message(self) -> str:
            """Message that is reported when a request is rejected by this validator."""
            return (
                f"Cannot perform request on application '{self.application.name}' because it is not in the "
                f"{self.state.name} state."
            )
