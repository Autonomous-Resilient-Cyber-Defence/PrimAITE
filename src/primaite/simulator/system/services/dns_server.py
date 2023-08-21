from abc import abstractmethod
from ipaddress import IPv4Address
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from primaite.simulator.network.protocols.dns import DNSPacket, DNSReply, DNSRequest


class DNSServer(BaseModel):
    """Represents a DNS Server as a Service."""

    dns_table: dict[str:IPv4Address] = {}
    "A dict of mappings between domain names and IPv4 addresses."

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

        :param action: A list of actions to apply. (unsure)
        """
        pass

    def dns_lookup(self, target_domain: str) -> Optional[IPv4Address]:
        """
        Attempts to find the IP address for a domain name.

        :param target_domain: The single domain name requested by a DNS client.
        :return ip_address: The IP address of that domain name or None.
        """
        if target_domain in self.dns_table:
            return self.dns_table[target_domain]
        else:
            return None

    def reset_component_for_episode(self):
        """
        Resets the Service component for a new episode.

        This method ensures the Service is ready for a new episode, including resetting any
        stateful properties or statistics, and clearing any message queues.
        """
        self.dns_table = {}

    def send(self, payload: Any, session_id: str, **kwargs) -> bool:
        """
        Sends a payload to the SessionManager.

        The specifics of how the payload is processed and whether a response payload
        is generated should be implemented in subclasses.

        :param payload: The payload to send.
        :return: True if successful, False otherwise.
        """
        ip_addresses = list(self.dns_table.values())
        domain_names = list(self.dns_table.keys())
        index_of_domain = ip_addresses.index(payload)
        DNSPacket(
            dns_request=DNSRequest(domain_name_request=domain_names[index_of_domain]),
            dns_reply=DNSReply(domain_name_ip_address=payload),
        )

    def receive(self, payload: Any, session_id: str, **kwargs) -> bool:
        """
        Receives a payload from the SessionManager.

        The specifics of how the payload is processed and whether a response payload
        is generated should be implemented in subclasses.

        :param payload: The payload to receive. (take the domain name and do dns lookup)
        :return: True if successful, False otherwise.
        """
        ip_address = self.dns_lookup(payload)
        if ip_address is not None:
            self.send(ip_address, session_id)
            return True

        return False
