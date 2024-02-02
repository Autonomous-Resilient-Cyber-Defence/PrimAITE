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
    arp: Dict[IPv4Address, ARPEntry] = {}

    def __init__(self, **kwargs):
        kwargs["name"] = "ARP"
        kwargs["port"] = Port.ARP
        kwargs["protocol"] = IPProtocol.UDP
        super().__init__(**kwargs)

    def describe_state(self) -> Dict:
        pass

    def show(self, markdown: bool = False):
        """Prints a table of ARC Cache."""
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
        Get the MAC address associated with an IP address.

        :param ip_address: The IP address to look up in the cache.
        :return: The MAC address associated with the IP address, or None if not found.
        """
        pass

    @abstractmethod
    def get_arp_cache_nic(self, ip_address: IPv4Address) -> Optional[NIC]:
        """
        Get the NIC associated with an IP address.

        :param ip_address: The IP address to look up in the cache.
        :return: The NIC associated with the IP address, or None if not found.
        """
        pass

    def send_arp_request(self, target_ip_address: Union[IPv4Address, str]):
        """
        Perform a standard ARP request for a given target IP address.

        Broadcasts the request through all enabled NICs to determine the MAC address corresponding to the target IP
        address. This method can be configured to ignore specific networks when sending out ARP requests,
        which is useful in environments where certain addresses should not be queried.

        :param target_ip_address: The target IP address to send an ARP request for.
        :param ignore_networks: An optional list of IPv4 addresses representing networks to be excluded from the ARP
            request broadcast. Each address in this list indicates a network which will not be queried during the ARP
            request process. This is particularly useful in complex network environments where traffic should be
            minimized or controlled to specific subnets. It is mainly used by the router to prevent ARP requests being
            sent back to their source.
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
                payload=arp_packet, dst_ip_address=target_ip_address, dst_port=Port.ARP, ip_protocol=self.protocol
            )
        else:
            print(f"failed for {target_ip_address}")

    def send_arp_reply(self, arp_reply: ARPPacket, from_nic: NIC):
        """
        Send an ARP reply back through the NIC it came from.

        :param arp_reply: The ARP reply to send.
        :param from_nic: The NIC to send the ARP reply from.
        """
        self.sys_log.info(
            f"Sending ARP reply from {arp_reply.sender_mac_addr}/{arp_reply.sender_ip_address} "
            f"to {arp_reply.target_ip_address}/{arp_reply.target_mac_addr} "
        )
        udp_header = UDPHeader(src_port=Port.ARP, dst_port=Port.ARP)

        ip_packet = IPPacket(
            src_ip_address=arp_reply.sender_ip_address,
            dst_ip_address=arp_reply.target_ip_address,
            protocol=IPProtocol.UDP,
        )

        ethernet_header = EthernetHeader(src_mac_addr=arp_reply.sender_mac_addr, dst_mac_addr=arp_reply.target_mac_addr)

        frame = Frame(ethernet=ethernet_header, ip=ip_packet, udp=udp_header, payload=arp_reply)
        from_nic.send_frame(frame)

    def process_arp_packet(self, from_nic: NIC, arp_packet: ARPPacket):
        """
        Process a received ARP packet, handling both ARP requests and responses.

        If an ARP request is received for the local IP, a response is sent back.
        If an ARP response is received, the ARP cache is updated with the new entry.

        :param from_nic: The NIC that received the ARP packet.
        :param arp_packet: The ARP packet to be processed.
        """

        # Unmatched ARP Request
        if arp_packet.target_ip_address != from_nic.ip_address:
            self.sys_log.info(
                f"Ignoring ARP request for {arp_packet.target_ip_address}. Current IP address is {from_nic.ip_address}"
            )
            return

        # Matched ARP request
        self.add_arp_cache_entry(
            ip_address=arp_packet.sender_ip_address, mac_address=arp_packet.sender_mac_addr, nic=from_nic
        )
        arp_packet = arp_packet.generate_reply(from_nic.mac_address)
        self.send_arp_reply(arp_packet, from_nic)

    @abstractmethod
    def _process_arp_request(self, arp_packet: ARPPacket, from_nic: NIC):
        self.sys_log.info(
            f"Received ARP request for {arp_packet.target_ip_address} from "
            f"{arp_packet.sender_mac_addr}/{arp_packet.sender_ip_address} "
        )

    def _process_arp_reply(self, arp_packet: ARPPacket, from_nic: NIC):
        self.sys_log.info(
            f"Received ARP response for {arp_packet.sender_ip_address} "
            f"from {arp_packet.sender_mac_addr} via NIC {from_nic}"
        )
        self.add_arp_cache_entry(
            ip_address=arp_packet.sender_ip_address, mac_address=arp_packet.sender_mac_addr, nic=from_nic
        )

    def receive(self, payload: Any, session_id: str, **kwargs) -> bool:
        if not isinstance(payload, ARPPacket):
            print("failied on payload check", type(payload))
            return False

        from_nic = kwargs.get("from_nic")
        if payload.request:
            self._process_arp_request(arp_packet=payload, from_nic=from_nic)
        else:
            self._process_arp_reply(arp_packet=payload, from_nic=from_nic)

    def __contains__(self, item: Any) -> bool:
        return item in self.arp
