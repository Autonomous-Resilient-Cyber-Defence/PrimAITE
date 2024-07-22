from enum import Enum
from typing import Any, Optional, Union

from primaite.simulator.network.protocols.packet import DataPacket


class FTPCommand(Enum):
    """FTP Commands that are allowed."""

    PORT = "PORT"
    """Set a port to be used for the FTP transfer."""

    STOR = "STOR"
    """Copy or put data to the FTP server."""

    RETR = "RETR"
    """Retrieve data from the FTP server."""

    DELE = "DELE"
    """Delete the file in the specified path."""

    RMD = "RMD"
    """Remove the directory in the specified path."""

    MKD = "MKD"
    """Make a directory in the specified path."""

    LIST = "LIST"
    """Return a list of files in the specified path."""

    QUIT = "QUIT"
    """Ends connection between client and server."""


class FTPStatusCode(Enum):
    """Status code of the current FTP request."""

    NOT_FOUND = 14
    """Destination not found."""

    OK = 200
    """Command successful."""

    ERROR = 500
    """General error code."""


class FTPPacket(DataPacket):
    """Represents an FTP Packet."""

    ftp_command: FTPCommand
    """Command type of the packet."""

    ftp_command_args: Optional[Any] = None
    """Arguments for command."""

    status_code: Union[FTPStatusCode, None] = None
    """Status of the response."""
