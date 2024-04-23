from __future__ import annotations

import hashlib
import json
import os.path
from pathlib import Path
from typing import Dict, Optional

from primaite import getLogger
from primaite.simulator.file_system.file_system_item_abc import FileSystemItemABC, FileSystemItemHealthStatus
from primaite.simulator.file_system.file_type import FileType, get_file_type_from_extension

_LOGGER = getLogger(__name__)


class File(FileSystemItemABC):
    """
    Class representing a file in the simulation.

    :ivar Folder folder: The folder in which the file resides.
    :ivar FileType file_type: The type of the file.
    :ivar Optional[int] sim_size: The simulated file size.
    :ivar bool real: Indicates if the file is actually a real file in the Node sim fs output.
    :ivar Optional[Path] sim_path: The path if the file is real.
    """

    folder_id: str
    "The id of the Folder the File is in."
    folder_name: str
    "The name of the Folder the file is in."
    file_type: FileType
    "The type of File."
    sim_size: Optional[int] = None
    "The simulated file size."
    real: bool = False
    "Indicates whether the File is actually a real file in the Node sim fs output."
    sim_path: Optional[Path] = None
    "The Path if real is True."
    sim_root: Optional[Path] = None
    "Root path of the simulation."
    num_access: int = 0
    "Number of times the file was accessed in the current step."

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
            self.sim_path = self.sim_root / self.path
            if not self.sim_path.exists():
                self.sim_path.parent.mkdir(exist_ok=True, parents=True)
                with open(self.sim_path, mode="a"):
                    pass

        self.sys_log.info(f"Created file /{self.path} (id: {self.uuid})")

    @property
    def path(self) -> str:
        """
        Get the path of the file in the file system.

        :return: The full path of the file.
        """
        return f"{self.folder_name}/{self.name}"

    @property
    def size(self) -> int:
        """
        Get the size of the file in bytes.

        :return: The size of the file in bytes.
        """
        if self.real:
            return os.path.getsize(self.sim_path)
        return self.sim_size

    def apply_timestep(self, timestep: int) -> None:
        """
        Apply a timestep to the file.

        :param timestep: The current timestep of the simulation.
        """
        super().apply_timestep(timestep=timestep)

    def pre_timestep(self, timestep: int) -> None:
        """Apply pre-timestep logic."""
        super().pre_timestep(timestep)

        # reset the number of accesses to 0
        self.num_access = 0

    def describe_state(self) -> Dict:
        """Produce a dictionary describing the current state of this object."""
        state = super().describe_state()
        state["size"] = self.size
        state["file_type"] = self.file_type.name
        state["num_access"] = self.num_access
        return state

    def scan(self) -> bool:
        """Updates the visible statuses of the file."""
        if self.deleted:
            self.sys_log.error(f"Unable to scan deleted file {self.folder_name}/{self.name}")
            return False

        self.num_access += 1  # file was accessed
        path = self.folder.name + "/" + self.name
        self.sys_log.info(f"Scanning file {self.sim_path if self.sim_path else path}")
        self.visible_health_status = self.health_status
        return True

    def reveal_to_red(self) -> None:
        """Reveals the folder/file to the red agent."""
        if self.deleted:
            self.sys_log.error(f"Unable to reveal deleted file {self.folder_name}/{self.name}")
            return
        self.revealed_to_red = True

    def check_hash(self) -> bool:
        """
        Check if the file has been changed.

        If changed, the file is considered corrupted.

        Return False if corruption is detected, otherwise True
        """
        if self.deleted:
            self.sys_log.error(f"Unable to check hash of deleted file {self.folder_name}/{self.name}")
            return False
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

        return True

    def repair(self) -> bool:
        """Repair a corrupted File by setting the status to FileSystemItemStatus.GOOD."""
        if self.deleted:
            self.sys_log.error(f"Unable to repair deleted file {self.folder_name}/{self.name}")
            return False

        # set file status to good if corrupt
        if self.health_status == FileSystemItemHealthStatus.CORRUPT:
            self.health_status = FileSystemItemHealthStatus.GOOD

        self.num_access += 1  # file was accessed
        path = self.folder.name + "/" + self.name
        self.sys_log.info(f"Repaired file {self.sim_path if self.sim_path else path}")
        return True

    def corrupt(self) -> bool:
        """Corrupt a File by setting the status to FileSystemItemStatus.CORRUPT."""
        if self.deleted:
            self.sys_log.error(f"Unable to corrupt deleted file {self.folder_name}/{self.name}")
            return False

        # set file status to good if corrupt
        if self.health_status == FileSystemItemHealthStatus.GOOD:
            self.health_status = FileSystemItemHealthStatus.CORRUPT

        self.num_access += 1  # file was accessed
        path = self.folder.name + "/" + self.name
        self.sys_log.info(f"Corrupted file {self.sim_path if self.sim_path else path}")
        return True

    def restore(self) -> bool:
        """Determines if the file needs to be repaired or unmarked as deleted."""
        if self.deleted:
            self.deleted = False
            return True

        if self.health_status == FileSystemItemHealthStatus.CORRUPT:
            self.health_status = FileSystemItemHealthStatus.GOOD

        self.num_access += 1  # file was accessed
        path = self.folder.name + "/" + self.name
        self.sys_log.info(f"Restored file {self.sim_path if self.sim_path else path}")
        return True

    def delete(self) -> bool:
        """Marks the file as deleted."""
        if self.deleted:
            self.sys_log.error(f"Unable to delete an already deleted file {self.folder_name}/{self.name}")
            return False

        self.num_access += 1  # file was accessed
        self.deleted = True
        self.sys_log.info(f"File deleted {self.folder_name}/{self.name}")
        return True
