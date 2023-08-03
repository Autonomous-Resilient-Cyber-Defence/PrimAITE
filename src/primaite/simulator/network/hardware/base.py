from __future__ import annotations

import re
import secrets
from enum import Enum
from ipaddress import IPv4Address, IPv4Network
from typing import Any, Dict, List, Optional, Tuple, Union

from primaite import getLogger
from primaite.exceptions import NetworkError
from primaite.simulator.core import SimComponent
from primaite.simulator.network.protocols.arp import ARPEntry, ARPPacket
from primaite.simulator.network.transmission.data_link_layer import EthernetHeader, Frame
from primaite.simulator.network.transmission.network_layer import ICMPPacket, ICMPType, IPPacket, IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port, TCPHeader
from primaite.simulator.system.processes.pcap import PCAP
from primaite.simulator.system.processes.sys_log import SysLog

_LOGGER = getLogger(__name__)


def generate_mac_address(oui: Optional[str] = None) -> str:
    """
    Generate a random MAC Address.

    :Example:

    >>> generate_mac_address()
    'ef:7e:97:c8:a8:ce'

    >>> generate_mac_address(oui='aa:bb:cc')
    'aa:bb:cc:42:ba:41'

    :param oui: The Organizationally Unique Identifier (OUI) portion of the MAC address. It should be a string with
        the first 3 bytes (24 bits) in the format "XX:XX:XX".
    :raises ValueError: If the 'oui' is not in the correct format (hexadecimal and 6 characters).
    """
    random_bytes = [secrets.randbits(8) for _ in range(6)]

    if oui:
        oui_pattern = re.compile(r"^([0-9A-Fa-f]{2}[:-]){2}[0-9A-Fa-f]{2}$")
        if not oui_pattern.match(oui):
            msg = f"Invalid oui. The oui should be in the format xx:xx:xx, where x is a hexadecimal digit, got '{oui}'"
            raise ValueError(msg)
        oui_bytes = [int(chunk, 16) for chunk in oui.split(":")]
        mac = oui_bytes + random_bytes[len(oui_bytes) :]
    else:
        mac = random_bytes

    return ":".join(f"{b:02x}" for b in mac)


