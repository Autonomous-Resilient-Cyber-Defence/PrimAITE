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

        agent_name: str = "TAP001"
        installed: bool = False

    def __init__(self) -> None:
        """___init___ bruv. Restecpa."""
        super().__init__()
        self.setup_agent()

    @property
    def starting_node_name(self) -> str:
        """Node that TAP001 starts from."""
        return self.config.starting_node_name

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
