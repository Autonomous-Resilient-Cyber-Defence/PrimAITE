from __future__ import annotations

import re
import secrets
from ipaddress import IPv4Address, IPv4Network
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from prettytable import MARKDOWN, PrettyTable

from primaite import getLogger
from primaite.exceptions import NetworkError
from primaite.simulator import SIM_OUTPUT
from primaite.simulator.core import RequestManager, RequestType, SimComponent
from primaite.simulator.domain.account import Account
from primaite.simulator.file_system.file_system import FileSystem
from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.protocols.arp import ARPEntry, ARPPacket
from primaite.simulator.network.transmission.data_link_layer import EthernetHeader, Frame
from primaite.simulator.network.transmission.network_layer import ICMPPacket, ICMPType, IPPacket, IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port, TCPHeader
from primaite.simulator.system.applications.application import Application
from primaite.simulator.system.core.packet_capture import PacketCapture
from primaite.simulator.system.core.session_manager import SessionManager
from primaite.simulator.system.core.software_manager import SoftwareManager
from primaite.simulator.system.core.sys_log import SysLog
from primaite.simulator.system.processes.process import Process
from primaite.simulator.system.services.service import Service

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
            _LOGGER.error(msg)
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
    subnet_mask: IPv4Address
    "The subnet mask assigned to the NIC."
    mac_address: str
    "The MAC address of the NIC. Defaults to a randomly set MAC address. Randomly generated upon creation."
    speed: int = 100
    "The speed of the NIC in Mbps. Default is 100 Mbps."
    mtu: int = 1500
    "The Maximum Transmission Unit (MTU) of the NIC in Bytes. Default is 1500 B"
    wake_on_lan: bool = False
    "Indicates if the NIC supports Wake-on-LAN functionality."
    _connected_node: Optional[Node] = None
    "The Node to which the NIC is connected."
    _port_num_on_node: Optional[int] = None
    "Which port number is assigned on this NIC"
    _connected_link: Optional[Link] = None
    "The Link to which the NIC is connected."
    enabled: bool = False
    "Indicates whether the NIC is enabled."
    pcap: Optional[PacketCapture] = None

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
        if "mac_address" not in kwargs:
            kwargs["mac_address"] = generate_mac_address()
        super().__init__(**kwargs)

        if self.ip_network.network_address == self.ip_address:
            msg = (
                f"Failed to set IP address {self.ip_address} and subnet mask {self.subnet_mask} as it is a "
                f"network address {self.ip_network.network_address}"
            )
            _LOGGER.error(msg)
            raise ValueError(msg)

        self.set_original_state()

    def set_original_state(self):
        """Sets the original state."""
        vals_to_include = {"ip_address", "subnet_mask", "mac_address", "speed", "mtu", "wake_on_lan", "enabled"}
        self._original_state = self.model_dump(include=vals_to_include)

    def reset_component_for_episode(self, episode: int):
        """Reset the original state of the SimComponent."""
        super().reset_component_for_episode(episode)
        if episode and self.pcap:
            self.pcap.current_episode = episode
            self.pcap.setup_logger()
        self.enable()

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        Please see :py:meth:`primaite.simulator.core.SimComponent.describe_state` for a more detailed explanation.

        :return: Current state of this object and child objects.
        :rtype: Dict
        """
        state = super().describe_state()
        state.update(
            {
                "ip_address": str(self.ip_address),
                "subnet_mask": str(self.subnet_mask),
                "mac_address": self.mac_address,
                "speed": self.speed,
                "mtu": self.mtu,
                "wake_on_lan": self.wake_on_lan,
                "enabled": self.enabled,
            }
        )
        return state

    def _init_request_manager(self) -> RequestManager:
        rm = super()._init_request_manager()

        rm.add_request("enable", RequestType(func=lambda request, context: self.enable()))
        rm.add_request("disable", RequestType(func=lambda request, context: self.disable()))

        return rm

    @property
    def ip_network(self) -> IPv4Network:
        """
        Return the IPv4Network of the NIC.

        :return: The IPv4Network from the ip_address/subnet mask.
        """
        return IPv4Network(f"{self.ip_address}/{self.subnet_mask}", strict=False)

    def enable(self):
        """Attempt to enable the NIC."""
        if self.enabled:
            return
        if not self._connected_node:
            _LOGGER.debug(f"NIC {self} cannot be enabled as it is not connected to a Node")
            return
        if self._connected_node.operating_state != NodeOperatingState.ON:
            self._connected_node.sys_log.error(f"NIC {self} cannot be enabled as the endpoint is not turned on")
            return
        if not self._connected_link:
            _LOGGER.debug(f"NIC {self} cannot be enabled as it is not connected to a Link")
            return

        self.enabled = True
        self._connected_node.sys_log.info(f"NIC {self} enabled")
        self.pcap = PacketCapture(hostname=self._connected_node.hostname, ip_address=self.ip_address)
        if self._connected_link:
            self._connected_link.endpoint_up()

    def disable(self):
        """Disable the NIC."""
        if not self.enabled:
            return

        self.enabled = False
        if self._connected_node:
            self._connected_node.sys_log.info(f"NIC {self} disabled")
        else:
            _LOGGER.debug(f"NIC {self} disabled")
        if self._connected_link:
            self._connected_link.endpoint_down()

    def connect_link(self, link: Link):
        """
        Connect the NIC to a link.

        :param link: The link to which the NIC is connected.
        :type link: :class:`~primaite.simulator.network.transmission.physical_layer.Link`
        """
        if self._connected_link:
            _LOGGER.error(f"Cannot connect Link to NIC ({self.mac_address}) as it already has a connection")
            return

        if self._connected_link == link:
            _LOGGER.error(f"Cannot connect Link to NIC ({self.mac_address}) as it is already connected")
            return

        # TODO: Inform the Node that a link has been connected
        self._connected_link = link
        self.enable()
        _LOGGER.debug(f"NIC {self} connected to Link {link}")

    def disconnect_link(self):
        """Disconnect the NIC from the connected Link."""
        if self._connected_link.endpoint_a == self:
            self._connected_link.endpoint_a = None
        if self._connected_link.endpoint_b == self:
            self._connected_link.endpoint_b = None
        self._connected_link = None

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
            self._connected_link.transmit_frame(sender_nic=self, frame=frame)
            return True
        # Cannot send Frame as the NIC is not enabled
        return False

    def receive_frame(self, frame: Frame) -> bool:
        """
        Receive a network frame from the connected link, processing it if the NIC is enabled.

        This method decrements the Time To Live (TTL) of the frame, captures it using PCAP (Packet Capture), and checks
        if the frame is either a broadcast or destined for this NIC. If the frame is acceptable, it is passed to the
        connected node. The method also handles the discarding of frames with TTL expired and logs this event.

        The frame's reception is based on various conditions:
        - If the NIC is disabled, the frame is not processed.
        - If the TTL of the frame reaches zero after decrement, it is discarded and logged.
        - If the frame is a broadcast or its destination MAC/IP address matches this NIC's, it is accepted.
        - All other frames are dropped and logged or printed to the console.

        :param frame: The network frame being received. This should be an instance of the Frame class.
        :return: Returns True if the frame is processed and passed to the node, False otherwise.
        """
        if self.enabled:
            frame.decrement_ttl()
            if frame.ip and frame.ip.ttl < 1:
                self._connected_node.sys_log.info("Frame discarded as TTL limit reached")
                return False
            frame.set_received_timestamp()
            self.pcap.capture(frame)
            # If this destination or is broadcast
            accept_frame = False

            # Check if it's a broadcast:
            if frame.ethernet.dst_mac_addr == "ff:ff:ff:ff:ff:ff":
                if frame.ip.dst_ip_address in {self.ip_address, self.ip_network.broadcast_address}:
                    accept_frame = True
            else:
                if frame.ethernet.dst_mac_addr == self.mac_address:
                    accept_frame = True

            if accept_frame:
                self._connected_node.receive_frame(frame=frame, from_nic=self)
                return True
        return False

    def __str__(self) -> str:
        return f"{self.mac_address}/{self.ip_address}"


class SwitchPort(SimComponent):
    """
    Models a switch port in a network switch device.

    :param mac_address: The MAC address of the SwitchPort. Defaults to a randomly set MAC address.
    :param speed: The speed of the SwitchPort in Mbps (default is 100 Mbps).
    :param mtu: The Maximum Transmission Unit (MTU) of the SwitchPort in Bytes, representing the largest data packet
        size it can handle without fragmentation (default is 1500 B).
    """

    port_num: int = 1
    mac_address: str
    "The MAC address of the SwitchPort. Defaults to a randomly set MAC address."
    speed: int = 100
    "The speed of the SwitchPort in Mbps. Default is 100 Mbps."
    mtu: int = 1500
    "The Maximum Transmission Unit (MTU) of the SwitchPort in Bytes. Default is 1500 B"
    _connected_node: Optional[Node] = None
    "The Node to which the SwitchPort is connected."
    _port_num_on_node: Optional[int] = None
    "The port num on the connected node."
    _connected_link: Optional[Link] = None
    "The Link to which the SwitchPort is connected."
    enabled: bool = False
    "Indicates whether the SwitchPort is enabled."
    pcap: Optional[PacketCapture] = None

    def __init__(self, **kwargs):
        """The SwitchPort constructor."""
        if "mac_address" not in kwargs:
            kwargs["mac_address"] = generate_mac_address()
        super().__init__(**kwargs)

        self.set_original_state()

    def set_original_state(self):
        """Sets the original state."""
        vals_to_include = {"port_num", "mac_address", "speed", "mtu", "enabled"}
        self._original_state = self.model_dump(include=vals_to_include)
        super().set_original_state()

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        Please see :py:meth:`primaite.simulator.core.SimComponent.describe_state` for a more detailed explanation.

        :return: Current state of this object and child objects.
        :rtype: Dict
        """
        state = super().describe_state()
        state.update(
            {
                "mac_address": self.mac_address,
                "speed": self.speed,
                "mtu": self.mtu,
                "enabled": self.enabled,
            }
        )
        return state

    def enable(self):
        """Attempt to enable the SwitchPort."""
        if self.enabled:
            return

        if not self._connected_node:
            _LOGGER.error(f"SwitchPort {self} cannot be enabled as it is not connected to a Node")
            return

        if self._connected_node.operating_state != NodeOperatingState.ON:
            self._connected_node.sys_log.info(f"SwitchPort {self} cannot be enabled as the endpoint is not turned on")
            return

        self.enabled = True
        self._connected_node.sys_log.info(f"SwitchPort {self} enabled")
        self.pcap = PacketCapture(hostname=self._connected_node.hostname, switch_port_number=self.port_num)
        if self._connected_link:
            self._connected_link.endpoint_up()

    def disable(self):
        """Disable the SwitchPort."""
        if not self.enabled:
            return
        self.enabled = False
        if self._connected_node:
            self._connected_node.sys_log.info(f"SwitchPort {self} disabled")
        else:
            _LOGGER.debug(f"SwitchPort {self} disabled")
        if self._connected_link:
            self._connected_link.endpoint_down()

    def connect_link(self, link: Link):
        """
        Connect the SwitchPort to a link.

        :param link: The link to which the SwitchPort is connected.
        """
        if self._connected_link:
            _LOGGER.error(f"Cannot connect link to SwitchPort {self.mac_address} as it already has a connection")
            return

        if self._connected_link == link:
            _LOGGER.error(f"Cannot connect Link to SwitchPort {self.mac_address} as it is already connected")
            return

        # TODO: Inform the Switch that a link has been connected
        self._connected_link = link
        _LOGGER.debug(f"SwitchPort {self} connected to Link {link}")
        self.enable()

    def disconnect_link(self):
        """Disconnect the SwitchPort from the connected Link."""
        if self._connected_link.endpoint_a == self:
            self._connected_link.endpoint_a = None
        if self._connected_link.endpoint_b == self:
            self._connected_link.endpoint_b = None
        self._connected_link = None

    def send_frame(self, frame: Frame) -> bool:
        """
        Send a network frame from the SwitchPort to the connected link.

        :param frame: The network frame to be sent.
        """
        if self.enabled:
            self.pcap.capture(frame)
            self._connected_link.transmit_frame(sender_nic=self, frame=frame)
            return True
        # Cannot send Frame as the SwitchPort is not enabled
        return False

    def receive_frame(self, frame: Frame) -> bool:
        """
        Receive a network frame from the connected link if the SwitchPort is enabled.

        The Frame is passed to the Node.

        :param frame: The network frame being received.
        """
        if self.enabled:
            frame.decrement_ttl()
            if frame.ip and frame.ip.ttl < 1:
                self._connected_node.sys_log.info("Frame discarded as TTL limit reached")
                return False
            self.pcap.capture(frame)
            connected_node: Node = self._connected_node
            connected_node.forward_frame(frame=frame, incoming_port=self)
            return True
        return False

    def __str__(self) -> str:
        return f"{self.mac_address}"


