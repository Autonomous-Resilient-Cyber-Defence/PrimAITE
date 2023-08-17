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

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        Please see :py:meth:`primaite.simulator.core.SimComponent.describe_state` for a more detailed explanation.

        :return: Current state of this object and child objects.
        :rtype: Dict
        """
        state = super().describe_state()
        state.update(
            {
                "nodes": {uuid: node.describe_state() for uuid, node in self.nodes.items()},
                "links": {uuid: link.describe_state() for uuid, link in self.links.items()},
            }
        )
        return state
