from typing import Dict, Tuple

from gymnasium.core import ObsType

from primaite.game.agent.interface import AbstractScriptedAgent


class RandomAgent(AbstractScriptedAgent):
    """Agent that ignores its observation and acts completely at random."""

    def get_action(self, obs: ObsType, timestep: int = 0) -> Tuple[str, Dict]:
        """Sample the action space randomly.

        :param obs: Current observation for this agent, not used in RandomAgent
        :type obs: ObsType
        :param timestep: The current simulation timestep, not used in RandomAgent
        :type timestep: int
        :return: Action formatted in CAOS format
        :rtype: Tuple[str, Dict]
        """
        return self.action_manager.get_action(self.action_manager.space.sample())
