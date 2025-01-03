# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
import random
from typing import Dict, Tuple

from gymnasium.core import ObsType

from primaite.game.agent.interface import AbstractScriptedAgent


class TAP001(AbstractScriptedAgent):
    """
    TAP001 | Mobile Malware -- Ransomware Variant.

    Scripted Red Agent. Capable of one action; launching the kill-chain (Ransomware Application)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_agent()

    next_execution_timestep: int = 0
    starting_node_idx: int = 0
    installed: bool = False

    def _set_next_execution_timestep(self, timestep: int) -> None:
        """Set the next execution timestep with a configured random variance.

        :param timestep: The timestep to add variance to.
        """
        random_timestep_increment = random.randint(
            -self.agent_settings.start_settings.variance, self.agent_settings.start_settings.variance
        )
        self.next_execution_timestep = timestep + random_timestep_increment

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
        if timestep < self.next_execution_timestep:
            return "DONOTHING", {}

        self._set_next_execution_timestep(timestep + self.agent_settings.start_settings.frequency)

        if not self.installed:
            self.installed = True
            return "NODE_APPLICATION_INSTALL", {
                "node_id": self.starting_node_idx,
                "application_name": "RansomwareScript",
            }

        return "NODE_APPLICATION_EXECUTE", {"node_id": self.starting_node_idx, "application_id": 0}

    def setup_agent(self) -> None:
        """Set the next execution timestep when the episode resets."""
        self._select_start_node()
        self._set_next_execution_timestep(self.agent_settings.start_settings.start_step)
        for n, act in self.action_manager.action_map.items():
            if not act[0] == "NODE_APPLICATION_INSTALL":
                continue
            if act[1]["node_id"] == self.starting_node_idx:
                self.ip_address = act[1]["ip_address"]
                return
        raise RuntimeError("TAP001 agent could not find database server ip address in action map")

    def _select_start_node(self) -> None:
        """Set the starting starting node of the agent to be a random node from this agent's action manager."""
        # we are assuming that every node in the node manager has a data manipulation application at idx 0
        num_nodes = len(self.action_manager.node_names)
        self.starting_node_idx = random.randint(0, num_nodes - 1)
