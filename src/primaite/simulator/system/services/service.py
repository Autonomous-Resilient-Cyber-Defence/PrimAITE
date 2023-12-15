from enum import Enum
from typing import Any, Dict, Optional

from primaite import getLogger
from primaite.simulator.core import RequestManager, RequestType
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.health_state_visible = SoftwareHealthState.UNUSED
        self.health_state_actual = SoftwareHealthState.UNUSED

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
            _LOGGER.error(f"Cannot perform action: {self.name} is {self.operating_state.name}")
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

    def set_original_state(self):
        """Sets the original state."""
        super().set_original_state()
        vals_to_include = {"operating_state", "restart_duration", "restart_countdown"}
        self._original_state.update(self.model_dump(include=vals_to_include))

    def _init_request_manager(self) -> RequestManager:
        rm = super()._init_request_manager()
        rm.add_request("scan", RequestType(func=lambda request, context: self.scan()))
        rm.add_request("stop", RequestType(func=lambda request, context: self.stop()))
        rm.add_request("start", RequestType(func=lambda request, context: self.start()))
        rm.add_request("pause", RequestType(func=lambda request, context: self.pause()))
        rm.add_request("resume", RequestType(func=lambda request, context: self.resume()))
        rm.add_request("restart", RequestType(func=lambda request, context: self.restart()))
        rm.add_request("disable", RequestType(func=lambda request, context: self.disable()))
        rm.add_request("enable", RequestType(func=lambda request, context: self.enable()))
        return rm

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

    def stop(self) -> None:
        """Stop the service."""
        if self.operating_state in [ServiceOperatingState.RUNNING, ServiceOperatingState.PAUSED]:
            self.sys_log.info(f"Stopping service {self.name}")
            self.operating_state = ServiceOperatingState.STOPPED
            self.health_state_actual = SoftwareHealthState.UNUSED

    def start(self, **kwargs) -> None:
        """Start the service."""
        # cant start the service if the node it is on is off
        if not super()._can_perform_action():
            return

        if self.operating_state == ServiceOperatingState.STOPPED:
            self.sys_log.info(f"Starting service {self.name}")
            self.operating_state = ServiceOperatingState.RUNNING
            self.health_state_actual = SoftwareHealthState.GOOD

    def pause(self) -> None:
        """Pause the service."""
        if self.operating_state == ServiceOperatingState.RUNNING:
            self.sys_log.info(f"Pausing service {self.name}")
            self.operating_state = ServiceOperatingState.PAUSED
            self.health_state_actual = SoftwareHealthState.OVERWHELMED

    def resume(self) -> None:
        """Resume paused service."""
        if self.operating_state == ServiceOperatingState.PAUSED:
            self.sys_log.info(f"Resuming service {self.name}")
            self.operating_state = ServiceOperatingState.RUNNING
            self.health_state_actual = SoftwareHealthState.GOOD

    def restart(self) -> None:
        """Restart running service."""
        if self.operating_state in [ServiceOperatingState.RUNNING, ServiceOperatingState.PAUSED]:
            self.sys_log.info(f"Pausing service {self.name}")
            self.operating_state = ServiceOperatingState.RESTARTING
            self.health_state_actual = SoftwareHealthState.OVERWHELMED
            self.restart_countdown = self.restart_duration

    def disable(self) -> None:
        """Disable the service."""
        self.sys_log.info(f"Disabling Application {self.name}")
        self.operating_state = ServiceOperatingState.DISABLED
        self.health_state_actual = SoftwareHealthState.OVERWHELMED

    def enable(self) -> None:
        """Enable the disabled service."""
        if self.operating_state == ServiceOperatingState.DISABLED:
            self.sys_log.info(f"Enabling Application {self.name}")
            self.operating_state = ServiceOperatingState.STOPPED
            self.health_state_actual = SoftwareHealthState.OVERWHELMED

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
                _LOGGER.debug(f"Restarting finished for service {self.name}")
                self.operating_state = ServiceOperatingState.RUNNING
                self.health_state_actual = SoftwareHealthState.GOOD
            self.restart_countdown -= 1
