# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from typing import Optional, Union

from pydantic import BaseModel, Field

from primaite.interface.request import RequestFormat


class Command_Opts(BaseModel):
    """A C2 Pydantic Schema acting as a base class for all C2 Commands."""


class Ransomware_Opts(Command_Opts):
    """A Pydantic Schema for the Ransomware Configuration command options."""

    server_ip_address: str
    """"""

    payload: Optional[str] = Field(default="ENCRYPT")
    """"""


class Remote_Opts(Command_Opts):
    """A base C2 Pydantic Schema for all C2 Commands that require a remote terminal connection."""

    ip_address: Optional[str] = Field(default=None)
    """"""

    username: str
    """"""

    password: str
    """"""


class Exfil_Opts(Remote_Opts):
    """A Pydantic Schema for the C2 Data Exfiltration command options."""

    target_ip_address: str
    """"""

    target_folder_name: str
    """"""

    target_file_name: str
    """"""

    exfiltration_folder_name: Optional[str] = Field(default="exfiltration_folder")
    """"""


class Terminal_Opts(Remote_Opts):
    """A Pydantic Schema for the C2 Terminal command options."""

    commands: Union[list[RequestFormat], RequestFormat]
    """"""
