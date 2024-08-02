# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from enum import Enum
from typing import Optional

from primaite.simulator.network.protocols.packet import DataPacket


class MasqueradePacket(DataPacket):
    """Represents an generic malicious packet that is masquerading as another protocol."""

    masquerade_protocol: Enum  # The 'Masquerade' protocol that is currently in use

    masquerade_port: Enum  # The 'Masquerade' port that is currently in use

    payload_type: Enum  # The type of C2 traffic (e.g keep alive, command or command out)

    command: Optional[Enum] = None  # Used to pass the actual C2 Command in C2 INPUT
