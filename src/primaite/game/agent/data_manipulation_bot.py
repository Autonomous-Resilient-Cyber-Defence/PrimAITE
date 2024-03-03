import random
from typing import Dict, Optional, Tuple

from gymnasium.core import ObsType

from primaite.game.agent.interface import AbstractScriptedAgent


class DataManipulationAgent(AbstractScriptedAgent):
    """Agent that uses a DataManipulationBot to perform an SQL injection attack."""

    next_execution_timestep: int = 0
    starting_node_idx: int = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reset_agent_for_episode()

    def _set_next_execution_timestep(self, timestep: int) -> None:
        """Set the next execution timestep with a configured random variance.

        :param timestep: The timestep to add variance to.
        """
        random_timestep_increment = random.randint(
            -self.agent_settings.start_settings.variance, self.agent_settings.start_settings.variance
        )
        self.next_execution_timestep = timestep + random_timestep_increment

    def get_action(self, obs: ObsType, reward: float = 0.0, timestep: Optional[int] = None) -> Tuple[str, Dict]:
        """Randomly sample an action from the action space.

        :param obs: _description_
        :type obs: ObsType
        :param reward: _description_, defaults to None
        :type reward: float, optional
        :return: _description_
        :rtype: Tuple[str, Dict]
        """
        if timestep < self.next_execution_timestep:
            return "DONOTHING", {"dummy": 0}

        self._set_next_execution_timestep(timestep + self.agent_settings.start_settings.frequency)

        return "NODE_APPLICATION_EXECUTE", {"node_id": self.starting_node_idx, "application_id": 0}

    def reset_agent_for_episode(self) -> None:
        """Set the next execution timestep when the episode resets."""
        super().reset_agent_for_episode()
        self._select_start_node()
        self._set_next_execution_timestep(self.agent_settings.start_settings.start_step)

    def _select_start_node(self) -> None:
        """Set the starting starting node of the agent to be a random node from this agent's action manager."""
        # we are assuming that every node in the node manager has a data manipulation application at idx 0
        num_nodes = len(self.action_manager.node_names)
        self.starting_node_idx = random.randint(0, num_nodes - 1)
