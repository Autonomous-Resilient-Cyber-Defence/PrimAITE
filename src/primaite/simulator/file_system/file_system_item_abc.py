# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from __future__ import annotations

import math
from abc import abstractmethod
from enum import Enum
from typing import Dict, Optional

from primaite import getLogger
from primaite.interface.request import RequestResponse
from primaite.simulator.core import RequestManager, RequestType, SimComponent
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
    """Status of the FileSystemItem."""

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

    revealed_to_red: bool = False
    "If true, the folder/file has been revealed to the red agent."

    sys_log: SysLog
    "Used for creating system logs."

    deleted: bool = False
    "If true, the FileSystemItem was deleted."

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        :return: Current state of this object and child objects.
        """
        state = super().describe_state()
        state["name"] = self.name
        state["health_status"] = self.health_status.value
        state["visible_status"] = self.visible_health_status.value
        state["previous_hash"] = self.previous_hash
        state["revealed_to_red"] = self.revealed_to_red
        return state

    def _init_request_manager(self) -> RequestManager:
        """
        Initialise the request manager.

        More information in user guide and docstring for SimComponent._init_request_manager.
        """
        rm = super()._init_request_manager()

        rm.add_request(
            name="scan", request_type=RequestType(func=lambda request, context: RequestResponse.from_bool(self.scan()))
        )
        rm.add_request(
            name="checkhash",
            request_type=RequestType(func=lambda request, context: RequestResponse.from_bool(self.check_hash())),
        )
        rm.add_request(
            name="repair",
            request_type=RequestType(func=lambda request, context: RequestResponse.from_bool(self.repair())),
        )
        rm.add_request(
            name="restore",
            request_type=RequestType(func=lambda request, context: RequestResponse.from_bool(self.restore())),
        )

        rm.add_request(
            name="corrupt",
            request_type=RequestType(func=lambda request, context: RequestResponse.from_bool(self.corrupt())),
        )

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
    def scan(self) -> bool:
        """Scan the folder/file - updates the visible_health_status."""
        return False

    @abstractmethod
    def reveal_to_red(self) -> None:
        """Reveal the folder/file to the red agent."""
        pass

    @abstractmethod
    def check_hash(self) -> bool:
        """
        Checks the hash of the file to detect any changes.

        For current implementation, any change in file hash means it is compromised.

        Return False if corruption is detected, otherwise True
        """
        return False

    @abstractmethod
    def repair(self) -> bool:
        """
        Repair the FileSystemItem.

        True if successfully repaired. False otherwise.
        """
        return False

    @abstractmethod
    def corrupt(self) -> bool:
        """
        Corrupt the FileSystemItem.

        True if successfully corrupted. False otherwise.
        """
        return False

    @abstractmethod
    def restore(self) -> bool:
        """Restore the file/folder to the state before it got ruined."""
        return False

    @abstractmethod
    def delete(self) -> None:
        """Mark the file/folder as deleted."""
        self.deleted = True
