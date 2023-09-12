from ipaddress import IPv4Address
from typing import Any, Dict, Optional

from prettytable import MARKDOWN, PrettyTable

from primaite import getLogger
from primaite.simulator.network.protocols.dns import DNSPacket
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.services.service import Service

_LOGGER = getLogger(__name__)


class DNSServer(Service):
    """Represents a DNS Server as a Service."""

    dns_table: Dict[str, IPv4Address] = {}
    "A dict of mappings between domain names and IPv4 addresses."

    def __init__(self, **kwargs):
        kwargs["name"] = "DNSServer"
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

    def dns_lookup(self, target_domain: Any) -> Optional[IPv4Address]:
        """
        Attempts to find the IP address for a domain name.

        :param target_domain: The single domain name requested by a DNS client.
        :return ip_address: The IP address of that domain name or None.
        """
        if target_domain in self.dns_table:
            return self.dns_table[target_domain]
        else:
            return None

    def dns_register(self, domain_name: str, domain_ip_address: IPv4Address):
        """
        Register a domain name and its IP address.

        :param: domain_name: The domain name to register
        :type: domain_name: str

        :param: domain_ip_address: The IP address that the domain should route to
        :type: domain_ip_address: IPv4Address
        """
        self.dns_table[domain_name] = domain_ip_address

    def reset_component_for_episode(self, episode: int):
        """
        Resets the Service component for a new episode.

        This method ensures the Service is ready for a new episode, including resetting any
        stateful properties or statistics, and clearing any message queues.
        """
        self.dns_table = {}
        super().reset_component_for_episode(episode=episode)

    def send(
        self,
        payload: Any,
        session_id: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """
        Sends a payload to the SessionManager.

        The specifics of how the payload is processed and whether a response payload
        is generated should be implemented in subclasses.

        :param: payload: The payload to send.
        :param: session_id: The id of the session

        :return: True if successful, False otherwise.
        """
        try:
            self.software_manager.send_payload_to_session_manager(payload=payload, session_id=session_id)
            return True
        except Exception as e:
            _LOGGER.error(e)
            return False

    def receive(
        self,
        payload: Any,
        session_id: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """
        Receives a payload from the SessionManager.

        The specifics of how the payload is processed and whether a response payload
        is generated should be implemented in subclasses.

        :param: payload: The payload to send.
        :param: session_id: The id of the session

        :return: True if DNS request returns a valid IP, otherwise, False
        """
        # The payload should be a DNS packet
        if not isinstance(payload, DNSPacket):
            _LOGGER.debug(f"{payload} is not a DNSPacket")
            return False
        # cast payload into a DNS packet
        payload: DNSPacket = payload
        if payload.dns_request is not None:
            # generate a reply with the correct DNS IP address
            payload = payload.generate_reply(self.dns_lookup(payload.dns_request.domain_name_request))
            # send reply
            self.send(payload, session_id)
            return payload.dns_reply is not None

        return False

    def show(self, markdown: bool = False):
        """Prints a table of DNS Lookup table."""
        table = PrettyTable(["Domain Name", "IP Address"])
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"{self.sys_log.hostname} DNS Lookup table"
        for dns in self.dns_table.items():
            table.add_row([dns[0], dns[1]])
        print(table)
