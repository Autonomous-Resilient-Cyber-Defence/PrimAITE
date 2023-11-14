from __future__ import annotations

from ipaddress import IPv4Address
from typing import Optional
from pydantic import BaseModel
from primaite.simulator.network.protocols.packet import DataPacket
from datetime import datetime


class NTPRequest(BaseModel):
    """Represents a NTP Request packet."""

    ntp_client: IPv4Address = None


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

    ntp_request: NTPRequest
    "NTP Request packet sent by NTP Client."
    ntp_reply: Optional[NTPReply] = None

    def generate_reply(self, time: datetime) -> NTPPacket:
        """ Generate a NTPPacket containing the time in a NTPReply object

        :param time: datetime object representing the time from the NTP server.
        :return: A new NTPPacket object.
        """
        self.ntp_reply = NTPReply(time)
        return self
