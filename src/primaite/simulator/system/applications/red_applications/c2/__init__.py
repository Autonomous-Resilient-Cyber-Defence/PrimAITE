# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from typing import Optional, Union

from pydantic import BaseModel, Field

from primaite.interface.request import RequestFormat


class Command_Opts(BaseModel):
    """A C2 Pydantic Schema acting as a base class for all C2 Commands."""


class Ransomware_Opts(Command_Opts):
    """A Pydantic Schema for the Ransomware Configuration command options."""

    server_ip_address: str
    """The IP Address of the target database that the RansomwareScript will attack."""

    payload: Optional[str] = Field(default="ENCRYPT")
    """The malicious payload to be used to attack the target database."""


class Remote_Opts(Command_Opts):
    """A base C2 Pydantic Schema for all C2 Commands that require a terminal connection."""

    ip_address: Optional[str] = Field(default=None)
    """The IP address of a remote host. If this field defaults to None then a local session is used."""

    username: str
    """A Username of a valid user account. Used to login into both remote and local hosts."""

    password: str
    """A Password of a valid user account. Used to login into both remote and local hosts."""


class Exfil_Opts(Remote_Opts):
    """A Pydantic Schema for the C2 Data Exfiltration command options."""

    target_ip_address: str
    """The IP address of the target host that will be the target of the exfiltration."""

    target_file_name: str
    """The name of the file that is attempting to be exfiltrated."""

    target_folder_name: str
    """The name of the remote folder which contains the target file."""

    exfiltration_folder_name: Optional[str] = Field(default="exfiltration_folder")
    """"""


class Terminal_Opts(Remote_Opts):
    """A Pydantic Schema for the C2 Terminal command options."""

    commands: Union[list[RequestFormat], RequestFormat]
    """A list or individual Terminal Command. Please refer to the RequestResponse system for further info."""
