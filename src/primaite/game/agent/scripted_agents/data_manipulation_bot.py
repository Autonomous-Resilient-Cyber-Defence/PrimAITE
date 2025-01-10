# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from typing import Dict, Optional, Tuple

from gymnasium.core import ObsType
from pydantic import Field

from primaite.game.agent.scripted_agents.abstract_tap import AbstractTAPAgent

__all__ = "DataManipulationAgent"


class DataManipulationAgent(AbstractTAPAgent, identifier="RedDatabaseCorruptingAgent"):
    """Agent that uses a DataManipulationBot to perform an SQL injection attack."""

    config: "DataManipulationAgent.ConfigSchema" = Field(default_factory=lambda: DataManipulationAgent.ConfigSchema())

    class ConfigSchema(AbstractTAPAgent.ConfigSchema):
        """Configuration Schema for DataManipulationAgent."""

        type: str = "RedDatabaseCorruptingAgent"
        starting_application_name: Optional[str] = None

    @property
    def starting_node_name(self) -> str:
        """Returns the agents starting node name."""
        return self.config.starting_node_name

    def get_action(self, obs: ObsType, timestep: int) -> Tuple[str, Dict]:
        """Waits until a specific timestep, then attempts to execute its data manipulation application.

        :param obs: Current observation for this agent, not used in DataManipulationAgent
        :type obs: ObsType
        :param timestep: The current simulation timestep, used for scheduling actions
        :type timestep: int
        :return: Action formatted in CAOS format
        :rtype: Tuple[str, Dict]
        """
        if self.starting_node_name or self.config is None:
            self.setup_agent()
            self.get_action(obs=obs, timestep=timestep)

        if timestep < self.next_execution_timestep:
            self.logger.debug(msg="Performing do nothing action")
            return "do_nothing", {}

        self._set_next_execution_timestep(timestep + self.config.frequency)
        self.logger.info(msg="Performing a data manipulation attack!")
        return "node_application_execute", {
            "node_name": self.config.starting_node_name,
            "application_name": self.config.starting_application_name,
        }

    def setup_agent(self) -> None:
        """Set the next execution timestep when the episode resets."""
        self._select_start_node()
        self._set_next_execution_timestep(self.config.start_step)
