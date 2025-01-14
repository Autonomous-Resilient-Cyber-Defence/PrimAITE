# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
import random
from typing import Dict, List, Tuple

from gymnasium.core import ObsType
from pydantic import Field

from primaite.game.agent.scripted_agents.random_agent import PeriodicAgent

__all__ = "DataManipulationAgent"


class DataManipulationAgent(PeriodicAgent, identifier="RedDatabaseCorruptingAgent"):
    """Agent that uses a DataManipulationBot to perform an SQL injection attack."""

    class ConfigSchema(PeriodicAgent.ConfigSchema):
        """Configuration Schema for DataManipulationAgent."""

        type: str = "RedDatabaseCorruptingAgent"
        starting_application_name: str = "DataManipulationBot"
        possible_start_nodes: List[str]

    config: "DataManipulationAgent.ConfigSchema" = Field(default_factory=lambda: DataManipulationAgent.ConfigSchema())

    start_node: str

    def __init__(self, **kwargs):
        kwargs["start_node"] = random.choice(kwargs["config"].possible_start_nodes)
        super().__init__(**kwargs)
        self._set_next_execution_timestep(timestep=self.config.start_step, variance=0)

    def get_action(self, obs: ObsType, timestep: int) -> Tuple[str, Dict]:
        """Waits until a specific timestep, then attempts to execute its data manipulation application.

        :param obs: Current observation for this agent, not used in DataManipulationAgent
        :type obs: ObsType
        :param timestep: The current simulation timestep, used for scheduling actions
        :type timestep: int
        :return: Action formatted in CAOS format
        :rtype: Tuple[str, Dict]
        """
        if timestep < self.next_execution_timestep:
            self.logger.debug(msg="Performing do nothing action")
            return "do_nothing", {}

        self._set_next_execution_timestep(timestep=timestep + self.config.frequency, variance=self.config.variance)
        self.logger.info(msg="Performing a data manipulation attack!")
        return "node_application_execute", {
            "node_name": self.start_node,
            "application_name": self.config.starting_application_name,
        }
