# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from __future__ import annotations

from ipaddress import IPv4Address
from typing import Optional

from pydantic import BaseModel

from primaite.simulator.network.protocols.packet import DataPacket


class ARPEntry(BaseModel):
    """
    Represents an entry in the ARP cache.

    :param mac_address: The MAC address associated with the IP address.
    :param network_interface_uuid: The UIId of the Network Interface through which the NIC with the IP address is
    reachable.
    """

    mac_address: str
    network_interface_uuid: str


class ARPPacket(DataPacket):
    """
    Represents the ARP layer of a network frame.

    :param request: ARP operation. True if a request, False if a reply.
    :param sender_mac_addr: Sender MAC address.
    :param sender_ip_address: Sender IP address.
    :param target_mac_addr: Target MAC address.
    :param target_ip_address: Target IP address.

    :Example:

    >>> arp_request = ARPPacket(
    ...     sender_mac_addr="aa:bb:cc:dd:ee:ff",
    ...     sender_ip_address=IPv4Address("192.168.0.1"),
    ...     target_ip_address=IPv4Address("192.168.0.2")
    ... )
    >>> arp_response = ARPPacket(
    ...     sender_mac_addr="aa:bb:cc:dd:ee:ff",
    ...     sender_ip_address=IPv4Address("192.168.0.1"),
    ...     target_ip_address=IPv4Address("192.168.0.2")
    ... )
    """

    request: bool = True
    "ARP operation. True if a request, False if a reply."
    sender_mac_addr: str
    "Sender MAC address."
    sender_ip_address: IPv4Address
    "Sender IP address."
    target_mac_addr: Optional[str] = None
    "Target MAC address."
    target_ip_address: IPv4Address
    "Target IP address."

    def generate_reply(self, mac_address: str) -> ARPPacket:
        """
        Generate a new ARPPacket to be sent as a response with a given mac address.

        :param mac_address: The mac_address that was being sought after from the original target IP address.
        :return: A new instance of ARPPacket.
        """
        return ARPPacket(
            request=False,
            sender_ip_address=self.target_ip_address,
            sender_mac_addr=mac_address,
            target_ip_address=self.sender_ip_address,
            target_mac_addr=self.sender_mac_addr,
        )
