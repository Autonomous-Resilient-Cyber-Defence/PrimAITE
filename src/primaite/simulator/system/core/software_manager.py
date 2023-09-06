from ipaddress import IPv4Address
from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING, Union

from prettytable import MARKDOWN, PrettyTable

from primaite.simulator.file_system.file_system import FileSystem
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.application import Application
from primaite.simulator.system.core.session_manager import Session
from primaite.simulator.system.core.sys_log import SysLog
from primaite.simulator.system.services.service import Service
from primaite.simulator.system.software import SoftwareType

if TYPE_CHECKING:
    from primaite.simulator.system.core.session_manager import SessionManager
    from primaite.simulator.system.core.sys_log import SysLog

from typing import Type, TypeVar

ServiceClass = TypeVar("ServiceClass", bound=Service)


class SoftwareManager:
    """A class that manages all running Services and Applications on a Node and facilitates their communication."""

    def __init__(self, session_manager: "SessionManager", sys_log: SysLog, file_system: FileSystem):
        """
        Initialize a new instance of SoftwareManager.

        :param session_manager: The session manager handling network communications.
        """
        self.session_manager = session_manager
        self.services: Dict[str, Service] = {}
        self.applications: Dict[str, Application] = {}
        self.port_protocol_mapping: Dict[Tuple[Port, IPProtocol], Union[Service, Application]] = {}
        self.sys_log: SysLog = sys_log
        self.file_system: FileSystem = file_system

    def add_service(self, service_class: Type[ServiceClass]):
        """
        Add a Service to the manager.

        :param: service_class: The class of the service to add
        """
        service = service_class(software_manager=self, sys_log=self.sys_log, file_system=self.file_system)

        service.software_manager = self
        self.services[service.name] = service
        self.port_protocol_mapping[(service.port, service.protocol)] = service

    def add_application(self, name: str, application: Application, port: Port, protocol: IPProtocol):
        """
        Add an Application to the manager.

        :param name: The name of the application.
        :param application: The application instance.
        :param port: The port used by the application.
        :param protocol: The network protocol used by the application.
        """
        application.software_manager = self
        self.applications[name] = application
        self.port_protocol_mapping[(port, protocol)] = application

    def send_internal_payload(self, target_software: str, target_software_type: SoftwareType, payload: Any):
        """
        Send a payload to a specific service or application.

        :param target_software: The name of the target service or application.
        :param target_software_type: The type of software (Service, Application, Process).
        :param payload: The data to be sent.
        :param receiver_type: The type of the target, either 'service' or 'application'.
        """
        if target_software_type is SoftwareType.SERVICE:
            receiver = self.services.get(target_software)
        elif target_software_type is SoftwareType.APPLICATION:
            receiver = self.applications.get(target_software)
        else:
            raise ValueError(f"Invalid receiver type {target_software_type}")

        if receiver:
            receiver.receive_payload(payload)
        else:
            raise ValueError(f"No {target_software_type.name.lower()} found with the name {target_software}")

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
        table = PrettyTable(["Name", "Operating State", "Health State", "Port"])
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"{self.sys_log.hostname} Software Manager"
        for service in self.services.values():
            table.add_row(
                [service.name, service.operating_state.name, service.health_state_actual.name, service.port.value]
            )
        print(table)
