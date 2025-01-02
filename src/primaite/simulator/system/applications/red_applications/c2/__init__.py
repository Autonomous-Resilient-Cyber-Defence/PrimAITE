# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from typing import Optional, Union

from pydantic import BaseModel, Field, field_validator, ValidationInfo

from primaite.interface.request import RequestFormat


class CommandOpts(BaseModel):
    """A C2 Pydantic Schema acting as a base class for all C2 Commands."""

    @field_validator("payload", "exfiltration_folder_name", "ip_address", mode="before", check_fields=False)
    @classmethod
    def not_none(cls, v: str, info: ValidationInfo) -> int:
        """If None is passed, use the default value instead."""
        if v is None:
            return cls.model_fields[info.field_name].default
        return v


class RansomwareOpts(CommandOpts):
    """A Pydantic Schema for the Ransomware Configuration command options."""

    server_ip_address: str
    """The IP Address of the target database that the RansomwareScript will attack."""

    payload: str = Field(default="ENCRYPT")
    """The malicious payload to be used to attack the target database."""


class RemoteOpts(CommandOpts):
    """A base C2 Pydantic Schema for all C2 Commands that require a terminal connection."""

    ip_address: Optional[str] = Field(default=None)
    """The IP address of a remote host. If this field defaults to None then a local session is used."""

    username: str
    """A Username of a valid user account. Used to login into both remote and local hosts."""

    password: str
    """A Password of a valid user account. Used to login into both remote and local hosts."""


class ExfilOpts(RemoteOpts):
    """A Pydantic Schema for the C2 Data Exfiltration command options."""

    target_ip_address: str
    """The IP address of the target host that will be the target of the exfiltration."""

    target_file_name: str
    """The name of the file that is attempting to be exfiltrated."""

    target_folder_name: str
    """The name of the remote folder which contains the target file."""

    exfiltration_folder_name: str = Field(default="exfiltration_folder")
    """The name of C2 Suite folder used to store the target file. Defaults to ``exfiltration_folder``"""


class TerminalOpts(RemoteOpts):
    """A Pydantic Schema for the C2 Terminal command options."""

    commands: Union[list[RequestFormat], RequestFormat]
    """A list or individual Terminal Command. Please refer to the RequestResponse system for further info."""
