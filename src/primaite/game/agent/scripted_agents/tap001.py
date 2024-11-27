# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from __future__ import annotations

import random
from typing import Dict, Tuple

from primaite.game.agent.scripted_agents.abstract_tap import AbstractTAPAgent


class TAP001(AbstractTAPAgent, identifier="TAP001"):
    """
    TAP001 | Mobile Malware -- Ransomware Variant.

    Scripted Red Agent. Capable of one action; launching the kill-chain (Ransomware Application)
    """

    config: "TAP001.ConfigSchema"

    class ConfigSchema(AbstractTAPAgent.ConfigSchema):
        """Configuration Schema for TAP001 Agent."""

        installed: bool = False

    @property
    def starting_node_name(self) -> str:
        """Node that TAP001 starts from."""
        return self.config.starting_node_name

    @classmethod
    def from_config(cls, config: Dict) -> TAP001:
        """Override the base from_config method to ensure successful agent setup."""
        obj: TAP001 = cls(config=cls.ConfigSchema(**config))
        obj.setup_agent()
        return obj

    def get_action(self, timestep: int) -> Tuple[str, Dict]:
        """Waits until a specific timestep, then attempts to execute the ransomware application.

        This application acts a wrapper around the kill-chain, similar to green-analyst and
        the previous UC2 data manipulation bot.

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
                "node_name": self.starting_node_name,
                "application_name": "RansomwareScript",
            }

        return "node_application_execute", {
            "node_name": self.starting_node_name,
            "application_name": "RansomwareScript",
        }

    def setup_agent(self) -> None:
        """Set the next execution timestep when the episode resets."""
        self._select_start_node()
        self._set_next_execution_timestep(self.config.agent_settings.start_settings.start_step)
        for n, act in self.config.action_manager.action_map.items():
            if not act[0] == "node_application_install":
                continue
            if act[1]["node_name"] == self.starting_node_name:
                self.ip_address = act[1]["ip_address"]
                return
        raise RuntimeError("TAP001 agent could not find database server ip address in action map")

    def _select_start_node(self) -> None:
        """Set the starting starting node of the agent to be a random node from this agent's action manager."""
        # we are assuming that every node in the node manager has a data manipulation application at idx 0
        num_nodes = len(self.config.action_manager.node_names)
        starting_node_idx = random.randint(0, num_nodes - 1)
        self.starting_node_name = self.config.action_manager.node_names[starting_node_idx]
        self.config.logger.debug(f"Selected Starting node ID: {self.starting_node_name}")
