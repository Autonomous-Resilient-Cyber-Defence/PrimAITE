from abc import abstractmethod
from ipaddress import IPv4Address
from typing import Any, Dict, List

from pydantic import BaseModel


class DNSClient(BaseModel):
    """Represents a DNS Client as a Service."""

    target_url: str
    "The URL/domain name the client requests the IP for."
    dns_cache: Dict[str:IPv4Address] = {}
    "A dict of known mappings between domain names and IPv4 addresses."

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
        pass

    def send(self, payload: Any, session_id: str, **kwargs) -> bool:
        """
        Sends a payload to the SessionManager.

        The specifics of how the payload is processed and whether a response payload
        is generated should be implemented in subclasses.

        :param payload: The payload to send.
        :return: True if successful, False otherwise.
        """
        pass

    def receive(self, payload: Any, session_id: str, **kwargs) -> bool:
        """
        Receives a payload from the SessionManager.

        The specifics of how the payload is processed and whether a response payload
        is generated should be implemented in subclasses.

        :param payload: The payload to receive.
        :return: True if successful, False otherwise.
        """
        pass
