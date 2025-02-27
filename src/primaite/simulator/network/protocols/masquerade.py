# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from enum import Enum
from typing import Optional

from primaite.simulator.network.protocols.packet import DataPacket
from primaite.utils.validation.ip_protocol import IPProtocol
from primaite.utils.validation.port import Port


class MasqueradePacket(DataPacket):
    """Represents an generic malicious packet that is masquerading as another protocol."""

    masquerade_protocol: IPProtocol  # The 'Masquerade' protocol that is currently in use

    masquerade_port: Port  # The 'Masquerade' port that is currently in use


class C2Packet(MasqueradePacket):
    """Represents C2 suite communications packets."""

    payload_type: Enum  # The type of C2 traffic (e.g keep alive, command or command out)

    command: Optional[Enum] = None  # Used to pass the actual C2 Command in C2 INPUT

    keep_alive_frequency: int
