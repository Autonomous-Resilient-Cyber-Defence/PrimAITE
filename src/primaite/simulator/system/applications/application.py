# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from __future__ import annotations

from abc import abstractmethod
from enum import Enum
from typing import Any, ClassVar, Dict, Optional, Set, Type

from primaite.interface.request import RequestFormat, RequestResponse
from primaite.simulator.core import RequestManager, RequestPermissionValidator, RequestType
from primaite.simulator.system.software import IOSoftware, SoftwareHealthState


class ApplicationOperatingState(Enum):
    """Enumeration of Application Operating States."""

    RUNNING = 1
    "The application is running."
    CLOSED = 2
    "The application is closed or not running."
    INSTALLING = 3
    "The application is being installed or updated."


class Application(IOSoftware):
    """
    Represents an Application in the simulation environment.

    Applications are user-facing programs that may perform input/output operations.
    """

    operating_state: ApplicationOperatingState = ApplicationOperatingState.CLOSED
    "The current operating state of the Application."
    execution_control_status: str = "manual"
    "Control status of the application's execution. It could be 'manual' or 'automatic'."
    num_executions: int = 0
    "The number of times the application has been executed. Default is 0."
    groups: Set[str] = set()
    "The set of groups to which the application belongs."
    install_duration: int = 2
    "How long it takes to install the application."
    install_countdown: Optional[int] = None
    "The countdown to the end of the installation process. None if not currently installing"

    _registry: ClassVar[Dict[str, Type["Application"]]] = {}
    """Registry of application types. Automatically populated when subclasses are defined."""

    def __init_subclass__(cls, identifier: str = "default", **kwargs: Any) -> None:
        """
        Register an application type.

        :param identifier: Uniquely specifies an application class by name. Used for finding items by config.
        :type identifier: str
        :raises ValueError: When attempting to register an application with a name that is already allocated.
        """
        if identifier == "default":
            return
        super().__init_subclass__(**kwargs)
        if identifier in cls._registry:
            raise ValueError(f"Tried to define new application {identifier}, but this name is already reserved.")
        cls._registry[identifier] = cls

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _init_request_manager(self) -> RequestManager:
        """
        Initialise the request manager.

        More information in user guide and docstring for SimComponent._init_request_manager.
        """
        _is_application_running = Application._StateValidator(application=self, state=ApplicationOperatingState.RUNNING)

        rm = super()._init_request_manager()
        rm.add_request(
            "scan",
            RequestType(
                func=lambda request, context: RequestResponse.from_bool(self.scan()), validator=_is_application_running
            ),
        )
        rm.add_request(
            "close",
            RequestType(
                func=lambda request, context: RequestResponse.from_bool(self.close()), validator=_is_application_running
            ),
        )
        rm.add_request(
            "fix",
            RequestType(
                func=lambda request, context: RequestResponse.from_bool(self.fix()), validator=_is_application_running
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
        state.update(
            {
                "operating_state": self.operating_state.value,
                "execution_control_status": self.execution_control_status,
                "num_executions": self.num_executions,
                "groups": list(self.groups),
            }
        )
        return state

    def apply_timestep(self, timestep: int) -> None:
        """
        Apply a timestep to the application.

        :param timestep: The current timestep of the simulation.
        """
        super().apply_timestep(timestep=timestep)
        if self.operating_state is ApplicationOperatingState.INSTALLING:
            self.install_countdown -= 1
            if self.install_countdown <= 0:
                self.operating_state = ApplicationOperatingState.RUNNING
                self.health_state_actual = SoftwareHealthState.GOOD
                self.install_countdown = None

    def pre_timestep(self, timestep: int) -> None:
        """Apply pre-timestep logic."""
        super().pre_timestep(timestep)
        self.num_executions = 0

    def _can_perform_action(self) -> bool:
        """
        Checks if the application can perform actions.

        This is done by checking if the application is operating properly or the node it is installed
        in is operational.

        Returns true if the software can perform actions.
        """
        if not super()._can_perform_action():
            return False

        if self.operating_state is not self.operating_state.RUNNING:
            # service is not running
            self.sys_log.error(f"Cannot perform action: {self.name} is {self.operating_state.name}")
            return False

        return True

    def run(self) -> None:
        """Open the Application."""
        if not super()._can_perform_action():
            return

        if self.operating_state == ApplicationOperatingState.CLOSED:
            self.sys_log.info(f"Running Application {self.name}")
            self.operating_state = ApplicationOperatingState.RUNNING
            # set software health state to GOOD if initially set to UNUSED
            if self.health_state_actual == SoftwareHealthState.UNUSED:
                self.set_health_state(SoftwareHealthState.GOOD)

    def _application_loop(self):
        """The main application loop."""
        pass

    def close(self) -> bool:
        """Close the Application."""
        if self.operating_state == ApplicationOperatingState.RUNNING:
            self.sys_log.info(f"Closed Application{self.name}")
            self.operating_state = ApplicationOperatingState.CLOSED
        return True

    def install(self) -> None:
        """Install Application."""
        super().install()
        if self.operating_state == ApplicationOperatingState.CLOSED:
            self.operating_state = ApplicationOperatingState.INSTALLING
            self.install_countdown = self.install_duration

    def receive(self, payload: Any, session_id: str, **kwargs) -> bool:
        """
        Receives a payload from the SessionManager.

        The specifics of how the payload is processed and whether a response payload
        is generated should be implemented in subclasses.

        :param payload: The payload to receive.
        :return: True if successful, False otherwise.
        """
        return super().receive(payload=payload, session_id=session_id, **kwargs)

    class _StateValidator(RequestPermissionValidator):
        """
        When requests come in, this validator will only let them through if the application is in the correct state.

        This is useful because most actions require the application to be in a specific state.
        """

        application: Application
        """Save a reference to the application instance."""

        state: ApplicationOperatingState
        """The state of the application to validate."""

        def __call__(self, request: RequestFormat, context: Dict) -> bool:
            """Return whether the application is in the state we are validating for."""
            return self.application.operating_state == self.state

        @property
        def fail_message(self) -> str:
            """Message that is reported when a request is rejected by this validator."""
            return (
                f"Cannot perform request on application '{self.application.name}' because it is not in the "
                f"{self.state.name} state."
            )

    def _can_perform_network_action(self) -> bool:
        """
        Checks if the application can perform outbound network actions.

        First confirms application suitability via the can_perform_action method.
        Then confirms that the host has an enabled NIC that can be used for outbound traffic.

        :return: True if outbound network actions can be performed, otherwise False.
        :rtype bool:
        """
        if not super()._can_perform_action():
            return False

        for nic in self.software_manager.node.network_interface.values():
            if nic.enabled:
                return True
        return False
