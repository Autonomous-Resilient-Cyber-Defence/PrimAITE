# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from primaite.simulator.network.protocols.packet import DataPacket


class NTPReply(BaseModel):
    """Represents a NTP Reply packet."""

    ntp_datetime: datetime
    "NTP datetime object set by NTP Server."


class NTPPacket(DataPacket):
    """
    Represents the NTP layer of a network frame.

    :param ntp_request: NTPRequest packet from NTP client.
    :param ntp_reply: NTPReply packet from NTP Server.
    """

    ntp_reply: Optional[NTPReply] = None

    def generate_reply(self, ntp_server_time: datetime) -> NTPPacket:
        """Generate a NTPPacket containing the time in a NTPReply object.

        :param time: datetime object representing the time from the NTP server.
        :return: A new NTPPacket object.
        """
        self.ntp_reply = NTPReply(ntp_datetime=ntp_server_time)
        return self
