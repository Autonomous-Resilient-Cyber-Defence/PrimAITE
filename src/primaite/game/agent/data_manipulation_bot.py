import random
from typing import Dict, List, Tuple

from gymnasium.core import ObsType

from primaite.game.agent.interface import AbstractScriptedAgent
from primaite.simulator.system.applications.red_applications.data_manipulation_bot import DataManipulationBot


class DataManipulationAgent(AbstractScriptedAgent):
    """Agent that uses a DataManipulationBot to perform an SQL injection attack."""

    data_manipulation_bots: List["DataManipulationBot"] = []
    next_execution_timestep: int = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._set_next_execution_timestep(self.agent_settings.start_settings.start_step)

    def _set_next_execution_timestep(self, timestep: int) -> None:
        """Set the next execution timestep with a configured random variance.

        :param timestep: The timestep to add variance to.
        """
        random_timestep_increment = random.randint(
            -self.agent_settings.start_settings.variance, self.agent_settings.start_settings.variance
        )
        self.next_execution_timestep = timestep + random_timestep_increment

    def get_action(self, obs: ObsType, reward: float = None) -> Tuple[str, Dict]:
        """Randomly sample an action from the action space.

        :param obs: _description_
        :type obs: ObsType
        :param reward: _description_, defaults to None
        :type reward: float, optional
        :return: _description_
        :rtype: Tuple[str, Dict]
        """
        current_timestep = self.action_manager.game.step_counter

        if current_timestep < self.next_execution_timestep:
            return "DONOTHING", {"dummy": 0}

        self._set_next_execution_timestep(current_timestep + self.agent_settings.start_settings.frequency)

        return "NODE_APPLICATION_EXECUTE", {"node_id": 0, "application_id": 0}
