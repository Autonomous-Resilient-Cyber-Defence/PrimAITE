from ipaddress import IPv4Address
from typing import Dict, Optional

from primaite import getLogger
from primaite.simulator.network.protocols.dns import DNSPacket, DNSRequest
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.core.software_manager import SoftwareManager
from primaite.simulator.system.services.service import Service

_LOGGER = getLogger(__name__)


class DNSClient(Service):
    """Represents a DNS Client as a Service."""

    dns_cache: Dict[str, IPv4Address] = {}
    "A dict of known mappings between domain/URLs names and IPv4 addresses."
    dns_server: Optional[IPv4Address] = None
    "The DNS Server the client sends requests to."

    def __init__(self, **kwargs):
        kwargs["name"] = "DNSClient"
        kwargs["port"] = Port.DNS
        # DNS uses UDP by default
        # it switches to TCP when the bytes exceed 512 (or 4096) bytes
        # TCP for now
        kwargs["protocol"] = IPProtocol.TCP
        super().__init__(**kwargs)
        self.start()

    def set_original_state(self):
        """Sets the original state."""
        super().set_original_state()
        vals_to_include = {"dns_server"}
        self._original_state.update(self.model_dump(include=vals_to_include))

    def reset_component_for_episode(self, episode: int):
        """Reset the original state of the SimComponent."""
        self.dns_cache.clear()
        super().reset_component_for_episode(episode)

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

    def add_domain_to_cache(self, domain_name: str, ip_address: IPv4Address):
        """
        Adds a domain name to the DNS Client cache.

        :param: domain_name: The domain name to save to cache
        :param: ip_address: The IP Address to attach the domain name to
        """
        self.dns_cache[domain_name] = ip_address

    def check_domain_exists(
        self,
        target_domain: str,
        session_id: Optional[str] = None,
        is_reattempt: bool = False,
    ) -> bool:
        """Function to check if domain name exists.

        :param: target_domain: The domain requested for an IP address.
        :param: session_id: The Session ID the payload is to originate from. Optional.
        :param: is_reattempt: Checks if the request has been reattempted. Default is False.
        """
        # check if DNS server is configured
        if self.dns_server is None:
            self.sys_log.error(f"{self.name}: DNS Server is not configured")
            return False

        # check if the target domain is in the client's DNS cache
        payload = DNSPacket(dns_request=DNSRequest(domain_name_request=target_domain))

        # check if the domain is already in the DNS cache
        if target_domain in self.dns_cache:
            self.sys_log.info(
                f"{self.name}: Domain lookup for {target_domain} successful,"
                f"resolves to {self.dns_cache[target_domain]}"
            )
            return True
        else:
            # return False if already reattempted
            if is_reattempt:
                self.sys_log.info(f"{self.name}: Domain lookup for {target_domain} failed")
                return False
            else:
                # send a request to check if domain name exists in the DNS Server
                software_manager: SoftwareManager = self.software_manager
                software_manager.send_payload_to_session_manager(
                    payload=payload, dest_ip_address=self.dns_server, dest_port=Port.DNS
                )

                # recursively re-call the function passing is_reattempt=True
                return self.check_domain_exists(
                    target_domain=target_domain,
                    session_id=session_id,
                    is_reattempt=True,
                )

    def send(
        self,
        payload: DNSPacket,
        session_id: Optional[str] = None,
        dest_ip_address: Optional[IPv4Address] = None,
        dest_port: Optional[Port] = None,
        **kwargs,
    ) -> bool:
        """
        Sends a payload to the SessionManager.

        :param payload: The payload to be sent.
        :param dest_ip_address: The ip address of the payload destination.
        :param dest_port: The port of the payload destination.
        :param session_id: The Session ID the payload is to originate from. Optional.

        :return: True if successful, False otherwise.
        """
        self.sys_log.info(f"{self.name}: Sending DNS request to resolve {payload.dns_request.domain_name_request}")

        return super().send(
            payload=payload, dest_ip_address=dest_ip_address, dest_port=dest_port, session_id=session_id, **kwargs
        )

    def receive(
        self,
        payload: DNSPacket,
        session_id: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """
        Receives a payload from the SessionManager.

        :param payload: The payload to be sent.
        :param session_id: The Session ID the payload is to originate from. Optional.
        :return: True if successful, False otherwise.
        """
        # The payload should be a DNS packet
        if not isinstance(payload, DNSPacket):
            _LOGGER.debug(f"{payload} is not a DNSPacket")
            return False

        if payload.dns_reply is not None:
            # add the IP address to the client cache
            if payload.dns_reply.domain_name_ip_address:
                self.sys_log.info(
                    f"{self.name}: Resolved domain name {payload.dns_request.domain_name_request} "
                    f"to {payload.dns_reply.domain_name_ip_address}"
                )
                self.dns_cache[payload.dns_request.domain_name_request] = payload.dns_reply.domain_name_ip_address
                return True

        self.sys_log.error(f"Failed to resolve domain name {payload.dns_request.domain_name_request}")
        return False
