from enum import Enum
from ipaddress import IPv4Address
from typing import Dict, List, Union

from primaite.simulator.core import SimComponent
from primaite.simulator.network.hardware.base import Node, NIC
from prettytable import PrettyTable

from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port


class ACLAction(Enum):
    DENY = 0
    PERMIT = 1


class ACLRule(SimComponent):
    action: ACLAction
    protocol: IPProtocol
    src_ip: IPv4Address
    src_wildcard: IPv4Address = IPv4Address("0.0.0.0")
    src_port: Port
    dst_ip: IPv4Address
    dst_port: Port


class RouteTableEntry(SimComponent):
    pass


class Router(Node):
    num_ports: int
    ethernet_ports: Dict[int, NIC] = {}
    acl: List = []
    route_table: Dict = {}

    def __init__(self, hostname: str, num_ports: int = 5, **kwargs):
        super().__init__(hostname=hostname, num_ports=num_ports, **kwargs)

        for i in range(1, self.num_ports + 1):
            nic = NIC(ip_address="127.0.0.1", subnet_mask="255.0.0.0", gateway="0.0.0.0")
            self.connect_nic(nic)
            self.ethernet_ports[i] = nic

    def describe_state(self) -> Dict:
        pass

    def configure_port(
            self,
            port: int,
            ip_address: Union[IPv4Address, str],
            subnet_mask: str
    ):
        if not isinstance(ip_address, IPv4Address):
            ip_address = IPv4Address(ip_address)
        nic = self.ethernet_ports[port]
        nic.ip_address = ip_address
        nic.subnet_mask = subnet_mask
        self.sys_log.info(f"Configured port {port} with {ip_address=} {subnet_mask=}")

    def enable_port(self, port: int):
        nic = self.ethernet_ports.get(port)
        if nic:
            nic.enable()

    def disable_port(self, port: int):
        nic = self.ethernet_ports.get(port)
        if nic:
            nic.disable()

    def show(self):
        """Prints a table of the NICs on the Node."""
        table = PrettyTable(["Port", "MAC Address", "Address", "Speed", "Status"])

        for port, nic in self.ethernet_ports.items():
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
