from __future__ import annotations

from abc import abstractmethod
from ipaddress import IPv4Address
from typing import Any, Dict, Optional, Union

from prettytable import MARKDOWN, PrettyTable

from primaite.simulator.network.hardware.base import NIC
from primaite.simulator.network.protocols.arp import ARPEntry, ARPPacket
from primaite.simulator.network.transmission.data_link_layer import EthernetHeader, Frame
from primaite.simulator.network.transmission.network_layer import IPPacket, IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port, UDPHeader
from primaite.simulator.system.services.service import Service


class ARP(Service):
    """
    The ARP (Address Resolution Protocol) Service.

    Manages ARP for resolving network layer addresses into link layer addresses. It maintains an ARP cache,
    sends ARP requests and replies, and processes incoming ARP packets.
    """
    arp: Dict[IPv4Address, ARPEntry] = {}

    def __init__(self, **kwargs):
        kwargs["name"] = "ARP"
        kwargs["port"] = Port.ARP
        kwargs["protocol"] = IPProtocol.UDP
        super().__init__(**kwargs)

    def describe_state(self) -> Dict:
        pass

    def show(self, markdown: bool = False):
        """
        Prints the current state of the ARP cache in a table format.

        :param markdown: If True, format the output as Markdown. Otherwise, use plain text.
        """
        table = PrettyTable(["IP Address", "MAC Address", "Via"])
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"{self.sys_log.hostname} ARP Cache"
        for ip, arp in self.arp.items():
            table.add_row(
                [
                    str(ip),
                    arp.mac_address,
                    self.software_manager.node.nics[arp.nic_uuid].mac_address,
                ]
            )
        print(table)

    def clear(self):
        """Clears the arp cache."""
        self.arp.clear()

    def add_arp_cache_entry(self, ip_address: IPv4Address, mac_address: str, nic: NIC, override: bool = False):
        """
        Add an ARP entry to the cache.

        If an entry for the given IP address already exists, the entry is only updated if the `override` parameter is
        set to True.

        :param ip_address: The IP address to be added to the cache.
        :param mac_address: The MAC address associated with the IP address.
        :param nic: The NIC through which the NIC with the IP address is reachable.
        :param override: If True, an existing entry for the IP address will be overridden. Default is False.
        """
        for _nic in self.software_manager.node.nics.values():
            if _nic.ip_address == ip_address:
                return
        if override or not self.arp.get(ip_address):
            self.sys_log.info(f"Adding ARP cache entry for {mac_address}/{ip_address} via NIC {nic}")
            arp_entry = ARPEntry(mac_address=mac_address, nic_uuid=nic.uuid)

            self.arp[ip_address] = arp_entry

    @abstractmethod
    def get_arp_cache_mac_address(self, ip_address: IPv4Address) -> Optional[str]:
        """
        Retrieves the MAC address associated with a given IP address from the ARP cache.

        :param ip_address: The IP address to look up.
        :return: The associated MAC address, if found. Otherwise, returns None.
        """
        pass

    @abstractmethod
    def get_arp_cache_nic(self, ip_address: IPv4Address) -> Optional[NIC]:
        """
        Retrieves the NIC associated with a given IP address from the ARP cache.

        :param ip_address: The IP address to look up.
        :return: The associated NIC, if found. Otherwise, returns None.
        """
        pass

    def send_arp_request(self, target_ip_address: Union[IPv4Address, str]):
        """
        Sends an ARP request to resolve the MAC address of a target IP address.

        :param target_ip_address: The target IP address for which the MAC address is being requested.
        """
        outbound_nic = self.software_manager.session_manager.resolve_outbound_nic(target_ip_address)
        if outbound_nic:
            self.sys_log.info(f"Sending ARP request from NIC {outbound_nic} for ip {target_ip_address}")
            arp_packet = ARPPacket(
                sender_ip_address=outbound_nic.ip_address,
                sender_mac_addr=outbound_nic.mac_address,
                target_ip_address=target_ip_address,
            )
            self.software_manager.session_manager.receive_payload_from_software_manager(
                payload=arp_packet, dst_ip_address=target_ip_address, dst_port=self.port, ip_protocol=self.protocol
            )
        else:
            self.sys_log.error(
                "Cannot send ARP request as there is no outbound NIC to use. Try configuring the default gateway."
            )

    def send_arp_reply(self, arp_reply: ARPPacket):
        """
        Sends an ARP reply in response to an ARP request.

        :param arp_reply: The ARP packet containing the reply.
        :param from_nic: The NIC from which the ARP reply is sent.
        """

        outbound_nic = self.software_manager.session_manager.resolve_outbound_nic(arp_reply.target_ip_address)
        if outbound_nic:
            self.sys_log.info(
                f"Sending ARP reply from {arp_reply.sender_mac_addr}/{arp_reply.sender_ip_address} "
                f"to {arp_reply.target_ip_address}/{arp_reply.target_mac_addr} "
            )
            self.software_manager.session_manager.receive_payload_from_software_manager(
                payload=arp_reply,
                dst_ip_address=arp_reply.target_ip_address,
                dst_port=self.port,
                ip_protocol=self.protocol
            )
        else:
            self.sys_log.error(
                "Cannot send ARP reply as there is no outbound NIC to use. Try configuring the default gateway."
            )


    @abstractmethod
    def _process_arp_request(self, arp_packet: ARPPacket, from_nic: NIC):
        """
        Processes an incoming ARP request.

        :param arp_packet: The ARP packet containing the request.
        :param from_nic: The NIC that received the ARP request.
        """
        self.sys_log.info(
            f"Received ARP request for {arp_packet.target_ip_address} from "
            f"{arp_packet.sender_mac_addr}/{arp_packet.sender_ip_address} "
        )

    def _process_arp_reply(self, arp_packet: ARPPacket, from_nic: NIC):
        """
        Processes an incoming ARP reply.

        :param arp_packet: The ARP packet containing the reply.
        :param from_nic: The NIC that received the ARP reply.
        """
        self.sys_log.info(
            f"Received ARP response for {arp_packet.sender_ip_address} "
            f"from {arp_packet.sender_mac_addr} via NIC {from_nic}"
        )
        self.add_arp_cache_entry(
            ip_address=arp_packet.sender_ip_address, mac_address=arp_packet.sender_mac_addr, nic=from_nic
        )

    def receive(self, payload: Any, session_id: str, **kwargs) -> bool:
        """
        Processes received data, handling ARP packets.

        :param payload: The payload received.
        :param session_id: The session ID associated with the received data.
        :param kwargs: Additional keyword arguments.
        :return: True if the payload was processed successfully, otherwise False.
        """
        if not isinstance(payload, ARPPacket):
            print("failied on payload check", type(payload))
            return False

        from_nic = kwargs.get("from_nic")
        if payload.request:
            self._process_arp_request(arp_packet=payload, from_nic=from_nic)
        else:
            self._process_arp_reply(arp_packet=payload, from_nic=from_nic)

    def __contains__(self, item: Any) -> bool:
        """
        Checks if an item is in the ARP cache.

        :param item: The item to check.
        :return: True if the item is in the cache, otherwise False.
        """
        return item in self.arp
