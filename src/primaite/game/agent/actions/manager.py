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

from typing import Dict, List, Optional, Tuple

from gymnasium import spaces

# from primaite.game.game import PrimaiteGame # TODO: Breaks things
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


class ActionManager:
    """Class which manages the action space for an agent."""

    def __init__(
        self,
        actions: List[Dict],  # stores list of actions available to agent
        nodes: List[Dict],  # extra configuration for each node
        act_map: Optional[
            Dict[int, Dict]
        ] = None,  # allows restricting set of possible actions - TODO: Refactor to be a list?
        *args,
        **kwargs,
    ) -> None:
        """Init method for ActionManager.

        :param game: Reference to the game to which the agent belongs.
        :type game: PrimaiteGame
        :param actions: List of action specs which should be made available to the agent. The keys of each spec are:
            'type' and 'options' for passing any options to the action class's init method
        :type actions: List[dict]
        :param act_map: Action map which maps integers to actions. Used for restricting the set of possible actions.
        :type act_map: Optional[Dict[int, Dict]]
        """
        self.actions: Dict[str, AbstractAction] = {}
        for act_spec in actions:
            act_type = act_spec.get("type")
            self.actions[act_type] = AbstractAction._registry[act_type]

        self.action_map: Dict[int, Tuple[str, Dict]] = {}
        """
        Action mapping that converts an integer to a specific action and parameter choice.

        For example :
        {0: ("node_service_scan", {node_name:"client_1", service_name:"WebBrowser"})}
        """
        if act_map is None:
            # raise RuntimeError("Action map must be specified in the config file.")
            pass
        else:
            self.action_map = {i: (a["action"], a["options"]) for i, a in act_map.items()}
        # make sure all numbers between 0 and N are represented as dict keys in action map
        assert all([i in self.action_map.keys() for i in range(len(self.action_map))])
        self.node_names: List[str] = [n["node_name"] for n in nodes]
        """List of node names in this action space. The list order is the mapping between node index and node name."""

    def get_action(self, action: int) -> Tuple[str, Dict]:
        """Produce action in CAOS format."""
        """the agent chooses an action (as an integer), this is converted into an action in CAOS format"""
        """The CAOS format is basically a action identifier, followed by parameters stored in a dictionary"""
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
    def from_config(cls, game: "PrimaiteGame", cfg: Dict) -> "ActionManager":  # noqa: F821
        """
        Construct an ActionManager from a config definition.

        The action space config supports the following three sections:
            1. ``action_list``
                ``action_list`` contains a list action components which need to be included in the action space.
                Each action component has a ``type`` which maps to a subclass of AbstractAction, and additional options
                which will be passed to the action class's __init__ method during initialisation.
            2. ``action_map``
                Since the agent uses a discrete action space which acts as a flattened version of the component-based
                action space, action_map provides a mapping between an integer (chosen by the agent) and a meaningful
                action and values of parameters. For example action 0 can correspond to do nothing, action 1 can
                correspond to "node_service_scan" with ``node_name="server"`` and
                ``service_name="WebBrowser"``, action 2 can be "
            3. ``options``
                ``options`` contains a dictionary of options which are passed to the ActionManager's __init__ method.
                These options are used to calculate the shape of the action space, and to provide additional information
                to the ActionManager which is required to convert the agent's action choice into a CAOS request.

        :param game: The Primaite Game to which the agent belongs.
        :type game: PrimaiteGame
        :param cfg: The action space config.
        :type cfg: Dict
        :return: The constructed ActionManager.
        :rtype: ActionManager
        """
        if "ip_list" not in cfg["options"]:
            cfg["options"]["ip_list"] = []

        obj = cls(
            actions=cfg["action_list"],
            **cfg["options"],
            protocols=game.options.protocols,
            ports=game.options.ports,
            act_map=cfg.get("action_map"),
        )

        return obj
