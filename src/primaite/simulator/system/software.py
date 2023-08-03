from enum import Enum

from primaite.simulator.core import SimComponent


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


class ApplicationOperatingState(Enum):
    """Enumeration of Application Operating States."""

    CLOSED = 0
    "The application is closed or not running."
    RUNNING = 1
    "The application is running."
    INSTALLING = 3
    "The application is being installed or updated."


class ServiceOperatingState(Enum):
    """Enumeration of Service Operating States."""

    STOPPED = 0
    "The service is not running."
    RUNNING = 1
    "The service is currently running."
    RESTARTING = 2
    "The service is in the process of restarting."
    INSTALLING = 3
    "The service is being installed or updated."
    PAUSED = 4
    "The service is temporarily paused."
    DISABLED = 5
    "The service is disabled and cannot be started."


class ProcessOperatingState(Enum):
    """Enumeration of Process Operating States."""

    RUNNING = 1
    "The process is running."
    PAUSED = 2
    "The process is temporarily paused."


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
    Represents software information along with its health, criticality, and status.

    This class inherits from the Pydantic BaseModel and provides a structured way to store
    information about software entities.

    Attributes:
        name (str): The name of the software.
        health_state_actual (SoftwareHealthState): The actual health state of the software.
        health_state_visible (SoftwareHealthState): The health state of the software visible to users.
        criticality (SoftwareCriticality): The criticality level of the software.
        patching_count (int, optional): The count of patches applied to the software. Default is 0.
        scanning_count (int, optional): The count of times the software has been scanned. Default is 0.
        revealed_to_red (bool, optional): Indicates if the software has been revealed to red team. Default is False.
    """

    name: str
    health_state_actual: SoftwareHealthState
    health_state_visible: SoftwareHealthState
    criticality: SoftwareCriticality
    patching_count: int = 0
    scanning_count: int = 0
    revealed_to_red: bool = False
