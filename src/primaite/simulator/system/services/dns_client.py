from abc import abstractmethod
from ipaddress import IPv4Address
from typing import Any, Dict, List

from pydantic import BaseModel

from primaite.simulator.network.protocols.dns import DNSPacket, DNSRequest


class DNSClient(BaseModel):
    """Represents a DNS Client as a Service."""

    dns_cache: Dict[str:IPv4Address] = {}
    "A dict of known mappings between domain/URLs names and IPv4 addresses."

    @abstractmethod
    def describe_state(self) -> Dict:
        """
        Describes the current state of the software.

        The specifics of the software's state, including its health, criticality,
        and any other pertinent information, should be implemented in subclasses.

        :return: A dictionary containing key-value pairs representing the current state of the software.
        :rtype: Dict
        """
        return {"Operating State": self.operating_state}

    def apply_action(self, action: List[str]) -> None:
        """
        Applies a list of actions to the Service.

        :param action: A list of actions to apply.
        """
        pass

    def reset_component_for_episode(self):
        """
        Resets the Service component for a new episode.

        This method ensures the Service is ready for a new episode, including resetting any
        stateful properties or statistics, and clearing any message queues.
        """
        self.dns_cache = {}

    def check_domain_is_in_cache(self, target_domain: str, session_id: str):
        """Function to check if domain name is in DNS client cache."""
        if target_domain in self.dns_cache:
            ip_address = self.dns_cache[target_domain]
            self.send(ip_address, session_id)
        else:
            self.send(target_domain, session_id)

    def send(self, payload: Any, session_id: str, **kwargs) -> bool:
        """
        Sends a payload to the SessionManager.

        The specifics of how the payload is processed and whether a response payload
        is generated should be implemented in subclasses.

        :param payload: The payload to send.
        :return: True if successful, False otherwise.
        """
        DNSPacket(dns_request=DNSRequest(domain_name_request=payload), dns_reply=None)

    def receive(self, payload: Any, session_id: str, **kwargs) -> bool:
        """
        Receives a payload from the SessionManager.

        The specifics of how the payload is processed and whether a response payload
        is generated should be implemented in subclasses.

        :param payload: The payload to receive. (receive a DNS packet with dns request and dns reply in, send to web
        browser)
        :return: True if successful, False otherwise.
        """
        # check DNS packet (dns request, dns reply) here and see if it actually worked

        pass
