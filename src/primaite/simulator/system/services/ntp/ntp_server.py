# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from datetime import datetime
from typing import Dict, Optional

from primaite import getLogger
from primaite.simulator.network.protocols.ntp import NTPPacket
from primaite.simulator.system.services.service import Service
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.port import PORT_LOOKUP

_LOGGER = getLogger(__name__)


class NTPServer(Service):
    """Represents a NTP server as a service."""

    def __init__(self, **kwargs):
        kwargs["name"] = "NTPServer"
        kwargs["port"] = PORT_LOOKUP["NTP"]
        kwargs["protocol"] = PROTOCOL_LOOKUP["UDP"]
        super().__init__(**kwargs)
        self.start()

    def describe_state(self) -> Dict:
        """
        Describes the current state of the software.

        The specifics of the software's state, including its health, criticality,
        and any other pertinent information, should be implemented in subclasses.

        :return: A dictionary containing key-value pairs representing the current
        state of the software.
        :rtype: Dict
        """
        state = super().describe_state()
        return state

    def receive(
        self,
        payload: NTPPacket,
        session_id: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """
        Receives a request from NTPClient.

        Check that request has a valid IP address.

        :param payload: The payload to send.
        :param session_id: Id of the session (Optional).

        :return: True if valid NTP request else False.
        """
        if not (isinstance(payload, NTPPacket)):
            self.sys_log.warning(f"{self.name}: Payload is not a NTPPacket")
            self.sys_log.debug(f"{self.name}: {payload}")
            return False
        payload: NTPPacket = payload

        # generate a reply with the current time
        time = datetime.now()
        payload = payload.generate_reply(time)
        # send reply
        self.software_manager.session_manager.receive_payload_from_software_manager(
            payload=payload, src_port=self.port, dst_port=self.port, ip_protocol=self.protocol, session_id=session_id
        )
        return True
