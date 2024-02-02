from __future__ import annotations

from ipaddress import IPv4Address
from typing import Optional

from primaite.simulator.network.hardware.base import NIC
from primaite.simulator.system.services.arp.arp import ARP, ARPPacket


class HostARP(ARP):
    def get_default_gateway_mac_address(self) -> Optional[str]:
        if self.software_manager.node.default_gateway:
            return self.get_arp_cache_mac_address(self.software_manager.node.default_gateway)

    def get_default_gateway_nic(self) -> Optional[NIC]:
        if self.software_manager.node.default_gateway:
            return self.get_arp_cache_nic(self.software_manager.node.default_gateway)

    def _get_arp_cache_mac_address(
        self, ip_address: IPv4Address, is_reattempt: bool = False, is_default_gateway_attempt: bool = False
    ) -> Optional[str]:
        arp_entry = self.arp.get(ip_address)

        if arp_entry:
            return arp_entry.mac_address
        else:
            if not is_reattempt:
                self.send_arp_request(ip_address)
                return self._get_arp_cache_mac_address(
                    ip_address=ip_address, is_reattempt=True, is_default_gateway_attempt=is_default_gateway_attempt
                )
            else:
                if self.software_manager.node.default_gateway:
                    if not is_default_gateway_attempt:
                        self.send_arp_request(self.software_manager.node.default_gateway)
                        return self._get_arp_cache_mac_address(
                            ip_address=self.software_manager.node.default_gateway, is_reattempt=True, is_default_gateway_attempt=True
                        )
        return None

    def get_arp_cache_mac_address(self, ip_address: IPv4Address) -> Optional[str]:
        """
        Get the MAC address associated with an IP address.

        :param ip_address: The IP address to look up in the cache.
        :return: The MAC address associated with the IP address, or None if not found.
        """
        return self._get_arp_cache_mac_address(ip_address)

    def _get_arp_cache_nic(
        self, ip_address: IPv4Address, is_reattempt: bool = False, is_default_gateway_attempt: bool = False
    ) -> Optional[NIC]:
        arp_entry = self.arp.get(ip_address)

        if arp_entry:
            return self.software_manager.node.nics[arp_entry.nic_uuid]
        else:
            if not is_reattempt:
                self.send_arp_request(ip_address)
                return self._get_arp_cache_nic(
                    ip_address=ip_address, is_reattempt=True, is_default_gateway_attempt=is_default_gateway_attempt
                )
            else:
                if self.software_manager.node.default_gateway:
                    if not is_default_gateway_attempt:
                        self.send_arp_request(self.software_manager.node.default_gateway)
                        return self._get_arp_cache_nic(
                            ip_address=self.software_manager.node.default_gateway, is_reattempt=True, is_default_gateway_attempt=True
                        )
        return None

    def get_arp_cache_nic(self, ip_address: IPv4Address) -> Optional[NIC]:
        """
        Get the NIC associated with an IP address.

        :param ip_address: The IP address to look up in the cache.
        :return: The NIC associated with the IP address, or None if not found.
        """
        return self._get_arp_cache_nic(ip_address)

    def _process_arp_request(self, arp_packet: ARPPacket, from_nic: NIC):
        super()._process_arp_request(arp_packet, from_nic)
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
