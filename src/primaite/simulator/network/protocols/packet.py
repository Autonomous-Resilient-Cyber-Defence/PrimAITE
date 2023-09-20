from pydantic import BaseModel


class DataPacket(BaseModel):
    """Data packet abstract class."""

    packet_payload_size: float = 0
    """Size of the packet."""

    def get_packet_size(self) -> float:
        """Returns the size of the packet header and payload."""
        return self.packet_payload_size + float(len(self.model_dump_json().encode("utf-8")))
