# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from __future__ import annotations

from abc import abstractmethod
from typing import Any, Dict, Optional, Union

from prettytable import MARKDOWN, PrettyTable

from primaite.simulator.network.hardware.base import NetworkInterface
from primaite.simulator.network.protocols.arp import ARPEntry, ARPPacket
from primaite.simulator.system.services.service import Service
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.ipv4_address import IPV4Address
from primaite.utils.validation.port import PORT_LOOKUP


class ARP(Service, identifier="ARP"):
    """
    The ARP (Address Resolution Protocol) Service.

    Manages ARP for resolving network layer addresses into link layer addresses. It maintains an ARP cache,
    sends ARP requests and replies, and processes incoming ARP packets.
    """

    config: "ARP.ConfigSchema" = None

    arp: Dict[IPV4Address, ARPEntry] = {}

    class ConfigSchema(Service.ConfigSchema):
        """ConfigSchema for ARP."""

        type: str = "ARP"

    def __init__(self, **kwargs):
        kwargs["name"] = "ARP"
        kwargs["port"] = PORT_LOOKUP["ARP"]
        kwargs["protocol"] = PROTOCOL_LOOKUP["UDP"]
        super().__init__(**kwargs)

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        :return: Current state of this object and child objects.
        """
        state = super().describe_state()
        state.update({str(ip): arp_entry.mac_address for ip, arp_entry in self.arp.items()})

        return super().describe_state()

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
                    self.software_manager.node.network_interfaces[arp.network_interface_uuid].mac_address,
                ]
            )
        print(table)

    def clear(self):
        """Clears the arp cache."""
        self.arp.clear()

    def get_default_gateway_network_interface(self) -> Optional[NetworkInterface]:
        """Not used at the parent ARP level. Should return None when there is no override by child class."""
        return None

    def add_arp_cache_entry(
        self, ip_address: IPV4Address, mac_address: str, network_interface: NetworkInterface, override: bool = False
    ):
        """
        Add an ARP entry to the cache.

        If an entry for the given IP address already exists, the entry is only updated if the `override` parameter is
        set to True.

        :param ip_address: The IP address to be added to the cache.
        :param mac_address: The MAC address associated with the IP address.
        :param network_interface: The NIC through which the NIC with the IP address is reachable.
        :param override: If True, an existing entry for the IP address will be overridden. Default is False.
        """
        for _network_interface in self.software_manager.node.network_interfaces.values():
            if _network_interface.ip_address == ip_address:
                return
        if override or not self.arp.get(ip_address):
            self.sys_log.info(f"Adding ARP cache entry for {mac_address}/{ip_address} via NIC {network_interface}")
            arp_entry = ARPEntry(mac_address=mac_address, network_interface_uuid=network_interface.uuid)

            self.arp[ip_address] = arp_entry

    @abstractmethod
    def get_arp_cache_mac_address(self, ip_address: IPV4Address) -> Optional[str]:
        """
        Retrieves the MAC address associated with a given IP address from the ARP cache.

        :param ip_address: The IP address to look up.
        :return: The associated MAC address, if found. Otherwise, returns None.
        """
        pass

    @abstractmethod
    def get_arp_cache_network_interface(self, ip_address: IPV4Address) -> Optional[NetworkInterface]:
        """
        Retrieves the NIC associated with a given IP address from the ARP cache.

        :param ip_address: The IP address to look up.
        :return: The associated NIC, if found. Otherwise, returns None.
        """
        pass

    def send_arp_request(self, target_ip_address: Union[IPV4Address, str]):
        """
        Sends an ARP request to resolve the MAC address of a target IP address.

        :param target_ip_address: The target IP address for which the MAC address is being requested.
        """
        if target_ip_address in self.arp:
            return

        use_default_gateway = True
        for network_interface in self.software_manager.node.network_interfaces.values():
            if target_ip_address in network_interface.ip_network:
                use_default_gateway = False
                break

        if use_default_gateway:
            if self.software_manager.node.default_gateway:
                target_ip_address = self.software_manager.node.default_gateway
            else:
                return

        outbound_network_interface = self.software_manager.session_manager.resolve_outbound_network_interface(
            target_ip_address
        )
        if outbound_network_interface:
            # ensure we are not attempting to find the network address or broadcast address (not useable IPs)
            if target_ip_address == outbound_network_interface.ip_network.network_address:
                self.sys_log.info(f"Cannot send ARP request to a network address {str(target_ip_address)}")
                return
            if target_ip_address == outbound_network_interface.ip_network.broadcast_address:
                self.sys_log.info(f"Cannot send ARP request to a broadcast address {str(target_ip_address)}")
                return

            self.sys_log.info(f"Sending ARP request from NIC {outbound_network_interface} for ip {target_ip_address}")
            arp_packet = ARPPacket(
                sender_ip_address=outbound_network_interface.ip_address,
                sender_mac_addr=outbound_network_interface.mac_address,
                target_ip_address=target_ip_address,
            )
            self.software_manager.session_manager.receive_payload_from_software_manager(
                payload=arp_packet, dst_ip_address=target_ip_address, dst_port=self.port, ip_protocol=self.protocol
            )
        else:
            self.sys_log.warning(
                "Cannot send ARP request as there is no outbound Network Interface to use. Try configuring the default "
                "gateway."
            )

    def send_arp_reply(self, arp_reply: ARPPacket):
        """
        Sends an ARP reply in response to an ARP request.

        :param arp_reply: The ARP packet containing the reply.
        """
        outbound_network_interface = self.software_manager.session_manager.resolve_outbound_network_interface(
            arp_reply.target_ip_address
        )
        if outbound_network_interface:
            self.sys_log.info(
                f"Sending ARP reply from {arp_reply.sender_mac_addr}/{arp_reply.sender_ip_address} "
                f"to {arp_reply.target_ip_address}/{arp_reply.target_mac_addr} "
            )
            self.software_manager.session_manager.receive_payload_from_software_manager(
                payload=arp_reply,
                dst_ip_address=arp_reply.target_ip_address,
                dst_port=self.port,
                ip_protocol=self.protocol,
            )
        else:
            self.sys_log.warning(
                "Cannot send ARP reply as there is no outbound Network Interface to use. Try configuring the default "
                "gateway."
            )

    @abstractmethod
    def _process_arp_request(self, arp_packet: ARPPacket, from_network_interface: NetworkInterface):
        """
        Processes an incoming ARP request.

        :param arp_packet: The ARP packet containing the request.
        :param from_network_interface: The NIC that received the ARP request.
        """
        self.sys_log.info(
            f"Received ARP request for {arp_packet.target_ip_address} from "
            f"{arp_packet.sender_mac_addr}/{arp_packet.sender_ip_address} "
        )

    def _process_arp_reply(self, arp_packet: ARPPacket, from_network_interface: NetworkInterface):
        """
        Processes an incoming ARP reply.

        :param arp_packet: The ARP packet containing the reply.
        :param from_network_interface: The NIC that received the ARP reply.
        """
        self.sys_log.info(
            f"Received ARP response for {arp_packet.sender_ip_address} "
            f"from {arp_packet.sender_mac_addr} via Network Interface {from_network_interface}"
        )
        self.add_arp_cache_entry(
            ip_address=arp_packet.sender_ip_address,
            mac_address=arp_packet.sender_mac_addr,
            network_interface=from_network_interface,
        )

    def receive(self, payload: Any, session_id: str, **kwargs) -> bool:
        """
        Processes received data, handling ARP packets.

        :param payload: The payload received.
        :param session_id: The session ID associated with the received data.
        :param kwargs: Additional keyword arguments.
        :return: True if the payload was processed successfully, otherwise False.
        """
        if not super().receive(payload, session_id, **kwargs):
            return False

        from_network_interface = kwargs["from_network_interface"]
        if payload.request:
            self._process_arp_request(arp_packet=payload, from_network_interface=from_network_interface)
        else:
            self._process_arp_reply(arp_packet=payload, from_network_interface=from_network_interface)
        return True

    def __contains__(self, item: Any) -> bool:
        """
        Checks if an item is in the ARP cache.

        :param item: The item to check.
        :return: True if the item is in the cache, otherwise False.
        """
        return item in self.arp
