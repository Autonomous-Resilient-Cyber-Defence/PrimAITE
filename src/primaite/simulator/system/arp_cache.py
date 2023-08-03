from ipaddress import IPv4Address

from pydantic import BaseModel


class ARPCacheService(BaseModel):
    def __init__(self, node):
        super().__init__()
        self.node = node

    def _add_arp_cache_entry(self, ip_address: IPv4Address, mac_address: str, nic: NIC):
        ...

    def _remove_arp_cache_entry(self, ip_address: IPv4Address):
        ...

    def _get_arp_cache_mac_address(self, ip_address: IPv4Address) -> Optional[str]:
        ...

    def _get_arp_cache_nic(self, ip_address: IPv4Address) -> Optional[NIC]:
        ...

    def _clear_arp_cache(self):
        ...

    def _send_arp_request(self, target_ip_address: Union[IPv4Address, str]):
        ...

    def process_arp_packet(self, from_nic: NIC, arp_packet: ARPPacket):
        ...