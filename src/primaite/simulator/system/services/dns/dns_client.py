# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
"""DNS Client."""
from ipaddress import IPv4Address
from typing import Dict, Optional, TYPE_CHECKING

from pydantic import Field

from primaite import getLogger
from primaite.simulator.network.protocols.dns import DNSPacket, DNSRequest
from primaite.simulator.system.core.software_manager import SoftwareManager
from primaite.simulator.system.services.service import Service
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.ipv4_address import IPV4Address
from primaite.utils.validation.port import Port, PORT_LOOKUP

if TYPE_CHECKING:
    from primaite.simulator.network.hardware.base import Node

_LOGGER = getLogger(__name__)


class DNSClient(Service, discriminator="dns-client"):
    """Represents a DNS Client as a Service."""

    class ConfigSchema(Service.ConfigSchema):
        """ConfigSchema for DNSClient."""

        type: str = "dns-client"
        dns_server: Optional[IPV4Address] = None
        "The DNS Server the client sends requests to."

    config: ConfigSchema = Field(default_factory=lambda: DNSClient.ConfigSchema())
    dns_cache: Dict[str, IPv4Address] = {}
    "A dict of known mappings between domain/URLs names and IPv4 addresses."

    def __init__(self, **kwargs):
        kwargs["name"] = "dns-client"
        kwargs["port"] = PORT_LOOKUP["DNS"]
        # DNS uses UDP by default
        # it switches to TCP when the bytes exceed 512 (or 4096) bytes
        # TCP for now
        kwargs["protocol"] = PROTOCOL_LOOKUP["TCP"]
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

    @property
    def dns_server(self) -> Optional[IPV4Address]:
        """Convenience property for accessing the dns server configuration."""
        return self.config.dns_server

    @dns_server.setter
    def dns_server(self, val: IPV4Address) -> None:
        self.config.dns_server = val

    def add_domain_to_cache(self, domain_name: str, ip_address: IPv4Address) -> bool:
        """
        Adds a domain name to the DNS Client cache.

        :param: domain_name: The domain name to save to cache
        :param: ip_address: The IP Address to attach the domain name to
        """
        if not self._can_perform_action():
            return False

        self.dns_cache[domain_name] = ip_address
        return True

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
        if not self._can_perform_action():
            return False

        # check if the domain is already in the DNS cache
        if target_domain in self.dns_cache:
            self.sys_log.info(
                f"{self.name}: Domain lookup for {target_domain} successful,"
                f"resolves to {self.dns_cache[target_domain]}"
            )
            return True

        # check if DNS server is configured
        if self.dns_server is None:
            self.sys_log.warning(f"{self.name}: DNS Server is not configured")
            return False

        # check if the target domain is in the client's DNS cache
        payload = DNSPacket(dns_request=DNSRequest(domain_name_request=target_domain))

        # return False if already reattempted
        if is_reattempt:
            self.sys_log.warning(f"{self.name}: Domain lookup for {target_domain} failed")
            return False
        else:
            # send a request to check if domain name exists in the DNS Server
            software_manager: SoftwareManager = self.software_manager
            software_manager.send_payload_to_session_manager(
                payload=payload, dest_ip_address=self.dns_server, dest_port=PORT_LOOKUP["DNS"]
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
            self.sys_log.warning(f"{self.name}: Payload is not a DNSPacket")
            self.sys_log.debug(f"{self.name}: {payload}")
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

        self.sys_log.warning(f"Failed to resolve domain name {payload.dns_request.domain_name_request}")
        return False

    def install(self) -> None:
        """Set the DNS server to be the node's DNS server unless a different one was already provided."""
        self.parent: Node
        if self.parent and not self.dns_server:
            self.config.dns_server = self.parent.dns_server
