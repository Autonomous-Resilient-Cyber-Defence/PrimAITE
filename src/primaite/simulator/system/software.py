from abc import abstractmethod
from enum import Enum
from ipaddress import IPv4Address
from typing import Any, Dict, Optional

from primaite.simulator.core import RequestManager, RequestType, SimComponent
from primaite.simulator.file_system.file_system import FileSystem, Folder
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.core.session_manager import Session
from primaite.simulator.system.core.sys_log import SysLog


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
    COMPROMISED = 2
    "The software's security has been compromised."
    OVERWHELMED = 3
    "he software is overwhelmed and not functioning properly."
    PATCHING = 4
    "The software is undergoing patching or updates."


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
    health_state_actual: SoftwareHealthState = SoftwareHealthState.GOOD
    "The actual health state of the software."
    health_state_visible: SoftwareHealthState = SoftwareHealthState.GOOD
    "The health state of the software visible to the red agent."
    criticality: SoftwareCriticality = SoftwareCriticality.LOWEST
    "The criticality level of the software."
    patching_count: int = 0
    "The count of patches applied to the software, defaults to 0."
    scanning_count: int = 0
    "The count of times the software has been scanned, defaults to 0."
    revealed_to_red: bool = False
    "Indicates if the software has been revealed to red agent, defaults is False."
    software_manager: Any = None
    "An instance of Software Manager that is used by the parent node."
    sys_log: SysLog = None
    "An instance of SysLog that is used by the parent node."
    file_system: FileSystem
    "The FileSystem of the Node the Software is installed on."
    folder: Optional[Folder] = None
    "The folder on the file system the Software uses."

    def _init_request_manager(self) -> RequestManager:
        rm = super()._init_request_manager()
        rm.add_request(
            "compromise",
            RequestType(
                func=lambda request, context: self.set_health_state(SoftwareHealthState.COMPROMISED),
            ),
        )
        rm.add_request("scan", RequestType(func=lambda request, context: self.scan()))
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
                "health_state": self.health_state_actual.value,
                "health_state_red_view": self.health_state_visible.value,
                "criticality": self.criticality.value,
                "patching_count": self.patching_count,
                "scanning_count": self.scanning_count,
                "revealed_to_red": self.revealed_to_red,
            }
        )
        return state

    def reset_component_for_episode(self, episode: int):
        """
        Resets the software component for a new episode.

        This method should ensure the software is ready for a new episode, including resetting any
        stateful properties or statistics, and clearing any message queues. The specifics of what constitutes a
        "reset" should be implemented in subclasses.
        """
        pass

    def set_health_state(self, health_state: SoftwareHealthState) -> None:
        """
        Assign a new health state to this software.

        Note: this should only be possible when the software is currently running, but the software base class has no
        operating state, only subclasses do. So subclasses will need to implement this check. TODO: check if this should
        be changed so that the base Software class has a running attr.

        :param health_state: New health state to assign to the software
        :type health_state: SoftwareHealthState
        """
        self.health_state_actual = health_state

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

    def scan(self) -> None:
        """Update the observed health status to match the actual health status."""
        self.health_state_visible = self.health_state_actual


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
    max_sessions: int = 1
    "The maximum number of sessions that the software can handle simultaneously. Default is 0."
    tcp: bool = True
    "Indicates if the software uses TCP protocol for communication. Default is True."
    udp: bool = True
    "Indicates if the software uses UDP protocol for communication. Default is True."
    port: Port
    "The port to which the software is connected."

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
                "port": self.port.value,
            }
        )
        return state

    def send(
        self,
        payload: Any,
        session_id: Optional[str] = None,
        dest_ip_address: Optional[IPv4Address] = None,
        dest_port: Optional[Port] = None,
        **kwargs,
    ) -> bool:
        """
        Sends a payload to the SessionManager.

        :param payload: The payload to be sent.
        :param dest_ip_address: The ip address of the payload destination.
        :param dest_port: The port of the payload destination.
        :param session_id: The Session ID the payload is to originate from. Optional.

        :return: True if successful, False otherwise.
        """
        return self.software_manager.send_payload_to_session_manager(
            payload=payload, dest_ip_address=dest_ip_address, dest_port=dest_port, session_id=session_id
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
        pass