class NIC(SimComponent):
    """
    Models a Network Interface Card (NIC) in a computer or network device.

    :param ip_address: The IPv4 address assigned to the NIC.
    :param subnet_mask: The subnet mask assigned to the NIC.
    :param gateway: The default gateway IP address for forwarding network traffic to other networks.
    :param mac_address: The MAC address of the NIC. Defaults to a randomly set MAC address.
    :param speed: The speed of the NIC in Mbps (default is 100 Mbps).
    :param mtu: The Maximum Transmission Unit (MTU) of the NIC in Bytes, representing the largest data packet size it
        can handle without fragmentation (default is 1500 B).
    :param wake_on_lan: Indicates if the NIC supports Wake-on-LAN functionality.
    :param dns_servers: List of IP addresses of DNS servers used for name resolution.
    """

    ip_address: IPv4Address
    "The IP address assigned to the NIC for communication on an IP-based network."
    subnet_mask: str
    "The subnet mask assigned to the NIC."
    gateway: IPv4Address
    "The default gateway IP address for forwarding network traffic to other networks. Randomly generated upon creation."
    mac_address: str
    "The MAC address of the NIC. Defaults to a randomly set MAC address."
    speed: int = 100
    "The speed of the NIC in Mbps. Default is 100 Mbps."
    mtu: int = 1500
    "The Maximum Transmission Unit (MTU) of the NIC in Bytes. Default is 1500 B"
    wake_on_lan: bool = False
    "Indicates if the NIC supports Wake-on-LAN functionality."
    dns_servers: List[IPv4Address] = []
    "List of IP addresses of DNS servers used for name resolution."
    connected_node: Optional[Node] = None
    "The Node to which the NIC is connected."
    connected_link: Optional[Link] = None
    "The Link to which the NIC is connected."
    enabled: bool = False
    "Indicates whether the NIC is enabled."
    pcap: Optional[PCAP] = None

    def __init__(self, **kwargs):
        """
        NIC constructor.

        Performs some type conversion the calls ``super().__init__()``. Then performs some checking on the ip_address
        and gateway just to check that it's all been configured correctly.

        :raises ValueError: When the ip_address and gateway are the same. And when the ip_address/subnet mask are a
            network address.
        """
        if not isinstance(kwargs["ip_address"], IPv4Address):
            kwargs["ip_address"] = IPv4Address(kwargs["ip_address"])
        if not isinstance(kwargs["gateway"], IPv4Address):
            kwargs["gateway"] = IPv4Address(kwargs["gateway"])
            if "mac_address" not in kwargs:
                kwargs["mac_address"] = generate_mac_address()
        super().__init__(**kwargs)

        if self.ip_address == self.gateway:
            msg = f"NIC ip address {self.ip_address} cannot be the same as the gateway {self.gateway}"
            _LOGGER.error(msg)
            raise ValueError(msg)
        if self.ip_network.network_address == self.ip_address:
            msg = (
                f"Failed to set IP address {self.ip_address} and subnet mask {self.subnet_mask} as it is a "
                f"network address {self.ip_network.network_address}"
            )
            _LOGGER.error(msg)
            raise ValueError(msg)

    @property
    def ip_network(self) -> IPv4Network:
        """
        Return the IPv4Network of the NIC.

        :return: The IPv4Network from the ip_address/subnet mask.
        """
        return IPv4Network(f"{self.ip_address}/{self.subnet_mask}", strict=False)

    def enable(self):
        """Attempt to enable the NIC."""
        if not self.enabled:
            if self.connected_node:
                if self.connected_node.hardware_state == NodeOperatingState.ON:
                    self.enabled = True
                    _LOGGER.info(f"NIC {self} enabled")
                    self.pcap = PCAP(hostname=self.connected_node.hostname, ip_address=self.ip_address)
                    if self.connected_link:
                        self.connected_link.endpoint_up()
                else:
                    _LOGGER.info(f"NIC {self} cannot be enabled as the endpoint is not turned on")
            else:
                msg = f"NIC {self} cannot be enabled as it is not connected to a Node"
                _LOGGER.error(msg)
                raise NetworkError(msg)

    def disable(self):
        """Disable the NIC."""
        if self.enabled:
            self.enabled = False
            _LOGGER.info(f"NIC {self} disabled")
            if self.connected_link:
                self.connected_link.endpoint_down()

    def connect_link(self, link: Link):
        """
        Connect the NIC to a link.

        :param link: The link to which the NIC is connected.
        :type link: :class:`~primaite.simulator.network.transmission.physical_layer.Link`
        :raise NetworkError: When an attempt to connect a Link is made while the NIC has a connected Link.
        """
        if not self.connected_link:
            if self.connected_link != link:
                _LOGGER.info(f"NIC {self} connected to Link")
                # TODO: Inform the Node that a link has been connected
                self.connected_link = link
            else:
                _LOGGER.warning(f"Cannot connect link to NIC ({self.mac_address}) as it is already connected")
        else:
            msg = f"Cannot connect link to NIC ({self.mac_address}) as it already has a connection"
            _LOGGER.error(msg)
            raise NetworkError(msg)

    def disconnect_link(self):
        """Disconnect the NIC from the connected Link."""
        if self.connected_link.endpoint_a == self:
            self.connected_link.endpoint_a = None
        if self.connected_link.endpoint_b == self:
            self.connected_link.endpoint_b = None
        self.connected_link = None

    def add_dns_server(self, ip_address: IPv4Address):
        """
        Add a DNS server IP address.

        :param ip_address: The IP address of the DNS server to be added.
        :type ip_address: ipaddress.IPv4Address
        """
        pass

    def remove_dns_server(self, ip_address: IPv4Address):
        """
        Remove a DNS server IP Address.

        :param ip_address: The IP address of the DNS server to be removed.
        :type ip_address: ipaddress.IPv4Address
        """
        pass

    def send_frame(self, frame: Frame) -> bool:
        """
        Send a network frame from the NIC to the connected link.

        :param frame: The network frame to be sent.
        :type frame: :class:`~primaite.simulator.network.osi_layers.Frame`
        """
        if self.enabled:
            frame.set_sent_timestamp()
            self.pcap.capture(frame)
            self.connected_link.transmit_frame(sender_nic=self, frame=frame)
            return True
        else:
            # Cannot send Frame as the NIC is not enabled
            return False

    def receive_frame(self, frame: Frame) -> bool:
        """
        Receive a network frame from the connected link if the NIC is enabled.

        The Frame is passed to the Node.

        :param frame: The network frame being received.
        :type frame: :class:`~primaite.simulator.network.osi_layers.Frame`
        """
        if self.enabled:
            frame.decrement_ttl()
            frame.set_received_timestamp()
            self.pcap.capture(frame)
            self.connected_node.receive_frame(frame=frame, from_nic=self)
            return True
        else:
            return False

    def describe_state(self) -> Dict:
        """
        Get the current state of the NIC as a dict.

        :return: A dict containing the current state of the NIC.
        """
        pass

    def apply_action(self, action: str):
        """
        Apply an action to the NIC.

        :param action: The action to be applied.
        :type action: str
        """
        pass

    def __str__(self) -> str:
        return f"{self.mac_address}/{self.ip_address}"


