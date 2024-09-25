# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
import copy
from abc import abstractmethod
from datetime import datetime
from enum import Enum
from ipaddress import IPv4Address, IPv4Network
from typing import Any, Dict, Optional, Set, TYPE_CHECKING, Union

from prettytable import MARKDOWN, PrettyTable
from pydantic import Field

from primaite.interface.request import RequestResponse
from primaite.simulator.core import RequestManager, RequestType, SimComponent
from primaite.simulator.file_system.file_system import FileSystem, Folder
from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.system.core.session_manager import Session
from primaite.simulator.system.core.sys_log import SysLog
from primaite.utils.validation.ip_protocol import IPProtocol, PROTOCOL_LOOKUP
from primaite.utils.validation.port import Port

if TYPE_CHECKING:
    from primaite.simulator.system.core.software_manager import SoftwareManager


class SoftwareType(Enum):
    """
    An enumeration representing the different types of software within a simulated environment.

    Members:
    - APPLICATION: User-facing programs that may perform input/output operations.
    - SERVICE: Represents programs that run in the background and may perform input/output operations.
    - PROCESS: Software executed by a Node that does not have the ability to performing input/output operations.
    """

    APPLICATION = 1
    "User-facing software that may perform input/output operations."
    SERVICE = 2
    "Software that runs in the background and may perform input/output operations."
    PROCESS = 3
    "Software executed by a Node that does not have the ability to performing input/output operations."


class SoftwareHealthState(Enum):
    """Enumeration of the Software Health States."""

    UNUSED = 0
    "Unused state."
    GOOD = 1
    "The software is in a good and healthy condition."
    FIXING = 2
    "The software is undergoing FIXING or updates."
    COMPROMISED = 3
    "The software's security has been compromised."
    OVERWHELMED = 4
    "he software is overwhelmed and not functioning properly."


class SoftwareCriticality(Enum):
    """Enumeration of Software Criticality Levels."""

    LOWEST = 1
    "The lowest level of criticality."
    LOW = 2
    "A low level of criticality."
    MEDIUM = 3
    "A medium level of criticality."
    HIGH = 4
    "A high level of criticality."
    HIGHEST = 5
    "The highest level of criticality."


