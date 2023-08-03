"""Core of the PrimAITE Simulator."""
from abc import abstractmethod
from typing import Callable, Dict, List
from uuid import uuid4

from pydantic import BaseModel, ConfigDict


class SimComponent(BaseModel):
    """Extension of pydantic BaseModel with additional methods that must be defined by all classes in  the simulator."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    uuid: str
    "The component UUID."

    def __init__(self, **kwargs):
        if not kwargs.get("uuid"):
            kwargs["uuid"] = str(uuid4())
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

    def apply_action(self, action: List[str]) -> None:
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
        possible_actions = self._possible_actions()
        if action[0] in possible_actions:
            # take the first element off the action list and pass the remaining arguments to the corresponding action
            # function
            possible_actions[action.pop(0)](action)
        else:
            raise ValueError(f"{self.__class__.__name__} received invalid action {action}")

    def _possible_actions(self) -> Dict[str, Callable[[List[str]], None]]:
        return {}

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
