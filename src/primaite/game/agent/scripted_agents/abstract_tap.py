# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

from gymnasium.core import ObsType
from pydantic import Field

from primaite.game.agent.scripted_agents.random_agent import PeriodicAgent

__all__ = "AbstractTAPAgent"


class AbstractTAPAgent(PeriodicAgent, ABC):
    """Base class for TAP agents to inherit from."""

    config: "AbstractTAPAgent.ConfigSchema" = Field(default_factory=lambda: AbstractTAPAgent.ConfigSchema())
    next_execution_timestep: int = 0

    class AgentSettingsSchema(PeriodicAgent.AgentSettingsSchema, ABC):
        """Schema for the `agent_settings` part of the agent config."""

        possible_starting_nodes: List[str] = Field(default_factory=list)

    class ConfigSchema(PeriodicAgent.ConfigSchema, ABC):
        """Configuration schema for Abstract TAP agents."""

        type: str = "abstract-tap"
        agent_settings: AbstractTAPAgent.AgentSettingsSchema = Field(
            default_factory=lambda: AbstractTAPAgent.AgentSettingsSchema()
        )

    starting_node: Optional[str] = None

    @abstractmethod
    def get_action(self, obs: ObsType, timestep: int = 0) -> Tuple[str, Dict]:
        """Return an action to be taken in the environment."""
        return super().get_action(obs=obs, timestep=timestep)

    @abstractmethod
    def setup_agent(self) -> None:
        """Set up agent."""
        pass

    def _set_next_execution_timestep(self, timestep: int) -> None:
        """Set the next execution timestep with a configured random variance.

        :param timestep: The timestep to add variance to.
        """
        random_timestep_increment = random.randint(
            -self.config.agent_settings.variance, self.config.agent_settings.variance
        )
        self.next_execution_timestep = timestep + random_timestep_increment

    def _select_start_node(self) -> None:
        """Set the starting starting node of the agent to be a random node from this agent's action manager."""
        # we are assuming that every node in the node manager has a data manipulation application at idx 0
        self.starting_node = random.choice(self.config.agent_settings.possible_starting_nodes)
        self.logger.debug(f"Selected starting node: {self.starting_node}")
