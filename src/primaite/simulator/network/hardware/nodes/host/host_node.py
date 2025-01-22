# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from __future__ import annotations

from ipaddress import IPv4Address
from typing import Any, ClassVar, Dict, Optional

from pydantic import Field

from primaite import getLogger
from primaite.simulator.network.hardware.base import (
    IPWiredNetworkInterface,
    Link,
    Node,
    UserManager,
    UserSessionManager,
)
from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.transmission.data_link_layer import Frame
from primaite.simulator.system.applications.application import ApplicationOperatingState
from primaite.simulator.system.applications.nmap import NMAP
from primaite.simulator.system.applications.web_browser import WebBrowser
from primaite.simulator.system.services.arp.arp import ARP, ARPPacket
from primaite.simulator.system.services.dns.dns_client import DNSClient
from primaite.simulator.system.services.icmp.icmp import ICMP
from primaite.simulator.system.services.ntp.ntp_client import NTPClient
from primaite.simulator.system.services.terminal.terminal import Terminal
from primaite.utils.validation.ipv4_address import IPV4Address

_LOGGER = getLogger(__name__)


class HostARP(ARP):
    """
    The Host ARP Service.

    Extends the ARP service for host-specific functionalities within a network, focusing on resolving and caching
    MAC addresses and network interfaces (NICs) based on IP addresses, especially concerning the default gateway.

    This specialized ARP service for hosts facilitates efficient network communication by managing ARP entries
    and handling ARP requests and replies with additional logic for default gateway processing.
    """

    def get_default_gateway_mac_address(self) -> Optional[str]:
        """
        Retrieves the MAC address of the default gateway as known from the ARP cache.

        :return: The MAC address of the default gateway if present in the ARP cache; otherwise, None.
        """
        if self.software_manager.node.default_gateway:
            return self.get_arp_cache_mac_address(self.software_manager.node.default_gateway)

    def get_default_gateway_network_interface(self) -> Optional[NIC]:
        """
        Obtains the network interface card (NIC) associated with the default gateway from the ARP cache.

        :return: The NIC associated with the default gateway if it exists in the ARP cache; otherwise, None.
        """
        if self.software_manager.node.default_gateway and self.software_manager.node.has_enabled_network_interface:
            return self.get_arp_cache_network_interface(self.software_manager.node.default_gateway)

    def _get_arp_cache_mac_address(
        self, ip_address: IPV4Address, is_reattempt: bool = False, is_default_gateway_attempt: bool = False
    ) -> Optional[str]:
        """
        Internal method to retrieve the MAC address associated with an IP address from the ARP cache.

        :param ip_address: The IP address whose MAC address is to be retrieved.
        :param is_reattempt: Indicates if this call is a reattempt after a failed initial attempt.
        :param is_default_gateway_attempt: Indicates if this call is an attempt to get the default gateway's MAC
            address.
        :return: The MAC address associated with the IP address if found, otherwise None.
        """
        arp_entry = self.arp.get(ip_address)

        if arp_entry:
            return arp_entry.mac_address

        if ip_address == self.software_manager.node.default_gateway:
            is_reattempt = True
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
                        ip_address=self.software_manager.node.default_gateway,
                        is_reattempt=True,
                        is_default_gateway_attempt=True,
                    )
        return None

    def get_arp_cache_mac_address(self, ip_address: IPv4Address) -> Optional[str]:
        """
        Retrieves the MAC address associated with a given IP address from the ARP cache.

        :param ip_address: The IP address for which the MAC address is sought.
        :return: The MAC address if available in the ARP cache; otherwise, None.
        """
        return self._get_arp_cache_mac_address(ip_address)

    def _get_arp_cache_network_interface(
        self, ip_address: IPV4Address, is_reattempt: bool = False, is_default_gateway_attempt: bool = False
    ) -> Optional[NIC]:
        """
        Internal method to retrieve the NIC associated with an IP address from the ARP cache.

        :param ip_address: The IP address whose NIC is to be retrieved.
        :param is_reattempt: Indicates if this call is a reattempt after a failed initial attempt.
        :param is_default_gateway_attempt: Indicates if this call is an attempt to get the NIC of the default gateway.
        :return: The NIC associated with the IP address if found, otherwise None.
        """
        arp_entry = self.arp.get(ip_address)

        if arp_entry:
            return self.software_manager.node.network_interfaces[arp_entry.network_interface_uuid]
        else:
            if ip_address == self.software_manager.node.default_gateway:
                is_reattempt = True
            if not is_reattempt:
                self.send_arp_request(ip_address)
                return self._get_arp_cache_network_interface(
                    ip_address=ip_address, is_reattempt=True, is_default_gateway_attempt=is_default_gateway_attempt
                )
            else:
                if self.software_manager.node.default_gateway:
                    if not is_default_gateway_attempt:
                        self.send_arp_request(self.software_manager.node.default_gateway)
                        return self._get_arp_cache_network_interface(
                            ip_address=self.software_manager.node.default_gateway,
                            is_reattempt=True,
                            is_default_gateway_attempt=True,
                        )
        return None

    def get_arp_cache_network_interface(self, ip_address: IPv4Address) -> Optional[NIC]:
        """
        Retrieves the network interface card (NIC) associated with a given IP address from the ARP cache.

        :param ip_address: The IP address for which the associated NIC is sought.
        :return: The NIC if available in the ARP cache; otherwise, None.
        """
        return self._get_arp_cache_network_interface(ip_address)

    def _process_arp_request(self, arp_packet: ARPPacket, from_network_interface: NIC):
        """
        Processes an ARP request.

        Adds a new entry to the ARP cache if the target IP address matches the NIC's IP address and sends an ARP
        reply back.

        :param arp_packet: The ARP packet containing the request.
        :param from_network_interface: The NIC that received the ARP request.
        """
        super()._process_arp_request(arp_packet, from_network_interface)
        # Unmatched ARP Request
        if arp_packet.target_ip_address != from_network_interface.ip_address:
            self.sys_log.warning(
                f"Ignoring ARP request for {arp_packet.target_ip_address}. Current IP address is "
                f"{from_network_interface.ip_address}"
            )
            return

        arp_packet = arp_packet.generate_reply(from_network_interface.mac_address)
        self.send_arp_reply(arp_packet)