class Software(SimComponent):
    """
    A base class representing software in a simulator environment.

    This class is intended to be subclassed by specific types of software entities.
    It outlines the fundamental attributes and behaviors expected of any software in the simulation.
    """

    name: str
    "The name of the software."
    health_state_actual: SoftwareHealthState = SoftwareHealthState.UNUSED
    "The actual health state of the software."
    health_state_visible: SoftwareHealthState = SoftwareHealthState.UNUSED
    "The health state of the software visible to the red agent."
    criticality: SoftwareCriticality = SoftwareCriticality.LOWEST
    "The criticality level of the software."
    fixing_count: int = 0
    "The count of patches applied to the software, defaults to 0."
    scanning_count: int = 0
    "The count of times the software has been scanned, defaults to 0."
    revealed_to_red: bool = False
    "Indicates if the software has been revealed to red agent, defaults is False."
    software_manager: Optional["SoftwareManager"] = None
    "An instance of Software Manager that is used by the parent node."
    sys_log: SysLog = None
    "An instance of SysLog that is used by the parent node."
    file_system: FileSystem
    "The FileSystem of the Node the Software is installed on."
    folder: Optional[Folder] = None
    "The folder on the file system the Software uses."
    fixing_duration: int = 2
    "The number of ticks it takes to patch the software."
    _fixing_countdown: Optional[int] = None
    "Current number of ticks left to patch the software."

    def _init_request_manager(self) -> RequestManager:
        """
        Initialise the request manager.

        More information in user guide and docstring for SimComponent._init_request_manager.
        """
        rm = super()._init_request_manager()
        rm.add_request(
            "compromise",
            RequestType(
                func=lambda request, context: RequestResponse.from_bool(
                    self.set_health_state(SoftwareHealthState.COMPROMISED)
                ),
            ),
        )
        rm.add_request(
            "fix",
            RequestType(
                func=lambda request, context: RequestResponse.from_bool(self.fix()),
            ),
        )
        rm.add_request("scan", RequestType(func=lambda request, context: RequestResponse.from_bool(self.scan())))
        return rm

    def _get_session_details(self, session_id: str) -> Session:
        """
        Returns the Session object from the given session id.

        :param: session_id: ID of the session that needs details retrieved
        """
        return self.software_manager.session_manager.sessions_by_uuid[session_id]

    @abstractmethod
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
                "health_state_actual": self.health_state_actual.value,
                "health_state_visible": self.health_state_visible.value,
                "criticality": self.criticality.value,
                "fixing_count": self.fixing_count,
                "scanning_count": self.scanning_count,
                "revealed_to_red": self.revealed_to_red,
            }
        )
        return state

    def set_health_state(self, health_state: SoftwareHealthState) -> bool:
        """
        Assign a new health state to this software.

        Note: this should only be possible when the software is currently running, but the software base class has no
        operating state, only subclasses do. So subclasses will need to implement this check. TODO: check if this should
        be changed so that the base Software class has a running attr.

        :param health_state: New health state to assign to the software
        :type health_state: SoftwareHealthState
        """
        self.health_state_actual = health_state
        return True

    def install(self) -> None:
        """
        Perform first-time setup of this service on a node.

        This is an abstract class that should be overwritten by specific applications or services. It must be called
        after the service is already associate with a node. For example, a service may need to authenticate with a
        server during installation, or create files in the node's filesystem.
        """
        pass

    def uninstall(self) -> None:
        """Uninstall this service from a node.

        This is an abstract class that should be overwritten by applications or services. It must be called after the
        `install` method has already been run on that node. It should undo any installation steps, for example by
        deleting files, or contacting a server.
        """
        pass

    def scan(self) -> bool:
        """Update the observed health status to match the actual health status."""
        self.health_state_visible = self.health_state_actual
        return True

    def fix(self) -> bool:
        """Perform a fix on the software."""
        if self.health_state_actual in (SoftwareHealthState.COMPROMISED, SoftwareHealthState.GOOD):
            self._fixing_countdown = self.fixing_duration
            self.set_health_state(SoftwareHealthState.FIXING)
            return True
        return False

    def _update_fix_status(self) -> None:
        """Update the fix status of the software."""
        self._fixing_countdown -= 1
        if self._fixing_countdown <= 0:
            self.set_health_state(SoftwareHealthState.GOOD)
            self._fixing_countdown = None
            self.fixing_count += 1

    def reveal_to_red(self) -> None:
        """Reveals the software to the red agent."""
        self.revealed_to_red = True

    def apply_timestep(self, timestep: int) -> None:
        """
        Apply a single timestep to the software.

        :param timestep: The current timestep of the simulation.
        """
        super().apply_timestep(timestep)
        if self.health_state_actual == SoftwareHealthState.FIXING:
            self._update_fix_status()

    def pre_timestep(self, timestep: int) -> None:
        """Apply pre-timestep logic."""
        super().pre_timestep(timestep)


