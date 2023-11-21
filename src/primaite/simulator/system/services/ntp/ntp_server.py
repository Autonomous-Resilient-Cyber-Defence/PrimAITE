from datetime import datetime
from typing import Any, Dict, Optional

from primaite import getLogger
from primaite.simulator.network.protocols.ntp import NTPPacket
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.services.service import Service

_LOGGER = getLogger(__name__)


class NTPServer(Service):
    """Represents a NTP server as a service."""

    def __init__(self, **kwargs):
        kwargs["name"] = "NTPServer"
        kwargs["port"] = Port.NTP
        kwargs["protocol"] = IPProtocol.UDP
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

    def reset_component_for_episode(self, episode: int):
        """
        Resets the Service component for a new episode.

        This method ensures the Service is ready for a new episode, including
        resetting any stateful properties or statistics, and clearing any message
        queues.
        """
        pass

    def receive(
        self,
        payload: Any,
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
        if not (isinstance(payload, NTPPacket) and payload.ntp_request.ntp_client):
            _LOGGER.debug(f"{payload} is not a NTPPacket")
            return False
        payload: NTPPacket = payload
        if payload.ntp_request.ntp_client:
            self.sys_log.info(
                f"{self.name}: Received request for {payload.ntp_request.ntp_client} \
                    from session {session_id}"
            )
            # generate a reply with the current time
            time = datetime.now()
            payload = payload.generate_reply(time)
            self.sys_log.info(
                f"{self.name}: Responding to NTP request for {payload.ntp_request.ntp_client} "
                f"with current time: {time}"
            )
            # send reply
            self.send(payload, session_id)
            return True