class NIC(IPWiredNetworkInterface):
    """
    Represents a Network Interface Card (NIC) in a Host Node.

    A NIC is a hardware component that provides a computer or other network device with the ability to connect to a
    network. It operates at both Layer 2 (Data Link Layer) and Layer 3 (Network Layer) of the OSI model, meaning it
    can interpret both MAC addresses and IP addresses. This class combines the functionalities of
    WiredNetworkInterface and Layer3Interface, allowing the NIC to manage physical connections and network layer
    addressing.

    Inherits from:
    - WiredNetworkInterface: Provides properties and methods specific to wired connections, including methods to connect
      and disconnect from network links and to manage the enabled/disabled state of the interface.
    - Layer3Interface: Provides properties for Layer 3 network configuration, such as IP address and subnet mask.
    """

    _connected_link: Optional[Link] = None
    "The network link to which the network interface is connected."
    wake_on_lan: bool = False
    "Indicates if the NIC supports Wake-on-LAN functionality."

    def model_post_init(self, __context: Any) -> None:
        """
        Performs post-initialisation checks to ensure the model's IP configuration is valid.

        This method is invoked after the initialisation of a network model object to validate its network settings,
        particularly to ensure that the assigned IP address is not a network address. This validation is crucial for
        maintaining the integrity of network simulations and avoiding configuration errors that could lead to
        unrealistic or incorrect behavior.

        :param __context: Contextual information or parameters passed to the method, used for further initializing or
            validating the model post-creation.
        :raises ValueError: If the IP address is the same as the network address, indicating an incorrect configuration.
        """
        if self.ip_network.network_address == self.ip_address:
            raise ValueError(f"{self.ip_address}/{self.subnet_mask} must not be a network address")

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        :return: Current state of this object and child objects.
        :rtype: Dict
        """
        # Get the state from the IPWiredNetworkInterface
        state = super().describe_state()

        # Update the state with NIC-specific information
        state.update({"wake_on_lan": self.wake_on_lan})

        return state

    def receive_frame(self, frame: Frame) -> bool:
        """
        Attempt to receive and process a network frame from the connected Link.

        This method processes a frame if the NIC is enabled. It checks the frame's destination and TTL, captures the
        frame using PCAP, and forwards it to the connected Node if valid. Returns True if the frame is processed,
        False otherwise (e.g., if the NIC is disabled, or TTL expired).

        :param frame: The network frame being received.
        :return: True if the frame is processed and passed to the node, False otherwise.
        """
        if self.enabled:
            frame.decrement_ttl()
            if frame.ip and frame.ip.ttl < 1:
                self._connected_node.sys_log.info(f"Frame discarded at {self} as TTL limit reached")
                return False
            frame.set_received_timestamp()
            self.pcap.capture_inbound(frame)
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
                super().receive_frame(frame)
                self._connected_node.receive_frame(frame=frame, from_network_interface=self)
                return True
        return False

    def __str__(self) -> str:
        """
        String representation of the NIC.

        :return: A string combining the port number, MAC address and IP address of the NIC.
        """
        return f"Port {self.port_name if self.port_name else self.port_num}: {self.mac_address}/{self.ip_address}"


class HostNode(Node, identifier="HostNode"):
    """
    Represents a host node in the network.

    An end-user device within the network, such as a computer or server, equipped with the capability to initiate and
    respond to network communications.

    A `HostNode` extends the base `Node` class by incorporating host-specific services and applications, thereby
    simulating the functionalities typically expected from a networked end-user device.

    **Example**::

        >>> pc_a = HostNode(
        ...     hostname="pc_a",
        ...     ip_address="192.168.1.10",
        ...     subnet_mask="255.255.255.0",
        ...     default_gateway="192.168.1.1"
        ... )
        >>> pc_a.power_on()

    The host node comes pre-equipped with a range of core functionalities, services, and applications necessary
    for engaging in various network operations and tasks.

    Core Functionality:
    -------------------

        * Packet Capture: Monitors and logs network traffic.
        * Sys Log: Logs system events and errors.

    Services:
    ---------

        * ARP (Address Resolution Protocol) Service: Resolves IP addresses to MAC addresses.
        * ICMP (Internet Control Message Protocol) Service: Handles ICMP operations, such as ping requests.
        * DNS (Domain Name System) Client: Resolves domain names to IP addresses.
        * FTP (File Transfer Protocol) Client: Enables file transfers between the host and FTP servers.
        * NTP (Network Time Protocol) Client: Synchronizes the system clock with NTP servers.
        * Terminal Client: Handles SSH requests between HostNode and external components.

    Applications:
    ------------

        * Web Browser: Provides web browsing capabilities.
    """

    SYSTEM_SOFTWARE: ClassVar[Dict] = {
        "HostARP": HostARP,
        "ICMP": ICMP,
        "DNSClient": DNSClient,
        "NTPClient": NTPClient,
        "WebBrowser": WebBrowser,
        "NMAP": NMAP,
        "UserSessionManager": UserSessionManager,
        "UserManager": UserManager,
        "Terminal": Terminal,
    }
    """List of system software that is automatically installed on nodes."""

    network_interfaces: Dict[str, NIC] = {}
    "The Network Interfaces on the node."
    network_interface: Dict[int, NIC] = {}
    "The NICs on the node by port id."

    config: HostNode.ConfigSchema = Field(default_factory=lambda: HostNode.ConfigSchema())

    class ConfigSchema(Node.ConfigSchema):
        """Configuration Schema for HostNode class."""

        hostname: str = "HostNode"
        ip_address: IPV4Address = "192.168.0.1"
        subnet_mask: IPV4Address = "255.255.255.0"
        default_gateway: IPV4Address = "192.168.10.1"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect_nic(NIC(ip_address=kwargs["config"].ip_address, subnet_mask=kwargs["config"].subnet_mask))

    @property
    def nmap(self) -> Optional[NMAP]:
        """
        Return the NMAP application installed on the Node.

        :return: NMAP application installed on the Node.
        :rtype: Optional[NMAP]
        """
        return self.software_manager.software.get("NMAP")

    @property
    def arp(self) -> Optional[ARP]:
        """
        Return the ARP Cache of the HostNode.

        :return: ARP Cache for given HostNode
        :rtype: Optional[ARP]
        """
        return self.software_manager.software.get("ARP")

    def default_gateway_hello(self):
        """
        Sends a hello message to the default gateway to establish connectivity and resolve the gateway's MAC address.

        This method is invoked to ensure the host node can communicate with its default gateway, primarily to confirm
        network connectivity and populate the ARP cache with the gateway's MAC address.
        """
        if self.operating_state == NodeOperatingState.ON and self.default_gateway:
            self.software_manager.arp.get_default_gateway_mac_address()

    def receive_frame(self, frame: Frame, from_network_interface: NIC):
        """
        Receive a Frame from the connected NIC and process it.

        Depending on the protocol, the frame is passed to the appropriate handler such as ARP or ICMP, or up to the
        SessionManager if no code manager exists.

        :param frame: The Frame being received.
        :param from_network_interface: The NIC that received the frame.
        """
        super().receive_frame(frame, from_network_interface)

        # Check if the destination port is open on the Node
        dst_port = None
        if frame.tcp:
            dst_port = frame.tcp.dst_port
        elif frame.udp:
            dst_port = frame.udp.dst_port

        can_accept_nmap = False
        if self.software_manager.software.get("NMAP"):
            if self.software_manager.software["NMAP"].operating_state == ApplicationOperatingState.RUNNING:
                can_accept_nmap = True

        accept_nmap = can_accept_nmap and frame.payload.__class__.__name__ == "PortScanPayload"

        accept_frame = False
        if frame.icmp or dst_port in self.software_manager.get_open_ports() or accept_nmap:
            # accept the frame as the port is open or if it's an ICMP frame
            accept_frame = True

        # TODO: add internal node firewall check here?

        if accept_frame:
            self.session_manager.receive_frame(frame, from_network_interface)
        else:
            self.sys_log.info(f"Ignoring frame from {frame.ip.src_ip_address}")
            # TODO: do we need to do anything more here?
            pass