class IOSoftware(Software):
    """
    Represents software in a simulator environment that is capable of input/output operations.

    This base class is meant to be sub-classed by Application and Service classes. It provides the blueprint for
    Applications and Services that can receive payloads from a Node's SessionManager (corresponding to layer 5 in the
    OSI Model), process them according to their internals, and send a response payload back to the SessionManager if
    required.
    """

    installing_count: int = 0
    "The number of times the software has been installed. Default is 0."
    max_sessions: int = 100
    "The maximum number of sessions that the software can handle simultaneously. Default is 0."
    tcp: bool = True
    "Indicates if the software uses TCP protocol for communication. Default is True."
    udp: bool = True
    "Indicates if the software uses UDP protocol for communication. Default is True."
    port: Port
    "The port to which the software is connected."
    listen_on_ports: Set[Port] = Field(default_factory=set)
    "The set of ports to listen on."
    protocol: IPProtocol
    "The IP Protocol the Software operates on."
    _connections: Dict[str, Dict] = {}
    "Active connections."

    @abstractmethod
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
                "installing_count": self.installing_count,
                "max_sessions": self.max_sessions,
                "tcp": self.tcp,
                "udp": self.udp,
                "port": self.port,
            }
        )
        return state

    @abstractmethod
    def _can_perform_action(self) -> bool:
        """
        Checks if the software can perform actions.

        This is done by checking if the software is operating properly or the node it is installed
        in is operational.

        Returns true if the software can perform actions.
        """
        if self.software_manager and self.software_manager.node.operating_state != NodeOperatingState.ON:
            self.software_manager.node.sys_log.error(
                f"{self.name} Error: {self.software_manager.node.hostname} is not powered on."
            )
            return False
        return True

    @property
    def connections(self) -> Dict[str, Dict]:
        """Return the public version of connections."""
        return copy.copy(self._connections)

    def add_connection(self, connection_id: Union[str, int], session_id: Optional[str] = None) -> bool:
        """
        Create a new connection to this service.

        Returns true if connection successfully created

        :param: connection_id: UUID of the connection to create
        :type: string
        """
        # if over or at capacity, set to overwhelmed
        if len(self._connections) >= self.max_sessions:
            self.set_health_state(SoftwareHealthState.OVERWHELMED)
            self.sys_log.warning(f"{self.name}: Connection request ({connection_id}) declined. Service is at capacity.")
            return False
        else:
            # if service was previously overwhelmed, set to good because there is enough space for connections
            if self.health_state_actual == SoftwareHealthState.OVERWHELMED:
                self.set_health_state(SoftwareHealthState.GOOD)

            # check that connection already doesn't exist
            if not self._connections.get(connection_id):
                session_details = None
                if session_id:
                    session_details = self._get_session_details(session_id)
                self._connections[connection_id] = {
                    "session_id": session_id,
                    "ip_address": session_details.with_ip_address if session_details else None,
                    "time": datetime.now(),
                }
                self.sys_log.info(f"{self.name}: Connection request ({connection_id}) authorised")
                return True
            # connection with given id already exists
            self.sys_log.warning(
                f"{self.name}: Connection request ({connection_id}) declined. Connection already exists."
            )
            return False

    def terminate_connection(self, connection_id: str, send_disconnect: bool = True) -> bool:
        """
        Terminates a connection from this service.

        Returns true if connection successfully removed

        :param: connection_id: UUID of the connection to create
        :param send_disconnect: If True, sends a disconnect payload to the ip address of the associated session.
        :type: string
        """
        if self.connections.get(connection_id):
            connection_dict = self._connections.pop(connection_id)
            if send_disconnect:
                self.software_manager.send_payload_to_session_manager(
                    payload={"type": "disconnect", "connection_id": connection_id},
                    session_id=connection_dict["session_id"],
                )
                self.sys_log.info(f"{self.name}: Connection {connection_id=} terminated")
                return True
        return False

    def show_connections(self, markdown: bool = False):
        """
        Display the connections in tabular format.

        :param markdown: Whether to display the table in Markdown format or not. Default is `False`.
        """
        table = PrettyTable(["IP Address", "Connection ID", "Creation Timestamp"])
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"{self.sys_log.hostname} {self.name} Connections"
        for connection_id, data in self.connections.items():
            table.add_row([data["ip_address"], connection_id, str(data["time"])])
        print(table.get_string(sortby="Creation Timestamp"))

    def clear_connections(self):
        """Clears all the connections from the software."""
        self._connections = {}

    def send(
        self,
        payload: Any,
        session_id: Optional[str] = None,
        dest_ip_address: Optional[Union[IPv4Address, IPv4Network]] = None,
        dest_port: Optional[int] = None,
        ip_protocol: IPProtocol = PROTOCOL_LOOKUP["TCP"],
        **kwargs,
    ) -> bool:
        """
        Sends a payload to the SessionManager for network transmission.

        This method is responsible for initiating the process of sending network payloads. It supports both
        unicast and Layer 3 broadcast transmissions. For broadcasts, the destination IP should be specified
        as an IPv4Network. It delegates the actual sending process to the SoftwareManager.

        :param payload: The payload to be sent.
        :param dest_ip_address: The IP address or network (for broadcasts) of the payload destination.
        :param dest_port: The destination port for the payload. Optional.
        :param session_id: The Session ID from which the payload originates. Optional.
        :return: True if the payload was successfully sent, False otherwise.
        """
        if not self._can_perform_action():
            return False

        return self.software_manager.send_payload_to_session_manager(
            payload=payload,
            dest_ip_address=dest_ip_address,
            dest_port=dest_port,
            ip_protocol=ip_protocol,
            session_id=session_id,
        )

    @abstractmethod
    def receive(self, payload: Any, session_id: str, **kwargs) -> bool:
        """
        Receives a payload from the SessionManager.

        The specifics of how the payload is processed and whether a response payload
        is generated should be implemented in subclasses.


        :param payload: The payload to receive.
        :param session_id: The identifier of the session that the payload is associated with.
        :param kwargs: Additional keyword arguments specific to the implementation.
        :return: True if the payload was successfully received and processed, False otherwise.
        """
        # return false if not allowed to perform actions
        return self._can_perform_action()
