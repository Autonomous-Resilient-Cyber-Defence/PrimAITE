from typing import Any, Dict, Union

from primaite import getLogger
from primaite.simulator.core import Action, ActionManager, AllowAllValidator, SimComponent
from primaite.simulator.network.hardware.base import Link, NIC, Node, SwitchPort

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

    def connect_nodes(self, endpoint_a: Union[NIC, SwitchPort], endpoint_b: Union[NIC, SwitchPort], **kwargs) -> None:
        """Connect two nodes on the network by creating a link between an NIC/SwitchPort of each one.

        :param endpoint_a: The endpoint to which to connect the link on the first node
        :type endpoint_a: Union[NIC, SwitchPort]
        :param endpoint_b: The endpoint to which to connct the link on the second node
        :type endpoint_b: Union[NIC, SwitchPort]
        :raises RuntimeError: _description_
        """
        node_a = endpoint_a.parent
        node_b = endpoint_b.parent
        msg = ""
        if node_a not in self:
            msg = f"Cannot create a link to {endpoint_a} because the node is not in the network."
        if node_b not in self:
            msg = f"Cannot create a link to {endpoint_b} because the node is not in the network."
        if node_a is node_b:
            msg = f"Cannot link {endpoint_a} to {endpoint_b} because they belong to the same node."
        if msg:
            _LOGGER.error(msg)
            raise RuntimeError(msg)

        link = Link(endpoint_a=endpoint_a, endpoint_b=endpoint_b, **kwargs)
        self.links[link.uuid] = link
        link.parent = self

    def remove_link(self, link: Link) -> None:
        """Disconnect a link from the network.

        :param link: The link to be removed
        :type link: Link
        """
        link.endpoint_a.disconnect_link()
        link.endpoint_b.disconnect_link()
        del self.links[link.uuid]
        del link.parent

    def __contains__(self, item: Any) -> bool:
        if isinstance(item, Node):
            return item.uuid in self.nodes
        elif isinstance(item, Link):
            return item.uuid in self.links
        raise TypeError("")
