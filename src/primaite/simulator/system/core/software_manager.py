from ipaddress import IPv4Address
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING, Union

from prettytable import MARKDOWN, PrettyTable

from primaite.simulator.file_system.file_system import FileSystem
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.application import Application, ApplicationOperatingState
from primaite.simulator.system.core.sys_log import SysLog
from primaite.simulator.system.services.service import Service, ServiceOperatingState
from primaite.simulator.system.software import IOSoftware

if TYPE_CHECKING:
    from primaite.simulator.system.core.session_manager import SessionManager
    from primaite.simulator.system.core.sys_log import SysLog

from typing import Type, TypeVar

IOSoftwareClass = TypeVar("IOSoftwareClass", bound=IOSoftware)


class SoftwareManager:
    """A class that manages all running Services and Applications on a Node and facilitates their communication."""

    def __init__(self, session_manager: "SessionManager", sys_log: SysLog, file_system: FileSystem):
        """
        Initialize a new instance of SoftwareManager.

        :param session_manager: The session manager handling network communications.
        """
        self.session_manager = session_manager
        self.software: Dict[str, Union[Service, Application]] = {}
        self._software_class_to_name_map: Dict[Type[IOSoftwareClass], str] = {}
        self.port_protocol_mapping: Dict[Tuple[Port, IPProtocol], Union[Service, Application]] = {}
        self.sys_log: SysLog = sys_log
        self.file_system: FileSystem = file_system

    def get_open_ports(self) -> List[Port]:
        """
        Get a list of open ports.

        :return: A list of all open ports on the Node.
        """
        open_ports = [Port.ARP]
        for software in self.port_protocol_mapping.values():
            if software.operating_state in {ApplicationOperatingState.RUNNING, ServiceOperatingState.RUNNING}:
                open_ports.append(software.port)
        open_ports.sort(key=lambda port: port.value)
        return open_ports

    def install(self, software_class: Type[IOSoftwareClass]):
        """
        Install an Application or Service.

        :param software_class: The software class.
        """
        if software_class in self._software_class_to_name_map:
            self.sys_log.info(f"Cannot install {software_class} as it is already installed")
            return
        software = software_class(software_manager=self, sys_log=self.sys_log, file_system=self.file_system)
        if isinstance(software, Application):
            software.install()
        software.software_manager = self
        self.software[software.name] = software
        self.port_protocol_mapping[(software.port, software.protocol)] = software
        self.sys_log.info(f"Installed {software.name}")
        if isinstance(software, Application):
            software.operating_state = ApplicationOperatingState.CLOSED

    def uninstall(self, software_name: str):
        """
        Uninstall an Application or Service.

        :param software_name: The software name.
        """
        if software_name in self.software:
            software = self.software.pop(software_name)  # noqa
            del software
            self.sys_log.info(f"Deleted {software_name}")
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
        dest_ip_address: Optional[IPv4Address] = None,
        dest_port: Optional[Port] = None,
        session_id: Optional[str] = None,
    ):
        """
        Send a payload to the SessionManager.

        :param payload: The payload to be sent.
        :param dest_ip_address: The ip address of the payload destination.
        :param dest_port: The port of the payload destination.
        :param session_id: The Session ID the payload is to originate from. Optional.
        """
        self.session_manager.receive_payload_from_software_manager(
            payload=payload, dst_ip_address=dest_ip_address, dst_port=dest_port, session_id=session_id
        )

    def receive_payload_from_session_manger(self, payload: Any, port: Port, protocol: IPProtocol, session_id: str):
        """
        Receive a payload from the SessionManager and forward it to the corresponding service or application.

        :param payload: The payload being received.
        :param session: The transport session the payload originates from.
        """
        receiver: Optional[Union[Service, Application]] = self.port_protocol_mapping.get((port, protocol), None)
        if receiver:
            receiver.receive(payload=payload, session_id=session_id)
        else:
            self.sys_log.error(f"No service or application found for port {port} and protocol {protocol}")
        pass

    def show(self, markdown: bool = False):
        """
        Prints a table of the SwitchPorts on the Switch.

        :param markdown: If True, outputs the table in markdown format. Default is False.
        """
        table = PrettyTable(["Name", "Type", "Operating State", "Health State", "Port"])
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
                    software.port.value,
                ]
            )
        print(table)