class Link(SimComponent):
    """
    Represents a network link between two network interface cards (NICs).

    :param endpoint_a: The first NIC connected to the Link.
    :type endpoint_a: NIC
    :param endpoint_b: The second NIC connected to the Link.
    :type endpoint_b: NIC
    :param bandwidth: The bandwidth of the Link in Mbps (default is 100 Mbps).
    :type bandwidth: int
    """

    endpoint_a: NIC
    "The first NIC connected to the Link."
    endpoint_b: NIC
    "The second NIC connected to the Link."
    bandwidth: int = 100
    "The bandwidth of the Link in Mbps (default is 100 Mbps)."
    current_load: float = 0.0
    "The current load on the link in Mbps."

    def __init__(self, **kwargs):
        """
        Ensure that endpoint_a and endpoint_b are not the same NIC.

        Connect the link to the NICs after creation.

        :raises ValueError: If endpoint_a and endpoint_b are the same NIC.
        """
        if kwargs["endpoint_a"] == kwargs["endpoint_b"]:
            msg = "endpoint_a and endpoint_b cannot be the same NIC"
            _LOGGER.error(msg)
            raise ValueError(msg)
        super().__init__(**kwargs)
        self.endpoint_a.connect_link(self)
        self.endpoint_b.connect_link(self)
        self.endpoint_up()

    def endpoint_up(self):
        """Let the Link know and endpoint has been brought up."""
        if self.up:
            _LOGGER.info(f"Link {self} up")

    def endpoint_down(self):
        """Let the Link know and endpoint has been brought down."""
        if not self.up:
            self.current_load = 0.0
            _LOGGER.info(f"Link {self} down")

    @property
    def up(self) -> bool:
        """
        Informs whether the link is up.

        This is based upon both NIC endpoints being enabled.
        """
        return self.endpoint_a.enabled and self.endpoint_b.enabled

    def _can_transmit(self, frame: Frame) -> bool:
        if self.up:
            frame_size_Mbits = frame.size_Mbits  # noqa - Leaving it as Mbits as this is how they're expressed
            return self.current_load + frame_size_Mbits <= self.bandwidth
        return False

    def transmit_frame(self, sender_nic: NIC, frame: Frame) -> bool:
        """
        Send a network frame from one NIC to another connected NIC.

        :param sender_nic: The NIC sending the frame.
        :param frame: The network frame to be sent.
        :return: True if the Frame can be sent, otherwise False.
        """
        if self._can_transmit(frame):
            receiver_nic = self.endpoint_a
            if receiver_nic == sender_nic:
                receiver_nic = self.endpoint_b
            frame_size = frame.size_Mbits
            sent = receiver_nic.receive_frame(frame)
            if sent:
                # Frame transmitted successfully
                # Load the frame size on the link
                self.current_load += frame_size
                _LOGGER.info(f"Added {frame_size:.3f} Mbits to {self}, current load {self.current_load:.3f} Mbits")
                return True
            # Received NIC disabled, reply

            return False
        else:
            _LOGGER.info(f"Cannot transmit frame as {self} is at capacity")
            return False

    def reset_component_for_episode(self):
        """
        Link reset function.

        Reset:
         - returns the link current_load to 0.
        """
        self.current_load = 0

    def describe_state(self) -> Dict:
        """
        Get the current state of the Libk as a dict.

        :return: A dict containing the current state of the Link.
        """
        pass

    def apply_action(self, action: str):
        """
        Apply an action to the Link.

        :param action: The action to be applied.
        :type action: str
        """
        pass

    def __str__(self) -> str:
        return f"{self.endpoint_a}<-->{self.endpoint_b}"


