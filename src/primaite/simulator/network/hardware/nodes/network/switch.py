# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from __future__ import annotations

from typing import Dict, Optional

from prettytable import MARKDOWN, PrettyTable
from pydantic import Field

from primaite import getLogger
from primaite.exceptions import NetworkError
from primaite.simulator.network.hardware.base import Link, WiredNetworkInterface
from primaite.simulator.network.hardware.nodes.network.network_node import NetworkNode
from primaite.simulator.network.transmission.data_link_layer import Frame

_LOGGER = getLogger(__name__)


class SwitchPort(WiredNetworkInterface):
    """
    Represents a Switch Port.

    Switch ports connect devices within the same network. They operate at the data link layer (Layer 2) of the OSI model
    and are responsible for receiving and forwarding frames based on MAC addresses. Despite operating at Layer 2,
    they are an essential part of network infrastructure, enabling LAN segmentation, bandwidth management, and
    the creation of VLANs.

    Inherits from:
    - WiredNetworkInterface: Provides properties and methods specific to wired connections.

    Switch ports typically do not have IP addresses assigned to them as they function at Layer 2, but managed switches
    can have management IP addresses for remote management and configuration purposes.
    """

    _connected_node: Optional[Switch] = None
    "The Switch to which the SwitchPort is connected."

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

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

    def send_frame(self, frame: Frame) -> bool:
        """
        Attempts to send a network frame through the interface.

        :param frame: The network frame to be sent.
        :return: A boolean indicating whether the frame was successfully sent.
        """
        if not self.enabled:
            return False
        if not self._connected_link.can_transmit_frame(frame):
            # Drop frame for now. Queuing will happen here (probably) if it's done in the future.
            self._connected_node.sys_log.info(f"{self}: Frame dropped as Link is at capacity")
            return False

        self.pcap.capture_outbound(frame)
        self._connected_link.transmit_frame(sender_nic=self, frame=frame)
        return True

    def receive_frame(self, frame: Frame) -> bool:
        """
        Receives a network frame on the interface.

        :param frame: The network frame being received.
        :return: A boolean indicating whether the frame was successfully received.
        """
        if self.enabled:
            frame.decrement_ttl()
            if frame.ip and frame.ip.ttl < 1:
                self._connected_node.sys_log.warning("Frame discarded as TTL limit reached")
                return False
            self.pcap.capture_inbound(frame)
            self._connected_node.receive_frame(frame=frame, from_network_interface=self)
            return True
        return False


class Switch(NetworkNode, identifier="switch"):
    """A class representing a Layer 2 network switch."""

    network_interfaces: Dict[str, SwitchPort] = {}
    "The SwitchPorts on the Switch."
    network_interface: Dict[int, SwitchPort] = {}
    "The SwitchPorts on the Switch by port id."
    mac_address_table: Dict[str, SwitchPort] = {}
    "A MAC address table mapping destination MAC addresses to corresponding SwitchPorts."

    class ConfigSchema(NetworkNode.ConfigSchema):
        """Configuration Schema for Switch nodes within PrimAITE."""

        hostname: str = "Switch"
        num_ports: int = 24
        "The number of ports on the switch. Default is 24."

    config: ConfigSchema = Field(default_factory=lambda: Switch.ConfigSchema())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for i in range(1, self.config.num_ports + 1):
            self.connect_nic(SwitchPort())

    def _install_system_software(self):
        pass

    def show(self, markdown: bool = False):
        """
        Prints a table of the SwitchPorts on the Switch.

        :param markdown: If True, outputs the table in markdown format. Default is False.
        """
        table = PrettyTable(["Port", "MAC Address", "Speed", "Status"])
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"{self.config.hostname} Switch Ports"
        for port_num, port in self.network_interface.items():
            table.add_row([port_num, port.mac_address, port.speed, "Enabled" if port.enabled else "Disabled"])
        print(table)

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        :return: Current state of this object and child objects.
        """
        state = super().describe_state()
        state["ports"] = {port_num: port.describe_state() for port_num, port in self.network_interface.items()}
        state["num_ports"] = self.config.num_ports  # redundant?
        state["mac_address_table"] = {mac: port.port_num for mac, port in self.mac_address_table.items()}
        return state

    def _add_mac_table_entry(self, mac_address: str, switch_port: SwitchPort):
        """
        Private method to add an entry to the MAC address table.

        :param mac_address: MAC address to be added.
        :param switch_port: Corresponding SwitchPort object.
        """
        mac_table_port = self.mac_address_table.get(mac_address)
        if not mac_table_port:
            self.mac_address_table[mac_address] = switch_port
            self.sys_log.info(f"Added MAC table entry: Port {switch_port.port_num} -> {mac_address}")
        else:
            if mac_table_port != switch_port:
                self.mac_address_table.pop(mac_address)
                self.sys_log.info(f"Removed MAC table entry: Port {mac_table_port.port_num} -> {mac_address}")
                self._add_mac_table_entry(mac_address, switch_port)

    def receive_frame(self, frame: Frame, from_network_interface: SwitchPort):
        """
        Forward a frame to the appropriate port based on the destination MAC address.

        :param frame: The Frame being received.
        :param from_network_interface: The SwitchPort that received the frame.
        """
        src_mac = frame.ethernet.src_mac_addr
        dst_mac = frame.ethernet.dst_mac_addr
        self._add_mac_table_entry(src_mac, from_network_interface)

        outgoing_port = self.mac_address_table.get(dst_mac)
        if outgoing_port and dst_mac.lower() != "ff:ff:ff:ff:ff:ff":
            outgoing_port.send_frame(frame)
        else:
            # If the destination MAC is not in the table, flood to all ports except incoming
            for port in self.network_interface.values():
                if port.enabled and port != from_network_interface:
                    port.send_frame(frame)

    def disconnect_link_from_port(self, link: Link, port_number: int):
        """
        Disconnect a given link from the specified port number on the switch.

        :param link: The Link object to be disconnected.
        :param port_number: The port number on the switch from where the link should be disconnected.
        :raise NetworkError: When an invalid port number is provided or the link does not match the connection.
        """
        port = self.network_interface.get(port_number)
        if port is None:
            msg = f"Invalid port number {port_number} on the switch"
            _LOGGER.error(msg)
            raise NetworkError(msg)

        if port._connected_link != link:
            msg = f"The link does not match the connection at port number {port_number}"
            _LOGGER.error(msg)
            raise NetworkError(msg)

        port.disconnect_link()
