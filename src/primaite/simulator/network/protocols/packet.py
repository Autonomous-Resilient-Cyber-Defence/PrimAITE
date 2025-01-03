# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from typing import Any

from pydantic import BaseModel


class DataPacket(BaseModel):
    """Data packet abstract class."""

    payload: Any = None
    """Payload content of the packet."""

    packet_payload_size: float = 0
    """Size of the packet."""

    def get_packet_size(self) -> float:
        """Returns the size of the packet header and payload."""
        return self.packet_payload_size + float(len(self.model_dump_json().encode("utf-8")))
