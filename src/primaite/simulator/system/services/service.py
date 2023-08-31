from abc import abstractmethod
from enum import Enum
from typing import Any, Dict, Optional

from primaite import getLogger
from primaite.simulator.core import Action, ActionManager
from primaite.simulator.system.software import IOSoftware

_LOGGER = getLogger(__name__)


class ServiceOperatingState(Enum):
    """Enumeration of Service Operating States."""

    RUNNING = 1
    "The service is currently running."
    STOPPED = 2
    "The service is not running."
    INSTALLING = 3
    "The service is being installed or updated."
    RESTARTING = 4
    "The service is in the process of restarting."
    PAUSED = 5
    "The service is temporarily paused."
    DISABLED = 6
    "The service is disabled and cannot be started."


class Service(IOSoftware):
    """
    Represents a Service in the simulation environment.

    Services are programs that run in the background and may perform input/output operations.
    """

    operating_state: ServiceOperatingState
    "The current operating state of the Service."
    restart_duration: int = 5
    "How many timesteps does it take to restart this service."
    _restart_countdown: Optional[int] = None
    "If currently restarting, how many timesteps remain until the restart is finished."

    def _init_action_manager(self) -> ActionManager:
        am = super()._init_action_manager()
        am.add_action("stop", Action(func=lambda request, context: self.stop()))
        am.add_action("start", Action(func=lambda request, context: self.start()))
        am.add_action("pause", Action(func=lambda request, context: self.pause()))
        am.add_action("resume", Action(func=lambda request, context: self.resume()))
        am.add_action("restart", Action(func=lambda request, context: self.restart()))
        am.add_action("disable", Action(func=lambda request, context: self.disable()))
        am.add_action("enable", Action(func=lambda request, context: self.enable()))
        return am

    @abstractmethod
    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        Please see :py:meth:`primaite.simulator.core.SimComponent.describe_state` for a more detailed explanation.

        :return: Current state of this object and child objects.
        :rtype: Dict
        """
        state = super().describe_state()
        state.update({"operating_state": self.operating_state.name})
        return state

    def reset_component_for_episode(self, episode: int):
        """
        Resets the Service component for a new episode.

        This method ensures the Service is ready for a new episode, including resetting any
        stateful properties or statistics, and clearing any message queues.
        """
        pass

    def send(self, payload: Any, session_id: str, **kwargs) -> bool:
        """
        Sends a payload to the SessionManager.

        The specifics of how the payload is processed and whether a response payload
        is generated should be implemented in subclasses.

        :param payload: The payload to send.
        :return: True if successful, False otherwise.
        """
        pass

    def receive(self, payload: Any, session_id: str, **kwargs) -> bool:
        """
        Receives a payload from the SessionManager.

        The specifics of how the payload is processed and whether a response payload
        is generated should be implemented in subclasses.

        :param payload: The payload to receive.
        :return: True if successful, False otherwise.
        """
        pass

    def stop(self) -> None:
        """Stop the service."""
        _LOGGER.debug(f"Stopping service {self.name}")
        if self.operating_state in [ServiceOperatingState.RUNNING, ServiceOperatingState.PAUSED]:
            self.parent.sys_log.info(f"Stopping service {self.name}")
            self.operating_state = ServiceOperatingState.STOPPED

    def start(self) -> None:
        """Start the service."""
        _LOGGER.debug(f"Starting service {self.name}")
        if self.operating_state == ServiceOperatingState.STOPPED:
            self.parent.sys_log.info(f"Starting service {self.name}")
            self.operating_state = ServiceOperatingState.RUNNING

    def pause(self) -> None:
        """Pause the service."""
        _LOGGER.debug(f"Pausing service {self.name}")
        if self.operating_state == ServiceOperatingState.RUNNING:
            self.parent.sys_log.info(f"Pausing service {self.name}")
            self.operating_state = ServiceOperatingState.PAUSED

    def resume(self) -> None:
        """Resume paused service."""
        _LOGGER.debug(f"Resuming service {self.name}")
        if self.operating_state == ServiceOperatingState.PAUSED:
            self.parent.sys_log.info(f"Resuming service {self.name}")
            self.operating_state = ServiceOperatingState.RUNNING

    def restart(self) -> None:
        """Restart running service."""
        _LOGGER.debug(f"Restarting service {self.name}")
        if self.operating_state in [ServiceOperatingState.RUNNING, ServiceOperatingState.PAUSED]:
            self.parent.sys_log.info(f"Pausing service {self.name}")
            self.operating_state = ServiceOperatingState.RESTARTING
            self.restart_countdown = self.restarting_duration  # TODO: implement restart duration

    def disable(self) -> None:
        """Disable the service."""
        _LOGGER.debug(f"Disabling service {self.name}")
        self.parent.sys_log.info(f"Disabling Application {self.name}")
        self.operating_state = ServiceOperatingState.DISABLED

    def enable(self) -> None:
        """Enable the disabled service."""
        _LOGGER.debug(f"Enabling service {self.name}")
        if self.operating_state == ServiceOperatingState.DISABLED:
            self.parent.sys_log.info(f"Enabling Application {self.name}")
            self.operating_state = ServiceOperatingState.STOPPED

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
            self.restart_countdown -= 1
