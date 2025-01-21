# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
"""yaml example.

agents:
  - name: agent_1
    action_space:
      actions:
        - do_nothing
        - node_service_start
        - node_service_stop
      action_map:
"""

from __future__ import annotations

from typing import Dict, Tuple

from gymnasium import spaces
from pydantic import BaseModel, ConfigDict, Field, field_validator

from primaite.game.agent.actions.abstract import AbstractAction
from primaite.interface.request import RequestFormat

__all__ = ("DoNothingAction", "ActionManager")


class DoNothingAction(AbstractAction, identifier="do_nothing"):
    """Do Nothing Action."""

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Configuration Schema for do_nothingAction."""

        type: str = "do_nothing"

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return ["do_nothing"]


class _ActionMapItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str
    options: Dict


class ActionManager(BaseModel):
    """Class which manages the action space for an agent."""

    class ConfigSchema(BaseModel):
        """Config Schema for ActionManager."""

        model_config = ConfigDict(extra="forbid")
        action_map: Dict[int, _ActionMapItem] = {}
        """Mapping between integer action choices and CAOS actions."""

        @field_validator("action_map", mode="after")
        def consecutive_action_nums(cls, v: Dict) -> Dict:
            """Make sure all numbers between 0 and N are represented as dict keys in action map."""
            assert all([i in v.keys() for i in range(len(v))])
            return v

    config: ActionManager.ConfigSchema = Field(default_factory=lambda: ActionManager.ConfigSchema())

    action_map: Dict[int, Tuple[str, Dict]] = {}
    """Init as empty, populate after model validation."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.action_map = {n: (v.action, v.options) for n, v in self.config.action_map.items()}

    def get_action(self, action: int) -> Tuple[str, Dict]:
        """
        Produce action in CAOS format.

        The agent chooses an action (as an integer), this is converted into an action in CAOS format
        The CAOS format is basically an action identifier, followed by parameters stored in a dictionary.
        """
        act_identifier, act_options = self.action_map[action]
        return act_identifier, act_options

    def form_request(self, action_identifier: str, action_options: Dict) -> RequestFormat:
        """Take action in CAOS format and use the execution definition to change it into PrimAITE request format."""
        act_class = AbstractAction._registry[action_identifier]
        config = act_class.ConfigSchema(**action_options)
        return act_class.form_request(config=config)

    @property
    def space(self) -> spaces.Space:
        """Return the gymnasium action space for this agent."""
        return spaces.Discrete(len(self.action_map))

    @classmethod
    def from_config(cls, cfg: Dict) -> "ActionManager":
        """
        Construct an ActionManager from a config dictionary.

        The action space config supports must contain the following key:
            ``action_map`` - List of actions available to the agent, formatted as a dictionary where the key is the
            action number between 0 - N, and the value is the CAOS-formatted action.

        :param cfg: The action space config.
        :type cfg: Dict
        :return: The constructed ActionManager.
        :rtype: ActionManager
        """
        return cls(**cfg.get("options", {}), act_map=cfg.get("action_map"))
