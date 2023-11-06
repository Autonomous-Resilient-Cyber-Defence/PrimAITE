from __future__ import annotations

from typing import Dict, Optional

from prettytable import MARKDOWN, PrettyTable

from primaite import getLogger
from primaite.simulator.core import RequestManager, RequestType
from primaite.simulator.file_system.file import File
from primaite.simulator.file_system.file_system_item_abc import FileSystemItemABC, FileSystemItemHealthStatus

_LOGGER = getLogger(__name__)


class Folder(FileSystemItemABC):
    """Simulation Folder."""

    files: Dict[str, File] = {}
    "Files stored in the folder."
    _files_by_name: Dict[str, File] = {}
    "Files by their name as <file name>.<file type>."
    deleted_files: Dict[str, File] = {}
    "Files that have been deleted."

    scan_duration: int = 3
    "How many timesteps to complete a scan. Default 3 timesteps"

    scan_countdown: int = 0
    "Time steps needed until scan completion."

    red_scan_duration: int = 3
    "How many timesteps to complete reveal to red scan. Default 3 timesteps"

    red_scan_countdown: int = 0
    "Time steps needed until red scan completion."

    restore_duration: int = 3
    "How many timesteps to complete a restore. Default 3 timesteps"

    restore_countdown: int = 0
    "Time steps needed until restore completion."

    def __init__(self, **kwargs):
        """
        Initialise Folder class.

        :param name: The name of the folder.
        :param sys_log: The SysLog instance to us to create system logs.
        """
        super().__init__(**kwargs)

        self.sys_log.info(f"Created file /{self.name} (id: {self.uuid})")

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
        state["deleted_files"] = {file.name: file.describe_state() for uuid, file in self.deleted_files.items()}
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
        table.title = f"{self.sys_log.hostname} File System Folder ({self.name})"
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
        Apply a single timestep of simulation dynamics to this folder and its files.

        In this instance, if any multi-timestep processes are currently occurring (such as scanning),
        then they are brought one step closer to being finished.

        :param timestep: The current timestep number. (Amount of time since simulation episode began)
        :type timestep: int
        """
        super().apply_timestep(timestep=timestep)

        self._scan_timestep()

        self._reveal_to_red_timestep()

        self._restoring_timestep()

        # apply timestep to files in folder
        for file_id in self.files:
            self.files[file_id].apply_timestep(timestep=timestep)

    def _scan_timestep(self) -> None:
        """Apply the scan action timestep."""
        if self.scan_countdown >= 0:
            self.scan_countdown -= 1

            if self.scan_countdown == 0:
                for file_id in self.files:
                    file = self.get_file_by_id(file_uuid=file_id)
                    file.scan()
                    if file.visible_health_status == FileSystemItemHealthStatus.CORRUPT:
                        self.visible_health_status = FileSystemItemHealthStatus.CORRUPT

    def _reveal_to_red_timestep(self) -> None:
        """Apply reveal to red timestep."""
        if self.red_scan_countdown >= 0:
            self.red_scan_countdown -= 1

            if self.red_scan_countdown == 0:
                self.revealed_to_red = True
                for file_id in self.files:
                    file = self.get_file_by_id(file_uuid=file_id)
                    file.reveal_to_red()

    def _restoring_timestep(self) -> None:
        """Apply restoring timestep."""
        if self.restore_countdown >= 0:
            self.restore_countdown -= 1

            if self.restore_countdown == 0:
                # repair all files
                for file_id in self.files:
                    self.restore_file(file_uuid=file_id)

                deleted_files = self.deleted_files.copy()
                for file_id in deleted_files:
                    self.restore_file(file_uuid=file_id)

                if self.deleted:
                    self.deleted = False
                elif self.health_status in [FileSystemItemHealthStatus.CORRUPT, FileSystemItemHealthStatus.RESTORING]:
                    self.health_status = FileSystemItemHealthStatus.GOOD

    def get_file(self, file_name: str) -> Optional[File]:
        """
        Get a file by its name.

        File name must be the filename and prefix, like 'memo.docx'.

        :param file_name: The file name.
        :return: The matching File.
        """
        # TODO: Increment read count?
        return self._files_by_name.get(file_name)

    def get_file_by_id(self, file_uuid: str, include_deleted: Optional[bool] = False) -> File:
        """
        Get a file by its uuid.

        :param: file_uuid: The file uuid.
        :param: include_deleted: If true, the deleted files will also be checked
        :return: The matching File.
        """
        if include_deleted:
            deleted_file = self.deleted_files.get(file_uuid)

            if deleted_file:
                return deleted_file

        return self.files.get(file_uuid)

    def add_file(self, file: File, force: Optional[bool] = False):
        """
        Adds a file to the folder.

        :param: file: The File object to be added to the folder.
        :param: force: Overwrite file - do not check if uuid or name already exists in folder. Default False.
        :raises Exception: If the provided `file` parameter is None or not an instance of the
            `File` class.
        """
        if file is None or not isinstance(file, File):
            raise Exception(f"Invalid file: {file}")

        # check if file with id or name already exists in folder
        if (force is not True) and file.name in self._files_by_name:
            raise Exception(f"File with name {file.name} already exists in folder")

        if (force is not True) and file.uuid in self.files:
            raise Exception(f"File with uuid {file.uuid} already exists in folder")

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
            self.deleted_files[file.uuid] = file
            file.delete()
            self.sys_log.info(f"Removed file {file.name} (id: {file.uuid})")
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
        for file_id in self.files:
            file = self.files.get(file_id)
            file.delete()
            self.deleted_files[file_id] = file

        self.files = {}
        self._files_by_name = {}

    def restore_file(self, file_uuid: str):
        """
        Restores a file.

        :param file_uuid: The id of the file to restore
        """
        # if the file was not deleted, run a repair
        file = self.get_file_by_id(file_uuid=file_uuid, include_deleted=True)
        if not file:
            self.sys_log.error(f"Unable to restore file with uuid {file_uuid}. File does not exist.")
            return

        file.restore()
        self.files[file.uuid] = file
        self._files_by_name[file.name] = file

        if file.deleted:
            self.deleted_files.pop(file_uuid)

    def quarantine(self):
        """Quarantines the File System Folder."""
        pass

    def unquarantine(self):
        """Unquarantine of the File System Folder."""
        pass

    def quarantine_status(self) -> bool:
        """Returns true if the folder is being quarantined."""
        pass

    def scan(self, instant_scan: bool = False) -> None:
        """
        Update Folder visible status.

        :param: instant_scan: If True, the scan is completed instantly and ignores scan duration. Default False.
        """
        if self.deleted:
            self.sys_log.error(f"Unable to scan deleted folder {self.name}")
            return

        if instant_scan:
            for file_id in self.files:
                file = self.get_file_by_id(file_uuid=file_id)
                file.scan()
                if file.visible_health_status == FileSystemItemHealthStatus.CORRUPT:
                    self.visible_health_status = FileSystemItemHealthStatus.CORRUPT
            return

        if self.scan_countdown <= 0:
            # scan one file per timestep
            self.scan_countdown = self.scan_duration
            self.sys_log.info(f"Scanning folder {self.name} (id: {self.uuid})")
        else:
            # scan already in progress
            self.sys_log.info(f"Scan is already in progress {self.name} (id: {self.uuid})")

    def reveal_to_red(self, instant_scan: bool = False):
        """
        Reveals the folders and files to the red agent.

        :param: instant_scan: If True, the scan is completed instantly and ignores scan duration. Default False.
        """
        if self.deleted:
            self.sys_log.error(f"Unable to reveal deleted folder {self.name}")
            return

        if instant_scan:
            self.revealed_to_red = True
            for file_id in self.files:
                file = self.get_file_by_id(file_uuid=file_id)
                file.reveal_to_red()
            return

        if self.red_scan_countdown <= 0:
            # scan one file per timestep
            self.red_scan_countdown = self.red_scan_duration
            self.sys_log.info(f"Folder revealed to red agent: {self.name} (id: {self.uuid})")
        else:
            # scan already in progress
            self.sys_log.info(f"Red Agent Scan is already in progress {self.name} (id: {self.uuid})")

    def check_hash(self) -> None:
        """
        Runs a :func:`check_hash` on all files in the folder.

        If a file under the folder is corrupted, the whole folder is considered corrupted.

        TODO: For now this will just iterate through the files and run :func:`check_hash` and ignores
        any other changes to the folder

        Return False if corruption is detected, otherwise True
        """
        if self.deleted:
            self.sys_log.error(f"Unable to check hash of deleted folder {self.name}")
            return

        # iterate through the files and run a check hash
        no_corrupted_files = True

        for file_id in self.files:
            file = self.get_file_by_id(file_uuid=file_id)
            file.check_hash()
            if file.health_status == FileSystemItemHealthStatus.CORRUPT:
                no_corrupted_files = False

        # if one file in the folder is corrupted, set the folder status to corrupted
        if not no_corrupted_files:
            self.corrupt()

        self.sys_log.info(f"Checking hash of folder {self.name} (id: {self.uuid})")

    def repair(self) -> None:
        """Repair a corrupted Folder by setting the folder and containing files status to FileSystemItemStatus.GOOD."""
        if self.deleted:
            self.sys_log.error(f"Unable to repair deleted folder {self.name}")
            return

        # iterate through the files in the folder
        for file_id in self.files:
            file = self.get_file_by_id(file_uuid=file_id)
            file.repair()

        # set file status to good if corrupt
        if self.health_status == FileSystemItemHealthStatus.CORRUPT:
            self.health_status = FileSystemItemHealthStatus.GOOD

        self.health_status = FileSystemItemHealthStatus.GOOD

        self.sys_log.info(f"Repaired folder {self.name} (id: {self.uuid})")

    def restore(self) -> None:
        """
        If a Folder is corrupted, run a repair on the folder and its child files.

        If the folder is deleted, restore the folder by setting deleted status to False.
        """
        if self.deleted:
            self.deleted = False

        if self.restore_countdown <= 0:
            self.restore_countdown = self.restore_duration
            self.health_status = FileSystemItemHealthStatus.RESTORING
            self.sys_log.info(f"Restoring folder: {self.name} (id: {self.uuid})")
        else:
            # scan already in progress
            self.sys_log.info(f"Folder restoration already in progress {self.name} (id: {self.uuid})")

    def corrupt(self) -> None:
        """Corrupt a File by setting the folder and containing files status to FileSystemItemStatus.CORRUPT."""
        if self.deleted:
            self.sys_log.error(f"Unable to corrupt deleted folder {self.name}")
            return

        # iterate through the files in the folder
        for file_id in self.files:
            file = self.get_file_by_id(file_uuid=file_id)
            file.corrupt()

        # set file status to corrupt
        self.health_status = FileSystemItemHealthStatus.CORRUPT

        self.sys_log.info(f"Corrupted folder {self.name} (id: {self.uuid})")

    def delete(self):
        """Marks the file as deleted. Prevents agent actions from occuring."""
        if self.deleted:
            self.sys_log.error(f"Unable to delete an already deleted folder {self.name}")
            return

        self.deleted = True
