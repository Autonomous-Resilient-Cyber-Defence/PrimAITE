# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from datetime import datetime
from ipaddress import IPv4Address
from typing import Dict, Optional

from pydantic import Field

from primaite import getLogger
from primaite.simulator.network.protocols.ntp import NTPPacket
from primaite.simulator.system.services.service import Service, ServiceOperatingState
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.port import Port, PORT_LOOKUP

_LOGGER = getLogger(__name__)


class NTPClient(Service, identifier="NTPClient"):
    """Represents a NTP client as a service."""

    class ConfigSchema(Service.ConfigSchema):
        """ConfigSchema for NTPClient."""

        type: str = "NTPClient"

        ntp_server_ip: Optional[IPv4Address] = None
        "The NTP server the client sends requests to."

    config: ConfigSchema = Field(default_factory=lambda: NTPClient.ConfigSchema())

    time: Optional[datetime] = None

    def __init__(self, **kwargs):
        kwargs["name"] = "NTPClient"
        kwargs["port"] = PORT_LOOKUP["NTP"]
        kwargs["protocol"] = PROTOCOL_LOOKUP["UDP"]
        super().__init__(**kwargs)
        self.ntp_server = self.config.ntp_server_ip
        self.start()

    def configure(self, ntp_server_ip_address: IPv4Address) -> None:
        """
        Set the IP address for the NTP server.

        :param ntp_server_ip_address: IPv4 address of NTP server.
        :param ntp_client_ip_Address: IPv4 address of NTP client.
        """
        self.config.ntp_server_ip = ntp_server_ip_address
        self.sys_log.info(f"{self.name}: ntp_server: {self.config.ntp_server_ip}")

    def describe_state(self) -> Dict:
        """
        Describes the current state of the software.

        The specifics of the software's state, including its health, criticality,
        and any other pertinent information, should be implemented in subclasses.

        :return: A dictionary containing key-value pairs representing the current state
        of the software.
        :rtype: Dict
        """
        state = super().describe_state()
        return state

    def send(
        self,
        payload: NTPPacket,
        session_id: Optional[str] = None,
        dest_ip_address: IPv4Address = None,
        dest_port: Port = PORT_LOOKUP["NTP"],
        **kwargs,
    ) -> bool:
        """Requests NTP data from NTP server.

        :param payload: The payload to be sent.
        :param session_id: The Session ID the payload is to originate from. Optional.
        :param dest_ip_address: The ip address of the payload destination.
        :param dest_port: The port of the payload destination.

        :return: True if successful, False otherwise.
        """
        return super().send(
            payload=payload,
            dest_ip_address=dest_ip_address,
            dest_port=dest_port,
            session_id=session_id,
            **kwargs,
        )

    def receive(
        self,
        payload: NTPPacket,
        session_id: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """Receives time data from server.

        :param payload: The payload to be sent.
        :param session_id: The Session ID the payload is to originate from. Optional.
        :return: True if successful, False otherwise.
        """
        if not isinstance(payload, NTPPacket):
            self.sys_log.warning(f"{self.name}: Failed to parse NTP update")
            return False
        if payload.ntp_reply.ntp_datetime:
            self.time = payload.ntp_reply.ntp_datetime
            return True

    def request_time(self) -> None:
        """Send request to ntp_server."""
        if self.config.ntp_server_ip:
            self.software_manager.session_manager.receive_payload_from_software_manager(
                payload=NTPPacket(),
                dst_ip_address=self.config.ntp_server_ip,
                src_port=self.port,
                dst_port=self.port,
                ip_protocol=self.protocol,
            )

    def apply_timestep(self, timestep: int) -> None:
        """
        For each timestep request the time from the NTP server.

        In this instance, if any multi-timestep processes are currently
        occurring (such as restarting or installation), then they are brought one step closer to
        being finished.

        :param timestep: The current timestep number. (Amount of time since simulation episode began)
        :type timestep: int
        """
        super().apply_timestep(timestep)
        if self.operating_state == ServiceOperatingState.RUNNING:
            # request time from server
            self.request_time()
