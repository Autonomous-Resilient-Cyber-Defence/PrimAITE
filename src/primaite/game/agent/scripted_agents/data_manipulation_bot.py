# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
import random
from typing import Dict, Tuple

from gymnasium.core import ObsType

from primaite.game.agent.interface import AbstractScriptedAgent


class DataManipulationAgent(AbstractScriptedAgent, identifier="Data_Manipulation_Agent"):
    """Agent that uses a DataManipulationBot to perform an SQL injection attack."""

    next_execution_timestep: int = 0
    starting_node_idx: int = 0

    config: "DataManipulationAgent.ConfigSchema"

    class ConfigSchema(AbstractScriptedAgent.ConfigSchema):
        """Configuration Schema for DataManipulationAgent."""

        # TODO: Could be worth moving this to a "AbstractTAPAgent"
        starting_node_name: str
        starting_application_name: str
        next_execution_timestep: int

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_agent()

    def _set_next_execution_timestep(self, timestep: int) -> None:
        """Set the next execution timestep with a configured random variance.

        :param timestep: The timestep to add variance to.
        """
        random_timestep_increment = random.randint(
            -self.agent_settings.start_settings.variance, self.agent_settings.start_settings.variance
        )
        self.next_execution_timestep = timestep + random_timestep_increment

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

        self._set_next_execution_timestep(timestep + self.agent_settings.start_settings.frequency)
        self.logger.info(msg="Performing a data manipulation attack!")
        return "node_application_execute", {
            "node_name": self.config.starting_node_name,
            "application_name": self.config.starting_application_name,
        }

    def setup_agent(self) -> None:
        """Set the next execution timestep when the episode resets."""
        self._select_start_node()
        self._set_next_execution_timestep(self.agent_settings.start_settings.start_step)

    def _select_start_node(self) -> None:
        """Set the starting starting node of the agent to be a random node from this agent's action manager."""
        # we are assuming that every node in the node manager has a data manipulation application at idx 0
        num_nodes = len(self.action_manager.node_names)
        self.starting_node_idx = random.randint(0, num_nodes - 1)
        self.logger.debug(msg=f"Select Start Node ID: {self.starting_node_idx}")
