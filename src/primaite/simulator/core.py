"""Core of the PrimAITE Simulator."""
from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Extra

from primaite import getLogger

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
        """Use the request and context paramters to decide whether the action should be permitted."""
        pass


class AllowAllValidator(ActionPermissionValidator):
    """Always allows the action."""

    def __call__(self, request: List[str], context: Dict) -> bool:
        """Always allow the action."""
        return True


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

        ``validator`` is an instance of a subclass of `ActionPermissionValidator`. This is essentially a callable that
        accepts `request` and `context` and returns a boolean to represent whether the permission is granted to perform
        the action.

        :param func: Function that performs the request.
        :type func: Callable[[List[str], Dict], None]
        :param validator: Function that checks if the request is authenticated given the context.
        :type validator: ActionPermissionValidator
        """
        self.func: Callable[[List[str], Dict], None] = func
        self.validator: ActionPermissionValidator = validator


class ActionManager:
    """
    ActionManager is used by `SimComponent` instances to keep track of actions.

    Its main purpose is to be a lookup from action name to action function and corresponding validation function. This
    class is responsible for providing a consistent API for processing actions as well as helpful error messages.
    """

    def __init__(self) -> None:
        """Initialise ActionManager with an empty action lookup."""
        self.actions: Dict[str, Action] = {}

    def process_request(self, request: List[str], context: Dict) -> None:
        """Process an action request.

        :param request: A list of strings which specify what action to take. The first string must be one of the allowed
            actions, i.e. it must be a key of self.actions. The subsequent strings in the list are passed as parameters
            to the action function.
        :type request: List[str]
        :param context: Dictionary of additional information necessary to process or validate the request.
        :type context: Dict
        :raises RuntimeError: If the request parameter does not have a valid action identifier as the first item.
        """
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

    def add_action(self, name: str, action: Action) -> None:
        """Add an action to this action manager.

        :param name: The string associated to this action.
        :type name: str
        :param action: Action object.
        :type action: Action
        """
        if name in self.actions:
            msg = f"Attempted to register an action but the action name {name} is already taken."
            _LOGGER.error(msg)
            raise RuntimeError(msg)

        self.actions[name] = action


class SimComponent(BaseModel):
    """Extension of pydantic BaseModel with additional methods that must be defined by all classes in the simulator."""

    uuid: str
    """The component UUID."""

    def __init__(self, **kwargs):
        if not kwargs.get("uuid"):
            kwargs["uuid"] = str(uuid4())
        super().__init__(**kwargs)

    model_config = ConfigDict(arbitrary_types_allowed=True, extra=Extra.allow)
    uuid: str = str(uuid4())
    "The component UUID."

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.action_manager: Optional[ActionManager] = None

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
