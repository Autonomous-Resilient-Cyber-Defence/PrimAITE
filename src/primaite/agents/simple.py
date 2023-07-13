from typing import TYPE_CHECKING

from primaite.agents.agent import HardCodedAgentSessionABC
from primaite.agents.utils import get_new_action, transform_action_acl_enum, transform_action_node_enum

if TYPE_CHECKING:
    import numpy as np


class RandomAgent(HardCodedAgentSessionABC):
    """
    A Random Agent.

    Get a completely random action from the action space.
    """

    def _calculate_action(self, obs: "np.ndarray") -> int:
        return self._env.action_space.sample()


class DummyAgent(HardCodedAgentSessionABC):
    """
    A Dummy Agent.

    All action spaces setup so dummy action is always 0 regardless of action type used.
    """

    def _calculate_action(self, obs: "np.ndarray") -> int:
        return 0


class DoNothingACLAgent(HardCodedAgentSessionABC):
    """
    A do nothing ACL agent.

    A valid ACL action that has no effect; does nothing.
    """

    def _calculate_action(self, obs: "np.ndarray") -> int:
        nothing_action = ["NONE", "ALLOW", "ANY", "ANY", "ANY", "ANY"]
        nothing_action = transform_action_acl_enum(nothing_action)
        nothing_action = get_new_action(nothing_action, self._env.action_dict)

        return nothing_action


class DoNothingNodeAgent(HardCodedAgentSessionABC):
    """
    A do nothing Node agent.

    A valid Node action that has no effect; does nothing.
    """

    def _calculate_action(self, obs: "np.ndarray") -> int:
        nothing_action = [1, "NONE", "ON", 0]
        nothing_action = transform_action_node_enum(nothing_action)
        nothing_action = get_new_action(nothing_action, self._env.action_dict)
        # nothing_action should currently always be 0

        return nothing_action
