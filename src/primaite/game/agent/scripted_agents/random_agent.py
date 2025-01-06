# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
import random
from typing import Dict, Tuple

from gymnasium.core import ObsType

from primaite.game.agent.interface import AbstractScriptedAgent

__all__ = ("RandomAgent", "PeriodicAgent")


class RandomAgent(AbstractScriptedAgent, identifier="Random_Agent"):
    """Agent that ignores its observation and acts completely at random."""

    class ConfigSchema(AbstractScriptedAgent.ConfigSchema):
        """Configuration Schema for Random Agents."""

        agent_name: str = "Random_Agent"

    def get_action(self) -> Tuple[str, Dict]:
        """Sample the action space randomly.

        :param obs: Current observation for this agent, not used in RandomAgent
        :type obs: ObsType
        :param timestep: The current simulation timestep, not used in RandomAgent
        :type timestep: int
        :return: Action formatted in CAOS format
        :rtype: Tuple[str, Dict]
        """
        return self.action_manager.get_action(self.action_manager.space.sample())


class PeriodicAgent(AbstractScriptedAgent, identifier="Periodic_Agent"):
    """Agent that does nothing most of the time, but executes application at regular intervals (with variance)."""

    config: "PeriodicAgent.ConfigSchema" = {}

    class ConfigSchema(AbstractScriptedAgent.ConfigSchema):
        """Configuration Schema for Periodic Agent."""

        agent_name: str = "Periodic_Agent"
        """Name of the agent."""

    max_executions: int = 999999
    "Maximum number of times the agent can execute its action."
    num_executions: int = 0
    """Number of times the agent has executed an action."""
    # TODO: Also in abstract_tap - move up and inherit? Add to AgentStartSettings?
    next_execution_timestep: int = 0
    """Timestep of the next action execution by the agent."""

    @property
    def start_step(self) -> int:
        """Return the timestep at which an agent begins performing it's actions."""
        return self.config.agent_settings.start_settings.start_step

    @property
    def start_variance(self) -> int:
        """Returns the deviation around the start step."""
        return self.config.agent_settings.start_settings.variance

    @property
    def frequency(self) -> int:
        """Returns the number of timesteps to wait between performing actions."""
        return self.config.agent_settings.start_settings.frequency

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
        if timestep == self.next_execution_timestep and self.num_executions < self.max_executions:
            self.num_executions += 1
            self._set_next_execution_timestep(timestep + self.frequency, self.start_variance)
            self.target_node = self.action_manager.node_names[0]
            return "node_application_execute", {"node_name": self.target_node, "application_name": 0}

        return "DONOTHING", {}
