# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

from enum import IntEnum
from typing import Dict, Optional

from primaite.interface.request import RequestResponse
from primaite.simulator.network.protocols.packet import DataPacket

# TODO: Elaborate / Confirm / Validate -  See 2709.
#       Placeholder implementation for Terminal Class implementation.


class SSHTransportMessage(IntEnum):
    """
    Enum list of Transport layer messages that can be handled by the simulation.

    Each msg value is equivalent to the real-world.
    """

    SSH_MSG_USERAUTH_REQUEST = 50
    """Requests User Authentication."""

    SSH_MSG_USERAUTH_FAILURE = 51
    """Indicates User Authentication failed."""

    SSH_MSG_USERAUTH_SUCCESS = 52
    """Indicates User Authentication failed was successful."""

    SSH_MSG_SERVICE_REQUEST = 24
    """Requests a service - such as executing a command."""

    # These two msgs are invented for primAITE however are modelled on reality

    SSH_MSG_SERVICE_FAILED = 25
    """Indicates that the requested service failed."""

    SSH_MSG_SERVICE_SUCCESS = 26
    """Indicates that the requested service was successful."""


class SSHConnectionMessage(IntEnum):
    """Int Enum list of all SSH's connection protocol messages that can be handled by the simulation."""

    SSH_MSG_CHANNEL_OPEN = 80
    """Requests an open channel - Used in combination with SSH_MSG_USERAUTH_REQUEST."""

    SSH_MSG_CHANNEL_OPEN_CONFIRMATION = 81
    """Confirms an open channel."""

    SSH_MSG_CHANNEL_OPEN_FAILED = 82
    """Indicates that channel opening failure."""

    SSH_MSG_CHANNEL_DATA = 84
    """Indicates that data is being sent through the channel."""

    SSH_MSG_CHANNEL_CLOSE = 87
    """Closes the channel."""


class SSHUserCredentials(DataPacket):
    """Hold Username and Password in SSH Packets"""

    username: str = None
    """Username for login"""

    password: str = None
    """Password for login"""


class SSHPacket(DataPacket):
    """Represents an SSHPacket."""

    transport_message: SSHTransportMessage = None

    connection_message: SSHConnectionMessage = None

    connection_uuid: Optional[str] = None  # The connection uuid used to validate the session

    ssh_output: Optional[RequestResponse] = None  # The Request Manager's returned RequestResponse

    ssh_command: Optional[str] = None  # This is the request string
