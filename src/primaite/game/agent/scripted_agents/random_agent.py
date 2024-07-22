# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
import random
from typing import Dict, Optional, Tuple

from gymnasium.core import ObsType
from pydantic import BaseModel

from primaite.game.agent.actions import ActionManager
from primaite.game.agent.interface import AbstractScriptedAgent
from primaite.game.agent.observations.observation_manager import ObservationManager
from primaite.game.agent.rewards import RewardFunction


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


class PeriodicAgent(AbstractScriptedAgent):
    """Agent that does nothing most of the time, but executes application at regular intervals (with variance)."""

    class Settings(BaseModel):
        """Configuration values for when an agent starts performing actions."""

        start_step: int = 20
        "The timestep at which an agent begins performing it's actions."
        start_variance: int = 5
        "Deviation around the start step."
        frequency: int = 5
        "The number of timesteps to wait between performing actions."
        variance: int = 0
        "The amount the frequency can randomly change to."
        max_executions: int = 999999
        "Maximum number of times the agent can execute its action."

    def __init__(
        self,
        agent_name: str,
        action_space: ActionManager,
        observation_space: ObservationManager,
        reward_function: RewardFunction,
        settings: Optional[Settings] = None,
    ) -> None:
        """Initialise PeriodicAgent."""
        super().__init__(
            agent_name=agent_name,
            action_space=action_space,
            observation_space=observation_space,
            reward_function=reward_function,
        )
        self.settings = settings or PeriodicAgent.Settings()
        self._set_next_execution_timestep(timestep=self.settings.start_step, variance=self.settings.start_variance)
        self.num_executions = 0

    def _set_next_execution_timestep(self, timestep: int, variance: int) -> None:
        """Set the next execution timestep with a configured random variance.

        :param timestep: The timestep when the next execute action should be taken.
        :type timestep: int
        :param variance: Uniform random variance applied to the timestep
        :type variance: int
        """
        random_increment = random.randint(-variance, variance)
        self.next_execution_timestep = timestep + random_increment

    def get_action(self, obs: ObsType, timestep: int) -> Tuple[str, Dict]:
        """Do nothing, unless the current timestep is the next execution timestep, in which case do the action."""
        if timestep == self.next_execution_timestep and self.num_executions < self.settings.max_executions:
            self.num_executions += 1
            self._set_next_execution_timestep(timestep + self.settings.frequency, self.settings.variance)
            return "NODE_APPLICATION_EXECUTE", {"node_id": 0, "application_id": 0}

        return "DONOTHING", {}