class NodeOperatingState(Enum):
    """Enumeration of Node Operating States."""

    OFF = 0
    "The node is powered off."
    ON = 1
    "The node is powered on."
    SHUTTING_DOWN = 2
    "The node is in the process of shutting down."
    BOOTING = 3
    "The node is in the process of booting up."


class Node(SimComponent):
    """
    A basic Node class.

    :param hostname: The node hostname on the network.
    :param hardware_state: The hardware state of the node.
    """

    hostname: str
    "The node hostname on the network."
    operating_state: NodeOperatingState = NodeOperatingState.OFF
    "The hardware state of the node."
    nics: Dict[str, NIC] = {}
    "The NICs on the node."

    accounts: Dict = {}
    "All accounts on the node."
    applications: Dict = {}
    "All applications on the node."
    services: Dict = {}
    "All services on the node."
    processes: Dict = {}
    "All processes on the node."
    file_system: Any = None
    "The nodes file system."
    arp_cache: Dict[IPv4Address, ARPEntry] = {}
    "The ARP cache."
    sys_log: Optional[SysLog] = None

    revealed_to_red: bool = False
    "Informs whether the node has been revealed to a red agent."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sys_log = SysLog(self.hostname)

    def turn_on(self):
        """Turn on the Node."""
        if self.operating_state == NodeOperatingState.OFF:
            self.operating_state = NodeOperatingState.ON
            self.sys_log.info("Turned on")
            for nic in self.nics.values():
                nic.enable()

    def turn_off(self):
        """Turn off the Node."""
        if self.operating_state == NodeOperatingState.ON:
            for nic in self.nics.values():
                nic.disable()
            self.operating_state = NodeOperatingState.OFF
            self.sys_log.info("Turned off")

    def connect_nic(self, nic: NIC):
        """
        Connect a NIC.

        :param nic: The NIC to connect.
        :raise NetworkError: If the NIC is already connected.
        """
        if nic.uuid not in self.nics:
            self.nics[nic.uuid] = nic
            nic.connected_node = self
            self.sys_log.info(f"Connected NIC {nic}")
            if self.operating_state == NodeOperatingState.ON:
                nic.enable()
        else:
            msg = f"Cannot connect NIC {nic} as it is already connected"
            self.sys_log.logger.error(msg)
            _LOGGER.error(msg)
            raise NetworkError(msg)

    def disconnect_nic(self, nic: Union[NIC, str]):
        """
        Disconnect a NIC.

        :param nic: The NIC to Disconnect.
        :raise NetworkError: If the NIC is not connected.
        """
        if isinstance(nic, str):
            nic = self.nics.get(nic)
        if nic or nic.uuid in self.nics:
            self.nics.pop(nic.uuid)
            nic.disable()
            self.sys_log.info(f"Disconnected NIC {nic}")
        else:
            msg = f"Cannot disconnect NIC {nic} as it is not connected"
            self.sys_log.logger.error(msg)
            _LOGGER.error(msg)
            raise NetworkError(msg)

    def _add_arp_cache_entry(self, ip_address: IPv4Address, mac_address: str, nic: NIC):
        """
        Add an ARP entry to the cache.

        :param ip_address: The IP address to be added to the cache.
        :param mac_address: The MAC address associated with the IP address.
        :param nic: The NIC through which the NIC with the IP address is reachable.
        """
        self.sys_log.info(f"Adding ARP cache entry for {mac_address}/{ip_address} via NIC {nic}")
        arp_entry = ARPEntry(mac_address=mac_address, nic_uuid=nic.uuid)
        self.arp_cache[ip_address] = arp_entry

    def _remove_arp_cache_entry(self, ip_address: IPv4Address):
        """
        Remove an ARP entry from the cache.

        :param ip_address: The IP address to be removed from the cache.
        """
        if ip_address in self.arp_cache:
            del self.arp_cache[ip_address]

    def _get_arp_cache_mac_address(self, ip_address: IPv4Address) -> Optional[str]:
        """
        Get the MAC address associated with an IP address.

        :param ip_address: The IP address to look up in the cache.
        :return: The MAC address associated with the IP address, or None if not found.
        """
        arp_entry = self.arp_cache.get(ip_address)
        if arp_entry:
            return arp_entry.mac_address

    def _get_arp_cache_nic(self, ip_address: IPv4Address) -> Optional[NIC]:
        """
        Get the NIC associated with an IP address.

        :param ip_address: The IP address to look up in the cache.
        :return: The NIC associated with the IP address, or None if not found.
        """
        arp_entry = self.arp_cache.get(ip_address)
        if arp_entry:
            return self.nics[arp_entry.nic_uuid]

    def _clear_arp_cache(self):
        """Clear the entire ARP cache."""
        self.arp_cache.clear()

    def _send_arp_request(self, target_ip_address: Union[IPv4Address, str]):
        """Perform a standard ARP request for a given target IP address."""
        for nic in self.nics.values():
            if nic.enabled:
                self.sys_log.info(f"Sending ARP request from NIC {nic} for ip {target_ip_address}")
                tcp_header = TCPHeader(src_port=Port.ARP, dst_port=Port.ARP)

                # Network Layer
                ip_packet = IPPacket(
                    src_ip=nic.ip_address,
                    dst_ip=target_ip_address,
                )
                # Data Link Layer
                ethernet_header = EthernetHeader(src_mac_addr=nic.mac_address, dst_mac_addr="ff:ff:ff:ff:ff:ff")
                arp_packet = ARPPacket(
                    sender_ip=nic.ip_address, sender_mac_addr=nic.mac_address, target_ip=target_ip_address
                )
                frame = Frame(ethernet=ethernet_header, ip=ip_packet, tcp=tcp_header, arp=arp_packet)
                nic.send_frame(frame)

    def process_arp_packet(self, from_nic: NIC, arp_packet: ARPPacket):
        """
        Process an ARP packet.

        # TODO: This will become a service that sits on the Node.

        :param from_nic: The NIC the arp packet was received at.
        :param arp_packet:The ARP packet to process.
        """
        if arp_packet.request:
            self.sys_log.info(
                f"Received ARP request for {arp_packet.target_ip} from "
                f"{arp_packet.sender_mac_addr}/{arp_packet.sender_ip} "
            )
            if arp_packet.target_ip == from_nic.ip_address:
                self._add_arp_cache_entry(
                    ip_address=arp_packet.sender_ip, mac_address=arp_packet.sender_mac_addr, nic=from_nic
                )
                arp_packet = arp_packet.generate_reply(from_nic.mac_address)
                self.sys_log.info(
                    f"Sending ARP reply from {arp_packet.sender_mac_addr}/{arp_packet.sender_ip} "
                    f"to {arp_packet.target_ip}/{arp_packet.target_mac_addr} "
                )

                tcp_header = TCPHeader(src_port=Port.ARP, dst_port=Port.ARP)

                # Network Layer
                ip_packet = IPPacket(
                    src_ip=arp_packet.sender_ip,
                    dst_ip=arp_packet.target_ip,
                )
                # Data Link Layer
                ethernet_header = EthernetHeader(
                    src_mac_addr=arp_packet.sender_mac_addr, dst_mac_addr=arp_packet.target_mac_addr
                )
                frame = Frame(ethernet=ethernet_header, ip=ip_packet, tcp=tcp_header, arp=arp_packet)
                self.send_frame(frame)
            else:
                self.sys_log.info(f"Ignoring ARP request for {arp_packet.target_ip}")
        else:
            self.sys_log.info(
                f"Received ARP response for {arp_packet.sender_ip} from {arp_packet.sender_mac_addr} via NIC {from_nic}"
            )
            self._add_arp_cache_entry(
                ip_address=arp_packet.sender_ip, mac_address=arp_packet.sender_mac_addr, nic=from_nic
            )

    def process_icmp(self, frame: Frame):
        """
        Process an ICMP packet.

        # TODO: This will become a service that sits on the Node.

        :param frame: The Frame containing the icmp packet to process.
        """
        if frame.icmp.icmp_type == ICMPType.ECHO_REQUEST:
            self.sys_log.info(f"Received echo request from {frame.ip.src_ip}")
            target_mac_address = self._get_arp_cache_mac_address(frame.ip.src_ip)
            src_nic = self._get_arp_cache_nic(frame.ip.src_ip)
            tcp_header = TCPHeader(src_port=Port.ARP, dst_port=Port.ARP)

            # Network Layer
            ip_packet = IPPacket(src_ip=src_nic.ip_address, dst_ip=frame.ip.src_ip, protocol=IPProtocol.ICMP)
            # Data Link Layer
            ethernet_header = EthernetHeader(src_mac_addr=src_nic.mac_address, dst_mac_addr=target_mac_address)
            icmp_reply_packet = ICMPPacket(
                icmp_type=ICMPType.ECHO_REPLY,
                icmp_code=0,
                identifier=frame.icmp.identifier,
                sequence=frame.icmp.sequence + 1,
            )
            frame = Frame(ethernet=ethernet_header, ip=ip_packet, tcp=tcp_header, icmp=icmp_reply_packet)
            self.sys_log.info(f"Sending echo reply to {frame.ip.src_ip}")
            src_nic.send_frame(frame)
        elif frame.icmp.icmp_type == ICMPType.ECHO_REPLY:
            self.sys_log.info(f"Received echo reply from {frame.ip.src_ip}")

    def _ping(
        self, target_ip_address: IPv4Address, sequence: int = 0, identifier: Optional[int] = None
    ) -> Tuple[int, Union[int, None]]:
        nic = self._get_arp_cache_nic(target_ip_address)
        if nic:
            sequence += 1
            target_mac_address = self._get_arp_cache_mac_address(target_ip_address)
            src_nic = self._get_arp_cache_nic(target_ip_address)
            tcp_header = TCPHeader(src_port=Port.ARP, dst_port=Port.ARP)

            # Network Layer
            ip_packet = IPPacket(
                src_ip=nic.ip_address,
                dst_ip=target_ip_address,
                protocol=IPProtocol.ICMP,
            )
            # Data Link Layer
            ethernet_header = EthernetHeader(src_mac_addr=src_nic.mac_address, dst_mac_addr=target_mac_address)
            icmp_packet = ICMPPacket(identifier=identifier, sequence=sequence)
            frame = Frame(ethernet=ethernet_header, ip=ip_packet, tcp=tcp_header, icmp=icmp_packet)
            self.sys_log.info(f"Sending echo request to {target_ip_address}")
            nic.send_frame(frame)
            return sequence, icmp_packet.identifier
        else:
            self.sys_log.info(f"No entry in ARP cache for {target_ip_address}")
            self._send_arp_request(target_ip_address)
            return 0, None

    def ping(self, target_ip_address: Union[IPv4Address, str], pings: int = 4) -> bool:
        """
        Ping an IP address.

        Performs a standard ICMP echo request/response four times.

        :param target_ip_address: The target IP address to ping.
        :return: True if successful, otherwise False.
        """
        if not isinstance(target_ip_address, IPv4Address):
            target_ip_address = IPv4Address(target_ip_address)
        if self.operating_state == NodeOperatingState.ON:
            self.sys_log.info(f"Attempting to ping {target_ip_address}")
            sequence, identifier = 0, None
            while sequence < pings:
                sequence, identifier = self._ping(target_ip_address, sequence, identifier)
            return True
        self.sys_log.info("Ping failed as the node is turned off")
        return False

    def send_frame(self, frame: Frame):
        """
        Send a Frame from the Node to the connected NIC.

        :param frame: The Frame to be sent.
        """
        nic: NIC = self._get_arp_cache_nic(frame.ip.dst_ip)
        nic.send_frame(frame)

    def receive_frame(self, frame: Frame, from_nic: NIC):
        """
        Receive a Frame from the connected NIC.

        The Frame is passed to up to the SessionManager.

        :param frame: The Frame being received.
        """
        if frame.ip.protocol == IPProtocol.TCP:
            if frame.tcp.src_port == Port.ARP:
                self.process_arp_packet(from_nic=from_nic, arp_packet=frame.arp)
        elif frame.ip.protocol == IPProtocol.UDP:
            pass
        elif frame.ip.protocol == IPProtocol.ICMP:
            self.process_icmp(frame=frame)

    def describe_state(self) -> Dict:
        """Describe the state of a Node."""
        pass
