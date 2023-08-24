from typing import Any, Dict

from primaite import getLogger
from primaite.simulator.core import Action, ActionManager, AllowAllValidator, SimComponent
from primaite.simulator.network.hardware.base import Link, Node

_LOGGER = getLogger(__name__)


class NetworkContainer(SimComponent):
    """Top level container object representing the physical network."""

    nodes: Dict[str, Node] = {}
    links: Dict[str, Link] = {}

    def __init__(self, **kwargs):
        """Initialise the network."""
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

    def add_node(self, node: Node) -> None:
        """
        Add an existing node to the network.

        :param node: Node instance that the network should keep track of.
        :type node: Node
        """
        if node in self:
            msg = f"Can't add node {node}. It is already in the network."
            _LOGGER.warning(msg)
            raise RuntimeWarning(msg)
        self.nodes[node.uuid] = node
        node.parent = self

    def remove_node(self, node: Node) -> None:
        """
        Remove a node from the network.

        :param node: Node instance that is currently part of the network that should be removed.
        :type node: Node
        """
        if node not in self:
            msg = f"Can't remove node {node}. It's not in the network."
            _LOGGER.warning(msg)
            raise RuntimeWarning(msg)
        del self.nodes[node.uuid]
        del node.parent  # misleading?

    def connect_nodes(self, node1: Node, node2: Node) -> None:
        """TODO."""
        # I think we should not be forcing users to add and remove individual links.
        # Clearly if a link exists between two nodes in the network, then the link is also part of the network.
        # I'm just not sure how we ought to handle link creation as it requires an unoccupied interface on the node.
        raise NotImplementedError

    def disconnect_nodes(self, node1: Node, node2: Node) -> None:
        """TODO."""
        raise NotImplementedError

    def __contains__(self, item: Any) -> bool:
        if isinstance(item, Node):
            return item.uuid in self.nodes
        elif isinstance(item, Link):
            return item.uuid in self.links
        raise TypeError("")
