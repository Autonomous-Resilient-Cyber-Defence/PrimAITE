# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from __future__ import annotations

from abc import abstractmethod
from enum import Enum
from typing import Any, ClassVar, Dict, Optional, Type

from primaite import getLogger
from primaite.interface.request import RequestFormat, RequestResponse
from primaite.simulator.core import RequestManager, RequestPermissionValidator, RequestType
from primaite.simulator.system.software import IOSoftware, SoftwareHealthState

_LOGGER = getLogger(__name__)


class ServiceOperatingState(Enum):
    """Enumeration of Service Operating States."""

    RUNNING = 1
    "The service is currently running."
    STOPPED = 2
    "The service is not running."
    PAUSED = 3
    "The service is temporarily paused."
    DISABLED = 4
    "The service is disabled and cannot be started."
    INSTALLING = 5
    "The service is being installed or updated."
    RESTARTING = 6
    "The service is in the process of restarting."


class Service(IOSoftware):
    """
    Represents a Service in the simulation environment.

    Services are programs that run in the background and may perform input/output operations.
    """

    operating_state: ServiceOperatingState = ServiceOperatingState.STOPPED
    "The current operating state of the Service."

    restart_duration: int = 5
    "How many timesteps does it take to restart this service."

    restart_countdown: Optional[int] = None
    "If currently restarting, how many timesteps remain until the restart is finished."

    _registry: ClassVar[Dict[str, Type["Service"]]] = {}
    """Registry of service types. Automatically populated when subclasses are defined."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __init_subclass__(cls, identifier: str = "default", **kwargs: Any) -> None:
        """
        Register a hostnode type.

        :param identifier: Uniquely specifies an hostnode class by name. Used for finding items by config.
        :type identifier: str
        :raises ValueError: When attempting to register an hostnode with a name that is already allocated.
        """
        if identifier == "default":
            return
        # Enforce lowercase registry entries because it makes comparisons everywhere else much easier.
        identifier = identifier.lower()
        super().__init_subclass__(**kwargs)
        if identifier in cls._registry:
            raise ValueError(f"Tried to define new hostnode {identifier}, but this name is already reserved.")
        cls._registry[identifier] = cls

    def _can_perform_action(self) -> bool:
        """
        Checks if the service can perform actions.

        This is done by checking if the service is operating properly or the node it is installed
        in is operational.

        Returns true if the software can perform actions.
        """
        if not super()._can_perform_action():
            return False

        if self.operating_state is not ServiceOperatingState.RUNNING:
            # service is not running
            self.sys_log.debug(f"Cannot perform action: {self.name} is {self.operating_state.name}")
            return False

        return True

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
        return super().receive(payload=payload, session_id=session_id, **kwargs)

    def _init_request_manager(self) -> RequestManager:
        """
        Initialise the request manager.

        More information in user guide and docstring for SimComponent._init_request_manager.
        """
        _is_service_running = Service._StateValidator(service=self, state=ServiceOperatingState.RUNNING)
        _is_service_stopped = Service._StateValidator(service=self, state=ServiceOperatingState.STOPPED)
        _is_service_paused = Service._StateValidator(service=self, state=ServiceOperatingState.PAUSED)
        _is_service_disabled = Service._StateValidator(service=self, state=ServiceOperatingState.DISABLED)

        rm = super()._init_request_manager()
        rm.add_request(
            "scan",
            RequestType(
                func=lambda request, context: RequestResponse.from_bool(self.scan()), validator=_is_service_running
            ),
        )
        rm.add_request(
            "stop",
            RequestType(
                func=lambda request, context: RequestResponse.from_bool(self.stop()), validator=_is_service_running
            ),
        )
        rm.add_request(
            "start",
            RequestType(
                func=lambda request, context: RequestResponse.from_bool(self.start()), validator=_is_service_stopped
            ),
        )
        rm.add_request(
            "pause",
            RequestType(
                func=lambda request, context: RequestResponse.from_bool(self.pause()), validator=_is_service_running
            ),
        )
        rm.add_request(
            "resume",
            RequestType(
                func=lambda request, context: RequestResponse.from_bool(self.resume()), validator=_is_service_paused
            ),
        )
        rm.add_request(
            "restart",
            RequestType(
                func=lambda request, context: RequestResponse.from_bool(self.restart()), validator=_is_service_running
            ),
        )
        rm.add_request("disable", RequestType(func=lambda request, context: RequestResponse.from_bool(self.disable())))
        rm.add_request(
            "enable",
            RequestType(
                func=lambda request, context: RequestResponse.from_bool(self.enable()), validator=_is_service_disabled
            ),
        )
        rm.add_request(
            "fix",
            RequestType(
                func=lambda request, context: RequestResponse.from_bool(self.fix()), validator=_is_service_running
            ),
        )
        return rm

    @abstractmethod
    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        Please see :py:meth:`primaite.simulator.core.SimComponent.describe_state` for a more detailed explanation.

        :return: Current state of this object and child objects.
        :rtype: Dict
        """
        state = super().describe_state()
        state["operating_state"] = self.operating_state.value
        state["health_state_actual"] = self.health_state_actual.value
        state["health_state_visible"] = self.health_state_visible.value
        return state

    def stop(self) -> bool:
        """Stop the service."""
        if self.operating_state in [ServiceOperatingState.RUNNING, ServiceOperatingState.PAUSED]:
            self.sys_log.info(f"Stopping service {self.name}")
            self.operating_state = ServiceOperatingState.STOPPED
            return True
        return False

    def start(self, **kwargs) -> bool:
        """Start the service."""
        # cant start the service if the node it is on is off
        if not super()._can_perform_action():
            return False

        if self.operating_state == ServiceOperatingState.STOPPED:
            self.sys_log.info(f"Starting service {self.name}")
            self.operating_state = ServiceOperatingState.RUNNING
            # set software health state to GOOD if initially set to UNUSED
            if self.health_state_actual == SoftwareHealthState.UNUSED:
                self.set_health_state(SoftwareHealthState.GOOD)
            return True
        return False

    def pause(self) -> bool:
        """Pause the service."""
        if self.operating_state == ServiceOperatingState.RUNNING:
            self.sys_log.info(f"Pausing service {self.name}")
            self.operating_state = ServiceOperatingState.PAUSED
            return True
        return False

    def resume(self) -> bool:
        """Resume paused service."""
        if self.operating_state == ServiceOperatingState.PAUSED:
            self.sys_log.info(f"Resuming service {self.name}")
            self.operating_state = ServiceOperatingState.RUNNING
            return True
        return False

    def restart(self) -> bool:
        """Restart running service."""
        if self.operating_state in [ServiceOperatingState.RUNNING, ServiceOperatingState.PAUSED]:
            self.sys_log.info(f"Pausing service {self.name}")
            self.operating_state = ServiceOperatingState.RESTARTING
            self.restart_countdown = self.restart_duration
            return True
        return False

    def disable(self) -> bool:
        """Disable the service."""
        self.sys_log.info(f"Disabling Application {self.name}")
        self.operating_state = ServiceOperatingState.DISABLED
        return True

    def enable(self) -> bool:
        """Enable the disabled service."""
        if self.operating_state == ServiceOperatingState.DISABLED:
            self.sys_log.info(f"Enabling Application {self.name}")
            self.operating_state = ServiceOperatingState.STOPPED
            return True
        return False

    def apply_timestep(self, timestep: int) -> None:
        """
        Apply a single timestep of simulation dynamics to this service.

        In this instance, if any multi-timestep processes are currently occurring (such as restarting or installation),
        then they are brought one step closer to being finished.

        :param timestep: The current timestep number. (Amount of time since simulation episode began)
        :type timestep: int
        """
        super().apply_timestep(timestep)
        if self.operating_state == ServiceOperatingState.RESTARTING:
            if self.restart_countdown <= 0:
                self.sys_log.debug(f"Restarting finished for service {self.name}")
                self.operating_state = ServiceOperatingState.RUNNING
            self.restart_countdown -= 1

    class _StateValidator(RequestPermissionValidator):
        """
        When requests come in, this validator will only let them through if the service is in the correct state.

        This is useful because most actions require the service to be in a specific state.
        """

        service: Service
        """Save a reference to the service instance."""

        state: ServiceOperatingState
        """The state of the service to validate."""

        def __call__(self, request: RequestFormat, context: Dict) -> bool:
            """Return whether the service is in the state we are validating for."""
            return self.service.operating_state == self.state

        @property
        def fail_message(self) -> str:
            """Message that is reported when a request is rejected by this validator."""
            return (
                f"Cannot perform request on service '{self.service.name}' because it is not in the "
                f"{self.state.name} state."
            )
