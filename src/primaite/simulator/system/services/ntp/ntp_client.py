from ipaddress import IPv4Address
from typing import Dict, Optional
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.services.service import Service


from primaite import getLogger

_LOGGER = getLogger(__name__)


class NTPClient(Service):
    """Represents a NTP client as a service"""

    ntp_server: Optional[IPv4Address] = None
    "The NTP server the client sends requests to."

    def __init__(self, **kwargs):
        kwargs["name"] = "NTPClient"
        kwargs["port"] = Port.NTP
        kwargs["protocol"] = IPProtocol.UDP
        super().__init__(**kwargs)
        self.start()

    def describe_state(self) -> Dict:
        """
        Describes the current state of the software.

        The specifics of the software's state, including its health, criticality,
        and any other pertinent information, should be implemented in subclasses.

        :return: A dictionary containing key-value pairs representing the current state of the software.
        :rtype: Dict
        """
        state = super().describe_state()
        return state

    def reset_component_for_episode(self, episode: int):
        """
        Resets the Service component for a new episode.

        This method ensures the Service is ready for a new episode, including resetting any
        stateful properties or statistics, and clearing any message queues.
        """
        pass

    def receive(self):
        """Receives time data from server"""
        pass
