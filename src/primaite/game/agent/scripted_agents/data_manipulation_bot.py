# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from typing import Dict, Tuple

from gymnasium.core import ObsType

from primaite.game.agent.scripted_agents.abstract_tap import AbstractTAPAgent


class DataManipulationAgent(AbstractTAPAgent, identifier="Data_Manipulation_Agent"):
    """Agent that uses a DataManipulationBot to perform an SQL injection attack."""

    config: "DataManipulationAgent.ConfigSchema"

    class ConfigSchema(AbstractTAPAgent.ConfigSchema):
        """Configuration Schema for DataManipulationAgent."""

        starting_application_name: str
        agent_name: str = "Data_Manipulation_Agent"

    def __init__(self) -> None:
        """Meh."""
        self.setup_agent()

    @property
    def next_execution_timestep(self) -> int:
        """Returns the agents next execution timestep."""
        return self.config.next_execution_timestep

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
        if timestep < self.next_execution_timestep:
            self.config.logger.debug(msg="Performing do nothing action")
            return "do_nothing", {}

        self._set_next_execution_timestep(timestep + self.config.agent_settings.start_settings.frequency)
        self.config.logger.info(msg="Performing a data manipulation attack!")
        return "node_application_execute", {
            "node_name": self.config.starting_node_name,
            "application_name": self.config.starting_application_name,
        }

    def setup_agent(self) -> None:
        """Set the next execution timestep when the episode resets."""
        self._select_start_node()
        self._set_next_execution_timestep(self.config.agent_settings.start_settings.start_step)
