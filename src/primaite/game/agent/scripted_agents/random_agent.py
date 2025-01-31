# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
import random
from functools import cached_property
from typing import Dict, List, Tuple

from gymnasium.core import ObsType
from pydantic import computed_field, Field, model_validator

from primaite.game.agent.interface import AbstractScriptedAgent

__all__ = ("RandomAgent", "PeriodicAgent")


class RandomAgent(AbstractScriptedAgent, discriminator="RandomAgent"):
    """Agent that ignores its observation and acts completely at random."""

    config: "RandomAgent.ConfigSchema" = Field(default_factory=lambda: RandomAgent.ConfigSchema())

    class ConfigSchema(AbstractScriptedAgent.ConfigSchema):
        """Configuration Schema for Random Agents."""

        type: str = "RandomAgent"

    def get_action(self) -> Tuple[str, Dict]:
        """Sample the action space randomly.

        :param obs: Current observation for this agent, not used in RandomAgent
        :type obs: ObsType
        :param timestep: The current simulation timestep, not used in RandomAgent
        :type timestep: int
        :return: Action formatted in CAOS format
        :rtype: Tuple[str, Dict]
        """
        return self.action_manager.get_action(self.action_manager.space.sample())


class PeriodicAgent(AbstractScriptedAgent, discriminator="PeriodicAgent"):
    """Agent that does nothing most of the time, but executes application at regular intervals (with variance)."""

    config: "PeriodicAgent.ConfigSchema" = Field(default_factory=lambda: PeriodicAgent.ConfigSchema())

    class AgentSettingsSchema(AbstractScriptedAgent.AgentSettingsSchema):
        """Schema for the `agent_settings` part of the agent config."""

        start_step: int = 5
        "The timestep at which an agent begins performing it's actions"
        start_variance: int = 0
        frequency: int = 5
        "The number of timesteps to wait between performing actions"
        variance: int = 0
        "The amount the frequency can randomly change to"
        max_executions: int = 999999
        possible_start_nodes: List[str]
        target_application: str

        @model_validator(mode="after")
        def check_variance_lt_frequency(self) -> "PeriodicAgent.ConfigSchema":
            """
            Make sure variance is equal to or lower than frequency.

            This is because the calculation for the next execution time is now + (frequency +- variance).
            If variance were greater than frequency, sometimes the bracketed term would be negative
            and the attack would never happen again.
            """
            if self.variance >= self.frequency:
                raise ValueError(
                    f"Agent start settings error: variance must be lower than frequency "
                    f"{self.variance=}, {self.frequency=}"
                )
            return self

    class ConfigSchema(AbstractScriptedAgent.ConfigSchema):
        """Configuration Schema for Periodic Agent."""

        type: str = "PeriodicAgent"
        """Name of the agent."""
        agent_settings: "PeriodicAgent.AgentSettingsSchema" = Field(
            default_factory=lambda: PeriodicAgent.AgentSettingsSchema()
        )

    num_executions: int = 0
    """Number of times the agent has executed an action."""
    next_execution_timestep: int = 0
    """Timestep of the next action execution by the agent."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._set_next_execution_timestep(
            timestep=self.config.agent_settings.start_step, variance=self.config.agent_settings.start_variance
        )

    @computed_field
    @cached_property
    def start_node(self) -> str:
        """On instantiation, randomly select a start node."""
        return random.choice(self.config.agent_settings.possible_start_nodes)

    def _set_next_execution_timestep(self, timestep: int, variance: int) -> None:
        """Set the next execution timestep with a configured random variance.

        :param timestep: The timestep when the next execute action should be taken.
        :type timestep: int
        :param variance: Uniform random variance applied to the timestep
        :type variance: int
        """
        random_increment = random.randint(-variance, variance)
        self.next_execution_timestep = timestep + random_increment

    def get_action(self, obs: ObsType, timestep: int) -> Tuple[str, Dict]:
        """Do nothing, unless the current timestep is the next execution timestep, in which case do the action."""
        if timestep == self.next_execution_timestep and self.num_executions < self.config.agent_settings.max_executions:
            self.num_executions += 1
            self._set_next_execution_timestep(
                timestep + self.config.agent_settings.frequency, self.config.agent_settings.variance
            )
            return "node_application_execute", {
                "node_name": self.start_node,
                "application_name": self.config.agent_settings.target_application,
            }

        return "do_nothing", {}
