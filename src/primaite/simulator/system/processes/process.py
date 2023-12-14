from abc import abstractmethod
from enum import Enum
from typing import Dict

from primaite.simulator.system.software import Software


class ProcessOperatingState(Enum):
    """Enumeration of Process Operating States."""

    RUNNING = 1
    "The process is running."
    PAUSED = 2
    "The process is temporarily paused."


class Process(Software):
    """
    Represents a Process, a program in execution, in the simulation environment.

    Processes are executed by a Node and do not have the ability to performing input/output operations.
    """

    operating_state: ProcessOperatingState
    "The current operating state of the Process."

    def set_original_state(self):
        """Sets the original state."""
        super().set_original_state()
        vals_to_include = {"operating_state"}
        self._original_state.update(self.model_dump(include=vals_to_include))

    @abstractmethod
    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        Please see :py:meth:`primaite.simulator.core.SimComponent.describe_state` for a more detailed explanation.

        :return: Current state of this object and child objects.
        :rtype: Dict
        """
        state = super().describe_state()
        state.update({"operating_state": self.operating_state.value})
        return state
