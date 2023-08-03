"""Core of the PrimAITE Simulator."""
from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from primaite import getLogger
from primaite.simulator.domain import AccountGroup

_LOGGER = getLogger(__name__)


class ActionPermissionValidator(ABC):
    """
    Base class for action validators.

    The permissions manager is designed to be generic. So, although in the first instance the permissions
    are evaluated purely on membership to AccountGroup, this class can support validating permissions based on any
    arbitrary criteria.
    """

    @abstractmethod
    def __call__(self, request: List[str], context: Dict) -> bool:
        """TODO."""
        pass


class AllowAllValidator(ActionPermissionValidator):
    """Always allows the action."""

    def __call__(self, request: List[str], context: Dict) -> bool:
        """Always allow the action."""
        return True


class GroupMembershipValidator(ActionPermissionValidator):
    """Permit actions based on group membership."""

    def __init__(self, allowed_groups: List[AccountGroup]) -> None:
        """TODO."""
        self.allowed_groups = allowed_groups

    def __call__(self, request: List[str], context: Dict) -> bool:
        """Permit the action if the request comes from an account which belongs to the right group."""
        # if context request source is part of any groups mentioned in self.allow_groups, return true, otherwise false
        requestor_groups: List[str] = context["request_source"]["groups"]
        for allowed_group in self.allowed_groups:
            if allowed_group.name in requestor_groups:
                return True
        return False


class Action:
    """
    This object stores data related to a single action.

    This includes the callable that can execute the action request, and the validator that will decide whether
    the action can be performed or not.
    """

    def __init__(self, func: Callable[[List[str], Dict], None], validator: ActionPermissionValidator) -> None:
        """
        Save the functions that are for this action.

        Here's a description for the intended use of both of these.

        ``func`` is a function that accepts a request and a context dict. Typically this would be a lambda function
        that invokes a class method of your SimComponent. For example if the component is a node and the action is for
        turning it off, then the SimComponent should have a turn_off(self) method that does not need to accept any args.
        Then, this Action will be given something like ``func = lambda request, context: self.turn_off()``.

        :param func: Function that performs the request.
        :type func: Callable[[List[str], Dict], None]
        :param validator: Function that checks if the request is authenticated given the context.
        :type validator: ActionPermissionValidator
        """
        self.func: Callable[[List[str], Dict], None] = func
        self.validator: ActionPermissionValidator = validator


class ActionManager:
    """TODO."""

    def __init__(self) -> None:
        """TODO."""
        self.actions: Dict[str, Action]

    def process_request(self, request: List[str], context: Dict) -> None:
        """Process action request."""
        action_key = request[0]

        if action_key not in self.actions:
            msg = (
                f"Action request {request} could not be processed because {action_key} is not a valid action",
                "within this ActionManager",
            )
            _LOGGER.error(msg)
            raise RuntimeError(msg)

        action = self.actions[action_key]
        action_options = request[1:]

        if not action.validator(action_options, context):
            _LOGGER.debug(f"Action request {request} was denied due to insufficient permissions")
            return

        action.func(action_options, context)


class SimComponent(BaseModel):
    """Extension of pydantic BaseModel with additional methods that must be defined by all classes in  the simulator."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    uuid: str
    "The component UUID."

    def __init__(self, **kwargs) -> None:
        self.action_manager: Optional[ActionManager] = None
        super().__init__(**kwargs)

    @abstractmethod
    def describe_state(self) -> Dict:
        """
        Return a dictionary describing the state of this object and any objects managed by it.

        This is similar to pydantic ``model_dump()``, but it only outputs information about the objects owned by this
        object. If there are objects referenced by this object that are owned by something else, it is not included in
        this output.
        """
        return {}

    def apply_action(self, action: List[str], context: Dict = {}) -> None:
        """
        Apply an action to a simulation component. Action data is passed in as a 'namespaced' list of strings.

        If the list only has one element, the action is intended to be applied directly to this object. If the list has
        multiple entries, the action is passed to the child of this object specified by the first one or two entries.
        This is essentially a namespace.

        For example, ["turn_on",] is meant to apply an action of 'turn on' to this component.

        However, ["services", "email_client", "turn_on"] is meant to 'turn on' this component's email client service.

        :param action: List describing the action to apply to this object.
        :type action: List[str]
        """
        if self.action_manager is None:
            return
        self.action_manager.process_request(action, context)

    def apply_timestep(self, timestep: int) -> None:
        """
        Apply a timestep evolution to this component.

        Override this method with anything that happens automatically in the component such as scheduled restarts or
        sending data.
        """
        pass

    def reset_component_for_episode(self):
        """
        Reset this component to its original state for a new episode.

        Override this method with anything that needs to happen within the component for it to be reset.
        """
        pass
