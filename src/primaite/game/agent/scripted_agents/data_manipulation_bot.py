# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from typing import Dict, Tuple

from gymnasium.core import ObsType
from pydantic import Field

from primaite.game.agent.scripted_agents.random_agent import PeriodicAgent

__all__ = "DataManipulationAgent"


class DataManipulationAgent(PeriodicAgent, discriminator="RedDatabaseCorruptingAgent"):
    """Agent that uses a DataManipulationBot to perform an SQL injection attack."""

    class AgentSettingsSchema(PeriodicAgent.AgentSettingsSchema):
        """Schema for the `agent_settings` part of the agent config."""

        target_application: str = "DataManipulationBot"

    class ConfigSchema(PeriodicAgent.ConfigSchema):
        """Configuration Schema for DataManipulationAgent."""

        type: str = "RedDatabaseCorruptingAgent"
        agent_settings: "DataManipulationAgent.AgentSettingsSchema" = Field(
            default_factory=lambda: DataManipulationAgent.AgentSettingsSchema()
        )

    config: "DataManipulationAgent.ConfigSchema" = Field(default_factory=lambda: DataManipulationAgent.ConfigSchema())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._set_next_execution_timestep(timestep=self.config.agent_settings.start_step, variance=0)

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

        self._set_next_execution_timestep(
            timestep=timestep + self.config.agent_settings.frequency, variance=self.config.agent_settings.variance
        )
        self.logger.info(msg="Performing a data manipulation attack!")
        return "node_application_execute", {
            "node_name": self.start_node,
            "application_name": self.config.agent_settings.target_application,
        }
