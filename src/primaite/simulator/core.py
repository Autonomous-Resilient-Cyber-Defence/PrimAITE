# flake8: noqa
"""Core of the PrimAITE Simulator."""
from abc import ABC, abstractmethod
from typing import Callable, ClassVar, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, ConfigDict

from primaite import getLogger

_LOGGER = getLogger(__name__)


class ActionPermissionValidator(BaseModel):
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


class Action(BaseModel):
    """
    This object stores data related to a single action.

    This includes the callable that can execute the action request, and the validator that will decide whether
    the action can be performed or not.
    """

    func: Callable[[Dict], None]
    """
    ``func`` is a function that accepts a request and a context dict. Typically this would be a lambda function
    that invokes a class method of your SimComponent. For example if the component is a node and the action is for
    turning it off, then the SimComponent should have a turn_off(self) method that does not need to accept any args.
    Then, this Action will be given something like ``func = lambda request, context: self.turn_off()``.

    ``func`` can also be another action manager, since ActionManager is a callable with a signature that matches what is
    expected by ``func``.
    """
    validator: ActionPermissionValidator = AllowAllValidator()
    """
    ``validator`` is an instance of `ActionPermissionValidator`. This is essentially a callable that
    accepts `request` and `context` and returns a boolean to represent whether the permission is granted to perform
    the action. The default validator will allow
    """


# TODO: maybe this can be renamed to something like action selector?
# Because there are two ways it's used, to select from a list of action verbs, or to select a child object to which to
# forward the request.
class ActionManager(BaseModel):
    """
    ActionManager is used by `SimComponent` instances to keep track of actions.

    Its main purpose is to be a lookup from action name to action function and corresponding validation function. This
    class is responsible for providing a consistent API for processing actions as well as helpful error messages.
    """

    actions: Dict[str, Action] = {}
    """maps action verb to an action object."""

    def __call__(self, request: Dict, context: Dict) -> None:
        """
        Process an action request.

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
        """
        Add an action to this action manager.

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

    def remove_action(self, name: str) -> None:
        """
        Remove an action from this manager.

        :param name: name identifier of the action
        :type name: str
        """
        if name not in self.actions:
            msg = f"Attempted to remove action {name} from action manager, but it was not registered."
            _LOGGER.error(msg)
            raise RuntimeError(msg)

        self.actions.pop(name)

    def get_action_tree(self) -> List[List[str]]:
        """Recursively generate action tree for this component."""
        actions = []
        for act_name, act in self.actions.items():
            if isinstance(act.func, ActionManager):
                sub_actions = act.func.get_action_tree()
                sub_actions = [[act_name] + a for a in sub_actions]
                actions.extend(sub_actions)
            else:
                actions.append([act_name])
        return actions


class SimComponent(BaseModel):
    """Extension of pydantic BaseModel with additional methods that must be defined by all classes in the simulator."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")
    """Configure pydantic to allow arbitrary types and to let the instance have attributes not present in model."""

    uuid: str
    """The component UUID."""

    def __init__(self, **kwargs):
        if not kwargs.get("uuid"):
            kwargs["uuid"] = str(uuid4())
        super().__init__(**kwargs)
        self._action_manager: ActionManager = self._init_action_manager()
        self._parent: Optional["SimComponent"] = None

    def _init_action_manager(self) -> ActionManager:
        """
        Initialise the action manager for this component.

        When using a hierarchy of components, the child classes should call the parent class's _init_action_manager and
        add additional actions on top of the existing generic ones.

        Example usage for inherited classes:

        ..code::python

            class WebBrowser(Application):
            def _init_action_manager(self) -> ActionManager:
                am = super()._init_action_manager() # all actions generic to any Application get initialised
                am.add_action(...) # initialise any actions specific to the web browser
                return am

        :return: Actiona manager object belonging to this sim component.
        :rtype: ActionManager
        """
        return ActionManager()

    @abstractmethod
    def describe_state(self) -> Dict:
        """
        Return a dictionary describing the state of this object and any objects managed by it.

        This is similar to pydantic ``model_dump()``, but it only outputs information about the objects owned by this
        object. If there are objects referenced by this object that are owned by something else, it is not included in
        this output.
        """
        state = {
            "uuid": self.uuid,
        }
        return state

    def possible_actions(self) -> List[List[str]]:
        """Enumerate all actions that this component can accept.

        :return: List of all action strings that can be passed to this component.
        :rtype: List[Dict[str]]
        """
        action_list = ActionManager  # TODO: extract possible actions? how to do this neatly?

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
        self.action_manager(action, context)

    def apply_timestep(self, timestep: int) -> None:
        """
        Apply a timestep evolution to this component.

        Override this method with anything that happens automatically in the component such as scheduled restarts or
        sending data.
        """
        pass

    def reset_component_for_episode(self, episode: int):
        """
        Reset this component to its original state for a new episode.

        Override this method with anything that needs to happen within the component for it to be reset.
        """
        pass

    @property
    def parent(self) -> "SimComponent":
        """Reference to the parent object which manages this object.

        :return: Parent object.
        :rtype: SimComponent
        """
        return self._parent

    @parent.setter
    def parent(self, new_parent: Union["SimComponent", None]) -> None:
        if self._parent and new_parent:
            msg = f"Overwriting parent of {self.uuid}. Old parent: {self._parent.uuid}, New parent: {new_parent.uuid}"
            _LOGGER.warn(msg)
            raise RuntimeWarning(msg)
        self._parent = new_parent
