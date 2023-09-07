from ipaddress import IPv4Address
from typing import Any, Dict, Optional

from primaite.simulator.network.protocols.dns import DNSPacket, DNSRequest
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.services.service import Service


class DNSClient(Service):
    """Represents a DNS Client as a Service."""

    dns_cache: Dict[str, IPv4Address] = {}
    "A dict of known mappings between domain/URLs names and IPv4 addresses."

    def __init__(self, **kwargs):
        kwargs["name"] = "DNSClient"
        kwargs["port"] = Port.DNS
        # DNS uses UDP by default
        # it switches to TCP when the bytes exceed 512 (or 4096) bytes
        kwargs["protocol"] = IPProtocol.UDP
        super().__init__(**kwargs)

    def describe_state(self) -> Dict:
        """
        Describes the current state of the software.

        The specifics of the software's state, including its health, criticality,
        and any other pertinent information, should be implemented in subclasses.

        :return: A dictionary containing key-value pairs representing the current state of the software.
        :rtype: Dict
        """
        return {"Operating State": self.operating_state}

    def reset_component_for_episode(self, episode: int):
        """
        Resets the Service component for a new episode.

        This method ensures the Service is ready for a new episode, including resetting any
        stateful properties or statistics, and clearing any message queues.
        """
        super().reset_component_for_episode(episode=episode)
        self.dns_cache = {}

    def add_domain_to_cache(self, domain_name: str, ip_address: IPv4Address):
        """
        Adds a domain name to the DNS Client cache.

        :param: domain_name: The domain name to save to cache
        :param: ip_address: The IP Address to attach the domain name to
        """
        self.dns_cache[domain_name] = ip_address

    def check_domain_in_cache(
        self,
        target_domain: str,
        dest_ip_address: Optional[IPv4Address] = None,
        dest_port: Optional[Port] = None,
        session_id: Optional[str] = None,
        is_reattempt: bool = False,
    ) -> bool:
        """Function to check if domain name is in DNS client cache.

        :param: target_domain: The domain requested for an IP address.
        :param: dest_ip_address: The ip address of the payload destination.
        :param: dest_port: The port of the payload destination.
        :param: session_id: The Session ID the payload is to originate from. Optional.
        :param: is_reattempt: Checks if the request has been reattempted. Default is False.
        """
        # check if the target domain is in the client's DNS cache
        payload = DNSPacket(dns_request=DNSRequest(domain_name_request=target_domain))

        # check if the domain is already in the DNS cache
        if target_domain in self.dns_cache:
            return True
        else:
            # return False if already reattempted
            if is_reattempt:
                return False
            else:
                # send a request to check if domain name exists in the DNS Server
                self.send(payload=payload, dest_ip_address=dest_ip_address, dest_port=dest_port, session_id=session_id)
                # call function again
                return self.check_domain_in_cache(
                    target_domain=target_domain,
                    dest_ip_address=dest_ip_address,
                    dest_port=dest_port,
                    session_id=session_id,
                    is_reattempt=True,
                )

    def send(
        self,
        payload: Any,
        dest_ip_address: Optional[IPv4Address] = None,
        dest_port: Optional[Port] = None,
        session_id: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """
        Sends a payload to the SessionManager.

        The specifics of how the payload is processed and whether a response payload
        is generated should be implemented in subclasses.

        :param payload: The payload to be sent.
        :param dest_ip_address: The ip address of the payload destination.
        :param dest_port: The port of the payload destination.
        :param session_id: The Session ID the payload is to originate from. Optional.

        :return: True if successful, False otherwise.
        """
        # create DNS request packet
        self.software_manager.send_payload_to_session_manager(
            payload=payload, dest_ip_address=dest_ip_address, dest_port=dest_port, session_id=session_id
        )

    def receive(
        self,
        payload: Any,
        dest_ip_address: Optional[IPv4Address] = None,
        dest_port: Optional[Port] = None,
        session_id: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """
        Receives a payload from the SessionManager.

        The specifics of how the payload is processed and whether a response payload
        is generated should be implemented in subclasses.

        :param payload: The payload to be sent.
        :param dest_ip_address: The ip address of the payload destination.
        :param dest_port: The port of the payload destination.
        :param session_id: The Session ID the payload is to originate from. Optional.
        :return: True if successful, False otherwise.
        """
        super().send()
        # check the DNS packet (dns request, dns reply) here and see if it actually worked
        pass
