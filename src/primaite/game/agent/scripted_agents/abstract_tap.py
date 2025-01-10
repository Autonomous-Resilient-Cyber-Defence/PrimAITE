# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from __future__ import annotations

import random
from abc import abstractmethod
from typing import Dict, Optional, Tuple

from gymnasium.core import ObsType
from pydantic import Field

from primaite.game.agent.interface import AbstractScriptedAgent

__all__ = "AbstractTAPAgent"


class AbstractTAPAgent(AbstractScriptedAgent, identifier="AbstractTAP"):
    """Base class for TAP agents to inherit from."""

    config: "AbstractTAPAgent.ConfigSchema" = Field(default_factory=lambda: AbstractTAPAgent.ConfigSchema())
    agent_name: str = "Abstract_TAP"
    next_execution_timestep: int = 0

    class ConfigSchema(AbstractScriptedAgent.ConfigSchema):
        """Configuration schema for Abstract TAP agents."""

        starting_node_name: Optional[str] = None

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
        random_timestep_increment = random.randint(-self.config.variance, self.config.variance)
        self.next_execution_timestep = timestep + random_timestep_increment

    def _select_start_node(self) -> None:
        """Set the starting starting node of the agent to be a random node from this agent's action manager."""
        # we are assuming that every node in the node manager has a data manipulation application at idx 0
        num_nodes = len(self.action_manager.node_names)
        starting_node_idx = random.randint(0, num_nodes - 1)
        self.config.starting_node_name = self.action_manager.node_names[starting_node_idx]
        self.logger.debug(f"Selected starting node: {self.config.starting_node_name}")
