from typing import Dict

from primaite.simulator.core import Action, ActionManager, AllowAllValidator, SimComponent
from primaite.simulator.network.hardware.base import Link, Node


class NetworkContainer(SimComponent):
    """TODO."""

    nodes: Dict[str, Node] = {}
    links: Dict[str, Link] = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.action_manager = ActionManager()
        self.action_manager.add_action(
            "node",
            Action(
                func=lambda request, context: self.nodes[request.pop(0)].apply_action(request, context),
                validator=AllowAllValidator(),
            ),
        )
