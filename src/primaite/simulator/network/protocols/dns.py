# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from __future__ import annotations

from ipaddress import IPv4Address
from typing import Optional

from pydantic import BaseModel

from primaite.simulator.network.protocols.packet import DataPacket


class DNSRequest(BaseModel):
    """Represents a DNS Request packet of a network frame.

    :param domain_name_request: Domain Name Request for IP address.
    """

    domain_name_request: str
    "Domain Name Request for IP address."


class DNSReply(BaseModel):
    """Represents a DNS Reply packet of a network frame.

    :param domain_name_ip_address: IP Address of the Domain Name requested.
    """

    domain_name_ip_address: Optional[IPv4Address] = None
    "IP Address of the Domain Name requested."


class DNSPacket(DataPacket):
    """
    Represents the DNS layer of a network frame.

    :param dns_request: DNS Request packet sent by DNS Client.
    :param dns_reply: DNS Reply packet generated by DNS Server.

    :Example:

    >>> dns_request = DNSPacket(
    ...     domain_name_request=DNSRequest(domain_name_request="www.google.co.uk"),
    ...     dns_reply=None
    ... )
    >>> dns_response = DNSPacket(
    ...     dns_request=DNSRequest(domain_name_request="www.google.co.uk"),
    ...     dns_reply=DNSReply(domain_name_ip_address=IPv4Address("142.250.179.227"))
    ... )
    """

    dns_request: DNSRequest
    "DNS Request packet sent by DNS Client."
    dns_reply: Optional[DNSReply] = None
    "DNS Reply packet generated by DNS Server."

    def generate_reply(self, domain_ip_address: IPv4Address) -> DNSPacket:
        """Generate a new DNSPacket to be sent as a response with a DNS Reply packet which contains the IP address.

        :param domain_ip_address: The IP address that was being sought after from the original target domain name.
        :return: A new instance of DNSPacket.
        """
        self.dns_reply = DNSReply(domain_name_ip_address=domain_ip_address)

        return self
