import secrets
from ipaddress import IPv4Address
from typing import Dict, Any, Union, Optional, Tuple

from primaite import getLogger
from primaite.simulator.network.hardware.base import NIC
from primaite.simulator.network.protocols.icmp import ICMPPacket, ICMPType
from primaite.simulator.network.transmission.data_link_layer import Frame, EthernetHeader
from primaite.simulator.network.transmission.network_layer import IPProtocol, IPPacket
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.services.service import Service

_LOGGER = getLogger(__name__)


class ICMP(Service):
    request_replies: Dict = {}

    def __init__(self, **kwargs):
        kwargs["name"] = "ICMP"
        kwargs["port"] = Port.NONE
        kwargs["protocol"] = IPProtocol.ICMP
        super().__init__(**kwargs)

    def describe_state(self) -> Dict:
        pass

    def clear(self):
        """Clears the ICMP request replies tracker."""
        self.request_replies.clear()

    def _send_icmp_echo_request(
            self, target_ip_address: IPv4Address, sequence: int = 0, identifier: Optional[int] = None, pings: int = 4
    ) -> Tuple[int, Union[int, None]]:
        """
        Send an ICMP echo request (ping) to a target IP address and manage the sequence and identifier.

        :param target_ip_address: The target IP address to send the ping.
        :param sequence: The sequence number of the echo request. Defaults to 0.
        :param identifier: An optional identifier for the ICMP packet. If None, a default will be used.
        :return: A tuple containing the next sequence number and the identifier, or (0, None) if the target IP address
            was not found in the ARP cache.
        """
        nic = self.software_manager.arp.get_arp_cache_nic(target_ip_address)

        if not nic:
            return pings, None

        # ARP entry exists
        sequence += 1
        target_mac_address = self.software_manager.arp.get_arp_cache_mac_address(target_ip_address)

        src_nic = self.software_manager.arp.get_arp_cache_nic(target_ip_address)

        # Network Layer
        ip_packet = IPPacket(
            src_ip_address=nic.ip_address,
            dst_ip_address=target_ip_address,
            protocol=IPProtocol.ICMP,
        )
        # Data Link Layer
        ethernet_header = EthernetHeader(src_mac_addr=src_nic.mac_address, dst_mac_addr=target_mac_address)
        icmp_packet = ICMPPacket(identifier=identifier, sequence=sequence)
        payload = secrets.token_urlsafe(int(32 / 1.3))  # Standard ICMP 32 bytes size
        frame = Frame(ethernet=ethernet_header, ip=ip_packet, icmp=icmp_packet, payload=payload)
        nic.send_frame(frame)
        return sequence, icmp_packet.identifier

    def ping(self, target_ip_address: Union[IPv4Address, str], pings: int = 4) -> bool:
        """
        Ping an IP address, performing a standard ICMP echo request/response.

        :param target_ip_address: The target IP address to ping.
        :param pings: The number of pings to attempt, default is 4.
        :return: True if the ping is successful, otherwise False.
        """
        if not self._can_perform_action():
            return False
        if target_ip_address.is_loopback:
            self.sys_log.info("Pinging loopback address")
            return any(nic.enabled for nic in self.nics.values())
        self.sys_log.info(f"Pinging {target_ip_address}:", to_terminal=True)
        sequence, identifier = 0, None
        while sequence < pings:
            sequence, identifier = self._send_icmp_echo_request(
                target_ip_address, sequence, identifier, pings
            )
        request_replies = self.software_manager.icmp.request_replies.get(identifier)
        passed = request_replies == pings
        if request_replies:
            self.software_manager.icmp.request_replies.pop(identifier)
        else:
            request_replies = 0
        output = (
            f"Ping statistics for {target_ip_address}: "
            f"Packets: Sent = {pings}, "
            f"Received = {request_replies}, "
            f"Lost = {pings - request_replies} ({(pings - request_replies) / pings * 100}% loss)"
        )
        self.sys_log.info(output, to_terminal=True)

        return passed

    def _process_icmp_echo_request(self, frame: Frame, from_nic: NIC, is_reattempt: bool = False):
        if frame.icmp.icmp_type == ICMPType.ECHO_REQUEST:
            if not is_reattempt:
                self.sys_log.info(f"Received echo request from {frame.ip.src_ip_address}")
            target_mac_address = self.software_manager.arp.get_arp_cache_mac_address(frame.ip.src_ip_address)

            src_nic = self.software_manager.arp.get_arp_cache_nic(frame.ip.src_ip_address)
            if not src_nic:
                self.software_manager.arp.send_arp_request(frame.ip.src_ip_address)
                self.process_icmp(frame=frame, from_nic=from_nic, is_reattempt=True)
                return

            # Network Layer
            ip_packet = IPPacket(
                src_ip_address=src_nic.ip_address, dst_ip_address=frame.ip.src_ip_address, protocol=IPProtocol.ICMP
            )
            # Data Link Layer
            ethernet_header = EthernetHeader(src_mac_addr=src_nic.mac_address, dst_mac_addr=target_mac_address)
            icmp_reply_packet = ICMPPacket(
                icmp_type=ICMPType.ECHO_REPLY,
                icmp_code=0,
                identifier=frame.icmp.identifier,
                sequence=frame.icmp.sequence + 1,
            )
            payload = secrets.token_urlsafe(int(32 / 1.3))  # Standard ICMP 32 bytes size
            frame = Frame(ethernet=ethernet_header, ip=ip_packet, icmp=icmp_reply_packet, payload=payload)
            self.sys_log.info(f"Sending echo reply to {frame.ip.dst_ip_address}")

            src_nic.send_frame(frame)

    def _process_icmp_echo_reply(self, frame: Frame, from_nic: NIC, is_reattempt: bool = False):
        time = frame.transmission_duration()
        time_str = f"{time}ms" if time > 0 else "<1ms"
        self.sys_log.info(
            f"Reply from {frame.ip.src_ip_address}: "
            f"bytes={len(frame.payload)}, "
            f"time={time_str}, "
            f"TTL={frame.ip.ttl}",
            to_terminal=True
        )
        if not self.request_replies.get(frame.icmp.identifier):
            self.request_replies[frame.icmp.identifier] = 0
        self.request_replies[frame.icmp.identifier] += 1

    def receive(self, payload: Any, session_id: str, **kwargs) -> bool:
        frame: Frame = kwargs["frame"]
        from_nic = kwargs["from_nic"]

        if not frame.icmp:
            return False

        if frame.icmp.icmp_type == ICMPType.ECHO_REQUEST:
            self._process_icmp_echo_request(frame, from_nic)
        elif frame.icmp.icmp_type == ICMPType.ECHO_REPLY:
            self._process_icmp_echo_reply(frame, from_nic)
        return True
