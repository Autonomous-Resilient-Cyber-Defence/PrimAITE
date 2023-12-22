from typing import Dict

from prettytable import MARKDOWN, PrettyTable

from primaite import getLogger
from primaite.exceptions import NetworkError
from primaite.simulator.network.hardware.base import Link, Node, SwitchPort
from primaite.simulator.network.transmission.data_link_layer import Frame

_LOGGER = getLogger(__name__)


class Switch(Node):
    """
    A class representing a Layer 2 network switch.

    :ivar num_ports: The number of ports on the switch. Default is 24.
    """

    num_ports: int = 24
    "The number of ports on the switch."
    switch_ports: Dict[int, SwitchPort] = {}
    "The SwitchPorts on the switch."
    mac_address_table: Dict[str, SwitchPort] = {}
    "A MAC address table mapping destination MAC addresses to corresponding SwitchPorts."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.switch_ports:
            self.switch_ports = {i: SwitchPort() for i in range(1, self.num_ports + 1)}
        for port_num, port in self.switch_ports.items():
            port._connected_node = self
            port._port_num_on_node = port_num
            port.parent = self
            port.port_num = port_num

    def show(self, markdown: bool = False):
        """
        Prints a table of the SwitchPorts on the Switch.

        :param markdown: If True, outputs the table in markdown format. Default is False.
        """
        table = PrettyTable(["Port", "MAC Address", "Speed", "Status"])
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"{self.hostname} Switch Ports"
        for port_num, port in self.switch_ports.items():
            table.add_row([port_num, port.mac_address, port.speed, "Enabled" if port.enabled else "Disabled"])
        print(table)

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        :return: Current state of this object and child objects.
        """
        state = super().describe_state()
        state["ports"] = {port_num: port.describe_state() for port_num, port in self.switch_ports.items()}
        state["num_ports"] = self.num_ports  # redundant?
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

    def forward_frame(self, frame: Frame, incoming_port: SwitchPort):
        """
        Forward a frame to the appropriate port based on the destination MAC address.

        :param frame: The Frame to be forwarded.
        :param incoming_port: The port number from which the frame was received.
        """
        src_mac = frame.ethernet.src_mac_addr
        dst_mac = frame.ethernet.dst_mac_addr
        self._add_mac_table_entry(src_mac, incoming_port)

        outgoing_port = self.mac_address_table.get(dst_mac)
        if outgoing_port and dst_mac != "ff:ff:ff:ff:ff:ff":
            outgoing_port.send_frame(frame)
        else:
            # If the destination MAC is not in the table, flood to all ports except incoming
            for port in self.switch_ports.values():
                if port.enabled and port != incoming_port:
                    port.send_frame(frame)

    def disconnect_link_from_port(self, link: Link, port_number: int):
        """
        Disconnect a given link from the specified port number on the switch.

        :param link: The Link object to be disconnected.
        :param port_number: The port number on the switch from where the link should be disconnected.
        :raise NetworkError: When an invalid port number is provided or the link does not match the connection.
        """
        port = self.switch_ports.get(port_number)
        if port is None:
            msg = f"Invalid port number {port_number} on the switch"
            _LOGGER.error(msg)
            raise NetworkError(msg)

        if port._connected_link != link:
            msg = f"The link does not match the connection at port number {port_number}"
            _LOGGER.error(msg)
            raise NetworkError(msg)

        port.disconnect_link()
