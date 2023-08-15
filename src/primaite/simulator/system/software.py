from abc import abstractmethod
from enum import Enum
from typing import Any, Dict, List, Set

from primaite.simulator.core import SimComponent
from primaite.simulator.network.transmission.transport_layer import Port


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
    health_state_actual: SoftwareHealthState
    "The actual health state of the software."
    health_state_visible: SoftwareHealthState
    "The health state of the software visible to the red agent."
    criticality: SoftwareCriticality
    "The criticality level of the software."
    patching_count: int = 0
    "The count of patches applied to the software, defaults to 0."
    scanning_count: int = 0
    "The count of times the software has been scanned, defaults to 0."
    revealed_to_red: bool = False
    "Indicates if the software has been revealed to red agent, defaults is False."

    @abstractmethod
    def describe_state(self) -> Dict:
        """
        Describes the current state of the software.

        The specifics of the software's state, including its health, criticality,
        and any other pertinent information, should be implemented in subclasses.

        :return: A dictionary containing key-value pairs representing the current state of the software.
        :rtype: Dict
        """
        pass

    def apply_action(self, action: List[str]) -> None:
        """
        Applies a list of actions to the software.

        The specifics of how these actions are applied should be implemented in subclasses.

        :param action: A list of actions to apply.
        :type action: List[str]
        """
        pass

    def reset_component_for_episode(self, episode: int):
        """
        Resets the software component for a new episode.

        This method should ensure the software is ready for a new episode, including resetting any
        stateful properties or statistics, and clearing any message queues. The specifics of what constitutes a
        "reset" should be implemented in subclasses.
        """
        pass

    @staticmethod
    def get_install():
        """
        This method ensures the software has to have a way to install it.

        This can be used by the software manager to install the software.
        """
        pass


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
    ports: Set[Port]
    "The set of ports to which the software is connected."

    @abstractmethod
    def describe_state(self) -> Dict:
        """
        Describes the current state of the software.

        The specifics of the software's state, including its health, criticality,
        and any other pertinent information, should be implemented in subclasses.

        :return: A dictionary containing key-value pairs representing the current state of the software.
        :rtype: Dict
        """
        pass

    def send(self, payload: Any, session_id: str, **kwargs) -> bool:
        """
        Sends a payload to the SessionManager.

        The specifics of how the payload is processed and whether a response payload
        is generated should be implemented in subclasses.

        :param payload: The payload to send.
        :param session_id: The identifier of the session that the payload is associated with.
        :param kwargs: Additional keyword arguments specific to the implementation.
        :return: True if the payload was successfully sent, False otherwise.
        """
        pass

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
