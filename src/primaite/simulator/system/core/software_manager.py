from ipaddress import IPv4Address, IPv4Network
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING, Union

from prettytable import MARKDOWN, PrettyTable

from primaite.simulator.file_system.file_system import FileSystem
from primaite.simulator.network.transmission.data_link_layer import Frame
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.application import Application, ApplicationOperatingState
from primaite.simulator.system.core.sys_log import SysLog
from primaite.simulator.system.services.service import Service, ServiceOperatingState
from primaite.simulator.system.software import IOSoftware

if TYPE_CHECKING:
    from primaite.simulator.system.core.session_manager import SessionManager
    from primaite.simulator.system.core.sys_log import SysLog
    from primaite.simulator.network.hardware.base import Node, NIC
    from primaite.simulator.system.services.arp.arp import ARP
    from primaite.simulator.system.services.icmp.icmp import ICMP

from typing import Type, TypeVar

IOSoftwareClass = TypeVar("IOSoftwareClass", bound=IOSoftware)


class SoftwareManager:
    """
    Manages all running services and applications on a network node and facilitates their communication.

    This class is responsible for installing, uninstalling, and managing the operational state of various network
    services and applications. It acts as a bridge between the node's session manager and its software components,
    ensuring that incoming and outgoing network payloads are correctly routed to and from the appropriate services
    or applications.
    """

    def __init__(
        self,
        parent_node: "Node",
        session_manager: "SessionManager",
        sys_log: SysLog,
        file_system: FileSystem,
        dns_server: Optional[IPv4Address],
    ):
        """
        Initialize a new instance of SoftwareManager.

        :param session_manager: The session manager handling network communications.
        """
        self.node = parent_node
        self.session_manager = session_manager
        self.software: Dict[str, Union[Service, Application]] = {}
        self._software_class_to_name_map: Dict[Type[IOSoftwareClass], str] = {}
        self.port_protocol_mapping: Dict[Tuple[Port, IPProtocol], Union[Service, Application]] = {}
        self.sys_log: SysLog = sys_log
        self.file_system: FileSystem = file_system
        self.dns_server: Optional[IPv4Address] = dns_server

    @property
    def arp(self) -> "ARP":
        """Provides access to the ARP service instance, if installed."""
        return self.software.get("ARP")  # noqa

    @property
    def icmp(self) -> "ICMP":
        """Provides access to the ICMP service instance, if installed."""
        return self.software.get("ICMP")  # noqa

    def get_open_ports(self) -> List[Port]:
        """
        Get a list of open ports.

        :return: A list of all open ports on the Node.
        """
        open_ports = []
        for software in self.port_protocol_mapping.values():
            if software.operating_state in {ApplicationOperatingState.RUNNING, ServiceOperatingState.RUNNING}:
                open_ports.append(software.port)
        return open_ports

    def install(self, software_class: Type[IOSoftwareClass]):
        """
        Install an Application or Service.

        :param software_class: The software class.
        """
        # TODO: Software manager and node itself both have an install method. Need to refactor to have more logical
        # separation of concerns.
        if software_class in self._software_class_to_name_map:
            self.sys_log.info(f"Cannot install {software_class} as it is already installed")
            return
        software = software_class(
            software_manager=self, sys_log=self.sys_log, file_system=self.file_system, dns_server=self.dns_server
        )
        if isinstance(software, Application):
            software.install()
        software.software_manager = self
        self.software[software.name] = software
        self.port_protocol_mapping[(software.port, software.protocol)] = software
        self.sys_log.info(f"Installed {software.name}")
        if isinstance(software, Application):
            software.operating_state = ApplicationOperatingState.CLOSED

        # add the software to the node's registry after it has been fully initialized
        if isinstance(software, Service):
            self.node.install_service(software)
        elif isinstance(software, Application):
            self.node.install_application(software)

    def uninstall(self, software_name: str):
        """
        Uninstall an Application or Service.

        :param software_name: The software name.
        """
        if software_name in self.software:
            software = self.software.pop(software_name)  # noqa
            if isinstance(software, Application):
                self.node.uninstall_application(software)
            elif isinstance(software, Service):
                self.node.uninstall_service(software)
            for key, value in self.port_protocol_mapping.items():
                if value.name == software_name:
                    self.port_protocol_mapping.pop(key)
                    break
            for key, value in self._software_class_to_name_map.items():
                if value == software_name:
                    self._software_class_to_name_map.pop(key)
                    break
            del software
            self.sys_log.info(f"Uninstalled {software_name}")
            return
        self.sys_log.error(f"Cannot uninstall {software_name} as it is not installed")

    def send_internal_payload(self, target_software: str, payload: Any):
        """
        Send a payload to a specific service or application.

        :param target_software: The name of the target service or application.
        :param payload: The data to be sent.
        """
        receiver = self.software.get(target_software)

        if receiver:
            receiver.receive_payload(payload)
        else:
            self.sys_log.error(f"No Service of Application found with the name {target_software}")

    def send_payload_to_session_manager(
        self,
        payload: Any,
        dest_ip_address: Optional[Union[IPv4Address, IPv4Network]] = None,
        dest_port: Optional[Port] = None,
        ip_protocol: IPProtocol = IPProtocol.TCP,
        session_id: Optional[str] = None,
    ) -> bool:
        """
        Sends a payload to the SessionManager for network transmission.

        This method is responsible for initiating the process of sending network payloads. It supports both
        unicast and Layer 3 broadcast transmissions. For broadcasts, the destination IP should be specified
        as an IPv4Network.

        :param payload: The payload to be sent.
        :param dest_ip_address: The IP address or network (for broadcasts) of the payload destination.
        :param dest_port: The destination port for the payload. Optional.
        :param session_id: The Session ID from which the payload originates. Optional.
        :return: True if the payload was successfully sent, False otherwise.
        """
        return self.session_manager.receive_payload_from_software_manager(
            payload=payload,
            dst_ip_address=dest_ip_address,
            dst_port=dest_port,
            ip_protocol=ip_protocol,
            session_id=session_id,
        )

    def receive_payload_from_session_manager(
        self,
        payload: Any,
        port: Port,
        protocol: IPProtocol,
        session_id: str,
        from_network_interface: "NIC",
        frame: Frame,
    ):
        """
        Receive a payload from the SessionManager and forward it to the corresponding service or application.

        :param payload: The payload being received.
        :param session: The transport session the payload originates from.
        """
        receiver: Optional[Union[Service, Application]] = self.port_protocol_mapping.get((port, protocol), None)
        if receiver:
            receiver.receive(
                payload=payload, session_id=session_id, from_network_interface=from_network_interface, frame=frame
            )
        else:
            self.sys_log.error(f"No service or application found for port {port} and protocol {protocol}")
        pass

    def show(self, markdown: bool = False):
        """
        Prints a table of the SwitchPorts on the Switch.

        :param markdown: If True, outputs the table in markdown format. Default is False.
        """
        table = PrettyTable(["Name", "Type", "Operating State", "Health State", "Port", "Protocol"])
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"{self.sys_log.hostname} Software Manager"
        for software in self.port_protocol_mapping.values():
            software_type = "Service" if isinstance(software, Service) else "Application"
            table.add_row(
                [
                    software.name,
                    software_type,
                    software.operating_state.name,
                    software.health_state_actual.name,
                    software.port.value if software.port != Port.NONE else None,
                    software.protocol.value,
                ]
            )
        print(table)
