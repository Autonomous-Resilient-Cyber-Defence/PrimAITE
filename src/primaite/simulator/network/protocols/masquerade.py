# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from enum import Enum
from typing import Optional

from primaite.simulator.network.protocols.packet import DataPacket


class C2Payload(Enum):
    """Represents the different types of command and control payloads."""

    KEEP_ALIVE = "keep_alive"
    """C2 Keep Alive payload. Used by the C2 beacon and C2 Server to confirm their connection."""

    INPUT = "input_command"
    """C2 Input Command payload. Used by the C2 Server to send a command to the c2 beacon."""

    OUTPUT = "output_command"
    """C2 Output Command. Used by the C2 Beacon to send the results of a Input command to the c2 server."""


class MasqueradePacket(DataPacket):
    """Represents an generic malicious packet that is masquerading as another protocol."""

    masquerade_protocol: Enum  # The 'Masquerade' protocol that is currently in use

    masquerade_port: Enum  # The 'Masquerade' port that is currently in use

    payload_type: C2Payload  # The type of C2 traffic (e.g keep alive, command or command out)

    command: Optional[str]  # Used to pass the actual C2 Command in C2 INPUT
