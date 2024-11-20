# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from __future__ import annotations

import random
from typing import Dict, Tuple

from gymnasium.core import ObsType

from primaite.game.agent.interface import AbstractScriptedAgent


class TAP001(AbstractScriptedAgent, identifier="TAP001"):
    """
    TAP001 | Mobile Malware -- Ransomware Variant.

    Scripted Red Agent. Capable of one action; launching the kill-chain (Ransomware Application)
    """

    # TODO: Link with DataManipulationAgent via a parent "TAP" agent class.

    config: "TAP001.ConfigSchema"

    class ConfigSchema(AbstractScriptedAgent.ConfigSchema):
        """Configuration Schema for TAP001 Agent."""

        starting_node_name: str
        next_execution_timestep: int = 0
        installed: bool = False

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.setup_agent()

    def _set_next_execution_timestep(self, timestep: int) -> None:
        """Set the next execution timestep with a configured random variance.

        :param timestep: The timestep to add variance to.
        """
        random_timestep_increment = random.randint(
            -self.config.agent_settings.start_settings.variance, self.config.agent_settings.start_settings.variance
        )
        self.config.next_execution_timestep = timestep + random_timestep_increment

    def get_action(self, obs: ObsType, timestep: int) -> Tuple[str, Dict]:
        """Waits until a specific timestep, then attempts to execute the ransomware application.

        This application acts a wrapper around the kill-chain, similar to green-analyst and
        the previous UC2 data manipulation bot.

        :param obs: Current observation for this agent.
        :type obs: ObsType
        :param timestep: The current simulation timestep, used for scheduling actions
        :type timestep: int
        :return: Action formatted in CAOS format
        :rtype: Tuple[str, Dict]
        """
        if timestep < self.config.next_execution_timestep:
            return "do_nothing", {}

        self._set_next_execution_timestep(timestep + self.config.agent_settings.start_settings.frequency)

        if not self.config.installed:
            self.config.installed = True
            return "node_application_install", {
                "node_name": self.config.starting_node_name,
                "application_name": "RansomwareScript",
            }

        return "node_application_execute", {"node_name": self.config.starting_node_name, "application_id": 0}

    def setup_agent(self) -> None:
        """Set the next execution timestep when the episode resets."""
        self._select_start_node()
        self._set_next_execution_timestep(self.config.agent_settings.start_settings.start_step)
        for n, act in self.config.action_manager.action_map.items():
            if not act[0] == "node_application_install":
                continue
            if act[1]["node_name"] == self.config.starting_node_name:
                self.ip_address = act[1]["ip_address"]
                return
        raise RuntimeError("TAP001 agent could not find database server ip address in action map")

    def _select_start_node(self) -> None:
        """Set the starting starting node of the agent to be a random node from this agent's action manager."""
        # we are assuming that every node in the node manager has a data manipulation application at idx 0
        num_nodes = len(self.config.action_manager.node_names)
        # TODO: Change this to something?
        self.starting_node_idx = random.randint(0, num_nodes - 1)
        self.logger.debug(f"Selected Starting node ID: {self.starting_node_idx}")