class Link(SimComponent):
    """
    Represents a network link between NIC<-->NIC, NIC<-->SwitchPort, or SwitchPort<-->SwitchPort.

    :param endpoint_a: The first NIC or SwitchPort connected to the Link.
    :param endpoint_b: The second NIC or SwitchPort connected to the Link.
    :param bandwidth: The bandwidth of the Link in Mbps (default is 100 Mbps).
    """

    endpoint_a: Union[NIC, SwitchPort]
    "The first NIC or SwitchPort connected to the Link."
    endpoint_b: Union[NIC, SwitchPort]
    "The second NIC or SwitchPort connected to the Link."
    bandwidth: float = 100.0
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
            msg = "endpoint_a and endpoint_b cannot be the same NIC or SwitchPort"
            _LOGGER.error(msg)
            raise ValueError(msg)
        super().__init__(**kwargs)
        self.endpoint_a.connect_link(self)
        self.endpoint_b.connect_link(self)
        self.endpoint_up()

        self.set_original_state()

    def set_original_state(self):
        """Sets the original state."""
        vals_to_include = {"bandwidth", "current_load"}
        self._original_state = self.model_dump(include=vals_to_include)
        super().set_original_state()

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        Please see :py:meth:`primaite.simulator.core.SimComponent.describe_state` for a more detailed explanation.

        :return: Current state of this object and child objects.
        :rtype: Dict
        """
        state = super().describe_state()
        state.update(
            {
                "endpoint_a": self.endpoint_a.uuid,  # TODO: consider if using UUID is the best way to do this
                "endpoint_b": self.endpoint_b.uuid,  # TODO: consider if using UUID is the best way to do this
                "bandwidth": self.bandwidth,
                "current_load": self.current_load,
            }
        )
        return state

    @property
    def current_load_percent(self) -> str:
        """Get the current load formatted as a percentage string."""
        return f"{self.current_load / self.bandwidth:.5f}%"

    def endpoint_up(self):
        """Let the Link know and endpoint has been brought up."""
        if self.is_up:
            _LOGGER.debug(f"Link {self} up")

    def endpoint_down(self):
        """Let the Link know and endpoint has been brought down."""
        if not self.is_up:
            self.current_load = 0.0
            _LOGGER.debug(f"Link {self} down")

    @property
    def is_up(self) -> bool:
        """
        Informs whether the link is up.

        This is based upon both NIC endpoints being enabled.
        """
        return self.endpoint_a.enabled and self.endpoint_b.enabled

    def _can_transmit(self, frame: Frame) -> bool:
        if self.is_up:
            frame_size_Mbits = frame.size_Mbits  # noqa - Leaving it as Mbits as this is how they're expressed
            # return self.current_load + frame_size_Mbits <= self.bandwidth
            # TODO: re add this check once packet size limiting and MTU checks are implemented
            return True
        return False

    def transmit_frame(self, sender_nic: Union[NIC, SwitchPort], frame: Frame) -> bool:
        """
        Send a network frame from one NIC or SwitchPort to another connected NIC or SwitchPort.

        :param sender_nic: The NIC or SwitchPort sending the frame.
        :param frame: The network frame to be sent.
        :return: True if the Frame can be sent, otherwise False.
        """
        can_transmit = self._can_transmit(frame)
        if not can_transmit:
            _LOGGER.debug(f"Cannot transmit frame as {self} is at capacity")
            return False

        receiver = self.endpoint_a
        if receiver == sender_nic:
            receiver = self.endpoint_b
        frame_size = frame.size_Mbits

        if receiver.receive_frame(frame):
            # Frame transmitted successfully
            # Load the frame size on the link
            self.current_load += frame_size
            _LOGGER.debug(
                f"Added {frame_size:.3f} Mbits to {self}, current load {self.current_load:.3f} Mbits "
                f"({self.current_load_percent})"
            )
            return True
        return False

    def __str__(self) -> str:
        return f"{self.endpoint_a}<-->{self.endpoint_b}"


class ARPCache:
    """
    The ARPCache (Address Resolution Protocol) class.

    Responsible for maintaining a mapping between IP addresses and MAC addresses (ARP cache) for the network. It
    provides methods for looking up, adding, and removing entries, and for processing ARPPackets.
    """

    def __init__(self, sys_log: "SysLog"):
        """
        Initialize an ARP (Address Resolution Protocol) cache.

        :param sys_log: The nodes sys log.
        """
        self.sys_log: "SysLog" = sys_log
        self.arp: Dict[IPv4Address, ARPEntry] = {}
        self.nics: Dict[str, "NIC"] = {}

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
                    self.nics[arp.nic_uuid].mac_address,
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
        for _nic in self.nics.values():
            if _nic.ip_address == ip_address:
                return
        if override or not self.arp.get(ip_address):
            self.sys_log.info(f"Adding ARP cache entry for {mac_address}/{ip_address} via NIC {nic}")
            arp_entry = ARPEntry(mac_address=mac_address, nic_uuid=nic.uuid)

            self.arp[ip_address] = arp_entry

    def _remove_arp_cache_entry(self, ip_address: IPv4Address):
        """
        Remove an ARP entry from the cache.

        :param ip_address: The IP address to be removed from the cache.
        """
        if ip_address in self.arp:
            del self.arp[ip_address]

    def get_arp_cache_mac_address(self, ip_address: IPv4Address) -> Optional[str]:
        """
        Get the MAC address associated with an IP address.

        :param ip_address: The IP address to look up in the cache.
        :return: The MAC address associated with the IP address, or None if not found.
        """
        arp_entry = self.arp.get(ip_address)
        if arp_entry:
            return arp_entry.mac_address

    def get_arp_cache_nic(self, ip_address: IPv4Address) -> Optional[NIC]:
        """
        Get the NIC associated with an IP address.

        :param ip_address: The IP address to look up in the cache.
        :return: The NIC associated with the IP address, or None if not found.
        """
        arp_entry = self.arp.get(ip_address)

        if arp_entry:
            return self.nics[arp_entry.nic_uuid]

    def clear_arp_cache(self):
        """Clear the entire ARP cache, removing all stored entries."""
        self.arp.clear()

    def send_arp_request(
        self, target_ip_address: Union[IPv4Address, str], ignore_networks: Optional[List[IPv4Address]] = None
    ):
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
        for nic in self.nics.values():
            use_nic = True
            if ignore_networks:
                for ipv4 in ignore_networks:
                    if ipv4 in nic.ip_network:
                        use_nic = False
            if nic.enabled and use_nic:
                self.sys_log.info(f"Sending ARP request from NIC {nic} for ip {target_ip_address}")
                tcp_header = TCPHeader(src_port=Port.ARP, dst_port=Port.ARP)

                # Network Layer
                ip_packet = IPPacket(
                    src_ip_address=nic.ip_address,
                    dst_ip_address=target_ip_address,
                )
                # Data Link Layer
                ethernet_header = EthernetHeader(src_mac_addr=nic.mac_address, dst_mac_addr="ff:ff:ff:ff:ff:ff")
                arp_packet = ARPPacket(
                    sender_ip_address=nic.ip_address,
                    sender_mac_addr=nic.mac_address,
                    target_ip_address=target_ip_address,
                )
                frame = Frame(ethernet=ethernet_header, ip=ip_packet, tcp=tcp_header, arp=arp_packet)
                nic.send_frame(frame)

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
        tcp_header = TCPHeader(src_port=Port.ARP, dst_port=Port.ARP)

        ip_packet = IPPacket(
            src_ip_address=arp_reply.sender_ip_address,
            dst_ip_address=arp_reply.target_ip_address,
        )

        ethernet_header = EthernetHeader(src_mac_addr=arp_reply.sender_mac_addr, dst_mac_addr=arp_reply.target_mac_addr)

        frame = Frame(ethernet=ethernet_header, ip=ip_packet, tcp=tcp_header, arp=arp_reply)
        from_nic.send_frame(frame)

    def process_arp_packet(self, from_nic: NIC, arp_packet: ARPPacket):
        """
        Process a received ARP packet, handling both ARP requests and responses.

        If an ARP request is received for the local IP, a response is sent back.
        If an ARP response is received, the ARP cache is updated with the new entry.

        :param from_nic: The NIC that received the ARP packet.
        :param arp_packet: The ARP packet to be processed.
        """
        # ARP Reply
        if not arp_packet.request:
            self.sys_log.info(
                f"Received ARP response for {arp_packet.sender_ip_address} "
                f"from {arp_packet.sender_mac_addr} via NIC {from_nic}"
            )
            self.add_arp_cache_entry(
                ip_address=arp_packet.sender_ip_address, mac_address=arp_packet.sender_mac_addr, nic=from_nic
            )
            return

        # ARP Request
        self.sys_log.info(
            f"Received ARP request for {arp_packet.target_ip_address} from "
            f"{arp_packet.sender_mac_addr}/{arp_packet.sender_ip_address} "
        )

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

    def __contains__(self, item: Any) -> bool:
        return item in self.arp


class ICMP:
    """
    The ICMP (Internet Control Message Protocol) class.

    Provides functionalities for managing and handling ICMP packets, including echo requests and replies.
    """

    def __init__(self, sys_log: SysLog, arp_cache: ARPCache):
        """
        Initialize the ICMP (Internet Control Message Protocol) service.

        :param sys_log: The system log to store system messages and information.
        :param arp_cache: The ARP cache for resolving IP to MAC address mappings.
        """
        self.sys_log: SysLog = sys_log
        self.arp: ARPCache = arp_cache
        self.request_replies = {}

    def clear(self):
        """Clears the ICMP request replies tracker."""
        self.request_replies.clear()

    def process_icmp(self, frame: Frame, from_nic: NIC, is_reattempt: bool = False):
        """
        Process an ICMP packet, including handling echo requests and replies.

        :param frame: The Frame containing the ICMP packet to process.
        """
        if frame.icmp.icmp_type == ICMPType.ECHO_REQUEST:
            if not is_reattempt:
                self.sys_log.info(f"Received echo request from {frame.ip.src_ip_address}")
            target_mac_address = self.arp.get_arp_cache_mac_address(frame.ip.src_ip_address)

            src_nic = self.arp.get_arp_cache_nic(frame.ip.src_ip_address)
            if not src_nic:
                self.arp.send_arp_request(frame.ip.src_ip_address)
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
        elif frame.icmp.icmp_type == ICMPType.ECHO_REPLY:
            time = frame.transmission_duration()
            time_str = f"{time}ms" if time > 0 else "<1ms"
            self.sys_log.info(
                f"Reply from {frame.ip.src_ip_address}: "
                f"bytes={len(frame.payload)}, "
                f"time={time_str}, "
                f"TTL={frame.ip.ttl}"
            )
            if not self.request_replies.get(frame.icmp.identifier):
                self.request_replies[frame.icmp.identifier] = 0
            self.request_replies[frame.icmp.identifier] += 1

    def ping(
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
        nic = self.arp.get_arp_cache_nic(target_ip_address)
        # TODO: Eventually this ARP request needs to be done elsewhere. It's not the responsibility of the
        # ping function to handle ARP lookups

        # Already tried once and cannot get ARP entry, stop trying
        if sequence == -1:
            if not nic:
                return 4, None
            else:
                sequence = 0

        # No existing ARP entry
        if not nic:
            self.sys_log.info(f"No entry in ARP cache for {target_ip_address}")
            self.arp.send_arp_request(target_ip_address)
            return -1, None

        # ARP entry exists
        sequence += 1
        target_mac_address = self.arp.get_arp_cache_mac_address(target_ip_address)
        src_nic = self.arp.get_arp_cache_nic(target_ip_address)
        tcp_header = TCPHeader(src_port=Port.ARP, dst_port=Port.ARP)

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
        frame = Frame(ethernet=ethernet_header, ip=ip_packet, tcp=tcp_header, icmp=icmp_packet, payload=payload)
        nic.send_frame(frame)
        return sequence, icmp_packet.identifier


class Node(SimComponent):
    """
    A basic Node class that represents a node on the network.

    This class manages the state of the node, including the NICs (Network Interface Cards), accounts, applications,
    services, processes, file system, and various managers like ARP, ICMP, SessionManager, and SoftwareManager.

    :param hostname: The node hostname on the network.
    :param operating_state: The node operating state, either ON or OFF.
    """

    hostname: str
    "The node hostname on the network."
    default_gateway: Optional[IPv4Address] = None
    "The default gateway IP address for forwarding network traffic to other networks."
    operating_state: NodeOperatingState = NodeOperatingState.OFF
    "The hardware state of the node."
    nics: Dict[str, NIC] = {}
    "The NICs on the node."
    ethernet_port: Dict[int, NIC] = {}
    "The NICs on the node by port id."
    dns_server: Optional[IPv4Address] = None
    "List of IP addresses of DNS servers used for name resolution."

    accounts: Dict[str, Account] = {}
    "All accounts on the node."
    applications: Dict[str, Application] = {}
    "All applications on the node."
    services: Dict[str, Service] = {}
    "All services on the node."
    processes: Dict[str, Process] = {}
    "All processes on the node."
    file_system: FileSystem
    "The nodes file system."
    root: Path
    "Root directory for simulation output."
    sys_log: SysLog
    arp: ARPCache
    icmp: ICMP
    session_manager: SessionManager
    software_manager: SoftwareManager

    revealed_to_red: bool = False
    "Informs whether the node has been revealed to a red agent."

    start_up_duration: int = 3
    "Time steps needed for the node to start up."

    start_up_countdown: int = 0
    "Time steps needed until node is booted up."

    shut_down_duration: int = 3
    "Time steps needed for the node to shut down."

    shut_down_countdown: int = 0
    "Time steps needed until node is shut down."

    is_resetting: bool = False
    "If true, the node will try turning itself off then back on again."

    node_scan_duration: int = 10
    "How many timesteps until the whole node is scanned. Default 10 time steps."

    node_scan_countdown: int = 0
    "Time steps until scan is complete"

    red_scan_countdown: int = 0
    "Time steps until reveal to red scan is complete."

    def __init__(self, **kwargs):
        """
        Initialize the Node with various components and managers.

        This method initializes the ARP cache, ICMP handler, session manager, and software manager if they are not
        provided.
        """
        if kwargs.get("default_gateway"):
            if not isinstance(kwargs["default_gateway"], IPv4Address):
                kwargs["default_gateway"] = IPv4Address(kwargs["default_gateway"])
        if not kwargs.get("sys_log"):
            kwargs["sys_log"] = SysLog(kwargs["hostname"])
        if not kwargs.get("arp"):
            kwargs["arp"] = ARPCache(sys_log=kwargs.get("sys_log"))
        if not kwargs.get("icmp"):
            kwargs["icmp"] = ICMP(sys_log=kwargs.get("sys_log"), arp_cache=kwargs.get("arp"))
        if not kwargs.get("session_manager"):
            kwargs["session_manager"] = SessionManager(sys_log=kwargs.get("sys_log"), arp_cache=kwargs.get("arp"))
        if not kwargs.get("root"):
            kwargs["root"] = SIM_OUTPUT.path / kwargs["hostname"]
        if not kwargs.get("file_system"):
            kwargs["file_system"] = FileSystem(sys_log=kwargs["sys_log"], sim_root=kwargs["root"] / "fs")
        if not kwargs.get("software_manager"):
            kwargs["software_manager"] = SoftwareManager(
                parent_node=self,
                sys_log=kwargs.get("sys_log"),
                session_manager=kwargs.get("session_manager"),
                file_system=kwargs.get("file_system"),
                dns_server=kwargs.get("dns_server"),
            )
        super().__init__(**kwargs)
        self.arp.nics = self.nics
        self.session_manager.software_manager = self.software_manager
        self._install_system_software()
        self.set_original_state()

    def set_original_state(self):
        """Sets the original state."""
        for software in self.software_manager.software.values():
            software.set_original_state()

        self.file_system.set_original_state()

        for nic in self.nics.values():
            nic.set_original_state()

        vals_to_include = {
            "hostname",
            "default_gateway",
            "operating_state",
            "revealed_to_red",
            "start_up_duration",
            "start_up_countdown",
            "shut_down_duration",
            "shut_down_countdown",
            "is_resetting",
            "node_scan_duration",
            "node_scan_countdown",
            "red_scan_countdown",
        }
        self._original_state = self.model_dump(include=vals_to_include)

    def reset_component_for_episode(self, episode: int):
        """Reset the original state of the SimComponent."""
        super().reset_component_for_episode(episode)

        # Reset ARP Cache
        self.arp.clear()

        # Reset ICMP
        self.icmp.clear()

        # Reset Session Manager
        self.session_manager.clear()

        # Reset File System
        self.file_system.reset_component_for_episode(episode)

        # Reset all Nics
        for nic in self.nics.values():
            nic.reset_component_for_episode(episode)

        for software in self.software_manager.software.values():
            software.reset_component_for_episode(episode)

        if episode and self.sys_log:
            self.sys_log.current_episode = episode
            self.sys_log.setup_logger()

    def _init_request_manager(self) -> RequestManager:
        # TODO: I see that this code is really confusing and hard to read right now... I think some of these things will
        # need a better name and better documentation.
        rm = super()._init_request_manager()
        # since there are potentially many services, create an request manager that can map service name
        self._service_request_manager = RequestManager()
        rm.add_request("service", RequestType(func=self._service_request_manager))
        self._nic_request_manager = RequestManager()
        rm.add_request("nic", RequestType(func=self._nic_request_manager))

        rm.add_request("file_system", RequestType(func=self.file_system._request_manager))

        # currently we don't have any applications nor processes, so these will be empty
        self._process_request_manager = RequestManager()
        rm.add_request("process", RequestType(func=self._process_request_manager))
        self._application_request_manager = RequestManager()
        rm.add_request("application", RequestType(func=self._application_request_manager))

        rm.add_request("scan", RequestType(func=lambda request, context: self.reveal_to_red()))

        rm.add_request("shutdown", RequestType(func=lambda request, context: self.power_off()))
        rm.add_request("startup", RequestType(func=lambda request, context: self.power_on()))
        rm.add_request("reset", RequestType(func=lambda request, context: self.reset()))  # TODO implement node reset
        rm.add_request("logon", RequestType(func=lambda request, context: ...))  # TODO implement logon request
        rm.add_request("logoff", RequestType(func=lambda request, context: ...))  # TODO implement logoff request

        self._os_request_manager = RequestManager()
        self._os_request_manager.add_request("scan", RequestType(func=lambda request, context: self.scan()))
        rm.add_request("os", RequestType(func=self._os_request_manager))

        return rm

    def _install_system_software(self):
        """Install System Software - software that is usually provided with the OS."""
        pass

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        Please see :py:meth:`primaite.simulator.core.SimComponent.describe_state` for a more detailed explanation.

        :return: Current state of this object and child objects.
        :rtype: Dict
        """
        state = super().describe_state()
        state.update(
            {
                "hostname": self.hostname,
                "operating_state": self.operating_state.value,
                "NICs": {eth_num: nic.describe_state() for eth_num, nic in self.ethernet_port.items()},
                # "switch_ports": {uuid, sp for uuid, sp in self.switch_ports.items()},
                "file_system": self.file_system.describe_state(),
                "applications": {app.name: app.describe_state() for app in self.applications.values()},
                "services": {svc.name: svc.describe_state() for svc in self.services.values()},
                "process": {proc.name: proc.describe_state() for proc in self.processes.values()},
                "revealed_to_red": self.revealed_to_red,
            }
        )
        return state

    def show(self, markdown: bool = False, component: Literal["NIC", "OPEN_PORTS"] = "NIC"):
        """A multi-use .show function that accepts either NIC or OPEN_PORTS."""
        if component == "NIC":
            self._show_nic(markdown)
        elif component == "OPEN_PORTS":
            self._show_open_ports(markdown)

    def _show_open_ports(self, markdown: bool = False):
        """Prints a table of the open ports on the Node."""
        table = PrettyTable(["Port", "Name"])
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"{self.hostname} Open Ports"
        for port in self.software_manager.get_open_ports():
            table.add_row([port.value, port.name])
        print(table)

    def _show_nic(self, markdown: bool = False):
        """Prints a table of the NICs on the Node."""
        table = PrettyTable(["Port", "MAC Address", "Address", "Speed", "Status"])
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"{self.hostname} Network Interface Cards"
        for port, nic in self.ethernet_port.items():
            table.add_row(
                [
                    port,
                    nic.mac_address,
                    f"{nic.ip_address}/{nic.ip_network.prefixlen}",
                    nic.speed,
                    "Enabled" if nic.enabled else "Disabled",
                ]
            )
        print(table)

    def apply_timestep(self, timestep: int):
        """
        Apply a single timestep of simulation dynamics to this node.

        In this instance, if any multi-timestep processes are currently occurring
        (such as starting up or shutting down), then they are brought one step closer to
        being finished.

        :param timestep: The current timestep number. (Amount of time since simulation episode began)
        :type timestep: int
        """
        super().apply_timestep(timestep=timestep)

        # count down to boot up
        if self.start_up_countdown > 0:
            self.start_up_countdown -= 1
        else:
            if self.operating_state == NodeOperatingState.BOOTING:
                self.operating_state = NodeOperatingState.ON
                self.sys_log.info(f"{self.hostname}: Turned on")
                for nic in self.nics.values():
                    if nic._connected_link:
                        nic.enable()

                self._start_up_actions()

        # count down to shut down
        if self.shut_down_countdown > 0:
            self.shut_down_countdown -= 1
        else:
            if self.operating_state == NodeOperatingState.SHUTTING_DOWN:
                self.operating_state = NodeOperatingState.OFF
                self.sys_log.info(f"{self.hostname}: Turned off")
                self._shut_down_actions()

                # if resetting turn back on
                if self.is_resetting:
                    self.is_resetting = False
                    self.power_on()

        # time steps which require the node to be on
        if self.operating_state == NodeOperatingState.ON:
            # node scanning
            if self.node_scan_countdown > 0:
                self.node_scan_countdown -= 1

                if self.node_scan_countdown == 0:
                    # scan everything!
                    for process_id in self.processes:
                        self.processes[process_id].scan()

                    # scan services
                    for service_id in self.services:
                        self.services[service_id].scan()

                    # scan applications
                    for application_id in self.applications:
                        self.applications[application_id].scan()

                    # scan file system
                    self.file_system.scan(instant_scan=True)

            if self.red_scan_countdown > 0:
                self.red_scan_countdown -= 1

                if self.red_scan_countdown == 0:
                    # scan processes
                    for process_id in self.processes:
                        self.processes[process_id].reveal_to_red()

                    # scan services
                    for service_id in self.services:
                        self.services[service_id].reveal_to_red()

                    # scan applications
                    for application_id in self.applications:
                        self.applications[application_id].reveal_to_red()

                    # scan file system
                    self.file_system.reveal_to_red(instant_scan=True)

            for process_id in self.processes:
                self.processes[process_id].apply_timestep(timestep=timestep)

            for service_id in self.services:
                self.services[service_id].apply_timestep(timestep=timestep)

            for application_id in self.applications:
                self.applications[application_id].apply_timestep(timestep=timestep)

            self.file_system.apply_timestep(timestep=timestep)

    def scan(self) -> None:
        """
        Scan the node and all the items within it.

        Scans the:
            - Processes
            - Services
            - Applications
            - Folders
            - Files

        to the red agent.
        """
        self.node_scan_countdown = self.node_scan_duration

    def reveal_to_red(self) -> None:
        """
        Reveals the node and all the items within it to the red agent.

        Set all the:
            - Processes
            - Services
            - Applications
            - Folders
            - Files

        `revealed_to_red` to `True`.
        """
        self.red_scan_countdown = self.node_scan_duration

    def power_on(self):
        """Power on the Node, enabling its NICs if it is in the OFF state."""
        if self.operating_state == NodeOperatingState.OFF:
            self.operating_state = NodeOperatingState.BOOTING
            self.start_up_countdown = self.start_up_duration

        if self.start_up_duration <= 0:
            self.operating_state = NodeOperatingState.ON
            self._start_up_actions()
            self.sys_log.info("Turned on")
            for nic in self.nics.values():
                if nic._connected_link:
                    nic.enable()

    def power_off(self):
        """Power off the Node, disabling its NICs if it is in the ON state."""
        if self.operating_state == NodeOperatingState.ON:
            for nic in self.nics.values():
                nic.disable()
            self.operating_state = NodeOperatingState.SHUTTING_DOWN
            self.shut_down_countdown = self.shut_down_duration

        if self.shut_down_duration <= 0:
            self._shut_down_actions()
            self.operating_state = NodeOperatingState.OFF
            self.sys_log.info("Turned off")

    def reset(self):
        """
        Resets the node.

        Powers off the node and sets is_resetting to True.
        Applying more timesteps will eventually turn the node back on.
        """
        if not self.operating_state.ON:
            self.sys_log.error(f"Cannot reset {self.hostname} - node is not turned on.")
        else:
            self.is_resetting = True
            self.sys_log.info(f"Resetting {self.hostname}...")
            self.power_off()

    def connect_nic(self, nic: NIC):
        """
        Connect a NIC (Network Interface Card) to the node.

        :param nic: The NIC to connect.
        :raise NetworkError: If the NIC is already connected.
        """
        if nic.uuid not in self.nics:
            self.nics[nic.uuid] = nic
            new_nic_num = len(self.nics)
            self.ethernet_port[new_nic_num] = nic
            nic._connected_node = self
            nic._port_num_on_node = new_nic_num
            nic.parent = self
            self.sys_log.info(f"Connected NIC {nic}")
            if self.operating_state == NodeOperatingState.ON:
                nic.enable()
            self._nic_request_manager.add_request(new_nic_num, RequestType(func=nic._request_manager))
        else:
            msg = f"Cannot connect NIC {nic} as it is already connected"
            self.sys_log.logger.error(msg)
            _LOGGER.error(msg)
            raise NetworkError(msg)

    def disconnect_nic(self, nic: Union[NIC, str]):
        """
        Disconnect a NIC (Network Interface Card) from the node.

        :param nic: The NIC to Disconnect, or its UUID.
        :raise NetworkError: If the NIC is not connected.
        """
        if isinstance(nic, str):
            nic = self.nics.get(nic)
        if nic or nic.uuid in self.nics:
            nic_num = -1
            for port, _nic in self.ethernet_port.items():
                if nic == _nic:
                    self.ethernet_port.pop(port)
                    nic_num = port
                    break
            self.nics.pop(nic.uuid)
            nic.parent = None
            nic.disable()
            self.sys_log.info(f"Disconnected NIC {nic}")
            if nic_num != -1:
                self._nic_request_manager.remove_request(nic_num)
        else:
            msg = f"Cannot disconnect NIC {nic} as it is not connected"
            self.sys_log.logger.error(msg)
            _LOGGER.error(msg)
            raise NetworkError(msg)

    def ping(self, target_ip_address: Union[IPv4Address, str], pings: int = 4) -> bool:
        """
        Ping an IP address, performing a standard ICMP echo request/response.

        :param target_ip_address: The target IP address to ping.
        :param pings: The number of pings to attempt, default is 4.
        :return: True if the ping is successful, otherwise False.
        """
        if self.operating_state == NodeOperatingState.ON:
            if not isinstance(target_ip_address, IPv4Address):
                target_ip_address = IPv4Address(target_ip_address)
            if target_ip_address.is_loopback:
                self.sys_log.info("Pinging loopback address")
                return any(nic.enabled for nic in self.nics.values())
            if self.operating_state == NodeOperatingState.ON:
                self.sys_log.info(f"Pinging {target_ip_address}:")
                sequence, identifier = 0, None
                while sequence < pings:
                    sequence, identifier = self.icmp.ping(target_ip_address, sequence, identifier, pings)
                request_replies = self.icmp.request_replies.get(identifier)
                passed = request_replies == pings
                if request_replies:
                    self.icmp.request_replies.pop(identifier)
                else:
                    request_replies = 0
                self.sys_log.info(
                    f"Ping statistics for {target_ip_address}: "
                    f"Packets: Sent = {pings}, "
                    f"Received = {request_replies}, "
                    f"Lost = {pings - request_replies} ({(pings - request_replies) / pings * 100}% loss)"
                )
                return passed
        return False

    def send_frame(self, frame: Frame):
        """
        Send a Frame from the Node to the connected NIC.

        :param frame: The Frame to be sent.
        """
        if self.operating_state == NodeOperatingState.ON:
            nic: NIC = self._get_arp_cache_nic(frame.ip.dst_ip_address)
        nic.send_frame(frame)

    def receive_frame(self, frame: Frame, from_nic: NIC):
        """
        Receive a Frame from the connected NIC and process it.

        Depending on the protocol, the frame is passed to the appropriate handler such as ARP or ICMP, or up to the
        SessionManager if no code manager exists.

        :param frame: The Frame being received.
        :param from_nic: The NIC that received the frame.
        """
        if self.operating_state == NodeOperatingState.ON:
            if frame.ip:
                if frame.ip.src_ip_address in self.arp:
                    self.arp.add_arp_cache_entry(
                        ip_address=frame.ip.src_ip_address, mac_address=frame.ethernet.src_mac_addr, nic=from_nic
                    )
            if frame.ip.protocol == IPProtocol.ICMP:
                self.icmp.process_icmp(frame=frame, from_nic=from_nic)
                return
            # Check if the destination port is open on the Node
            if frame.tcp.dst_port in self.software_manager.get_open_ports():
                # accept thr frame as the port is open
                if frame.tcp.src_port == Port.ARP:
                    self.arp.process_arp_packet(from_nic=from_nic, arp_packet=frame.arp)
                else:
                    self.session_manager.receive_frame(frame)
            else:
                # denied as port closed
                self.sys_log.info(f"Ignoring frame for port {frame.tcp.dst_port.value} from {frame.ip.src_ip_address}")
                # TODO: do we need to do anything more here?
                pass

    def install_service(self, service: Service) -> None:
        """
        Install a service on this node.

        :param service: Service instance that has not been installed on any node yet.
        :type service: Service
        """
        if service in self:
            _LOGGER.warning(f"Can't add service {service.name} to node {self.hostname}. It's already installed.")
            return
        self.services[service.uuid] = service
        service.parent = self
        service.install()  # Perform any additional setup, such as creating files for this service on the node.
        self.sys_log.info(f"Installed service {service.name}")
        _LOGGER.debug(f"Added service {service.name} to node {self.hostname}")
        self._service_request_manager.add_request(service.name, RequestType(func=service._request_manager))

    def uninstall_service(self, service: Service) -> None:
        """
        Uninstall and completely remove service from this node.

        :param service: Service object that is currently associated with this node.
        :type service: Service
        """
        if service not in self:
            _LOGGER.warning(f"Can't remove service {service.name} from node {self.hostname}. It's not installed.")
            return
        service.uninstall()  # Perform additional teardown, such as removing files or restarting the machine.
        self.services.pop(service.uuid)
        service.parent = None
        self.sys_log.info(f"Uninstalled service {service.name}")
        _LOGGER.info(f"Removed service {service.name} from node {self.hostname}")
        self._service_request_manager.remove_request(service.name)

    def install_application(self, application: Application) -> None:
        """
        Install an application on this node.

        :param application: Application instance that has not been installed on any node yet.
        :type application: Application
        """
        if application in self:
            _LOGGER.warning(
                f"Can't add application {application.name} to node {self.hostname}. It's already installed."
            )
            return
        self.applications[application.uuid] = application
        application.parent = self
        self.sys_log.info(f"Installed application {application.name}")
        _LOGGER.debug(f"Added application {application.name} to node {self.hostname}")
        self._application_request_manager.add_request(application.name, RequestType(func=application._request_manager))

    def uninstall_application(self, application: Application) -> None:
        """
        Uninstall and completely remove application from this node.

        :param application: Application object that is currently associated with this node.
        :type application: Application
        """
        if application not in self:
            _LOGGER.warning(
                f"Can't remove application {application.name} from node {self.hostname}. It's not installed."
            )
            return
        self.applications.pop(application.uuid)
        application.parent = None
        self.sys_log.info(f"Uninstalled application {application.name}")
        _LOGGER.info(f"Removed application {application.name} from node {self.hostname}")
        self._application_request_manager.remove_request(application.name)

    def _shut_down_actions(self):
        """Actions to perform when the node is shut down."""
        # Turn off all the services in the node
        for service_id in self.services:
            self.services[service_id].stop()

        # Turn off all the applications in the node
        for app_id in self.applications:
            self.applications[app_id].close()

        # Turn off all processes in the node
        # for process_id in self.processes:
        #     self.processes[process_id]

    def _start_up_actions(self):
        """Actions to perform when the node is starting up."""
        # Turn on all the services in the node
        for service_id in self.services:
            self.services[service_id].start()

        # Turn on all the applications in the node
        for app_id in self.applications:
            self.applications[app_id].run()

        # Turn off all processes in the node
        # for process_id in self.processes:
        #     self.processes[process_id]

    def __contains__(self, item: Any) -> bool:
        if isinstance(item, Service):
            return item.uuid in self.services
        return None
